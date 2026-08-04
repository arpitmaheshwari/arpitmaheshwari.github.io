#!/usr/bin/env python3
"""
canon-lint.py — mechanical gate for the drift the contrast gate cannot see: WRONG WORDS.

WHY THIS EXISTS
    On 2026-08-01 Arpit found "The Trust Layer" still printed on his book cover — a term retired the
    previous day. Eight QA passes had reported the site clean. Two reasons, both structural:

      1. I had recorded my own judgement in CANONICAL-FACTS ("brand name unchanged — never rename
         these") and every later audit obeyed it as if it were a verified fact.
      2. My term search was `trust.layer (design|practice|approach)` — a pattern qualified by what I
         EXPECTED to find, which by construction could not match a bare brand usage on a cover.

    So this linter greps BARE tokens, reports raw counts before any triage, and — like
    contrast-audit.py — refuses to report clean until a planted violation proves it can fail.

WHAT IT CHECKS
    * BANNED strings: retired terms, fabricated facts, superseded job titles.
    * MALFORMED metric strings: the number-writing rules in CANONICAL-FACTS §3.
    * PAIRED strings: where one phrase appears, its locked companion must too.
    Shipped surfaces (html/txt/xml/svg/js/css) are ERRORS. Planning docs and markdown are WARNINGS,
    because they are repo history rather than something a hiring manager reads — but they are public
    on GitHub, so they are still surfaced.

USAGE
    python3 tools/canon-lint.py [--root .] [--selftest]
EXIT
    0 = calibrated and clean · 1 = violation, or calibration failed to go red
"""
import argparse, os, re, sys, tempfile

# --------------------------------------------------------------------- rules
# Every rule cites its authority in CANONICAL-FACTS.md so a reader can check it, and so a future
# change to canon has an obvious corresponding change here.

BANNED = [
    # (bare regex, human explanation, canon reference)
    (r"trust[\s\-_]?layer",
     'the retired term. Practice = "human-in-the-loop design"; book/portfolio/newsletter = '
     '"Human in the Loop"; module = hitl.js',
     "§1 retired completely 2026-08-01"),
    (r"\b16 years\b|\bsixteen years\b",
     'fabricated tenure — canon locks FIFTEEN years',
     "§1 the line is locked"),
    (r"\$120M",
     'fabricated revenue figure with zero basis anywhere in canon',
     "ChatGPT-spec fact quarantine"),
    (r"\b8 AI products\b",
     'no basis — canon has 8 PATTERNS and 6 case studies, not 8 products',
     "ChatGPT-spec fact quarantine"),
    (r"AI Product Designer",
     'superseded job title — use "Product & Design Leader"',
     "§1 retitled 2026-07-25"),
    (r"2\s*wks?\s*(?:→|->)\s*1\s*hr|two weeks to one hour",
     'the retired speed variant — "2 wks → 3 hrs" is the ONLY time metric on any surface',
     "§3 case 4, retired 2026-07-31"),
    (r"\bfour weeks'? notice\b",
     'availability must use the digit "4", never the word',
     "§2 availability"),
]

# CASE_SENSITIVE rules must NOT be scanned with re.I — the first version of this file ran every
# rule case-insensitively, so `\b550K\+` matched the perfectly correct "550k+" and produced 11 false
# positives. A rule about letter case cannot be checked case-insensitively.
CASE_SENSITIVE = {r"\b550K\+"}

# (pattern, why, ref, severity). "warn" never fails the build.
MALFORMED = [
    (r"\b3w\s*(?:→|->)\s*4d\b", 'write "3 wks → 4 days" in full', "§3 number-writing rules", "error"),
    (r"\b550K\+", 'lowercase k: "550k+"', "§3 number-writing rules", "error"),
    # ONLY a metric arrow jammed against its own numbers/units. The first attempt was `\S→|→\S`,
    # which matched `→<` (an arrow before a closing tag) and `"→` (an arrow inside an attribute) and
    # produced 91 false positives across the site. Canon's rule is about prose like "2 wks→3 hrs",
    # not about an arrow's adjacency to markup.
    # WARN, not error, and digit-to-digit only. Two reasons for the caution:
    #  * `[\w%]→` also matched "Listen→Structure→Prove→Land" — a process sequence, not a metric.
    #  * CANON CONTRADICTS ITSELF here: §3 says the arrow takes a space each side, yet canon's own
    #    metric table writes "5→1 platforms" and "9→11 locales", which the site mirrors. Until Arpit
    #    settles which form is canonical, failing the build on it would be enforcing my guess.
    (r"\d→\d", 'canon §3 says the arrow takes a space each side, but canon\'s own metric table '
                'writes this unspaced — needs a human decision, not a build failure',
     "§3 vs §3 table — unresolved", "warn"),
]

# DELIBERATELY NOT MECHANISED — canon's 'never write "−60%" (use "60% faster")' bans phrasing an
# IMPROVEMENT as a negative percentage. Deciding that needs to know whether the number is a headline
# claim or real directional data, and the site has three legitimate negatives ("print run −92% in year
# one", "inventory price −8%", "sessions −19% → +31%"). A regex flagged all three. A gate that cries
# wolf gets switched off, so this rule stays a human review item rather than a build failure.

# If the left phrase appears in a file, the right one must appear in the same file.
PAIRED = [
    (r"years, five industries", r"[Ff]ifteen years",
     'the "five industries" line must carry "Fifteen years"', "§1 the line is locked"),
]

# Shipped = what a visitor or a crawler reads. Errors here fail the build.
SHIPPED_EXT = {".html", ".txt", ".xml", ".svg", ".js", ".css", ".json"}
# Warnings only: repo history and internal docs. Public on GitHub, but not the product.
SOFT_EXT = {".md"}

# Paths where an occurrence is legitimate and deliberate. Each needs a stated reason.
ALLOW = {
    "prototypes/paper-first.html":
        "ARCHIVED PROTOTYPE (noindex, unlinked): the ChatGPT-era paper mockup, kept as a record "
        "of a rejected direction. It predates the 2026-08-01 term retirement; rewriting an "
        "archive would falsify what was actually explored.",
    "prototypes/hook-d.html":
        "ARCHIVED PROTOTYPE (noindex, unlinked): the boarding-pass concept as first drawn, "
        "before the Loop Air rename. Same archive rule — the shipped pass on index.html is "
        "the corrected surface.",
    "lab/trustlayer.html":
        "forwarding stub for a URL published in the sitemap and linked from the portfolio PDF; "
        "renders no visible copy, noindex",
    "assets/og-images/_book-og.template.html":
        "generator comment recording why the card was rebuilt",
    "CANONICAL-FACTS.md":
        "canon records the ban itself",
    "DESIGN-SYSTEM.md":
        "records the superseded values as measured history",
    "tools/canon-lint.py":
        "this file defines the rules",
    "tools/contrast-audit.py":
        "docstring recounts the failure that motivated it",
    ".github/workflows/contrast-gate.yml":
        "comment recounts the same failure",
    ".github/workflows/canon-gate.yml":
        "comment recounts the same failure",
    ".githooks/pre-push":
        "comment recounts the same failure",
}
SKIP_DIRS = {".git", "node_modules", ".claude", "portfolio-sources", ".requirements"}


def walk(root):
    """Yield (relpath, ext) for files git TRACKS. Using git ls-files rather than os.walk means
    .gitignore is respected for free — an earlier version flagged prototype-paper.html, which is
    gitignored and never ships. Falls back to a filesystem walk outside a git repo (selftest)."""
    import subprocess
    tracked = None
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "-z"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            tracked = [x for x in r.stdout.split("\0") if x]
    except (OSError, subprocess.SubprocessError):
        pass
    if tracked is None:
        tracked = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                tracked.append(os.path.relpath(os.path.join(dirpath, fn), root))
    for rel in tracked:
        if any(part in SKIP_DIRS for part in rel.split(os.sep)):
            continue
        base = os.path.basename(rel)
        if base.startswith(("__ca_", "__canon_canary", "_qa-", "_g-")):
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext in SHIPPED_EXT or ext in SOFT_EXT:
            if os.path.exists(os.path.join(root, rel)):
                yield rel, ext


def scan(root, extra=None):
    """Returns (errors, warnings, allowed) — each a list of (path, line_no, rule, detail, ref).
    `extra` forces additional relative paths to be scanned even if git does not track them; the
    calibration canaries are untracked by design."""
    errors, warnings, allowed = [], [], []
    files = list(walk(root))
    for rel in (extra or []):
        files.append((rel, os.path.splitext(rel)[1].lower()))
    for rel, ext in files:
        try:
            text = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        lines = text.split("\n")
        soft = ext in SOFT_EXT
        allowlisted = rel in ALLOW

        # For formatting rules only, blank out code comments so an illustrative example inside one
        # is not linted as shipped copy.
        decommented = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        decommented = re.sub(r"<!--.*?-->", " ", decommented, flags=re.S)
        dec_lines = decommented.split("\n")

        rules = [(pat, why, ref, "error") for pat, why, ref in BANNED] + list(MALFORMED)
        for pattern, why, ref, severity in rules:
            flags = 0 if pattern in CASE_SENSITIVE else re.I
            source = lines if severity == "error" and (pattern, why, ref) in [
                (p2, w2, r2) for p2, w2, r2 in BANNED] else dec_lines
            for i, line in enumerate(source, 1):
                for m in re.finditer(pattern, line, flags):
                    hit = (rel, i, m.group(0).strip(), why, ref)
                    if allowlisted:
                        allowed.append(hit)
                    elif soft or severity == "warn":
                        warnings.append(hit)
                    else:
                        errors.append(hit)

        for left, right, why, ref in PAIRED:
            if re.search(left, text) and not re.search(right, text):
                hit = (rel, 0, f"missing companion for /{left}/", why, ref)
                (warnings if soft else errors).append(hit)
    return errors, warnings, allowed


# Sensitivity canaries — MUST be caught.
CANARIES = [
    ("__canon_canary_a.html", "<p>Fifteen years… the trust layer between people and AI.</p>"),
    ("__canon_canary_b.html", "<p>16 years shipping, and a $120M ARR platform.</p>"),
]

# Precision canary — MUST produce ZERO hits. This is the second calibration axis, added after three
# separate bugs in this very file each produced a confident wall of false positives (re.I defeating a
# case rule; scanning gitignored files; an arrow rule that matched HTML markup). Proving a linter CAN
# go red says nothing about whether it goes red for the RIGHT reasons — a gate that cries wolf is a
# gate that gets switched off, which is strictly worse than no gate at all.
CLEAN_CANARY = ("__canon_canary_ok.html", """<!doctype html><html><body>
<p>Fifteen years, five industries, one problem. Available &middot; 4 weeks' notice.</p>
<p>Campaign planning 2 wks &rarr; 3 hrs. Deal screening 60% faster. Diligence 3 wks &rarr; 4 days.</p>
<p>550k+ registered learners &middot; subscription 0% &rarr; 64% of new bookings &middot; $1M / yr.</p>
<p>Print run &minus;92% in year one. Product &amp; Design Leader. Human in the Loop.</p>
<a href="./hitl.js">Read the source &rarr;</a>
<p>human-in-the-loop design is the specialism.</p>
</body></html>""")


def selftest(root):
    """Two-sided calibration.
      SENSITIVITY — planted violations must be caught (the linter can go red).
      PRECISION   — a file of legitimate, canon-correct copy must yield ZERO hits (it goes red only
                    for the right reasons).
    Either side failing means the linter's verdict is worthless, so nothing else is reported."""
    made = []
    try:
        for name, body in CANARIES + [CLEAN_CANARY]:
            p = os.path.join(root, name)
            open(p, "w", encoding="utf-8").write(body)
            made.append(p)
        names = [n for n, _ in CANARIES] + [CLEAN_CANARY[0]]
        errors, _, _ = scan(root, extra=names)

        caught = {os.path.basename(e[0]) for e in errors}
        missing = [n for n, _ in CANARIES if n not in caught]
        if missing:
            return False, f"SENSITIVITY: planted violations NOT caught in {', '.join(missing)}"

        false_pos = [e for e in errors if os.path.basename(e[0]) == CLEAN_CANARY[0]]
        if false_pos:
            detail = "; ".join(f"{e[2]!r} ({e[3]})" for e in false_pos[:4])
            return False, (f"PRECISION: {len(false_pos)} FALSE POSITIVE(S) on canon-correct copy — "
                           f"{detail}")

        found = sorted({e[2].lower() for e in errors
                        if os.path.basename(e[0]) in [n for n, _ in CANARIES]})
        return True, (f"sensitivity OK (caught {', '.join(found)}) + precision OK "
                      f"(0 false positives on correct copy)")
    finally:
        for p in made:
            if os.path.exists(p):
                os.unlink(p)


def main():
    ap = argparse.ArgumentParser(description="Canon / naming drift gate.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true", help="run calibration only")
    ap.add_argument("--no-selftest", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if not a.no_selftest:
        ok, msg = selftest(root)
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:
            print("\nRefusing to report results. A linter that cannot fail is not evidence.")
            sys.exit(1)
        if a.selftest:
            sys.exit(0)

    errors, warnings, allowed = scan(root)

    # Raw counts BEFORE triage — pre-filtering is how the original miss happened.
    print(f"\nscanned shipped surfaces + markdown under {root}")
    print(f"  raw hits: {len(errors)} error(s), {len(warnings)} warning(s), "
          f"{len(allowed)} allowlisted")

    if errors:
        print("\nERRORS — shipped surfaces (these fail the build):")
        for path, line, hit, why, ref in errors:
            where = f"{path}:{line}" if line else path
            print(f"  {where}\n      found {hit!r} — {why}\n      canon: {ref}")
    if warnings:
        print("\nWARNINGS — repo docs (public on GitHub, but not the product):")
        for path, line, hit, why, ref in warnings[:20]:
            print(f"  {path}:{line}  {hit!r} — {why}")
        if len(warnings) > 20:
            print(f"  … and {len(warnings) - 20} more")
    if allowed:
        print(f"\nALLOWLISTED ({len(allowed)} hits, each with a stated reason):")
        for path in sorted({h[0] for h in allowed}):
            print(f"  {path} — {ALLOW[path]}")

    print("\nNOT covered by this gate: the resume/portfolio PDFs and .docx live in the private "
          "folio-private repo and are not checked out here. Verify them there with pdftotext.")
    if not errors:
        print("Result: clean.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
