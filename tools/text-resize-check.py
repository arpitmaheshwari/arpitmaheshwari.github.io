#!/usr/bin/env python3
"""text-resize-check.py — does the reader's own text-size setting actually work?

WHY. WCAG 1.4.4 asks that text can be enlarged to 200% without loss of content or
function. Until 2026-09-26 this site answered no, twice over: the root was pinned
with html{font-size:16px}, and 448 sizes were written in px, which ignores the root
anyway. A reader who had set larger text in their browser got the same page as
everyone else — silently, with nothing to tell them their setting had been overruled.

WHAT IT MEASURES, and it is two opposite things:
  IDENTICAL  at the default root, every sampled element must render at exactly the
             size it did before. A unit change that moves the page at 100% is not a
             unit change, it is a redesign.
  RESPONSIVE at a 200% root, body text must actually grow. A site can pass the first
             test by doing nothing at all, so the second is what proves the first
             was worth doing.

WHAT IT CANNOT SEE. Whether the enlarged page still LOOKS right — text can grow,
overflow its container, and pass every assertion here. That is what the render pass
and the reachability gate are for. Nor does it judge text inside an SVG, which is
sized by the artboard and not by the root.

USAGE  text-resize-check.py [--snapshot FILE] [--compare FILE] [URL ...]
       --snapshot writes the measurements; --compare diffs a page against them.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls

WIDTHS = (1440, 390)
PROBE = """(()=>{
  const out = {};
  const sel = ['h2','h3','.t-body','.lbl-eyebrow','.cta','.role-line','.bcard-m',
               '.nav-links a','footer','main p, article p, .t-body, main li, p'];
  for (const s of sel) {
    const e = document.querySelector(s);
    if (!e) continue;
    const cs = getComputedStyle(e);
    out[s] = [Math.round(parseFloat(cs.fontSize) * 100) / 100,
              Math.round(parseFloat(cs.lineHeight) * 100) / 100];
  }
  out['__scrollHeight'] = document.documentElement.scrollHeight;
  out['__scrollWidth']  = document.documentElement.scrollWidth;
  return JSON.stringify(out);
})()"""


# THE SENTINEL IS PROSE, NOT <body>. First version watched body and reported that
# 7 of 8 pages ignored the reader — while main p went 12px to 24px on the same page.
# On every page but the homepage nothing sets body's size and nothing inherits from
# it, because each component declares its own: body is a container, and a container
# that never changes is not evidence that the text didn't.
PROSE = ('main p, article p, .t-body, .case-body p, .prose p, main li, p')

def measure(br, url, width, standard=None):
    br.viewport(width, 900)
    if standard:
        # THE READER'S ACTUAL SETTING, not a JS style hack. Chrome's default font
        # size is the thing a person changes in Settings > Appearance; setting it
        # through the browser is the only version of this test that matches what a
        # reader does. (The JS hack agreed here, but it agrees for the wrong reason
        # on a page whose root is re-declared, and I would not know which I had.)
        br.cmd("Page.setFontSizes", fontSizes={"standard": standard, "fixed": max(10, standard - 3)})
    br.navigate(url, settle=1.6)
    if standard:
        br.pump(0.4)
    return br.eval_json(PROBE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--snapshot')
    ap.add_argument('--compare')
    a = ap.parse_args()
    cdp.ensure_server(8000)
    urls = a.urls or page_urls(include_book=False)[:8]

    data, grew, flat = {}, [], []
    with cdp.Browser() as br:
        for url in urls:
            for w in WIDTHS:
                data[f"{url}@{w}"] = measure(br, url, w)
            # THE SECOND TEST. A 200% root must actually move body text; if it does
            # not, the units are still absolute somewhere above it.
            base = measure(br, url, 1440, standard=16)
            big = measure(br, url, 1440, standard=32)
            measure(br, url, 1440, standard=16)          # leave the browser as found
            k = 'main p, article p, .t-body, main li, p'
            b0 = (base.get(k) or [0])[0]
            b1 = (big.get(k) or [0])[0]
            (grew if b1 > b0 * 1.5 else flat).append((url, b0, b1))

    if a.snapshot:
        json.dump(data, open(a.snapshot, 'w'), indent=1, sort_keys=True)
        print(f"  snapshot of {len(data)} page/width pair(s) -> {a.snapshot}")

    bad = []
    if a.compare:
        prev = json.load(open(a.compare))
        for k, now in data.items():
            was = prev.get(k)
            if not was:
                continue
            for sel, v in now.items():
                if sel.startswith('__'):
                    continue
                if was.get(sel) and was[sel][0] != v[0]:
                    bad.append(f"{k} {sel}: was {was[sel][0]}px, now {v[0]}px")
        print(f"  {len(bad)} size change(s) at the default root — expected 0")
        for b in bad[:25]:
            print(f"    {b}")

    for url, b0, b1 in flat:
        print(f"  DOES NOT RESPOND — {url}: prose {b0}px at a 16px setting, {b1}px at 32px")
    print(f"\n  {len(grew)} page(s) enlarge with the reader's setting, {len(flat)} do not")
    print("CANNOT SEE: whether the enlarged page still looks right — growth without "
          "overflow is the render pass's job, not this one's. Nor SVG text, sized by "
          "its artboard. Nor display headings whose clamp() is driven by viewport "
          "width: those are deliberately width-led and do not follow the reader.")
    return 1 if (bad or flat) else 0


if __name__ == '__main__':
    sys.exit(main())
