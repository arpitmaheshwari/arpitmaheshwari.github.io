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
DEFAULT_THRESHOLD = 4

def signatures(root):
    # portfolio-sources/ is a SEPARATE private repo checked out inside this one. Its print
    # documents carry the same debt, so they are scanned when present and skipped when not.
    pats = ['*.html','*/index.html','case-studies/*.html','patterns/*.html','lab/*.html',
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
                k = ';'.join(props); sig[k] += 1; where[k].add(os.path.relpath(f, root))
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
    print(f'scanned {nfiles} HTML files · {total} inline styles carry 2+ type declarations')
    if not over:
        print(f'\nResult: clean — no type treatment is duplicated {a.threshold}+ times inline.')
        print('NOT covered: single-use inline styles (fine), page <style> blocks, and whether a '
              'named class is used CONSISTENTLY (see tools/type-consistency-check.md for that).')
        return 0
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
