#!/usr/bin/env python3
"""print-loss-check.py — how much of a page's PROSE disappears when it is printed.

WHY. A hiring manager who prints a case study gets whatever the print stylesheet
leaves behind. Nothing here had ever measured that, and an earlier session recorded
"printing drops 9-22% of the text" as a note — a judgement, not a receipt. This is
the receipt.

WHAT IT MEASURES. innerText is a RENDERED view: content hidden by display:none is
absent from it. So the same page read under screen and under print emulation gives
two texts, and the difference is what a reader on paper never sees.

WHAT IT DELIBERATELY IGNORES. Navigation, footer, skip links, the video frame and
the on-page controls are hidden in print ON PURPOSE — a printed page has no use for
a menu. Those are subtracted before the loss is computed, so the number reported is
prose loss, not chrome loss. Counting chrome would report a large, meaningless
figure and hide the small, real one.

WHAT IT CANNOT SEE. Text that prints but is unreadable (clipped by a fixed height,
running off the paper edge, or white-on-white), anything split badly across a page
break, and images that carry text. innerText also collapses whitespace, so the
figure is characters of content, not of layout.

USAGE  print-loss-check.py [--max-loss 2.0] [URL ...]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls

# Hidden in print by design — see @media print in css/site/02-components.css.
CHROME = ("#nav,nav,footer,.menu-toggle,.skip-link,.dyslexia-toggle,.footer-back,"
          ".vid-frame,.nav-cta,#ckl-reset,.hire-print-note,.scr-print-note")

TEXT = ('(()=>{const m=document.querySelector("main,[role=main]")||document.body;'
        'return (m.innerText||"").replace(/\\s+/g," ").trim().length})()')

def strip_chrome(br):
    br.eval('(()=>{document.querySelectorAll(%r).forEach(e=>e.remove());return 1})()' % CHROME)

def selftest(br, url):
    """PLANT A DEFECT AND WATCH IT SCREAM. A check that has never gone red is not
    evidence, it is a hope. This hides a third of one page's paragraphs in print
    only — the exact shape of the defect this tool exists to catch — and requires
    the tool to notice. The rule is injected into the BROWSER, never written to a
    served file: a canary written into site.css was committed once, and a gate that
    can dirty the repo is a worse problem than the one it was checking for.
    """
    br.navigate(url, settle=1.6)
    strip_chrome(br)
    before = int(br.eval(TEXT))
    br.eval("""(()=>{const ps=[...document.querySelectorAll('main p, article p, p')];
        const n=Math.max(1,Math.floor(ps.length/3));
        ps.slice(0,n).forEach((e,i)=>e.classList.add('__plant'));
        const s=document.createElement('style');
        s.textContent='@media print{.__plant{display:none}}';
        document.head.appendChild(s); return n})()""")
    br.cmd("Emulation.setEmulatedMedia", media="print")
    br.pump(0.4)
    after = int(br.eval(TEXT))
    br.cmd("Emulation.setEmulatedMedia", media="screen")
    if before == 0:
        return False, "no prose found on the calibration page"
    loss = 100.0 * (before - after) / before
    return (loss > 2.0), f"a planted print-only hide cost {loss:.1f}% of the prose"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--max-loss', type=float, default=2.0,
                    help='percent of prose a page may lose in print before it is a defect')
    a = ap.parse_args()
    cdp.ensure_server(8000)
    urls = a.urls or page_urls(include_book=False)
    bad, rows = [], []
    with cdp.Browser() as br:
        br.viewport(1280, 900)
        ok, msg = selftest(br, urls[0])
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:
            print("Refusing to report results. An instrument that cannot fail is not evidence.")
            return 2
        for url in urls:
            br.viewport(1280, 900)
            br.navigate(url, settle=1.8)
            strip_chrome(br)
            screen = int(br.eval(TEXT))
            br.cmd("Emulation.setEmulatedMedia", media="print")
            br.pump(0.4)
            printed = int(br.eval(TEXT))
            br.cmd("Emulation.setEmulatedMedia", media="screen")
            if screen == 0:
                rows.append((url, screen, printed, None)); continue
            loss = round(100.0 * (screen - printed) / screen, 1)
            rows.append((url, screen, printed, loss))
            if loss > a.max_loss:
                bad.append((url, loss, screen - printed))
    for url, s, p, loss in rows:
        name = url.rsplit('/', 2)[-2] if url.endswith('/') else url.rsplit('/', 1)[-1]
        if loss is None:
            print(f"  {name:38s} NO PROSE FOUND — check the selector, not the page")
        elif loss > a.max_loss:
            print(f"  {name:38s} LOSES {loss:5.1f}%  ({s - p} of {s} characters)")
    print(f"\n{len(bad)} of {len(rows)} page(s) lose more than {a.max_loss}% of their prose in print")
    print("CANNOT SEE: text that prints but is clipped, runs off the paper, or is "
          "white-on-white; bad page breaks; text baked into an image.")
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
