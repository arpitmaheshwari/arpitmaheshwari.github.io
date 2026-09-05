#!/usr/bin/env python3
"""social-title-check.py — twitter:title must not say something og:title does not

The site's convention, held on 40 of 41 pages: twitter:title is og:title with the
"| Arpit Maheshwari" byline stripped, because a Twitter card shows the site name
separately. Descriptions deliberately diverge — the card gets a punchier line — and
that is an editorial choice, so this checks TITLES only.

patterns/provenance-citations.html broke it in the one direction that is always a
mistake: its twitter:title said "Provenance & Citations Patterns" while og:title,
the <title> and the h1 all said "Provenance & Citations". The card advertised a word
that appears nowhere on the page. Nothing compares two meta tags to each other, so
nothing saw it.

Rule: after stripping a trailing byline, twitter:title must be a prefix of og:title.
Longer, or divergent, fails.

Exit 0 clean · 1 finding.
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ('prototypes/', 'portfolio-sources/', 'tests/', 'assets/', 'partials/')
BYLINE = re.compile(r'\s*[|—–-]\s*Arpit Maheshwari\s*$')

bad, checked = [], 0
for f in sorted(glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True)):
    # Scratch files: gates plant temp .html into the docroot during their
    # calibration (__canon_canary_a.html, __al_*.html, __tr.html). If the
    # owning gate deletes one between this glob and the open, this gate dies
    # with FileNotFoundError mid-push — which is how image-dimension-check
    # broke a push on 2026-09-05. Every scratch name carries the __ prefix.
    if os.path.basename(f).startswith('__'):
        continue
    rel = os.path.relpath(f, ROOT)
    if rel.startswith(SKIP):
        continue
    s = open(f, encoding='utf-8').read()
    og = re.search(r'property="og:title"[^>]*content="([^"]+)"', s)
    tw = re.search(r'name="twitter:title"[^>]*content="([^"]+)"', s)
    if not (og and tw):
        continue
    checked += 1
    o, t = BYLINE.sub('', og.group(1)).strip(), BYLINE.sub('', tw.group(1)).strip()
    if o != t and not o.startswith(t):
        bad.append((rel, og.group(1), tw.group(1)))

for rel, o, t in bad:
    print(f'  {rel}\n      og:title      {o}\n      twitter:title {t}\n'
          f'      the card says something the page does not.')
if bad:
    print(f'\n{len(bad)} social-title divergence(s) across {checked} pages.')
    sys.exit(1)
print(f'{checked} pages: every twitter:title is og:title minus the byline.')
print('CANNOT SEE: whether either title is TRUE of the page, or matches the h1.')
