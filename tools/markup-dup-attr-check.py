#!/usr/bin/env python3
"""
markup-dup-attr-check.py — the attribute a parser throws away without telling anyone.

WHY THIS EXISTS
    On 2026-09-12 seven of the site's inlined art diagrams were found carrying TWO
    role="img" attributes and TWO aria-label attributes each — fourteen duplicated
    attributes across five case studies, live for twenty-eight days (born in 1b376e0c,
    the commit that inlined the drawings: the inlining pass wrote its own role and
    aria-label onto tags that already had them).

    An HTML parser resolves a duplicate by keeping the FIRST occurrence and dropping the
    rest. No error, no console warning, no visual difference. So one of two deliberately
    written descriptions — in one case the longer, richer one, carrying facts the drawing
    prints in its own footer — had never been spoken to a single screen-reader user, and
    nothing in the repo could tell.

    Every gate here asks about a RESOLVED property: what colour did this text compute to,
    how wide did this box end up, what does this element say. A duplicate attribute is
    invisible to all of them BY CONSTRUCTION, because by the time anything is resolved the
    parser has already silently picked a winner. The missing class is not "duplicate
    aria-label" — it is *markup the browser has to repair before it can render it*. This
    gate checks the source text, before any parser gets to be forgiving.

WHAT IT CHECKS, on every shipped page (gatelib.pages())
    * DUPLICATE   the same attribute name twice on one start tag. Reported with the two
                  values when they differ, because differing values mean real content was
                  discarded; identical values are only redundancy.
    * Case-insensitively, because HTML attribute names are case-insensitive: CLASS and
      class on one tag is the same duplicate, and a case-sensitive check would miss it.

WHAT IT CANNOT SEE
    * Any other malformed markup: unclosed tags, mis-nesting, stray end tags, an unquoted
      attribute value containing a space. Those need a real validator; this is one rule.
    * Duplicates produced at runtime by JavaScript (setAttribute cannot duplicate, but
      innerHTML assembled from strings can ship malformed markup this never reads).
    * Duplicates inside <script>/<style> text or HTML comments — deliberately skipped,
      since that is not markup the parser acts on.
    * Whether the SURVIVING value is the right one. It was wrong in five of the seven
      original cases and no mechanical rule could have known.

USAGE
    python3 tools/markup-dup-attr-check.py [--root .] [--selftest]
EXIT
    0 = calibrated and clean · 1 = a duplicate attribute · 2 = calibration failed to go red
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gatelib import pages  # noqa: E402

# A start tag, with quoted values allowed to contain '>' — the naive [^>]* form ends the
# tag early on any attribute value holding an angle bracket, and this site has several
# (the code samples, and aria-labels quoting markup). Self-closing and void tags match too;
# both can carry duplicates.
START_TAG = re.compile(r'<([A-Za-z][\w:-]*)((?:"[^"]*"|\'[^\']*\'|[^>"\'])*)>')

# One attribute: a name, optionally = and a quoted or bare value. The name character class
# is deliberately wide (xml:lang, data-art-scoped, @click) so a duplicate on an unusual
# name is still counted rather than skipped as unparseable.
ATTR = re.compile(r'''([:@\w.\[\]()-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?''')


def _blank(text, pattern):
    """Replace each match with spaces, KEEPING its newlines.

    The first version of this used ' ' * len(match), which eats the newlines inside a long
    comment or script block and shifts every line number after it. My own first sweep
    reported adtech.html:229 for a duplicate that is on line 260 — a 31-line drift, which
    is exactly the kind of wrong-but-plausible number that sends someone to the wrong place
    in a file and makes them doubt the finding.
    """
    return pattern.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


COMMENT = re.compile(r'(?s)<!--.*?-->')
RAW_TEXT = re.compile(r'(?is)<(script|style)\b[^>]*>.*?</\1>')


def scan(text):
    """Yield (line, tag_name, attr_name, count, values) for every duplicated attribute."""
    clean = _blank(_blank(text, COMMENT), RAW_TEXT)
    for m in START_TAG.finditer(clean):
        seen = {}
        for a in ATTR.finditer(m.group(2)):
            name = a.group(1).lower()
            value = next((g for g in a.groups()[1:] if g is not None), None)
            seen.setdefault(name, []).append(value)
        for name, values in seen.items():
            if len(values) > 1:
                yield (clean[:m.start()].count('\n') + 1, m.group(1), name,
                       len(values), values)


def run(root, targets=None):
    findings = []
    rels = targets if targets is not None else pages()
    for rel in rels:
        path = os.path.join(root, rel)
        try:
            with open(path, encoding='utf-8', errors='ignore') as fh:
                text = fh.read()
        except OSError:
            continue
        for line, tag, name, count, values in scan(text):
            findings.append((rel, line, tag, name, count, values))
    return sorted(findings), len(rels)


def report(findings, n_pages):
    for rel, line, tag, name, count, values in findings:
        distinct = len({v for v in values})
        kind = 'CONTENT DISCARDED' if distinct > 1 else 'redundant'
        print(f'  {rel}:{line}  <{tag}>  {name} x{count}  — {kind}')
        if distinct > 1:
            for i, v in enumerate(values):
                head = 'kept by the parser' if i == 0 else 'DISCARDED'
                shown = (v or '')[:104] + ('…' if v and len(v) > 104 else '')
                print(f'      [{head}] {shown}')
    word = 'attribute' if len(findings) == 1 else 'attributes'
    print(f'\n{len(findings)} duplicated {word} across {n_pages} page(s)')
    print('CANNOT SEE: any other malformed markup (unclosed or mis-nested tags, stray end '
          'tags), duplicates assembled at runtime by JavaScript, duplicates inside script/'
          'style/comments, or whether the value the parser KEPT is the right one.')


def selftest(root):
    """Plant a duplicate in a real page and require the scanner to go RED on it.

    A rule that has never been watched failing is not evidence. Both halves are planted:
    a duplicate with DIFFERING values (content discarded) and one with identical values
    (redundant), because the report distinguishes them and only one shape was ever seen
    in the wild.
    """
    victim = pages()[0]
    with open(os.path.join(root, victim), encoding='utf-8') as fh:
        original = fh.read()
    plants = [
        ('differing values',
         '<p class="quombulate" id="a" class="wibble">planted</p>', 2),
        ('identical values',
         '<img src="/x.png" alt="planted" alt="planted">', 2),
    ]
    ok = True
    for label, snippet, expect in plants:
        doctored = original.replace('</body>', snippet + '\n</body>', 1)
        if doctored == original:
            print(f'  CALIBRATION FAILED: no </body> in {victim} to plant into')
            return False
        try:
            with open(os.path.join(root, victim), 'w', encoding='utf-8') as fh:
                fh.write(doctored)
            found, _ = run(root, [victim])
        finally:
            with open(os.path.join(root, victim), 'w', encoding='utf-8') as fh:
                fh.write(original)
        # Identify the plant by its own signature, not by tag name: filtering on
        # <p>/<img> would also collect a REAL duplicate elsewhere in the victim and
        # report calibration as broken when the gate was working correctly.
        planted = [f for f in found
                   if f[1] == doctored[:doctored.index(snippet)].count('\n') + 1
                   and f[4] == expect]
        if len(planted) == 1:
            print(f'  calibrated: the planted duplicate ({label}) went RED')
        else:
            print(f'  CALIBRATION FAILED: planted {label} in {victim}, '
                  f'scanner reported {found}')
            ok = False
    # and the page must scan clean once the plant is gone, or the plant was never the
    # thing that went red.
    residue, _ = run(root, [victim])
    if residue:
        print(f'  CALIBRATION FAILED: {victim} still reports {residue} after restore')
        ok = False
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if not selftest(root):
        return 2
    if a.selftest:
        return 0

    findings, n = run(root)
    report(findings, n)
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
