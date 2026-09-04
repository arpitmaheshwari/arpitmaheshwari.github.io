#!/usr/bin/env python3
"""ci-status-check.py — is CI actually green?

The Contrast gate failed on EVERY push from at least 2026-08-30 to 2026-09-03 and
nobody knew, because the local pre-push hook said OK every time. It was running a
different command: two URLs where CI ran --all over 41 pages. Local green said
nothing about CI, and no one was looking at CI.

So this asks GitHub directly. Needs the network, so it is NOT in pre-push — run it
after a push, or whenever "the gates pass" is about to be said out loud.

    python3 tools/ci-status-check.py            # latest run per workflow
    python3 tools/ci-status-check.py --sha HEAD # the runs for one commit

Exit 0 all green · 1 something failed · 2 could not measure (offline, API limit).
"""
import argparse, json, subprocess, sys, urllib.error, urllib.request

REPO = 'arpitmaheshwari/arpitmaheshwari.github.io'
API = f'https://api.github.com/repos/{REPO}/actions/runs?per_page=40'

ap = argparse.ArgumentParser()
ap.add_argument('--sha', help='only runs for this commit (accepts HEAD)')
a = ap.parse_args()

sha = a.sha
if sha:
    sha = subprocess.run(['git', 'rev-parse', sha], capture_output=True,
                         text=True).stdout.strip() or sha

try:
    req = urllib.request.Request(API, headers={'Accept': 'application/vnd.github+json',
                                               'User-Agent': 'ci-status-check'})
    with urllib.request.urlopen(req, timeout=25) as r:
        runs = json.load(r).get('workflow_runs', [])
except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
    print(f'  UNMEASURED  {e}\n\nCould not reach the Actions API. This is not a pass.')
    sys.exit(2)

if not runs:
    print('  UNMEASURED  the API returned no runs.\n\nThis is not a pass.')
    sys.exit(2)

seen, rows = set(), []
for run in runs:
    if sha:
        if run['head_sha'] != sha:
            continue
    elif run['name'] in seen:
        continue
    seen.add(run['name'])
    rows.append((run['name'], run['conclusion'] or run['status'],
                 run['head_sha'][:7], run['created_at'][:16], run['html_url']))

if not rows:
    print(f'  UNMEASURED  no runs found for {sha[:7] if sha else "HEAD"}.')
    sys.exit(2)

# STILL RUNNING IS NOT FAILED. The first version printed FAIL for a run whose status
# was in_progress, because it tested `conclusion != 'success'` and an unfinished run has
# no conclusion at all. That is the exact defect this whole audit has been chasing — a
# true reading (not success) under a label claiming more (failed) — produced by my own
# instrument, twice in one day.
RUNNING = {'in_progress', 'queued', 'waiting', 'requested', 'pending'}
bad = [r for r in rows if r[1] != 'success' and r[1] not in RUNNING]
running = [r for r in rows if r[1] in RUNNING]
for name, concl, s, when, url in sorted(rows):
    mark = 'ok  ' if concl == 'success' else ('.. ' if concl in RUNNING else 'FAIL')
    print(f'  {mark} {name:24} {s}  {when}')
    if concl != 'success':
        print(f'       {concl} — {url}')
if bad:
    print(f'\n{len(bad)} of {len(rows)} workflow(s) not green. '
          f'A red gate nobody reads is not a gate.')
    sys.exit(1)
if running:
    print(f'\n{len(running)} workflow(s) still running — no verdict yet. Not a pass.')
    sys.exit(2)
print(f'\nAll {len(rows)} workflow(s) green.')
print('CANNOT SEE: a gate that passes for the wrong reason, a step that silently')
print('skipped itself, or a workflow whose paths: filter meant it never ran at all.')
