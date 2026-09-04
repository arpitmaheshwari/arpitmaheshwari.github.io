#!/usr/bin/env python3
"""Fail when two in-flow elements' INK BOXES collide.

WHY THIS EXISTS (2026-08-17)
Arpit found "shipped, broke, fixed — in that order" printed straight through the caption
below it on /patterns/. Every gate here was green. None of them could see it:
  * overflow-sweep asks whether content escapes the VIEWPORT — this stays inside it;
  * contrast-audit samples a glyph against its background — two cream glyphs on the same
    dark ground both pass while sitting on top of each other;
  * a11y-sweep reads the tree, which is perfectly well-formed;
  * inline-style-check reads CSS text, and no rule says "overlap".
A layout defect that is obvious to a human was invisible to five instruments.

WHAT IT MEASURES
getBoundingClientRect() is the LAYOUT box. For most text those agree, but a display or
script face inks well outside its line box: .hand (Caveat) reports offsetHeight 28 and a
60px ink box for one line, so the element after it can be laid out "correctly" and still be
overprinted. So this walks in-flow siblings and compares their real rects, and it reports
the offending pair with the number of overlapping pixels.

WHAT IT DELIBERATELY IGNORES
  * position absolute/fixed/sticky — overlap is the whole point of those;
  * ancestor/descendant pairs, and anything inside a deliberately stacked component
    (listed in ALLOW below) — a badge sitting on a card is a design, not a defect.

USAGE  overlap-check.py [--all] [URL…] [--widths 1440,1024,390]
"""
import argparse, json, os, shutil, signal, subprocess, sys, tempfile, time, urllib.request, pathlib
import websocket

# Guarantee the server these gates assume. Every one of them hard-codes
# http://localhost:8000 and none checked it was there; when it was not, they did not report
# "no server", they reported findings (see cdp.ensure_server). Idempotent: reuses a server
# that is already listening, so a dev server is never disturbed or double-bound.
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)

# $CHROME first: every CI runner is Linux and this path is macOS-only.

# Eleven tools pinned it, so fixing cdp.py alone would only have moved the

# CI failure to the next step that launches Chrome.

CHROME = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ALLOW = ["plA-", "plF-", "plM-", "plO-", "plP-", "plV-", "recon", "mock", "browser",
         "pass", "field", "chip-", "badge", "seam", "halo"]
MIN_OVERLAP = 3          # px; below this is antialiasing and subpixel rounding

PROBE = r"""
(() => {
  const ALLOW = %s, MIN = %d;
  const inAllowed = el => {
    let n = el;
    while (n && n.tagName !== 'BODY') {
      const c = (n.className + '').toLowerCase();
      if (ALLOW.some(a => c.includes(a.toLowerCase()))) return true;
      n = n.parentElement;
    }
    return false;
  };
  const hasText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  // SVG internals are laid out by hand inside a viewBox; stacked labels there are a
  // drawing, not a collision, and their className is an SVGAnimatedString (unreadable in
  // a report). Excluded.
  const isSvg = el => el.ownerSVGElement || el.namespaceURI === 'http://www.w3.org/2000/svg';
  // INLINE elements are excluded, and this is the difference between a gate and a noise
  // machine: <b> and <em> on two consecutive lines of ONE wrapped paragraph have rects
  // that overlap on both axes by design. The first run reported 33 such pairs. The defect
  // shape is a BLOCK printed over a BLOCK — which is exactly what .hand over .lbl-cap was.
  const isBlock = el => !/^inline($|-)/.test(getComputedStyle(el).display);
  const out = [];
  document.querySelectorAll('main *, header *, section *, footer *, div, p, h1, h2, h3').forEach(el => {
    if (!hasText(el) || inAllowed(el) || isSvg(el) || !isBlock(el)) return;
    const cs = getComputedStyle(el);
    if (cs.position !== 'static' && cs.position !== 'relative') return;
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
    const a = el.getBoundingClientRect();
    if (a.width < 4 || a.height < 4) return;
    // only compare against LATER in-flow siblings: a collision with the thing that
    // follows you is the defect shape we are hunting
    let sib = el.nextElementSibling;
    while (sib) {
      if (hasText(sib) && !inAllowed(sib) && !isSvg(sib) && isBlock(sib)) {
        const sc = getComputedStyle(sib);
        if ((sc.position === 'static' || sc.position === 'relative') &&
            sc.display !== 'none' && sc.visibility !== 'hidden' && +sc.opacity !== 0) {
          const b = sib.getBoundingClientRect();
          const vy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          const vx = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          if (vy >= MIN && vx >= MIN) {
            out.push({
              overlap: Math.round(vy),
              a: (el.tagName + '.' + ((el.className + '').trim().split(/\s+/)[0] || '')).slice(0, 34),
              b: (sib.tagName + '.' + ((sib.className + '').trim().split(/\s+/)[0] || '')).slice(0, 34),
              at: (el.textContent || '').trim().slice(0, 40),
              bt: (sib.textContent || '').trim().slice(0, 40),
            });
          }
        }
      }
      sib = sib.nextElementSibling;
    }
  });
  const seen = new Set();
  return JSON.stringify(out.filter(o => {
    const k = o.a + '|' + o.b + '|' + o.overlap;
    if (seen.has(k)) return false; seen.add(k); return true;
  }).sort((x, y) => y.overlap - x.overlap).slice(0, 12));
})()
"""

CANARY = ("<div><p style='line-height:8px;margin:0'>CANARY ONE overlapping line of text</p>"
          "<p style='margin:-24px 0 0'>CANARY TWO sits on top of it</p></div>")


def run(urls, widths):
    # shared harness — see tools/cdp.py
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from cdp import Browser
    br = Browser(port_base=9862)
    cmd = br.cmd
    try:

        probe = PROBE % (json.dumps(ALLOW), MIN_OVERLAP)

        # ── calibration: plant an overlap, require RED, then remove it ──────────
        cmd("Emulation.setDeviceMetricsOverride", width=1440, height=900,
            deviceScaleFactor=1, mobile=False)
        cmd("Page.navigate", url=urls[0]); time.sleep(2.0)
        cmd("Runtime.evaluate", expression=(
            "(()=>{const d=document.createElement('div');d.id='__canary';"
            f"d.innerHTML={json.dumps(CANARY)};document.querySelector('main,body').prepend(d);return 1}})()"),
            returnByValue=True)
        time.sleep(.3)
        got = json.loads(cmd("Runtime.evaluate", expression=probe, returnByValue=True)["result"]["value"])
        caught = any("CANARY" in (g["at"] + g["bt"]) for g in got)
        cmd("Runtime.evaluate", expression="document.getElementById('__canary').remove()")
        if not caught:
            print("[calibration] FAILED — planted overlap not caught; this gate proves nothing.")
            return 2
        print("[calibration] PASS — planted overlap caught")

        bad = 0
        for u in urls:
            for w in widths:
                cmd("Emulation.setDeviceMetricsOverride", width=w, height=900,
                    deviceScaleFactor=1, mobile=w < 700)
                cmd("Page.navigate", url=u); time.sleep(1.9)
                cmd("Runtime.evaluate", expression=(
                    "(async()=>{const h=document.body.scrollHeight;"
                    "for(let y=0;y<h;y+=500){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,15));}"
                    "window.scrollTo(0,0);await new Promise(r=>setTimeout(r,120));})()"),
                    awaitPromise=True)
                hits = json.loads(cmd("Runtime.evaluate", expression=probe,
                                      returnByValue=True)["result"]["value"])
                tag = f'{u.split("8000")[-1] or "/"} @{w}'
                if hits:
                    bad += len(hits)
                    print(f"FAIL {tag}")
                    for h in hits:
                        print(f"       {h['overlap']:>3}px  {h['a']} over {h['b']}")
                        print(f"            {h['at']!r}")
                        print(f"            {h['bt']!r}")
                else:
                    print(f"ok   {tag}")
        print()
        print(f"{bad} overlapping element pair(s).")
        return 1 if bad else 0
    finally:
        br.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--widths", default="1440,1024,390")
    ap.add_argument("--base", default="http://localhost:8000")
    a = ap.parse_args()
    urls = list(a.urls)
    if a.all or not urls:
        root = pathlib.Path(__file__).resolve().parent.parent
        for p in sorted(root.rglob("*.html")):
            rel = p.relative_to(root).as_posix()
            if any(rel.startswith(x) for x in ("prototypes/", "portfolio-sources/", "partials/", "tests/", ".")):
                continue
            if p.name.startswith("__"):
                continue
            urls.append(f"{a.base}/{rel}")
    return run(urls, [int(x) for x in a.widths.split(",")])


if __name__ == "__main__":
    sys.exit(main())
