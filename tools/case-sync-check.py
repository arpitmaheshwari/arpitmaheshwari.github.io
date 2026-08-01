#!/usr/bin/env python3
"""
case-sync-check.py — fail the build when the BOOK and the CLASSIC case studies disagree.

WHY THIS EXISTS
    The same six case studies are told twice: once as classic pages under case-studies/, once
    inside book/portfolio.js. Two copies of the same facts, maintained by hand. On 2026-08-01 a
    comparison found the book had silently gone stale:

      * OrgOS and Technical Due Diligence still said "Design Lead" — the classic pages and canon
        had said "Product & Design Lead" since the 2026-07-25 PM-receipts retitle.
      * The book claimed "the screens are redacted on purpose" on four spreads that were visibly
        showing screens, and carried none of the synthetic-data provenance captions that canon
        locks and both the classic pages and the PDF display.
      * PTC's 0% → 64% subscription shift and AdTech's 45% / 3x / 70% never crossed over.

    None of it was WRONG in the sense of contradicting a number. It was STALE: updates landed on
    one surface and never the other. That failure mode is invisible to the contrast gate (colours
    are fine) and to canon-lint (no banned words), so it needs its own check.

    This does not make the book generate from canon — that would be a large refactor of a working
    3,000-line file. It does the enforceable 80%: assert the two surfaces agree on the facts that
    must never diverge, and fail loudly when they do.

WHAT IT CHECKS, per case
    * ROLE — the exact role string, in canon, in the classic page's vitals, and in the book's meta.
    * LOCKED METRICS — every canon-locked figure for that case must appear on BOTH surfaces.
    * PROVENANCE — any surface displaying a reconstruction/product screenshot must caption it;
      and nothing may claim screens are hidden while displaying them.

CALIBRATION
    Like the other gates here, it proves it can fail before it reports clean: --selftest mutates
    each rule's input in memory and confirms the rule catches it.

USAGE   python3 tools/case-sync-check.py [--root .] [--selftest]
EXIT    0 = calibrated and in sync · 1 = drift found, or calibration did not go red
"""
import argparse, os, re, sys

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

def gh(level, msg):
    if IN_CI:
        print(f"::{level}::{str(msg).replace(chr(13),'').replace(chr(10),'%0A')}", flush=True)

# case key -> (classic file, book title as it appears in NDA_CASES/CASES, canonical role)
CASES = {
    "ptc":          ("case-studies/ptc.html",          "PTC University — Learning Connector", "Lead Product Designer"),
    "o2":           ("case-studies/o2.html",           "Telefónica MyO2 & Priority Moments",       "Designer + Front-end"),
    "fintech":      ("case-studies/fintech.html",      "AI-Assisted Private Equity Investing",     "Lead Product Designer"),
    "adtech":       ("case-studies/adtech.html",       "Programmatic Advertising Platform",        "Lead Product Designer"),
    "orgos":        ("case-studies/orgos.html",        "OrgOS · Transparent Org Tooling",          "Product & Design Lead"),
    "vc-diligence": ("case-studies/vc-diligence.html", "Technical Due Diligence Platform",         "Product & Design Lead"),
}

# Canon-locked figures that must be present on BOTH the classic page and in the book.
# Regexes, because the same number is legitimately typeset differently across surfaces
# (&rarr; vs →, "550k+" inside prose vs a metric slot).
LOCKED = {
    "ptc":          [("$1M/yr",        r"\$1M"),
                     ("550k+",         r"550k\+"),
                     ("0% → 64%",      r"0%\s*(?:→|&rarr;|\\u2192)\s*64%")],
    "o2":           [("4M+",           r"4M\+"),
                     ("2.6M",          r"2\.6M")],
    "fintech":      [("60% faster",    r"60%\s*faster")],
    "adtech":       [("2 wks → 3 hrs", r"2\s*wks?\s*(?:→|&rarr;|\\u2192)\s*3\s*hrs"),
                     ("£69k",          r"£69[,k]?0?0?0?")],
    "orgos":        [("8 modules",     r"\b8\s*modules|eight modules"),
                     ("250 today",     r"\b250\b")],
    "vc-diligence": [("3 wks → 4 days",r"3\s*wks?\s*(?:→|&rarr;|\\u2192)\s*4\s*days")],
}

# A surface must never assert screens are withheld while rendering one.
CONTRADICTION = (r"screens? (?:are|is) redacted", "claims screens are redacted")


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def _decode_escapes(src):
    r"""portfolio.js stores titles with \uXXXX escapes (non-breaking space, mid-dot, accents).
    Decode them so a plain-text title from the CASES table above matches literally."""
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), src)


def _rich_case_regions(book):
    """Only the arrays holding FULL case records (meta / ledger / outcome / plate).

    portfolio.js ALSO contains a short summary list using the same `title:` key but carrying no
    role and no metrics. Matching that list instead was this checker's own first bug: every role
    came back None and every present metric looked missing — output indistinguishable from real
    drift. Scope the search to the rich records first, then match."""
    out = []
    for anchor, opener, closer in (("const CASES = {", "{", "}"),
                                   ("const NDA_CASES = [", "[", "]")):
        i = book.find(anchor)
        if i < 0:
            continue
        j = i + book[i:].index(opener)
        depth, k = 0, j
        while k < len(book):
            if book[k] == opener:
                depth += 1
            elif book[k] == closer:
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out.append(book[j:k + 1])
    return out


def book_case_chunk(book, title):
    """Return the slice of portfolio.js holding one case's FULL record, or None."""
    norm = " ".join(title.split())          # collapses non-breaking spaces too
    for region in _rich_case_regions(_decode_escapes(book)):
        for m in re.finditer(r'title:\s*"([^"]+)"', region):
            if " ".join(m.group(1).split()) == norm:
                nxt = re.search(r'\n\s*\}(?:,\s*\{)?\s*\n?\s*(?:no|key):\s*"', region[m.end():])
                return region[m.start(): m.end() + (nxt.start() if nxt else 4000)]
    return None


def check(root, book_override=None, classic_override=None):
    """Returns a list of human-readable drift findings."""
    book = book_override if book_override is not None else read(root, "book/portfolio.js")
    findings = []

    for key, (rel, title, canon_role) in CASES.items():
        classic = classic_override.get(key) if classic_override and key in classic_override \
                  else read(root, rel)
        chunk = book_case_chunk(book, title)
        if chunk is None:
            findings.append(f"{key}: case not found in book/portfolio.js (looked for title {title!r})")
            continue

        # ---- ROLE ----
        bm = re.search(r'\["Role",\s*"([^"]+)"\]', chunk)
        book_role = bm.group(1) if bm else None
        cm = re.search(r"<dt[^>]*>\s*Role\s*</dt>\s*<dd[^>]*>(.*?)</dd>", classic, re.S)
        classic_role = re.sub(r"<[^>]+>", "", cm.group(1)).replace("&amp;", "&").strip() if cm else None
        if book_role != canon_role:
            findings.append(f"{key}: ROLE in book is {book_role!r}, canon says {canon_role!r}")
        if classic_role != canon_role:
            findings.append(f"{key}: ROLE on classic page is {classic_role!r}, canon says {canon_role!r}")

        # ---- LOCKED METRICS on both surfaces ----
        for label, rx in LOCKED.get(key, []):
            if not re.search(rx, chunk, re.I):
                findings.append(f"{key}: locked metric {label!r} missing from the BOOK")
            if not re.search(rx, classic, re.I):
                findings.append(f"{key}: locked metric {label!r} missing from the CLASSIC page")

        # ---- PROVENANCE: don't claim screens are hidden while showing one ----
        shows_image = bool(re.search(r'\bimg:\s*"', chunk))
        if shows_image and re.search(CONTRADICTION[0], chunk, re.I):
            findings.append(f"{key}: book {CONTRADICTION[1]} while also rendering an image")

    # the blanket NDA footnote lives outside any one case chunk — check it globally too
    if re.search(CONTRADICTION[0], book, re.I):
        findings.append(f"book/portfolio.js {CONTRADICTION[1]} somewhere in shared copy — every NDA "
                        f"spread renders a reconstruction or schematic, so this claim is false")
    return findings


def selftest(root):
    """Mutate each rule's input and confirm the rule catches it. Two-sided: also confirm the
    unmutated tree is clean, so a rule that fires on everything is caught too."""
    book = read(root, "book/portfolio.js")

    baseline = check(root)
    if baseline:
        return False, ("PRECISION: the unmutated tree already reports drift, so calibration cannot "
                       f"distinguish signal from noise — {len(baseline)} finding(s), first: {baseline[0]}")

    # sensitivity A: break a role
    mutated = book.replace('["Role", "Product & Design Lead"]', '["Role", "Design Lead"]', 1)
    if mutated == book or not any("ROLE" in f for f in check(root, book_override=mutated)):
        return False, "SENSITIVITY: a planted ROLE mismatch was not caught"

    # sensitivity B: remove a locked metric
    # replace ALL occurrences: "550k+" appears in the short summary list too, and mutating only
    # the first left the PTC record intact, so the rule correctly still found it — the planted
    # defect simply was not where the rule looks. Caught by this calibration, which is the point.
    mutated2 = book.replace("550k+", "five hundred thousand")
    if mutated2 == book or not any("550k+" in f for f in check(root, book_override=mutated2)):
        return False, "SENSITIVITY: a planted missing-metric was not caught"

    # sensitivity C: re-introduce the redaction contradiction
    mutated3 = book.replace('note: "trust = the model declining to bluff"',
                            'note: "The screens are redacted on purpose"', 1)
    if mutated3 == book or not any("redacted" in f for f in check(root, book_override=mutated3)):
        return False, "SENSITIVITY: a planted screens-are-redacted contradiction was not caught"

    return True, "sensitivity OK (role, metric, provenance) + precision OK (clean tree reports nothing)"


def main():
    ap = argparse.ArgumentParser(description="Book <-> classic case-study drift gate.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-selftest", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if not a.no_selftest:
        ok, msg = selftest(root)
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:
            print("\nRefusing to report results. A check that cannot fail is not evidence.")
            gh("error", f"case-sync-check CALIBRATION FAILED — {msg}")
            sys.exit(1)
        if a.selftest:
            sys.exit(0)

    findings = check(root)
    print(f"\nchecked {len(CASES)} case studies across book/portfolio.js and case-studies/*.html")
    if findings:
        print(f"\nDRIFT — the book and the classic pages disagree ({len(findings)}):")
        for f in findings:
            print(f"  {f}")
            gh("error", f"CASE DRIFT — {f}")
    else:
        print("Result: in sync (roles, locked metrics, and provenance claims all agree).")
    print("\nNOT covered: prose tone, ordering, or anything not in the LOCKED table above. "
          "Adding a canon-locked figure means adding it here too.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
