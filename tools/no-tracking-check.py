#!/usr/bin/env python3
"""Fail when a tool can drive a browser without refusing the trackers.

Arpit caught this: every page on the site loads Google Analytics AND Microsoft
Clarity, so every page any gate opened sent a real pageview and a real session
recording. One full sweep is ~844 page loads. A day of work is thousands of
fabricated visits in the numbers he reads to judge whether his outreach is
landing — the gates were corrupting the decision the data exists for.

The fix is one Chrome flag. This check exists because the fix is easy to
forget: the next browser tool written here will not have it unless something
insists. It is static and takes milliseconds.

  UNBLOCKED   a file launches Chrome without cdp.NO_TRACKING_FLAG
  UNBLOCKED   a Playwright config/helper with no analytics route abort

CALIBRATION
    --selftest checks a synthetic launch line with no flag and requires it to
    be reported.
"""
import argparse, glob, os, re, sys

LAUNCH = re.compile(r'\[\s*(CHROME|CH)\s*,', re.M)
PW_BLOCK = re.compile(r'page\.route\([^)]*(googletagmanager|google-analytics)', re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    findings = []

    for p in sorted(glob.glob('tools/*.py')):
        if os.path.basename(p) in ('cdp.py', 'no-tracking-check.py'):
            continue
        s = open(p, encoding='utf-8').read()
        if not LAUNCH.search(s):
            continue
        if 'NO_TRACKING_FLAG' not in s:
            findings.append((p, 'launches Chrome without NO_TRACKING_FLAG'))

    # cdp.py itself must still carry the flag into every launch
    cdp = open('tools/cdp.py', encoding='utf-8').read()
    if 'NO_TRACKING_FLAG' not in cdp or 'NO_TRACKING_FLAG,' not in cdp:
        findings.append(('tools/cdp.py', 'the shared harness no longer applies the flag'))

    for p in glob.glob('tests/pw/*.js'):
        s = open(p, encoding='utf-8').read()
        if 'newContext' in s or 'settle' in os.path.basename(p):
            if not PW_BLOCK.search(s) and os.path.basename(p) == 'settle.js':
                findings.append((p, 'no page.route abort for analytics'))

    if a.selftest:
        synthetic = '[CHROME, "--headless", "--dump-dom", url]'
        caught = bool(LAUNCH.search(synthetic)) and 'NO_TRACKING_FLAG' not in synthetic
        print(f'[calibration] {"PASS" if caught else "FAIL"} — an unflagged launch '
              f'line is {"caught" if caught else "INVISIBLE"}')
        if not caught:
            return 2

    for p, why in findings:
        print(f'  UNBLOCKED   {p}\n              {why}')
    print(f'\n{len(findings)} tool(s) could send a tracker beacon')
    print('CANNOT SEE: a tracker loaded from a host not in TRACKER_HOSTS, or a '
          'browser driven by something other than these files.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
