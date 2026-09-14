#!/usr/bin/env python3
"""composition-check.py — the class of defect every per-element gate is blind to: a band whose content
leaves most of its width empty, a hero that makes a claim with nothing beside it, one sentence printed
twice as lead and heading, and a card grid whose members are not the same kind of thing.

WHY (2026-09-14/15, Arpit: "fix the empty right half of the lab hero … it has many fundamental gaps"
and then "fix architectural gap across all the pages"). The Lab hero set its claim in a 62ch column and
left the right half of the band empty; seventeen article pages and five Lab tool pages did the same in
every band. Contrast, spacing, rhythm and clearance were all green, because each of them measures ONE
element's own properties. This measures the band against its contents.

RULES, at 1440 and 1024:
  NARROW-BAND   a band ≥200px tall spanning ≥90% of the viewport whose visible text/media covers <50%
                of the band's width (centred or one-sided — both are a column that ended)
  NAKED-HERO    the first band covers <60% and holds no object (image, video, svg, figure, table,
                instrument panel, card)
  DOUBLE-ENDING a bold lead or lede sentence that is also an h1/h2/h3 on the same page
  MIXED-GRID    a card grid where some cards open pages and others jump within the page, or where some
                cards carry a measured figure and others none
EXEMPT: bands Arpit chose to centre on purpose (the homepage's closing card on its stage) — listed
in EXEMPT with the date of the decision, never silently.
CALIBRATION: one page is loaded with a band's content forced to 40% width and must go red.
Exit: 0 clean / 1 finding(s) / 2 calibration failed.
CANNOT SEE: whether a full band is GOOD (a wall of text covers 100%), interior alignment, anything that
appears only after interaction, or the book (its own layout).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import pages

BASE = os.environ.get('BASE', 'http://localhost:8000')
WIDTHS = (1440, 1024)
EXEMPT = {
    'index.html': ['section#contact.close'],   # 2026-09-13, Arpit: the boarding pass is "a card on a stage, not a chapter"
}
JS = r"""(()=>{
const vis=e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'};
const leaf=e=>[...e.childNodes].some(t=>t.nodeType===3&&t.textContent.trim())||/^(IMG|VIDEO|SVG|CANVAS|PRE|TABLE|FIGURE)$/.test(e.tagName);
const bbox=b=>{let L=1e9,R=-1e9,n=0;for(const e of b.querySelectorAll('*')){if(!vis(e)||!leaf(e))continue;const r=e.getBoundingClientRect();if(r.width<8||r.height<8)continue;L=Math.min(L,r.left);R=Math.max(R,r.right);n++;}return{L,R,n}};
const name=b=>b.tagName.toLowerCase()+(b.id?'#'+b.id:'')+'.'+(b.className||'').toString().trim().split(/\s+/).slice(0,2).join('.');
const out={bands:[],hero:null,dup:[],grids:[]};
const cands=[...document.querySelectorAll('main section, main header, main > div, .page-head, .case-hero, body > header:not(#nav)')].filter(vis)
  .filter(b=>{const r=b.getBoundingClientRect();return r.height>=200&&r.width>=innerWidth*0.9&&!b.closest('#nav')&&!b.closest('footer')});
for(const b of cands){
  if(cands.some(o=>o!==b&&o.contains(b)&&Math.abs(o.getBoundingClientRect().height-b.getBoundingClientRect().height)<40))continue;
  const br=b.getBoundingClientRect();const {L,R,n}=bbox(b);if(!n)continue;const cover=(R-L)/br.width;
  if(cover<0.5) out.bands.push({band:name(b),cover:+cover.toFixed(2),h:Math.round(br.height)});
}
const first=cands[0];
if(first){const br=first.getBoundingClientRect();const {L,R}=bbox(first);const cover=(R-L)/br.width;
  const obj=first.querySelector('img,video,svg,canvas,figure,table,.vg,.lh-inst,.lh-side,.ph-card,.hero-demo,.bcard,.lab-card');
  out.hero={band:name(first),cover:+cover.toFixed(2),object:!!obj};}
const norm=t=>t.trim().replace(/[.!?]$/,'').replace(/\s+/g,' ').toLowerCase();
const heads=new Set([...document.querySelectorAll('h1,h2,h3')].map(h=>norm(h.textContent)));
for(const e of document.querySelectorAll('p strong, p b, p.lede, .lede, .scene, .lab-lede')){const t=norm(e.textContent);if(t.length>20&&heads.has(t))out.dup.push(t.slice(0,70));}
for(const g of document.querySelectorAll('.lab-cards, .rrow, .bcards, .cards, .card-grid, .work-grid, .pat-grid, .res-grid, .idx-grid')){
  const cards=[...g.children].filter(vis);if(cards.length<3)continue;const links=cards.map(c=>c.matches('a')?c:c.querySelector('a')).filter(Boolean);
  const kinds=new Set(links.map(a=>(a.getAttribute('href')||'').startsWith('#')?'anchor':'page'));
  const nums=cards.map(c=>/\d/.test((c.querySelector('.lab-tags,.bcard-s,.tags,.meta')||{textContent:''}).textContent));
  const mixedNum=nums.some(Boolean)&&!nums.every(Boolean);
  if(kinds.size>1||mixedNum) out.grids.push({grid:name(g),mixedTargets:kinds.size>1,mixedNumbers:mixedNum});
}
return out;})()"""
PLANT = "(()=>{const s=document.createElement('style');s.textContent='main > .section .lab-wrap, main > section > *, .page-head > .xi-process-004{max-width:40% !important;margin:0 auto !important}';document.head.appendChild(s);return 1})()"


def main():
    findings = []
    with cdp.Browser() as br:
        br.viewport(1440, 900)
        br.navigate(f'{BASE}/lab/loop.html', settle=1.2); br.eval(PLANT)
        d = br.eval_json(JS)
        if not d['bands']:
            print('CALIBRATION FAILED: a band forced to 40% width was not reported'); return 2
        print('  calibrated: a band forced to 40% width goes red')
        for w in WIDTHS:
            br.viewport(w, 900)
            for rel in pages(include_book=False):
                br.navigate(f'{BASE}/{rel}', settle=1.2)
                d = br.eval_json(JS)
                ex = EXEMPT.get(rel, [])
                for b in d['bands']:
                    if b['band'] in ex: continue
                    findings.append(f"NARROW-BAND   {rel:42} @{w:<5} {b['band'][:40]:40} covers {b['cover']:.2f} of its width (h{b['h']})")
                h = d['hero']
                if w == 1440 and h and h['cover'] < 0.6 and not h['object'] and h['band'] not in ex:
                    findings.append(f"NAKED-HERO    {rel:42} @{w:<5} {h['band'][:40]:40} covers {h['cover']:.2f}, nothing beside the claim")
                if w == 1440:
                    for t in d['dup']: findings.append(f"DOUBLE-ENDING {rel:42}        {t!r}")
                    for g in d['grids']: findings.append(f"MIXED-GRID    {rel:42}        {g['grid'][:40]:40} targets={'mixed' if g['mixedTargets'] else 'same'} numbers={'mixed' if g['mixedNumbers'] else 'same'}")
    for f in findings: print('  ' + f)
    n = len(WIDTHS) * len(pages(include_book=False))
    print(f'{len(findings)} composition finding(s) across {n} page-widths.')
    print('CANNOT SEE: whether a full band is good, interior alignment, post-interaction states, or the book.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
