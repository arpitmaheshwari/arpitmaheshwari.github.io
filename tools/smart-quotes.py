#!/usr/bin/env python3
"""Set straight quotes and apostrophes as typographic ones, in prose only.

The site used curly marks in 363 places and straight ones in 129, and
apostrophes ran the other way — 634 straight against 134 curly. On a portfolio
whose argument IS craft, mixed quote styles is the detail a design reader
notices before they reach the work.

What it will not touch:
  - anything inside a tag, so every attribute, class and URL is untouched
  - script, style, code, pre, kbd, samp, var — a literal must stay literal
  - a quoted string that looks like code ("*.html", "--flag", "a > b")
  - a file whose double quotes do not pair up; an odd count means the
    apostrophe/quote reading is ambiguous, so it is reported, not guessed

--check reports what would change and exits non-zero, for the gate.
"""
import argparse, re, subprocess, sys

SKIP = re.compile(r'^</?(script|style|code|pre|kbd|samp|var)\b', re.I)
TAG = re.compile(r'<[^>]*>', re.S)
CODEY = re.compile(r'[*{}\\|<>=;$]|^-{1,2}\w|\.\w{2,4}$|^\w+\(\)')


def split_stream(s):
    """Yield ('tag'|'text', chunk) preserving the document exactly."""
    i = 0
    for m in TAG.finditer(s):
        if m.start() > i:
            yield 'text', s[i:m.start()]
        yield 'tag', m.group(0)
        i = m.end()
    if i < len(s):
        yield 'text', s[i:]


def convert(src):
    out, depth, changes = [], 0, 0
    open_quote = False
    # Pre-scan: are the straight double quotes in prose balanced?
    prose = ''.join(c for k, c in split_stream(src) if k == 'text')
    balanced = prose.count('"') % 2 == 0

    for kind, chunk in split_stream(src):
        if kind == 'tag':
            if SKIP.match(chunk):
                depth += 0 if chunk.startswith('</') else 1
                if chunk.startswith('</'):
                    depth = max(0, depth - 1)
            out.append(chunk)
            continue
        if depth > 0:
            out.append(chunk)
            continue

        t = chunk
        # Apostrophes: between letters (don't, O'Neill), and elisions ('90s).
        new = re.sub(r"(?<=[A-Za-z])'(?=[A-Za-z])", '’', t)
        new = re.sub(r"(?<=[A-Za-z])'(?=\s|[.,;:!?)]|$)", '’', new)
        new = re.sub(r"(?<![A-Za-z])'(?=\d\d\b)", '’', new)

        if balanced:
            res = []
            for ch in new:
                if ch == '"':
                    res.append('”' if open_quote else '“')
                    open_quote = not open_quote
                else:
                    res.append(ch)
            candidate = ''.join(res)
            # Undo the pair if what it wrapped looks like code, not speech.
            def restore(m):
                return m.group(0) if not CODEY.search(m.group(1)) \
                    else '"%s"' % m.group(1)
            candidate = re.sub('“([^“”]{0,80})”',
                               restore, candidate)
            new = candidate
        if new != t:
            changes += sum(1 for a, b in zip(t, new) if a != b)
        out.append(new)
    return ''.join(out), changes, balanced


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    files = [f for f in subprocess.run(['git', 'ls-files', '*.html'],
                                       capture_output=True, text=True).stdout.split()
             if not f.startswith(('tests/', 'assets/og-images/'))]
    total, touched, skipped = 0, 0, []
    for f in files:
        src = open(f, encoding='utf-8').read()
        new, n, balanced = convert(src)
        if not balanced:
            skipped.append(f)
        if n:
            total += n
            touched += 1
            print(f'  {"would set" if a.check else "set":10} {n:4} mark(s)  {f}')
            if not a.check:
                open(f, 'w', encoding='utf-8').write(new)
    for f in skipped:
        print(f'  SKIPPED    unbalanced straight quotes in prose — {f}')
    print(f'\n{total} mark(s) across {touched} file(s)'
          f'{"; " + str(len(skipped)) + " file(s) need a human" if skipped else ""}')
    return 1 if (a.check and (total or skipped)) else 0


if __name__ == '__main__':
    sys.exit(main())
