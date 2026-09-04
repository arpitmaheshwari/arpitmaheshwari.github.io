#!/usr/bin/env python3
"""run-gates.py — the one runner both the hook and CI use.

    python3 tools/run-gates.py --stage pre-push
    python3 tools/run-gates.py --stage ci
    python3 tools/run-gates.py --audit          # is the manifest honest?
    python3 tools/run-gates.py --list

WHY. There used to be two hand-maintained lists of gates: one in .githooks/pre-push,
one spread across .github/workflows/. Nothing required them to agree, and they did not
— the hook ran asset-load-check against two URLs while CI ran it against every page.
The result was a Contrast gate that failed on thirty consecutive pushes while every
local run said OK, because local was not running the check that was failing.

Divergence is still permitted: a seven-minute sweep does not belong on every push. What
is no longer permitted is UNDECLARED divergence. tools/gates.json names the stages each
gate runs in, --audit fails when a check exists that the manifest does not list, and a
pre-push run PRINTS the ci-only gates it is skipping so nobody mistakes a green hook for
a green build.

One server is started for every gate that needs one, not one per gate. Under GitHub
Actions each failure is emitted as a ::error:: annotation, because job logs need admin
rights to read and an unreadable failure is how the last one hid for five days.

Exit 0 all passed · 1 a gate failed · 2 could not run.
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'tools', 'gates.json')
IN_CI = bool(os.environ.get('GITHUB_ACTIONS'))


def load():
    with open(MANIFEST, encoding='utf-8') as fh:
        return json.load(fh)


def annotate(title, output):
    """Emit a failure as a check annotation — the only channel readable without admin."""
    if not IN_CI:
        return
    tail = output.splitlines()[-25:]
    body = '%0A'.join(l.replace('%', '%25').replace('\r', '') for l in tail)
    print(f'::error title={title}::{body or "(no output captured)"}')


def wait_for(base, tries=60, pause=0.25):
    # A refused connection returns INSTANTLY, so a bare retry loop burns all its
    # attempts in under a second and reports "could not start a server" while the
    # server is still binding. Sleep between tries.
    for _ in range(tries):
        try:
            urllib.request.urlopen(base + '/', timeout=2).read(1)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(pause)
    return False


def start_server(port):
    """One server for every gate that needs one."""
    base = f'http://localhost:{port}'
    try:
        urllib.request.urlopen(base + '/', timeout=2).read(1)
        print(f'  reusing the server already on :{port}')
        return base, None
    except (urllib.error.URLError, OSError):
        pass
    proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(port),
                             '--directory', ROOT],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait_for(base):
        proc.terminate()
        return None, None
    return base, proc


def selected(data, stage):
    out = []
    for g in data['gates']:
        stages = g.get('stages') or []
        if not stages:
            continue
        if stage not in stages:
            continue
        # runner:false gates are declared here but executed by .githooks/pre-push's own
        # parallel orchestration. Running them here too would double every Chrome sweep.
        # In CI there is no other orchestrator, so the runner owns them.
        if stage == 'pre-push' and g.get('runner') is False:
            continue
        out.append(g)
    return out


def audit(data):
    """Every check in tools/ must appear in the manifest, and every gate must run somewhere."""
    listed = {g['id'] for g in data['gates']} | {g['id'] for g in data.get('manual', [])}
    scripts = {' '.join(g['cmd']) for g in data['gates']}
    scripts |= {' '.join(g['cmd']) for g in data.get('manual', [])}
    problems = []

    for g in data['gates']:
        if not g.get('stages'):
            problems.append(f"{g['id']} runs in no stage and gives no manual_reason")
        script = g['cmd'][1] if len(g['cmd']) > 1 else ''
        if script.startswith('tools/') and not os.path.exists(os.path.join(ROOT, script)):
            problems.append(f"{g['id']} points at {script}, which does not exist")
    for g in data.get('manual', []):
        if not g.get('manual_reason'):
            problems.append(f"{g['id']} is manual with no stated reason")

    # A gate can be declared for pre-push and executed by the hook instead of by this
    # runner. Prove the hook really invokes it — otherwise "declared" and "run" drift
    # apart again, which is the whole failure this manifest exists to prevent.
    hook_path = os.path.join(ROOT, '.githooks', 'pre-push')
    hook_src = open(hook_path, encoding='utf-8').read() if os.path.exists(hook_path) else ''
    for g in data['gates']:
        if g.get('runner') is False and 'pre-push' in (g.get('stages') or []):
            script = g['cmd'][1] if len(g['cmd']) > 1 else ''
            if script and script not in hook_src:
                problems.append(f"{g['id']} is declared pre-push with runner:false, but "
                                f".githooks/pre-push never invokes {script}")

    pattern = os.path.join(ROOT, 'tools', '*.py')
    suffixes = ('-check.py', '-sweep.py', '-audit.py', '-lint.py')
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)
        if not name.endswith(suffixes):
            continue
        if not any(f'tools/{name}' in s for s in scripts):
            problems.append(f'tools/{name} is a check that gates.json does not list')

    for p in problems:
        print(f'  {p}')
    if problems:
        print(f'\n{len(problems)} manifest problem(s). A gate the manifest forgets is a '
              f'gate nobody runs.')
        return 1
    print(f'{len(listed)} gate(s) declared, every check in tools/ accounted for.')
    print('CANNOT SEE: whether a gate actually checks what its id claims, or whether the')
    print('stage it declares is the right one for its cost.')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['pre-push', 'ci', 'ci-always', 'nightly'])
    ap.add_argument('--audit', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--only', help='comma-separated gate ids to run instead of the whole stage')
    ap.add_argument('--parallel', type=int, default=4,
                    help='gates to run at once (they are independent); 1 to serialise')
    a = ap.parse_args()

    data = load()

    if a.audit:
        sys.exit(audit(data))

    if a.list:
        for g in data['gates']:
            print(f"  {g['id']:28} {'+'.join(g.get('stages', [])):16} "
                  f"{'server' if 'server' in (g.get('needs') or []) else ''}")
        for g in data.get('manual', []):
            print(f"  {g['id']:28} {'manual':16} {g['manual_reason'][:60]}")
        sys.exit(0)

    if not a.stage:
        ap.error('--stage is required unless --audit or --list')

    gates = selected(data, a.stage)
    if a.only:
        want = {x.strip() for x in a.only.split(',') if x.strip()}
        gates = [g for g in gates if g['id'] in want]
        if not gates:
            print(f'  no gate with id {a.only} in stage {a.stage}')
            sys.exit(2)

    # Say out loud what this stage is NOT checking. A green hook must never be mistaken
    # for a green build.
    if a.stage == 'pre-push':
        elsewhere = [g['id'] for g in data['gates']
                     if 'ci' in (g.get('stages') or []) and 'pre-push' not in (g.get('stages') or [])]
        if elsewhere:
            print(f'  {len(elsewhere)} gate(s) run in CI only and are NOT checked here: '
                  f'{", ".join(elsewhere)}')

    base, proc = None, None
    if any('server' in (g.get('needs') or []) for g in gates):
        base, proc = start_server(a.port)
        if base is None:
            print('  UNMEASURED  could not start a server. This is not a pass.')
            sys.exit(2)

    def run_one(g):
        cmd = [base if c == '{BASE}' else c.replace('{BASE}', base or '') for c in g['cmd']]
        # A gate that takes page URLs gets them from gatelib, the single definition of
        # "a shipped page" — not from a hand-typed list that goes stale. include_book
        # is false where a gate asserts something the book deliberately does not have:
        # it carries no shared nav or footer, so a landmark rule fails it by design.
        pages_opt = g.get('pages')
        if pages_opt:
            sys.path.insert(0, os.path.join(ROOT, 'tools'))
            from gatelib import page_urls
            kw = {} if pages_opt is True else dict(pages_opt)
            cmd = cmd + page_urls(base or 'http://localhost:8000', **kw)
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        return g, r.returncode, (r.stdout or '') + (r.stderr or '')

    failed = []
    try:
        # SERIAL GATES RUN ALONE. A gate driving Chrome with --dump-dom and
        # --virtual-time-budget is not safe to run beside another one: virtual time
        # advances only while the page is idle, so several Chromes on a 2-core runner
        # let the budget expire mid-render and --dump-dom returns a half-styled DOM.
        # That is what made theme-remnant-check and cta-grammar-check fail only in CI —
        # both pass alone on the same runner. Contention I introduced with --parallel 4.
        serial_gates = [g for g in gates if g.get('serial')]
        parallel_gates = [g for g in gates if not g.get('serial')]
        total = len(gates)          # count BEFORE splitting: the summary reports how many
                                    # gates RAN, and reassigning `gates` here made it say
                                    # "all 1 gate(s) passed" after running three.
        if serial_gates:
            print(f'  {len(serial_gates)} gate(s) run alone (virtual-time drivers): '
                  f'{", ".join(g["id"] for g in serial_gates)}')
        if a.parallel > 1 and len(parallel_gates) > 1:
            # The heavy gates each boot their own Chrome and re-render the same pages;
            # serially that was ~20 minutes of doing identical work several times over.
            # They are independent, so overlap the waiting. Output is still printed
            # per-gate and in manifest order, so a log reads the same either way.
            with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex:
                results = list(ex.map(run_one, parallel_gates))
        else:
            results = [run_one(g) for g in parallel_gates]
        results = results + [run_one(g) for g in serial_gates]
        for g, code, out in results:
            print(f"\n=== {g['id']}")
            print(out.rstrip())
            if code != 0:
                failed.append(g['id'])
                annotate(f"{g['id']} failed", out)
    finally:
        if proc:
            proc.terminate()

    print()
    if failed:
        print(f'{len(failed)} of {total} gate(s) failed: {", ".join(failed)}')
        sys.exit(1)
    print(f'all {total} gate(s) passed in stage {a.stage}')
    sys.exit(0)


if __name__ == '__main__':
    main()
