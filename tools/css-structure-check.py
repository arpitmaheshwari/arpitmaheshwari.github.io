#!/usr/bin/env python3
"""
CSS STRUCTURAL INTEGRITY — braces balanced, and @layer still wraps what it wrapped.

WHY THIS EXISTS. On 2026-09-10, mid-session, a single orphan `}` in ember.css
closed `@layer base` at char 29,123 instead of 191,305 — dumping ~161KB, the
bulk of the stylesheet, OUT of the layer. Unlayered rules outrank layered ones
regardless of specificity, so the cascade for the entire site inverted in one
character. The visible symptom was one homepage h2 rendering 44px instead of
42px, because `.voices h2` (higher specificity, previously layered and losing)
started beating `body.p-home main h2` (unlayered). heading-rank-check caught
that ONE pixel-level symptom. Nothing looked at the cause, and the cause was
sitting in plain text.

HOW THE BRACE GOT THERE, because the mechanism matters more than the fix: I
moved a media query by cutting `c[i:j]` where
`j = c.index('}\\n', c.index('.pass .pc{font-size:36px}'))`. That is "find the
next closing brace" — the CSS twin of "find the next closing tag", which this
repo's execution lesson 2 forbids by name. It matched the `.pc` RULE's own
closing brace, so the cut ended one brace early and left the media query's `}`
behind. Committed in the same session as a gate written about exactly that
mistake in HTML.

WHAT IT CHECKS, on text alone — no browser, no server, ~0.2s:
  1. every stylesheet's braces balance, and depth never goes negative (a
     negative depth localises an orphan `}` to a line);
  2. every @layer block's span, as a share of the file, against a recorded
     baseline. A layer that suddenly wraps 9% of the file instead of 57% is
     the signature of this defect, and a share is stable under ordinary edits
     in a way a char offset is not.

Comments are blanked before counting, so a `}` inside a comment cannot fool it
— an earlier version of this file's own logic was fooled by exactly that when
inline-style-check parsed prose as declarations.

WHERE IT POINTS. On the real defect the negative-depth line was 1259, not 332
where the orphan actually sat — because an orphan `}` inside @layer base
*legally* closes the layer (depth 1 -> 0), and depth only goes negative at the
layer's own closing brace much later. So read the LAYER SHARE finding to know
what happened and roughly where; the line number is the point at which the
imbalance becomes undeniable, not the typo.

WHAT IT CANNOT SEE: whether the layer ASSIGNMENT is right, only that it did not
change; unbalanced parentheses inside a value; an @media that is balanced but
nests the wrong rules. Those need the browser gates.
"""
import sys, os, re, json, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'css-layer-baseline.json')
TOL = 0.06        # a layer's share of its file may drift this much before it is a finding


def decomment(s):
    """blank out /* ... */ so braces inside prose never count as structure"""
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), s, flags=re.S)


def brace_report(src):
    """(balance, first line where depth goes negative or None)"""
    s = decomment(src)
    depth, line, neg = 0, 1, None
    for ch in s:
        if ch == '\n':
            line += 1
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0 and neg is None:
                neg = line
    return depth, neg


def layer_shares(src):
    """{name: {share, chars}} for each top-level @layer block, by brace depth.

    THE SHARE ALONE HAS A FALSE POSITIVE, found 2026-09-12. A share falls for two
    completely different reasons: the layer shrank (the defect this gate exists for —
    an orphan `}` closing it early) or the FILE GREW while the layer stayed put. Adding
    27KB of rules to ember.css's unlayered tail dropped @layer base from 53.8% to 50.1%
    and the gate reported "rules moved in or out of the layer", which had not happened:
    base's span was unchanged to the character, +0. So the absolute span is recorded
    alongside the share, and a share drift with an unchanged span is not a finding.
    The share is still the primary signal, because it is what survives ordinary edits.
    """
    s = decomment(src)
    out = {}
    for m in re.finditer(r'@layer\s+([\w, ]+)\s*\{', s):
        depth, i = 0, m.end() - 1
        while i < len(s):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        name = m.group(1).strip()
        out.setdefault(name, {'share': round((i - m.start()) / float(len(s)), 3),
                              'chars': i - m.start()})
    return out


def sheets():
    return sorted(f for f in glob.glob(os.path.join(ROOT, '**', '*.css'), recursive=True)
                  if 'prototypes' not in f and 'node_modules' not in f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--record', action='store_true',
                    help='write the current layer shares as the baseline')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        good = 'a{color:red}\n@layer base {\n.x{color:blue}\n.y{color:green}\n}\n.z{color:teal}\n'
        bad = good.replace('.x{color:blue}\n', '.x{color:blue}\n}\n')     # one orphan brace
        d0, n0 = brace_report(good)
        d1, n1 = brace_report(bad)
        s0, s1 = layer_shares(good), layer_shares(bad)
        ok = (d0 == 0 and n0 is None and d1 != 0 and s1['base'] < s0['base'])
        print('[calibration] %s — clean sheet balances (%+d); one planted orphan brace '
              'unbalances it (%+d) and shrinks @layer base %.0f%% -> %.0f%%'
              % ('PASS' if ok else 'FAIL', d0, d1, 100 * s0['base'], 100 * s1['base']))
        # a brace inside a comment must NOT register
        cmt = 'a{color:red}\n/* a stray } inside prose */\n'
        d2, _ = brace_report(cmt)
        print('[calibration] %s — a `}` inside a comment is ignored (%+d)'
              % ('PASS' if d2 == 0 else 'FAIL', d2))
        if not ok or d2 != 0:
            return 2

    base = {}
    if os.path.exists(BASELINE):
        base = json.load(open(BASELINE))

    findings, cur = [], {}
    for f in sheets():
        rel = os.path.relpath(f, ROOT)
        src = open(f, encoding='utf-8', errors='replace').read()
        d, neg = brace_report(src)
        if d != 0:
            findings.append('%s: braces do not balance (%+d) — an unclosed or orphan rule' % (rel, d))
        if neg is not None:
            findings.append('%s: brace depth goes NEGATIVE at line %d — an orphan `}` there '
                            'closes whatever block encloses it (an @layer, most likely)' % (rel, neg))
        sh = layer_shares(src)
        if sh:
            cur[rel] = sh
            for name, info in sh.items():
                share, chars = info['share'], info['chars']
                want = (base.get(rel) or {}).get(name)
                if want is None:
                    continue
                # a baseline recorded before this gate kept spans is a bare float
                want_share = want['share'] if isinstance(want, dict) else want
                want_chars = want.get('chars') if isinstance(want, dict) else None
                if abs(share - want_share) <= TOL:
                    continue
                if want_chars is not None and chars == want_chars:
                    # the layer is byte-identical; the file grew around it. Not the
                    # defect this checks for, and saying so is more use than silence.
                    print('  note %s: @layer %s share moved %.0f%% -> %.0f%% but its span '
                          'is unchanged (%d chars) — the file grew around it, nothing moved '
                          'in or out.' % (rel, name, 100 * want_share, 100 * share, chars))
                    continue
                delta = '' if want_chars is None else ' (span %+d chars)' % (chars - want_chars)
                findings.append('%s: @layer %s wraps %.0f%% of the file, baseline %.0f%% '
                                '(%+.0f points)%s — rules moved in or out of the layer, which '
                                'reorders the whole cascade'
                                % (rel, name, 100 * share, 100 * want_share,
                                   100 * (share - want_share), delta))

    if a.record:
        json.dump(cur, open(BASELINE, 'w'), indent=1, sort_keys=True)
        open(BASELINE, 'a').write('\n')
        print('recorded layer shares for %d stylesheet(s): %s'
              % (len(cur), ', '.join('%s %s' % (k, v) for k, v in sorted(cur.items()))))
        return 0

    if findings:
        print('%d CSS structure finding(s):\n' % len(findings))
        for f in findings:
            print('  %s' % f)
        return 1
    n = len(sheets())
    print('Result: clean — %d stylesheet(s) balance, and every @layer wraps the same share '
          'of its file as the recorded baseline.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
