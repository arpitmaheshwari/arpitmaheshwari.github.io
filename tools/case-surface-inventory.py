#!/usr/bin/env python3
"""case-surface-inventory.py — find every file that makes a CASE-FACT claim, and fail when
one of them is outside the audit scopes.

WHY THIS EXISTS (2026-08-07)
    The 2026-08-05 AdTech correction ("no confidence scores, ever"; A/R/I was a synthesis,
    never born in AdTech) reached the case pages, the book, the resume and both PDFs — and sat
    uncorrected in FOUR pattern pages for two days, through several QA passes. The reason was
    not carelessness at the file level. It was scope:

      * case-sync-check.py enumerates case-studies/ and book/ ONLY.
      * canon-lint.py greps every file, but only for rules someone remembered to encode —
        and no rule existed for "a score attributed to the AdTech client" until 2026-08-07.
      * The narrative audits were handed an explicit surface list that named
        patterns/index.html but not patterns/*.html, so they truthfully reported
        "patterns/ clean" having read one file out of ten.

    Underneath all three: patterns/ was mentally filed as generic reference material. It is
    not. Nine pattern pages carry twenty links into real case studies under a "See this
    pattern in action" heading, each making a factual claim about Arpit's work.

WHAT IT DOES
    Treats "links to a case study" as the definition of a case-fact surface, discovers them
    mechanically, and fails if any is not in KNOWN_SCOPES. A new surface cannot be invented
    without this gate noticing — which is the property the last two days lacked.

USAGE   python3 tools/case-surface-inventory.py [--check]
EXIT    0 = every case-fact surface is claimed by a scope · 1 = an unscoped surface exists
"""
import os, re, subprocess, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every scope below must name who audits it, so "in scope" is never a vague claim.
KNOWN_SCOPES = {
    "case-studies/": "case-sync-check.py (vs data/case-facts.js) + canon-lint",
    "book/":         "case-sync-check.py (book mirrors the same facts) + canon-lint",
    "patterns/":     "canon-lint proximity rules; ADDED to audit scope 2026-08-07",
    "index.html":    "case-sync-check + canon-lint",
    "hire/":         "canon-lint",
    "screen/":       "canon-lint",
    "process/":      "canon-lint",
    "now/":          "canon-lint",
    "resources/":    "canon-lint",
    "writing/":      "canon-lint",
    "lab/":          "canon-lint + teardown-facts.py",
    "llms.txt":      "canon-lint",
    "data/":         "case-sync-check.py (it IS the source)",
    "404.html":      "canon-lint",
    "sitemap.xml":   "canon-lint",
}

def tracked():
    out = subprocess.run("git ls-files", shell=True, cwd=R, capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f.endswith((".html", ".js", ".txt", ".xml"))]

def main():
    unscoped, surfaces = [], []
    for f in tracked():
        if f.startswith("prototypes/"):      # archives: deliberately frozen, canon-lint allowlists them
            continue
        try:
            s = open(os.path.join(R, f), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        hits = len(re.findall(r"case-studies/[a-z0-9-]+\.html", s))
        if not hits:
            continue
        surfaces.append((f, hits))
        if not any(f == k or f.startswith(k) for k in KNOWN_SCOPES):
            unscoped.append((f, hits))

    print(f"  {len(surfaces)} files make case-fact claims "
          f"({sum(h for _, h in surfaces)} case links total).")
    for f, h in sorted(surfaces, key=lambda x: -x[1])[:6]:
        print(f"      {h:3}  {f}")
    if unscoped:
        print("\n  UNSCOPED — these make case claims and no audit scope owns them:")
        for f, h in unscoped:
            print(f"      {f}  ({h} case links)")
        print("\n  Add them to KNOWN_SCOPES with the name of the gate that covers them,")
        print("  or bring them under one. An unowned surface is how the AdTech story survived.")
    print("Result:", "UNSCOPED SURFACES" if unscoped else "clean — every case-fact surface is owned.")
    return 1 if unscoped else 0

if __name__ == "__main__":
    sys.exit(main())
