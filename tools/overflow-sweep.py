#!/usr/bin/env python3
"""Sweep every page at a given width and report elements escaping the viewport.

Uses a same-origin iframe so the tested page gets a TRUE CSS viewport width
(headless clamps the real window to ~500px, which would silently lie below that).
"""
import subprocess, sys, json, re, html as H, pathlib, os
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W=int(sys.argv[1]) if len(sys.argv)>1 else 1440
PAGES=sys.argv[2:] or [str(p) for p in sorted(pathlib.Path('.').rglob('*.html'))
    if not any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules')
                    for x in p.parts) and not p.name.startswith('_')]
PROBE="""<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s';
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
 document.title='R:'+JSON.stringify({vw,ox:d.documentElement.scrollWidth-vw,bad:out.slice(0,6)});
}catch(e){document.title='R:{"err":"'+String(e).slice(0,90)+'"}'}},2600);};
</script></body></html>"""
fails=0
for pg in PAGES:
    open("__ov.html","w").write(PROBE % (pg, W))
    try:
        r=subprocess.run([CH,"--headless=new","--disable-gpu","--no-sandbox",
          f"--window-size={max(W+80,600)},1000","--virtual-time-budget=9000","--dump-dom",
          "http://localhost:8000/__ov.html"],capture_output=True,text=True,timeout=90)
        m=re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        d=json.loads(H.unescape(m.group(1))) if m else {"err":"no probe result"}
    except Exception as e: d={"err":str(e)[:80]}
    finally:
        if os.path.exists("__ov.html"): os.unlink("__ov.html")
    if d.get("err") or d.get("bad") or d.get("ox",0)>2:
        fails+=1; print(f"FAIL {pg} @{W}px  ox={d.get('ox')}  {d.get('err','')}")
        for b in d.get("bad",[]): print(f"       {b['c']:38} left={b['l']:>6} right={b['r']:>6} w={b['w']:>5} ml={b['ml']} {b['tf']}")
    else: print(f"ok   {pg}")
print(f"\n{fails} page(s) with content escaping the viewport at {W}px.")
sys.exit(1 if fails else 0)
