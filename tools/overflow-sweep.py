#!/usr/bin/env python3
"""Sweep every page at a given width and report elements escaping the viewport.

Uses a same-origin iframe so the tested page gets a TRUE CSS viewport width
(headless clamps the real window to ~500px, which would silently lie below that).
"""
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
W=int(sys.argv[1]) if len(sys.argv)>1 else 1440
# One definition of "a shipped page", in gatelib. This used to be a private rglob
# with its own exclusion tuple — one of three such copies, which is how partials/
# was excluded in two of them and not the third.
from gatelib import pages as _pages
PAGES = sys.argv[2:] or _pages()
PROBE="""<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:%dpx;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;
 const vw=d.documentElement.clientWidth,bad=[];
 d.querySelectorAll('body *').forEach(el=>{const cs=w.getComputedStyle(el);
  if(cs.position==='fixed'||cs.display==='none'||cs.visibility==='hidden')return;
  const r=el.getBoundingClientRect(); if(r.width<8||r.height<4)return;
  // Content inside a deliberately scrollable box (code blocks, wide tables) is
  // ALLOWED to be wider than the viewport — that is the correct pattern, not a
  // defect. Only flag it if it also escapes that box's own visible bounds.
  let sc=el.parentElement, clipped=false;
  while(sc&&sc!==d.body){const o=w.getComputedStyle(sc);
   // ONLY auto/scroll earns the exemption. `hidden` means the content is clipped
   // away and unreachable — that is a defect, not a scrolling affordance.
   if(/(auto|scroll)/.test(o.overflowX)){const sr=sc.getBoundingClientRect();
    if(sr.left>=-2&&sr.right<=vw+2){clipped=true;} break;} sc=sc.parentElement;}
  if(clipped)return;
  if(r.left<-2||r.right>vw+2){
   bad.push({c:(el.tagName+'.'+((el.className+'').trim().split(/\\s+/)[0]||'')).slice(0,40),
    l:Math.round(r.left),r:Math.round(r.right),w:Math.round(r.width),
    ml:cs.marginLeft,tf:cs.transform==='none'?'':'T'});}});
 // keep only outermost offenders
 const out=bad.filter((b,i)=>!bad.some((o,j)=>j<i&&o.l<=b.l&&o.r>=b.r));
 // COLLISION WITH THE SECTION BOUNDARY. A decoration that doubles as spacing
 // (the old diagonal seam did) leaves text 1px off the edge the day it is
 // removed — which is exactly what happened, on three sections, unnoticed.
 // Space must be declared, so a section whose first ink hugs its own top fails.
 const tight=[];
 d.querySelectorAll('main > section').forEach(sec=>{
  const sr=sec.getBoundingClientRect(); if(sr.height<80)return;
  const f=sec.querySelector('p,h1,h2,h3,li'); if(!f)return;
  const fr=f.getBoundingClientRect(); const gap=Math.round(fr.top-sr.top);
  if(gap<32&&fr.height>0) tight.push({sec:(sec.id||(sec.className+'').split(' ')[0]||'section'),gap});});
 // scrollWidth INCLUDES the classic scrollbar gutter, so on any page tall enough to scroll
 // it reads viewport+scrollbar and reports phantom overflow. patterns/ml-explainability.html
 // was "5px over" for weeks on exactly that: measured in a real browser, innerWidth 395 vs
 // clientWidth 375 — a 20px scrollbar — while scrollLeft could not move past 0. Ask whether the
 // document can ACTUALLY scroll right instead; that is the thing a reader would experience.
 var de=d.documentElement, was=de.scrollLeft;
 de.scrollLeft=99999; var canScroll=de.scrollLeft; de.scrollLeft=was;
 // ox is what a READER would experience: how far the page can actually be scrolled right.
 // scrollWidth arithmetic is not used at all — inside this probe's iframe it still picks up a
 // scrollbar gutter and reported a phantom 5px. The per-element `bad` list below is the other
 // half: an element whose box escapes the viewport fails even when the page cannot scroll
 // (because something clipped it), so a genuine escape cannot hide behind a zero here.
 var ox=Math.max(0, canScroll);
 // TWO WAYS A WORD IS UNREADABLE WITHOUT THE PAGE EVER OVERFLOWING (2026-09-12).
 // Both were found by walking the site at 390 by hand, and neither could be seen from
 // here before: every rule above asks whether a BOX escapes the VIEWPORT.
 //  squeeze — a leaf's own text is wider than its own content box. Cause on the day:
 //    a wireframe's two mock buttons were flex:1 basis:0 inside a 70px column, so
 //    "Search Web" held 45px of text in 30px and the neighbour painted over the rest.
 //  wordbreak — prose that computes word-break:break-all/break-word. That property
 //    breaks to MINIMISE width rather than only when a token cannot fit, so a table
 //    cell collapses and "Act|ion", "Revi|ew", "Confid|ence" split with room to spare:
 //    24 of them across six pages at 390 on the day, from one rule on every td/th.
 //    The rendered test was tried first and does not work — once the property is on,
 //    the COLUMN collapses too, so the word genuinely no longer fits its box and a
 //    "does it fit?" probe sees nothing wrong. The cause is the property; check that.
 //    Monospace surfaces (a JSON dump, a lint excerpt) set it deliberately and are
 //    exempt — a code identifier has no spaces and must be allowed to break anywhere.
 const sq=[],sp=[];
 const srOnly=e=>{for(let x=e;x&&x!==d.body;x=x.parentElement){const c=w.getComputedStyle(x);
  if((c.clip||'').startsWith('rect(0')||c.clipPath==='inset(50%%)')return true;}return false;};
 d.querySelectorAll('body *').forEach(el=>{
  if(el.children.length||!el.textContent.trim()||srOnly(el))return;
  if(/^(TEXTAREA|INPUT|SELECT|PRE|CODE|OPTION)$/.test(el.tagName))return;
  const cs=w.getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden')return;
  if(/(auto|scroll)/.test(cs.overflowX))return;
  const cw=el.clientWidth; if(cw<=1)return;
  if(el.scrollWidth>cw+1) sq.push({c:(el.tagName+'.'+((el.className+'').trim().split(/\s+/)[0]||'')).slice(0,34),
    t:el.textContent.trim().slice(0,22),sw:el.scrollWidth,cw});
  if(/break-(all|word)/.test(cs.wordBreak)&&!/mono/i.test(cs.fontFamily))
   sp.push({c:(el.tagName+'.'+((el.className+'').trim().split(/\s+/)[0]||'')).slice(0,34),
     t:el.textContent.trim().slice(0,22),wb:cs.wordBreak});});
 // A TABLE THAT NEEDS A SIDEWAYS GESTURE ON A PHONE. This site's answer to a wide
 // comparison table at phone width is to restack it as cards (.ba-table/.td-table),
 // never to park a column behind a scroll — a reader cannot know to look there. The
 // rule exists because removing word-break from td/th on 2026-09-12 released
 // patterns/ml-explainability's four-column table to its natural 434px inside a 342px
 // wrapper, and the whole "Best For" column went off-screen. contrast-audit caught it
 // (six cells painting no ink); every rule above passed it, because the PAGE does not
 // overflow — the wrapper scrolls. Only at phone widths: at 768 and up the scroll is
 // the right affordance and is exempt above.
 const tb=vw<=420?[...d.querySelectorAll('table')].filter(t=>{
   const p=t.parentElement; return p&&p.scrollWidth>p.clientWidth+1;
  }).map(t=>({c:('table.'+((t.className+'').trim().split(/\s+/)[0]||'')).slice(0,34),
   need:t.parentElement.scrollWidth,got:t.parentElement.clientWidth})):[];
 document.title='R:'+JSON.stringify({vw,ox:ox,bad:out.slice(0,6),tight:tight.slice(0,5),
   squeeze:sq.slice(0,5),split:sp.slice(0,5),tscroll:tb.slice(0,3)});
}catch(e){document.title='R:{"err":"'+String(e).slice(0,90)+'"}'}},2600);};
</script></body></html>"""
fails=0
for pg in PAGES:
    open("__ov.html","w").write(PROBE % (pg, W))
    try:
        r=subprocess.run([CH,"--headless=new",NO_TRACKING_FLAG,"--disable-gpu","--no-sandbox",
          f"--window-size={max(W+80,600)},1000","--virtual-time-budget=9000","--dump-dom",
          "http://localhost:8000/__ov.html"],capture_output=True,text=True,timeout=90)
        m=re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        d=json.loads(H.unescape(m.group(1))) if m else {"err":"no probe result"}
    except Exception as e: d={"err":str(e)[:80]}
    finally:
        if os.path.exists("__ov.html"): os.unlink("__ov.html")
    if d.get("err") or d.get("bad") or d.get("tight") or d.get("ox",0)>2 or d.get("squeeze") or d.get("split") or d.get("tscroll"):
        fails+=1; print(f"FAIL {pg} @{W}px  ox={d.get('ox')}  {d.get('err','')}")
        for b in d.get("bad",[]): print(f"       {b['c']:38} left={b['l']:>6} right={b['r']:>6} w={b['w']:>5} ml={b['ml']} {b['tf']}")
        for q in d.get("squeeze",[]): print(f"       SQUEEZED {q['c']:29} {q['t']!r} needs {q['sw']}px in {q['cw']}px")
        for q in d.get("split",[]):   print(f"       WORDBREAK {q['c']:28} {q['t']!r} computes word-break:{q['wb']} on prose")
        for q in d.get("tscroll",[]): print(f"       TABLE-SCROLL {q['c']:25} needs {q['need']}px in {q['got']}px — restack it, do not hide a column")
        for t in d.get("tight",[]): print(f"       section '{t['sec']}' — first text only {t['gap']}px from its own top edge")
    else: print(f"ok   {pg}")
print(f"\n{fails} page(s) with content escaping the viewport at {W}px.")
sys.exit(1 if fails else 0)
