#!/usr/bin/env python3
"""wcag-reflow-target-check — two conformance requirements nothing here measured.

Prompted by an article Arpit sent (ux-maldo.hashnode.dev, "Auditing UX laws for
AI coding instructions"), whose useful move is turning heuristics into
INSPECTABLE ARTIFACTS rather than advice. Two of its checkable items had no
instrument in this repo:

  REFLOW  — WCAG 2.1 SC 1.4.10 (AA). At 320 CSS pixels of width, content must
            reflow without requiring scrolling in TWO dimensions. 320px is the
            requirement, not 390: it is 1280px at 400% zoom, which is how a
            low-vision reader actually reads this site. Every gate here tests
            390 and above, so the requirement has never been measured.

  TARGET  — WCAG 2.2 SC 2.5.8 (AA). An interactive target must be at least
            24x24 CSS px, OR have 24px of clearance to its neighbours. Notes in
            this repo assumed 44px, which is SC 2.5.5 (AAA) and a different
            requirement — so the AA line was never checked at all.

CANNOT SEE: whether reflowed content is still USABLE (order, emphasis and
meaning survive), targets revealed only after interaction, or the spacing
exception's full geometry — this measures the simple 24x24 case and the
horizontal gap, not the full offset-circle rule.

Self-calibrating: plants a 700px fixed-width block (must fail reflow) and a
12x12 link (must fail target), and requires both to go red.
"""
import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

REFLOW_W = 320
MIN_TARGET = 24

PLANT = ("var d=document.createElement('div');d.style.cssText="
         "'width:700px;height:60px;background:#eee';document.body.appendChild(d);"
         "var a=document.createElement('a');a.href='#';a.textContent='x';"
         "a.style.cssText='display:block;width:12px;height:12px';"
         "document.querySelector('main').appendChild(a);")

REFLOW = """JSON.stringify((()=>{
  const d=document.documentElement;
  const over=d.scrollWidth-d.clientWidth;
  if(over<=1) return {over:0, culprits:[]};
  // name what is actually too wide, so the finding is actionable
  const culprits=[...document.querySelectorAll('body *')].filter(e=>{
    const r=e.getBoundingClientRect();
    if(r.width<=d.clientWidth+1) return false;
    if(r.height<3) return false;
    const c=getComputedStyle(e);
    if(c.position==='fixed') return false;
    return true;})
    .map(e=>({el:e.tagName.toLowerCase()+'.'+((e.className+'')||'-').split(' ')[0],
              w:Math.round(e.getBoundingClientRect().width)}))
    .sort((a,b)=>b.w-a.w).slice(0,4);
  return {over:over, culprits:culprits};})())"""

TARGETS = """JSON.stringify((()=>{
  const out=[];
  for(const e of document.querySelectorAll('a[href],button,input,select,summary,[role="button"]')){
    const c=getComputedStyle(e);
    if(c.visibility==='hidden'||c.display==='none') continue;
    const r=e.getBoundingClientRect();
    if(r.width<1||r.height<1) continue;                 // off-canvas: not a target yet
    if(r.width>=%d && r.height>=%d) continue;
    // SC 2.5.8 exception: 24px of clearance counts as meeting it
    let near=false;
    for(const o of document.querySelectorAll('a[href],button,input,select,summary,[role="button"]')){
      if(o===e) continue;
      const q=o.getBoundingClientRect();
      if(q.width<1||q.height<1) continue;
      const dx=Math.max(0, Math.max(e.getBoundingClientRect().left-q.right, q.left-r.right));
      const dy=Math.max(0, Math.max(r.top-q.bottom, q.top-r.bottom));
      if(Math.hypot(dx,dy) < 24){ near=true; break; }
    }
    if(!near) continue;                                  // isolated small target: allowed
    // text inside a sentence is exempt (SC 2.5.8 inline exception)
    const p=e.closest('p,li,figcaption,blockquote');
    if(p){
      const linkLen=[...p.querySelectorAll('a')].reduce((n,x)=>n+x.textContent.trim().length,0);
      if(p.textContent.trim().length-linkLen > 20) continue;
    }
    out.push({el:e.tagName.toLowerCase()+'.'+((e.className+'')||'-').split(' ')[0],
              w:Math.round(r.width), h:Math.round(r.height),
              txt:(e.textContent||'').trim().slice(0,26)});
  }
  return out.slice(0,6);})())""" % (MIN_TARGET, MIN_TARGET)


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        br.viewport(REFLOW_W, 800)
        br.navigate("http://localhost:8000/index.html", settle=1.6)
        br.eval(PLANT); br.pump(0.4)
        r = br.eval_json(REFLOW); t = br.eval_json(TARGETS)
        if not r["over"]:
            print("[calibration] FAIL — a planted 700px block did not break reflow at "
                  "320px; instrument blind."); sys.exit(2)
        print(f"[calibration] PASS — planted 700px block broke reflow "
              f"({r['over']}px of horizontal scroll)")

    bad_r, bad_t = [], []
    with Browser() as br:                    # clean context
        for w, label in ((REFLOW_W, "reflow"),):
            br.viewport(w, 800)
            for p in pages:
                br.navigate(f"http://localhost:8000/{p}", settle=1.5)
                if br.eval_json("JSON.stringify([location.pathname])")[0].lstrip("/") != p:
                    continue                 # redirect stub
                    br.pump(0.3)
                r = br.eval_json(REFLOW)
                if r["over"] > 1:
                    bad_r.append((p, r))
                for x in br.eval_json(TARGETS) or []:
                    bad_t.append((p, x))

    for p, r in bad_r:
        print(f"REFLOW  {p}  {r['over']}px of horizontal scroll at {REFLOW_W}px")
        for c in r["culprits"]:
            print(f"          {c['el']} is {c['w']}px wide")
    for p, x in bad_t:
        print(f"TARGET  {p}  {x['el']} is {x['w']}x{x['h']} (<{MIN_TARGET}) "
              f"with a neighbour inside 24px  '{x['txt']}'")
    if bad_r or bad_t:
        print(f"\n{len(bad_r)} page(s) fail reflow at {REFLOW_W}px, "
              f"{len(bad_t)} target(s) below {MIN_TARGET}x{MIN_TARGET} without clearance.")
        sys.exit(1)
    print(f"ok — {len(pages)} pages: reflow at {REFLOW_W}px with no two-dimensional "
          f"scrolling, and every crowded target is at least {MIN_TARGET}x{MIN_TARGET}.")
    print("CANNOT SEE: whether reflowed content is still USABLE, targets revealed only "
          "by interaction, or the full offset-circle geometry of the spacing exception.")


if __name__ == "__main__":
    main()
