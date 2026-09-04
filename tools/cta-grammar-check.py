#!/usr/bin/env python3
"""Fail when a CTA link speaks a different grammar than the house one.

Why this exists: three defects in a row lived in the same blind spot — an
element doing the SAME JOB as its siblings (a heading, an arrow-CTA) but
styled from a different era. Colour gates pass it (its colours are legal
tokens); geometry gates pass it (it fits). The defect is inconsistency, and
inconsistency is only visible as a DIFF of the same component across pages.

Method: collect every text link ending in an arrow across all pages, build a
grammar signature (family, size, tracking, transform, color), find the
dominant signature, and fail every outlier. Buttons/pills are excluded — they
are a different component. Self-calibrating: plants an off-grammar CTA and
requires red.
"""
import sys as _gl_s, os as _gl_o
_gl_s.path.insert(0, _gl_o.path.dirname(_gl_o.path.abspath(__file__)))
from gatelib import planted   # locked plant/restore — see gatelib for why
import subprocess, sys, json, re, html as H, pathlib, os, collections
import sys as _sys, os as _os

# Guarantee the server these gates assume. Every one of them hard-codes
# http://localhost:8000 and none checked it was there; when it was not, they did not report
# "no server", they reported findings (see cdp.ensure_server). Idempotent: reuses a server
# that is already listening, so a dev server is never disturbed or double-bound.
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
# Trackers are refused for every browser this repo drives — see cdp.py.
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG

# $CHROME first: every CI runner is Linux and this path is macOS-only.

# Eleven tools pinned it, so fixing cdp.py alone would only have moved the

# CI failure to the next step that launches Chrome.

CH = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROBE = """<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:1440px;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;const out=[];
 d.querySelectorAll('main a, footer a').forEach(a=>{
  const t=a.textContent.trim(); if(!/[\\u2192\\u2197]\\s*$/.test(t))return;
  const cs=w.getComputedStyle(a); const r=a.getBoundingClientRect();
  if(r.width<8||cs.display==='none')return;
  // buttons/pills carry a fill or heavy border — different component, skip
  if(cs.backgroundColor!=='rgba(0, 0, 0, 0)'||cs.backgroundImage!=='none')return;
  if(parseFloat(cs.borderTopWidth)>0.5)return;
  // links inside plate/paper artifacts keep artifact styling — skip
  let n=a,skip=false; while(n&&n.tagName!=='BODY'){const c=(n.className+'').toLowerCase();
    if(/pl[a-z]-|fig-paper|recon|pass|mock|card-p\\d|thought-card|lab-card|\\blane\\b/.test(c)){skip=true;break;}n=n.parentElement;}
  if(skip)return;
  // TWO SPECIES: a STANDALONE CTA (the link is its block's content) must speak
  // the house grammar; an INLINE link flowing inside a sentence correctly
  // inherits the prose around it and is not this component. A link is
  // standalone when it makes up most of its block's text.
  // standalone = the block is MADE OF links (nav row, CTA row); inline = the
  // block is prose that happens to contain a link. Judge the block, not the link:
  // subtract every child link's text from the block's — what remains is prose.
  const block=a.closest('p,div,li,figcaption')||a.parentElement;
  if(block){
    const linkLen=[...block.querySelectorAll('a')].reduce((n,x)=>n+x.textContent.trim().length,0);
    const proseLen=block.textContent.trim().length-linkLen;
    if(proseLen>block.textContent.trim().length*0.3)return; // prose block: inline link, exempt
  }
  // the GROUND decides which house ink is correct: the paper act remaps the
  // same component to a darker violet by design (one component, two grounds)
  let g=a, ground='dark';
  while(g){const b=w.getComputedStyle(g).backgroundColor;
    const mm=b.match(/rgba?\((\d+), (\d+), (\d+)/);
    if(mm && (!/rgba/.test(b) || !/, 0\)$/.test(b))){
      ground=(0.2126*mm[1]+0.7152*mm[2]+0.0722*mm[3])>128?'paper':'dark';break;}
    g=g.parentElement;}
  out.push({sig:[cs.fontFamily.split(',')[0],cs.fontSize,cs.textTransform,
    Math.round(parseFloat(cs.letterSpacing)*10)/10+''].join(' | '),
    ink:cs.color, ground:ground,
    txt:t.slice(0,34)});});
 document.title='R:'+JSON.stringify(out);
}catch(e){document.title='R:[]'}},2800);};
</script></body></html>"""

def scan(page):
    open("__cg.html","w").write(PROBE % page)
    try:
        r = subprocess.run([CH,"--headless=new",NO_TRACKING_FLAG,"--disable-gpu","--no-sandbox",
            "--window-size=1520,1000","--virtual-time-budget=9000","--dump-dom",
            "http://localhost:8000/__cg.html"], capture_output=True, text=True, timeout=90)
        m = re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        return json.loads(H.unescape(m.group(1))) if m else []
    except Exception:
        return []
    finally:
        if os.path.exists("__cg.html"): os.unlink("__cg.html")

def collect(pages):
    per_page = {}
    for pg in pages:
        per_page[pg] = scan(pg)
    return per_page

def calibrate():
    # Plant the canary on ONE CTA and leave at least one untouched witness.
    # (2026-08-29: the old canary hit `.contract-links a`, which after the
    # four-act restructure was EVERY qualifying CTA on the homepage — all rows
    # turned Georgia together, one signature remained, and the calibration
    # could not split. An instrument that repaints its whole sample has no
    # baseline to diff against.)
    base = scan("index.html")
    base_sigs = collections.Counter(r["sig"] for r in base)
    if len(base) < 2:
        print(f"[calibration] FAIL — index.html has {len(base)} qualifying CTA(s); "
              "need >=2 so the canary can differ from a witness."); sys.exit(2)
    # Under gatelib.planted — locked plant -> scan -> restore. Unguarded, this raced with
    # theme-remnant-check and balance-check, which plant into the same file.
    with planted("ember.css",
                 '\nhtml[data-theme="ember"] #patterns .contract-links a'
                 '{font-family:Georgia,serif!important;font-size:19px!important}\n'):
        rows = scan("index.html")
        sigs = collections.Counter(r["sig"] for r in rows)
    if len(sigs) <= len(base_sigs):
        print("[calibration] FAIL — planted 19px Georgia CTA on #patterns .contract-links "
              "did not add a signature (selector matched nothing, or probe blind)."); sys.exit(2)
    print(f"[calibration] PASS — canary split the set ({len(base_sigs)} -> {len(sigs)} grammars), witness intact")

if __name__ == "__main__":
    pages = sys.argv[1:]
    ran_all = not pages
    if ran_all:
        calibrate()
        pages = [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
                 if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules')
                            for x in p.parts) and not p.name.startswith('_')]
    per_page = collect(pages)
    # TYPE grammar (face/size/case/tracking) must be ONE, site-wide. INK is
    # judged against the GROUND: the design system deliberately maps the same
    # component to a darker violet on the paper act (2026-09-03 — one ground-
    # blind signature made two correct inks read as two grammars, the majority
    # of a 2-CTA sample picked the paper one, and the calibration canary could
    # only swap a signature, never add one).
    HOUSE_INK = {"dark": "rgb(232, 107, 255)",    # --link on dark grounds
                 "paper": "rgb(107, 58, 153)"}    # --link inside the cream act
    allsigs = collections.Counter(r["sig"] for rows in per_page.values() for r in rows)
    if not allsigs:
        print("no arrow-CTAs found — probe broken?"); sys.exit(2)
    dominant, dn = allsigs.most_common(1)[0]
    total = sum(allsigs.values())
    print(f"house grammar ({dn}/{total} CTAs): {dominant}\n")
    bad = 0
    for pg, rows in per_page.items():
        outliers = [r for r in rows if r["sig"] != dominant
                    or r.get("ink") not in (None, HOUSE_INK.get(r.get("ground", "dark")))]
        if outliers:
            bad += 1; print(f"FAIL {pg}")
            for r in outliers[:6]:
                why = r["sig"] if r["sig"] != dominant else (
                    f"ink {r.get('ink')} on a {r.get('ground')} ground "
                    f"(house: {HOUSE_INK.get(r.get('ground','dark'))})")
                print(f"       '{r['txt']}'\n        speaks: {why}")
        elif rows:
            print(f"ok   {pg}  ({len(rows)} CTAs on grammar)")
    print(f"\n{bad} page(s) with off-grammar CTAs.")
    sys.exit(1 if bad else 0)
