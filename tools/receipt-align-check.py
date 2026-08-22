import subprocess,json,tempfile,pathlib,sys,shutil
import sys as _sys, os as _os
# Trackers are refused for every browser this repo drives — see cdp.py.
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGES=["case-studies/adtech.html","case-studies/fintech.html","case-studies/o2.html",
       "case-studies/orgos.html","case-studies/ptc.html","case-studies/vc-diligence.html"]
PROBE="""<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:%dpx;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{const d=f.contentDocument,w=f.contentWindow,out=[];
 d.querySelectorAll('.framed,.framed-tight,.rcpt-box').forEach((box,bi)=>{
  const rows=[...box.querySelectorAll('.rcpt-r,.rcpt-r-tight,.rcpt-r-last,.rcpt-r-tight-last')];
  rows.forEach(r=>{const kid=r.firstElementChild; if(!kid)return;
   out.push({box:bi,cls:r.className.split(' ')[0],
     left:+kid.getBoundingClientRect().left.toFixed(1),
     pad:w.getComputedStyle(r).paddingLeft});});});
 document.title='RES'+JSON.stringify(out);},700);};
</script></body></html>"""
bad=0
for W in (1440,1024,390):
  for pg in PAGES:
    open('__ra.html','w').write(PROBE%(pg,W))
    o=subprocess.run([CH,"--headless=new",NO_TRACKING_FLAG,"--disable-gpu","--no-sandbox",
      f"--window-size={W+80},1000",
      "--virtual-time-budget=9000","--dump-dom","http://localhost:8000/__ra.html"],capture_output=True,text=True,timeout=60).stdout
    import re
    m=re.search(r'<title>RES(.*?)</title>',o,re.S)
    if not m: print('NO DATA',pg,W); bad+=1; continue
    rows=json.loads(m.group(1))
    if not rows: print("NO ROWS FOUND",pg,W); bad+=1; continue
    from collections import defaultdict
    g=defaultdict(list)
    for r in rows: g[r['box']].append(r)
    for bi,rs in g.items():
      lefts={r['left'] for r in rs}
      if len(lefts)>1:
        bad+=1;print(f"MISALIGNED {W}px {pg} box{bi}: "+", ".join(f"{r['cls']}@{r['left']}({r['pad']})" for r in rs))
print(("\nFAIL %d misaligned receipt boxes"%bad) if bad else "\nPASS — every receipt row shares one left edge at 1440/1024/390")
sys.exit(1 if bad else 0)
