#!/usr/bin/env python3
"""runner-diagnose.py — why do two gates pass on macOS and fail on a Linux runner?

theme-remnant-check reports h1 colour #515863 "slate ink" on 40 pages in CI. That value
is authored in NO stylesheet in this repo. cta-grammar-check's calibration fails there
with "selector matched nothing, or probe blind". Both pass locally, and three local
hypotheses were ruled out by measurement (ember.css not applying, prefers-color-scheme,
a stylesheet load race).

So the evidence has to come from the runner. This runs the SAME page through the TWO
drivers those gates use and prints what each sees:

    A. --dump-dom --virtual-time-budget, the driver theme-remnant and cta-grammar use
    B. CDP, the driver every other gate uses

If A and B disagree, the driver is the defect and not the page. Virtual time is the prime
suspect: it advances the clock only while the page is idle, so on a slower machine the
budget can expire before an iframe's stylesheets have applied — and the DOM is then
dumped mid-render, with elements styled by whatever had loaded.

Prints a plain report; under GitHub Actions also emits it as an annotation, because job
logs need admin rights to read.

    python3 tools/runner-diagnose.py [url-path]
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp  # noqa: E402
from cdp import NO_TRACKING_FLAG  # noqa: E402

CH = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = os.environ.get("BASE", "http://localhost:8000")
PATH = sys.argv[1] if len(sys.argv) > 1 else "process/"

REPORT = """(()=>{const h=document.querySelector('h1');
 const sheets=[...document.styleSheets].map(s=>{
   let n=-1; try{ n=s.cssRules.length; }catch(e){ n='BLOCKED:'+e.name; }
   return ((s.href||'inline').split('/').pop())+'='+n;});
 return JSON.stringify({
   theme: document.documentElement.getAttribute('data-theme'),
   bodyClass: (document.body.className||'').slice(0,60),
   h1: h? h.tagName+'.'+((h.className||'').split(' ')[0]||'') : 'NO H1',
   h1color: h? getComputedStyle(h).color : null,
   h1font: h? getComputedStyle(h).fontFamily.slice(0,40) : null,
   ink: getComputedStyle(document.documentElement).getPropertyValue('--ink').trim(),
   sheets: sheets,
   ctaSel: document.querySelectorAll('#patterns .contract-links').length,
   ready: document.readyState});})()"""

# ---- A: the dump-dom + virtual-time driver those two gates use ----------------
WRAPPER = """<!doctype html><html><body><script>
const f=document.createElement('iframe');
f.src='%s/%s?cb=diag';
f.style.cssText='width:1280px;height:900px;border:0';
document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{
  const d=f.contentDocument, w=f.contentWindow;
  const r=(function(){%s}).call({document:d});
  document.title='R:'+JSON.stringify({note:'see inner'});
}catch(e){document.title='R:ERR '+e.message;}},2600);};
</script></body></html>"""


def via_dump_dom():
    """Reproduce the failing driver as closely as the wrapper allows."""
    import tempfile
    inner = REPORT.replace('document.', 'd.').replace('getComputedStyle', 'w.getComputedStyle')
    wrapper = ("""<!doctype html><html><body><script>
const f=document.createElement('iframe');f.src='%s/%s?cb=diag';
f.style.cssText='width:1280px;height:900px;border:0';document.body.appendChild(f);
f.onload=()=>{setTimeout(()=>{try{const d=f.contentDocument,w=f.contentWindow;
  document.title='R:'+(%s);}catch(e){document.title='R:ERR '+e.message;}},2600);};
</script></body></html>""") % (BASE, PATH, inner)
    fd, path = tempfile.mkstemp(suffix='.html', prefix='__diag_', dir='.')
    os.close(fd)
    open(path, 'w', encoding='utf-8').write(wrapper)
    try:
        r = subprocess.run(
            [CH, "--headless=new", NO_TRACKING_FLAG, "--disable-gpu", "--no-sandbox",
             "--disable-dev-shm-usage", "--window-size=1400,1000",
             "--virtual-time-budget=9000", "--dump-dom",
             f"{BASE}/{os.path.basename(path)}"],
            capture_output=True, text=True, timeout=120)
        m = re.search(r'<title>R:(.*?)</title>', r.stdout, re.S)
        return m.group(1) if m else f'(no title; {len(r.stdout)} bytes of DOM, stderr: {r.stderr[:160]})'
    finally:
        os.unlink(path)


def via_cdp():
    b = cdp.Browser()
    try:
        b.viewport(1280, 900, False)
        b.navigate(f"{BASE}/{PATH}", settle=2.0)
        return b.eval(REPORT)
    finally:
        try:
            b.close()
        except Exception:
            pass


def main():
    lines = [f'page: {BASE}/{PATH}']
    v = subprocess.run([CH, '--version'], capture_output=True, text=True).stdout.strip()
    lines.append(f'chrome: {v}  ({CH})')
    lines.append(f'platform: {sys.platform}')

    for name, fn in (('A dump-dom + virtual-time (the failing driver)', via_dump_dom),
                     ('B CDP (every other gate)', via_cdp)):
        lines.append('')
        lines.append(name)
        try:
            raw = fn()
            try:
                d = json.loads(raw)
                for k in ('ready', 'theme', 'bodyClass', 'h1', 'h1color', 'ink', 'ctaSel'):
                    lines.append(f'    {k:10} {d.get(k)}')
                lines.append(f'    sheets     {d.get("sheets")}')
            except (ValueError, TypeError):
                lines.append(f'    RAW {str(raw)[:400]}')
        except Exception as e:
            lines.append(f'    FAILED {type(e).__name__}: {e}')

    out = '\n'.join(lines)
    print(out)
    if os.environ.get('GITHUB_ACTIONS'):
        body = '%0A'.join(l.replace('%', '%25') for l in out.splitlines())
        print(f'::error title=runner-diagnose::{body}')


if __name__ == '__main__':
    main()
