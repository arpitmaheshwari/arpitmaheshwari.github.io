#!/usr/bin/env python3
"""Fail when text inside an inlined SVG artifact is invisible against its own background.

Why this exists (2026-08-15): the artifacts used to be <img> files, which no
page CSS could reach, so no gate ever looked inside one. The day they were
inlined so the brand fonts would apply, two defects shipped to production
together and every existing gate passed them:

  1. Each artifact carries its own <style> using generic class names
     (.ik .lb .hd .em). Inlined, those became PAGE-WIDE rules — so on a page
     with two artifacts, the second one's ink silently overwrote the first's.
     Result: cream text on cream paper.
  2. The colour re-skin remapped only the colours it knew. Anything else kept
     its original lightness while its text was remapped, so light boxes ended
     up holding light text and dark bars holding dark text.

Arpit found it by eye on the live site. This gate is the instrument that
should have found it first.

METHOD — the part that matters. An artifact's text is NOT judged against the
artifact's canvas: a label sitting on a green box inside a cream diagram is
correct, and comparing it to the canvas invents failures (measured: 11 false
positives on lab/eval alone). Each text is judged against the SMALLEST painted
rect that actually contains it — its real background.

THRESHOLD. Hard-fail below HARD (near-invisible: the defect that shipped
measured 1.00–1.10). Between HARD and WCAG it warns, because some annotations
are deliberately faint and a gate that cries wolf is a gate that gets ignored.

NOT COVERED: text over gradients or images inside an artifact (no single
background colour to measure), <text> without a painted rect behind it, and
whether the words are the RIGHT words — only whether a reader can see them.
"""
import subprocess, sys, json, re, html as H, pathlib, tempfile
import sys, os
# Trackers are refused for every browser this repo drives — see cdp.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG

CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HARD = 2.0          # below this, a human cannot read it — hard failure
DOCROOT = pathlib.Path(".")

PROBE = r"""<!doctype html><html><head><title>PENDING</title></head><body><script>
const f=document.createElement('iframe');f.src='/%s?cb='+Date.now();
f.style.cssText='width:1280px;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;
%s
const srgb=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)};
const lum=a=>0.2126*srgb(a[0])+0.7152*srgb(a[1])+0.0722*srgb(a[2]);
const parse=c=>(c.match(/[\d.]+/g)||[0,0,0]).map(Number).slice(0,3);
const out=[];let measured=0;
d.querySelectorAll('svg').forEach((svg,si)=>{
 if(!svg.querySelector('text'))return;
 const rects=[...svg.querySelectorAll('rect')]
   .map(r=>({b:r.getBoundingClientRect(),fill:w.getComputedStyle(r).fill}))
   .filter(o=>!/rgba\(0, 0, 0, 0\)|none/.test(o.fill)&&o.b.width>2&&o.b.height>2);
 if(!rects.length)return;
 svg.querySelectorAll('text').forEach(t=>{
  const s=(t.textContent||'').trim(); if(s.length<3)return;
  const cs=w.getComputedStyle(t);
  if(cs.display==='none'||cs.visibility==='hidden'||+cs.opacity<0.15)return;
  const tb=t.getBoundingClientRect(); if(tb.width<2||tb.height<2)return;
  // the text's REAL background: smallest painted rect that contains it
  const cov=rects.filter(o=>o.b.left<=tb.left+2&&o.b.right>=tb.right-2
                          &&o.b.top<=tb.top+2&&o.b.bottom>=tb.bottom-2)
                 .sort((a,b)=>(a.b.width*a.b.height)-(b.b.width*b.b.height));
  if(!cov.length)return;
  measured++;
  const bg=parse(cov[0].fill), fg=parse(cs.fill);
  const l1=lum(fg),l2=lum(bg);
  const cr=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
  const fs=parseFloat(cs.fontSize)||12;
  const need=(fs>=24||(fs>=18.66&&+cs.fontWeight>=700))?3:4.5;
  if(cr<need-0.05) out.push({svg:si,t:s.slice(0,30),r:+cr.toFixed(2),need,fs:Math.round(fs)});
 });});
document.title='R:'+JSON.stringify({measured,items:out});
}catch(e){document.title='R:{"err":"'+String(e.message).slice(0,60)+'"}'}},2600);};
</script></body></html>"""


def pages_with_artifacts():
    out = []
    for p in sorted(DOCROOT.rglob("*.html")):
        s = str(p)
        if any(x in s for x in ("node_modules", ".claude/", ".git/", "prototypes/",
                                "portfolio-sources", "__", "backup")):
            continue
        try:
            html = p.read_text()
        except Exception:
            continue
        if re.search(r"<svg\b[^>]*>(?:(?!</svg>).)*?<text\b", html, re.S):
            out.append(str(p))
    return out


class Inconclusive(RuntimeError):
    """Measurement failed. Never report this as a defect."""


def scan(page, port, inject=""):
    pathlib.Path("__al.html").write_text(PROBE % (page, inject))
    cmd = [CH, "--headless=new", NO_TRACKING_FLAG, "--disable-gpu", "--no-sandbox",
           "--window-size=1360,1000", "--virtual-time-budget=12000", "--dump-dom",
           f"http://localhost:{port}/__al.html"]
    # 100s was fine when this gate ran alone (~49s for 17 pages) and far too tight
    # once the other browser gates run beside it. The push failed reporting "text
    # inside an artifact is invisible" when nothing was invisible — only slow.
    # A timeout is NOT a finding; say that instead of blaming the page.
    try:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            print(f"  retrying {page} — Chrome exceeded 240s (machine under load)")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=360)
    except subprocess.TimeoutExpired:
        raise Inconclusive(
            f"Chrome timed out twice on {page}. Nothing was measured — this is "
            f"NOT a legibility finding.")
    finally:
        pathlib.Path("__al.html").unlink(missing_ok=True)
    m = re.search(r"<title>R:(.*?)</title>", r.stdout, re.S)
    if not m:
        return None
    return json.loads(H.unescape(m.group(1)))


def _own_server():
    """Start a throwaway server on an EPHEMERAL port and return it.

    This gate used to require someone to have already started `python3 -m http.server 8000`
    and exited 2 when nobody had. Two things went wrong with that on 2026-08-30:
      * the pre-push hook only treats exit 3 as "could not measure", so a MISSING SERVER was
        reported to Arpit as "text inside an artifact is invisible against its own
        background" — a defect that did not exist, on a push that should have gone through.
      * hard-coding :8000 also collided with generate-og-cards.py, which binds the same port;
        whichever ran second died on "Address already in use".
    An ephemeral port has neither problem, and the gate no longer depends on the operator.
    """
    import threading
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    import urllib.request
    port, httpd = 8000, None
    try:
        # Reuse a server the operator already has; it is faster and keeps local runs familiar.
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
    except Exception:
        try:
            httpd = _own_server()
            port = httpd.server_address[1]
        except OSError as e:
            # Could not measure. NEVER report this as a legibility finding.
            raise Inconclusive(f"could not start a local server: {e}")

    pages = pages_with_artifacts()
    if not pages:
        print("artifact-legibility: no inlined artifacts found — nothing to check")
        sys.exit(0)

    # ---- CALIBRATION: make one artifact's text match its own box, demand RED ----
    probe_page = pages[0]
    plant = ("const st=d.createElement('style');"
             "st.textContent='svg text{fill:#F5EDE6 !important}';d.head.appendChild(st);")
    planted = scan(probe_page, port, plant)
    clean_probe = scan(probe_page, port)
    if not planted or not clean_probe:
        print("[calibration] FAIL — probe returned no data; refusing to report")
        sys.exit(1)
    caught = len(planted.get("items", [])) > len(clean_probe.get("items", []))
    if not caught:
        print("[calibration] FAIL — a planted invisible-text defect was NOT caught. "
              "A check that cannot fail is not evidence.")
        sys.exit(1)
    print(f"[calibration] PASS — planted invisible text caught "
          f"({len(planted['items'])} findings vs {len(clean_probe['items'])} clean)")

    hard, warn, total = [], [], 0
    for pg in pages:
        d = scan(pg, port)
        if d is None or d.get("err"):
            print(f"  {pg:44s} NO DATA {d.get('err','') if d else ''}")
            hard.append((pg, "probe failed"))
            continue
        total += d.get("measured", 0)
        for it in d.get("items", []):
            if it["r"] < HARD:
                hard.append((pg, f"{it['t']!r} {it['r']}:1 (needs {it['need']})"))
            else:
                warn.append((pg, f"{it['t']!r} {it['r']}:1 (needs {it['need']})"))

    print(f"\nmeasured {total} artifact text runs across {len(pages)} page(s), "
          f"each against its own background box")

    if warn:
        print(f"\nWARNINGS — below WCAG but still visible ({len(warn)}):")
        for pg, msg in warn[:12]:
            print(f"  {pg}: {msg}")

    if hard:
        print(f"\nFAIL — text a reader cannot see ({len(hard)}):")
        for pg, msg in hard:
            print(f"  {pg}: {msg}")
        print("\nUsually one of two causes: an artifact's <style> leaking into the page "
              "(scope it to the artifact's id), or a colour change applied to the text "
              "but not to the box behind it.")
    else:
        print("\nResult: clean — every artifact text is visible against its own background.")
    sys.exit(1 if hard else 0)


try:
    main()
except Inconclusive as e:
    print(f"\nINCONCLUSIVE — {e}")
    print("The gate did not run. Do not read this as a clean page OR a defect.")
    sys.exit(3)
