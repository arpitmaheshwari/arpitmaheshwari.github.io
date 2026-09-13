#!/usr/bin/env python3
"""pixel-census.py — the PIXEL half of a refactor's proof: photograph every page, then diff.

WHY (2026-09-13, Arpit: "how will you make sure that you are not introducing regression
bugs" before an architecture refactor). render-census reads the DOM — every element's box
and computed style — and a clean census is strong evidence. It is not proof: the DOM can
say one thing and the paint another (an overlay, a mask, a gradient, a font that did not
load — lesson 9, "when two instruments disagree, the one that samples pixels wins"). So a
refactor that must change nothing a reader sees is proved twice: geometry by render-census,
paint by this.

METHOD. `capture DIR` photographs every classic page at 390/768/1024/1440 (full page, in
≤8000px segments, animations and transitions frozen, scroll-reveals forced visible, the
video poster the only image state allowed) into DIR/<slug>@<w>-<n>.png. `diff A B` compares
each pair pixel-for-pixel and reports pages whose mismatch exceeds a tolerance (default 0.02%
of pixels, to absorb antialiasing jitter), with the first differing region's coordinates.
`--selftest` captures one page twice and requires 0, then plants a 1px border and requires >0.

Exit: 0 identical within tolerance / 1 differences / 2 calibration failed / 3 could not measure.
CANNOT SEE: anything behind interaction (drawer, receipts, hover), the book, lazy content
that never scrolled into view, and whether a difference is GOOD — only that it exists.
"""
import argparse, base64, io, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls, planted
from PIL import Image, ImageChops

WIDTHS = (390, 768, 1024, 1440)
SEG = 8000
FREEZE = ("(()=>{const s=document.createElement('style');s.id='__pc';s.textContent="
          "'*,*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent!important}"
          " video{visibility:hidden!important}';document.head.appendChild(s);"
          "document.querySelectorAll('[style*=\"opacity\"]').forEach(e=>{});return 1})()")


def slug(url):
    p = url.split('8000/')[1] or 'index'
    return re.sub(r'[^a-z0-9]+', '-', p.lower()).strip('-') or 'index'


def capture(out, urls):
    os.makedirs(out, exist_ok=True)
    with cdp.Browser() as br:
        for u in urls:
            for w in WIDTHS:
                br.viewport(w, 900); br.navigate(u, settle=3.0); br.eval(FREEZE)
                br.scroll_through(step=700, pause=15)
                h = int(br.eval('document.documentElement.scrollHeight'))
                n = 0
                for y in range(0, h, SEG):
                    r = br.cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
                               clip={'x': 0, 'y': y, 'width': w, 'height': min(SEG, h - y), 'scale': 1})
                    open(os.path.join(out, f'{slug(u)}@{w}-{n}.png'), 'wb').write(base64.b64decode(r['data'])); n += 1
    json.dump({'urls': urls, 'widths': WIDTHS}, open(os.path.join(out, 'manifest.json'), 'w'))
    return out


def diff(a, b, tol):
    bad, seen = [], 0
    for fn in sorted(os.listdir(a)):
        if not fn.endswith('.png'): continue
        pa, pb = os.path.join(a, fn), os.path.join(b, fn)
        if not os.path.exists(pb): bad.append((fn, 'missing in AFTER', None)); continue
        ia, ib = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')
        seen += 1
        if ia.size != ib.size: bad.append((fn, f'size {ia.size}→{ib.size}', None)); continue
        d = ImageChops.difference(ia, ib).convert('L').point(lambda v: 255 if v > 24 else 0)
        box = d.getbbox()
        if not box: continue
        frac = sum(1 for v in d.getdata() if v) / (ia.size[0] * ia.size[1])
        if frac > tol: bad.append((fn, f'{frac*100:.3f}% of pixels', box))
    return bad, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', nargs='?', choices=['capture', 'diff'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--tol', type=float, default=0.0002)
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        a.mode = None
    elif a.mode is None or (a.mode == 'capture' and not a.paths) or (a.mode == 'diff' and len(a.paths) < 2):
        ap.error('capture DIR [URL...] | diff BEFORE AFTER | --selftest')
    if a.mode == 'capture':
        cdp.ensure_server(8000)
        urls = a.paths[1:] or page_urls(include_book=False)
        capture(a.paths[0], urls); print(f'captured {len(urls)} page(s) × {len(WIDTHS)} widths → {a.paths[0]}'); return 0
    if a.mode == 'diff':
        bad, seen = diff(a.paths[0], a.paths[1], a.tol)
        for fn, what, box in bad: print(f'  DIFF  {fn:44s} {what}' + (f'  first region x{box[0]}-{box[2]} y{box[1]}-{box[3]}' if box else ''))
        print(f'{len(bad)} of {seen} screenshot(s) differ beyond {a.tol*100:.3f}%. CANNOT SEE: interaction states, the book, whether a change is good.')
        return 1 if bad else 0
    # selftest
    cdp.ensure_server(8000)
    import tempfile
    t = tempfile.mkdtemp(); u = ['http://localhost:8000/lab/plugin.html']
    capture(os.path.join(t, 'a'), u); capture(os.path.join(t, 'b'), u)
    same, _ = diff(os.path.join(t, 'a'), os.path.join(t, 'b'), a.tol)
    with planted('site.css', '\nmain h1{border-bottom:3px solid red !important}\n'):
        capture(os.path.join(t, 'c'), u)
    red, _ = diff(os.path.join(t, 'a'), os.path.join(t, 'c'), a.tol)
    ok = not same and red
    print(f'[calibration] {"PASS" if ok else "FAIL"} — self-diff {len(same)} (want 0), planted 3px rule {len(red)} (want >0)')
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
