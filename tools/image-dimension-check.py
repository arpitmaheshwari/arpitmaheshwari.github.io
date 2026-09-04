#!/usr/bin/env python3
"""image-dimension-check.py — does every raster image reserve its own space?

The three photographs on the O2 case study carried no width/height attributes. With
loading="lazy" and CSS of width:100%;height:auto, the browser reserved TWO PIXELS of
height for each until the file arrived, then shoved ~195px of page down — three times,
on a phone. Measured before and after: 342x2 became 342x199.

Nothing saw it. Every gate here asks about a element's colour, its overflow, its text or
its position ON A FULLY LOADED PAGE — this defect exists only in the seconds BEFORE the
image loads, which is the whole of the reader's first impression.

Rule: a raster <img> must declare width and height. SVGs are exempt (they carry their own
viewBox and are sized by CSS).

It does NOT require the attributes to match the file's real pixels. I wrote that rule first
and it produced six findings, every one a false positive: the avatars declare 34x34 against
a 926x1273 photo, and the PTC screenshot declares 1280x1400 against a 1280x1313 file, but
all of them are styled object-fit:cover inside a CSS-determined box, so the attributes never
govern their layout. A check that cries wolf six times to catch nothing gets switched off,
so the rule was deleted rather than kept with exceptions.

Exit 0 clean · 1 finding.
"""
import glob, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ('prototypes/', 'portfolio-sources/', 'tests/', 'assets/', 'partials/')

def png_jpg_size(path):
    with open(path, 'rb') as fh:
        head = fh.read(24)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', head[16:24])
        if head[:2] == b'\xff\xd8':
            fh.seek(2)
            while True:
                byte = fh.read(1)
                while byte and byte != b'\xff':
                    byte = fh.read(1)
                marker = fh.read(1)
                while marker == b'\xff':
                    marker = fh.read(1)
                if not marker:
                    return None
                if marker[0] in range(0xC0, 0xD0) and marker[0] not in (0xC4, 0xC8, 0xCC):
                    fh.read(3)
                    h, w = struct.unpack('>HH', fh.read(4))
                    return w, h
                length = struct.unpack('>H', fh.read(2))[0]
                fh.read(length - 2)
    return None

findings, checked = [], 0
# gatelib.pages() enumerates from `git ls-files`, so an untracked temp file cannot appear
# in it. A raw glob can: canon-lint writes __canon_canary_a.html into the repo root during
# its calibration, and this gate globbed it a moment before it was deleted, then died with
# FileNotFoundError mid-push. Same shape as the ember.css race — one gate's scratch file
# inside another gate's working set.
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from gatelib import pages as _pages
for rel in _pages(include_redirects=True):
    f = os.path.join(ROOT, rel)
    if rel.startswith(SKIP):
        continue
    src_html = re.sub(r'(?s)<!--.*?-->', '', open(f, encoding='utf-8').read())
    for m in re.finditer(r'<img\b([^>]*)>', src_html):
        attrs = m.group(1)
        src = (re.search(r'src="([^"]+)"', attrs) or [None, ''])[1]
        if not src or src.lower().endswith('.svg') or src.startswith(('http', 'data:')):
            continue
        checked += 1
        w = re.search(r'\bwidth="(\d+)"', attrs)
        h = re.search(r'\bheight="(\d+)"', attrs)
        if not (w and h):
            findings.append((rel, src, 'no width/height — reserves no space before it loads'))

for rel, src, why in findings:
    print(f'  {rel}\n      {src} — {why}')
if findings:
    print(f'\n{len(findings)} image(s) of {checked} will shift the page as they load.')
    sys.exit(1)
print(f'{checked} raster images: every one declares a width and height.')
print('CANNOT SEE: SVGs, CSS background images, images injected by script, whether the')
print('declared box is the right SHAPE, or an image whose CSS overrides the attributes.')
