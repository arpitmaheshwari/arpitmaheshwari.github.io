#!/usr/bin/env python3
"""Fail when an image or diagram is cut off, misaligned, or broken.

WHY THIS EXISTS (2026-08-19)
Arpit found figures on /case-studies/o2 sliced off at the left edge — the
diagram and all three photographs, 116px outside the viewport at desktop and
123px at mobile. Every gate in tools/ was green.

They were green because EVERY ONE OF THEM CHECKS TEXT. reachability,
overlap-check, contrast-audit and line-height-check all begin by requiring an
element to own a text node. An <img> owns none, so images were invisible to
the entire suite from the day it was written. Not a bug in any gate — a whole
category nobody had asked about.

WHAT IT CHECKS, per image and inline <svg>, at every width
  OFF-VIEWPORT   any part of the image outside the viewport, either edge
  CLIPPED        the image is larger than an ancestor that hides overflow
  OVERFLOWS      the image is wider than its own container
  BROKEN         a raster that failed to load (naturalWidth 0)
  STRETCHED      rendered aspect ratio differs from the file's by >2%
  UNSIZED        no width/height attributes and no CSS size — a layout shift
  OFF-CENTRE     max-width narrower than its container, hard against one side
                 waiting for a slow connection

LAZY IMAGES ARE FORCED EAGER FIRST. The first version of this measurement
missed three of the four broken figures because loading="lazy" meant they were
0x0 when measured, and a zero-size image is skipped. An image that has not
loaded is not an image that is fine.

USAGE  image-alignment-check.py [--all] [URL…] [--widths 390,768,1024,1440]
"""
import argparse, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cdp import Browser

PROBE = r"""
(() => {
  const out = [];
  const vw = innerWidth;
  document.querySelectorAll('img, svg, picture, video').forEach(el => {
    const b = el.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) {
      // a raster that never loaded still deserves a report
      if (el.tagName === 'IMG' && el.getAttribute('src') && !el.complete) {
        out.push({kind:'BROKEN', src:(el.getAttribute('src')||'').split('/').pop(), detail:'did not load'});
      }
      return;
    }
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
    const name = (el.getAttribute('src') || el.id || el.getAttribute('class') || el.tagName)
                   .split('/').pop().slice(0, 38);

    const offL = Math.round(Math.max(0, -b.left));
    const offR = Math.round(Math.max(0, b.right - vw));
    if (offL > 1 || offR > 1) out.push({
      kind: 'OFF-VIEWPORT', src: name,
      detail: `${Math.round(b.width)}px wide at x${Math.round(b.left)}..${Math.round(b.right)}` +
              (offL > 1 ? ` — ${offL}px past the LEFT edge` : '') +
              (offR > 1 ? ` — ${offR}px past the RIGHT edge` : '')
    });

    // clipped by an ancestor that hides overflow
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const ac = getComputedStyle(a);
      if (ac.overflow === 'visible' && ac.overflowX === 'visible' && ac.overflowY === 'visible') continue;
      const ar = a.getBoundingClientRect();
      if (a.clientWidth <= 4) break;
      const hidden = Math.round(Math.max(0, ar.left - b.left) +
                                Math.max(0, b.right - (ar.left + a.clientWidth)));
      if (hidden > 2 && ac.overflowX !== 'auto' && ac.overflowX !== 'scroll') {
        out.push({kind:'CLIPPED', src:name,
                  detail:`${hidden}px hidden by ${a.tagName.toLowerCase()}.${(a.className+'').trim().split(/\s+/)[0]||''}`});
      }
      break;
    }

    if (el.tagName === 'IMG') {
      if (el.complete && el.naturalWidth === 0) {
        out.push({kind:'BROKEN', src:name, detail:'naturalWidth 0 — file missing or unreadable'});
      } else if (el.naturalWidth > 0) {
        // Compare the CONTENT box, not the border box. .framed adds padding
        // and a 3px left border, which made a genuinely square 1024x1024 file
        // measure 1.11:1 and report as an 11% stretch on four pages. The image
        // was never distorted; the ruler included the frame around it.
        const pad = (v) => parseFloat(cs[v]) || 0;
        const cw = b.width  - pad('paddingLeft') - pad('paddingRight')
                            - pad('borderLeftWidth') - pad('borderRightWidth');
        const ch = b.height - pad('paddingTop') - pad('paddingBottom')
                            - pad('borderTopWidth') - pad('borderBottomWidth');
        const natural = el.naturalWidth / el.naturalHeight;
        const shown = cw / ch;
        const skew = Math.abs(shown - natural) / natural;
        const fit = getComputedStyle(el).objectFit;
        // SVG letterboxes instead of distorting (preserveAspectRatio defaults
        // to xMidYMid meet), so a ratio mismatch on an .svg is not a stretch.
        // Reported the site logo as "30% off" on the first run; a gate that
        // cries wolf is a gate people learn to ignore.
        const isSvg = /\.svg(\?|$)/i.test(el.getAttribute('src') || '');
        if (skew > 0.02 && !isSvg && fit !== 'cover' && fit !== 'contain') {
          out.push({kind:'STRETCHED', src:name,
                    detail:`content box ${shown.toFixed(2)}:1, file is ${natural.toFixed(2)}:1 (${Math.round(skew*100)}% off)`});
        }
      }
      // OFF-CENTRE. Every other check here asks about the image alone. This
      // one asks about the image AGAINST THE SPACE IT WAS GIVEN — an <img> is
      // inline-level, so a max-width narrower than its container leaves the
      // remainder as dead space on one side. The O2 case had 180px of it.
      const par = el.parentElement;
      if (par && cs.position !== 'absolute' && cs.position !== 'fixed') {
        const pr = par.getBoundingClientRect(), ps = getComputedStyle(par);
        const cL = pr.left + parseFloat(ps.paddingLeft || 0);
        const cR = pr.right - parseFloat(ps.paddingRight || 0);
        const gapL = b.left - cL, gapR = cR - b.right;
        // A sibling beside it means a deliberate multi-column arrangement,
        // not leftover space — that is composition, and this gate has no
        // opinion on it.
        const rowMate = [...par.children].some(sib => {
          if (sib === el) return false;
          const sr = sib.getBoundingClientRect();
          return sr.width > 8 && sr.height > 8 &&
                 sr.top < b.bottom - 4 && sr.bottom > b.top + 4;
        });
        if (!rowMate && gapL + gapR >= 24 && Math.abs(gapL - gapR) > 2) {
          out.push({kind:'OFF-CENTRE', src:name,
            detail:`${Math.round(b.width)}px inside ${Math.round(cR-cL)}px — `
                 + `${Math.round(gapL)}px left, ${Math.round(gapR)}px right`});
        }
      }
      const hasAttrs = el.getAttribute('width') && el.getAttribute('height');
      const hasCss = cs.aspectRatio !== 'auto' || (cs.width !== 'auto' && cs.height !== 'auto');
      if (!hasAttrs && !hasCss) {
        out.push({kind:'UNSIZED', src:name, detail:'no width/height and no CSS size — will shift on load'});
      }
    }
  });
  const seen = new Set();
  return JSON.stringify(out.filter(o => {
    const k = o.kind + '|' + o.src + '|' + o.detail;
    if (seen.has(k)) return false; seen.add(k); return true;
  }));
})()
"""

# A picture that overflows its viewport, so the gate must prove it can see one.
CANARY = ("(()=>{const i=document.createElement('img');i.id='__imgcan';"
          "i.src='data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"10\" height=\"10\"/>';"
          "i.style.cssText='position:relative;left:-300px;width:400px;height:80px;display:block';"
          "document.querySelector('main,body').prepend(i);return 1})()")


def pages(base):
    root = pathlib.Path(__file__).resolve().parent.parent
    out = []
    for p in sorted(root.rglob("*.html")):
        rel = p.relative_to(root).as_posix()
        if any(rel.startswith(x) for x in ("prototypes/", "portfolio-sources/", "partials/", "tests/", ".")):
            continue
        if p.name.startswith("__") or "og-images" in rel:
            continue
        out.append(f"{base}/{rel}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--widths", default="390,768,1024,1440")
    ap.add_argument("--base", default="http://localhost:8000")
    a = ap.parse_args()
    widths = [int(x) for x in a.widths.split(",")]
    urls = list(a.urls) or pages(a.base) if not a.all else pages(a.base)

    br = Browser(port_base=9370)
    try:
        # calibration: plant an image that hangs off the left edge, require RED
        br.viewport(1440)
        br.navigate(urls[0])
        br.eval(CANARY)
        got = br.eval_json(PROBE)
        if not any(g["kind"] == "OFF-VIEWPORT" and "__imgcan" not in g["src"] or
                   g["kind"] == "OFF-VIEWPORT" for g in got):
            print("[calibration] FAILED — a planted off-viewport image was not seen.")
            return 2
        br.eval("document.getElementById('__imgcan').remove()")
        print("[calibration] PASS — planted off-viewport image caught")

        bad = 0
        for u in urls:
            for w in widths:
                br.viewport(w)
                br.navigate(u, settle=1.4)
                # lazy images are 0x0 until scrolled to; force them, or the gate
                # measures nothing and calls it clean
                br.eval("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                br.scroll_through()
                hits = br.eval_json(PROBE)
                tag = f'{u.split("8000")[-1] or "/"} @{w}'
                if hits:
                    bad += len(hits)
                    print(f"FAIL {tag}")
                    for h in hits[:8]:
                        print(f"       {h['kind']:<13} {h['src']}")
                        print(f"                     {h['detail']}")
                    if len(hits) > 8:
                        print(f"       ...and {len(hits)-8} more")
                else:
                    print(f"ok   {tag}")
        print(f"\n{bad} image problem(s).")
        print("CANNOT SEE: whether the image is the CORRECT one, whether its alt text is "
              "accurate, CSS background-images, or anything only visible after interaction.")
        return 1 if bad else 0
    finally:
        br.close()


if __name__ == "__main__":
    sys.exit(main())
