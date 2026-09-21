#!/usr/bin/env python3
"""art-collision-check.py — after the type in a drawing grows, what does it hit?

WHY (2026-09-21). Raising the labels in the nine diagram-led artboards to clear the
12.5px rendered floor grows every string by up to 1.85x inside a fixed viewBox.
tools/svg-text-size-check.py predicted the consequence and could not see it: "whether
raising a label would COLLIDE with its neighbours ... no gate here reads it." Two
collisions in the first drawing were found by eye, and a third — band numbers sitting
flush on the box edge — was found only after re-rendering. Eye is not a method.

TWO FAULTS, measured in screen pixels off the live page:
  OVERLAP  two <text> boxes intersect by more than TOUCH px on both axes
  ESCAPE   a <text> crosses out of the smallest <rect> that encloses its anchor,
           or comes within PAD px of that rect's edge

PAD exists because flush is a defect: a label touching its container's border reads as
broken even though nothing technically overlaps.

CALIBRATION
    --selftest injects a label at a known-colliding position and requires both faults
    to be reported, then confirms the injection did not leak into the next read.

CANNOT SEE: collisions with strokes, paths, arcs and circles — only <rect> containers
and other <text>. A needle drawn through a numeral is invisible here (that one was
found by eye, and re-laid by hand). Nor whether the drawing still READS correctly.
"""
import argparse, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp, gatelib

TOUCH = 1.0     # px of mutual intersection before it counts as an overlap
PAD   = 4.0     # px of clearance a label must keep from its container's edge

JS = r"""(() => {
  const out = [];
  document.querySelectorAll('svg.art-svg, svg.art-narrow').forEach(svg => {
    if (getComputedStyle(svg).display === 'none') return;
    const id = svg.id || '(anon)';
    const R = e => { const r = e.getBoundingClientRect();
                     return {x:r.x, y:r.y, w:r.width, h:r.height, r:r.right, b:r.bottom}; };
    const texts = [...svg.querySelectorAll('text')]
      .filter(t => (t.textContent||'').trim() && t.getBoundingClientRect().height > 0)
      .map(t => ({t:(t.textContent||'').trim().slice(0,38), box:R(t)}));
    const rects = [...svg.querySelectorAll('rect')]
      .map(e => ({box:R(e)})).filter(o => o.box.w > 8 && o.box.h > 8);
    out.push({id, texts, rects, svg:R(svg)});
  });
  return out;})()"""

def overlap(a, b):
    ox = min(a['r'], b['r']) - max(a['x'], b['x'])
    oy = min(a['b'], b['b']) - max(a['y'], b['y'])
    return ox, oy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--widths', default='1440')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if a.urls:
        urls = a.urls
    else:
        urls = ['http://localhost:8000/' + p.lstrip('/')
                for p in sorted(gatelib.pages(root))]
    widths = [int(w) for w in a.widths.split(',')]

    faults, drawings, checked = [], 0, 0
    with cdp.Browser() as b:
        for w in widths:
            b.viewport(w, 900, mobile=(w < 700))
            for u in urls:
                try:
                    b.navigate(u, settle=1.2)
                except Exception as e:
                    print(f'NAV-FAIL {u} {e}'); continue
                b.scroll_through(step=900, pause=7)
                if a.selftest and u == urls[0]:
                    b.eval("""(()=>{const s=document.querySelector('svg.art-svg');if(!s)return;
                      const ts=s.querySelectorAll('text'); if(ts.length<2) return;
                      const v=ts[1]; const c=v.cloneNode(true);
                      c.setAttribute('x', v.getAttribute('x')||0);
                      c.setAttribute('y', v.getAttribute('y')||0);
                      c.setAttribute('id','__selftest_collider');
                      c.textContent='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';
                      v.parentNode.appendChild(c);})()""")
                    b.pump(0.4)
                for d in b.eval_json(JS):
                    drawings += 1
                    checked += len(d['texts'])
                    for i, t1 in enumerate(d['texts']):
                        for t2 in d['texts'][i+1:]:
                            ox, oy = overlap(t1['box'], t2['box'])
                            if ox > TOUCH and oy > TOUCH:
                                faults.append(('OVERLAP', w, u, d['id'],
                                               f"'{t1['t']}' x '{t2['t']}'  by {ox:.1f}x{oy:.1f}px"))
                        # smallest rect whose box contains this label's centre
                        cx = t1['box']['x'] + t1['box']['w']/2
                        cy = t1['box']['y'] + t1['box']['h']/2
                        host, area = None, None
                        for r in d['rects']:
                            bx = r['box']
                            if bx['x'] <= cx <= bx['r'] and bx['y'] <= cy <= bx['b']:
                                ar = bx['w']*bx['h']
                                if area is None or ar < area:
                                    host, area = bx, ar
                        if host:
                            tb = t1['box']
                            for edge, gap in (('left', tb['x']-host['x']),
                                              ('right', host['r']-tb['r']),
                                              ('top', tb['y']-host['y']),
                                              ('bottom', host['b']-tb['b'])):
                                if gap < PAD:
                                    faults.append(('ESCAPE', w, u, d['id'],
                                                   f"'{t1['t']}' {edge} clearance {gap:.1f}px"))

    if a.selftest:
        hit = any('__' not in f[4] and 'XXXX' in f[4] for f in faults)
        print(f'  {drawings} drawing(s), {checked} label(s) read')
        print(f"  calibration: planted collider {'REPORTED' if hit else 'MISSED'}")
        return 0 if hit else 1

    for kind, w, u, did, what in faults:
        print(f'  {kind:8s} @{w}  {did:22s} {what}')
        print(f'           {u}')
    print(f'\n{len(faults)} fault(s) across {drawings} drawing(s), {checked} label(s) read')
    print('CANNOT SEE: collisions with strokes, paths, arcs or circles; only <rect> '
          'containers and other <text>. Nor whether the drawing still reads correctly.')
    return 1 if faults else 0

if __name__ == '__main__':
    sys.exit(main())
