#!/usr/bin/env python3
"""negative-space-check — a band of the page may not leave a third of its width
empty on one side, and may not push its content off-centre.

Arpit's standing layout rule: "Whitespace must be designed, not left over.
Capped-width text inside a full-width container is a decision about the
remaining space: either give that space a content-role element or don't cap the
text. 'Empty because the column ended' is a defect."

This is the THIRD attempt at measuring it, and the first two failures are the
reason it is shaped this way:
  · attempt 1 measured the whole VIEWPORT against the whole page. Every page has
    legitimate outer margin, so the real defect drowned in it.
  · attempt 2 measured each CONTAINER against its own children — which finds zero
    by construction, because a container is exactly as wide as it was told to be.
So this measures each BAND (a top-level section) against the union of the INK
actually painted inside it: leaf elements with text, images, svg, video, canvas.
A container that is wide and empty is invisible to it; a band whose content sits
in a 600px column at one edge is not.

Two findings, both from the layout rule:
  VOID         one side of a band is more than a third of its width, empty
  OFF-AXIS     the content's two side gaps differ by more than a sixth
  UNDERFILLED  a tall band uses less than 62% of the width available to it —
               the symmetric case, and the one the first two versions missed

Only bands taller than MIN_H are judged: a short band (a rule, a one-line label)
is allowed to be narrow and is not a composition.

CANNOT SEE: whether space that IS filled is filled with something worth having
(an empty rail passes this gate, and an empty rail is worse than the void it
replaced — that mistake was made on 2026-09-06 and only a render caught it),
vertical rhythm, or whether an off-axis band is off-axis ON PURPOSE.

Self-calibrating: plants a narrow left-aligned column in a wide band and requires
red, then plants nothing and requires the planted page to come back clean.
"""
import sys, glob, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

WIDTHS = [1440, 1280]
MIN_H = 220              # a band shorter than this is not a composition
VOID = 1 / 3.0           # one side empty by more than this fraction of the band
AXIS = 1 / 6.0           # side gaps may not differ by more than this fraction
UTIL = 0.62              # a tall band must USE at least this much of the width

# UTIL is the threshold that matters, and it was missing from the first two
# versions of this gate. The defect that prompted the whole exercise — the essay
# pages — was SYMMETRIC: 704px of ink centred in 1312px of available width, gaps
# of 304px on each side. Each side was 23%, so no "one side over a third" rule
# could ever see it, and the gate passed the exact page it was written for. What
# was actually wrong is that a band 2,511px tall used 54% of the width it had.
# Verified both ways: the pre-fix essay measures 54% and fires, the fixed one
# measures 71% and does not.

PLANT = ("var s=document.createElement('style');"
         "s.textContent='main > section > *{max-width:320px !important;"
         "margin-left:0 !important;margin-right:auto !important}';"
         "document.head.appendChild(s);")

PROBE = r"""JSON.stringify((()=>{
  const main=document.querySelector('main')||document.body;
  // THE REFERENCE FRAME IS THE AVAILABLE WIDTH, not the band's own box. Measuring
  // each band against itself produced NEGATIVE gaps (-234px) and no useful
  // finding, because on the essay and pattern pages main's child IS the capped
  // 704px column — a box that the rail and the pull-quotes deliberately break
  // out of. The defect being hunted is precisely "a capped column inside a wide
  // container", so the container's content box is what the ink must be compared
  // against.
  const ms=getComputedStyle(main), mr=main.getBoundingClientRect();
  const availL = mr.left + parseFloat(ms.paddingLeft||0);
  const availR = mr.right - parseFloat(ms.paddingRight||0);
  const availW = availR - availL;
  const bands=[...main.children].filter(e=>/^(SECTION|DIV|ARTICLE|HEADER|FOOTER)$/.test(e.tagName));
  const out=[];
  for(const b of bands){
    const br=b.getBoundingClientRect();
    if(br.height < %d) continue;
    if(availW < 600) continue;
    // the INK: leaf elements that actually paint something
    let L=Infinity, R=-Infinity, n=0;
    const walk=b.querySelectorAll('*');
    for(const e of walk){
      const tag=e.tagName;
      const isMedia=/^(IMG|SVG|VIDEO|CANVAS|PICTURE)$/.test(tag);
      let hasOwnText=false;
      if(!isMedia){
        for(const nd of e.childNodes){
          if(nd.nodeType===3 && nd.textContent.trim().length>1){hasOwnText=true;break;}
        }
      }
      if(!isMedia && !hasOwnText) continue;
      const cs=getComputedStyle(e);
      if(cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)<0.06) continue;
      const r=e.getBoundingClientRect();
      if(r.height<4||r.width<4) continue;
      if(r.bottom<br.top||r.top>br.bottom) continue;   // clipped out of this band
      L=Math.min(L,r.left); R=Math.max(R,r.right); n++;
    }
    if(!n||!isFinite(L)) continue;
    const left=Math.round(L-availL), right=Math.round(availR-R);
    out.push({id:b.id||'', cls:(b.className+'').split(' ').slice(0,2).join('.'),
              w:Math.round(availW), h:Math.round(br.height),
              left:left, right:right, ink:n});
  }
  return out;})())""" % MIN_H


def judge(bands, width):
    bad = []
    for b in bands:
        w = b["w"]
        ink = w - b["left"] - b["right"]
        big = max(b["left"], b["right"])
        if big > w * VOID:
            side = "left" if b["left"] > b["right"] else "right"
            bad.append(("VOID", b, f"{side} gap {big}px of a {w}px band "
                                   f"({big*100//w}%) — more than a third empty"))
        elif abs(b["left"] - b["right"]) > w * AXIS:
            bad.append(("OFF-AXIS", b, f"gaps {b['left']}px / {b['right']}px differ by "
                                       f"{abs(b['left']-b['right'])}px on a {w}px band"))
        elif ink < w * UTIL:
            bad.append(("UNDERFILLED", b, f"{ink}px of ink in {w}px available "
                                          f"({ink*100//w}%) — {w-ink}px has no role"))
    return bad


def sweep(br, pages, widths, plant=False):
    found = []
    for w in widths:
        br.viewport(w, 1000)
        for p in pages:
            br.navigate(f"http://localhost:8000/{p}", settle=1.6)
            # A REDIRECT STUB IS NOT A PAGE. Four ~1KB files in this repo exist
            # only to location.replace() somewhere else. Navigated to, they hand
            # back the DESTINATION's document, so this gate was grading
            # lab/loop.html three times over and attributing two of those runs to
            # lab/hitl.html and lab/trustlayer.html — findings on pages that have
            # no layout at all.
            here = br.eval_json("JSON.stringify([location.pathname])")[0]
            if here.lstrip("/") != p:
                continue
            br.eval("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
            if plant:
                br.eval(PLANT)
            br.pump(0.35)
            for kind, b, why in judge(br.eval_json(PROBE) or [], w):
                found.append((p, w, kind, b, why))
            if plant and found:
                return found
    return found


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    with Browser() as br:
        planted = sweep(br, ["index.html"], [1440], plant=True)
        if not planted:
            print("[calibration] FAIL — a planted 320px left-aligned column in a "
                  "1440px band was not flagged; instrument blind."); sys.exit(2)
        print(f"[calibration] PASS — planted narrow column flagged "
              f"({planted[0][2]}: {planted[0][4]})")

    with Browser() as br:                       # clean context, no plant
        found = sweep(br, pages, WIDTHS)

    by_page = {}
    for p, w, kind, b, why in found:
        by_page.setdefault(p, []).append((w, kind, b, why))
    for p in sorted(by_page):
        print(f"\n{p}")
        for w, kind, b, why in by_page[p]:
            name = (f"#{b['id']}" if b['id'] else f".{b['cls']}") or "<band>"
            print(f"  {kind:9} @{w}px  {name:26} {b['h']}px tall, {b['ink']} ink boxes")
            print(f"            {why}")
    if found:
        print(f"\n{len(found)} band(s) on {len(by_page)} page(s) leave space undesigned.")
        sys.exit(1)
    print(f"ok — {len(pages)} pages x {len(WIDTHS)} widths: every band taller than "
          f"{MIN_H}px keeps its content on axis and within a third.")
    print("CANNOT SEE: whether filled space is filled with something WORTH having "
          "(an empty rail passes this gate), vertical rhythm, or deliberate asymmetry.")


if __name__ == "__main__":
    main()
