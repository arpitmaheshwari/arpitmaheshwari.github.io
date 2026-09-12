#!/usr/bin/env python3
"""qa-loop.py — run the whole quality system several times and report what is STABLE.

WHY (2026-09-13, Arpit: "create a loop of quality analysis … and test the entire system
multiple times"). One green run proves the site passed once. Gates that read a browser can
pass on a quiet machine and fail under load; a rebuild in flight can make a sweep photograph
a half-built stylesheet (see memory: sweep-during-rebuild-reads-intermediate-css). Only a
result that repeats is a result.

WHAT ONE ITERATION RUNS
  1. run-gates.py --stage pre-push     (39 gates: markup, links, CSS structure, contrast…)
  2. run-gates.py --stage nightly      (16 gates: overflow ×4, leading, reachability, overlap,
                                        keyboard, a11y, rhythm, paper objects, contrast…)
  3. the gates the runner declares but does not run (runner:false in gates.json) — asset
     load, runtime errors, interaction state, component identity, CTA viewport, artifact
     legibility, fit calibration, image alignment — invoked exactly as gates.json says
  4. journey-check.py                  (navigation, drawer, jump anchors, receipts, images
                                        painted, every internal link resolves)

GUARDS. Refuses to start while the CSS pipeline (css-consolidate / css-adopt-tokens /
css-components-pass) is running; refuses if the working tree changes between iterations
(a moving target makes "flaky" meaningless). Every gate keeps its own calibration.

REPORT. Per gate: PASS/FAIL per iteration, then STABLE PASS · STABLE FAIL · FLAKY. Written to
prototypes/qa-loop/<timestamp>/report.md (renders and logs beside it) and printed. Exit 0
when every gate is a stable pass, 1 when any is a stable fail, 2 when any is flaky and none
fails stably (an instrument problem to chase, not a site defect).
"""
import argparse, datetime, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE = re.compile(r'css-consolidate\.py|css-adopt-tokens\.py|css-components-pass\.py|components-pass\.py')


def sh(cmd, log, timeout=3600):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        out, code = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired:
        out, code = f'TIMEOUT after {timeout}s', 124
    open(log, 'w').write(out)
    return code, time.time() - t0, out


def pipeline_running():
    ps = subprocess.run(['ps', '-axo', 'command'], capture_output=True, text=True).stdout
    return [l for l in ps.splitlines() if PIPELINE.search(l) and 'qa-loop' not in l]


RECORDERS = ('.cssver.json',)   # files a gate itself rewrites as a record of the run — not a moving target


def tree_state():
    st = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout
    st = '\n'.join(l for l in st.splitlines() if not l.endswith(RECORDERS))
    return st + subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout


def per_gate_from_runner(out):
    """run-gates prints '=== <id>' blocks and a final summary naming failures."""
    ids = re.findall(r'^=== (\S+)', out, re.M)
    failed = set(); broken = set(); unmeasured = set()
    m = re.search(r'FOUND A DEFECT: (.+)', out);            failed |= set(x.strip() for x in m.group(1).split(',')) if m else set()
    m = re.search(r'CALIBRATION FAILED and reported nothing: (.+)', out); broken |= set(x.strip() for x in m.group(1).split(',')) if m else set()
    m = re.search(r'COULD NOT MEASURE: (.+)', out);         unmeasured |= set(x.strip() for x in m.group(1).split(',')) if m else set()
    res = {}
    for i in ids:
        res[i] = 'FAIL' if i in failed else 'BROKEN' if i in broken else 'UNMEASURED' if i in unmeasured else 'PASS'
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iterations', type=int, default=3)
    ap.add_argument('--parallel', type=int, default=2)
    ap.add_argument('--skip-stage', default='', help='comma list of stages to skip (e.g. nightly) for a quick loop')
    a = ap.parse_args()
    busy = pipeline_running()
    if busy:
        print('REFUSING TO START: the CSS pipeline is running —', busy[0][:80]); return 3
    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    out_dir = os.path.join(ROOT, 'prototypes', 'qa-loop', ts); os.makedirs(out_dir, exist_ok=True)
    gates = json.load(open(os.path.join(ROOT, 'tools', 'gates.json')))
    gates = gates['gates'] if isinstance(gates, dict) else gates
    unrun = [g for g in gates if g.get('runner') is False]
    skip = set(s for s in a.skip_stage.split(',') if s)
    results = {}     # gate -> [verdict per iteration]
    times = {}
    base_state = tree_state()

    def record(name, verdict, secs):
        results.setdefault(name, []).append(verdict); times[name] = times.get(name, 0) + secs

    for it in range(1, a.iterations + 1):
        print(f'\n===== iteration {it}/{a.iterations}  {datetime.datetime.now():%H:%M}')
        if tree_state() != base_state:
            print('STOPPING: the working tree or HEAD changed between iterations — the target moved.'); break
        for stage in ('pre-push', 'nightly'):
            if stage in skip: continue
            code, secs, out = sh(['python3', 'tools/run-gates.py', '--stage', stage, '--parallel', str(a.parallel)],
                                 os.path.join(out_dir, f'it{it}-{stage}.log'), timeout=5400)
            per = per_gate_from_runner(out)
            if not per: per = {f'stage:{stage}': 'PASS' if code == 0 else 'FAIL'}
            for k, v in per.items(): record(k, v, secs / max(1, len(per)))
            print(f'  {stage:9s} exit {code}  {secs/60:.1f} min  ' + ', '.join(f'{k}={v}' for k, v in per.items() if v != 'PASS'))
        for g in unrun:
            cmd = [c.replace('{BASE}', 'http://localhost:8000') for c in g['cmd']]
            code, secs, out = sh(cmd, os.path.join(out_dir, f"it{it}-{g['id']}.log"), timeout=2400)
            v = 'PASS' if code == 0 else 'BROKEN' if code == 2 else 'UNMEASURED' if code == 3 else 'FAIL'
            record(g['id'], v, secs); print(f"  {g['id']:28s} {v:10s} {secs:5.0f}s")
        code, secs, out = sh(['python3', 'tools/journey-check.py'], os.path.join(out_dir, f'it{it}-journey.log'), timeout=2400)
        v = 'PASS' if code == 0 else 'BROKEN' if code == 2 else 'UNMEASURED' if code == 3 else 'FAIL'
        record('journey-check', v, secs); print(f"  {'journey-check':28s} {v:10s} {secs:5.0f}s")

    # classify
    rows = []
    for k, vs in sorted(results.items()):
        if all(v == 'PASS' for v in vs): cls = 'STABLE PASS'
        elif all(v == vs[0] for v in vs): cls = f'STABLE {vs[0]}'
        else: cls = 'FLAKY'
        rows.append((cls, k, vs))
    stable_fail = [r for r in rows if r[0] == 'STABLE FAIL']
    flaky = [r for r in rows if r[0] == 'FLAKY']
    broken = [r for r in rows if 'BROKEN' in r[0] or 'UNMEASURED' in r[0]]
    lines = [f'# QA loop — {ts}', '', f'{a.iterations} iteration(s); {len(rows)} checks; '
             f'{len(stable_fail)} stable failure(s), {len(flaky)} flaky, {len(broken)} broken/unmeasured.', '',
             '| class | check | per iteration | minutes total |', '|---|---|---|---|']
    for cls, k, vs in sorted(rows, key=lambda r: (r[0] == 'STABLE PASS', r[0], r[1])):
        lines.append(f'| {cls} | {k} | {" · ".join(vs)} | {times.get(k, 0)/60:.1f} |')
    lines += ['', 'Logs per iteration and per check sit beside this file.',
              'CANNOT SEE: defects no gate has a class for yet; a stable pass is only as good as the gate set.']
    open(os.path.join(out_dir, 'report.md'), 'w').write('\n'.join(lines))
    print('\n' + '\n'.join(lines[:4]))
    for cls, k, vs in rows:
        if cls != 'STABLE PASS': print(f'  {cls:14s} {k:32s} {" · ".join(vs)}')
    print(f'\nreport: {os.path.relpath(os.path.join(out_dir, "report.md"), ROOT)}')
    return 1 if stable_fail else 2 if (flaky or broken) else 0


if __name__ == '__main__':
    sys.exit(main())
