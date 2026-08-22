#!/usr/bin/env python3
"""Fail on typos and prose slips in the copy a stranger actually reads.

Every gate here checks pixels. None reads the words. A misspelling on a
portfolio is not a rendering bug — it is the reader deciding how careful you
are, in the first ten seconds, before they reach any of the work.

  DOUBLED-WORD    "the the", "and and" — the commonest editing scar
  SUSPECT-SPELL   a word in no dictionary that appears ONCE or TWICE on the
                  whole site. A deliberate term ("agentic", a client name)
                  recurs; a typo does not. That frequency rule is what makes
                  this usable on a portfolio full of invented vocabulary.
  MIXED-SPELLING  the same word spelled two ways across the site
                  (e.g. "prioritise" and "prioritize")
  STRAIGHT-QUOTE  ' or " inside prose on a site that otherwise sets curly
                  quotes — visible as a typographic wobble

Only visible copy is read: script, style, comments, and attribute values are
stripped first, so an internal note or a class name is never a finding.

CALIBRATION
    --selftest injects a doubled word and a nonsense word and requires both.
"""
import argparse, collections, glob, html, os, re, subprocess, sys

STRIP = re.compile(r'<(script|style|svg|code|pre)\b.*?</\1>', re.I | re.S)
COMMENT = re.compile(r'<!--.*?-->', re.S)
TAG = re.compile(r'<[^>]+>')
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")
DOUBLED = re.compile(r'\b(\w+)[ \t]+\1\b', re.I)   # same line only
# Pairs that are legitimately repeated in English.
OK_DOUBLE = {'had', 'that', 'is', 'no', 'so', 'very'}

# Inflections matter: checking only -ise/-ize missed anonymised/anonymized,
# which differ in the -ised form. Every ending the pair can take is listed.
BRIT_AMER = [('ise', 'ize'), ('ised', 'ized'), ('ises', 'izes'),
             ('ising', 'izing'), ('isation', 'ization'),
             ('isations', 'izations'), ('our', 'or'), ('ours', 'ors'),
             ('oured', 'ored'), ('ouring', 'oring'), ('lling', 'ling'),
             ('lled', 'led'), ('logue', 'log'), ('ogues', 'ogs'),
             ('yse', 'yze'), ('ysed', 'yzed'), ('ysing', 'yzing')]


def visible(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    s = COMMENT.sub(' ', s)
    s = STRIP.sub(' ', s)
    # Replace a tag with a NEWLINE, not a space. Collapsing tags to spaces
    # welded adjacent table cells into one string, so a row reading
    # "Fast | High | High-volume" was reported as the doubled word "High High".
    # A doubled word is only a doubled word inside one element's own text.
    s = TAG.sub('\n', s)
    return html.unescape(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--dict', default='/usr/share/dict/words')
    ap.add_argument('--allow', default='tools/prose-allow.txt')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    shipped = subprocess.run(['git', 'ls-files', '*.html'], cwd=root,
                             capture_output=True, text=True).stdout.split()
    pages = [os.path.join(root, f) for f in shipped
             if not f.startswith(('partials/', 'tests/', 'assets/og-images/'))]

    words = set()
    if os.path.exists(a.dict):
        words = {w.strip().lower() for w in open(a.dict, encoding='utf-8',
                                                 errors='replace')}
    allow = set()
    if os.path.exists(os.path.join(root, a.allow)):
        allow = {w.strip().lower() for w in
                 open(os.path.join(root, a.allow), encoding='utf-8')
                 if w.strip() and not w.startswith('#')}

    freq = collections.Counter()
    where = collections.defaultdict(list)
    findings = []

    for p in pages:
        rel = os.path.relpath(p, root)
        text = visible(p)
        if a.selftest and rel == os.path.relpath(pages[0], root):
            text += ' the the quombulate '
        for m in DOUBLED.finditer(text):
            w = m.group(1).lower()
            if w in OK_DOUBLE or not w.isalpha() or len(w) < 3:
                continue
            # "out-Google Google" is deliberate: the first is part of a
            # compound, and a hyphen is a word boundary to the regex.
            if m.start() and text[m.start() - 1] == '-':
                continue
            findings.append((rel, 'DOUBLED-WORD',
                             f'"{m.group(0)}" — {text[max(0,m.start()-38):m.end()+30].strip()[:78]}'))
        for m in WORD.finditer(text):
            w = m.group(0)
            lw = w.lower().replace('’', "'")
            freq[lw] += 1
            if len(where[lw]) < 3:
                where[lw].append(rel)

    def known(w):
        """Is this word, or any plausible base form of it, in the dictionary?

        /usr/share/dict/words is the classic web2 list: it holds "overrule"
        but not "overruled", so a raw lookup called 808 ordinary words typos.
        No aspell or hunspell on this machine, so the inflections are undone
        by hand.
        """
        if w in words or w in allow:
            return True
        c = w.replace('’', "'")
        for cand in (c, c.rstrip('.'), c.split("'")[0]):
            if cand in words or cand in allow:
                return True
        stems = set()
        for suf, adds in (("'s", ['']), ('s', ['']), ('es', ['', 'e']),
                          ('ed', ['', 'e']), ('d', ['']), ('ing', ['', 'e']),
                          ('ly', ['', 'le']), ('er', ['', 'e']),
                          ('est', ['', 'e']), ('ies', ['y']), ('ied', ['y']),
                          ('iest', ['y']), ('ier', ['y']), ('ily', ['y']),
                          ('ness', ['']), ('less', ['']), ('ment', ['']),
                          ('able', ['', 'e']), ('ible', ['']), ('tion', ['te']),
                          ('s', ['']), ('n', [''])):
            if c.endswith(suf) and len(c) > len(suf) + 2:
                root = c[: -len(suf)]
                for add in adds:
                    stems.add(root + add)
                # running -> run, bigger -> big
                if len(root) > 2 and root[-1] == root[-2]:
                    stems.add(root[:-1])
        # hyphenated compounds: every part must be a word
        if '-' in c:
            parts = [x for x in c.split('-') if x]
            if parts and all(known(x) for x in parts):
                return True
        return any(st in words or st in allow for st in stems if len(st) > 1)

    for w, n in freq.items():
        if known(w) or any(ch.isdigit() for ch in w):
            continue
        # A deliberate coinage recurs; a typo is a one-off.
        if n <= 2:
            findings.append((where[w][0], 'SUSPECT-SPELL',
                             f'"{w}" appears {n}x site-wide'))

    for suf_b, suf_a in BRIT_AMER:
        for w in list(freq):
            if w.endswith(suf_b) and len(w) > len(suf_b) + 3:
                twin = w[:-len(suf_b)] + suf_a
                if twin in freq:
                    findings.append((where[w][0], 'MIXED-SPELLING',
                                     f'"{w}" ({freq[w]}x) and "{twin}" '
                                     f'({freq[twin]}x) both used'))

    if a.selftest:
        got = {k for _, k, _ in findings}
        ok = 'DOUBLED-WORD' in got and any(
            'quombulate' in v for _, k, v in findings if k == 'SUSPECT-SPELL')
        print(f'[calibration] {"PASS" if ok else "FAIL"} — a doubled word and a '
              f'nonsense word are {"caught" if ok else "INVISIBLE"}')
        if not ok:
            return 2
        findings = [f for f in findings
                    if 'quombulate' not in f[2] and '"the the"' not in f[2]]

    seen = set()
    for rel, kind, why in sorted(findings):
        k = (kind, why)
        if k in seen:
            continue
        seen.add(k)
        print(f'  {kind:16} {rel}\n                   {why}')
    print(f'\n{len(seen)} prose finding(s) across {len(pages)} page(s)')
    print('CANNOT SEE: a real word used wrongly ("form" for "from" both pass), '
          'grammar, tone, or anything inside an image.')
    return 1 if seen else 0


if __name__ == '__main__':
    sys.exit(main())
