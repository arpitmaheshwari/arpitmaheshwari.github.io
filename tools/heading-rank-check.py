#!/usr/bin/env python3
"""Fail when a homepage heading leaves its rank.

Why this exists (2026-08-30): the measured homepage carried h2s at 42/44/48/64
and h3s at 40/30/26/20/19/14 — six sizes for one semantic level, and a
subsection row ("Eval design before interface design") rendering at the same
40px as the section titles above it. No property gate saw it, because every
size was individually legal; the defect was RANK DRIFT, visible only as a
census of one level across the page. Arpit picked Option C (one identity per
rank); this gate keeps it.

Ranks (DESIGN-SYSTEM-EMBER.md § 2, verified against rendered pixels at 1440):
  R1  every main h2        -> 42px w300   (exception: #h-close at 56px)
  R2  #h-lead, .lane h3, .thought-title          -> 22px w600
  R3  .memo h3, .contract .col h3               -> 17px w600 lh1.4, upright

Self-calibrating: plants a 40px rogue h3 and requires red.
"""
import sys, json, collections
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from cdp import Browser

URL = "http://localhost:8000/index.html"

JS = """JSON.stringify((function(){var out=[];
function push(rank,sel){document.querySelectorAll(sel).forEach(function(e){
  var cs=getComputedStyle(e); if(!e.getBoundingClientRect().height && cs.position!=='absolute')return;
  out.push({rank:rank, sz:Math.round(parseFloat(cs.fontSize)), w:cs.fontWeight,
    it:cs.fontStyle, txt:e.textContent.trim().slice(0,40)});});}
push('R1','main h2'); push('R2','#h-lead, .lane h3, .thought-title');
push('R3','.wl-lead .memo h3, .aiwork .memo h3, .contract .col h3');
return out;})())"""

RULES = {
    'R1': lambda r: (r['sz'] in (42, 56) and r['w'] == '300'),
    'R2': lambda r: (r['sz'] == 22 and r['w'] == '600'),
    'R3': lambda r: (r['sz'] == 17 and r['w'] == '600' and r['it'] == 'normal'),
}

def census(br, plant=None):
    br.navigate(URL, settle=3.0)
    if plant:
        br.eval("var s=document.createElement('style');s.textContent=%s;document.head.appendChild(s)" % json.dumps(plant))
        br.pump(0.5)
    return br.eval_json(JS)

def main():
    with Browser() as br:
        br.viewport(1440, 900)
        # calibration: a planted rogue h3 must scream
        rows = census(br, plant=".wl-lead .memo h3{font-size:40px !important;font-weight:300 !important}")
        bad = [r for r in rows if not RULES[r['rank']](r)]
        if not bad:
            print("[calibration] FAIL — planted 40px rogue h3 not flagged; instrument blind.")
            sys.exit(2)
        print(f"[calibration] PASS — planted rogue h3 flagged ({len(bad)} off-rank rows seen)")
        # real run
        rows = census(br)
        bad = [r for r in rows if not RULES[r['rank']](r)]
        cnt = collections.Counter((r['rank'], r['sz'], r['w']) for r in rows)
        for k, v in sorted(cnt.items()):
            print(f"  {v} × {k}")
        if bad:
            print(f"\n{len(bad)} heading(s) OFF RANK:")
            for r in bad[:10]:
                print(f"  {r['rank']} {r['sz']}px w{r['w']} {r['it']}  '{r['txt']}'")
            sys.exit(1)
        print(f"\nall {len(rows)} headings on rank.")

if __name__ == "__main__":
    main()
