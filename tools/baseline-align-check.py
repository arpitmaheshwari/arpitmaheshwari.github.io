#!/usr/bin/env python3
"""
SIBLING BASELINE ALIGNMENT — the class of defect every other gate is blind to.

WHY THIS EXISTS. On 2026-09-08 Arpit selected the act numeral on the homepage
and said "these numerals don't feel align to the corresponding text". He was
right in all four acts at all three widths: the numeral's baseline sat 6.0px
above the title's at 1440 and 7.0px at 768 and 390. Every gate in this repo passed it,
and they had to — .chap used align-items:start, so the two boxes had IDENTICAL
tops (measured: n=1141.0, t=1141.0). Contrast, overflow, spacing, reflow,
line-height and heading-rank all ask a question about ONE element (its own
properties, or its position inside its own container). Not one of them compares
two siblings to each other, so a row can be provably correct on every axis any
gate measures and still read as broken to a human eye.

The cause is generic, not specific to .chap: a solid-set child (line-height:1)
beside a leaded one (1.25, 1.5) gets the same box top and a lower glyph, because
half-leading pushes the leaded child's text down inside its own line box. Any
row mixing a display numeral, a mono label or an eyebrow with body copy is
exposed. receipt-align-check.py checks LEFT edges of one component on six case
pages; nothing checked baselines anywhere.

HOW IT MEASURES. Not with font arithmetic — the first attempt approximated the
ascent as 0.75em and reported a 4.5px spread on a row the browser had already
aligned exactly, which is an instrument fault, not a finding. Instead it asks
the browser: insert a zero-size inline-block as the element's first child. Such
a box sits ON the line's baseline by definition, so its bottom edge IS the
baseline y, exactly, in the browser's own metrics. The probe is removed
immediately and the page is a throwaway.

WHAT IT FLAGS. Only rows where misalignment is unlikely to be deliberate: the
children must be text-only leaves (no image, svg, input or nested block), must
actually share a visual row (>60% vertical overlap), and must be laid out by a
grid or flex parent. Rows whose children carry different font-sizes are still
checked — a 22px numeral and a 26px title SHOULD share a baseline; that is the
whole point of a baseline.

ROWS IT DELIBERATELY SKIPS. A row where any child is not exactly one rendered
line — which includes children whose `line-height` computes to `normal`, since
there is no ratio to measure against. A row where any child wraps to more than
one line:
there, centre and baseline are both defensible (centre reads against the block,
baseline puts the short item on line one) and no gate should cast that vote. The
consequence is real — a two-line row CAN be misaligned and this will not say so.
A row under any rotated or skewed ancestor is not
checked at all: its children's screen-space baselines diverge with the tilt, and
this repo tilts things on purpose (the boarding pass 1.4deg, the facts card
1.2deg). Measuring those rows in their own frame is possible and is NOT done
here — so a real misalignment inside a tilted card is invisible to this gate.
Said plainly rather than quietly, because that is where the next defect hides.

WHAT IT CANNOT SEE. Children that are themselves flex or grid containers are
skipped, because the probe would become a flex/grid item and stop reporting a
baseline at all — so a misaligned row of two flex children is invisible to this
gate. Rows that are deliberately centre-aligned and happen to share a baseline
are indistinguishable from correct ones (fine). It does not
judge whether baseline is the right choice for a row — only whether a row that
looks like it wants one has one. Multi-line children are measured on their FIRST
line only, which is the correct reference for a wrapping title but says nothing
about the lines below it.
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser, ensure_server
from gatelib import pages as _pages

TOL = 1.5          # px; below this a human cannot see it and subpixel rounding lives here
OVERLAP = 0.60     # share of the shorter child's height that must overlap to be "one row"

PROBE = r"""
(() => {
  const TOL = %f, OVERLAP = %f;
  const LEAF_BAD = 'img,svg,input,textarea,select,button,video,canvas,picture,iframe';
  const txt = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  // A zero-size inline-block sits ON the baseline: its bottom edge IS the baseline.
  function baseline(el){
    const p = document.createElement('span');
    p.setAttribute('data-bl-probe','');
    p.style.cssText = 'display:inline-block;width:0;height:0;overflow:hidden;vertical-align:baseline';
    el.insertBefore(p, el.firstChild);
    const y = p.getBoundingClientRect().bottom;
    p.remove();
    return y;
  }
  // Is this element exactly ONE rendered line? Measured on the CONTENT box
  // against the element's own line-height, because both cheaper tests lie:
  //   - height/lineHeight straight off the border box counts PADDING as
  //     leading and calls a padded one-line button three lines;
  //   - a Range over the element's own direct text nodes cannot see height
  //     contributed by DESCENDANTS. That hole let the fintech signal row
  //     through: .plF-sig's first child holds a heading AND a three-line
  //     quote, and the chips beside it are centred against the whole 120px
  //     block. The gate called that a 29.2px baseline defect. It is not a
  //     text row at all.
  function oneLine(el){
    const cs = getComputedStyle(el);
    const lh = parseFloat(cs.lineHeight);
    if (!isFinite(lh) || lh <= 0) return false;   // line-height:normal — cannot judge
    const inner = el.clientHeight
      - parseFloat(cs.paddingTop || 0) - parseFloat(cs.paddingBottom || 0);
    return Math.abs(inner - lh) <= 1.5;
  }
  function skewed(el){
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const t = getComputedStyle(n).transform;
      if (!t || t === 'none') continue;
      const m = t.match(/matrix(?:3d)?\(([^)]+)\)/);
      if (!m) continue;
      const v = m[1].split(',').map(Number);
      // matrix(a,b,c,d,e,f): b and c are the rotation/skew terms
      const b = v.length === 6 ? v[1] : v[1], cc = v.length === 6 ? v[2] : v[4];
      if (Math.abs(b) > 1e-4 || Math.abs(cc) > 1e-4) return true;
    }
    return false;
  }
  const out = [];
  for (const parent of document.querySelectorAll('*')) {
    const pcs = getComputedStyle(parent);
    if (!/^(grid|flex|inline-grid|inline-flex)$/.test(pcs.display)) continue;
    if (pcs.flexDirection === 'column' && pcs.display.includes('flex')) continue;
    // getBoundingClientRect returns the TRANSFORMED box. Under a rotation or
    // skew, two children that share a baseline in their own frame have
    // different screen-space y — by design, not by defect. The first run of
    // this gate reported 11.6px between the boarding pass's "IND" and "YOU",
    // two identical 44px spans: 474px of row width x the pass's 1.4deg tilt
    // (matrix b = 0.0244) is 11.6px exactly. It was measuring the tilt.
    // Scale and translate are fine — they preserve baseline coincidence — so
    // only a non-zero b or c component (rotation/skew) disqualifies a row.
    if (skewed(parent)) continue;
    const kids = [...parent.children].filter(k => {
      if (!txt(k)) return false;                       // must carry its own text
      if (k.querySelector(LEAF_BAD)) return false;     // text-only leaves
      const cs = getComputedStyle(k);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      // The probe must land in an INLINE formatting context. If the child is
      // itself flex or grid, a zero-size inline-block becomes a flex/grid item
      // and its bottom edge is no longer the line's baseline — the instrument
      // would invent a finding. Skip rather than mis-measure.
      if (/(flex|grid)/.test(cs.display)) return false;
      // Screen-reader-only text has no visual baseline to align. The site's
      // .visually-hidden is position:absolute;width:1px;height:1px;clip:rect(0,0,0,0)
      // — tested geometrically, not by class name, so any convention is caught.
      if (cs.clip && cs.clip !== 'auto') return false;
      if (cs.clipPath && cs.clipPath !== 'none') return false;
      const r = k.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return false;
      return true;
    });
    if (kids.length < 2) continue;
    // group into visual rows
    const boxes = kids.map(k => ({k, r: k.getBoundingClientRect()}));
    const used = new Set();
    for (let i = 0; i < boxes.length; i++) {
      if (used.has(i)) continue;
      const row = [boxes[i]]; used.add(i);
      for (let j = i + 1; j < boxes.length; j++) {
        if (used.has(j)) continue;
        const a = boxes[i].r, b = boxes[j].r;
        const ov = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ov / Math.min(a.height, b.height) >= OVERLAP) { row.push(boxes[j]); used.add(j); }
      }
      if (row.length < 2) continue;
      const meas = row.map(({k}) => {
        const cs = getComputedStyle(k);
        return {sel: (k.tagName.toLowerCase() + (k.className && typeof k.className === 'string'
                      ? '.' + k.className.trim().split(/\s+/).slice(0,2).join('.') : '')),
                y: baseline(k), fs: parseFloat(cs.fontSize), lh: cs.lineHeight,
                text: (k.textContent || '').trim().slice(0, 28)};
      });
      // ONLY single-line rows. If any child wraps, alignment is a judgement the
      // gate cannot make: centre is then defensible and baseline would strand
      // the wrapped lines. The site footer is exactly this — its note wraps to
      // two lines at 1440 and the four one-line items are centred against it,
      // which is correct; the gate's first run called that a 13.3px defect.
      // .chap is still caught at 768 and 1440, where its title is one line.
      if (row.some(({k}) => !oneLine(k))) continue;
      const ys = meas.map(m => m.y);
      const spread = Math.max(...ys) - Math.min(...ys);
      if (spread <= TOL) continue;
      out.push({parent: parent.tagName.toLowerCase() +
                  (parent.className && typeof parent.className === 'string'
                   ? '.' + parent.className.trim().split(/\s+/).slice(0,2).join('.') : ''),
                align: pcs.alignItems, display: pcs.display,
                spread: +spread.toFixed(1),
                kids: meas.map(m => ({s: m.sel, fs: m.fs, lh: m.lh,
                                      d: +(m.y - Math.min(...ys)).toFixed(1), t: m.text}))});
    }
  }
  document.querySelectorAll('[data-bl-probe]').forEach(p => p.remove());
  return out;
})()
""" % (TOL, OVERLAP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--widths', default='390,768,1440')
    ap.add_argument('--pages', default='')
    a = ap.parse_args()
    ensure_server(8000)
    widths = [int(w) for w in a.widths.split(',')]
    paths = ([p.strip() for p in a.pages.split(',') if p.strip()]
             or [str(p) for p in _pages(include_book=True, include_redirects=False)])

    findings, checked = [], 0
    for w in widths:
        b = Browser()
        b.viewport(w, 900)
        for path in paths:
            b.navigate('http://localhost:8000/' + path.lstrip('/'))
            b.pump(0.5)
            # resolve every play-once instrument so pre-state opacity never hides a row
            b.eval("document.querySelectorAll('.bcard,.vg-hero').forEach(e=>e.classList.add('live'))")
            b.pump(0.2)
            checked += 1
            try:
                rows = b.eval_json(PROBE) or []
            except Exception as e:
                print('  ! %s @ %d — probe failed: %s' % (path, w, e))
                continue
            for r in rows:
                findings.append((w, path, r))
        b.close()

    if not findings:
        print('Result: clean — %d page-widths checked, every sibling row shares a baseline '
              'within %.1fpx.' % (checked, TOL))
        return 0

    seen = {}
    for w, path, r in findings:
        seen.setdefault((r['parent'], tuple(k['s'] for k in r['kids'])), []).append((w, path, r))
    print('%d row(s) with siblings off the baseline, in %d component(s):\n'
          % (len(findings), len(seen)))
    for (parent, _), hits in sorted(seen.items(), key=lambda kv: -max(h[2]['spread'] for h in kv[1])):
        w, path, r = max(hits, key=lambda h: h[2]['spread'])
        others = sorted({h[1] for h in hits})
        print('  %s   align-items:%s  display:%s' % (parent, r['align'], r['display']))
        print('    worst %.1fpx at %dpx on %s   (%d page-width hit(s), %d page(s))'
              % (r['spread'], w, path, len(hits), len(others)))
        for k in r['kids']:
            print('      %-34s %5.1fpx/lh %-6s  baseline %+5.1fpx  "%s"'
                  % (k['s'], k['fs'], k['lh'], k['d'], k['t']))
        if len(others) > 1:
            print('    also: %s' % ', '.join(others[:6]) + (' …' if len(others) > 6 else ''))
        print()
    return 1


if __name__ == '__main__':
    sys.exit(main())
