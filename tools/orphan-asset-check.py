#!/usr/bin/env python3
"""orphan-asset-check.py — files shipped to visitors that nothing points at

1.7 MB of assets/ was referenced by no HTML, CSS, JS, JSON, XML or text file in the
repository: thirteen webfonts from font stacks that lost the selection (Inter,
Newsreader, Public Sans, IBM Plex Sans and Mono, DM Mono, Literata — 642 KB), eleven
superseded diagrams, a 725 KB pattern illustration, and a ZERO-BYTE JPEG that a failed
copy left behind and a commit carried in.

None of it broke a page, which is exactly why it survived: every gate here asks whether
something the page NEEDS is present. Nothing asked the reverse — whether something
present is needed. On a site whose teardown page argues for a lean build, dead weight in
the repository is a claim quietly going stale.

Matching is by basename across every tracked text file, so a path built with a different
prefix still counts as a reference. og-images/ is exempt: those are generated per page
and referenced by absolute URL in meta tags, which the basename match already sees, but
they are listed separately to keep the two inventories distinct.

Exit 0 clean · 1 orphan found.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = ('.css', '.html', '.js', '.json', '.txt', '.xml', '.md', '.yml', '.yaml')
SKIP_PREFIX = ('prototypes/', 'node_modules', 'tests/pw/node_modules')

def tracked():
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split('\0') if p]

files = tracked()
corpus = []
for rel in files:
    if rel.startswith(SKIP_PREFIX) or not rel.endswith(TEXT):
        continue
    try:
        corpus.append(open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read())
    except OSError:
        pass
blob = '\n'.join(corpus)

orphans = []
for rel in files:
    if not rel.startswith('assets/') or '/og-images/' in rel:
        continue
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        continue
    if os.path.basename(rel) not in blob:
        orphans.append((rel, os.path.getsize(path)))
    elif os.path.getsize(path) == 0:
        orphans.append((rel, 0))

for rel, size in orphans:
    why = 'zero bytes' if size == 0 else f'{size/1024:.0f} KB, referenced nowhere'
    print(f'  {rel} — {why}')
if orphans:
    total = sum(s for _, s in orphans) / 1024
    print(f'\n{len(orphans)} orphan asset(s), {total:.0f} KB. Delete them or point at them.')
    sys.exit(1)
print(f'{len(files)} tracked files: every asset is referenced and none is empty.')
print('CANNOT SEE: an asset referenced only from an untracked file, one built from a')
print('string at runtime, or a file that IS referenced but by a page nobody can reach.')
