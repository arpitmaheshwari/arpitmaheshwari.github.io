#!/usr/bin/env python3
"""Fail when an <svg><use> points at a symbol the page does not have.

Why this exists: on 2026-08-30 the footer's "Back to top" chevron was invisible on 17
shipped pages. The button referenced <use href="#i-chevron-up">, but the symbol lived in a
page-level sprite that those pages did not carry, so the <svg> reserved its 14x14 box and
painted a bounding box of 0x0 — a hole where an icon should be.

NOTHING caught it, and nothing could:
  * link-integrity-check strips the fragment and checks the file, and a pure fragment is
    treated as same-page and skipped entirely;
  * asset-load-check verifies <img> elements paint — a <use> is not an <img>, makes no
    network request, and cannot 404;
  * contrast, overflow and prose gates never look at an icon at all.
A broken sprite reference is invisible to every gate that reads text or watches requests.

CALIBRATION
    --selftest plants a <use> pointing at a symbol that does not exist and requires it.

CANNOT SEE: a symbol that EXISTS but draws nothing (an empty <symbol>), an icon that is
the wrong icon, or one painted in the background colour. This is a reference check.
"""
import os, re, subprocess, sys

USE = re.compile(r'<use\b[^>]*?(?:xlink:)?href="#([^"]+)"', re.I)
IDS = re.compile(r'\sid="([^"]+)"')


def pages(root):
    out = subprocess.run(['git', 'ls-files', '*.html'], cwd=root,
                         capture_output=True, text=True).stdout.split()
    return [f for f in out if not f.startswith(('tests/', 'prototypes/'))]


def scan(root, extra_text=None):
    findings = []
    for rel in pages(root):
        p = os.path.join(root, rel)
        try:
            s = open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        if extra_text and rel == 'index.html':
            s += extra_text
        have = set(IDS.findall(s))
        for m in USE.finditer(s):
            ref = m.group(1)
            if ref not in have:
                findings.append((rel, ref))
    return findings


def main():
    root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    selftest = '--selftest' in sys.argv

    planted = '<svg><use href="#i-does-not-exist-canary"/></svg>'
    caught = [f for f in scan(root, extra_text=planted) if f[1] == 'i-does-not-exist-canary']
    ok = bool(caught)
    print(f"[calibration] {'PASS' if ok else 'FAIL'} — a <use> pointing at a missing symbol "
          f"is {'caught' if ok else 'INVISIBLE'}")
    if not ok:
        print("\nRefusing to report. A checker that cannot fail is not evidence.")
        return 2
    if selftest:
        return 0

    findings = scan(root)
    n = len(pages(root))
    if findings:
        for rel, ref in findings:
            print(f"  BROKEN  {rel}  ->  <use href=\"#{ref}\"> — no element with that id on the page")
        print(f"\n{len(findings)} broken sprite reference(s) across {n} page(s)")
        print("CANNOT SEE: a symbol that exists but draws nothing, or the wrong icon.")
        return 1
    print(f"\n0 broken sprite reference(s) across {n} page(s)")
    print("CANNOT SEE: a symbol that exists but draws nothing, or the wrong icon.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
