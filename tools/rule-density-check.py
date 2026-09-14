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
CALIBRATION: a page is loaded with five <hr> injected into one band and must go red.
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
    '.rule-list': "trustlint's seven rules ARE a list; the rows are the content",
    '.fr': "the Candidate Facts card is a nutrition label by design (2026-08)",
    '.td-block,.td-scroll': 'the teardown table is measurements in rows',
    '.lab-fn,.vg,.lh-inst,.dsg-card,.recon,.rxp-cat,.rxo-panel,.hero-demo,.hd-card,.pd,.vid-frame,.card-wire,.artalt,.thesis,.card-gold,.fig-paper,.bp,.boarding,[class*="-chrome"],[class*="pl"][class*="-bar"]': 'an instrument or reconstruction draws its own internal lines',
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
PLANT = "(()=>{const s=document.querySelector('main > section');for(let i=0;i<5;i++){const h=document.createElement('hr');h.style.cssText='margin:40px 0;border:0;border-top:1px solid #000';s.appendChild(h);}return 1})()"


def main():
    findings = []
    with cdp.Browser() as br:
        br.viewport(1440, 900)
        br.navigate(f'{BASE}/lab/plugin.html', settle=1.2); br.eval(PLANT)
        if not [o for o in br.eval_json(JS) if o['kind'] == 'DENSE']:
            print('CALIBRATION FAILED: five planted rules in one band were not reported'); return 2
        print('  calibrated: five planted rules in one band go red')
        for w in WIDTHS:
            br.viewport(w, 900)
            for rel in pages(include_book=False):
                br.navigate(f'{BASE}/{rel}', settle=1.2)
                for o in br.eval_json(JS):
                    findings.append(f"{o['kind']:8} {rel:42} @{w:<5} {o['band'][:34]:34} {o['n']:>2} rules  {o['fam'][:110]}")
    seen = set(); uniq = [f for f in findings if not (f in seen or seen.add(f))]
    for f in uniq: print('  ' + f)
    print(f'{len(uniq)} rule-density finding(s) across {len(WIDTHS) * len(pages(include_book=False))} page-widths.')
    print('CANNOT SEE: other repeated devices (dashed boxes, chips), rules drawn by images or shadows, the book, or post-interaction states.')
    return 1 if uniq else 0


if __name__ == '__main__':
    sys.exit(main())
