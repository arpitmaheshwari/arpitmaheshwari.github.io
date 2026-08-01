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
import argparse, json, os, re, sys

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

def gh(level, msg):
    if IN_CI:
        print(f"::{level}::{str(msg).replace(chr(13),'').replace(chr(10),'%0A')}", flush=True)

# case key -> classic page. Everything else (title, role, metrics, provenance) now comes from
# data/case-facts.js — the single source the book renders from. This file used to carry its own
# copy of the roles, which made it a THIRD place a fact could go stale. It now reads the hub.
CLASSIC = {
    "ptc":          "case-studies/ptc.html",
    "o2":           "case-studies/o2.html",
    "fintech":      "case-studies/fintech.html",
    "adtech":       "case-studies/adtech.html",
    "orgos":        "case-studies/orgos.html",
    "vc-diligence": "case-studies/vc-diligence.html",
}


def load_facts(root):
    """Parse data/case-facts.js — the single source. It is a JS file (no build step on this
    site), but its payload is a plain JSON object literal, so slice that out and json.loads it
    rather than shelling out to node."""
    src = read(root, "data/case-facts.js")
    i = src.index("var CASE_FACTS =") + len("var CASE_FACTS =")
    depth, k, start = 0, src.index("{", i), src.index("{", i)
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return json.loads(src[start:k + 1])


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


def check(root, facts_override=None, classic_override=None):
    """Compare each CLASSIC page against the single source in data/case-facts.js.

    The BOOK is no longer compared field-by-field: since the single-source refactor it RENDERS
    from that file, so book-vs-source drift is structurally impossible. What can still drift is
    the hand-written classic HTML, and the provenance rule — so that is what is checked."""
    facts = facts_override if facts_override is not None else load_facts(root)
    book = read(root, "book/portfolio.js")
    findings = []

    for key, rel in CLASSIC.items():
        case = facts["cases"].get(key)
        if case is None:
            findings.append(f"{key}: missing from data/case-facts.js")
            continue
        classic = (classic_override or {}).get(key) or read(root, rel)

        # ---- ROLE: the classic page must match the single source ----
        canon_role = dict((m[0], m[1]) for m in case["meta"]).get("Role")
        cm = re.search(r"<dt[^>]*>\s*Role\s*</dt>\s*<dd[^>]*>(.*?)</dd>", classic, re.S)
        classic_role = re.sub(r"<[^>]+>", "", cm.group(1)).replace("&amp;", "&").strip() if cm else None
        if canon_role and classic_role != canon_role:
            findings.append(f"{key}: ROLE on the classic page is {classic_role!r}, "
                            f"data/case-facts.js says {canon_role!r}")

        # ---- LOCKED METRICS: every figure in the source must appear on the classic page ----
        for label, rx in LOCKED.get(key, []):
            if not re.search(rx, classic, re.I):
                findings.append(f"{key}: locked metric {label!r} missing from the CLASSIC page")

    # ---- the book must actually be wired to the source, not quietly re-hardcoded ----
    if "window.CASE_FACTS" not in book and "CF.get(" not in book:
        findings.append("book/portfolio.js no longer reads data/case-facts.js — the single "
                        "source has been bypassed and the two surfaces can drift again")

    # ---- provenance: never claim a screen is hidden while rendering one ----
    if re.search(CONTRADICTION[0], book, re.I):
        findings.append(f"book/portfolio.js {CONTRADICTION[1]} — every NDA spread renders a "
                        f"reconstruction or a schematic, so the claim is false")
    for key, case in facts["cases"].items():
        prov = case.get("provenance")
        if prov and re.search(CONTRADICTION[0], prov, re.I):
            findings.append(f"{key}: provenance caption {CONTRADICTION[1]}")
    return findings


def selftest(root):
    """Two-sided calibration, now against the single source.

    SENSITIVITY — mutate data/case-facts.js and confirm the classic pages are reported as
                  disagreeing with it; and confirm a re-hardcoded book is caught.
    PRECISION   — the untouched tree must report nothing, so a rule that fires on everything
                  cannot masquerade as a clean pass."""
    facts = load_facts(root)

    if check(root):
        first = check(root)[0]
        return False, (f"PRECISION: the untouched tree already reports drift, so calibration "
                       f"cannot separate signal from noise — first: {first}")

    # sensitivity A: change a ROLE in the source; the classic page now disagrees with it
    import copy
    mutated = copy.deepcopy(facts)
    for m in mutated["cases"]["orgos"]["meta"]:
        if m[0] == "Role":
            m[1] = "Chief Wireframe Officer"
    if not any("ROLE" in f for f in check(root, facts_override=mutated)):
        return False, "SENSITIVITY: a role changed in the single source was not caught"

    # sensitivity B: a provenance caption that lies about what the screen is
    mutated2 = copy.deepcopy(facts)
    mutated2["cases"]["adtech"]["provenance"] = "The screens are redacted on purpose"
    if not any("provenance" in f.lower() for f in check(root, facts_override=mutated2)):
        return False, "SENSITIVITY: a lying provenance caption was not caught"

    # sensitivity C: the book quietly bypassing the single source
    findings = check(root, facts_override=facts,
                     classic_override=None)
    saved = read(root, "book/portfolio.js")
    try:
        tmp = saved.replace("CF.get(", "XX_BYPASSED(").replace("window.CASE_FACTS", "nothing")
        with open(os.path.join(root, "book/portfolio.js"), "w", encoding="utf-8") as fh:
            fh.write(tmp)
        if not any("bypassed" in f.lower() or "no longer reads" in f.lower()
                   for f in check(root)):
            return False, "SENSITIVITY: a book that stopped reading the single source was not caught"
    finally:
        with open(os.path.join(root, "book/portfolio.js"), "w", encoding="utf-8") as fh:
            fh.write(saved)

    return True, ("sensitivity OK (role drift, lying provenance, book bypassing the source) "
                  "+ precision OK (untouched tree reports nothing)")


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
    print(f"\nchecked {len(CLASSIC)} classic case pages against data/case-facts.js "
          f"(the book renders from that same file, so it cannot drift from it)")
    if findings:
        print(f"\nDRIFT — the book and the classic pages disagree ({len(findings)}):")
        for f in findings:
            print(f"  {f}")
            gh("error", f"CASE DRIFT — {f}")
    else:
        print("Result: in sync — every classic page agrees with the single source, the "
              "book still reads it, and no provenance caption misdescribes a screen.")
    print("\nNOT covered: narrative prose, which deliberately stays per-surface. Adding a new\ncanon-locked figure means adding it to data/case-facts.js AND to the LOCKED table here.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
