#!/usr/bin/env python3
"""The rendered-coverage instrument the teardown page owes.

Why this exists: a first dead-CSS pass (regex-based) proved unreliable and the
teardown has said so publicly since. And lesson 10 is standing: rules matching
0 elements rot until one silently retargets (the homepage nav, the #lab band).

Method — three independent tests must ALL agree before a rule is called dead:
  1. COVERAGE: Chrome's CSS.ruleUsageTracking across every page at 390+1440,
     with reveals forced and known interactives toggled (receipts, presets,
     dyslexia toggle) — a rule used anywhere is alive.
  2. DOM: the selector (pseudo-classes stripped) matches 0 elements in every
     page's live DOM — catches rules coverage can't see (later media queries).
  3. JS: no class token from the selector appears in any shipped .js file or
     inline <script> — catches classes only added by interaction paths the
     harness didn't drive (.visible, dialog states).
Rules inside @keyframes/@font-face/@page are never candidates. :hover/:focus
variants whose BASE selector is alive are never candidates.

Output: a report; --delete removes only the triple-confirmed set from ember.css
(styles.css is the classic theme — audited but not deleted from here).
Self-calibrating: plants a known-dead rule and requires it in the report.
"""
import sys, re, json, pathlib, subprocess
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from cdp import Browser

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHEET = ROOT / 'ember.css'

def all_pages():
    out = []
    for p in sorted(ROOT.rglob('*.html')):
        parts = p.relative_to(ROOT).parts
        if any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules','book','tests') for x in parts):
            continue
        if p.name.startswith('_'): continue
        out.append(str(p.relative_to(ROOT)))
    return out

INTERACT = """(async function(){
  document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'));
  const clickables = ['.rcpt-btn','.rcpt-close','.rxa-preset','#rxf-explain','.rxo-toggle',
    '.rxp-toggle','.ccd-q','#dyslexiaToggle','#menuToggle','.hd-preset','.rxv-row'];
  for (const sel of clickables) {
    document.querySelectorAll(sel).forEach(e=>{ try{ if(e.tagName!=='A') e.click(); }catch(_){} });
  }
  window.scrollTo(0, document.body.scrollHeight); return true;})()"""

def collect_coverage():
    used = set()   # (styleSheetHref-ish, startOffset)
    sheets = {}    # styleSheetId -> sourceURL
    pages = all_pages()
    with Browser() as c:
        for w in (390, 1440):
            c.viewport(w, 900 if w==1440 else 844)
            for pg in pages:
                c.cmd('DOM.enable'); c.cmd('CSS.enable')
                c.cmd('CSS.startRuleUsageTracking')
                c.navigate(f'http://localhost:8000/{pg}', settle=2.0)
                try: c.eval(INTERACT); c.pump(1.0)
                except Exception: pass
                r = c.cmd('CSS.stopRuleUsageTracking')
                res = r.get('result', r)
                for ru in res.get('ruleUsage', []):
                    if ru.get('used'):
                        used.add((ru['styleSheetId'], ru['startOffset']))
                # map sheet ids to urls via getStyleSheetText? use CSS.styleSheetAdded events —
                # simpler: resolve each used offset to text now, while ids are valid
                # (ids are per-load; resolve immediately)
                for ru in res.get('ruleUsage', []):
                    if not ru.get('used'): continue
                    sid = ru['styleSheetId']
                    if sid not in sheets:
                        try:
                            t = c.cmd('CSS.getStyleSheetText', styleSheetId=sid)
                            sheets[sid] = t.get('result', t).get('text','')
                        except Exception:
                            sheets[sid] = ''
                # extract used selector texts from this load
                for ru in res.get('ruleUsage', []):
                    if not ru.get('used'): continue
                    txt = sheets.get(ru['styleSheetId'],'')
                    frag = txt[int(ru['startOffset']):int(ru['endOffset'])]
                    sel = frag.split('{',1)[0].strip()
                    if sel: yield_sel.add(sel)
                sheets.clear()
    return yield_sel

yield_sel = set()

def parse_sheet_rules():
    """Top-level and media-nested rules of ember.css as (selector, span)."""
    css = SHEET.read_text()
    rules = []
    i, n = 0, len(css)
    stack = []
    while i < n:
        m = re.search(r'[^{}]+\{|\}', css[i:])
        if not m: break
        tok = m.group(0); start = i + m.start(); i = i + m.end()
        if tok == '}':
            if stack: stack.pop()
            continue
        head = tok[:-1].strip()
        if head.startswith('@'):
            if head.startswith(('@media','@supports')):
                stack.append('@'); continue
            # @keyframes/@font-face/@page: skip its whole block
            depth = 1
            while i < n and depth:
                if css[i] == '{': depth += 1
                elif css[i] == '}': depth -= 1
                i += 1
            continue
        # plain rule: find its closing brace
        end = css.find('}', i)
        rules.append({'sel': re.sub(r'\s+',' ',head), 'start': start, 'end': end+1})
        i = end + 1
    return rules

def dom_dead_everywhere(selectors):
    """Return the subset of selectors matching 0 elements on EVERY page."""
    pages = all_pages()
    alive = set()
    payload = json.dumps(sorted(selectors))
    with Browser() as c:
        c.viewport(1440, 900)
        for pg in pages:
            c.navigate(f'http://localhost:8000/{pg}', settle=1.6)
            try: c.eval(INTERACT); c.pump(0.6)
            except Exception: pass
            res = c.eval_json("""JSON.stringify((function(sels){var hit=[];
              sels.forEach(function(s){var base=s.replace(/::?[a-zA-Z-]+(\\([^)]*\\))?/g,'').trim();
                if(!base){hit.push(s);return}
                try{ if(document.querySelector(base)) hit.push(s);}catch(e){ hit.push(s); }});
              return hit;})(%s))""" % payload)
            alive.update(res)
    return set(selectors) - alive

def js_tokens():
    toks = set()
    for f in list(ROOT.glob('*.js')) + list(ROOT.rglob('lab/*.js')):
        toks.update(re.findall(r'[\w-]{3,}', f.read_text(errors='ignore')))
    for p in all_pages():
        html = (ROOT/p).read_text(errors='ignore')
        for m in re.finditer(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.S):
            toks.update(re.findall(r'[\w-]{3,}', m.group(1)))
    return toks

def main():
    delete = '--delete' in sys.argv
    # calibration: plant a dead rule
    orig = SHEET.read_text()
    canary = '\nhtml[data-theme="ember"] .zz-canary-dead-rule{color:red}\n'
    SHEET.write_text(orig + canary)
    try:
        print('collecting rendered coverage (all pages × 2 widths)…')
        used_sels = collect_coverage()
        rules = parse_sheet_rules()
        unused = [r for r in rules if r['sel'] not in used_sels]
        print(f'ember.css rules: {len(rules)} · unused in coverage: {len(unused)}')
        # base-alive pseudo variants are alive
        used_bases = {re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?','',s).strip() for s in used_sels}
        cands = [r for r in unused
                 if re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?','',r['sel']).strip() not in used_bases]
        print(f'after pseudo-base check: {len(cands)} candidates')
        dead_dom = dom_dead_everywhere({r['sel'] for r in cands})
        print(f'matching 0 elements on every page: {len(dead_dom)}')
        toks = js_tokens()
        final = []
        for r in cands:
            if r['sel'] not in dead_dom: continue
            classes = set(re.findall(r'\.([\w-]+)', r['sel']))
            if classes & toks: continue   # a JS file mentions the class → keep
            final.append(r)
        cal = [r for r in final if 'zz-canary-dead-rule' in r['sel']]
        if not cal:
            print('[calibration] FAIL — planted dead rule not found by the instrument.'); sys.exit(2)
        print(f'[calibration] PASS — planted dead rule detected. Triple-confirmed dead: {len(final)-1}')
        report = ROOT/'portfolio-sources'/'css-coverage-report.txt'
        report.parent.mkdir(exist_ok=True)
        report.write_text('\n'.join(r['sel'] for r in final if 'zz-canary' not in r['sel']))
        print(f'report: {report}')
        if delete and len(final) > 1:
            css = orig
            # delete from the ORIGINAL text, matching by exact rule text spans recomputed
            for r in sorted((x for x in final if 'zz-canary' not in x['sel']), key=lambda x:-x['start']):
                css = css[:r['start']] + css[r['end']:]
            SHEET.write_text(css)
            print(f'deleted {len(final)-1} rule(s) from ember.css')
            return
    finally:
        if not delete:
            # NEVER restore over a file someone edited while we ran (2026-08-30:
            # a mid-run edit was silently clobbered by this restore). If the
            # sheet no longer equals snapshot+canary, strip only our canary.
            cur = SHEET.read_text()
            if cur == orig + canary:
                SHEET.write_text(orig)
            elif canary in cur:
                SHEET.write_text(cur.replace(canary, ''))
                print('NOTE: sheet changed during the run — canary stripped, edits preserved.')

if __name__ == '__main__':
    main()
