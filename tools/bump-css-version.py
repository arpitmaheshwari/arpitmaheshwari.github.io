#!/usr/bin/env python3
"""Bump the ember.css cache version on EVERY page, whatever version it is on.

Why: bumps were done with `sed s/v=eN/v=eN+1/`, which only touches pages already
on eN. Pages drifted onto different versions (e12 vs e26 in the wild), so a bump
silently missed most of the site and CSS fixes "did not apply" — twice.
Usage: python3 tools/bump-css-version.py [newversion]
"""
import re, sys, pathlib
new = sys.argv[1] if len(sys.argv)>1 else None
files = [p for p in pathlib.Path('.').rglob('*.html')
         if not any(x.startswith('.') or x in ('prototypes','node_modules','portfolio-sources') for x in p.parts)]
cur = set()
for p in files: cur.update(re.findall(r'ember\.css\?v=([a-z0-9]+)', p.read_text()))
if not new:
    nums = [int(v[1:]) for v in cur if v.startswith('e') and v[1:].isdigit()]
    new = 'e' + str((max(nums) if nums else 0) + 1)
n = 0
for p in files:
    s = p.read_text(); s2 = re.sub(r'ember\.css\?v=[a-z0-9]+', f'ember.css?v={new}', s)
    if s2 != s: p.write_text(s2); n += 1
print(f"was {sorted(cur)} -> now {new} on {n} page(s)")
