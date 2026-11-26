#!/usr/bin/env python3
"""book-fit-check.py — the open book must sit wholly inside the window at laptop sizes.

WHY (2026-11-26). /book/ lays its spread out at 1180 x 880 and scales it down to fit. The scale was
right and the POSITION was wrong: the grid track grew to the unscaled size, so on any window shorter
than 880px the book sat low and lost the bottom of both pages (44px at 1280x720, 28px at 1366x768),
and narrower than 1180px it sat right, under the Next arrow. Every gate and every look at the book ran
at 1440x900, the one common size where it happens to fit. No gate asks "is the whole object on screen".

RULE: at each size in SIZES, on the cover, a chapter spread and a case spread, the book's painted box
lies inside the viewport, and its centre is within 2px of the viewport's centre.
CALIBRATION: the same page with the track rule switched off in the browser (never in the file) must
go red at a short size.
Exit: 0 clean / 1 finding(s) / 2 calibration failed / 3 could not measure.
CANNOT SEE: whether the page CONTENT fits its page (book-case-pagination owns that), whether the
scaled type is still readable at 1100x720 (it is 74% size there), or the phone/tablet scroll layout.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

BASE = os.environ.get('GATE_BASE', 'http://localhost:8000')
SIZES = ((1100, 720), (1280, 720), (1366, 768), (1280, 800), (1440, 900), (1920, 1080))
SPOTS = ('', '#spine-5', '#cases-1')
PLANT = "document.head.insertAdjacentHTML('beforeend','<style>.bk-stage{grid-template:none!important}</style>')"
READ = r"""(()=>{const e=document.querySelector('.bk-spread')||document.querySelector('.bk-book');if(!e)return 'null';
const r=e.getBoundingClientRect();return JSON.stringify({l:r.left,t:r.top,r:r.right,b:r.bottom,w:innerWidth,h:innerHeight})})()"""


def faults(br, w, h, spot, plant=False):
    br.viewport(w, h)
    br.navigate('%s/book/?fit=%dx%d' % (BASE, w, h), settle=1.0)
    br.eval("try{localStorage.clear();sessionStorage.clear()}catch(e){}")   # the book reopens where it was left
    br.navigate('%s/book/?fit=%dx%d%s%s' % (BASE, w, h, 'p' if plant else '', spot), settle=3.0)
    if plant:
        br.eval(PLANT)
    br.pump(1.5)
    m = json.loads(br.eval(READ))
    if not m or m['r'] - m['l'] < 100:
        return None
    out = []
    if m['t'] < -0.5 or m['b'] > m['h'] + 0.5:
        out.append('runs off the %s by %dpx' % ('bottom' if m['b'] > m['h'] else 'top', max(m['b'] - m['h'], -m['t'])))
    if m['l'] < -0.5 or m['r'] > m['w'] + 0.5:
        out.append('runs off the side by %dpx' % max(m['r'] - m['w'], -m['l']))
    dx, dy = (m['l'] + m['r'] - m['w']) / 2, (m['t'] + m['b'] - m['h']) / 2
    if abs(dx) > 2 or abs(dy) > 2:
        out.append('off-centre by %+d across, %+d down' % (dx, dy))
    return out


def main():
    found, n = [], 0
    with cdp.Browser() as br:
        cal = faults(br, 1280, 720, '#spine-5', plant=True)
        if cal is None:
            print('COULD NOT MEASURE: no book on %s/book/' % BASE); return 3
        if not cal:
            print('CALIBRATION FAILED: the planted off-centre book at 1280x720 read clean'); return 2
        print('[calibration] PASS: planted fault caught (%s)' % '; '.join(cal))
        for w, h in SIZES:
            for spot in SPOTS:
                f = faults(br, w, h, spot)
                if f is None:
                    print('COULD NOT MEASURE: %dx%d %s' % (w, h, spot or 'cover')); return 3
                n += 1
                found += ['%dx%d %-9s %s' % (w, h, spot or 'cover', x) for x in f]
    for x in found:
        print('  OFF-SCREEN ', x)
    print('\n%d book view(s) measured, %d finding(s).' % (n, len(found)))
    print('CANNOT SEE: page content fit, readability of the scaled type, the phone and tablet layout.')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
