#!/usr/bin/env python3
"""Fail when a page's content leaves LOPSIDED empty space.

Why this exists: every gate here checked whether content stayed on screen, was
readable, or used the right colour. None asked whether the space AROUND the
content was balanced — so a text column capped narrower than its container and
left-aligned passed everything while leaving a 457px void down one side. That
defect shipped on six pages and was found by eye, twice, after I had reported
the layout fixed. Whitespace is designed or it is a defect; this measures it.

Method: for each page, take the body paragraphs, and compare the median gap
from the viewport's left edge to the median gap on the right. A difference

# Guarantee the server these gates assume. Every one of them hard-codes
# http://localhost:8000 and none checked it was there; when it was not, they did not report
# "no server", they reported findings (see cdp.ensure_server). Idempotent: reuses a server
# that is already listening, so a dev server is never disturbed or double-bound.
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
beyond TOL means the reading column is not centred in the space it occupies.
Self-calibrating: plants a one-sided margin and requires the check to go red.
"""
import sys as _gl_s, os as _gl_o
_gl_s.path.insert(0, _gl_o.path.dirname(_gl_o.path.abspath(__file__)))
from gatelib import planted   # locked plant/restore — see gatelib for why
import subprocess, sys, json, re, html as H, pathlib, os
import sys as _sys, os as _os
# Trackers are refused for every browser this repo drives — see cdp.py.
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG

# $CHROME first: every CI runner is Linux and this path is macOS-only.

# Eleven tools pinned it, so fixing cdp.py alone would only have moved the

# CI failure to the next step that launches Chrome.

CH = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TOL = 48   # px of allowed left/right asymmetry
W   = 1440

PROBE = """<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:%dpx;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;
 const vw=d.documentElement.clientWidth;
 const ps=[...d.querySelectorAll('main p, main li')].filter(p=>{
   const cs=w.getComputedStyle(p);
   if(cs.display==='none'||cs.visibility==='hidden')return false;
   if(cs.textAlign==='center')return false;          // deliberately centred text
   let n=p; while(n&&n.tagName!=='BODY'){const c=(n.className+'').toLowerCase();
     if(/pl[a-z]-|fig-paper|recon|pass|mock|browser|card|note|gate|vitals/.test(c))return false;
     n=n.parentElement;}
   return p.textContent.trim().length>80 && p.getBoundingClientRect().width>120;});
 if(ps.length<3){document.title='R:{"skip":1,"n":'+ps.length+'}';return;}
 const med=a=>a.slice().sort((x,y)=>x-y)[Math.floor(a.length/2)];
 // A gap is only a VOID if nothing lives in it. A two-column band — prose left,
 // an artifact right — is a composition, not a defect, and a check that cannot
 // tell them apart is a check I will learn to ignore. So for each paragraph,
 // look for any painted element beside it, overlapping its vertical band.
 const all=[...d.querySelectorAll('body *')].map(e=>({e,r:e.getBoundingClientRect()}))
   .filter(o=>o.r.width>24&&o.r.height>16&&w.getComputedStyle(o.e).visibility!=='hidden');
 const lonely=ps.filter(p=>{const pr=p.getBoundingClientRect();
   return !all.some(o=>o.e!==p&&!p.contains(o.e)&&!o.e.contains(p)
     && o.r.top<pr.bottom-4 && o.r.bottom>pr.top+4
     && (o.r.left>=pr.right+24 || o.r.right<=pr.left-24));});
 if(lonely.length<3){document.title='R:{"skip":1,"paired":'+(ps.length-lonely.length)+'}';return;}
 // THE READING COLUMN IS THE DOMINANT AXIS, not a blind median. A demo widget's
 // right-hand list (7 items at x=757 on lab/eval) once outvoted the prose and
 // produced a phantom skew — the page's actual column was dead centre. Cluster
 // left edges (12px bins), take the largest cluster as the column, and judge
 // balance for THAT column only; off-axis items are compositions.
 const bins={};
 lonely.forEach(p=>{const l=Math.round(p.getBoundingClientRect().left/12)*12;(bins[l]=bins[l]||[]).push(p);});
 const col=Object.values(bins).sort((a,b)=>b.length-a.length)[0];
 if(col.length<3){document.title='R:{"skip":1,"paired":0}';return;}
 const L=med(col.map(p=>Math.round(p.getBoundingClientRect().left)));
 const R=med(col.map(p=>Math.round(vw-p.getBoundingClientRect().right)));
 document.title='R:'+JSON.stringify({vw,n:col.length,left:L,right:R,skew:Math.abs(L-R)});
}catch(e){document.title='R:{"err":"'+String(e).slice(0,80)+'"}'}},2800);};
</script></body></html>"""

def scan(page):
    open("__bal.html","w").write(PROBE % (page, W))
    try:
        r = subprocess.run([CH,"--headless=new",NO_TRACKING_FLAG,"--disable-gpu","--no-sandbox",
            f"--window-size={W+80},1000","--virtual-time-budget=9000","--dump-dom",
            "http://localhost:8000/__bal.html"], capture_output=True, text=True, timeout=90)
        m = re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        return json.loads(H.unescape(m.group(1))) if m else {"err":"no result"}
    except Exception as e:
        return {"err": str(e)[:70]}
    finally:
        if os.path.exists("__bal.html"): os.unlink("__bal.html")

def calibrate():
    # Under gatelib.planted, which holds a lock for the whole plant -> scan -> restore
    # window. Unguarded, two gates doing this at once clobber each other's restore and
    # leave a canary rule in ember.css permanently.
    with planted("ember.css",
                 '\nhtml[data-theme="ember"] body.p-home main p{margin-right:400px!important}\n'):
        d = scan("index.html")
    if d.get("skew",0) <= TOL:
        print(f"[calibration] FAIL — planted 400px one-sided margin gave skew "
              f"{d.get('skew')}. The check cannot see lopsided space."); sys.exit(2)
    print(f"[calibration] PASS — planted one-sided space caught (skew {d['skew']}px)")

if __name__ == "__main__":
    pages = sys.argv[1:]
    if not pages:
        calibrate()
        pages = [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
                 if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules')
                            for x in p.parts) and not p.name.startswith('_')]
    bad = 0
    for pg in pages:
        d = scan(pg)
        if d.get("skip") or d.get("err"):
            print(f"skip {pg}  {d.get('err','too few paragraphs to judge')}"); continue
        if d["skew"] > TOL:
            bad += 1
            print(f"FAIL {pg}\n       reading column {d['left']}px from the left, "
                  f"{d['right']}px from the right — {d['skew']}px of one-sided empty space")
        else:
            print(f"ok   {pg}  (±{d['skew']}px)")
    print(f"\n{bad} page(s) with lopsided whitespace at {W}px (tolerance {TOL}px).")
    sys.exit(1 if bad else 0)
