#!/usr/bin/env python3
"""menu-overlay-check — the open mobile menu must paint ABOVE every page's content.

Class of defect (2026-09-06): a cream.css rule gave `body > header` z-index:50 to lift
the nav's banner wrapper; on pages whose page-hero is itself a body-child <header>,
that hero drew OVER the open menu. No load-time gate can see this: it is
post-interaction stacking, invisible until the toggle is clicked (lesson: gates
cannot see composition or interaction state).

Method: at 390px (mobile emulation), click #menuToggle on every page, then for every
nav link ask elementFromPoint at its center whether the link itself is topmost.
Self-calibrating: plants a z-raised sibling and requires red.
"""
import sys, glob, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

PROBE = """JSON.stringify((()=>{
  const t=document.getElementById('menuToggle'); if(!t) return 'no-toggle';
  t.click();
  const links=document.querySelector('.nav-links'); if(!links) return 'no-links';
  const rows=[...links.querySelectorAll('a')];
  const hidden=rows.filter(a=>{const r=a.getBoundingClientRect();
    if(!r.width) return true;
    const top=document.elementFromPoint(Math.min(r.x+r.width/2,389), Math.min(r.y+r.height/2,843));
    return !(top===a||a.contains(top)||(top&&top.contains(a)));});
  return hidden.length? 'COVERED: '+hidden.map(a=>a.textContent.trim()).join(', ') : 'ok';
})())"""

PLANT = ("var d=document.createElement('div');d.style.cssText="
         "'position:fixed;inset:0;z-index:9999;background:var(--surface-page,#fff)';"
         "document.body.appendChild(d)")

def sweep(br, pages, plant=False):
    bad = []
    for p in pages:
        br.navigate(f"http://localhost:8000/{p}", settle=1.5)
        if plant:
            br.eval(PLANT)
        r = br.eval_json(PROBE)
        if r != 'ok':
            bad.append((p, r))
        if plant:
            break  # calibration needs one page
    return bad

def main():
    pages = sorted(p for p in glob.glob('*.html') + glob.glob('*/[a-z]*.html')
                   if not p.startswith(('prototypes', 'partials', 'book', 'portfolio-sources', '__')))
    with Browser() as br:
        br.viewport(500, 900)
        br.cmd('Emulation.setDeviceMetricsOverride', width=390, height=844,
               deviceScaleFactor=2, mobile=True)
        planted = sweep(br, pages[:1], plant=True)
        if not planted:
            print('[calibration] FAIL — planted full-page overlay not flagged; instrument blind.')
            sys.exit(2)
        print(f'[calibration] PASS — planted overlay flagged')
        bad = sweep(br, pages)
        for p, r in bad:
            print(f'FAIL {p}  {r}')
        if bad:
            print(f'\n{len(bad)} page(s) hide the open menu.')
            sys.exit(1)
        print(f'ok — the open menu paints on top on all {len(pages)} pages @390.')
        print('CANNOT SEE: keyboard focus order inside the menu, scrim behavior, '
              'or covers that appear only after scrolling.')

if __name__ == '__main__':
    main()
