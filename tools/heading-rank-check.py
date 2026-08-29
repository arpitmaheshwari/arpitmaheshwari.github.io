#!/usr/bin/env python3
"""Fail when ANY heading on a checked page speaks an unregistered rank.

v2 (2026-08-30): site-wide. v1 checked only the homepage's named selectors —
which is a whitelist that can't see a NEW rogue heading. v2 measures EVERY
main h1/h2/h3 on each page and classifies it against the registered ranks and
named component exceptions below; anything unclassified fails. Two page
families exist by design (DESIGN-SYSTEM-EMBER.md §2):

  home family (/, /folio): R1 h2=42/300 (+close 56/300) · R2 h3=22/600 ·
    R3 h3=17/600 · components: .facts h3 20/600 · .rcpt-h 20/400 ·
    .idx h3 14/400 · .chap-n is a span (not audited here)
  case/subpage family: section h2=31/400 · component h2 (.vband h2)=24/400 ·
    component h3: .t-card-title 24/400 · .labc-ish labels 14/500 · h1 hero free

Self-calibrating: plants a rogue size and requires red.
"""
import sys, json, collections
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from cdp import Browser

HOME = ["index.html", "folio/index.html"]
SUB  = ["case-studies/adtech.html","case-studies/fintech.html","case-studies/vc-diligence.html",
        "case-studies/ptc.html","case-studies/o2.html","case-studies/orgos.html",
        "case-studies/planit.html","patterns/index.html","lab/index.html",
        "process/index.html","fit/index.html"]

JS = """JSON.stringify((function(){var out=[];
document.querySelectorAll('main h2, main h3, body > section h2, body > section h3').forEach(function(e){
  if(!e.getBoundingClientRect().height && getComputedStyle(e).position!=='absolute') return;
  var cs=getComputedStyle(e);
  out.push({tag:e.tagName.toLowerCase(), sz:Math.round(parseFloat(cs.fontSize)), w:cs.fontWeight,
    cls:(e.className+''), in_vband:!!e.closest('.vband'), in_facts:!!e.closest('.facts'),
    in_idx:!!e.closest('.idx'), in_lab:!!(e.closest('.labc')||e.closest('.lab3')),
    txt:e.textContent.trim().slice(0,36)});});
return out;})())"""

def classify_home(r):
    if r['tag']=='h2': return r['sz'] in (42,56) and r['w']=='300'
    if 'rcpt-h' in r['cls']: return r['sz']==20 and r['w']=='400'
    if r['in_facts']: return r['sz']==20 and r['w']=='600'
    if r['in_idx']: return r['sz']==14
    return (r['sz'],r['w']) in ((22,'600'),(17,'600'))

def classify_sub(r):
    if r['tag']=='h2':
        if r['in_vband'] or 'card-title' in r['cls']: return r['sz']==24 and r['w']=='400'
        return r['sz']==31 and r['w']=='400'
    if 't-card-title' in r['cls']: return r['sz']==24
    if r['in_lab'] or r['sz']==14: return r['sz']==14
    if 'rcpt-h' in r['cls']: return r['sz']==20
    return (r['sz'],r['w']) in ((22,'600'),(17,'600'),(24,'400'),(20,'400'))

def sweep(br, plant=None):
    bad_all=[]
    for fam, pages, clf in (('home',HOME,classify_home),('sub',SUB,classify_sub)):
        for pg in pages:
            br.navigate(f"http://localhost:8000/{pg}", settle=2.2)
            if plant:
                br.eval("var s=document.createElement('style');s.textContent=%s;document.head.appendChild(s)" % json.dumps(plant)); br.pump(0.4)
            rows=br.eval_json(JS)
            bad=[(pg,r) for r in rows if not clf(r)]
            bad_all += bad
            if not plant:
                print(f"{'FAIL' if bad else 'ok  '} {pg}  ({len(rows)} headings)")
                for pg2,r in bad[:6]:
                    print(f"       {r['tag']} {r['sz']}px w{r['w']}  '{r['txt']}'")
        if plant: break  # calibration only needs one family
    return bad_all

def main():
    with Browser() as br:
        br.viewport(1440,900)
        bad = sweep(br, plant="main h3{font-size:40px !important;font-weight:300 !important}")
        if not bad:
            print("[calibration] FAIL — planted 40px rogue h3 not flagged; instrument blind."); sys.exit(2)
        print(f"[calibration] PASS — planted rogue flagged ({len(bad)} rows)")
        bad = sweep(br)
        if bad:
            print(f"\n{len(bad)} heading(s) OFF RANK site-wide."); sys.exit(1)
        print("\nall pages on rank.")

if __name__ == "__main__":
    main()
