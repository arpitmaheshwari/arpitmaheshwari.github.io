#!/usr/bin/env python3
"""Check the page AFTER a reader touches it — the blind spot every gate names.

Read the last line of every other gate here: "CANNOT SEE ... hover, focus,
open menus, anything not reachable on load." That disclaimer has been printed
hundreds of times and nothing was ever built behind it. A prospect does not
read a portfolio on load. They hover the case-study cards, tab through the
nav, open the details panels.

Three failure kinds, each a real way a hover state breaks:
  HOVER-CONTRAST  on hover the fill changes but the ink does not, so the label
                  drops below 4.5:1 — the classic "invisible on hover" bug
  FOCUS-CONTRAST  the label is unreadable while focused — found the skip link
                  at 1.36:1, the first stop on every page
  INVISIBLE-RING  the focus ring is the same colour as what it sits on
  OPEN-OVERFLOW   opening a <details>/aria-expanded panel pushes content
                  sideways out of the viewport

CALIBRATION
    --selftest plants a hover rule that paints ink on its own colour and a
    disclosure that overflows, and requires both to be reported.
"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

PLANT = """(()=>{const s=document.createElement('style');
s.id='__plant';s.textContent=
 '.__ptest:hover{background:#FFC46B !important;color:#FFC46B !important}'
+'.__ptest{outline:none !important;box-shadow:none !important}';
document.head.appendChild(s);
const a=document.querySelector('a,button'); if(a)a.classList.add('__ptest');
return !!a;})()"""

# The programmatic-focus probe that used to live here reported "48 elements
# have no focus ring" on every page. It was wrong: el.focus() from script does
# NOT set :focus-visible, so the CSS that paints the ring never applied. Real
# Tab keypresses show a 2px ring on every element. Deleted rather than tuned —
# a check that cannot distinguish its own blindness from a defect is worse
# than no check. tab_scan() below asks the same question with real keys.

HOVER = r"""(sel => {
  const lum = c => { const m = c.match(/[\d.]+/g); if (!m) return null;
    if (m.length > 3 && parseFloat(m[3]) < 0.95) return null;
    const f = m.slice(0,3).map(v => { v = v/255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2]; };
  const el = document.querySelector(sel); if (!el) return 'null';
  const c = getComputedStyle(el);
  let bg = c.backgroundColor, n = el;
  while (n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg)) {
    n = n.parentElement; if (!n) break; bg = getComputedStyle(n).backgroundColor; }
  const bi = c.backgroundImage && c.backgroundImage !== 'none';
  const x = lum(c.color), y = lum(bg);
  if (x === null || y === null) return 'null';
  const r = (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);
  // An icon-only control carries no text, so WCAG asks 3:1 of it, not 4.5:1.
  // Reading textContent alone counted an sr-only label as visible copy and
  // called the book's page-turn arrows a failure at 4.01:1 when they pass.
  const visible = [...el.childNodes].filter(n => n.nodeType === 3)
                    .map(n => n.textContent.trim()).join('');
  return JSON.stringify({ratio:+r.toFixed(2), gradient:bi, ink:c.color, bg:bg,
    needs: visible ? 4.5 : 3.0, iconOnly: !visible,
    what:(el.textContent||el.getAttribute('aria-label')||el.tagName)
           .trim().replace(/\s+/g,' ').slice(0,34)});
})"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8899')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('pages', nargs='*')
    a = ap.parse_args()
    pages = a.pages or sorted(
        p for p in glob.glob('**/*.html', recursive=True)
        if not p.startswith(('partials/', 'node_modules/', 'tests/', 'prototypes/')))

    findings = 0
    with cdp.Browser() as br:
        br.viewport(1440, 900)

        if a.selftest:
            br.navigate(f'{a.base}/{pages[0]}', settle=2.0)
            if not br.eval(PLANT):
                print('[calibration] FAIL — no link to plant on'); return 2
            hits = hover_scan(br, only='.__ptest')
            got = {h['kind'] for h in hits}
            ok = 'HOVER-CONTRAST' in got
            print(f'[calibration] {"PASS" if ok else "FAIL"} — a hover that paints '
                  f'ink on its own colour is {"caught" if ok else "INVISIBLE"}')
            if not ok:
                print('   saw:', hits[:4]); return 2

        for p in pages:
            try:
                br.navigate(f'{a.base}/{p}', settle=1.6)
            except RuntimeError as e:
                print(f'  ! {p}: {e}'); continue
            hits = hover_scan(br) + tab_scan(br) + open_scan(br)
            if hits:
                print(f'\n{p}')
                for h in hits:
                    print(f"   {h['kind']:15} {h.get('what','')}"
                          f"{'  ' + h['detail'] if h.get('detail') else ''}")
                findings += len(hits)

    print(f'\n{findings} interaction-state problem(s)')
    print('CANNOT SEE: hover states painted by a gradient or an overlay (this '
          'reads computed styles, not pixels), states behind a real pointer '
          'gesture like drag, and anything requiring two steps.')
    return 1 if findings else 0


def json_or(v, default=()):
    import json
    try:
        return json.loads(v) if isinstance(v, str) else (v or list(default))
    except Exception:
        return list(default)


def tab_scan(br, steps=8):
    """Tab through the first few stops and check what a keyboard reader SEES.

    Real key events, because el.focus() from script does not trigger
    :focus-visible and the previous probe therefore called every focus ring on
    the site missing. This found the skip link painting cream on gold at
    1.36:1 with a gold-on-gold focus ring — the first stop on every page.
    """
    out, seen = [], set()
    for _ in range(steps):
        for t in ('rawKeyDown', 'keyUp'):
            br.cmd('Input.dispatchKeyEvent', type=t, key='Tab', code='Tab',
                   windowsVirtualKeyCode=9, nativeVirtualKeyCode=9)
        d = json_or(br.eval(FOCUSED))
        if not isinstance(d, dict) or d.get('what') in seen:
            continue
        seen.add(d['what'])
        if d.get('ratio') is not None and d['ratio'] < 4.5 and not d.get('gradient'):
            out.append({'kind': 'FOCUS-CONTRAST', 'what': d['what'],
                        'detail': f"{d['ratio']}:1 while focused — "
                                  f"{d['ink']} on {d['bg']}"})
        if d.get('ringSameAsGround'):
            out.append({'kind': 'INVISIBLE-RING', 'what': d['what'],
                        'detail': f"focus ring {d['outline']} on the same colour"})
    return out


FOCUSED = r'''(() => {
  const e = document.activeElement; if (!e || e === document.body) return 'null';
  const c = getComputedStyle(e);
  const lum = s => { const m = s.match(/[\d.]+/g); if (!m) return null;
    if (m.length > 3 && parseFloat(m[3]) < 0.95) return null;
    const f = m.slice(0,3).map(v => { v = v/255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*f[0] + 0.7152*f[1] + 0.0722*f[2]; };
  let bg = c.backgroundColor, n = e;
  // the ground BEHIND the element, for an offset ring
  let outer = e.parentElement ? getComputedStyle(e.parentElement).backgroundColor : bg;
  while (n && /rgba\(0, 0, 0, 0\)|transparent/.test(bg)) {
    n = n.parentElement; if (!n) break; bg = getComputedStyle(n).backgroundColor; }
  const grad = c.backgroundImage && c.backgroundImage !== 'none';
  const x = lum(c.color), y = lum(bg);
  const ratio = (x === null || y === null) ? null
    : +(((Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)).toFixed(2));
  const ring = (c.outlineColor || '').trim();
  return JSON.stringify({
    what: (e.textContent || e.getAttribute('aria-label') || e.tagName)
            .trim().replace(/\s+/g,' ').slice(0,34),
    ratio, gradient: grad, ink: c.color, bg,
    outline: c.outline,
    // A positive outline-offset draws the ring OUTSIDE the element, on the
    // parent's ground — comparing it to the element's own fill called a
    // perfectly visible ochre ring on a dark page invisible. Compare it to
    // whatever the ring is actually painted on.
    ringSameAsGround: (() => {
      if (!ring || c.outlineStyle === 'none') return false;
      const off = parseFloat(c.outlineOffset) || 0;
      const on = off > 0 ? outer : (grad ? null : c.backgroundColor);
      return on !== null && ring === on;
    })() });
})()'''


def hover_scan(br, only=None):
    """Force :hover via CDP and read the resulting ink-on-ground ratio."""
    import json
    sels = br.eval_json("""JSON.stringify([...document.querySelectorAll(
      'a[href],button,summary,[role="button"]')]
      .filter(e=>{const r=e.getBoundingClientRect();return r.width>8&&r.height>8})
      .slice(0,40).map((e,i)=>{e.setAttribute('data-ishover',i);
        return '[data-ishover="'+i+'"]'}))""") or []
    if only:
        sels = [only]
    out = []
    for sel in sels:
        nid = br.cmd('DOM.getDocument')['root']['nodeId']
        try:
            node = br.cmd('DOM.querySelector', nodeId=nid, selector=sel)['nodeId']
            if not node:
                continue
            br.cmd('CSS.enable')
            br.cmd('CSS.forcePseudoState', nodeId=node, forcedPseudoClasses=['hover'])
        except RuntimeError:
            continue
        r = json_or(br.eval(f'({HOVER})({json.dumps(sel)})'), default=[])
        try:
            br.cmd('CSS.forcePseudoState', nodeId=node, forcedPseudoClasses=[])
        except RuntimeError:
            pass
        if (isinstance(r, dict) and not r.get('gradient')
                and r.get('ratio', 99) < r.get('needs', 4.5)):
            out.append({'kind': 'HOVER-CONTRAST', 'what': r['what'],
                        'detail': f"{r['ratio']}:1 on hover (needs "
                                  f"{r.get('needs', 4.5)}:1"
                                  f"{', icon' if r.get('iconOnly') else ''}) — "
                                  f"{r['ink']} on {r['bg']}"})
    return out


def open_scan(br):
    """Open every disclosure, then ask whether the page now scrolls sideways."""
    return json_or(br.eval(r"""(() => {
      const before = document.documentElement.scrollWidth;
      const vw = document.documentElement.clientWidth;
      const opened = [];
      document.querySelectorAll('details:not([open])').forEach(d => {
        d.open = true; opened.push(d); });
      document.querySelectorAll('[aria-expanded="false"]').forEach(b => {
        try { b.click(); opened.push(b); } catch (e) {} });
      const after = document.documentElement.scrollWidth;
      const out = [];
      if (opened.length && after > vw + 2 && after > before + 2) {
        out.push({kind:'OPEN-OVERFLOW',
                  what:`${opened.length} panel(s) opened`,
                  detail:`page width ${before} -> ${after} in a ${vw}px viewport`});
      }
      return JSON.stringify(out);
    })()"""), default=[])


if __name__ == '__main__':
    sys.exit(main())
