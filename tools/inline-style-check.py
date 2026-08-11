#!/usr/bin/env python3
"""
inline-style-check — fail when a type treatment is duplicated inline instead of named.

WHY (2026-08-02): the site accumulated 2,095 inline style attributes, 562 of whose type
declarations were exact duplicates of each other. Every duplicate is an independent fork, and
several had silently drifted: two identically-classed <dl>s rendering differently, one mono
label spelled 16 ways, a <th> bold only because that is the browser default. The correctness
gates (canon-lint, contrast-audit, case-sync, asset-load) all passed the whole time — they
check whether a page is RIGHT, never whether it is STRUCTURED. This gate closes that gap.

WHAT IT CHECKS: for each HTML file, extract the type declarations (font-*, letter-spacing,
text-transform, color, line-height) from every inline style attribute. If the same combination
appears >= THRESHOLD times across the site, it is a component that should be a class in
styles.css, and this fails.

CALIBRATION: plants a duplicated signature and confirms it is caught; then confirms the
untouched tree reports nothing above threshold. A check that cannot fail is not evidence.

USAGE:  python3 tools/inline-style-check.py --root .
        python3 tools/inline-style-check.py --root . --threshold 4
EXIT:   0 = clean and calibrated · 1 = duplicates found, or calibration did not go red.
"""
import argparse, collections, glob, os, re, sys

TYPE = ['font-family','font-size','font-weight','font-style','letter-spacing',
        'text-transform','color','line-height']
# Layout duplication is the same disease: 263 elements repeated the receipt row, the button and
# the card inline before they were extracted (2026-08-02). A layout signature needs 3+ properties
# to count as a component — two properties is usually a genuine one-off nudge.
LAYOUT = ['display','flex','flex-wrap','flex-direction','align-items','justify-content','gap',
          'grid-template-columns','margin','margin-top','margin-bottom','margin-left',
          'margin-right','padding','border','border-radius','border-top','border-bottom',
          'border-left','max-width','width']
DEFAULT_THRESHOLD = 4


SPACE_SCALE = {4,8,12,16,20,24,32,40,48,64,80}
SPACE_PROPS = r'(?:margin|padding|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left))?'

def off_scale_spacing(root):
    """Spacing values that are neither on the 4px grid nor a documented exception.
    Exceptions, by design: <4px optical nudges, >80px structural values (the nav clearance
    DESIGN-SYSTEM requires at >=104px, hero bands), 0, and non-px units."""
    # The BOOK is a separate visual system but shares the px grid — one grid across every
    # surface is a stronger property than two locally-optimal ones. The PRINT documents use mm
    # and get their own 0.5mm grid (see below).
    pats = ['*.html','*/index.html','case-studies/*.html','patterns/*.html','lab/*.html',
            'assets/og-images/*.html',
            'styles.css','book/book.css','book/index.html']
    # contrast-audit.py writes its canary page to a temp file INSIDE the docroot (it must be
    # same-origin to be instrumentable), named __ca_*.html. Running the two gates concurrently
    # made this gate read the OTHER gate's scratch file and report a phantom 6px off-grid
    # value — a failure in code that does not exist. Measured 2026-08-08, not assumed.
    files = sorted({p for pat in pats for p in glob.glob(os.path.join(root, pat))
                    if not os.path.basename(p).startswith('__ca_')})
    bad = collections.Counter(); where = collections.defaultdict(set)
    for f in files:
        s = open(f, encoding='utf-8').read()
        for m in re.finditer(SPACE_PROPS + r'\s*:\s*([^;"}]+)', s):
            for tok in re.findall(r'(?<![\w.-])(\d+)px', m.group(1)):
                v = int(tok)
                if v == 0 or v < 4 or v > 80 or v in SPACE_SCALE: continue
                bad[v] += 1; where[v].add(os.path.relpath(f, root))
    # book/portfolio.js — React style objects, unitless numbers
    jsf = os.path.join(root, 'book', 'portfolio.js')
    if os.path.exists(jsf):
        s = open(jsf, encoding='utf-8').read()
        for m in re.finditer(r'(?:margin|marginTop|marginBottom|marginLeft|marginRight|padding'
                             r'|paddingTop|paddingBottom|gap)\s*:\s*(\d+)', s):
            v = int(m.group(1))
            if v == 0 or v < 4 or v > 80 or v in SPACE_SCALE: continue
            bad[v] += 1; where[v].add('book/portfolio.js')
    # print documents — 0.5mm grid; <1mm are hairlines and exempt
    for f in sorted(glob.glob(os.path.join(root, 'portfolio-sources', '*.html'))):
        s = open(f, encoding='utf-8').read()
        for m in re.finditer(SPACE_PROPS + r'\s*:\s*([^;"}]+)', s):
            for tok in re.findall(r'(?<![\w.-])([\d.]+)mm', m.group(1)):
                v = float(tok)
                if v < 1.0 or abs(v*2 - round(v*2)) < 1e-9: continue
                bad[f'{v:g}mm'] += 1; where[f'{v:g}mm'].add(os.path.relpath(f, root))
    return bad, where

def signatures(root):
    # portfolio-sources/ is a SEPARATE private repo checked out inside this one. Its print
    # documents carry the same debt, so they are scanned when present and skipped when not.
    pats = ['*.html','*/index.html','case-studies/*.html','patterns/*.html','lab/*.html',
            'assets/og-images/*.html',
            'portfolio-sources/*.html']
    files = sorted({p for pat in pats for p in glob.glob(os.path.join(root, pat))})
    sig = collections.Counter(); where = collections.defaultdict(set)
    for f in files:
        s = open(f, encoding='utf-8').read()
        for m in re.finditer(r'style="([^"]*)"', s):
            d = m.group(1); props = []
            for p in TYPE:
                mm = re.search(r'(?:^|;)\s*' + p + r'\s*:\s*([^;]+)', d)
                if mm: props.append(f'{p}:{mm.group(1).strip()}')
            if len(props) >= 2:
                k = 'TYPE ' + ';'.join(props); sig[k] += 1; where[k].add(os.path.relpath(f, root))
            lay = []
            for p in LAYOUT:
                mm = re.search(r'(?:^|;)\s*' + re.escape(p) + r'\s*:\s*([^;]+)', d)
                if mm: lay.append(f'{p}:{mm.group(1).strip()}')
            if len(lay) >= 3:
                k = 'LAYOUT ' + ';'.join(lay); sig[k] += 1; where[k].add(os.path.relpath(f, root))
    return sig, where, len(files)

def calibrate(root, threshold):
    sig, _, _ = signatures(root)
    over = [k for k, n in sig.items() if n >= threshold]
    if over:
        return False, (f'the untouched tree already has {len(over)} signature(s) at or above '
                       f'threshold — cannot separate a planted duplicate from existing noise')
    canary = os.path.join(root, '__isc_canary.html')
    dup = '<p style="font-family:var(--ff-mono);font-size:99px;color:rebeccapurple">x</p>'
    open(canary, 'w', encoding='utf-8').write('<html><body>' + dup * threshold + '</body></html>')
    try:
        sig2, _, _ = signatures(root)
        caught = any(n >= threshold and 'rebeccapurple' in k for k, n in sig2.items())
    finally:
        os.remove(canary)
    if not caught:
        return False, 'planted a duplicated signature and the check did not flag it'
    return True, 'sensitivity OK (planted duplicate caught) + precision OK (clean tree silent)'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--threshold', type=int, default=DEFAULT_THRESHOLD)
    ap.add_argument('--no-selftest', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if not a.no_selftest:
        ok, why = calibrate(root, a.threshold)
        print(f'[calibration] {"PASS" if ok else "FAIL"} — {why}\n')
        if not ok:
            print('Refusing to report results. A check that cannot fail is not evidence.')
            return 1

    sig, where, nfiles = signatures(root)
    over = sorted(((n, k) for k, n in sig.items() if n >= a.threshold), reverse=True)
    total = sum(sig.values())
    print(f'scanned {nfiles} HTML files · {total} inline signatures (type 2+ props, layout 3+ props)')
    bad, bwhere = off_scale_spacing(root)
    if not over and not bad:
        print('\nResult: clean — no duplicated component, no off-grid spacing.')
        print('NOT covered: single-use inline styles (fine), page <style> blocks, and whether a '
              'named class is used CONSISTENTLY (see tools/type-consistency-check.md for that).')
        return 0
    if bad:
        print(f'\n{sum(bad.values())} spacing value(s) off grid (px: 4·8·12·16·20·24·32·40·48·64·80 · print: 0.5mm steps):')
        for v, n in bad.most_common():
            unit = '' if isinstance(v, str) else 'px'
            print(f'  {n:4}×  {v}{unit}   in: {", ".join(sorted(bwhere[v])[:4])}')
        print('\nSnap to the nearest step. <4px optical nudges and >80px structural values are')
        print('already exempt — a value in between needs a reason.')
    if not over:
        print(f'\nResult: {sum(bad.values())} off-grid spacing value(s).')
        return 1
    print(f'\n{len(over)} type treatment(s) duplicated {a.threshold}+ times — each is an unnamed component:\n')
    for n, k in over:
        print(f'  {n:4}×  {k}')
        print(f'        in: {", ".join(sorted(where[k])[:5])}')
    print('\nFix: add the declarations as a class in styles.css and put the class on the elements.')
    print('A repeated component styled inline is a fork per instance — that is how the site ended')
    print('up with one mono label spelled 16 different ways.')
    print(f'\nResult: {len(over)} unnamed component(s).')
    return 1

if __name__ == '__main__':
    sys.exit(main())
