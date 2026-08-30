#!/usr/bin/env python3
"""Fail when WRAPPED text is set too tight to read comfortably.

WHY THIS EXISTS (2026-08-18)
Arpit pointed at two headings on the homepage and said the line height looked
tight. Measured: the hero h1 is ratio 1.01 — 38px type with 38.4px of leading,
which is solid-set. On a phone it wraps to three lines and the descenders of
one line run at the ascenders of the next. Every h2 on the site is 1.12.

No gate here had an opinion on leading. contrast-audit measures a glyph against
its ground, overlap-check compares two ELEMENTS (not two line boxes inside one
element), reachability asks whether text is visible at all. Text can be perfectly
contrasting, fully reachable, non-overlapping — and still set too tight to read.

WHAT IT MEASURES
Rendered line-height / rendered font-size, per element, at four widths, and
ONLY for elements that actually wrap to 2+ lines at that width. Leading is
invisible on a single line, so a tight <button> or a one-line eyebrow is not a
defect and reporting it would be noise. The line count comes from a Range over the
element's own text nodes — one client rect per rendered line — because
height/lineHeight counts padding as leading and flagged one-line buttons.

THRESHOLDS (floors, by rendered size — bigger type needs proportionally less)
    >= 40px  display   1.05
    24-40px  heading   1.15
    18-24px  subhead   1.25
    < 18px   body/UI   1.40
These are floors, not targets. A floor says "below this it is a defect", it does
not say the value above it is well chosen.

IT ALSO REPORTS DRIFT: the same component (tag + first class) set at different
ratios on different pages. A site with one type system has one answer per
component; see the .nav-links precedent, where links inherited each page's body
line-height and computed 21.45px on one page and 22.1px on the rest.

COVERS the classic site AND /book/ — they are separate stylesheets and the book
was never audited for this.

USAGE  line-height-check.py [--all] [URL…] [--widths 390,768,1024,1440]
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

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# leading is a deliberate design choice inside these: a printed-docket metaphor,
# a code block set to a fixed grid, or a mark drawn as type.
ALLOW = ["rcpt", "rcell", "rfoot", "stamp", "boarding", "lab-code", "nav-logo",
         "footer-logo", "plF-", "plA-", "plM-", "plO-", "plP-", "plV-"]

PROBE = r"""
(() => {
  const ALLOW = %s;
  const floorFor = fs => fs >= 40 ? 1.05 : fs >= 24 ? 1.15 : fs >= 18 ? 1.25 : 1.40;
  const inAllowed = el => {
    for (let n = el; n && n.tagName !== 'BODY'; n = n.parentElement) {
      const c = (n.className + '').toLowerCase();
      if (ALLOW.some(a => c.includes(a.toLowerCase()))) return true;
    }
    return false;
  };
  const hasText = el => [...el.childNodes]
    .some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
  const tight = [], census = {};
  document.querySelectorAll('body *').forEach(el => {
    if (!hasText(el) || inAllowed(el)) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return;
    const fs = parseFloat(cs.fontSize);
    let lh = parseFloat(cs.lineHeight);
    if (!isFinite(lh)) lh = fs * 1.2;          // 'normal' — the browser's own guess
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    // LINE COUNT FROM THE TEXT ITSELF, not from the box. height/lineHeight
    // counts PADDING as leading: a one-line <button> with 12px of vertical
    // padding reported 3 lines and "Send me the role" was flagged as tight
    // text. A Range over the element's OWN text nodes yields one client rect
    // per rendered line fragment; distinct tops are the real line count, and
    // children's rects never enter it.
    let tops = new Set();
    [...el.childNodes].forEach(n => {
      if (n.nodeType !== 3 || !n.textContent.trim()) return;
      const rg = document.createRange(); rg.selectNodeContents(n);
      [...rg.getClientRects()].forEach(q => { if (q.width > 1) tops.add(Math.round(q.top)); });
    });
    const lines = tops.size;
    const ratio = lh / fs;
    const sig = el.tagName.toLowerCase() + '.' + ((el.className + '').trim().split(/\s+/)[0] || '');
    // census records EVERY element, wrapped or not — drift is a system fault
    // whether or not this particular instance happens to wrap today.
    (census[sig] = census[sig] || {})[ratio.toFixed(2)] = true;
    if (lines < 2) return;                      // leading is invisible on one line
    const floor = floorFor(fs);
    if (ratio < floor - 0.005) {
      tight.push({ sig, lines, fs: +fs.toFixed(1), lh: +lh.toFixed(1),
        ratio: +ratio.toFixed(3), floor,
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 46) });
    }
  });
  const seen = new Set();
  const uniq = tight.filter(t => {
    const k = t.sig + '|' + t.ratio;
    if (seen.has(k)) return false; seen.add(k); return true;
  }).sort((a, b) => a.ratio - b.ratio);
  const cen = {};
  Object.keys(census).forEach(k => { cen[k] = Object.keys(census[k]).sort(); });
  return JSON.stringify({ tight: uniq.slice(0, 12), census: cen });
})()
"""

CANARY = ("<h2 id='__lhc' style='font-size:32px;line-height:1.02;width:260px'>"
          "CANARY a heading set solid that wraps onto a second line</h2>")


def run(urls, widths):
    # shared harness — see tools/cdp.py
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from cdp import Browser
    br = Browser(port_base=9718)
    cmd = br.cmd
    try:

        probe = PROBE % json.dumps(ALLOW)

        cmd("Emulation.setDeviceMetricsOverride", width=390, height=900,
            deviceScaleFactor=1, mobile=True)
        nav = cmd("Page.navigate", url=urls[0]); time.sleep(2.2)
        if nav.get("errorText"):
            print(f"[calibration] FAILED — {urls[0]} did not load ({nav['errorText']}). "
                  "Is the server on :8000 up?")
            return 2
        cmd("Runtime.evaluate", returnByValue=True, expression=(
            "(()=>{const d=document.createElement('div');d.id='__lhcw';"
            f"d.innerHTML={json.dumps(CANARY)};document.querySelector('main,body').prepend(d);return 1}})()"))
        time.sleep(.3)
        got = json.loads(cmd("Runtime.evaluate", expression=probe,
                             returnByValue=True)["result"]["value"])
        caught = any("CANARY" in t["text"] for t in got["tight"])
        cmd("Runtime.evaluate", expression="document.getElementById('__lhcw').remove()")
        if not caught:
            print("[calibration] FAILED — a solid-set wrapped heading was not flagged. "
                  "This gate proves nothing.")
            return 2
        print("[calibration] PASS — planted solid-set wrapped heading caught")

        bad, census = 0, {}
        for u in urls:
            for w in widths:
                cmd("Emulation.setDeviceMetricsOverride", width=w, height=900,
                    deviceScaleFactor=1, mobile=w < 700)
                # "did not load" is a NAVIGATION failure, not a short page. Body
                # length was the first heuristic and it called an OG-image
                # template (114 chars, entirely legitimate) a dead server.
                # Page.navigate reports errorText for ERR_CONNECTION_REFUSED and
                # friends — that is the real signal, and it is size-blind.
                nav = cmd("Page.navigate", url=u); time.sleep(1.7)
                if nav.get("errorText"):
                    print(f"LOAD FAILURE {u} @{w} — {nav['errorText']}. Refusing a verdict.")
                    return 2
                cmd("Runtime.evaluate", awaitPromise=True, expression=(
                    "(async()=>{const h=document.body.scrollHeight;"
                    "for(let y=0;y<h;y+=500){scrollTo(0,y);await new Promise(r=>setTimeout(r,12));}"
                    "scrollTo(0,0);await new Promise(r=>setTimeout(r,140));})()"))
                res = json.loads(cmd("Runtime.evaluate", expression=probe,
                                     returnByValue=True)["result"]["value"])
                for sig, ratios in res["census"].items():
                    census.setdefault(sig, set()).update(ratios)
                tag = f'{u.split("8000")[-1] or "/"} @{w}'
                if res["tight"]:
                    bad += len(res["tight"])
                    print(f"FAIL {tag}")
                    for t in res["tight"]:
                        print(f"       {t['ratio']:.2f} (floor {t['floor']:.2f})  {t['sig']}  "
                              f"{t['fs']}px/{t['lh']}px  {t['lines']} lines")
                        print(f"            {t['text']!r}")
                else:
                    print(f"ok   {tag}")

        drift = {k: sorted(v) for k, v in census.items() if len(v) > 1}
        print()
        print(f"{bad} element(s) set below the leading floor while wrapped.")
        if drift:
            print(f"\n{len(drift)} component(s) set at MORE THAN ONE ratio across the site")
            print("  (a type system has one answer per component; responsive size ramps")
            print("   are legitimate — a ratio that changes with them is not):")
            for k, v in sorted(drift.items(), key=lambda x: -len(x[1]))[:14]:
                print(f"    {k:<30} {v}")
        print("\nCANNOT SEE: whether a value ABOVE the floor is well chosen, optical")
        print("tightness from a specific face's descenders, and text not rendered on load.")
        return 1 if bad else 0
    finally:
        br.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--widths", default="390,768,1024,1440")
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
