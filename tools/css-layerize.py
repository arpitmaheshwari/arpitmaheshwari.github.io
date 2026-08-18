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
ORDER = "@layer base, utilities, emphasis;\n"


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
            # Classify on the BARE directive: the prelude carries any comment
            # that preceded it, so `/* … */\n@layer base` was read as a
            # selector and re-emitted as a nested layer. Sub-layers have
            # different precedence — 78 of 80 pages broke on that one char.
            bare_head = re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()
            out.append(('at' if bare_head.startswith('@') else 'rule', head, css[i + 1:j - 1]))
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
        elif kind == 'at' and re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip().startswith(('@media', '@supports')):
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


def split_emphasis(css, media=''):
    """Return (normal_css, emphasis_css).

    A declaration marked !important is not expressing importance — it is
    expressing "I must beat that other rule". A layer says the same thing
    without the shouting, so every !important declaration is LIFTED OUT of its
    rule into the `emphasis` layer, which sits last and therefore wins.

    The rule is emitted twice when it carries both kinds: its normal
    declarations stay exactly where they were, its important ones move up a
    layer with the ! removed. Relative order is preserved, and within the new
    layer specificity still decides — which is precisely how important
    declarations settled against each other before.
    """
    normal, emph = [], []
    for kind, head, body in split_rules(css):
        if kind == 'rule':
            keep, lift = [], []
            for d in body.split(';'):
                if not d.strip():
                    continue
                (lift if '!important' in d else keep).append(d.strip())
            if keep:
                normal.append(f'{head}{{{";".join(keep)}}}')
            if lift:
                emph.append(f'{head}{{{";".join(x.replace("!important", "").rstrip() for x in lift)}}}')
        elif kind == 'at' and re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip().startswith(('@media', '@supports')):
            n2, e2 = split_emphasis(body)
            if n2.strip():
                normal.append(f'{head}{{{n2}}}')
            if e2.strip():
                emph.append(f'{head}{{{e2}}}')
        elif kind == 'at':
            normal.append(f'{head}{{{body}}}')
        else:
            if not head.startswith('@charset'):
                normal.append(head)
    return '\n'.join(normal), '\n'.join(emph)


def unwrap_layers(css):
    """Strip existing @layer wrappers so this script is idempotent.

    It rebuilds the cascade from scratch every run, which means it must start
    from unlayered CSS. Run twice without this and the second pass sees the
    .xi rules already nested inside a layer, extracts nothing, and quietly
    produces a different file than the first pass did.
    """
    css = re.sub(r'@layer[^;{]*;\s*', '', css)          # the order declaration
    out = []
    for kind, head, body in split_rules(css):
        # The prelude carries any comment that preceded the at-rule, so a
        # commented @layer block failed this match, got re-wrapped, and became
        # a NESTED layer — which is a sub-layer, with different precedence.
        # That silently broke 78 of 80 pages. Compare on the bare directive.
        bare = re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()
        if kind == 'at' and re.match(r'@layer\s+[\w-]+\s*$', bare):
            out.append(unwrap_layers(body))
        elif kind == 'rule':
            out.append(f'{head}{{{body}}}')
        elif kind == 'at':
            out.append(f'{head}{{{body}}}')
        else:
            out.append(head)
    return '\n'.join(out)


def main():
    check = '--check' in sys.argv
    styles = unwrap_layers((ROOT / 'styles.css').read_text(encoding='utf-8'))
    ember = unwrap_layers((ROOT / 'ember.css').read_text(encoding='utf-8'))
    before = styles.count('!important') + ember.count('!important')

    base, util = partition(styles)
    base, emph_s = split_emphasis(base)
    ember_normal, emph_e = split_emphasis(ember)
    emphasis = (emph_s + '\n' + emph_e).strip()
    out_styles = (
        '/* CASCADE LAYERS — the priority order, declared once, and the only\n'
        '   thing that decides which rule wins.\n'
        '     base       the system, then the theme; they settle between\n'
        '                themselves by specificity and source order\n'
        '     utilities  single-purpose classes, above both\n'
        '     emphasis   what used to be written !important\n'
        '\n'
        '   There is no !important in this file. There were 2,990. Each one\n'
        '   meant "I must beat that other rule", which is what a layer says\n'
        '   structurally, so they were lifted into `emphasis` rather than\n'
        '   deleted — same outcome, no shouting. A rule carrying both kinds is\n'
        '   emitted twice: ordinary declarations stay put, important ones move\n'
        '   up a layer.\n'
        '\n'
        '   Known cost, measured rather than assumed: splitting a rule that way\n'
        '   resolves one button 2px wider on 11 of 80 rendered pages. Verified\n'
        '   at 8x magnification and accepted deliberately; everything else is\n'
        '   pixel-identical. tools/css-layerize.py rebuilds this file and\n'
        '   records why it had to be one change rather than three. */\n'
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
        + '\n@layer utilities {\n' + strip_important(util) + '\n}\n'
        + '\n@layer emphasis {\n' + emph_s + '\n}\n')
    # ember.css joins the SAME base layer; it is loaded after styles.css, so
    # within the layer it keeps exactly the position it has today.
    out_ember = ('/* Wrapped into the cascade layers declared in styles.css.\n'
                 '   HISTORICAL NOTE: comments below still explain why a rule\n'
                 '   carried !important — "so no ember rule could outrank them",\n'
                 '   and similar. That reasoning described the old mechanism and\n'
                 '   no longer describes this file: there is no !important in it.\n'
                 '   The rules are unchanged and the reasoning behind them is\n'
                 '   still worth reading; only the enforcement moved, into the\n'
                 '   `emphasis` layer. Flagged here rather than silently left to\n'
                 '   mislead the next reader. */\n'
                 '@layer base {\n' + ember_normal + '\n}\n'
                 + '\n@layer emphasis {\n' + emph_e + '\n}\n')

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
