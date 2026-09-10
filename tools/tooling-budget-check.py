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
# closed-state-cover, css-coverage, inline-style, jsonld,
# link-integrity, social-title, wcag-reflow). Folding those into gatelib is the
# repayment, and it retires this bug class rather than fixing it a fifth time.
# 2026-09-08: 11_840 -> 12_100. What the 273 lines bought (251 of gate, the rest
# this note): baseline-align-check,
# a defect CLASS no gate in this repo could see. Arpit selected the homepage act
# numeral and said "these numerals don't feel align to the corresponding text";
# its baseline sat 6.0px above the act title's at 1440 and 7.0px at 768 and 390,
# in all four acts, and every gate passed — .chap used align-items:start, so the two
# boxes had identical tops (1141.0 and 1141.0). Contrast, overflow, spacing,
# reflow, leading, heading-rank and a11y each ask about ONE element's own
# properties or its place inside its own container; not one compares two
# siblings to each other. receipt-align-check is the only relative check in the
# repo and it tests LEFT edges of one component on six case pages.
# Not folded into receipt-align-check: different axis (baselines vs left edges),
# different scope (every grid/flex row on 59 pages vs .rcpt-r on six), and that
# gate is 54 lines running nightly — folding would have saved nothing and made
# one gate answer two unrelated questions.
# The ratio moved 1.74x -> 1.76x — tooling grew against the site it governs,
# which is the cost this ceiling exists to make visible.
# OUTSTANDING DEBT unchanged: nine gates still discover pages themselves
# (ci-claim, closed-state-cover, css-coverage, inline-style, jsonld,
# link-integrity, social-title, wcag-reflow) — eight now, not nine:
# freshness-stamp was DELETED on 2026-09-09, not fixed. Arpit: "Remove the
# stamp, that no value, it's an additional task for you to do." The cheapest
# repayment on a gate is the one you retire. Folding the rest into gatelib
# is the repayment, and it retires that bug class rather than fixing it a fifth
# time.
# 2026-09-08 (2): 12_100 -> 12_110. Ten lines: inline-style-check now strips
# /* ... */ before scanning for off-grid spacing. Its value regex read a
# comment opening "no stacking margin: the footer is..." as a declaration and
# harvested a px figure out of the prose, reporting a spacing value that no
# rule contains. Every stylesheet here is mostly prose, so that false positive
# was going to recur on every explanation written from now on.
# 2026-09-09: 12_110 -> 12_030. The ceiling comes DOWN for once: freshness-stamp.py
# deleted (Arpit asked for the footer ship stamp gone — no reader value, and it cost
# a re-stamp of 38 pages on every push) and build-partials lost the freshness()
# function with it. A ceiling that only ever rises is a budget nobody keeps.
# 2026-09-09 (2): 12_030 -> 12060. What the lines bought: interaction-state-check
# stopped failing on a control it cannot measure. It reported the nav toggle at
# 1.25:1 on hover and focus across 41 pages — 82 findings — by grading a
# text-less button's default black `color`. Pixels inside that control in that
# state: 8.12:1. The toggle's glyph is three gradient-filled child spans, and the
# gate's existing gradient flag only tested the element itself.
# 2026-09-09  +187  grid-containment-check.py. Arpit selected a homepage line and
# asked "why is this line jumping off the grid and why couldn't you catch it". No gate
# here compares one element to ANOTHER, so a paragraph sitting outside its column was
# invisible to all 46. It buys the comparison class of check: prose outside its own
# section siblings' envelope on BOTH sides. Three premises failed on the way (a .wrap
# every section has; a section's modal left edge; a 90%-of-viewport width test that was
# only ever measured at 1440 and produced 53 findings all reading exactly 92% at 390) —
# 106 of those lines are that reasoning written down, so premise 4 is not attempted by
# the next person from scratch.
# 2026-09-10  +170  css-structure-check.py. One orphan `}` closed @layer base
# 161KB early, un-layering the bulk of ember.css and inverting the cascade for the
# whole site; the only symptom any gate saw was one h2 at 44px instead of 42. This
# buys a structural check on the TEXT — braces balance, @layer spans hold their
# share — at pre-commit, because it needs no browser and takes 0.2s. The lines are
# mostly the account of how the brace got there: a cut to "the next closing brace".
# 2026-09-10  +228  nontext-contrast-check.py (MANUAL). Arpit asked how the CTAs
# were passing accessibility. They were not: the text passed, the button's boundary
# sat at 2.84:1 against a 3:1 requirement, and no gate here had ever measured a
# control's EDGE rather than its text. Manual rather than pre-push because scoped to
# actions it still reports 153 controls — the site's --border token is 1.41:1 — and
# that is a design decision, not a push blocker. Half the lines are the record of
# five screenshot-sampling faults, so the next person computes from resolved colours.
# 2026-09-10  +8  not a new gate: the retargeting notes in cta-viewport-check and
# component-identity-check. Both were pointed at classes deleted that morning —
# cta-viewport planted its calibration on .pill and refused to report (correctly),
# and component-identity printed "0 inconsistent" while SIX of its nine names no
# longer existed. Eight lines record which names were dead and the page counts that
# proved it, so the next person retargets from evidence instead of re-deriving it.
# They also earned their keep on the spot: pointed at live classes, component-identity
# found an unclosed <strong> that had swallowed the footer on two writing pages.
# 2026-09-10  +28  css-version-check, and not a new gate: two defects in the one
# that already existed. Its calibration was a TAUTOLOGY —
#   caught = probe["version"] == probe["version"] and probe["hash"] != "deadbeef…"
# compares a value with itself, so it printed PASS on every run since 2026-08-15
# without ever exercising the rule, while its docstring claimed it "requires the
# check to fail". And version_of() read THREE hardcoded pages of the 41 that link
# styles.css, returning the first hit — so pages drifting onto different versions,
# the exact failure bump-css-version.py records from the wild, was invisible. The
# rule now lives at module level so the calibration provably exercises the same
# code, and page disagreement is a finding. Verified by planting ?v=deadbeef on
# one page and watching it name that page.
# 2026-09-10  +48  css-version-check gains the check it never had: a page's ?v=
# must equal sha256(file)[:8]. Its manifest rule LAUNDERS that failure — it
# re-records {version: page's OLD version, hash: file's CURRENT hash} on every
# non-stale run, after which prev.hash == file.hash for ever and the sheet reads
# clean. It reported "0 served stale" while index.html asked for styles.css
# ?v=149ac7d3 against a file hashing to 3a6ed7ac, and the hook's own partials
# check blocked the push over exactly that. The new rule needs no state, so it
# cannot be laundered, and it covers JS as well as CSS.
# 2026-09-10  +22  runtime-error-check and interaction-state-check now default
# --base to $BASE and start a server if none is up. NOT the correctness bug I
# reported to Arpit: the hook already passes --base explicitly, so both were
# always right under the hook, and both exit 3 saying "nothing was measured"
# rather than faking a pass. The real gap was that the eight hook-only gates
# could not simply be run by hand before a push — the step whose absence cost
# two blocked pushes today. Now they can.
# 2026-09-10  +14  QuietServer in cdp.ensure_server and devserver.py. Chrome hangs
# up as soon as it has what it needs, so socketserver dumped a 20-line
# BrokenPipeError traceback from copyfile() into the middle of a gate's output —
# and a traceback in a gate that then exits 0 is how people learn to distrust
# green. Silences CLIENT DISCONNECTS ONLY: calibrated by raising a genuine
# RuntimeError through the same handler and confirming it still prints. A blanket
# except would hide a real server bug, which is the same defect as a check that
# cannot go red.
# 2026-09-10  +18  runtime-error-check now reports WHERE an exception was thrown.
# It kept only the first line of the description, so a push blocked on
# "ReferenceError: nothing is not defined" in book/index.html with no url, no line
# and no stack — an identifier that appears in NO served file and did not reproduce
# in six clean loads or three 44-page sweeps. Nothing left to chase. Now it prints
# url:line:col and the function, which on a reproduction of the same message
# resolved to "(inline):0:21 in boomHere()" — i.e. it tells you the throw came from
# an INLINE script, which is exactly the fact that was missing.
# 2026-09-10  +50  the exit-code convention, made real in two places. Gates already
# used 1/2/3 to mean defect / calibration-failed / could-not-measure, and BOTH
# run-gates.py and contrast-audit.py documented that distinction while collapsing it
# in code: run-gates did `if code != 0: failed.append(...)`, and contrast-audit
# returned 2 for "could not measure" as well as for a failed calibration. That is how
# a push came to be blocked with "1 of 27 gate(s) failed: contrast-audit" when two
# pages had simply never loaded. Both now discriminate, and the runner was calibrated
# with three planted gates, one per code.
# 2026-09-10  +160  contrast-algebra-test.py (152) and audit()'s named outcomes.
# The algebra was the only part of contrast-audit with no test: four constants set
# after incidents, verified only by four canaries needing a browser, a server and
# 12MB of screenshots to check three lines of arithmetic. These construct the frames
# instead, run in milliseconds, and are calibrated by perturbation — dropping
# ALPHA_FLOOR to .3 or removing the 1/alpha division each turns them red. Includes a
# standing regression for the exact false failure (#1A0D08 on #F67E99, 7.57:1,
# reported as 2.49:1). audit() now names its four failure modes instead of returning
# None for all of them, so 'bad-camera' can exit 2 while a dead server exits 3.
CEILING = 13_264


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
