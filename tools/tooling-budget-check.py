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
#   2026-09-05  11,400  TEMPORARY, and it owes a repayment. runner-diagnose.py and
#                       alpha-probe.py are DIAGNOSTICS, not gates: they grade nothing and
#                       block nothing, and they exist to answer one open question — why the
#                       Linux runner reports ten contrast failures whose authored pairs
#                       measure 6.4:1 to 10.7:1. When that is answered BOTH FILES ARE
#                       DELETED and this comes back to 11,000. If you are reading this and
#                       the question is closed, the deletion is overdue.
#   2026-09-07  11,800  section-nav-check.py (144 lines), plus ~30 lines of instrument
#                       repairs it forced (see below). It measures two properties every
#                       other gate here is structurally blind to, because all of them grade
#                       ONE element's own attributes: that no two headings on a page say the
#                       same thing, and that every section carrying its own h2 is reachable
#                       from the page's own jump nav. Its first run found a duplicated h2 on
#                       /case-studies/o2 (the §01 stakes heading printed again over §04) and
#                       six sections across five case studies that the page's own table of
#                       contents did not list. Six defects on a site that was green on
#                       contrast, heading-rank, leading, reflow, target-size and a11y.
#                       The repairs: contrast-audit's reveal canary was hiding itself with
#                       the SITE's `.reveal{opacity:0}` rule, so deleting that rule on
#                       2026-09-07 left the canary visible from the start and the
#                       calibration proving nothing while still reporting PASS — it now
#                       carries its own hiding. And bump-css-version's fallback returned
#                       `stem[0] + "1"` for any sheet not on a numeric version, so two
#                       hash-versioned bumps in a row would both have produced `s1`: a
#                       REPEATED cache key, which is the one failure that script exists to
#                       prevent. It uses the content hash now.
# 2026-09-08: 11_800 -> 11_840. What the 40 lines bought: heading-rank-check now
# takes its page set from gatelib instead of a private list, so it no longer
# navigates folio/index.html (a script redirect stub), read the HOMEPAGE's DOM
# mid-handover and reported the same six headings twice against a 1.5KB file —
# the FOURTH gate to hit that bug. Plus the case-board heading ranks, registered
# by component so 15/600 stays illegal everywhere else. The ratio went DOWN
# (1.83x -> 1.82x): tooling did not grow relative to the site it governs.
# OUTSTANDING DEBT: nine gates still discover pages themselves (ci-claim,
# closed-state-cover, css-coverage, freshness-stamp, inline-style, jsonld,
# link-integrity, social-title, wcag-reflow). Folding those into gatelib is the
# repayment, and it retires this bug class rather than fixing it a fifth time.
CEILING = 11_840


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
