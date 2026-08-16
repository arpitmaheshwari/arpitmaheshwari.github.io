#!/usr/bin/env python3
"""A component must not change its identity between viewports.

WHY THIS EXISTS (2026-08-16). Arpit: "on mobile button still of the old design system,
bad job, how can this survive despite multiple round of QA". The homepage's PRIMARY call
to action rendered a flat #FFB08E fill on every phone while the nav CTA beside it carried
the ember->violet gradient. It survived because every gate was aimed elsewhere:

  * cta-grammar-check.py renders at width 1440 ONLY, and excludes buttons/pills by design.
  * contrast-audit measures whether text is LEGIBLE, never whether it is CONSISTENT — a
    flat peach button passes contrast beautifully.
  * theme-remnant-check looks for the retired palette; #FFB08E was not in it.
  * Every screenshot I took of the hero was at desktop width.

A defect that only exists below 640px cannot be found by a checker that never looks below
640px. This one renders the same CTA at both widths and fails if its painted fill or ink
differs — no opinion about what the fill should BE, only that a phone and a laptop must
agree about it.

CALIBRATION: plants a viewport-specific override and requires it to be caught.
"""
import json, subprocess, sys, re, os, html as H, pathlib

CH = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
SEL = ".pill,.nav-cta,.btn-a,.btn-a-ghost,.rcpt-btn,.lbl-pill-bg,.lbl-badge-gold"
PAGES = sys.argv[1:] or ["index.html", "case-studies/adtech.html", "case-studies/planit.html",
                         "patterns/index.html", "lab/index.html", "404.html"]

PROBE = """<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='http://localhost:8000/%s?cb='+Date.now();
f.style.cssText='width:%dpx;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;const out={};
 %s
 d.querySelectorAll('%s').forEach((e,i)=>{const c=w.getComputedStyle(e);
   const fill=c.backgroundImage==='none'?c.backgroundColor:c.backgroundImage;
   out[(e.className||'x').toString().trim().slice(0,30)+'#'+i]=fill+' | '+c.color;});
 document.title='R:'+JSON.stringify(out);
}catch(e){document.title='R:{"__err":"'+String(e).slice(0,80)+'"}'}},2200);};
</script></body></html>"""

def sample(page, width, inject=""):
    open("__cv.html", "w").write(PROBE % (page, width, inject, SEL))
    try:
        r = subprocess.run([CH, "--headless=new", "--disable-gpu", "--no-sandbox",
                            f"--window-size={max(width+80,600)},1000",
                            "--virtual-time-budget=8000", "--dump-dom",
                            "http://localhost:8000/__cv.html"],
                           capture_output=True, text=True, timeout=90)
        m = re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
        return json.loads(H.unescape(m.group(1))) if m else {"__err": "no probe result"}
    except Exception as e:
        return {"__err": str(e)[:80]}
    finally:
        if os.path.exists("__cv.html"):
            os.unlink("__cv.html")

INJECT = ("const s=d.createElement('style');"
          "s.textContent='@media(max-width:640px){.pill{background:#00FF00!important}}';"
          "d.head.appendChild(s);")

def diff(a, b):
    return sorted(k for k in a if k != "__err" and a.get(k) != b.get(k))

print("[calibration] planting a viewport-specific fill on .pill …")
cal_wide, cal_narrow = sample(PAGES[0], 1440, INJECT), sample(PAGES[0], 390, INJECT)
if not diff(cal_wide, cal_narrow):
    print("[calibration] FAIL — planted override was not detected; refusing to report.")
    sys.exit(1)
print("[calibration] PASS — a viewport-specific fill is caught\n")

fails = 0
for pg in PAGES:
    wide, narrow = sample(pg, 1440), sample(pg, 390)
    if wide.get("__err") or narrow.get("__err"):
        print(f"FAIL {pg}: {wide.get('__err') or narrow.get('__err')}"); fails += 1; continue
    d = diff(wide, narrow)
    if d:
        fails += 1
        print(f"FAIL {pg} — {len(d)} CTA(s) change identity below 640px:")
        for k in d:
            print(f"       {k}\n         1440: {wide.get(k)}\n          390: {narrow.get(k)}")
    else:
        print(f"ok   {pg}  ({len([k for k in wide if k!='__err'])} CTAs identical at both widths)")

print(f"\nNOT covered: hover/focus states, and whether the shared fill is the RIGHT one — this "
      f"only asserts a phone and a laptop agree.")
print(f"Result: {'clean — every CTA keeps its identity across viewports' if not fails else f'{fails} page(s) with a viewport-dependent CTA'}")
sys.exit(1 if fails else 0)
