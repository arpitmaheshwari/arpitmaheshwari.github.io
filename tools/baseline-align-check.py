#!/usr/bin/env python3
"""
SIBLING BASELINE ALIGNMENT — the class of defect every other gate is blind to.

WHY THIS EXISTS. On 2026-09-08 Arpit selected the act numeral on the homepage
and said "these numerals don't feel align to the corresponding text". He was
right in all four acts at all three widths: the numeral's baseline sat about
6px above the title's — 6.3px at 1440 and 6.5px at 768 by the read-only metric
below, 6.0px and 7.0px by the inline-block probe it replaced. The two methods
agree within 0.5px; the sibling DIFFERENCE, which is what this reports, agrees
far closer than that. Every gate in this repo passed it,
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

MEASUREMENT — READ-ONLY, AND THAT IS THE WHOLE POINT.
Two earlier attempts failed, in opposite directions, and the second failure is
why this is now read-only:
  1. hand arithmetic that approximated the ascent as 0.75em. It reported a 4.5px
     spread on a row the browser had already aligned exactly.
  2. inserting a zero-size inline-block as the element's first child, whose
     bottom edge sits ON the line's baseline by definition. Exact — but it
     MUTATES LAYOUT. On lab/index.html at 768px, inserting it into a wrapping
     flex row of chips moved two of the three chips up a whole line (32.7px):
     the gate then compared positions from the perturbed page against rows
     grouped from the unperturbed one, and invented a 32.7px defect. An
     instrument that changes the thing it measures cannot be trusted about a
     layout, however exact its reading.
That was the FOURTH instrument fault on this gate (rotated frames, descendant
height, screen-reader text, and this), which is the point at which this repo's
own rule says stop patching and change the architecture. So: the browser's real
font metrics via canvas TextMetrics — fontBoundingBoxAscent/Descent for the
element's exact computed font — and the baseline is content-box top +
half-leading + ascent. Nothing is inserted, nothing reflows.
Validated against the probe on rows the probe does NOT disturb: agreement within
0.88px absolute, and the error is systematic PER FONT, so the sibling DIFFERENCE
— the only quantity this gate reports — agrees within 0.03px to 0.25px. Well
inside the 1.5px tolerance.

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

It also skips single-glyph children (see the icon note in the leaf filter),
which means a genuinely misaligned icon is invisible to it.

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

  // Is this element exactly ONE rendered line? Measured on the CONTENT box against
  // the element's own line-height. Both cheaper tests lie: height/lineHeight off the
  // border box counts PADDING as leading; a Range over an element's own direct text
  // nodes cannot see height contributed by DESCENDANTS (that hole called the fintech
  // signal row — a heading plus a three-line quote — a 29.2px baseline defect).
  function oneLine(el){
    const cs = getComputedStyle(el);
    const lh = parseFloat(cs.lineHeight);
    if (!isFinite(lh) || lh <= 0) return false;          // line-height:normal — cannot judge
    const inner = el.clientHeight
      - parseFloat(cs.paddingTop || 0) - parseFloat(cs.paddingBottom || 0);
    return Math.abs(inner - lh) <= 1.5;
  }

  // THE MEASUREMENT. Do not compute a baseline — ask the browser the question that
  // actually matters: would baseline-aligning this row move anything relative to
  // anything else? Force align-items:baseline, watch what shifts, put it back.
  // The MISALIGNMENT is the SPREAD of those shifts: if every child moves by the same
  // amount the row merely translated, which is not a misalignment.
  function shifts(parent, kids){
    const h0 = parent.getBoundingClientRect().height;
    const before = kids.map(k => k.getBoundingClientRect().top);
    const had = parent.style.alignItems;
    parent.style.alignItems = 'baseline';
    const h1 = parent.getBoundingClientRect().height;
    const after = kids.map(k => k.getBoundingClientRect().top);
    if (had) parent.style.alignItems = had; else parent.style.removeProperty('align-items');
    const d = kids.map((k, i) => after[i] - before[i]);
    return { d, spread: Math.max(...d) - Math.min(...d), grew: +(h1 - h0).toFixed(2) };
  }

  const out = [];
  for (const parent of document.querySelectorAll('*')) {
    const pcs = getComputedStyle(parent);
    if (!/^(grid|flex|inline-grid|inline-flex)$/.test(pcs.display)) continue;
    if (pcs.flexDirection === 'column' && pcs.display.includes('flex')) continue;
    const kids = [...parent.children].filter(k => {
      if (!txt(k)) return false;
      if (k.querySelector(LEAF_BAD)) return false;
      const cs = getComputedStyle(k);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      if (cs.clip && cs.clip !== 'auto') return false;          // screen-reader-only text
      if (cs.clipPath && cs.clipPath !== 'none') return false;  // has no visual baseline
      // An ICON rendered as text is not text sharing a baseline. The boarding
      // pass's plane sits CENTRED between "IND" and "YOU" — that is how a ticket
      // is drawn, and baseline-aligning it would drop the glyph to the text
      // baseline. Same for a chevron, arrow or bullet beside a label. Tested by
      // CONTENT, not class: one or two characters containing no letter or digit.
      // (Removed once for simplicity, which immediately re-flagged the plane.)
      const t = (k.textContent || '').trim();
      if (t.length <= 2 && !/[\p{L}\p{N}]/u.test(t)) return false;
      const r = k.getBoundingClientRect();
      return r.width >= 2 && r.height >= 2;
    });
    if (kids.length < 2) continue;
    const boxes = kids.map(k => ({ k, r: k.getBoundingClientRect() }));
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
      // Only single-line rows. Where a child wraps, centre and baseline are both
      // defensible and no gate should cast that vote — the site footer is exactly
      // that case and an earlier build of this called it a 13.3px defect.
      if (row.some(({k}) => !oneLine(k))) continue;
      const els = row.map(x => x.k);
      const s = shifts(parent, els);
      if (s.spread <= TOL) continue;
      const lo = Math.min(...s.d);
      out.push({parent: parent.tagName.toLowerCase() +
                  (parent.className && typeof parent.className === 'string'
                   ? '.' + parent.className.trim().split(/\s+/).slice(0,2).join('.') : ''),
                align: pcs.alignItems, display: pcs.display,
                spread: +s.spread.toFixed(1), grew: s.grew,
                kids: els.map((k, n) => {
                  const cs = getComputedStyle(k);
                  return {s: k.tagName.toLowerCase() + (k.className && typeof k.className === 'string'
                            ? '.' + k.className.trim().split(/\s+/).slice(0,2).join('.') : ''),
                          fs: parseFloat(cs.fontSize), lh: cs.lineHeight,
                          d: +(s.d[n] - lo).toFixed(1),
                          t: (k.textContent || '').trim().slice(0, 28)};})});
    }
  }
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
            print('      %-34s %5.1fpx/lh %-6s  shifts %+5.1fpx  "%s"'
                  % (k['s'], k['fs'], k['lh'], k['d'], k['t']))
        if len(others) > 1:
            print('    also: %s' % ', '.join(others[:6]) + (' …' if len(others) > 6 else ''))
        print()
    return 1


if __name__ == '__main__':
    sys.exit(main())
