#!/usr/bin/env python3
"""tooling-budget-check.py — is the checking bigger than the thing it checks?

From the architecture review, 2026-09-04: tools/ held 10,090 lines against 5,459 lines of
site CSS. The apparatus that checks the site had grown to roughly 1.8x the size of the
site, and every line of it is a line someone maintains, a line that can be wrong, and a
line that competes with writing and outreach for the same evening.

Fix 04 was written as "a rule, not a task": before adding a gate, retire one. A rule
nobody enforces is a wish, so this is the enforcement — and it is deliberately a CEILING,
not a ratchet. It does not care that the number goes up; it cares that it goes up without
anyone deciding to let it.

Raising CEILING is the whole point: it is a one-line commit that makes the trade explicit
and puts it in the history next to what was bought with it.

Exit 0 under budget · 1 over.
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Raised deliberately, with the reason. Never edit this to make a red build go green
# without saying what the new lines bought.
#   2026-09-04  11,000  the architecture review's own fixes: gatelib, run-gates, the
#                       manifest runner, ci-deps/ci-claim/jsonld/social-title/
#                       image-dimension/orphan-asset checks, and this file.
CEILING = 11_000


def loc(paths):
    n = 0
    for p in paths:
        try:
            with open(p, encoding='utf-8', errors='replace') as fh:
                n += sum(1 for _ in fh)
        except OSError:
            pass
    return n


tool_files = sorted(glob.glob(os.path.join(ROOT, 'tools', '*.py')))
tools_loc = loc(tool_files)
site_loc = loc([os.path.join(ROOT, f) for f in ('styles.css', 'ember.css', 'fonts.css')])

print(f'  tools/   {tools_loc:>6,} lines across {len(tool_files)} files')
print(f'  site CSS {site_loc:>6,} lines')
print(f'  ratio    {tools_loc / site_loc:.2f}x   ceiling {CEILING:,}')

if tools_loc > CEILING:
    over = tools_loc - CEILING
    print(f'\n  tools/ is {over:,} line(s) over the declared ceiling of {CEILING:,}.')
    print('  Retire a gate, fold one into another, or raise CEILING in this file and say')
    print('  in the commit what the extra lines bought. Do not raise it silently.')
    sys.exit(1)
print(f'\n{CEILING - tools_loc:,} lines of headroom.')
print('CANNOT SEE: whether the lines are any good, whether two gates check the same thing,')
print('or whether a gate that exists is one anybody runs.')
