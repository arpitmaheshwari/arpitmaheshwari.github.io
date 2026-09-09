#!/usr/bin/env python3
"""
ESCAPED THE COLUMN — prose outside its siblings' envelope on BOTH sides.

WHY THIS EXISTS. On 2026-09-09 Arpit selected a line on the homepage: "why is
this line jumping off the grid and why couldn't you catch it". I had moved that
paragraph earlier the same session and landed it as a sibling of `.wrap` instead
of inside it, so it rendered 0..1440 where the column runs 140..1300.

Two root causes, both mine:
  * the move used `c.index('</div>', j)` — "the next closing tag" — which this
    repo's execution lessons forbid; boundaries get walked by tag depth.
  * the verification asked whether the string was PRESENT. Presence is not
    placement, and no gate here compares one element to another, so a paragraph
    sitting outside the column was invisible to all of them.

THE INVARIANT, AND HOW IT WAS ARRIVED AT. Three earlier premises failed, and
the failures are the reason this file measures what it measures:

  1. "every section has a .wrap to be inside of" — FALSE. Five column
     containers by page family (.wrap 1240 home, .section-inner 1180 patterns,
     .lab-wrap 781 lab, per-element caps on case pages, .xi-* on writing).
     The first page opened had none of them.
  2. "the modal left edge of a section IS its column" — FALSE. /fit/ has three
     legitimate left edges (394, 419, 755); no edge held 40% of the elements,
     so the section was skipped and a planted defect went unseen.
  3. "full-bleed prose is the signature; nothing legitimate spans >=90% of the
     viewport" — TRUE AT 1440 ONLY, and I measured it at 1440 only. At 390 the
     column is 358 of 390px = 92%, so the check reported 53 findings, every one
     of them at exactly 92%. An identical reading across 53 elements is an
     instrument fault, not a discovery. Absolute width cannot separate "on the
     column" from "off it" at phone widths, where the gutter is 16px.

  So this compares an element to its OWN SIBLINGS, which needs no notion of a
  column and works identically at every width. Envelope = the union of every
  other prose box in the same section.

  BOTH SIDES IS THE WHOLE POINT. Measured across 36 pages at 390 and 1440, the
  envelope test alone produces 61 hits and every legitimate one escapes on
  exactly ONE side: a section-title flush-left in a padded card (left+24,
  right+0), an indented pull-quote (left+0, right+27), an eyebrow in a rail
  (left+253, right+0). Those are alignments. Escaping on the LEFT AND THE RIGHT
  at once is not an alignment — it means the element is not in the column at
  all. Requiring both sides takes 61 hits to 0 while still catching the real
  defect by 140px a side at 1440 and 16px a side at 390.

WHAT IT CANNOT SEE. A paragraph shifted sideways but still the same width as
its siblings (off the column on one side only) is indistinguishable here from a
deliberate indent, and passes. Closing that needs the per-family column map
this gate deliberately refuses to assume. Sections with fewer than 3 prose
elements have no envelope to speak of and are skipped. Figures, tables, images
and aria-hidden subtrees are exempt: they break out by design on case pages.
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser, ensure_server
from gatelib import pages as _pages

TOL = 8          # px; below this is sub-pixel and rounding noise
MIN_SIBS = 3     # an envelope needs enough peers to mean anything

PROBE = """
(() => {
  const TOL = %d, MIN = %d;
  const prose = [...document.querySelectorAll('p, li, h1, h2, h3, h4, blockquote')]
    .filter(e => {
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      if (e.closest('[aria-hidden="true"], figure, table, svg')) return false;
      if ((e.innerText || '').trim().length < 12) return false;
      return e.getBoundingClientRect().height > 4;
    });
  const groups = new Map();
  for (const e of prose) {
    const g = e.closest('section') || document.querySelector('main') || document.body;
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(e);
  }
  const out = [];
  for (const [g, kids] of groups) {
    if (kids.length < MIN) continue;
    const box = kids.map(e => e.getBoundingClientRect());
    for (let i = 0; i < kids.length; i++) {
      let L = Infinity, R = -Infinity;
      for (let j = 0; j < kids.length; j++) if (j !== i) {
        L = Math.min(L, box[j].left); R = Math.max(R, box[j].right); }
      const oL = Math.round(L - box[i].left), oR = Math.round(box[i].right - R);
      if (oL < TOL || oR < TOL) continue;        // one side only = an alignment
      out.push({
        el: kids[i].tagName.toLowerCase() + (typeof kids[i].className === 'string'
              && kids[i].className ? '.' + kids[i].className.trim().split(/\\s+/)[0] : ''),
        sec: g.id || (typeof g.className === 'string' && g.className
              ? g.className.trim().split(/\\s+/)[0] : g.tagName.toLowerCase()),
        oL: oL, oR: oR,
        own: [Math.round(box[i].left), Math.round(box[i].right)],
        env: [Math.round(L), Math.round(R)],
        text: (kids[i].innerText || '').trim().slice(0, 44).replace(/\\s+/g, ' ')});
    }
  }
  return out;
})()
""" % (TOL, MIN_SIBS)

# the plant reproduces the real defect: a paragraph appended as a DIRECT child of
# a section, beside (not inside) that section's column container
PLANT = """
(() => {
  const need = %d;
  for (const s of document.querySelectorAll('section')) {
    const n = [...s.querySelectorAll('p, li, h1, h2, h3, h4, blockquote')]
      .filter(e => (e.innerText || '').trim().length >= 12).length;
    if (n < need) continue;
    const p = document.createElement('p');
    p.id = 'planted-escape';
    p.textContent = 'planted defect: a paragraph beside the column instead of inside it';
    s.appendChild(p);
    const r = p.getBoundingClientRect();
    if (r.width < 40 || r.height < 4) { p.remove(); continue; }
    return {sec: s.id || s.className || s.tagName, w: Math.round(r.width)};
  }
  return null;
})()
""" % MIN_SIBS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--widths', default='390,1440')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    ensure_server(8000)
    widths = [int(w) for w in a.widths.split(',')]
    paths = [str(p) for p in _pages(include_book=False, include_redirects=False)]
    b = Browser()

    if a.selftest:
        # do not assume any one page can host the plant — premise 2 died of that
        planted = None
        for w in widths:
            b.viewport(w, 900)
            for p in paths[:6]:
                b.navigate('http://localhost:8000/' + p, settle=1.2); b.pump(0.4)
                got = b.eval_json(PLANT)
                if not got:
                    continue
                hits = [f for f in (b.eval_json(PROBE) or []) if 'planted defect' in f['text']]
                planted = (w, p, got, hits)
                print('[calibration] %dpx %s  planted in section %s (%dpx wide) -> %s'
                      % (w, p, got['sec'], got['w'], 'CAUGHT' if hits else 'INVISIBLE'))
                if hits:
                    h = hits[0]
                    print('              escapes left+%d right+%d (own %s vs siblings %s)'
                          % (h['oL'], h['oR'], h['own'], h['env']))
                if not hits:
                    b.close(); return 2
                break
        if not planted:
            print('[calibration] INCONCLUSIVE — no page could host the plant; refusing to '
                  'report a verdict on a check that was never exercised')
            b.close(); return 3

    findings, checked = [], 0
    for w in widths:
        b.viewport(w, 900)
        for p in paths:
            b.navigate('http://localhost:8000/' + p, settle=1.0); b.pump(0.35)
            checked += 1
            for f in (b.eval_json(PROBE) or []):
                findings.append((w, p, f))
    b.close()

    if not findings:
        print('Result: clean — %d page-widths checked, every prose element sits inside the '
              'envelope of its own section siblings on at least one side.' % checked)
        return 0
    print('%d prose element(s) outside their siblings on BOTH sides — off the column:\n'
          % len(findings))
    for w, p, f in sorted(findings, key=lambda r: -(r[2]['oL'] + r[2]['oR'])):
        print('  %-28s in section %-18s at %dpx on %s' % (f['el'], f['sec'], w, p))
        print('    escapes left+%dpx right+%dpx  — own %s, siblings %s'
              % (f['oL'], f['oR'], f['own'], f['env']))
        print('    "%s"\n' % f['text'])
    return 1


if __name__ == '__main__':
    sys.exit(main())
