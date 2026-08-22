#!/usr/bin/env python3
"""Fail if any page still PAINTS a colour from the retired classic palette
while the Ember theme is active.

This is the answer to "how can I be confident the port is complete?" — it does
not read CSS or count classes, it reads the colour each element actually
renders, so a component Ember never restyled shows up as a hard failure.
Self-calibrating: plants a known remnant and requires the check to go red.
"""
import subprocess, sys, json, re, html as H, pathlib, os
import sys as _sys, os as _os
# Trackers are refused for every browser this repo drives — see cdp.py.
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG

CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# classic-theme values that must never render under ember
RETIRED = {"#515863":"slate ink","#e3e6ea":"slate line","#16181d":"slate bg",
  "#0e7a5f":"classic green","#0e6e56":"classic green dk","#7e5a14":"dark gold",
  "#7a5410":"dark gold","#d4a85e":"muted gold","#8b93a1":"slate dim",
  "#464c56":"slate 2","#3a3f48":"slate 3","#2e323a":"slate 4","#22252b":"slate 5",
  "#f4f5f7":"slate paper"}
# elements inside a deliberately cream/paper artifact keep the classic palette
# artifacts that DEPICT the real product keep the paper palette on purpose:
# the plate mockups (.plA-*…), the paper figures, the boarding-pass card.
EXEMPT_ANCESTORS = ["fig-paper","recon","pass","plate","paper","mock","artifact","browser",
  "pla-","plf-","plm-","plo-","plp-","plv-"]

PROBE = """<!doctype html><html><body><script>
const RET=%s, EX=%s;
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:1280px;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;
 const hex=c=>{const m=(c||'').match(/[\\d.]+/g); if(!m||m.length<3)return null;
   if(m.length>3&&+m[3]===0)return null;
   return '#'+m.slice(0,3).map(v=>(+v).toString(16).padStart(2,'0')).join('');};
 const exempt=el=>{let n=el;while(n&&n.tagName!=='BODY'){
   const c=(n.className+'').toLowerCase(); if(EX.some(x=>c.includes(x)))return true; n=n.parentElement;} return false;};
 // BLIND SPOT, stated because it cost a wrong "fix": this walks backgroundColor up the
 // tree, so it only sees cream a PARENT declares. Cream painted by a pseudo-element, a
 // gradient or a background-image is invisible to it, and the label then looks like it is
 // on the dark page when the rendered pixels are #F4ECDA. When this gate and contrast-audit
 // disagree, contrast-audit wins — it samples what was actually painted. The class-name
 // exempt list above is what covers the overlay cases; name the surface.
 // The ink follows the SURFACE, never the component name. A label that has crossed onto a
 // cream plate takes the paper palette on purpose — that is the design system's rule, and
 // #7E5A14 is 5.62:1 on cream where the page amber is 1.33:1. Judging by ancestor CLASS
 // NAME missed every paper plate not spelled "paper" (.pat-card), so the gate called a
 // deliberate, accessible, correct ink a port failure. Measure the ground instead.
 const ground=el=>{let n=el;while(n){const m=((w.getComputedStyle(n).backgroundColor)||'').match(/[\d.]+/g);
   if(m&&m.length>=3&&(m.length<4||+m[3]>0.5)){const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
     return 0.2126*f(+m[0])+0.7152*f(+m[1])+0.0722*f(+m[2]);}
   n=n.parentElement;} return 0;};
 const hits={};
 d.querySelectorAll('body *').forEach(el=>{const cs=w.getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return;
  if(exempt(el))return;
  ['color','backgroundColor','borderTopColor','borderLeftColor'].forEach(p=>{
   const h=hex(cs[p]); if(h&&RET[h]){
    // ink on a light ground is the paper palette doing its job, not a remnant
    if(p==='color'&&ground(el)>0.5)return;
    // border colours only count when the border is actually drawn
    if(p.startsWith('border')&&parseFloat(cs[p.replace('Color','Width')])===0)return;
    const k=h+'|'+p+'|'+(el.tagName+'.'+((el.className+'').trim().split(/\\s+/)[0]||''));
    hits[k]=(hits[k]||0)+1;}});});
 document.title='R:'+JSON.stringify(Object.entries(hits).slice(0,8));
}catch(e){document.title='R:[["ERR|'+String(e).slice(0,70)+'|",1]]'}},2600);};
</script></body></html>"""

def scan(page):
    open("__tr.html","w").write(PROBE % (json.dumps(RETIRED), json.dumps(EXEMPT_ANCESTORS), page))
    try:
        r = subprocess.run([CH,"--headless=new",NO_TRACKING_FLAG,"--disable-gpu","--no-sandbox",
            "--window-size=1400,1000","--virtual-time-budget=9000","--dump-dom",
            "http://localhost:8000/__tr.html"], capture_output=True, text=True, timeout=90)
        m = re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        return json.loads(H.unescape(m.group(1))) if m else [["NO-RESULT||",1]]
    except Exception as e:
        return [[f"ERR|{str(e)[:60]}|",1]]
    finally:
        if os.path.exists("__tr.html"): os.unlink("__tr.html")

def calibrate():
    css = pathlib.Path("ember.css"); orig = css.read_text()
    css.write_text(orig + '\nhtml[data-theme="ember"] h1{color:#515863!important}\n')
    try: red = bool(scan("index.html"))
    finally: css.write_text(orig)
    if not red:
        print("[calibration] FAIL — planted remnant #515863 on h1 was NOT caught.\n             Either the check is blind or the browser served a cached ember.css."); sys.exit(2)
    print("[calibration] PASS — planted classic-palette remnant caught")

if __name__ == "__main__":
    pages = sys.argv[1:]
    if not pages:
        calibrate()
        pages = [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
                 if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules')
                    for x in p.parts) and not p.name.startswith('_')]
    bad = 0
    for pg in pages:
        hits = scan(pg)
        if hits:
            bad += 1; print(f"FAIL {pg}")
            for k, n in hits:
                h, prop, who = k.split("|")
                print(f"       {RETIRED.get(h,h):14} {h}  {prop:16} ×{n:<4} {who}")
        else:
            print(f"ok   {pg}")
    print(f"\n{bad} page(s) still painting the retired classic palette under Ember.")
    sys.exit(1 if bad else 0)
