#!/usr/bin/env python3
"""closed-state-cover-check — in its DEFAULT, untouched state, nothing may cover
the page's own content.

Class of defect (shipped 2026-09-06, caught by nothing that was watching for it):
a nav rule declared `display:flex` on `.nav-links` at `#nav` specificity with no
width scope. That outranks classic's `@media(max-width:1100px){.nav-links{
display:none}}`, so the mobile drawer rendered PERMANENTLY OPEN on every page
below 1100px — an opaque white panel over the top 475px of the viewport, and
`pointer-events:auto`, so it silently ate every click underneath it.

Why the suite was blind to it, precisely:
  · menu-overlay-check   proves the menu covers the page WHEN OPENED. It opens the
                         menu first, so a menu that was already open passes.
  · menu-keyboard-check  opens, presses Escape, checks aria. Same blind spot.
  · reachability-check   asks whether content is behind a gesture, per element.
  · contrast-audit       DID see it — 177 NO-INK. It was the only instrument that
                         screamed, and its verdict was initially dismissed as
                         noise because the shape looked instrumental. It was not.
  · everything else      is per-element and on-load; none asks whether element A
                         is painted ON TOP OF element B.

Method: no clicks, no keys — load the page and leave it alone, which is the state
every visitor arrives in. Sample a grid of points across the content column and
require the topmost hit element at each point to belong to the content, to the nav
bar's own band, or to a known-benign decoration. Anything else is a cover.

Swept across a width RANGE, not at the breakpoints alone: this defect laid out
correctly at 1200+ and was invisible in the two widths menus are usually checked
at. 390 is checked FIRST, because that is where layouts actually fail.

CANNOT SEE: covers that appear only after interaction or on a timer (a modal, a
cookie bar with a delay), covers that are transparent to hit-testing but still
paint (pointer-events:none over text — contrast-audit's pixels catch those), and
anything below the sampled grid's resolution.

Self-calibrating: plants a fixed cover and requires red.
"""
import sys, glob, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

WIDTHS = [390, 768, 1024, 1099, 1440]        # mobile first; 1440 is the control
PLANT = ("var d=document.createElement('div');d.id='__plant';"
         "d.style.cssText='position:fixed;top:64px;left:0;right:0;height:400px;"
         "background:#fff;z-index:99';document.body.appendChild(d);")
# the NEGATIVE plant: an absolute cover must NOT be flagged. Without this the
# exclusion above would be an untested assumption, and a later edit could widen
# or narrow the gate without anything noticing.
PLANT_ABS = ("var d=document.createElement('div');d.id='__plantabs';"
             "d.style.cssText='position:absolute;top:200px;left:0;right:0;height:300px;"
             "background:#fff;z-index:99';document.body.appendChild(d);")

PROBE = """JSON.stringify((()=>{
  // NO fallback to <body>: for one revision this read `querySelector('main')
  // || document.body`, and since body contains every node, `main.contains(top)`
  // was true at every point — the gate passed a planted cover on the 404 page,
  // which has no <main>. A missing content root means nothing is exempt by
  // containment, not that everything is.
  const main=document.querySelector('main');
  const nav=document.getElementById('nav');
  const navBot = nav ? nav.getBoundingClientRect().bottom : 0;
  const bad=[];
  const seen=new Set();
  // a grid over the content column, starting below the nav's own band
  const x0=Math.max(8,innerWidth*0.06), x1=innerWidth-Math.max(8,innerWidth*0.06);
  for(let y=Math.ceil(navBot)+8; y<innerHeight-8; y+=26){
    for(let x=x0; x<=x1; x+=Math.max(40,(x1-x0)/6)){
      const top=document.elementsFromPoint(x,y)[0];
      if(!top) continue;
      if(main&&(main.contains(top)||top===main)) continue;
      if(nav&&(nav.contains(top)||top===nav)) continue;
      const c=getComputedStyle(top);
      // VIEWPORT-ANCHORED overlays only. A `fixed`/`sticky` element rides the
      // reader and can end up over anything at any scroll offset — that is the
      // defect class. An `absolute` element is placed inside its own container's
      // box and can only cover what its author put behind it (planit's hero
      // video, the 404's .divert): flagging those produced three false reds and
      // no true ones. Text actually obscured by an absolute element is
      // contrast-audit's job, and it goes red on it — that is how the drawer was
      // caught (177 NO-INK). The boundary is asserted by PLANT_ABS below.
      if(c.position!=='fixed'&&c.position!=='sticky') continue;
      // a decoration that paints nothing and catches nothing is not a cover
      if(c.pointerEvents==='none') continue;
      const key=top.tagName+'.'+(top.className+'');
      if(seen.has(key)) continue;
      seen.add(key);
      bad.push({el:key.slice(0,52), pos:c.position, z:c.zIndex, bg:c.backgroundColor,
                at:[Math.round(x),Math.round(y)],
                rect:(r=>[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)])(top.getBoundingClientRect())});
    }
  }
  return bad;})())"""


def sweep(br, pages, widths, plant=None):
    bad = []
    for w in widths:
        br.viewport(w, 900)
        if w <= 500:
            br.cmd("Emulation.setDeviceMetricsOverride", width=w, height=844,
                   deviceScaleFactor=2, mobile=True)
        for p in pages:
            br.navigate(f"http://localhost:8000/{p}", settle=1.5)
            if plant:
                br.eval(plant); br.pump(0.3)
            for r in br.eval_json(PROBE) or []:
                bad.append((p, w, r))
            if plant and bad:
                return bad
    return bad


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        planted = sweep(br, pages[:1], [390], plant=PLANT)
        if not planted:
            print("[calibration] FAIL — a planted fixed white cover was not flagged; "
                  "instrument blind."); sys.exit(2)
        neg = sweep(br, pages[:1], [390], plant=PLANT_ABS)
        if neg:
            print(f"[calibration] FAIL — an ABSOLUTE cover was flagged ({neg[0][2]['el']}); "
                  "this gate is scoped to viewport-anchored overlays and has drifted."); sys.exit(2)
        print(f"[calibration] PASS — fixed cover flagged ({planted[0][2]['el']}), "
              "absolute cover correctly ignored (that case belongs to contrast-audit)")

    with Browser() as br:                       # clean context, no plant
        bad = sweep(br, pages, WIDTHS)

    for p, w, r in bad:
        print(f"FAIL @{w}px  {p}\n     {r['el']}  {r['pos']} z={r['z']} bg={r['bg']} "
              f"rect={r['rect']} covers point {r['at']}")
    if bad:
        pgs = len({b[0] for b in bad})
        print(f"\n{len(bad)} cover(s) on {pgs} page(s): content is painted over in the "
              f"page's default state, before any visitor touches anything.")
        sys.exit(1)
    print(f"ok — {len(pages)} pages x {len(WIDTHS)} widths ({', '.join(map(str,WIDTHS))}): "
          "nothing covers the content in the untouched state.")
    print("CANNOT SEE: covers that need an interaction or a timer to appear; covers that "
          "paint but do not hit-test; ABSOLUTE covers inside their own container (all "
          "three belong to contrast-audit's pixels); or anything finer than the grid.")


if __name__ == "__main__":
    main()
