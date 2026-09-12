#!/usr/bin/env python3
"""css-consolidate.py — styles.css + ember.css + amber-bridge.css -> ONE site.css,
on the design system's cascade layers.

WHY (2026-09-12, Arpit: "you are admitting that you have created a bridge rather
than fixing it"). The site was carrying three stylesheets for one job:
  styles.css        the 2026-07 base — layout, type components, 814 extracted .xi-*
  ember.css         the dark theme — 1,398 rules keyed to html[data-theme="ember"],
                    of which 2,400 lines were appended OUTSIDE the cascade layers
                    the 2026-08-19 layering put in place
  amber-bridge.css  a token map written because the unlayered tail beat every layer
The decision that makes this possible is Arpit's, 2026-09-12: amber is the ONLY
look. There is no second theme to switch, so the attribute selector that guarded
1,398 rules guards nothing, and the three files can become one.

WHAT THIS DOES — and, deliberately, what it does NOT.
  1. Unwraps the old @layer wrappers (css-layerize did the same; it is idempotent).
  2. Strips `html[data-theme="ember"]` from every selector. A selector that WAS only
     the prefix becomes `:root`, so the theme's token block keeps beating the base
     :root by source order the way it did by specificity.
  3. Lifts every remaining !important into the last layer, `overrides`, with the
     shout removed (css-layerize's mechanism, kept).
  4. Emits site.css on amber.css's layer names — the layer order IS the contract:
       components  styles.css (non-.xi) then ember.css then the bridge, in source
                   order, so specificity and position settle exactly as today
       utilities   the .xi-* extracted classes (they beat components, as their
                   !important once did)
       overrides   what used to be !important
  It changes NO declaration values. Colours, spacing and type are untouched; this
  step is judged by tools/render-census.py reporting an empty diff, and the places
  it is NOT empty are where the unlayered tail had been beating the system's own
  layers — each one a finding to read, not a regression to hide.

Re-pointing the site's tokens at the system's roles, deleting the dark-ground
rules paper cannot use, and rebuilding components one look each are the NEXT
steps, and they are hand work. Doing them in the same pass as the structural fold
would make the census diff unreadable: two kinds of expected change in one report
is how a regression hides.

USAGE  css-consolidate.py [--check] [--swap-links]
  --check        write nothing; print what would happen and every assertion
  --swap-links   also rewrite the <link> tags and the <html> attribute on every
                 page that linked ember.css (prototypes are NOT touched here)
Exit: 0 written and every assertion held / 1 an assertion failed (nothing written).
"""
import importlib.util, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import csslib as L
LEGACY = ROOT / 'prototypes' / 'legacy'   # where the folded inputs were moved after the fold

PREFIX_RE = re.compile(r'html\[data-theme=["\']?ember["\']?\]\s*')
NESTING = ('@media', '@supports', '@container')


def protect_comments(css, table=None):
    """Swap every comment for a brace-free placeholder before splitting.

    css-layerize's split_rules scans for `{` without blanking comments, so a
    comment that QUOTES a rule (`.pass .grid{...}` in prose) opens a phantom rule
    whose prelude is the comment text — and the real @media below it was then
    never recognised as a media query, so its rules kept the theme prefix. Five
    rules, found by the assertion. The comments come back verbatim at the end.
    """
    table = [] if table is None else table
    def sub(m):
        table.append(m.group(0)); return f'/*@@{len(table)-1}@@*/'
    return re.sub(r'/\*.*?\*/', sub, css, flags=re.S), table


def restore_comments(css, table):
    return re.sub(r'/\*@@(\d+)@@\*/', lambda m: table[int(m.group(1))], css)


def _bare(head):
    return re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()


def _split_top_commas(sel):
    parts, depth, buf = [], 0, ''
    for ch in sel:
        if ch in '([': depth += 1
        elif ch in ')]': depth -= 1
        if ch == ',' and depth == 0:
            parts.append(buf); buf = ''
        else:
            buf += ch
    parts.append(buf)
    return parts


def strip_prefix_selector(prelude):
    """Rewrite one rule prelude. The prelude may start with a comment; keep it."""
    m = re.match(r'^((?:\s*/\*.*?\*/\s*)*)(.*)$', prelude, flags=re.S)
    comment, sel = m.group(1), m.group(2)
    if PREFIX_RE.search(sel) is None:
        return prelude
    sel = PREFIX_RE.sub('', sel)
    # a broken generated line in the bridge: `body body.p-fit` matched nothing
    sel = re.sub(r'\bbody\s+body\.', 'body.', sel)
    parts = [p.strip() or ':root' for p in _split_top_commas(sel)]
    return comment + ',\n'.join(parts)


def strip_prefix(css):
    out = []
    for kind, head, body in L.split_rules(css):
        if kind == 'rule':
            out.append(f'{strip_prefix_selector(head)}{{{body}}}')
        elif kind == 'at' and _bare(head).startswith(NESTING):
            out.append(f'{head}{{{strip_prefix(body)}}}')
        elif kind == 'at':
            out.append(f'{head}{{{body}}}')
        else:
            out.append(head)
    return '\n'.join(out)


def count_rules(css):
    n = 0
    for kind, head, body in L.split_rules(css):
        if kind == 'rule': n += 1
        elif kind == 'at' and _bare(head).startswith(NESTING + ('@layer',)): n += count_rules(body)
    return n


def blank_comments(css):
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def brace_check(css):
    depth = 0
    for i, ch in enumerate(blank_comments(css)):
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                return f'orphan }} at char {i} (line {css.count(chr(10), 0, i) + 1})'
    return None if depth == 0 else f'unclosed: depth {depth} at end of file'


def fix_bridge_text(css):
    # One generated line in block 15 carried a comment fragment with no opener,
    # `*/`, inside a selector — the whole rule was invalid and never applied.
    css = css.replace(
        'html[data-theme="ember"] body * one hue per verdict, each stated on the page ground it actually sits on */ ',
        '')
    return css


HEADER = """/* ============================================================================
   SITE.CSS — this site's own stylesheet, on the design system's cascade layers.
   ----------------------------------------------------------------------------
   Loads AFTER amber.css and shares its layer order, which is the whole contract:

     reset → tokens → ground → type → layout → components → utilities → overrides

   A later layer beats an earlier one regardless of specificity, and within one
   layer specificity and source order decide as they always did. amber.css fills
   the early layers and the generic half of `components`; this file fills:

     components  the site's own components — page layouts, cards, instruments,
                 the reconstruction plates. Where both files style the same thing
                 in this layer, this file is later and wins ties; where the system
                 is more specific it wins, which is the point of sharing a layer
                 rather than stacking one on the other.
     utilities   the extracted single-purpose classes (.xi-*), above components
     overrides   the last word — what once had to be written !important

   There is no theme attribute. There is one look, and its dark passages are the
   two bookends the system defines ([data-ground="bookend"]), not a mode.

   GENERATED ONCE by tools/css-consolidate.py from styles.css, ember.css and
   amber-bridge.css on 2026-09-12, then hand-edited from here on. The generator
   preserved every declaration value; everything after that date is a decision.
   ============================================================================ */
@layer reset, tokens, ground, type, layout, components, utilities, overrides;
"""

LINK_RE = re.compile(r'[ \t]*<link rel="stylesheet" href="(?P<pfx>\.\./|\./|/|(?:\.\./)+)(?P<name>styles|ember|amber-bridge)\.css\?v=[^"]*">\n?')
AMBER_RE = re.compile(r'(?P<indent>[ \t]*)<link rel="stylesheet" href="(?P<pfx>\.\./|\./|/|(?:\.\./)+)amber\.css\?v=[^"]*">\n?')
HTML_RE = re.compile(r'<html lang="en" data-theme="ember">')


def swap_links(check):
    files = [p for p in ROOT.rglob('*.html')
             if not any(s in p.parts for s in ('prototypes', 'node_modules', '.claude', 'portfolio-sources', 'book'))
             and 'ember.css?v=' in p.read_text(encoding='utf-8', errors='ignore')]
    problems = []
    for p in sorted(files):
        src = p.read_text(encoding='utf-8')
        n_html = len(HTML_RE.findall(src))
        if n_html != 1:
            problems.append(f'{p}: expected one <html data-theme="ember">, found {n_html}'); continue
        amber = AMBER_RE.search(src)
        removed = LINK_RE.findall(src)
        out = LINK_RE.sub('', src)
        if amber:
            pfx, indent = amber.group('pfx'), amber.group('indent')
            m = AMBER_RE.search(out)
            insert = f'{indent}<link rel="stylesheet" href="{pfx}site.css">\n'
            out = out[:m.end()] + insert + out[m.end():]
        else:
            # no amber.css link yet: put both where styles.css was
            m = LINK_RE.search(src)
            pfx = m.group('pfx') if m else '/'
            first = src[:m.start()] if m else None
            if first is None:
                problems.append(f'{p}: no stylesheet link to anchor on'); continue
            anchor = LINK_RE.search(src).start()
            out = LINK_RE.sub('', src)
            # recompute anchor in `out`: everything before the first removed link is unchanged
            out = out[:anchor] + f'<link rel="stylesheet" href="{pfx}amber.css">\n<link rel="stylesheet" href="{pfx}site.css">\n' + out[anchor:]
        out = HTML_RE.sub('<html lang="en">', out)
        # assertions on the result
        if out.count('site.css') != 1 or out.count('amber.css?') + out.count('amber.css"') != 1 \
           or 'data-theme="ember"' in out or LINK_RE.search(out):
            problems.append(f'{p}: post-swap assertion failed '
                            f'(site={out.count("site.css")}, amber={out.count("amber.css")}, '
                            f'theme={"data-theme=" in out}, old={bool(LINK_RE.search(out))})'); continue
        if out.index('amber.css') > out.index('site.css'):
            problems.append(f'{p}: amber.css must load before site.css'); continue
        if not check:
            p.write_text(out, encoding='utf-8')
    print(f"  pages re-linked: {len(files) - len(problems)} of {len(files)}"
          f"{' (dry run)' if check else ''}")
    for pr in problems: print('  PROBLEM', pr)
    return not problems


def main():
    check = '--check' in sys.argv
    raw_s = (LEGACY / 'styles.css').read_text(encoding='utf-8')
    raw_e = (LEGACY / 'ember.css').read_text(encoding='utf-8')
    raw_b = fix_bridge_text((LEGACY / 'amber-bridge.css').read_text(encoding='utf-8'))
    # the layering tool's own header notes are about a file that will not exist
    raw_e = re.sub(r'/\*\s*Wrapped into the cascade layers.*?\*/\s*', '', raw_e, flags=re.S)
    raw_s = re.sub(r'/\* CASCADE LAYERS — the priority order.*?\*/\s*', '', raw_s, flags=re.S)
    table = []
    ps, _ = protect_comments(raw_s, table)
    pe, _ = protect_comments(raw_e, table)
    pb, _ = protect_comments(raw_b, table)
    styles = L.unwrap_layers(ps)
    ember = L.unwrap_layers(pe)
    bridge = pb
    n_before = count_rules(styles) + count_rules(ember) + count_rules(bridge)

    base_s, xi = L.partition(styles)
    base_s, emph_s = L.split_emphasis(base_s)
    ember_n, emph_e = L.split_emphasis(strip_prefix(ember))
    bridge_n, emph_b = L.split_emphasis(strip_prefix(bridge))

    site = (HEADER
            + '\n@layer components {\n'
            + '/* ── from styles.css ── */\n' + base_s
            + '\n\n/* ── from ember.css ── */\n' + ember_n
            + '\n\n/* ── from amber-bridge.css ── */\n' + bridge_n
            + '\n}\n\n@layer utilities {\n' + L.strip_important(xi) + '\n}\n'
            + '\n@layer overrides {\n' + '\n'.join(x for x in (emph_s, emph_e, emph_b) if x.strip()) + '\n}\n')
    site = restore_comments(site, table)

    ok = True
    def assert_(cond, msg):
        nonlocal ok
        print(('  ok   ' if cond else '  FAIL ') + msg)
        ok = ok and cond

    n_after = count_rules(site)
    assert_(n_after >= n_before, f'rules: {n_before} in -> {n_after} out (splitting a rule for !important may add, never lose)')
    err = brace_check(site)
    assert_(err is None, f'braces balanced{"" if err is None else ": " + err}')
    code = blank_comments(site)
    assert_('data-theme' not in code, f'no theme attribute left in code ({code.count("data-theme")} found)')
    assert_(code.count('!important') == 0, f'no !important left in code ({code.count("!important")} found)')
    assert_(code.count('body body.') == 0, 'no `body body.` selectors')
    assert_('*/ ' not in code, 'no orphan comment closers in code')
    # every var() resolves against amber.css + site.css (or carries a fallback)
    amber = (ROOT / 'amber.css').read_text(encoding='utf-8')
    declared = set(re.findall(r'(--[A-Za-z0-9_-]+)\s*:', amber + site))
    used = re.findall(r'var\((--[A-Za-z0-9_-]+)\s*([,)])', code)
    inline = set()
    for hp in ROOT.rglob('*.html'):
        if any(x in hp.parts for x in ('node_modules', '.claude', 'prototypes')): continue
        inline |= set(re.findall(r'style="[^"]*?(--[A-Za-z0-9_-]+)\s*:', hp.read_text(encoding='utf-8', errors='ignore')))
    unresolved = sorted({n for n, sep in used if n not in declared and n not in inline and sep == ')'})
    before_code = blank_comments(raw_s + raw_e + raw_b)
    pre = sorted({n for n, sep in re.findall(r'var\((--[A-Za-z0-9_-]+)\s*([,)])', before_code)
                  if n not in declared and n not in inline and sep == ')'})
    new_dead = [n for n in unresolved if n not in pre]
    assert_(not new_dead, f'no var() made unresolvable by this fold ({len(new_dead)} new: {", ".join(new_dead[:8])})')
    if pre:
        print(f'  WARN {len(pre)} var() were ALREADY unresolvable in the inputs — pre-existing, fix in the value pass: {", ".join(pre)}')
    layers = re.findall(r'^@layer (\w+) \{', site, flags=re.M)
    assert_(layers == ['components', 'utilities', 'overrides'], f'top-level layers {layers}')
    print(f'  site.css: {site.count(chr(10)):,} lines, {len(site)/1024:.1f} KB')

    scratch = pathlib.Path('/private/tmp/claude-501/-Users-arpit-Code-git/91c61cad-dfbf-4e82-be35-f03d6fd108c1/scratchpad/site.check.css')
    scratch.write_text(site, encoding='utf-8')
    if not ok:
        print(f'NOT WRITTEN (inspectable copy at {scratch})'); return 1
    if check:
        print(f'--check: nothing written to the repo (inspectable copy at {scratch})')
    else:
        (ROOT / 'site.css').write_text(site, encoding='utf-8')
        print('  written site.css')
    if '--swap-links' in sys.argv:
        if not swap_links(check): return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
