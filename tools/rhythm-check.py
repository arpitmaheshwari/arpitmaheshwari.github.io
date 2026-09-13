#!/usr/bin/env python3
"""rhythm-check.py — every act on a page shares ONE vertical rhythm, and nothing adds to it.

WHY (2026-09-13, Arpit: "the negative space in between sections and within sections is not
proper"). The system names one act rhythm (--act-rhythm) and says every section in a
sequence shares it; the site never consumed it. Homepage acts carried five different
paddings, a decorative seam line added 96px of its own, and a section's first card added
its own 40px margin on top of the section's padding — so the blank between two acts ran
~200px on a phone. No gate measured any of it, because every spacing check here reads
DECLARED values on one element; the blank is the SUM across a boundary.

METHOD. For every classic page at 390 and 1440, take the visible bands (`main > section`,
descending single wrappers), skip the opening hero, and require: padding-top ==
padding-bottom == the page's resolved --rhythm-act (a seam-carrying act moves its top
space onto the seam, checked as such); the first and last visible child carry no
margin toward the band edge. Reports every band that breaks the number.

CALIBRATION. Plants `body.p-home .voices{padding-top:120px}` and requires a report.
Exit: 0 clean / 1 off-rhythm band(s) / 2 calibration failed.
CANNOT SEE: whether the rhythm number itself is right (Arpit's eye), a band's interior
composition, or gaps inside a single article (chapter margins — see the census tool).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls, planted

JS = r"""(()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none'};
 const css=getComputedStyle(document.documentElement); const rhythm=parseFloat(css.getPropertyValue('--rhythm-act'))||null; const chapter=parseFloat(css.getPropertyValue('--rhythm-chapter'))||null; const out=[];
 const main=document.querySelector('main')||document.body;
 // CLASS 1 — acts: full-width bands, the direct <section> children of main
 const bands=[...main.children].filter(e=>e.tagName==='SECTION'&&vis(e));
 if(bands.length>=2&&rhythm!==null) bands.forEach((b,i)=>{ const first=i===0; if(first&&/hero/.test(b.className)) return; const c=getComputedStyle(b); const seam=b.querySelector(':scope > .seam, :scope > .seam-up');
   const pt=parseFloat(c.paddingTop)+(seam?parseFloat(getComputedStyle(seam).marginBottom):0), pb=parseFloat(c.paddingBottom);
   let box=b; while([...box.children].filter(vis).length===1) box=[...box.children].filter(vis)[0];
   const kids=[...box.children].filter(k=>vis(k)&&!k.matches('.seam,.seam-up')); const f=kids[0], l=kids[kids.length-1];
   const mt=f?parseFloat(getComputedStyle(f).marginTop):0, mb=l?parseFloat(getComputedStyle(l).marginBottom):0;
   const bad=[]; if(!first&&Math.abs(pt-rhythm)>1) bad.push(`top ${pt}`); /* a first band's top clears the fixed nav (nav-clearance-check owns it) */ if(Math.abs(pb-rhythm)>1) bad.push(`bottom ${pb}`); if(mt>0) bad.push(`first-child margin ${mt}`); if(mb>0) bad.push(`last-child margin ${mb}`);
   if(bad.length) out.push({band:'act .'+(b.className||b.id||'section').toString().split(' ')[0], bad}); });
 // CLASS 2 — chapters: an h2-led <section> inside a single-column article; the gap below it is one number
 let m=main; while([...m.children].filter(vis).length===1) m=[...m.children].filter(vis)[0];
 if(m!==main&&chapter!==null) for(const s of [...m.children].filter(e=>e.tagName==='SECTION'&&vis(e)&&e.firstElementChild&&e.firstElementChild.tagName==='H2')){
   const mb=parseFloat(getComputedStyle(s).marginBottom); if(Math.abs(mb-chapter)>1) out.push({band:'chapter .'+(s.className||'section').toString().split(' ')[0].slice(0,30), bad:[`margin-bottom ${mb}`]}); }
 return JSON.stringify({rhythm,bands:out})})()"""


def scan(br, urls, widths=(390, 1440)):
    hits = []
    for u in urls:
        for w in widths:
            br.viewport(w, 900); br.navigate(u, settle=2.5)
            r = br.eval_json(JS)
            for b in r['bands']:
                hits.append((u.split('8000/')[1] or '/', w, r['rhythm'], b['band'], ', '.join(b['bad'])))
    return hits


def main():
    cdp.ensure_server(8000)
    with cdp.Browser() as br:
        with planted('site.css', '\nbody.p-home .voices{padding-top:120px !important}\n'):
            red = any(h[3] == 'act .voices' for h in scan(br, ['http://localhost:8000/'], (1440,)))
        if not red:
            print('CALIBRATION FAILED: a planted off-rhythm act was not reported'); return 2
        print('  calibrated: a planted off-rhythm act goes red')
        hits = scan(br, page_urls(include_book=False))
    for pg, w, rh, band, bad in hits:
        print(f"  OFF  {pg:40s} @{w:<5} rhythm={rh:<4} .{band:14s} {bad}")
    print(f"{len(hits)} off-rhythm band(s). CANNOT SEE: the number's rightness, interior composition, chapter gaps inside one article.")
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
