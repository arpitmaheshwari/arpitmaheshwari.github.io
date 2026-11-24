#!/usr/bin/env python3
"""resources-preview-check — the "Inside" previews on /resources/ are copies; this proves they still match.

WHY (2026-11-24): each row on the resources index shows the first three real lines of its resource and
"+ N more". Those lines are typed into the index, so an edit to the resource page leaves a stale quote
on the index and nothing notices. This reads both and fails when
  1. a preview line is not, word for word, an item on the page it links to,
  2. the three lines are not that page's FIRST three items, in order,
  3. "+ N more" is not (items on the page - 3).

What it cannot see: whether the card's title or description still describes the page (canon-lint's job),
and anything about how the preview renders. It reads source files only; no browser, no server.

  python3 tools/resources-preview-check.py            # check
  python3 tools/resources-preview-check.py --selftest # plant three defects in memory, require three reds
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'partials', 'pages', 'resources')
# how each resource marks one item; the count of matches is the number the index must add up to
ITEMS = {
    'ai-design-checklist.html': r'<li class="xi-resources-ai-design-checklist-019">(.*?)</li>',
    'founder-questions.html': r'<strong>(\s*&ldquo;.*?)</strong>',
    'intelligent-systems-glossary.html': r'<dt\b[^>]*>(.*?)</dt>',
}


def text(fragment):
    t = re.sub(r'<[^>]+>', ' ', fragment)
    t = html.unescape(t).replace(' ', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def check(index, pages):
    errs = []
    rows = re.findall(r'<a class="card-p32[^"]*" href="\./([^"]+)".*?<[ou]l class="rx-list">(.*?)</[ou]l>\s*<p class="rx-more">\+ (\d+) more', index, re.S)
    if len(rows) != len(ITEMS):
        errs.append('expected %d preview rows on the index, found %d' % (len(ITEMS), len(rows)))
    for href, lis, more in rows:
        if href not in ITEMS:
            errs.append('%s: no item rule for this page — add one to ITEMS' % href); continue
        items = [text(m) for m in re.findall(ITEMS[href], pages[href], re.S)]
        shown = [text(m) for m in re.findall(r'<li>(.*?)</li>', lis, re.S)]
        if len(shown) != 3:
            errs.append('%s: preview shows %d lines, expected 3' % (href, len(shown)))
        for i, line in enumerate(shown):
            if line not in items:
                errs.append('%s: preview line %d is not an item on the page: "%s"' % (href, i + 1, line))
            elif i >= len(items) or items[i] != line:
                errs.append('%s: preview line %d is not item %d of the page: "%s"' % (href, i + 1, i + 1, line))
        if int(more) != len(items) - len(shown):
            errs.append('%s: index says "+ %s more" but the page has %d items (%d shown, so %d more)' % (href, more, len(items), len(shown), len(items) - len(shown)))
    return errs


def load():
    index = open(os.path.join(SRC, 'index.html'), encoding='utf8').read()
    pages = {f: open(os.path.join(SRC, f), encoding='utf8').read() for f in ITEMS}
    return index, pages


def main():
    index, pages = load()
    if '--selftest' in sys.argv:
        plants = [
            ('a reworded preview line', index.replace('<li>Abstention</li>', '<li>Abstaining</li>', 1)),
            ('a wrong count', index.replace('+ 50 more', '+ 49 more', 1)),
            ('lines out of order', index.replace('<li>Abstention</li><li>Act / Review / Ignore</li>', '<li>Act / Review / Ignore</li><li>Abstention</li>', 1)),
        ]
        bad = 0
        for name, planted in plants:
            assert planted != index, 'selftest anchor missing: ' + name
            got = check(planted, pages)
            print('selftest: %-26s -> %s' % (name, 'RED (%d)' % len(got) if got else 'stayed green'))
            bad += 0 if got else 1
        if check(index, pages):
            print('selftest: the unplanted index is not green'); bad += 1
        sys.exit(1 if bad else 0)
    errs = check(index, pages)
    for e in errs:
        print('resources-preview-check: ' + e)
    if errs:
        sys.exit(1)
    print('resources-preview-check: 3 previews match their pages, line for line and count for count')


if __name__ == '__main__':
    main()
