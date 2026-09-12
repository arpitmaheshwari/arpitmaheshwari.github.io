#!/usr/bin/env python3
"""paper-object-check.py — a paper OBJECT paints paper, wherever on the page it sits.

WHY (2026-09-12, Arpit: "Why is it black colour, is it a mistake?"). The boarding pass in
the homepage's closing bookend is a cream ticket by design — one of the site's paper
objects (receipt, QC slip, boarding pass, luggage tag, envelope, spec tag) that were never
re-skinned by any theme. The value pass mapped its old colour names onto PAGE roles, and
on a dark bookend the page ground is dark: a cream ticket went black, and I had called it
"intentional" from a render instead of checking the source. No gate asked the question,
because every colour gate here asks about ink against ground and both were consistent.

METHOD. Load every classic page at 1440, find every element carrying an object class,
and require its painted background to be LIGHT (relative luminance ≥ 0.5) regardless of
the ground it sits on. Objects with no background of their own are skipped, not judged.

CALIBRATION. Plants `.pass{background:#140C16}` into site.css and requires the pass to be
reported dark. A check that has never gone red is not evidence.

Exit: 0 clean / 1 dark object(s) / 2 calibration failed.
CANNOT SEE: an object whose interior INK is wrong on a correct ground (contrast-audit
does), an object hidden or off-screen on load, objects added by interaction.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls, planted

OBJECTS = '.pass,.bp,.qc,.psc,.cf,.env,.spec-tag,.lug,.stick,.slip,.rcpt-box,.hire-receipt'
JS = r"""(()=>{const lum=c=>{const m=(c||'').match(/[\d.]+/g); if(!m||m.length<3||(m.length>3&&+m[3]===0))return null;
 const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}; return .2126*f(+m[0])+.7152*f(+m[1])+.0722*f(+m[2]);};
 const out=[]; for(const e of document.querySelectorAll(%s)){const r=e.getBoundingClientRect(); if(r.width<60||r.height<40)continue;
  const bg=getComputedStyle(e).backgroundColor; const L=lum(bg); if(L===null)continue;
  out.push({cls:(e.className||'').toString().split(' ')[0], bg, L:+L.toFixed(3), bookend:!!e.closest('[data-ground="bookend"]')});}
 return JSON.stringify(out);})()""" % json.dumps(OBJECTS)


def scan(br, urls):
    dark = []
    for u in urls:
        br.viewport(1440, 900); br.navigate(u, settle=2.5)
        for o in br.eval_json(JS):
            if o['L'] < 0.5:
                o['page'] = u.split('8000/')[1] or '/'; dark.append(o)
    return dark


def main():
    cdp.ensure_server(8000)
    home = ['http://localhost:8000/']
    with cdp.Browser() as br:
        with planted('site.css', '\n.pass{background:#140C16 !important}\n'):
            red = any(o['cls'] == 'pass' for o in scan(br, home))
        if not red:
            print('CALIBRATION FAILED: a planted dark boarding pass was not reported'); return 2
        print('  calibrated: a planted dark object goes red')
        dark = scan(br, page_urls(include_book=False))
    for o in dark:
        print(f"  DARK  {o['page']:36s} .{o['cls']:16s} {o['bg']:22s} L={o['L']}  {'in a bookend' if o['bookend'] else ''}")
    print(f"{len(dark)} paper object(s) painting dark. CANNOT SEE: ink inside a correct object (contrast-audit), objects hidden on load.")
    return 1 if dark else 0


if __name__ == '__main__':
    sys.exit(main())
