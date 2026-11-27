#!/usr/bin/env python3
"""rule-density-check.py — the same separator device repeated until a band reads as a grid of lines.

WHY (2026-09-15, Arpit, twice in one evening: "this section has too many rule lines" on the homepage's
"How I lead" block, then "it's not about horizontal rules, it's about repetitive patterns" on "The quality bar
is code" — four list rows, five ledger rows and three underlined links, eleven rules in one band). Every gate
here reads one element (its own border is fine) or one band's padding. None counts how many times one visual
device repeats inside a band. This does.

METHOD, at 1440 and 390: for every act-level band (main > section, and the article wrappers), count the
painted horizontal rules a reader sees inside it — an <hr>, or a block's border-top / border-bottom of 1px+
that spans at least 40% of the band. Table cells, the rails' contents lists, code, controls and the
instrument panels that draw their own internal rules on purpose are skipped (EXEMPT, each with its reason).
  DENSE   more than 4 rules in one band (a border on all four sides is a box, not a rule, and is not counted)
  DOUBLED two rules from different elements within 40px of each other (a rule drawn on a rule)
  STACKED two rules anywhere on the page with no text between them, however far apart (2026-11-26)
  HEADING a heading ruled on both sides: the only text between two rules is a heading or its eyebrow (2026-11-26)
WHY THE LAST TWO (2026-11-26, Arpit: "There are so many separators on the homepage, separators are supposed to
give a break point, multiple separators are not helpful"). This gate was green on a homepage with 48 rules on a
phone. Three blind spots, each structural: it counted rules INSIDE a band, so a section's own top line never met
the chapter rule 49px below it; DOUBLED stopped at 40px; and the instrument panels were exempt wholesale. The
page-level pass below has no band and no exemption list (tables only: on a phone their hidden header row still
has a box). The rule it enforces is DESIGN-SYSTEM.md section 6, "One break, one mark".
CALIBRATION: a page is loaded with five <hr> injected into one band and must go red; and two <hr> planted
back to back must be reported as STACKED.
Exit: 0 clean / 1 finding(s) / 2 calibration failed.
CANNOT SEE: whether the rules that remain are the right ones, repeats of OTHER devices (dashed boxes, chips,
underlines drawn as background), rules drawn by images or shadows, the book, or any state after interaction.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import pages

BASE = os.environ.get('BASE', 'http://localhost:8000')
WIDTHS = (1440, 390)
DENSE_MAX, DOUBLE_GAP = 4, 40
EXEMPT = {
    'table,tr,td,th': 'a table is rows by definition',
    '.ia-toc,.ia-rail,.lh-side,.lh-log': 'the rails list sections; their left rule is the device',
    '.rcpt-rows,.rcpt-r,.rcpt-r-tight,.rcpt-box': 'the receipt is a ledger the reader opened on purpose (2026-08); the case pages carry the same ledger inline',
    '.rule-list,.lint-findings,.lint-stats': "trustlint's rules and findings ARE lists; the rows are the content",
    '.fr,.hero-facts,.rs-facts': "the Candidate Facts card is a nutrition label by design (2026-08); the hero's fact sheet is four labelled rows, his pick (2026-11-24, Arpit: '1 · Fact sheet'); the résumé's fact card is the same sheet, five rows in one card (2026-11-27: counted only on a phone, where a row spans the band)",
    '.td-block,.td-scroll,.td-ledger,.td-fig': 'the teardown ledger is measurements in rows',
    '.lab-fn,.vg,.lh-inst,.dsg-card,.recon,.rxp-cat,.rxo-panel,.hero-demo,.hd-card,.pd,.vid-frame,.card-wire,.artalt,.thesis,.card-gold,.fig-paper,.bp,.boarding,[class*="-chrome"],[class*="pl"][class*="-bar"]': 'an instrument or reconstruction draws its own internal lines',
    'body.p-writing .xi-resources-004': 'the writing index is a list of essays, one ruled row each; six since 2026-11-27 (Arpit: "publish")',
    'pre,code,button,input,select,textarea,.cta,.rcpt-btn,nav,#nav,footer': 'controls and chrome',
}
SKIP = ','.join(EXEMPT.keys())
JS = r"""(()=>{
const vis=e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.display!=='none'&&cs.visibility!=='hidden'&&cs.opacity!=='0'};
const painted=c=>c&&c!=='transparent'&&!/rgba\(\d+, \d+, \d+, 0\)/.test(c);
const SKIP=%s;
const all=[...document.querySelectorAll('main section, main > header, .page-head, main > div, main > .xi-process-004 > section')].filter(vis).filter(b=>b.getBoundingClientRect().height>=200);
const bands=all.filter(b=>!all.some(o=>o!==b&&b.contains(o)));   /* innermost bands only: a whole article is not one band, its sections are */
const out=[];
for(const b of bands){
  const bw=b.getBoundingClientRect().width;const rules=[];
  for(const e of b.querySelectorAll('*')){
    if(!vis(e)||e.closest(SKIP))continue;const cs=getComputedStyle(e);const r=e.getBoundingClientRect();
    const name=e.tagName.toLowerCase()+'.'+(e.className||'').toString().trim().split(/\s+/).slice(0,2).join('.');
    if(e.tagName==='HR'){rules.push({y:Math.round(r.top+scrollY),el:name});continue;}
    if(r.width<bw*0.4)continue;
    if(parseFloat(cs.borderLeftWidth)>=1&&parseFloat(cs.borderRightWidth)>=1)continue;   /* a box is not a rule: four sides make a card, and card-density is another gate's question */
    if(e.tagName==='ABBR')continue;   /* a dotted underline on a term is a text convention, not a separator */
    if(parseFloat(cs.borderTopWidth)>=1&&cs.borderTopStyle!=='none'&&painted(cs.borderTopColor))rules.push({y:Math.round(r.top+scrollY),el:name});
    if(parseFloat(cs.borderBottomWidth)>=1&&cs.borderBottomStyle!=='none'&&painted(cs.borderBottomColor))rules.push({y:Math.round(r.bottom+scrollY),el:name});
  }
  rules.sort((a,b)=>a.y-b.y);const d=[];for(const x of rules){if(!d.length||x.y-d[d.length-1].y>2)d.push(x);}
  const bn=b.tagName.toLowerCase()+(b.id?'#'+b.id:'')+'.'+(b.className||'').toString().trim().split(/\s+/).slice(0,1).join('');
  if(d.length>%d){const fam={};d.forEach(x=>fam[x.el]=(fam[x.el]||0)+1);out.push({kind:'DENSE',band:bn,n:d.length,fam:Object.entries(fam).map(([k,v])=>k+'×'+v).join(' · ')});}
  for(let i=0;i+1<d.length;i++){if(d[i+1].y-d[i].y<=%d&&d[i].el!==d[i+1].el)out.push({kind:'DOUBLED',band:bn,n:2,fam:d[i].el+' + '+d[i+1].el+' @y'+d[i].y});}
}
return out;})()""" % (repr(SKIP), DENSE_MAX, DOUBLE_GAP)
JS_PAGE = r"""(()=>{
const vw=innerWidth,lines=[];const M=document.querySelector('main')||document.body;
const sel=e=>e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+'.'+(e.className||'').toString().trim().split(/\s+/).filter(c=>!/^xi-/.test(c)).slice(0,2).join('.');
const closed=e=>e.closest('details:not([open])')&&!e.closest('summary');
for(const e of M.querySelectorAll('*')){
  if(e.closest('table'))continue;const r=e.getBoundingClientRect();if(r.width<vw*0.5||(r.height===0&&e.tagName!=='HR'))continue;
  const cs=getComputedStyle(e);if(cs.display==='none'||cs.visibility==='hidden'||closed(e))continue;const Y=r.top+scrollY;
  if(e.tagName==='HR'){lines.push({y:Math.round(Y),s:sel(e),side:'hr'});continue;}
  if(parseFloat(cs.borderLeftWidth)>0)continue;   /* a box, not a rule */
  for(const side of ['Top','Bottom']){const w=parseFloat(cs['border'+side+'Width'])||0;const c=cs['border'+side+'Color'];
    if(w>0&&cs['border'+side+'Style']!=='none'&&!/, 0\)$/.test(c)&&c!=='transparent')lines.push({y:Math.round(side==='Top'?Y:Y+r.height),s:sel(e),side});}
}
lines.sort((a,b)=>a.y-b.y);const texts=[];const w=document.createTreeWalker(M,NodeFilter.SHOW_TEXT);let n;
while(n=w.nextNode()){if(!n.nodeValue.trim())continue;const p=n.parentElement;if(!p||p.closest('script,style,.visually-hidden,.sr-only')||closed(p))continue;
  const cs=getComputedStyle(p);if(cs.display==='none'||cs.visibility==='hidden')continue;const g=document.createRange();g.selectNodeContents(n);const b=g.getBoundingClientRect();
  if(!b.height||!b.width)continue;texts.push({c:b.top+scrollY+b.height/2,h:!!p.closest('h1,h2,h3,h4,header.chap,[class*=eyebrow],.chapter-k,.lbl')});}
const out=[];for(let i=1;i<lines.length;i++){const A=lines[i-1],B=lines[i];if(A.s===B.s&&A.side===B.side)continue;const gap=B.y-A.y;if(gap>700)continue;
  const bt=texts.filter(t=>t.c>A.y&&t.c<B.y);const kind=!bt.length?'STACKED':(bt.every(t=>t.h)?'HEADING':null);
  if(kind)out.push({kind,band:'page',n:2,fam:A.s+' '+A.side+' + '+B.s+' '+B.side+' @y'+A.y+' gap '+gap});}
return out;})()"""
PLANT_STACK = "(()=>{const m=document.querySelector('main');for(let i=0;i<2;i++){const h=document.createElement('hr');h.className='planted'+i;h.style.cssText='margin:0 0 30px;border:0;border-top:1px solid #000;width:100%';m.insertBefore(h,m.firstChild);}return 1})()"
PLANT = "(()=>{const s=document.querySelector('main > section');for(let i=0;i<5;i++){const h=document.createElement('hr');h.style.cssText='margin:40px 0;border:0;border-top:1px solid #000';s.appendChild(h);}return 1})()"


def main():
    findings = []
    with cdp.Browser() as br:
        br.viewport(1440, 900)
        br.navigate(f'{BASE}/lab/plugin.html', settle=1.2); br.eval(PLANT)
        if not [o for o in br.eval_json(JS) if o['kind'] == 'DENSE']:
            print('CALIBRATION FAILED: five planted rules in one band were not reported'); return 2
        print('  calibrated: five planted rules in one band go red')
        br.navigate(f'{BASE}/lab/plugin.html', settle=1.2); br.eval(PLANT_STACK)
        if not [o for o in br.eval_json(JS_PAGE) if o['kind'] == 'STACKED' and 'planted' in o['fam']]:
            print('CALIBRATION FAILED: two planted rules back to back were not reported as STACKED'); return 2
        print('  calibrated: two planted rules with nothing between them go red')
        for w in WIDTHS:
            br.viewport(w, 900)
            for rel in pages(include_book=False):
                br.navigate(f'{BASE}/{rel}', settle=1.2)
                for o in br.eval_json(JS) + br.eval_json(JS_PAGE):
                    findings.append(f"{o['kind']:8} {rel:42} @{w:<5} {o['band'][:34]:34} {o['n']:>2} rules  {o['fam'][:110]}")
    seen = set(); uniq = [f for f in findings if not (f in seen or seen.add(f))]
    for f in uniq: print('  ' + f)
    print(f'{len(uniq)} rule-density finding(s) across {len(WIDTHS) * len(pages(include_book=False))} page-widths.')
    print('CANNOT SEE: inner rules of a bordered card (rule 4 of "One break, one mark" is looked at, not gated), other repeated devices (dashed boxes, chips), rules drawn by images or shadows, the book, or post-interaction states.')
    return 1 if uniq else 0


if __name__ == '__main__':
    sys.exit(main())
