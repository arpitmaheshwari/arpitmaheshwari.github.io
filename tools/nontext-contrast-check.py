#!/usr/bin/env python3
"""
NON-TEXT CONTRAST (WCAG 1.4.11) — can a reader SEE the control, not just read it?

WHY THIS EXISTS. On 2026-09-10 Arpit said of the site's calls to action: "the
cta are not very readable I am not sure how they are passing the accessibility
test, or work on that." He was right, and the answer is that they were passing
because nothing here was looking.

Measured at the time: the CTA *text* passed everywhere — contrast-audit graded
347 text nodes on a case page with zero failures. What failed was the BUTTON'S
OWN BOUNDARY. .lbl-badge-gold (19 instances) sat at 2.84:1 against the page and
.lbl-pill-gold at 2.86:1, where WCAG 1.4.11 requires 3:1 for the visual
boundary of a UI component. 29 of 38 asks failed it. Every one of the 48 gates
in this repo measures TEXT against its ground; not one measured a control's
edge. So a button nobody could find passed all of them.

HOW IT MEASURES, and why it does NOT use pixels. Finding this took FIVE
consecutive instrument faults, all of them mine, all from screenshot sampling:
  1. sampling a pill's ROUNDED CORNERS, where the "ground" inside the box is
     really page background — every reading came back 1.00:1;
  2. a per-column minimum across the glyph band caught ANTIALIASED EDGES —
     worst 1.47:1 against a median of 16.74:1 on the same button;
  3. mobile emulation shifts the screenshot coordinate frame — every 390px
     reading was exactly 1.00:1 while 1440 looked fine;
  4. scrollIntoView returns a STALE rect because this site scrolls smoothly,
     so the clip never landed on the element at all;
  5. sampling a button's CENTRE hits its LABEL, not its fill — a reported
     1.88:1 was ink-against-ground wearing a boundary's name.
An identical reading across every instance, or a worst case an order of
magnitude from the median, indicts the instrument. Three-strikes says stop at
three; I went to five before asking the right question.

The right question needs no pixels: a control's boundary is its own resolved
colour against its resolved ground, and the browser will tell you both. For a
gradient fill, the endpoints ARE the extremes, so the worst case is exact
rather than sampled. This is deterministic, runs in one pass, and cannot be
fooled by antialiasing, corners, emulation or scroll.

WHAT IT CANNOT SEE, and says so rather than passing: a ground it cannot
resolve. If an ancestor's background is an image, a gradient or a noise
overlay, the true ground is a painted pixel and this instrument reports
UNMEASURABLE — that case belongs to contrast-audit, which samples pixels and
is calibrated for it. It also does not judge focus indicators, hover states,
icon glyphs inside a control, or whether a control needs a boundary at all
(text-only links legitimately have none, and are skipped).
"""
import sys, os, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser, ensure_server
from gatelib import pages as _pages

NEED = 3.0

PROBE_TMPL = r"""
(() => {
  const px = s => { const m = (s||'').match(/-?[\d.]+/g); return m ? m.slice(0,4).map(Number) : null; };
  const lin = c => { c /= 255; return c <= 0.04045 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
  const lum = c => 0.2126*lin(c[0]) + 0.7152*lin(c[1]) + 0.0722*lin(c[2]);
  const ratio = (a,b) => { const A = lum(a), B = lum(b), hi = Math.max(A,B), lo = Math.min(A,B);
    return (hi + 0.05) / (lo + 0.05); };
  const opaque = s => { const c = px(s); return c && (c.length < 4 || c[3] > 0.95); };

  // the ground: nearest ancestor with an opaque, resolvable background COLOUR.
  // an image/gradient/overlay anywhere on the way makes it unresolvable, and we
  // say so instead of guessing.
  const ground = el => {
    for (let n = el.parentElement; n; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return {unresolved: cs.backgroundImage.slice(0,40)};
      if (opaque(cs.backgroundColor)) return {c: px(cs.backgroundColor).slice(0,3)};
    }
    const b = getComputedStyle(document.body).backgroundColor;
    return opaque(b) ? {c: px(b).slice(0,3)} : {unresolved: 'body background is not opaque'};
  };

  const ALL = __ALL__;
  // SCOPE. Unscoped, this check reports 190 controls, because the site's own
  // --border token measures 1.41:1 and every card, input and toggle uses it.
  // That is a whole-site design decision for Arpit to make, not a defect a gate
  // should block a push on — and gates.json already records that "a gate that
  // fails on a plane is a gate people learn to skip". So the DEFAULT scope is
  // the ACTION family: things a reader is meant to press to move forward. Cards
  // are excluded (they carry a heading and their affordance is their text), and
  // so are the simulated client product UIs inside case-study demos, which
  // replicate a real product's design and would be falsified by restyling.
  // --all lifts the scope and reports everything, for the design conversation.
  const isCard = el => !!el.querySelector('h1,h2,h3,h4') ||
                       (el.innerText || '').trim().split(/\s+/).length > 8;
  const inDemo = el => !!el.closest('[class*="recon-"], [class*="rx"], [class*="pd__"], [class*="demo"]');
  const out = [];
  for (const el of document.querySelectorAll('a, button, [role="button"], input, select, textarea')) {
    if (!ALL && (isCard(el) || inDemo(el))) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (el.closest('[aria-hidden="true"]')) continue;

    // what forms this control's boundary?
    const bw = ['Top','Right','Bottom','Left'].map(s => parseFloat(cs['border'+s+'Width']) || 0);
    const hasBorder = Math.max(...bw) >= 0.5;
    const img = cs.backgroundImage && cs.backgroundImage !== 'none' ? cs.backgroundImage : null;
    const bg  = opaque(cs.backgroundColor) ? px(cs.backgroundColor).slice(0,3) : null;

    // a SEMI-TRANSPARENT border is still a boundary: composite it over the ground
    // rather than discarding it. Discarding it made this instrument fall through to
    // the card's fill and report 1.15:1 for every card on the site — 80-odd findings
    // that were the probe, not the page.
    const over = (fg, bgc) => { const a = fg.length > 3 ? fg[3] : 1;
      return [0,1,2].map(i => Math.round(fg[i]*a + bgc[i]*(1-a))); };

    let stops = [], kind = null;
    const bc = px(cs.borderTopColor);
    if (hasBorder && bc && (bc.length < 4 || bc[3] > 0.02)) { stops = [bc]; kind = 'border'; }
    else if (img) {
      // a gradient's endpoints ARE its extremes — exact, not sampled
      const cols = img.match(/rgba?\([^)]*\)/g) || [];
      stops = cols.map(c => px(c).slice(0,3)).filter(Boolean);
      kind = 'gradient';
    } else if (bg) { stops = [bg]; kind = 'fill'; }
    if (!stops.length) continue;                 // a text-only link has no boundary: correct, skip

    const g = ground(el);
    const label = (el.innerText || el.value || el.getAttribute('aria-label') || '').replace(/\s+/g,' ').trim().slice(0,28);
    if (g.unresolved) {
      out.push({unmeasurable: g.unresolved, kind, label,
        sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '')});
      continue;
    }
    let worst = 99, at = null;
    for (const s0 of stops) {
      const s = over(s0, g.c);                      // alpha resolved against the real ground
      const v = ratio(s, g.c); if (v < worst) { worst = v; at = s; }
    }
    out.push({ratio: Math.round(worst*100)/100, kind, label, stop: at, ground: g.c,
      sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '')});
  }
  return out;
})()
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true',
                    help='lift the action-family scope and report every control '
                         '(the site-wide border-token conversation, not a gate verdict)')
    ap.add_argument('--widths', default='390,1440')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    ensure_server(8000)
    widths = [int(w) for w in a.widths.split(',')]
    paths = [str(p) for p in _pages(include_book=False, include_redirects=False)]
    PROBE = PROBE_TMPL.replace('__ALL__', 'true' if a.all else 'false')
    b = Browser()

    if a.selftest:
        b.viewport(1440, 900)
        b.navigate('http://localhost:8000/' + paths[0], settle=1.4); b.pump(0.5)
        planted = b.eval_json("""(() => {
          const host = document.querySelector('main') || document.body;
          const wrap = document.createElement('div');
          wrap.style.cssText = 'background:#120B14;padding:20px';   // an opaque, resolvable ground
          const bad = document.createElement('button');
          bad.id = 'planted-invisible';
          bad.textContent = 'planted: outline nobody can see';
          bad.style.cssText = 'background:transparent;border:1px solid #1E1620;color:#fff;padding:8px 16px';
          const good = document.createElement('button');
          good.id = 'planted-visible';
          good.textContent = 'planted: clearly bounded';
          good.style.cssText = 'background:#FF8A5C;border:none;color:#1A0D08;padding:8px 16px';
          wrap.appendChild(bad); wrap.appendChild(good); host.appendChild(wrap);
          return !!document.getElementById('planted-invisible').getBoundingClientRect().width; })()""")
        if not planted:
            print('[calibration] INCONCLUSIVE — could not plant; refusing a verdict'); b.close(); return 3
        rows = b.eval_json(PROBE) or []
        bad = next((r for r in rows if 'outline nobody' in (r.get('label') or '')), None)
        good = next((r for r in rows if 'clearly bounded' in (r.get('label') or '')), None)
        ok = (bad and bad.get('ratio', 9) < NEED) and (good and good.get('ratio', 0) >= NEED)
        print('[calibration] %s — invisible outline flagged at %s:1; the filled control '
              'correctly passes at %s:1'
              % ('PASS' if ok else 'FAIL',
                 bad.get('ratio') if bad else '?', good.get('ratio') if good else '?'))
        if not ok:
            b.close(); return 2

    fails, unmeasurable, checked = [], [], 0
    for w in widths:
        b.viewport(w, 900)
        for p in paths:
            b.navigate('http://localhost:8000/' + p, settle=1.0); b.pump(0.35)
            checked += 1
            for r in (b.eval_json(PROBE) or []):
                if 'unmeasurable' in r:
                    unmeasurable.append((w, p, r)); continue
                if r['ratio'] < NEED:
                    fails.append((w, p, r))
    b.close()

    if unmeasurable:
        seen = {}
        for w, p, r in unmeasurable:
            seen.setdefault((r['sel'], r['unmeasurable']), []).append(p)
        print('UNMEASURABLE by this instrument (%d) — NOT a verdict; the ground is painted, '
              'so these belong to contrast-audit\'s pixels:' % len(unmeasurable))
        for (sel, why), ps in sorted(seen.items())[:8]:
            print('    %-26s ground: %s   (%d instance(s), e.g. %s)' % (sel, why, len(ps), ps[0]))
        print()

    if not fails:
        print('Result: clean — %d page-widths checked, every control\'s boundary clears %.1f:1 '
              'against its ground (WCAG 1.4.11).' % (checked, NEED))
        return 0
    grouped = {}
    for w, p, r in fails:
        grouped.setdefault((r['sel'], r['kind'], r['ratio']), []).append((w, p, r))
    print('%d control(s) with a boundary under %.1f:1 — WCAG 1.4.11:\n' % (len(fails), NEED))
    for (sel, kind, ratio), hits in sorted(grouped.items(), key=lambda kv: kv[0][2]):
        w, p, r = hits[0]
        print('  %-28s %-9s %5.2f:1   %s vs ground %s' % (sel, kind, ratio, r['stop'], r['ground']))
        print('     "%s"   %d instance(s), e.g. %dpx %s\n' % (r['label'], len(hits), w, p))
    return 1


if __name__ == '__main__':
    sys.exit(main())
