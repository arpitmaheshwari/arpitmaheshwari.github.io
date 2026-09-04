#!/usr/bin/env python3
"""Fail when content exists on the page but a reader cannot SEE it without a gesture.

WHY THIS EXISTS (2026-08-17)
Arpit opened /case-studies/adtech.html on a phone and saw a before/after table
showing only the BEFORE column. The table was min-width:640px inside a 294px
column with overflow-x:auto, so 346px of it — the entire "After" answer, the
whole point of the comparison — was parked behind a sideways scroll.

Every gate here was green, and each was right by its own question:
  * overflow-sweep asks "does content escape the VIEWPORT?" — content inside a
    scroll box does not escape. It hides. Opposite answers, same defect;
  * contrast-audit measures a glyph against its ground — an unreachable glyph
    still has excellent contrast;
  * overlap-check compares two elements' boxes — nothing is overlapping;
  * a11y-sweep reads the tree — the tree is complete. That is the problem: the
    content IS there, which is exactly why nothing noticed it wasn't visible.

REACHABILITY is its own property, and it is invisible to every gate that asks
about one element's own attributes.

WHAT IT MEASURES
For every element with its own text, the nearest ancestor that clips (overflow
x or y not visible). If the element's ink extends past that ancestor's client
box, the text is hidden until a gesture is made, and it reports:
  h-scroll / v-scroll   hidden behind a scroll INSIDE a box (auto|scroll)
  CLIPPED               overflow:hidden — no gesture recovers it at all

WHAT IT DELIBERATELY IGNORES
  * the page's own vertical scroll — that is reading, not a hidden gesture;
  * the 1px clip of .visually-hidden / skip links — that is a screen-reader
    affordance, deliberately not visible;
  * display:none / hidden / zero-opacity subtrees — not rendered, so this gate
    has no opinion; disclosure (menus, <details>) is a design, not a defect;
  * anything under an ALLOW class — a marquee or a deliberate carousel.

WIDTHS ARE MOBILE-FIRST (390 → 768 → 1024 → 1440). Narrow is where layouts
fail; desktop is the easy case and it goes last (Arpit, 2026-08-17:
"qa should be mobile first and exploratory").

USAGE  reachability-check.py [--all] [URL…] [--widths 390,768,1024,1440]
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
ALLOW = ["marquee", "ticker", "carousel-track"]
MIN_HIDDEN = 8      # px; below this is rounding and subpixel rendering

PROBE = r"""
(() => {
  const ALLOW = %s, MIN = %d;
  const inAllowed = el => {
    for (let n = el; n && n.tagName !== 'BODY'; n = n.parentElement) {
      const c = (n.className + '').toLowerCase();
      if (ALLOW.some(a => c.includes(a))) return true;
    }
    return false;
  };
  const hasText = el => [...el.childNodes]
    .some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
  const out = [];
  document.querySelectorAll('body *').forEach(el => {
    if (!hasText(el) || inAllowed(el)) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;

    // walk up to the nearest CLIPPING ancestor (root excluded: page scroll is reading)
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const ac = getComputedStyle(a);
      const ox = ac.overflowX, oy = ac.overflowY;
      const clipsX = ox !== 'visible', clipsY = oy !== 'visible';
      if (!clipsX && !clipsY) continue;
      const ar = a.getBoundingClientRect();
      // the .visually-hidden idiom: a 1px clip box. Deliberate, for screen readers.
      if (a.clientWidth <= 4 || a.clientHeight <= 4) break;

      const overRight  = clipsX ? Math.round(r.right  - (ar.left + a.clientWidth))  : 0;
      const overBottom = clipsY ? Math.round(r.bottom - (ar.top  + a.clientHeight)) : 0;
      const overLeft   = clipsX ? Math.round(ar.left - r.left) : 0;
      const hidX = Math.max(overRight, overLeft), hidY = overBottom;

      if (hidX >= MIN || hidY >= MIN) {
        const scrollable = h => h === 'auto' || h === 'scroll';
        const kind = hidX >= MIN
          ? (scrollable(ox) ? 'h-scroll' : 'CLIPPED')
          : (scrollable(oy) ? 'v-scroll' : 'CLIPPED');
        out.push({
          kind, hidden: Math.max(hidX, hidY),
          el: (el.tagName + '.' + ((el.className + '').trim().split(/\s+/)[0] || '')).slice(0, 30),
          box: (a.tagName + '.' + ((a.className + '').trim().split(/\s+/)[0] || '')).slice(0, 30),
          text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 52),
        });
      }
      break;   // nearest clipping ancestor only
    }
  });
  // ── SECOND PASS: the BOX itself ───────────────────────────────────────────
  // The per-element maths above compares an element's rect to its clipping
  // ancestor's client box, and that quietly fails when the ancestor carries a
  // transform (the breakout idiom `transform:translateX(-147px)` moves the
  // reference frame out from under the arithmetic). On /case-studies/fintech
  // it reported ONE hidden line where a screenshot showed a dozen: the whole
  // right edge of the deal-screening mockup was sliced off on a phone.
  // A box that scrolls more than it shows is the defect, whatever its
  // children measure — so ask the box directly. scrollWidth vs clientWidth
  // needs no reference frame and no transform correction.
  document.querySelectorAll('body *').forEach(a => {
    if (inAllowed(a)) return;
    const ac = getComputedStyle(a);
    if (ac.display === 'none' || ac.visibility === 'hidden') return;
    if (a.clientWidth <= 4) return;
    const overX = a.scrollWidth - a.clientWidth;
    if (overX < MIN) return;
    const scrollable = ac.overflowX === 'auto' || ac.overflowX === 'scroll';
    if (ac.overflowX === 'visible') return;   // not clipped: it just overflows, overflow-sweep's job
    // EVIDENCE REQUIRED. scrollWidth is inflated by things a reader never
    // misses: a transformed child, a decorative pseudo-element, an absolutely
    // positioned bleed. On /case-studies/fintech this pass claimed SECTION.recon
    // hid 172px CLIPPED — and not one text descendant was actually outside the
    // box. A gate that cries about invisible decoration teaches me to ignore it.
    // So: name a text-bearing descendant whose ink really is past the edge, or
    // say nothing.
    const boxRight = a.getBoundingClientRect().left + a.clientWidth;
    const proven = [...a.querySelectorAll('*')].some(d =>
      hasText(d) && d.getBoundingClientRect().right - boxRight >= MIN);
    if (!proven) return;
    out.push({
      kind: scrollable ? 'h-scroll' : 'CLIPPED', hidden: overX, box: 'BOX',
      el: (a.tagName + '.' + ((a.className + '').trim().split(/\s+/)[0] || '')).slice(0, 30),
      text: (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 52),
    });
  });

  const seen = new Set();
  return JSON.stringify(out.filter(o => {
    const k = o.el + '|' + o.box + '|' + o.kind;
    if (seen.has(k)) return false; seen.add(k); return true;
  }).sort((x, y) => y.hidden - x.hidden).slice(0, 14));
})()
"""

# Two canaries, because the gate makes two distinct claims. If either fails to
# go red the gate proves nothing about that half.
CANARY = ("<div id='__reach'>"
          "<div style='width:120px;overflow-x:auto'>"
          "<p style='width:700px;margin:0'>CANARY SCROLL hidden behind a sideways scroll</p></div>"
          "<div style='width:120px;height:20px;overflow:hidden'>"
          "<p style='width:700px;margin:0'>CANARY CLIP unreachable by any gesture</p></div>"
          "</div>")


def run(urls, widths):
    # one shared harness — see tools/cdp.py. This file used to carry its own
    # ~110 lines of launch + websocket + cmd(), as did four other gates.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from cdp import Browser
    br = Browser(port_base=9930)
    cmd = br.cmd
    try:

        probe = PROBE % (json.dumps(ALLOW), MIN_HIDDEN)

        # ── calibration: plant both defects, require RED on both, then remove ──
        cmd("Emulation.setDeviceMetricsOverride", width=390, height=900,
            deviceScaleFactor=1, mobile=True)
        nav = cmd("Page.navigate", url=urls[0]); time.sleep(2.0)
        # calibrate on a page that actually loaded, or the whole run is theatre
        if nav.get("errorText"):
            print(f"[calibration] FAILED — {urls[0]} did not load ({nav['errorText']}). "
                  "Is the server on :8000 up?")
            return 2
        cmd("Runtime.evaluate", returnByValue=True, expression=(
            "(()=>{const d=document.createElement('div');"
            f"d.innerHTML={json.dumps(CANARY)};document.querySelector('main,body').prepend(d);return 1}})()"))
        time.sleep(.3)
        got = json.loads(cmd("Runtime.evaluate", expression=probe,
                             returnByValue=True)["result"]["value"])
        blob = json.dumps(got)
        caught_scroll = "CANARY SCROLL" in blob and any(g["kind"] == "h-scroll" for g in got)
        caught_clip = "CANARY CLIP" in blob and any(g["kind"] == "CLIPPED" for g in got)
        cmd("Runtime.evaluate", expression="document.getElementById('__reach').remove()")
        if not (caught_scroll and caught_clip):
            print(f"[calibration] FAILED — scroll:{caught_scroll} clip:{caught_clip}. "
                  "This gate proves nothing.")
            return 2
        print("[calibration] PASS — planted h-scroll AND clip both flagged")

        bad = 0
        for u in urls:
            for w in widths:
                cmd("Emulation.setDeviceMetricsOverride", width=w, height=900,
                    deviceScaleFactor=1, mobile=w < 700)
                cmd("Page.navigate", url=u); time.sleep(1.7)
                cmd("Runtime.evaluate", awaitPromise=True, expression=(
                    "(async()=>{const h=document.body.scrollHeight;"
                    "for(let y=0;y<h;y+=500){scrollTo(0,y);await new Promise(r=>setTimeout(r,12));}"
                    "scrollTo(0,0);await new Promise(r=>setTimeout(r,140));})()"))
                # DID THE PAGE ACTUALLY LOAD? Without this, a dead server is a
                # clean bill of health: Chrome's error page has a <body>, the
                # probe finds no clipped text in it, and every URL prints "ok".
                # The calibration canary does not catch this either — it plants
                # into `main,body`, which the error page also has. Found on
                # 2026-08-17 when :8000 died mid-session and a 180-combination
                # sweep came back green. An empty result must mean "looked and
                # found nothing", never "there was nothing to look at".
                # Body LENGTH was the first attempt at this and was wrong: it
                # called a 114-char OG-image template a dead server. The
                # navigation's own errorText is the size-blind signal.
                if nav.get("errorText"):
                    print(f"LOAD FAILURE {u} @{w} — {nav['errorText']}")
                    print("  Refusing to report a verdict on a page that did not load. "
                          "Is the server on :8000 up?")
                    return 2

                hits = json.loads(cmd("Runtime.evaluate", expression=probe,
                                      returnByValue=True)["result"]["value"])
                tag = f'{u.split("8000")[-1] or "/"} @{w}'
                if hits:
                    bad += len(hits)
                    print(f"FAIL {tag}")
                    for h in hits:
                        print(f"       {h['hidden']:>4}px {h['kind']:<8} {h['el']} inside {h['box']}")
                        print(f"            {h['text']!r}")
                else:
                    print(f"ok   {tag}")
        print()
        print(f"{bad} unreachable text element(s).")
        print("CANNOT SEE: content behind INTERACTION (closed menus, tabs, <details>, "
              "carousel slides past the first) — those are not rendered on load, so this "
              "gate has no opinion on them. Drive them by hand.")
        return 1 if bad else 0
    finally:
        br.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--widths", default="390,768,1024,1440")   # mobile FIRST
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
