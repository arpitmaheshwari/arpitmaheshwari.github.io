#!/usr/bin/env python3
"""Fail if any page still PAINTS a colour from a RETIRED palette.

Three palettes have been retired on this site: the 2026-07 classic (slate inks, dated
gold), the ember dark theme (plum grounds, the four heats, the cream ink) and, on
2026-09-12, every literal that the amber system replaced with a role. A colour from
any of them rendering anywhere outside a reconstruction plate or a paper object is a
rule that never got ported — this reads the colour each element actually renders, so
a component no stylesheet restyled shows up as a hard failure rather than a hunch.

The reconstruction plates (.plA-… .recon, the paper receipts, the sticky notes) quote
somebody else's product or are objects; they keep their own palette and are exempt by
class. Everything else takes the system's roles, on paper AND on a bookend.
Self-calibrating: plants a known remnant and requires the check to go red.
"""
import sys as _gl_s, os as _gl_o
_gl_s.path.insert(0, _gl_o.path.dirname(_gl_o.path.abspath(__file__)))
from gatelib import planted   # locked plant/restore — see gatelib for why
import subprocess, sys, json, re, html as H, pathlib, os
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
# classic-theme values that must never render under ember
RETIRED = {
  # classic (2026-07)
  "#515863":"slate ink","#e3e6ea":"slate line","#16181d":"slate bg","#0e7a5f":"classic green",
  "#0e6e56":"classic green dk","#7e5a14":"dark gold","#7a5410":"dark gold","#d4a85e":"muted gold",
  "#8b93a1":"slate dim","#464c56":"slate 2","#3a3f48":"slate 3","#2e323a":"slate 4","#22252b":"slate 5",
  "#f4f5f7":"slate paper","#0a0a0a":"classic bg","#111111":"classic bg-soft","#141414":"classic card",
  "#e8c88a":"gold light","#a07835":"gold dark","#f2ede4":"classic ink","#4a6b5c":"classic copper",
  "#6b8a7c":"classic copper lt","#5ed48e":"classic ok","#e0736b":"classic err",
  # ember (2026-08 .. 2026-09-12)
  "#120b14":"plum bg","#1b1320":"plum soft","#241830":"plum card","#1e1022":"plum field",
  "#f5ede6":"ember ink","#ff8a5c":"heat ember","#ff6a3d":"heat adtech","#e86bff":"heat violet",
  "#c64bff":"heat fintech","#a96bff":"heat o2","#ffc46b":"heat amber","#ff7aa8":"heat rose",
  "#ff5fa2":"heat ptc","#c98f3f":"ember gold-dark","#ffd28a":"ember gold-light","#ffb08e":"heat2",
  "#ffe0a8":"heat2 amber","#ff9dc6":"heat2 rose","#7fcf9e":"ember ok","#ff9f8a":"ember cannot",
  "#1a0d08":"ember cta ink","#f1e8d6":"cream act bg","#eae0ca":"cream act card","#e6dcc3":"contract card",
  "#20180c":"cream act ink","#221c10":"contract ink","#635848":"cream act muted","#5d5442":"contract muted",
  "#a93a24":"cream red"}
# elements inside a deliberately cream/paper artifact keep the classic palette
# artifacts that DEPICT the real product keep the paper palette on purpose:
# the plate mockups (.plA-*…), the paper figures, the boarding-pass card.
# 2026-09-20: three more DEPICTIONS, found by this gate failing in CI on every build.
#   card-wire  — the wireframes on the pattern pages that illustrate an AI UI. The green
#                pill behind "92%" is the depicted product's confidence colour.
#   bk-device  — the device mark in the book: a drawing of hardware, not site chrome.
#   lh-log / lh-inst — the Lab's test-run log. Its checkmarks are green because a passing
#                test is green; repainting those to the amber system would make the
#                instrument LIE about what a terminal shows.
# The test for this list is not "does the gate go quiet" — it is whether the element
# DEPICTS something (a product, a document, a console) or IS the site. All three depict.
EXEMPT_ANCESTORS = ["fig-paper","recon","pass","plate","paper","mock","artifact","browser",
  "pla-","plf-","plm-","plo-","plp-","plv-","stick","rcpt-box","psc","lug","env","qc","slip",
  "card-wire","bk-device","lh-log","lh-inst"]

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
    // (2026-09-12) the light-ground exemption that lived here is gone: under amber the page
    // IS light, so a retired heat on paper is the remnant this gate exists to find.
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
    # Under gatelib.planted: this used to read-modify-write ember.css unguarded, and
    # running beside another gate that does the same left the plant on disk — which is
    # exactly how this gate came to report #515863, its OWN canary, on 40 pages.
    with planted("site.css", '\nh1{color:#515863!important}\n'):
        red = bool(scan("index.html"))
    if not red:
        print("[calibration] FAIL — planted remnant #515863 on h1 was NOT caught.\n             Either the check is blind or the browser served a cached ember.css."); sys.exit(2)
    print("[calibration] PASS — planted retired-palette remnant caught")

if __name__ == "__main__":
    pages = sys.argv[1:]
    if not pages:
        calibrate()
        pages = [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
                 if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules','partials')
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
    print(f"\n{bad} page(s) still painting a retired palette.")
    sys.exit(1 if bad else 0)
