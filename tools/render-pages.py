#!/usr/bin/env python3
"""render-pages.py — full-page renders of every page at every width, to LOOK at.

WHY. The layout rule is "render the full affected section and LOOK at it before
showing Arpit", and QA is mobile-first: 390 → 768 → 1024 → 1440. A pane screenshot at
half scale is not looking. This writes one PNG per page per width, tall pages split
into segments, into prototypes/renders/<name>/ — inside the repo, because renders
Arpit will view never live only in a session scratchpad.

Two traps this file already knows about (both recorded in memory after they cost a
round each):
  * Page.captureScreenshot's clip is in DOCUMENT coordinates and needs
    captureBeyondViewport, or the camera stays aimed at the top of the document while
    the page is scrolled and the shot comes back black.
  * beyond-viewport captures wrap past 16,384px, so a 27,000px phone page is taken in
    segments no taller than 16,000px and stitched by filename, not by pixel.

USAGE  render-pages.py NAME [--widths 390,768,1024,1440] [URL ...]
       writes prototypes/renders/NAME/<slug>@<w>[-<n>].png
"""
import argparse, base64, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEG = 16000
FREEZE = ("(()=>{const s=document.createElement('style');s.textContent="
          "'*,*::before,*::after{transition:none!important;animation-duration:0s!important;"
          "animation-delay:0s!important}';document.head.appendChild(s);return true})()")


def slug(url):
    s = re.sub(r'^https?://[^/]+/', '', url).strip('/') or 'index'
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s)


def render(br, url, width, outdir):
    br.viewport(width, 900)
    br.navigate(url, settle=3.0)
    br.eval(FREEZE)
    br.scroll_through(step=600, pause=8)
    br.eval("scrollTo(0,0)")
    time.sleep(0.2)
    h = int(br.eval("Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)"))
    n = 0
    for y in range(0, h, SEG):
        seg_h = min(SEG, h - y)
        r = br.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                   clip={"x": 0, "y": y, "width": width, "height": seg_h, "scale": 1})
        suffix = f"-{n}" if h > SEG else ""
        fn = os.path.join(outdir, f"{slug(url)}@{width}{suffix}.png")
        with open(fn, 'wb') as fh:
            fh.write(base64.b64decode(r["data"]))
        n += 1
    return h, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--widths', default='390,768,1024,1440')
    a = ap.parse_intermixed_args()
    cdp.ensure_server(8000)
    outdir = os.path.join(ROOT, 'prototypes', 'renders', a.name)
    os.makedirs(outdir, exist_ok=True)
    urls = a.urls or page_urls(include_book=False)
    widths = [int(w) for w in a.widths.split(',')]
    with cdp.Browser() as br:
        for url in urls:
            for w in widths:
                h, n = render(br, url, w, outdir)
                print(f"  {slug(url):44s} @{w:<5} {h:6d}px  {n} file(s)")
    print(f"renders -> {os.path.relpath(outdir, ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
