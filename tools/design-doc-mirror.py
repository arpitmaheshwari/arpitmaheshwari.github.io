#!/usr/bin/env python3
"""design-doc-mirror.py — the design system is not in version control. Mirror it, and prove it matches.

WHY (2026-09-22). DESIGN-SYSTEM.md and DESIGN-SYSTEM-EMBER.md govern the classic site and hold the
measured reasoning behind every rule in it — the noise-overlay contrast correction, the 12.5px
rendered floor, the scale rule. On 2026-08-17 commit 50d2edea both removed them from the repo and
added them to .gitignore, correctly: this repo IS the public website and those files would have
been served. The side effect is that the design system existed as two untracked files on one
laptop, with no history and no backup.

They are mirrored into the PRIVATE folio-private repo (portfolio-sources/design-system/), which is
itself gitignored here, so nothing is published.

A MIRROR THAT DRIFTS IS WORSE THAN NO MIRROR. That is not hypothetical here: the Cream design
system's copy in prototypes/cream-system/ is a stale v1.0 import that has to be remembered as stale
every time anyone looks at it. So the copy is checked, not trusted:

    --check   (the gate) the mirror must be byte-identical to the source
    --sync    copy source -> mirror, for after an edit

SKIPS, rather than fails, when the private repo is not checked out — CI does not have it, the same
way canon-lint cannot see the PDFs that live there.

CANNOT SEE: whether the document is RIGHT, only whether the two copies agree. Nor whether the
mirror has been committed and pushed in the private repo — that is a separate repo's problem.
"""
import argparse, filecmp, os, shutil, sys

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(ROOT, 'portfolio-sources', 'design-system')
DOCS   = ('DESIGN-SYSTEM.md', 'DESIGN-SYSTEM-EMBER.md')

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check', action='store_true')
    g.add_argument('--sync', action='store_true')
    a = ap.parse_args()

    if not os.path.isdir(os.path.join(ROOT, 'portfolio-sources')):
        print('  portfolio-sources/ is not checked out here — nothing to mirror against.')
        print('CANNOT SEE: the private repo is absent, so this says nothing about the mirror.')
        return 0

    if a.sync:
        os.makedirs(MIRROR, exist_ok=True)

    drift, missing_src = [], []
    for d in DOCS:
        src = os.path.join(ROOT, d)
        dst = os.path.join(MIRROR, d)
        if not os.path.exists(src):
            missing_src.append(d)
            continue
        if a.sync:
            shutil.copy2(src, dst)
            print(f'  synced  {d}  ({os.path.getsize(src):,} bytes)')
            continue
        if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
            drift.append(d)

    if missing_src:
        print(f'  source missing: {", ".join(missing_src)}')

    if a.sync:
        print(f'{len(DOCS) - len(missing_src)} document(s) mirrored to portfolio-sources/design-system/')
        print('Commit them in that repo — it is a separate repo and this does not do that for you.')
        return 0

    for d in drift:
        print(f'  DRIFTED  {d}  — mirror does not match the source')
    print(f'\n{len(drift)} drifted document(s) of {len(DOCS) - len(missing_src)} mirrored.')
    if drift:
        print('Run: python3 tools/design-doc-mirror.py --sync   then commit in portfolio-sources/')
    print('CANNOT SEE: whether the document is RIGHT, only whether the two copies agree; nor '
          'whether the mirror has been committed and pushed in the private repo.')
    return 1 if drift else 0

if __name__ == '__main__':
    sys.exit(main())
