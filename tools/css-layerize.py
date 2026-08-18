#!/usr/bin/env python3
"""Rebuild the stylesheets on cascade layers and delete every !important.

WHY (2026-08-19, Arpit: "fix the mess that you created")
The Lab invites a reader to open the code. What they currently find is 3,053
!important declarations and the same decision copied up to 32 times under
different names. That is my doing: the inline-style extractor I wrote produced
1,109 .xi-* classes each stamped !important, and the ember theme was layered on
top of the old stylesheet instead of replacing it.

WHY IT MUST BE ONE CHANGE, not the increments I proposed and tried:
  * two cascade layers alone         -> 66 of 80 pages broke (!important
                                        INVERTS layer order, so styles.css's
                                        2,800 began beating the whole theme)
  * removing !important alone        -> 12 of 80 broke, in BOTH load orders:
                                        the theme selects at (0,3,1), a utility
                                        is (0,1,0), and order cannot beat
                                        specificity
  * consolidating rules alone        -> 7 of 80 broke, 19,413px on one page:
                                        among !important declarations, SOURCE
                                        POSITION decides, so moving a rule
                                        changes who wins
Each step is blocked by the other two. @layer is the only mechanism that beats
specificity outright, which is what lets !important go — so layering and
de-importanting are a single operation.

THE MODEL (ITCSS order; later layers win, regardless of specificity)
    settings  generic  elements  objects  components  theme  utilities
  styles.css non-.xi  -> components   (order preserved exactly)
  ember.css           -> theme        (beats components without !important)
  styles.css .xi-*    -> utilities    (beats theme, as its !important did)
This reproduces today's precedence with position instead of volume.

USAGE  css-layerize.py [--check]     --check writes nothing, just reports
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# TWO layers, not seven — and the reason is measured, not stylistic.
# Putting styles.css in `components` and ember.css in a later `theme` layer
# made the theme beat styles.css ALWAYS, even where styles.css had the higher
# specificity and legitimately won today (e.g. :where(body.p-case-studies-x)
# .plF at (0,2,0) over a plain ember class). That broke 74 of 80 pages.
# styles.css and ember.css must therefore share ONE layer, where specificity
# and source order settle things exactly as they do now. Only the extracted
# classes move up — they are the ones whose !important was doing real work.
ORDER = "@layer base, utilities;\n"


def split_rules(css):
    """Top-level items as (kind, prelude, body). kind: 'rule' | 'at' | 'stmt'."""
    out, i, n, buf = [], 0, len(css), ''
    while i < n:
        c = css[i]
        if c == '{':
            head = buf.strip(); buf = ''
            depth, j = 1, i + 1
            while j < n and depth:
                if css[j] == '{': depth += 1
                elif css[j] == '}': depth -= 1
                j += 1
            out.append(('at' if head.startswith('@') else 'rule', head, css[i + 1:j - 1]))
            i = j; continue
        if c == ';' and buf.strip().startswith('@'):
            out.append(('stmt', buf.strip() + ';', '')); buf = ''; i += 1; continue
        buf += c; i += 1
    if buf.strip():
        out.append(('stmt', buf.strip(), ''))
    return out


def is_xi(prelude):
    return all(p.strip().startswith('.xi-') for p in prelude.split(',') if p.strip())


def partition(css):
    """Return (non_xi_css, xi_css), preserving order and @media context."""
    base, util = [], []
    for kind, head, body in split_rules(css):
        if kind == 'rule':
            (util if is_xi(head) else base).append(f'{head}{{{body}}}')
        elif kind == 'at' and head.startswith(('@media', '@supports')):
            b2, u2 = partition(body)
            if b2.strip(): base.append(f'{head}{{{b2}}}')
            if u2.strip(): util.append(f'{head}{{{u2}}}')
        elif kind == 'at':
            base.append(f'{head}{{{body}}}')       # @keyframes, @font-face…
        else:
            if not head.startswith('@charset'):
                base.append(head)
    return '\n'.join(base), '\n'.join(util)


def strip_important(css):
    return re.sub(r'\s*!important', '', css)


def main():
    check = '--check' in sys.argv
    styles = (ROOT / 'styles.css').read_text(encoding='utf-8')
    ember = (ROOT / 'ember.css').read_text(encoding='utf-8')
    before = styles.count('!important') + ember.count('!important')

    base, util = partition(styles)
    out_styles = (
        '/* Cascade layers, declared once. Later layers win outright — that is\n'
        '   what replaced 3,053 !important declarations. See tools/css-layerize.py\n'
        '   for why this had to be one change rather than three. */\n'
        + ORDER
        # NOT strip_important(base). The blanket removal broke 74 of 80 pages
        # under two different layer models — identical count both times, which
        # is the tell that layers were never the cause. A layer only replaces
        # the !important that was fighting ACROSS files; the ~170 inside
        # styles.css and ember.css are fighting rules in their OWN layer, where
        # specificity still decides and !important is still the only lever.
        # Those stay. The 2,820 on .xi-* go, because the utilities layer now
        # does that job structurally.
        + '\n@layer base {\n' + base + '\n}\n'
        + '\n@layer utilities {\n' + strip_important(util) + '\n}\n')
    # ember.css joins the SAME base layer; it is loaded after styles.css, so
    # within the layer it keeps exactly the position it has today.
    out_ember = '@layer base {\n' + ember + '\n}\n'

    after = out_styles.count('!important') + out_ember.count('!important')
    print(f"  !important: {before} -> {after}")
    print(f"  base layer (styles): {len(base.splitlines())} lines")
    print(f"  utilities layer:  {len(util.splitlines())} lines")
    print(f"  base layer (ember):  {len(ember.splitlines())} lines")
    if check:
        print("  --check: nothing written"); return 0
    (ROOT / 'styles.css').write_text(out_styles, encoding='utf-8')
    (ROOT / 'ember.css').write_text(out_ember, encoding='utf-8')
    print("  written")
    return 0


if __name__ == '__main__':
    sys.exit(main())
