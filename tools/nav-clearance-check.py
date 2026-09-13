#!/usr/bin/env python3
"""nav-clearance-check.py — the first thing on every page clears the fixed nav by a breath.

WHY (2026-09-14, Arpit, on /patterns/: "sticking to header, you missed in exploratory
setting"). The eyebrow sat 4px UNDER the 94px bar at 1440 — its band was padded 90px, a
number typed before the nav grew. lab/plugin sat 29px under it at every width. journey-check
had learned to clear the bar for JUMP anchors and never asked about the top of the page; every
other gate reads one element's declared padding, and the defect is the DIFFERENCE between two
elements (the nav's rendered bottom and the first content's rendered top).

METHOD. Every classic page at 390/768/1024/1440, scrolled to 0: the lowest-top visible text or
media element outside the nav must sit at least FLOOR px below the nav's rendered bottom. The
site's rule is padding-top: calc(var(--nav-h) + 32px) on every first band; FLOOR is 24 so a
1px rounding never trips it while a typed 90 or a rhythm-sized 48 always does.
CALIBRATION: one page is loaded with its first band's padding-top forced to 0 and must go red.
Exit: 0 clean / 1 page-width(s) under the bar / 2 calibration failed.
CANNOT SEE: content that becomes the first thing only after interaction (an opened drawer),
the book (its own layout, no fixed nav), or whether the breath LOOKS right — only that it exists.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import pages

FLOOR = 24
WIDTHS = (390, 768, 1024, 1440)
BASE = os.environ.get('BASE', 'http://localhost:8000')
JS = r"""(()=>{window.scrollTo(0,0);const n=document.getElementById('nav');if(!n)return {nav:null};
const nb=n.getBoundingClientRect().bottom;let best=null;
for(const e of document.querySelectorAll('body *')){
  if(e.closest('#nav')||e.closest('.skip-link')||e.id==='doubt-ring')continue;
  const cs=getComputedStyle(e);if(cs.position==='fixed'||cs.visibility==='hidden'||cs.opacity==='0')continue;
  const txt=[...e.childNodes].some(t=>t.nodeType===3&&t.textContent.trim());
  const media=/^(IMG|VIDEO|SVG)$/.test(e.tagName);if(!txt&&!media)continue;
  const r=e.getBoundingClientRect();if(r.height<4||r.width<4||r.bottom<0)continue;
  if(!best||r.top<best.top)best={top:r.top,txt:(e.textContent||e.getAttribute('alt')||e.tagName).trim().slice(0,40)};}
return {nav:Math.round(nb),first:best?Math.round(best.top):null,txt:best?best.txt:''}})()"""
PLANT = "(()=>{const s=document.createElement('style');s.textContent='.page-head{padding-top:0!important}';document.head.appendChild(s);return 1})()"


def measure(br, rel):
    br.navigate(f'{BASE}/{rel}', settle=1.0)
    return br.eval_json(JS)


def main():
    bad = []
    with cdp.Browser() as br:
        # calibration: the plant must go red before anything is trusted
        br.viewport(1440, 900)
        br.navigate(f'{BASE}/process/index.html', settle=1.0)
        br.eval(PLANT)
        d = br.eval_json(JS)
        if d.get('nav') is None or d['first'] - d['nav'] >= FLOOR:
            print('CALIBRATION FAILED: a first band with no top padding was not reported'); return 2
        print('  calibrated: a first band padded 0 goes red')
        for w in WIDTHS:
            br.viewport(w, 900)
            for rel in pages(include_book=False):
                d = measure(br, rel)
                if d.get('nav') is None or d.get('first') is None:
                    continue
                gap = d['first'] - d['nav']
                if gap < FLOOR:
                    bad.append((w, rel, gap, d['txt']))
    for w, rel, gap, txt in sorted(bad, key=lambda x: x[2]):
        print(f'  UNDER THE BAR  {rel:42} @{w:<5} {gap:>4}px  {txt!r}')
    n = len(WIDTHS) * len(pages(include_book=False))
    print(f'{len(bad)} page-width(s) with less than {FLOOR}px between the nav and the first content, of {n}.')
    print('CANNOT SEE: what becomes first after an interaction, the book, or whether the breath looks right.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
