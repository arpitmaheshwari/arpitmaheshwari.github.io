#!/usr/bin/env python3
"""xi-dedup.py — collapse the extracted-inline classes that say the same thing.

WHY (2026-09-13, architecture review #2). `.xi-*` classes are inline `style=""` attributes that
extract-inline.py hoisted into the stylesheet, one class per element: 828 rules, of which 532
are verbatim copies of another rule's body (23 classes say `margin-bottom:16px`; 17 say
`display:none`). That is the inline-style museum with a new address, and it grows by one class
per new element.

METHOD (dry by default; --apply writes).
  1. Parse every `.xi-…{…}` rule in css/site/*.css (simple single-class selectors only).
  2. Group by normalised body. In each group the FIRST class (source order) is canonical; the
     rest are aliases.
  3. Rewrite every page: each alias in a class="" attribute becomes the canonical name (and a
     class already present is not repeated).
  4. Delete the alias rules from the stylesheet. Rules that appear inside compound selectors
     (`body.p-x .xi-…`, `:is(.xi-a,.xi-b)`) keep their class and are NOT aliased away — the
     compound is a real selector with a real target and stays.
  5. Delete `.xi-*` rules no page and no script references (48 tonight).
  6. Print a plan; with --apply, write css/site/ and the pages, then tools/build-css.py.

PROOF is external and mandatory: render-census + pixel-census before/after must differ only
within the instruments' own noise, and css-parse-check must keep every rule. This tool changes
NAMES and removes DUPLICATES; it never changes a declaration.

CANNOT SEE: an alias used only by a script that builds the class name at runtime (none found
tonight — no script mentions any xi class), and whether two identical bodies were MEANT to
diverge later (if they were, give the second one a real component class, not an xi one).
"""
import glob, json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sorted(glob.glob(os.path.join(ROOT, 'css', 'site', '0*.css')))
PAGES = [p for p in glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, '*', '*.html'))
         if not any(x in p for x in ('/prototypes/', '/partials/', '/assets/', '/node_modules/', '/portfolio-sources/'))]
SIMPLE = re.compile(r'(?<![\w\-.#:>+~\[ ])\.(xi-[a-z0-9-]+)\{([^{}]*)\}')


def norm(body):
    return ';'.join(sorted(d.strip() for d in body.split(';') if d.strip()))


def main():
    apply = '--apply' in sys.argv
    css = {f: open(f, encoding='utf-8').read() for f in SRC}
    joined = '\n'.join(css.values())
    # classes that appear in compound selectors must keep their names
    compound = set()
    for m in re.finditer(r'([^{}]*)\{', re.sub(r'/\*.*?\*/', '', joined, flags=re.S)):
        sel = m.group(1)
        for c in re.findall(r'\.(xi-[a-z0-9-]+)', sel):
            if not re.fullmatch(r'\s*\.' + re.escape(c) + r'\s*', sel): compound.add(c)
    html = {p: open(p, encoding='utf-8').read() for p in PAGES}
    allhtml = ' '.join(html.values())
    js = ' '.join(open(f, encoding='utf-8', errors='ignore').read() for f in glob.glob(os.path.join(ROOT, '*.js')) + glob.glob(os.path.join(ROOT, '*', '*.js')) if 'vendor' not in f)
    groups = collections.OrderedDict()
    rules = []
    for f, s in css.items():
        blank = re.sub(r'/\*.*?\*/', lambda mm: ' ' * len(mm.group(0)), s, flags=re.S)
        # nesting context per offset: a rule inside @media/@supports must only group with rules
        # inside the SAME at-rule prelude (first run grouped a 1024px-only rule with a global one
        # and the patterns page grew 500px — caught by render-census, 2026-09-13)
        ctx, stack = {}, []
        for mm in re.finditer(r'(@[^{}]*?)\{|\{|\}', blank):
            if mm.group(0) == '}':
                if stack: stack.pop()
            elif mm.group(1):
                stack.append(re.sub(r'\s+', ' ', mm.group(1).strip()))
            else:
                stack.append(None)
            ctx[mm.end()] = tuple(x for x in stack if x)
        def context_at(pos):
            keys = [k for k in ctx if k <= pos]
            return ctx[max(keys)] if keys else ()
        for m in SIMPLE.finditer(blank):
            c = context_at(m.start())
            rules.append((f, m.group(1), m.group(2), m.start(), m.end()))
            groups.setdefault((f, c, norm(m.group(2))), []).append(m.group(1))
    used = lambda c: re.search(r'\b' + re.escape(c) + r'\b', allhtml) or c in js
    dead = [c for _, c, _, _, _ in rules if not used(c) and c not in compound]
    # a class with MORE THAN ONE rule (a base and a media variant, say) is not the sum of one
    # body: aliasing it on one rule's strength drops the other — first run turned a PTC label
    # violet that way (render-census caught it). Only single-rule classes take part.
    nrules = collections.Counter(c for _, c, _, _, _ in rules)
    alias = {}
    for key, members in groups.items():
        keep = [c for c in members if c not in dead and nrules[c] == 1]
        if len(keep) < 2: continue
        canon = keep[0]
        for c in keep[1:]:
            if c in compound: continue
            alias[c] = canon
    print(f'{len(rules)} xi rules · {len(groups)} distinct bodies · {len(alias)} aliases → canonical · {len(dead)} dead (unused anywhere) · {len(compound)} kept for compound selectors')
    if not apply:
        for c, k in list(alias.items())[:8]: print(f'   {c} → {k}')
        print('dry run. --apply to write.'); return 0
    # rewrite pages
    changed_pages = 0
    for p, s in html.items():
        def fix(m):
            classes = m.group(1).split()
            out = []
            for c in classes:
                c2 = alias.get(c, c)
                if c2 not in out: out.append(c2)
            return f'class="{" ".join(out)}"'
        s2 = re.sub(r'class="([^"]*)"', fix, s)
        if s2 != s: open(p, 'w', encoding='utf-8').write(s2); changed_pages += 1
    # delete alias + dead rules from the sources
    remove = set(alias) | set(dead)
    removed = 0
    for f, s in css.items():
        def drop(m):
            nonlocal removed
            if m.group(1) in remove: removed += 1; return ''
            return m.group(0)
        s2 = SIMPLE.sub(drop, s)
        if s2 != s: open(f, 'w', encoding='utf-8').write(s2)
    print(f'applied: {changed_pages} page(s) rewritten, {removed} rule(s) removed')
    json.dump({'alias': alias, 'dead': dead}, open(os.path.join(ROOT, 'css', 'site', 'xi-dedup-2026-09-13.json'), 'w'), indent=1)
    os.system(f'python3 {os.path.join(ROOT, "tools", "build-css.py")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
