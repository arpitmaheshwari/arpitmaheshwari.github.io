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
import subprocess, sys, json, re, html as H, pathlib, os, collections

CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

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
    if(/pl[a-z]-|fig-paper|recon|pass|mock/.test(c)){skip=true;break;}n=n.parentElement;}
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
  out.push({sig:[cs.fontFamily.split(',')[0],cs.fontSize,cs.textTransform,
    Math.round(parseFloat(cs.letterSpacing)*10)/10+'', cs.color].join(' | '),
    txt:t.slice(0,34)});});
 document.title='R:'+JSON.stringify(out);
}catch(e){document.title='R:[]'}},2800);};
</script></body></html>"""

def scan(page):
    open("__cg.html","w").write(PROBE % page)
    try:
        r = subprocess.run([CH,"--headless=new","--disable-gpu","--no-sandbox",
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
    css = pathlib.Path("ember.css"); orig = css.read_text()
    css.write_text(orig + '\nhtml[data-theme="ember"] .contract-links a{font-family:Georgia,serif!important;font-size:19px!important}\n')
    try:
        rows = scan("index.html")
        sigs = collections.Counter(r["sig"] for r in rows)
    finally:
        css.write_text(orig)
    if len(sigs) < 2:
        print("[calibration] FAIL — planted 19px Georgia CTA produced no second grammar."); sys.exit(2)
    print("[calibration] PASS — planted off-grammar CTA splits the signature set")

if __name__ == "__main__":
    pages = sys.argv[1:]
    ran_all = not pages
    if ran_all:
        calibrate()
        pages = [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
                 if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules')
                            for x in p.parts) and not p.name.startswith('_')]
    per_page = collect(pages)
    allsigs = collections.Counter(r["sig"] for rows in per_page.values() for r in rows)
    if not allsigs:
        print("no arrow-CTAs found — probe broken?"); sys.exit(2)
    dominant, dn = allsigs.most_common(1)[0]
    total = sum(allsigs.values())
    print(f"house grammar ({dn}/{total} CTAs): {dominant}\n")
    bad = 0
    for pg, rows in per_page.items():
        outliers = [r for r in rows if r["sig"] != dominant]
        if outliers:
            bad += 1; print(f"FAIL {pg}")
            for r in outliers[:6]:
                print(f"       '{r['txt']}'\n        speaks: {r['sig']}")
        elif rows:
            print(f"ok   {pg}  ({len(rows)} CTAs on grammar)")
    print(f"\n{bad} page(s) with off-grammar CTAs.")
    sys.exit(1 if bad else 0)
