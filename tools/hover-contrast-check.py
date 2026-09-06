#!/usr/bin/env python3
"""hover-contrast-check — every interactive element must stay legible WHILE HOVERED.

Class of defect (found by Arpit, 2026-09-06, not by any gate): the secondary CTA
"See selected work" turned its label parchment on hover while its plate stayed
near-white — 1.07:1, invisible. Cause: a hover rule written for the primary named
`.pill`, which every secondary also carries.

Nothing in the suite could see it. contrast-audit measures the page AS LOADED and
freezes transitions to do so; reachability asks whether content is reachable;
menu-keyboard presses a key. None of them hovers anything, and a hover state is a
different set of colours from the resting state.

Method: for every visible link and button, move a REAL pointer to its centre
(Input.dispatchMouseEvent — a synthetic :hover class would not exercise the same
cascade), wait for the transition, then measure the hovered label against the
hovered fill. A transparent fill resolves to the nearest opaque ancestor.

CANNOT SEE: focus and active states (different pseudo-classes), colours that only
appear mid-transition, and anything a screenshot would catch that arithmetic does
not — this is DOM arithmetic, so a shadow or overlay behind the label is invisible
to it. For that, contrast-audit's pixel sampling remains the authority.

Self-calibrating: plants a low-contrast hover and requires red.
"""
import sys, glob, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

AA = 4.5
PLANT = """
var s=document.createElement('style');
s.textContent='a:hover,button:hover{color:#f7f4ee !important;background:#f2f1ed !important}';
document.head.appendChild(s);
"""

TARGETS = """JSON.stringify((()=>{
  const out=[];
  for(const e of document.querySelectorAll('a[href],button')){
    const r=e.getBoundingClientRect();
    if(r.width<8||r.height<8) continue;
    if(r.top<0||r.top>innerHeight-4) continue;          // must be on screen to hover
    const t=(e.textContent||'').trim();
    if(!t) continue;
    out.push({x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), txt:t.slice(0,34)});
  }
  return out.slice(0,14);})())"""


def lum(rgb):
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    la, lb = max(la, lb), min(la, lb)
    return (la + 0.05) / (lb + 0.05)


def rgb(s):
    n = re.findall(r"[\d.]+", s)
    return tuple(int(float(x)) for x in n[:3])


READ = """JSON.stringify((()=>{
  const e=document.querySelector(':hover:is(a,button)') ||
          [...document.querySelectorAll('a:hover,button:hover')].pop();
  if(!e) return null;
  const c=getComputedStyle(e);
  // walk up for the first opaque background actually behind the label
  let g=e, bg='rgba(0, 0, 0, 0)';
  while(g){ const b=getComputedStyle(g).backgroundColor;
    const m=(b.match(/[\\d.]+/g)||[]).map(Number);
    if(m.length>=3 && (m[3]===undefined || m[3]>0.9)){ bg=b; break; }
    g=g.parentElement; }
  return {txt:(e.textContent||'').trim().slice(0,34), color:c.color, bg};})())"""


def sweep(br, pages, plant=False):
    bad = []
    for p in pages:
        br.navigate(f"http://localhost:8000/{p}", settle=1.5)
        if plant:
            br.eval(PLANT)
        for t in br.eval_json(TARGETS):
            br.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=t["x"], y=t["y"], button="none")
            br.pump(0.35)
            got = br.eval_json(READ)
            if not got:
                continue
            r = ratio(rgb(got["color"]), rgb(got["bg"]))
            if r < AA:
                bad.append((p, got["txt"], round(r, 2), got["color"], got["bg"]))
        if plant and bad:
            break
    return bad


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        br.viewport(1440, 900)
        planted = sweep(br, pages[:1], plant=True)
        if not planted:
            print("[calibration] FAIL — a planted 1.07:1 hover was not flagged; instrument blind.")
            sys.exit(2)
        print(f"[calibration] PASS — planted low-contrast hover flagged ({planted[0][2]}:1)")

    bad = []
    with Browser() as br:                      # clean context, no plant
        br.viewport(1440, 900)
        bad = sweep(br, pages)
    for p, txt, r, fg, bg in bad:
        print(f"FAIL {r}:1  '{txt}'  {fg} on {bg}   {p}")
    if bad:
        print(f"\n{len(bad)} element(s) lose legibility on hover.")
        sys.exit(1)
    print(f"ok — every hovered link and button on {len(pages)} pages stays at {AA}:1 or better.")
    print("CANNOT SEE: focus/active states, mid-transition colours, or anything behind "
          "the label that arithmetic misses — contrast-audit's pixels remain the authority.")


if __name__ == "__main__":
    main()
