#!/usr/bin/env python3
"""lab-mirror-check.py — is "verbatim" still true?

lab/index.html tells the reader the public repo holds "the same files that run
here, MIT, verbatim". That is a claim about two artifacts being identical, and
nothing in the build compares them. It was true on 2026-09-03; it stops being
true the first time either copy is edited alone, silently and in whichever
direction is more embarrassing.

Needs the network, so this is NOT in pre-push — a gate that fails on a plane is
a gate people learn to skip. Run it when either copy changes:

    python3 tools/lab-mirror-check.py

Exit 0 identical · 1 drifted · 2 could not measure (offline, repo moved).
"""
import hashlib, os, sys, urllib.request, urllib.error

RAW = 'https://raw.githubusercontent.com/arpitmaheshwari/the-lab/main/'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ('loop.js', 'loop.test.js', 'trustlint.js')

def sha(b): return hashlib.sha256(b).hexdigest()

drift, unmeasurable = [], []
for name in FILES:
    local = os.path.join(ROOT, 'lab', name)
    if not os.path.exists(local):
        unmeasurable.append(f'{name}: no local copy at lab/{name}'); continue
    try:
        with urllib.request.urlopen(RAW + name, timeout=20) as r:
            remote = r.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        unmeasurable.append(f'{name}: {e}'); continue
    a, b = open(local, 'rb').read(), remote
    if sha(a) != sha(b):
        drift.append(f'{name}: local {len(a):,} bytes, public repo {len(b):,} bytes')

for d in drift:        print('  DRIFTED   ', d)
for u in unmeasurable: print('  UNMEASURED', u)

if drift:
    print(f'\n{len(drift)} file(s) differ from the public repo — lab/index.html says "verbatim".')
    sys.exit(1)
if unmeasurable:
    print('\nCould not compare. This is not a pass.')
    sys.exit(2)
print(f'{len(FILES)} files byte-identical to the public repo. "Verbatim" holds.')
print('CANNOT SEE: files that exist in one repo and not the other, or a repo rename.')
