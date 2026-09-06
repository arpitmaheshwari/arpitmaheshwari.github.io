#!/usr/bin/env python3
"""menu-keyboard-check — the open mobile menu must be dismissible from the keyboard,
and its aria state must be the truth.

Class of defect (found 2026-09-06 by exploratory testing, not by any gate):
29 pages carried a stale INLINE menu binder as well as the shared one in
dyslexia.js. dyslexia.js replaces the button node to strip stale listeners, but
it cannot unbind the DOCUMENT-level listeners the inline copy registered. So on
Escape the stale handler won the race, removed the open class, and wrote
aria-expanded="false" to the node that had already been replaced — leaving the
LIVE button announcing "expanded" after the drawer had visibly closed, and
dropping focus on <body> instead of returning it to the toggle.

Nothing in the suite could see this. The menu-overlay gate proves the open menu
paints on top; the reachability gate proves content is not hidden behind a
gesture. Neither presses a key, and neither compares a component's aria state
against reality AFTER an interaction.

Method: at 390px, click the toggle, press a REAL Escape (Input.dispatchKeyEvent,
because a synthetic KeyboardEvent does not exercise the same path), then require
all four: the open class is gone, aria-expanded is "false", the inert guard has
released the page, and focus is back on the toggle.

Self-calibrating: plants a stale duplicate binder and requires red.
"""
import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

# The plant must register its listener BEFORE the real one — that ordering IS the
# defect. Two earlier attempts were no-ops and reported the instrument blind:
# one added the listener after page load (the real handler had already closed the
# menu, so the plant found nothing open), and one wrapped it in DOMContentLoaded
# (defer scripts execute BEFORE that event, so dyslexia.js still bound first).
# It therefore binds at document-creation time and resolves elements lazily.
STALE = """
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Escape') return;
  var l = document.querySelector('.nav-links');
  if (!l || !l.classList.contains('nav-open')) return;
  l.classList.remove('nav-open');                       // closes it...
  var ghost = document.getElementById('menuToggle');
  if (ghost) ghost.setAttribute('aria-expanded', 'x');  // ...but lies about it
});
"""

PROBE = """JSON.stringify((()=>{
  const t=document.getElementById('menuToggle');
  if(!t) return 'no-toggle';
  return {aria:t.getAttribute('aria-expanded'),
    navOpen:document.querySelector('.nav-links').classList.contains('nav-open'),
    inert:[...document.body.children].filter(e=>e.hasAttribute&&e.hasAttribute('inert')).length,
    focus:document.activeElement.id||document.activeElement.tagName};})())"""


def escape(br):
    for t in ("rawKeyDown", "keyUp"):
        br.cmd("Input.dispatchKeyEvent", type=t, key="Escape", code="Escape",
               windowsVirtualKeyCode=27, nativeVirtualKeyCode=27)


def check(br, page, plant=False):
    if plant:
        br.cmd("Page.enable")
        br.cmd("Page.addScriptToEvaluateOnNewDocument", source=STALE)
    br.navigate(f"http://localhost:8000/{page}", settle=1.5)
    br.eval("var t=document.getElementById('menuToggle'); if(t) t.click()")
    br.pump(0.4)
    escape(br)
    br.pump(0.4)
    r = br.eval_json(PROBE)
    if r == "no-toggle":
        return None
    ok = (r["aria"] == "false" and not r["navOpen"]
          and r["inert"] == 0 and r["focus"] == "menuToggle")
    return ok, r


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        br.viewport(500, 900)
        br.cmd("Emulation.setDeviceMetricsOverride", width=390, height=844,
               deviceScaleFactor=2, mobile=True)

        planted = check(br, pages[0], plant=True)
        # the plant lives in the browser's new-document hook; a fresh Browser for
        # the real sweep guarantees it cannot leak into the results
        if planted and planted[0]:
            print("[calibration] FAIL — a planted stale binder was not flagged; "
                  "instrument blind."); sys.exit(2)
        print("[calibration] PASS — planted stale binder flagged")

    bad = []
    with Browser() as br:                     # clean context: no plant installed
        br.viewport(500, 900)
        br.cmd("Emulation.setDeviceMetricsOverride", width=390, height=844,
               deviceScaleFactor=2, mobile=True)
        for p in pages:
            res = check(br, p)
            if res is None:
                continue
            ok, r = res
            if not ok:
                bad.append((p, r))
                print(f"FAIL {p}  {r}")
        if bad:
            print(f"\n{len(bad)} page(s) do not honour Escape on the open menu.")
            sys.exit(1)
        print(f"ok — all {len(pages)} pages: Escape closes the menu, aria-expanded "
              "tells the truth, the page is released, focus returns to the toggle.")
        print("CANNOT SEE: whether the menu is dismissible by TOUCH (tap-outside is "
              "tested by no gate), nor the order of focus once it is closed.")


if __name__ == "__main__":
    main()
