#!/usr/bin/env python3
"""build-css.py — site.css is the concatenation of css/site/*.css, in order. That is the whole build.

WHY (2026-09-13, architecture review finding #1). Until tonight site.css had no source: it was
re-derived on every change by folding two RETIRED stylesheets through three Python passes and a
124-line CSS string literal inside a Python file. A one-line CSS change meant editing a Python
string and regenerating 41 pages' cache stamps. The fold was a one-time migration being run as a
build. It ran for the last time to produce the file this script now treats as the source.

The source is css/site/: one file per cascade layer, each holding exactly its `@layer x{…}`
block, plus the header. Edit those. Run this. Then tools/build-partials.py re-stamps `?v=`.
The output is byte-identical to the retired pipeline's last output — proven by render-census
(0 differences across 35 pages × 4 widths) and pixel-census on the night of the switch.
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'css', 'site')
OUT = os.path.join(ROOT, 'site.css')
ORDER = ['00-header.css', '01-tokens.css', '02-components.css', '03-utilities.css', '04-overrides.css']


def build():
    parts = [open(os.path.join(SRC, f), encoding='utf-8').read() for f in ORDER]
    gaps = json.load(open(os.path.join(SRC, '.gaps.json'))) if os.path.exists(os.path.join(SRC, '.gaps.json')) else ['\n'] * 4
    out = parts[0]
    for i, p in enumerate(parts[1:]):
        out += p + (gaps[i] if i < len(gaps) else '\n')
    return out


if __name__ == '__main__':
    css = build()
    if '--check' in sys.argv:
        cur = open(OUT, encoding='utf-8').read()
        print('site.css matches css/site/ byte for byte' if cur == css else f'site.css DIFFERS from the build by {abs(len(cur)-len(css))} chars'); sys.exit(0 if cur == css else 1)
    open(OUT, 'w', encoding='utf-8').write(css); print(f'site.css written: {len(css):,} chars from {len(ORDER)} source files')
