#!/usr/bin/env python3
"""csslib.py — the one CSS parser the stylesheet tools share.

Split a stylesheet into top-level items, partition the extracted .xi-* classes,
lift !important declarations, unwrap @layer blocks. Extracted 2026-09-12 from
css-layerize.py, which rebuilt styles.css and ember.css on cascade layers and
retired when those two files were folded into site.css (tools/css-consolidate.py).
Its history is kept here because the lessons still govern this parser:

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

KNOWN LIMIT, found the day this file was extracted: split_rules scans for braces
WITHOUT blanking comments first, so a comment that quotes a rule (`.pass .grid{...}`
in prose) opens a phantom rule. Callers protect comments with placeholders before
splitting (css-consolidate.protect_comments) — do the same in any new caller.
"""
import re, sys, pathlib



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
    # drop a note this script wrote on a previous run, or every rebuild stacks
    # another copy on top — the same idempotency trap as the layer wrappers.
    css = re.sub(r'/\*\s*Wrapped into the cascade layers.*?\*/\s*', '', css, flags=re.S)
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
