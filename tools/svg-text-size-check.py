#!/usr/bin/env python3
"""
svg-text-size-check.py — the type nobody measured, because it is inside a drawing.

WHY THIS EXISTS
    The site enforces a 12.5px floor on rendered type: prose-check, overflow-sweep and
    line-height-check all reason about it. None of them walks into an <svg>. So the 24
    inlined art diagrams were never measured, and on 2026-09-12 they turned out to set
    their labels at 10-15 USER UNITS inside a 1180- or 1280-unit viewBox that renders at
    976-1120px — a scale of 0.65 to 0.88. Effective sizes measured 7.63px to 12.23px.
    Every one of the 24 was below the floor, at every desktop width.

    contrast-audit DOES grade this text and it passes: the ink is fine, the size is not.
    Two gates looking at the same glyph, one of them with no opinion about how big it is.

THE ARITHMETIC, and why it is not renderedWidth/viewBoxWidth
    Effective px = computed font-size x the uniform scale of the element's own
    getScreenCTM(). Dividing the SVG's rendered width by its viewBox width ignores
    preserveAspectRatio and any transform on a <g> between the <svg> and the <text>, and
    would silently mis-report a label inside a scaled group. The two agreed on all 410
    labels here, which is worth knowing but is not a reason to trust the shortcut.

WIDTH MATTERS, AND THE WORST CASE IS NOT THE WIDEST
    These drawings are display:none below 1000px, where a typeset .artalt block replaces
    them (ember.css:3047), so narrow widths are not the problem. The worst case is the
    NARROWEST width at which the drawing is still shown — 1024, where the same artwork is
    squeezed into less space and every label shrinks with it. A check that only ran at
    1440 would report the best case and call it the answer.

WHAT IT CANNOT SEE
    * Whether a label is legible for any reason other than size: a thin weight, a tight
      tracking, a busy ground behind it, or a face that renders small for its em.
    * Text in an <svg> loaded through <img> or as a CSS background — unreachable by script.
    * Text revealed only by interaction or animation.
    * Whether raising a label would COLLIDE with its neighbours. It would, in this
      artwork: a 12u -> 14u bump was simulated across 144 labels and put 31 stacked line
      pairs into em-box contact and 7 labels side-by-side into real overlap. Size is one
      axis; the hand-placed layout around it is another, and no gate here reads it.
    * Whether the reader has a legible alternative. Every one of these 24 does, in HTML,
      at prose size. That is why this is a legibility finding and not a WCAG failure:
      SC 1.4.4 is about scaling, and SVG text scales with browser zoom better than px HTML.

USAGE
    python3 tools/svg-text-size-check.py [--widths 1024,1440] [--floor 12.5]
                                         [--selftest] [--report] [URL ...]
EXIT
    0 = calibrated and clean · 1 = a label below the floor · 2 = calibration failed
    3 = could not measure (no drawing was visible at any width asked for)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gatelib import Browser, ensure_server, page_urls  # noqa: E402

FLOOR = 12.5
# 1024 is the narrowest width at which any of these drawings is shown, and therefore the
# worst case. 1440 is included because /process hides its poster below 1040px and so has
# no reading at 1024 at all — without it that drawing would be silently unmeasured.
WIDTHS = (1024, 1440)

PROBE = r"""
(plant => {
  const out = [];
  document.querySelectorAll('svg').forEach(svg => {
    if (getComputedStyle(svg).display === 'none') return;
    const r = svg.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    if (plant) {                       // calibration: one deliberately undersized label
      const t = svg.querySelector('text');
      if (t) t.style.fontSize = plant + 'px';
    }
    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.width : null;
    svg.querySelectorAll('text').forEach(t => {
      const cs = getComputedStyle(t);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const txt = (t.textContent || '').trim();
      if (!txt) return;
      const m = t.getScreenCTM();
      if (!m) return;                  // not rendered: nothing to measure, not a pass
      const scale = Math.sqrt(Math.abs(m.a * m.d - m.b * m.c));
      const fs = parseFloat(cs.fontSize);
      if (!(fs > 0) || !(scale > 0)) return;
      out.push({
        id: svg.id || null, vb,
        fs: +fs.toFixed(2), scale: +scale.toFixed(4),
        eff: +(fs * scale).toFixed(2),
        naive: vb ? +(r.width / vb).toFixed(4) : null,
        weight: cs.fontWeight,
        t: txt.slice(0, 46),
      });
    });
    if (plant) { const t = svg.querySelector('text'); if (t) t.style.fontSize = ''; }
  });
  return JSON.stringify(out);
})
"""


def measure(b, url, width, plant=None):
    b.viewport(width, 900)
    b.navigate(url, settle=2.4)
    b.scroll_through()
    return b.eval_json(f'({PROBE})({json.dumps(plant)})')


def run(urls, widths, floor, report=False):
    findings, seen, drift = [], 0, []
    with Browser() as b:
        for url in urls:
            for w in widths:
                for r in measure(b, url, w):
                    seen += 1
                    r['url'], r['w'] = url, w
                    if r['naive'] and abs(r['scale'] - r['naive']) > 0.002:
                        drift.append(r)
                    if r['eff'] < floor:
                        findings.append(r)
    return findings, seen, drift


def summarise(findings, seen, drift, floor, report):
    if not seen:
        print('  COULD NOT MEASURE: no <svg> with text was visible at any width asked for.')
        return 3
    # worst reading per drawing, because 22 labels in one drawing is one finding to act on
    worst = {}
    for f in findings:
        k = (f['url'], f['id'])
        if k not in worst or f['eff'] < worst[k]['eff']:
            worst[k] = f
    for k in sorted(worst, key=lambda k: worst[k]['eff']):
        f = worst[k]
        n = sum(1 for x in findings if (x['url'], x['id']) == k and x['w'] == f['w'])
        print(f"  {f['eff']:5.2f}px < {floor}  {f['fs']:g}u x scale {f['scale']:.3f}  "
              f"@{f['w']}px  {f['id'] or '(no id)':22} {n:2} label(s) under  "
              f"'{f['t'][:34]}'")
        print(f"        {f['url']}")
    if report:
        print('\n  every reading, worst first:')
        for f in sorted(findings, key=lambda x: x['eff'])[:400]:
            print(f"    {f['eff']:6.2f}px  {f['fs']:>5g}u  s{f['scale']:.3f} @{f['w']}  "
                  f"{f['id']:22} '{f['t'][:40]}'")
    if drift:
        print(f"\n  {len(drift)} label(s) whose own CTM scale differs from "
              f"renderedWidth/viewBox — they sit inside a transformed group, and any "
              f"check using the shortcut would mis-report them:")
        for f in drift[:6]:
            print(f"    {f['id']:22} ctm {f['scale']} vs naive {f['naive']}  '{f['t'][:28]}'")
    print(f"\n{len(worst)} drawing(s) with type below {floor}px, "
          f"{len(findings)} label(s) in total, out of {seen} measured")
    print('CANNOT SEE: legibility for any reason other than size (weight, tracking, a busy '
          'ground), text in an <svg> loaded via <img>, text revealed only by interaction, '
          'whether raising a label would collide with its neighbours, or whether the reader '
          'has a legible alternative elsewhere on the page.')
    return 1 if findings else 0


def selftest(urls, widths, floor):
    """Plant an undersized label and require the check to go red on it.

    The plant is applied to the FIRST <text> of every visible svg at a size chosen so the
    effective result is unambiguously under the floor whatever the page's own scale is.

    THE VICTIM IS CHOSEN, NOT ASSUMED. urls[0] out of page_urls() is the homepage, which
    carries no <svg> text, so the first version of this reported "CALIBRATION FAILED: the
    planted 1px label was not measured at all" when the only thing wrong was where it
    looked. Returns None — meaning "nothing to measure anywhere", exit 3 — rather than
    False, which would claim the instrument is broken.
    """
    url = None
    with Browser() as b:
        for u in urls:
            if measure(b, u, widths[-1]):
                url = u
                break
        if url is None:
            print('  no page carries measurable <svg> text at '
                  f'{widths[-1]}px — nothing to calibrate against')
            return None
        rows = measure(b, url, widths[-1], plant=1)
        planted = [r for r in rows if r['fs'] == 1]
        if not planted:
            print('  CALIBRATION FAILED: the planted 1px label was not measured at all')
            return False
        if any(r['eff'] >= floor for r in planted):
            print(f'  CALIBRATION FAILED: a 1px label measured {planted[0]["eff"]}px '
                  f'effective, which is not under the floor')
            return False
        after = measure(b, url, widths[-1])
        if any(r['fs'] == 1 for r in after):
            print('  CALIBRATION FAILED: the plant survived into the next measurement')
            return False
    print(f'  calibrated: a planted 1px label measured {planted[0]["eff"]}px and went RED '
          f'on {len(planted)} drawing(s), and did not leak into the next read')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--widths', default=','.join(str(w) for w in WIDTHS))
    ap.add_argument('--floor', type=float, default=FLOOR)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()

    ensure_server(8000)
    urls = a.urls or page_urls()
    widths = [int(x) for x in a.widths.split(',')]

    cal = selftest(urls, widths, a.floor)
    if cal is None:
        return 3
    if not cal:
        return 2
    if a.selftest:
        return 0

    findings, seen, drift = run(urls, widths, a.floor, a.report)
    return summarise(findings, seen, drift, a.floor, a.report)


if __name__ == '__main__':
    sys.exit(main())
