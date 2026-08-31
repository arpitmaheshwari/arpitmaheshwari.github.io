#!/usr/bin/env python3
"""Stamp the footer with a machine-measured freshness line.

From the Reach-Out Gap review (2026-08-31): the most actively maintained
portfolio in a 72-site field read as timeless instead of alive. The fix is a
line the reader can trust because a machine wrote it: last shipped date and
this month's commit count, from git — never hand-typed.

Idempotent: inserts <span class="fresh"> after .footer-logo if missing,
rewrites its text otherwise. --check fails when the published line no longer
matches a fresh measurement (same contract as teardown-facts).
"""
import pathlib, re, subprocess, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent

def measure():
    last = subprocess.run(['git','log','-1','--format=%cs'], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    month = datetime.date.today().strftime('%Y-%m')
    n = subprocess.run(['git','rev-list','--count',f'--since={month}-01','HEAD'], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return f'last shipped {last} &middot; {n} changes this month'

def pages():
    for p in sorted(ROOT.rglob('*.html')):
        parts = p.relative_to(ROOT).parts
        if any(x.startswith('.') or x in ('prototypes','portfolio-sources','node_modules','book','tests') for x in parts): continue
        if p.name.startswith('_'): continue
        if 'footer-logo' in p.read_text(): yield p

def main():
    line = measure()
    check = '--check' in sys.argv
    bad = 0; changed = 0
    for p in pages():
        s = p.read_text()
        cur = re.search(r'<span class="fresh">([^<]*)</span>', s)
        if check:
            if not cur or cur.group(1) != line:
                bad += 1; print(f'STALE {p.relative_to(ROOT)}: wants "{line}"')
            continue
        if cur:
            if cur.group(1) != line:
                s = s.replace(cur.group(0), f'<span class="fresh">{line}</span>'); changed += 1
        else:
            s = s.replace('</div>\n', f'</div>\n', 1)  # no-op guard
            m = re.search(r'(<div class="footer-logo">[^<]*</div>)', s)
            if not m: continue
            s = s.replace(m.group(1), m.group(1) + f'\n  <span class="fresh">{line}</span>', 1); changed += 1
        p.write_text(s)
    if check:
        print('Result:', 'STALE' if bad else 'clean.'); sys.exit(1 if bad else 0)
    print(f'stamped "{line}" · {changed} page(s) updated')

if __name__ == '__main__':
    main()
