#!/usr/bin/env python3
"""art-relabel.py — raise the type inside an inlined art diagram to a rendered floor.

WHY (2026-09-21, Arpit chose "redraw the artwork with bigger labels"). The nine
diagram-led pages render their 1280-unit artboards into a 692px grid track, a scale of
0.539, so a 13-unit label reaches the reader at 7.00px against a 12.5px floor. The
layout is not available to change: commit 6a08022a confined these figures to the grid
track on purpose, because the full-width version pushed the page 31px past the viewport
at 1440 and slid the sticky rail under the drawing.

So the artwork moves instead. This raises every font-size below the floor and then
REPORTS what that broke, because the raise is the easy half — tools/svg-text-size-check.py
records a simulated 12u->14u bump putting 31 stacked pairs into em-box contact and 7
labels into real overlap, and this jump is larger.

It edits partials/pages/** (the source), never the built page.

CANNOT SEE: whether the re-laid drawing still READS — that it says the same thing in the
same order. Only a person looking at it can say that.
"""
import argparse, re, sys, os, math

def art_svgs(html, art_id=None):
    for m in re.finditer(r'<svg[^>]*class="[^"]*art-svg[^"]*"[^>]*>.*?</svg>', html, re.S):
        if art_id:
            i = re.search(r'id="([^"]+)"', m.group(0))
            if not i or i.group(1) != art_id:
                continue
        yield m

def raise_sizes(svg, floor_u):
    """Every font-size below floor_u becomes floor_u. Returns (new_svg, changes).

    TWO SPELLINGS. Most of these drawings size their type with a font-size ATTRIBUTE,
    but /process states it in a CSS rule inside the svg's own <style> block
    (font-size:13px). Handling only the attribute raised 0 of 20 labels there and
    reported success, which is the silent no-op the execution notes warn about.
    """
    changes = []

    def attr(m):
        try: v = float(m.group(1))
        except ValueError: return m.group(0)
        if v < floor_u:
            changes.append((v, floor_u))
            return f'font-size="{floor_u:g}"'
        return m.group(0)

    def css(m):
        try: v = float(m.group(1))
        except ValueError: return m.group(0)
        if v < floor_u:
            changes.append((v, floor_u))
            return f'font-size:{floor_u:g}px'
        return m.group(0)

    svg = re.sub(r'font-size="([^"]+)"', attr, svg)
    svg = re.sub(r'font-size:\s*([0-9.]+)px', css, svg)
    return svg, changes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('partial')
    ap.add_argument('--floor-units', type=float, required=True,
                    help='minimum user units (rendered px / scale)')
    ap.add_argument('--art-id')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()

    html = open(a.partial).read()
    hits = list(art_svgs(html, a.art_id))
    if not hits:
        print(f'no art-svg in {a.partial}' + (f' with id {a.art_id}' if a.art_id else ''))
        return 1
    out, total = html, 0
    for m in reversed(hits):                    # reversed: earlier spans stay valid
        new, ch = raise_sizes(m.group(0), a.floor_units)
        total += len(ch)
        if ch:
            from collections import Counter
            c = Counter(f'{o:g}u -> {n:g}u' for o, n in ch)
            for k, n in sorted(c.items()):
                print(f'  {n:3d} x  {k}')
        out = out[:m.start()] + new + out[m.end():]
    print(f'{total} label(s) raised in {a.partial}')
    if a.apply and total:
        open(a.partial, 'w').write(out)
        print('WRITTEN — rebuild with tools/build-pages.py')
    elif total:
        print('(dry run — pass --apply)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
