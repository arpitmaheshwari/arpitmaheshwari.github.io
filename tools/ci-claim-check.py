#!/usr/bin/env python3
"""ci-claim-check.py — does the site's "on every push" match the workflow triggers?

Four surfaces told the reader that contrast, overflow and legibility run "on every
push", and that the tests run "under Node in CI on every push". Neither is true:
contrast-gate.yml and test-lab.yml both carry a `paths:` filter, so a push that
touches neither the rendered site nor lab/ runs nothing. The teardown page had it
right — "on every push and pull request touching lab/" — so the site contradicted
itself, and the honest wording was the one on the page about honesty.

A claim about CI can only be checked against CI. This reads the workflows: any
workflow with a `paths:` filter is CONDITIONAL, and no page may then use the bare
phrase "on every push" / "on every change" without a qualifier right after it.

Exit 0 clean · 1 an unqualified claim · 2 could not measure.
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUALIFIERS = ('that touches', 'that changes', 'touching', 'to the rendered site',
              'and pull request touching')
CLAIMS = re.compile(r'on every (?:push|change)(?![a-z])', re.I)

wf = sorted(glob.glob(os.path.join(ROOT, '.github/workflows/*.yml')))
if not wf:
    print('  UNMEASURED no workflows found — cannot check a CI claim'); sys.exit(2)

conditional = [os.path.basename(w) for w in wf
               if re.search(r'^\s*paths:', open(w, encoding='utf-8').read(), re.M)]
print(f'  workflows: {len(wf)} · conditional (have a paths: filter): {conditional}')
if not conditional:
    print('  Every workflow runs unconditionally — "on every push" is fair.'); sys.exit(0)

bad = []
for f in sorted(glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True)):
    # Scratch files: gates plant temp .html into the docroot during their
    # calibration (__canon_canary_a.html, __al_*.html, __tr.html). If the
    # owning gate deletes one between this glob and the open, this gate dies
    # with FileNotFoundError mid-push — which is how image-dimension-check
    # broke a push on 2026-09-05. Every scratch name carries the __ prefix.
    if os.path.basename(f).startswith('__'):
        continue
    rel = os.path.relpath(f, ROOT)
    if rel.startswith(('prototypes/', 'portfolio-sources/', 'tests/', 'assets/', 'book/')):
        continue
    text = re.sub(r'<[^>]+>', ' ', open(f, encoding='utf-8').read())
    for m in CLAIMS.finditer(text):
        tail = text[m.end():m.end() + 60].lower()
        if not any(q in tail for q in QUALIFIERS):
            bad.append((rel, re.sub(r'\s+', ' ', text[max(0, m.start()-60):m.end()+40]).strip()))

for rel, ctx in bad:
    print(f'  UNQUALIFIED  {rel}\n               ...{ctx}...')
if bad:
    print(f'\n{len(bad)} unqualified CI claim(s), but {len(conditional)} workflow(s) are '
          f'path-filtered. Say which pushes.')
    sys.exit(1)
print('  No unqualified "on every push" claims. Wording matches the triggers.')
print('  CANNOT SEE: whether the paths: filter actually covers what the page implies,')
print('  or a workflow that is disabled, failing, or has no runner.')
