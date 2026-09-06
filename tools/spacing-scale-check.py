#!/usr/bin/env python3
"""spacing-scale-check — every declared space must be a step on the scale, and
every act must share one rhythm.

Arpit: "you are still not following the grid religiously, the sections and the
items and elements in the homepage don't look evenly spaced out." Measured on
the homepage at 1440 before any fix:

  section padding-top     0, 92, 96, 104, 120, 140     six values
  section padding-bottom  80, 88, 92, 96, 140          five values
  declared margins        included 12, 20 and 40

Two sections had ZERO top padding and leaned on a neighbour's margin, so the
rhythm collapsed wherever that neighbour changed. Evenly spaced means the SAME
number, not a similar one: 92 against 96 reads as a mistake at a glance, which
is exactly what the complaint described.

WHAT THIS MEASURES, and what it deliberately does not: DECLARED margins and
paddings, never rendered box-to-box gaps. A gap between two boxes includes the
half-leading of each line box, so it is almost never a clean multiple even when
the spacing is perfectly correct — the first version of this check flagged a
67px "gap" between a heading and the line under it as off-grid when both
margins were exactly on the scale.

CANNOT SEE: whether a correct step is the RIGHT step for that pair, optical
spacing (a heading over a rule needs less than over a paragraph), or horizontal
rhythm — tools/section-heading-census.py covers the left-edge anchor.

Self-calibrating: plants an off-scale margin and requires red.
"""
import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

SCALE = {0, 8, 16, 24, 32, 40, 48, 64, 96, 128, 160}
PLANT = ("var s=document.createElement('style');"
         "s.textContent='main > section > .wrap > h2{margin-bottom:37px !important}';"
         "document.head.appendChild(s);")

PROBE = """JSON.stringify((()=>{
  const off=[], pads=[];
  document.querySelectorAll('main > :is(section,header)').forEach(s=>{
    const c=getComputedStyle(s);
    // the FULL class list, not just the first class. `section.lab-hero` has its
    // hero class second, so reading className.split(' ')[0] returned "section"
    // and five lab/fit heroes were reported as breaking the act rhythm when
    // they are exempt by design.
    const n=(s.className+'')+' '+(s.id||'')+' '+s.tagName;
    if(/hero/i.test(n)) return;                // a hero is not an act in the sequence
    pads.push({sec:n, pt:Math.round(parseFloat(c.paddingTop)), pb:Math.round(parseFloat(c.paddingBottom))});
  });
  document.querySelectorAll('main > :is(section,header) > :is(.wrap,.lab-wrap) > *').forEach(e=>{
    const c=getComputedStyle(e);
    const name=e.tagName.toLowerCase()+'.'+((e.className+'')||'-').split(' ')[0];
    [['margin-top',c.marginTop],['margin-bottom',c.marginBottom]].forEach(([k,v])=>{
      const n=Math.round(parseFloat(v)||0);
      if(n!==0) off.push({el:name, prop:k, v:n});});
  });
  return {pads:pads, spaces:off};})())"""


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        br.viewport(1440, 1000)
        br.navigate("http://localhost:8000/index.html", settle=1.8)
        br.eval(PLANT); br.pump(0.3)
        got = br.eval_json(PROBE)
        if not any(s["v"] not in SCALE for s in got["spaces"]):
            print("[calibration] FAIL — a planted 37px margin was not flagged; "
                  "instrument blind."); sys.exit(2)
        print("[calibration] PASS — planted 37px margin flagged")

    bad_space, bad_rhythm = [], []
    with Browser() as br:
        br.viewport(1440, 1000)
        for p in pages:
            br.navigate(f"http://localhost:8000/{p}", settle=1.5)
            if br.eval_json("JSON.stringify([location.pathname])")[0].lstrip("/") != p:
                continue
            br.eval("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
            br.pump(0.3)
            got = br.eval_json(PROBE) or {"pads": [], "spaces": []}
            for s in got["spaces"]:
                if s["v"] not in SCALE:
                    bad_space.append((p, s))
            tops = {x["pt"] for x in got["pads"]}
            bots = {x["pb"] for x in got["pads"]}
            if len(tops) > 1 or len(bots) > 1:
                bad_rhythm.append((p, sorted(tops), sorted(bots)))

    for p, s in bad_space:
        print(f"OFF-SCALE  {p}  {s['el']} {s['prop']}:{s['v']}px")
    for p, tops, bots in bad_rhythm:
        print(f"RHYTHM     {p}  section padding top {tops} / bottom {bots} "
              f"— acts must share one rhythm")
    if bad_space or bad_rhythm:
        print(f"\n{len(bad_space)} off-scale space(s), {len(bad_rhythm)} page(s) "
              f"whose acts do not share one rhythm.")
        sys.exit(1)
    print(f"ok — {len(pages)} pages: every declared space is a step on the 8px scale "
          f"{sorted(SCALE)}, and every act on a page shares one rhythm.")
    print("CANNOT SEE: whether a correct step is the RIGHT step for that pair, "
          "optical spacing, or horizontal rhythm (see section-heading-census).")


if __name__ == "__main__":
    main()
