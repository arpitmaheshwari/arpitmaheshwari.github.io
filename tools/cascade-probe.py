#!/usr/bin/env python3
"""cascade-probe.py — which declaration actually wins, here versus on the runner.

WHY. contrast-audit reports the same ten hairline failures on the Linux runner and none
locally. Every alpha hypothesis has been ruled out (gates.json records three attempts,
one reverted for blinding 30 elements), and the note there names the next step exactly:
"dump the WINNING declaration for one of these anchors on the runner
(getMatchedCSSRules order / stylesheet load order), not another alpha hypothesis."

That was never run, because it needs the runner. This is that step.

The evidence it prints, per anchor: the COMPUTED colour, every rule that sets `color`
with its selector in cascade order (last wins), the resolved value of the custom
properties involved, and the stylesheet each winning rule came from. Locally the winner
is `.xi-process-020{color:var(--accent-text)}` resolving to rgb(144,92,12) — 4.884:1,
comfortably over the floor. If the runner prints a different winner, or the same winner
resolving to a different value, that is the answer and the ten are a cascade difference.
If it prints exactly this, the cascade is exonerated and the un-blend arithmetic is the
remaining suspect.

A DIAGNOSTIC, NOT A GATE. It grades nothing and always exits 0: a diagnosis must never
be able to redden a build. Delete it, and the two probes beside it, when the question is
answered — the budget ledger records that debt.

CANNOT SEE: what the runner PAINTS. It reads the cascade, not pixels, and this repo has
been wrong before by trusting a style-based walk over a screenshot. It answers one
question — which declaration won — and nothing about whether the pixels match it.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

# The anchors contrast-audit reports on the runner and not here.
ANCHORS = [('lab/loop.html', 'the pattern library'),
           ('patterns/act-review-ignore.html', 'Get AI design patterns in your inbox')]
VARS = ('--accent-text', '--link-ink', '--accent-fill', '--link', '--acc-copper')

JS = r"""(t => {
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while (n = walk.nextNode()) {
    if (!(n.nodeValue || '').includes(t)) continue;
    const e = n.parentElement;
    if (!e || e.getBoundingClientRect().width < 2) continue;
    e.setAttribute('data-cascade-probe', '1');
    const cs = getComputedStyle(e), rs = getComputedStyle(document.documentElement);
    const vars = {};
    for (const v of %s) { const x = rs.getPropertyValue(v).trim(); if (x) vars[v] = x; }
    return {found: true, tag: e.tagName, cls: (e.className || '').toString(),
            color: cs.color, fontSize: cs.fontSize, weight: cs.fontWeight, vars};
  }
  return {found: false};
})(%s)"""

def main():
    port = int(os.environ.get('PORT', '8000'))
    base = f'http://localhost:{port}/'
    for page, text in ANCHORS:
        print(f'\n=== {page}  —  "{text}"')
        try:
            with cdp.Browser() as b:
                b.viewport(1440, 900)
                b.navigate(base + page, settle=1.8)
                b.scroll_through(step=900, pause=8)
                info = b.eval_json(JS % (json.dumps(list(VARS)), json.dumps(text)))
                if not info.get('found'):
                    print('  anchor not found on this page — the text may have changed')
                    continue
                print(f"  element   {info['tag']}.{info['cls'][:48]}")
                print(f"  computed  {info['color']}   {info['fontSize']} / {info['weight']}")
                for k, v in info['vars'].items():
                    print(f"  var       {k} = {v}")
                b.cmd('DOM.enable'); b.cmd('CSS.enable')
                root = b.cmd('DOM.getDocument')['root']['nodeId']
                nid = b.cmd('DOM.querySelector', nodeId=root,
                            selector='[data-cascade-probe="1"]')['nodeId']
                m = b.cmd('CSS.getMatchedStylesForNode', nodeId=nid)
                print('  declarations setting `color`, in cascade order (LAST WINS):')
                any_rule = False
                for entry in m.get('matchedCSSRules', []):
                    rule = entry['rule']
                    for p in rule['style'].get('cssProperties', []):
                        if p['name'] == 'color' and p.get('text'):
                            any_rule = True
                            sheet = rule.get('styleSheetId', '')
                            print(f"    {rule['selectorList']['text'][:58]:60s} {p['text'][:34]:36s} sheet={sheet}")
                inline = m.get('inlineStyle') or {}
                for p in inline.get('cssProperties', []):
                    if p['name'] == 'color':
                        any_rule = True
                        print(f"    {'(inline style attribute)':60s} {p.get('text', '')[:34]}")
                if not any_rule:
                    print('    none — the colour is inherited')
        except Exception as e:                       # a diagnosis never reddens a build
            print(f'  probe failed: {type(e).__name__}: {e}')
    print('\nCANNOT SEE: what the runner PAINTS — this reads the cascade, not pixels.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
