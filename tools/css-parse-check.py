#!/usr/bin/env python3
"""css-parse-check.py — every rule written in the stylesheet is a rule the browser KEPT.

WHY (2026-09-12). A block of twenty rules was inserted one character too early — inside
the declaration list of the rule above it. Braces still balanced, every @layer still
wrapped its recorded share of the file, css-structure-check said "clean", and the
browser silently discarded all twenty as malformed declarations. The defect showed up
as a hero statistic at 2.99:1 and was found by a colour audit, not a structure check,
because no gate asked the only question that mattered: does the browser's parsed
stylesheet contain the rules the text contains?

METHOD. Load one page in headless Chrome, walk document.styleSheets recursively
(layers, media, supports) and collect every style rule's selector for site.css and
amber.css. Split the same files' text with csslib and collect every selector. A
selector in the text that never reaches the CSSOM is a swallowed rule — reported with
its line. Selectors are compared after whitespace normalisation; a selector the
browser rejects for its OWN reasons (an unknown pseudo-class in a plain list) also
shows up here, which is a finding too.

CALIBRATION. Plants an unclosed rule followed by a real one into site.css and requires
the real one to be reported missing. A check that has never gone red is not evidence.

Exit: 0 clean / 1 swallowed rule(s) / 2 calibration failed.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp, csslib
from gatelib import planted

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS = ('site.css', 'amber.css')
CSSOM = r"""
(()=>{const out={};
 function walk(rules,name){for(const r of rules){
   if(r.cssRules&&(r.constructor.name==='CSSLayerBlockRule'||r.media||r.constructor.name==='CSSSupportsRule')){walk(r.cssRules,name);continue;}
   if(r.selectorText) out[name].push(r.selectorText);}}
 for(const s of document.styleSheets){const h=(s.href||'').split('/').pop().split('?')[0];
   if(!%s.includes(h))continue; out[h]=[]; try{walk(s.cssRules,h)}catch(e){out[h]=['ERR '+e]}}
 return JSON.stringify(out);})()
"""


def norm(sel):
    s = re.sub(r'\s+', ' ', sel).strip()
    s = re.sub(r'\s*([>+~,])\s*', r'\1', s)
    s = re.sub(r'\(\s+', '(', s); s = re.sub(r'\s+\)', ')', s)     # `:is( .a` and `:is(.a` are one selector
    s = s.replace(':nth-of-type(even)', ':nth-of-type(2n)').replace(':nth-of-type(odd)', ':nth-of-type(2n+1)')
    s = s.replace(':nth-child(even)', ':nth-child(2n)').replace(':nth-child(odd)', ':nth-child(2n+1)')   # Chrome serialises the keywords as An+B
    s = s.replace('::before', ':before').replace('::after', ':after')  # Chrome serialises either form
    s = re.sub(r'\*(?=:)', '', s)                                          # and drops the universal before any pseudo
    return s.lower()


def text_selectors(path):
    """Every rule-like prelude in the text — INCLUDING one nested inside another rule's
    braces, which is exactly the swallowed case. csslib.split_rules cannot be used here:
    it walks braces the same way the browser does and so shares its blindness."""
    src = open(path, encoding='utf-8').read()
    src = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), src, flags=re.S)
    src = re.sub(r'url\([^)]*\)', 'url()', src)                      # data URIs carry braces
    found = []
    for m in re.finditer(r'(?:^|(?<=[;{}]))\s*([^{};@][^{};]*?)\s*\{', src):   # lookbehind: the previous match's { is not consumed
        sel = m.group(1).strip()
        if not sel or sel.startswith('@') or re.match(r'^(\d+%|from|to)$', sel): continue
        if re.search(r'::?-(moz|ms|webkit)-', sel): continue      # another engine's pseudo: Chrome drops it by design
        if ':' in sel and not re.search(r'[.#\[]|::?[a-z-]+\(|^[a-z*]', sel): continue   # a declaration, not a selector
        found.append(sel)
    return found


def check(url, quiet=False):
    with cdp.Browser() as br:
        br.viewport(1280, 900); br.navigate(url, settle=3.0)
        cssom = br.eval_json(CSSOM % list(SHEETS))
    bad = []
    for sheet in SHEETS:
        kept = set(norm(s) for s in cssom.get(sheet, []))
        written = text_selectors(os.path.join(ROOT, sheet))
        missing = [w for w in written if norm(w) not in kept
                   and not re.match(r'^\d+%|^from$|^to$', w.strip())]      # keyframe steps
        if not quiet:
            print(f"  {sheet}: {len(written)} rules written, {len(kept)} distinct selectors kept, {len(missing)} missing")
        for m in missing:
            bad.append((sheet, m))
            if not quiet: print(f"     MISSING  {m[:110]}")
    return bad


def main():
    cdp.ensure_server(8000)
    url = 'http://localhost:8000/'
    # calibrate: an unclosed rule swallows the one after it
    with planted('site.css', '\n.zz-parse-canary-a{color:red\n.zz-parse-canary-b{color:blue}\n}\n'):
        red = any('zz-parse-canary-b' in m for _, m in check(url, quiet=True))
    if not red:
        print('CALIBRATION FAILED: a planted swallowed rule was not reported'); return 2
    print('  calibrated: a planted swallowed rule goes red')
    bad = check(url)
    print('CANNOT SEE: a rule the browser kept but whose DECLARATIONS it dropped (an invalid value inside a valid rule),'
          ' or rules only present on other pages\' inline <style> blocks.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
