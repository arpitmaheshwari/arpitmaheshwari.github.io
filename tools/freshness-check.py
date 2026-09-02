#!/usr/bin/env python3
"""Fail when a page's "Last updated <Month Year>" claim is older than its own prose.

Why this exists: on 2026-09-03 ten pages published "Last updated June 2026" — the nine
pattern pages and the glossary. Their visible copy had changed as recently as the previous
day. The claim was three months stale on the pages whose entire argument is "check me", and
nothing could see it: it is not a broken link, not a contrast failure, not a typo. It is a
true-looking sentence that has quietly stopped being true.

A stale freshness claim is worse than none. It is the one piece of metadata a reader uses to
decide whether the thinking is current, and getting it wrong costs exactly the credibility
the rest of the page is trying to earn.

WHAT COUNTS AS AN UPDATE: a change to the VISIBLE PROSE inside <main>. Not a version stamp,
not a footer partial, not a CSS hash — a reader means "the words changed". The walk stops at
the first revision whose main text differs, so it is cheap for recently-edited pages.

CALIBRATION
    --selftest rewinds a real page's claim by a year and requires the gate to catch it.

CANNOT SEE: whether the prose change was meaningful or a typo fix, and pages that state no
date at all (silence is not a claim, so it is not this gate's business).
"""
import html, re, subprocess, sys

CLAIM = re.compile(r'(?i)(?:last\s+)?updated\s+([A-Z][a-z]+)\s+(20\d\d)')
MONTHS = ['january','february','march','april','may','june','july','august',
          'september','october','november','december']
MAX_WALK = 60


def visible_main(blob):
    m = re.search(r'(?is)<main\b[^>]*>(.*)</main>', blob)
    if not m:
        return ''
    s = re.sub(r'(?is)<(script|style|svg)\b[^>]*>.*?</\1>', ' ', m.group(1))
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def last_prose_change(path):
    """(year, month) of the newest revision whose visible main text differs from the next."""
    log = [l.split() for l in subprocess.run(
        ['git', 'log', '--format=%H %cs', '--', path],
        capture_output=True, text=True).stdout.strip().split('\n') if l.strip()]
    prev, newest = None, None
    for sha, date in log[:MAX_WALK]:
        blob = subprocess.run(['git', 'show', f'{sha}:{path}'],
                              capture_output=True, text=True).stdout
        cur = visible_main(blob)
        if prev is None:
            prev, newest = cur, date
            continue
        if cur != prev:
            break
        newest = date
    if not newest:
        return None
    y, m, _ = newest.split('-')
    return int(y), int(m)


def pages():
    out = subprocess.run(['git', 'ls-files', '*.html'], capture_output=True, text=True).stdout.split()
    return [f for f in out if not f.startswith(('partials/', 'tests/', 'prototypes/', 'assets/'))]


def scan(override=None):
    findings, checked = [], 0
    for rel in pages():
        try:
            src = open(rel, encoding='utf-8').read()
        except OSError:
            continue
        if override and rel == override[0]:
            src = override[1]
        # Claims are read from the WHOLE document, not just <main>: on the pattern pages the
        # "Last updated" line sits in the page-head block above <main>, so scanning main only
        # saw 1 page of the 11 that state a date. The prose comparison below still uses main —
        # a reader means "the words changed", not "the header changed".
        doc = re.sub(r'(?is)<(script|style|svg)\b[^>]*>.*?</\1>', ' ', src)
        doc = re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', doc)))
        claims = {(m.group(1).lower(), int(m.group(2))) for m in CLAIM.finditer(doc)}
        if not claims:
            continue
        checked += 1
        real = last_prose_change(rel)
        if not real:
            continue
        for mon, yr in claims:
            if mon not in MONTHS:
                continue
            claimed = (yr, MONTHS.index(mon) + 1)
            if claimed < real:
                findings.append((rel, f"{mon.title()} {yr}", f"{real[0]}-{real[1]:02d}"))
    return findings, checked


def main():
    selftest = '--selftest' in sys.argv
    # CALIBRATION: rewind a real page's claim by a year and require the gate to notice.
    victim = next((p for p in pages()
                   if CLAIM.search(visible_main(open(p, encoding='utf-8').read()))), None)
    if victim:
        src = open(victim, encoding='utf-8').read()
        rigged = CLAIM.sub(lambda m: f"updated {m.group(1)} {int(m.group(2)) - 1}", src, count=1)
        caught = any(f[0] == victim for f in scan(override=(victim, rigged))[0])
        print(f"[calibration] {'PASS' if caught else 'FAIL'} — a claim rewound by a year is "
              f"{'caught' if caught else 'INVISIBLE'}")
        if not caught:
            print("\nRefusing to report. A checker that cannot fail is not evidence.")
            return 2
    if selftest:
        return 0

    findings, checked = scan()
    for rel, claimed, real in findings:
        print(f"  STALE  {rel}\n         says \"updated {claimed}\" — its visible copy changed {real}")
    print(f"\n{len(findings)} stale freshness claim(s) across {checked} page(s) that state a date")
    print("CANNOT SEE: whether a prose change was meaningful, or pages that state no date.")
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
