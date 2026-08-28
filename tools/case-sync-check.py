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
    "planit":       "case-studies/planit.html",
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
    "planit":       [("250 active",    r"\b250\b"),
                     ("1,000 visitors",r"1,000"),
                     ("0 complaints",  r"\b0\b[^.]{0,24}complaints|complaints[^.]{0,24}\b0\b")],
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


# Which canon table row (by its "#" column) corresponds to which case key.
CANON_ROW = {"1": "ptc", "2": "o2", "3": "fintech", "4": "adtech", "5": "orgos",
             "6": "vc-diligence", "7": "planit"}


def _norm(t):
    """Compare meaning, not typography: collapse whitespace incl. non-breaking spaces, strip
    markdown bold, and normalise the dash/quote variants that differ between a markdown table
    and a rendered page."""
    t = re.sub(r"\*\*", "", t)
    t = t.replace("\u00a0", " ").replace("\u2011", "-")
    return re.sub(r"\s+", " ", t).strip()


def parse_canon(root):
    """Pull the locked case table out of CANONICAL-FACTS.md §3.

    Canon is prose written for a human, so its cells carry editorial annotations
    ("Role: X (per PM-receipts retitle, 2026-07-25)"). Only the unambiguous parts are compared:
    the canonical NAME, the ROLE phrase, the HEADLINE metric, and the TAG. Everything else in
    those cells is commentary and is deliberately not machine-checked — inventing a parser for
    free prose would produce exactly the confident false positives this repo keeps getting
    burned by."""
    # CANONICAL-FACTS.md is deliberately UNTRACKED (2026-08-16): this repo is the live site, so
    # anything committed here is fetchable at arpitmaheshwari.com/<path> and readable on a public
    # GitHub repo — and canon holds NDA client identities and private rulings. It exists on the
    # author's machine and nowhere else. So on a fresh clone (CI) it is legitimately absent, and
    # this gate must degrade rather than crash: the classic-vs-case-facts.js comparison below is
    # the half that guards shipped surfaces, and it runs regardless. Skipping is announced loudly
    # rather than silently, because a check that quietly stops checking is worse than no check.
    if not os.path.exists(os.path.join(root, "CANONICAL-FACTS.md")):
        print("NOTE  CANONICAL-FACTS.md is absent (expected on a fresh clone — it is untracked on\n"
              "      purpose, see .gitignore). The canon-vs-page comparison is SKIPPED; the\n"
              "      classic-vs-case-facts.js comparison still runs and still fails the build.")
        return {}
    md = read(root, "CANONICAL-FACTS.md")
    out = {}
    for line in md.split("\n"):
        m = re.match(r"^\|\s*([1-6])\s*\|", line)
        if not m:
            continue
        key = CANON_ROW[m.group(1)]
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        role = re.search(r"Role:\s*([^·|]+)", cells[4])
        role_txt = role.group(1) if role else None
        if role_txt:
            # drop trailing editorial annotation: "(per PM-receipts retitle, …)", "via Equal Experts…"
            role_txt = re.split(r"\s*\(|\s+via\s+", role_txt)[0]
        # the headline metric is the bolded run in the 4th cell
        head = re.search(r"\*\*(.+?)\*\*", cells[3])
        out[key] = {
            "title": _norm(cells[1]),
            "tag": _norm(cells[2]),
            "role": _norm(role_txt) if role_txt else None,
            "headline": _norm(head.group(1)) if head else None,
        }
    return out


def check_against_canon(root, facts):
    """CANONICAL-FACTS.md is the ultimate authority; data/case-facts.js must not drift from it.

    Without this, the single source could be edited to say anything and every downstream gate
    would happily agree with it — one confident, self-consistent, wrong answer on every surface."""
    findings = []
    canon = parse_canon(root)
    # An EMPTY dict means canon is legitimately absent (fresh clone / CI) and parse_canon has
    # already said so. That is a skip, not drift. A PARTIAL parse still means the table's shape
    # changed under us and the check has gone blind — that must still fail.
    if not canon:
        return findings
    if len(canon) != 6:
        findings.append(f"canon: parsed {len(canon)} case rows from CANONICAL-FACTS §3, expected 6 "
                        f"— the locked table's shape changed and this check has gone blind")
        return findings

    for key, c in canon.items():
        f = facts["cases"].get(key)
        if f is None:
            findings.append(f"{key}: in CANONICAL-FACTS but missing from data/case-facts.js")
            continue

        if _norm(f["title"]) != c["title"]:
            findings.append(f"{key}: TITLE is {_norm(f['title'])!r} in data/case-facts.js, "
                            f"CANONICAL-FACTS says {c['title']!r}")

        # canon's tag may carry extra qualifiers ("· full case", "/ public"); require the source's
        # tag to be contained in canon's, not identical to it
        if _norm(f["tag"]).lower() not in c["tag"].lower():
            findings.append(f"{key}: TAG is {_norm(f['tag'])!r} in data/case-facts.js, "
                            f"not found within CANONICAL-FACTS' {c['tag']!r}")

        src_role = dict((m[0], m[1]) for m in f["meta"]).get("Role")
        if c["role"] and src_role:
            if _norm(src_role).lower() != c["role"].lower():
                findings.append(f"{key}: ROLE is {_norm(src_role)!r} in data/case-facts.js, "
                                f"CANONICAL-FACTS says {c['role']!r}")

        if c["headline"]:
            metrics_blob = _norm(" ".join(v + " " + l for v, l in f["metrics"]))
            if c["headline"].lower() not in metrics_blob.lower():
                findings.append(f"{key}: canon's HEADLINE metric {c['headline']!r} does not appear "
                                f"in data/case-facts.js metrics")
    return findings


def check(root, facts_override=None, classic_override=None):
    """Compare each CLASSIC page against the single source in data/case-facts.js.

    The BOOK is no longer compared field-by-field: since the single-source refactor it RENDERS
    from that file, so book-vs-source drift is structurally impossible. What can still drift is
    the hand-written classic HTML, and the provenance rule — so that is what is checked."""
    facts = facts_override if facts_override is not None else load_facts(root)
    book = read(root, "book/portfolio.js")
    findings = []

    # canon outranks the single source; if they disagree, canon is right
    findings += check_against_canon(root, facts)

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

    # sensitivity B2: the single source contradicting CANONICAL-FACTS, which outranks it.
    # Only meaningful when canon is present — it is untracked on purpose, so on a fresh clone
    # this probe would be testing a comparison that is legitimately switched off. Skipping the
    # PROBE when its subject is absent is correct; skipping it silently would not be, so it says so.
    # Both canon-outranks-source probes live together: they test a comparison that is only
    # possible when CANONICAL-FACTS.md is present, and it is untracked on purpose so a fresh
    # clone legitimately has none. Skipping the probes whose SUBJECT is absent is correct;
    # doing it silently would not be, so it prints. Any future canon probe belongs in here.
    if os.path.exists(os.path.join(root, "CANONICAL-FACTS.md")):
        mutatedC = copy.deepcopy(facts)
        mutatedC["cases"]["adtech"]["title"] = "Programmatic Advertising Platform (rebranded)"
        if not any("TITLE" in f and "CANONICAL-FACTS" in f for f in check(root, facts_override=mutatedC)):
            return False, "SENSITIVITY: a source title contradicting CANONICAL-FACTS was not caught"

        mutatedD = copy.deepcopy(facts)
        for m in mutatedD["cases"]["fintech"]["meta"]:
            if m[0] == "Role":
                m[1] = "Consultant"
        if not any("ROLE" in f and "CANONICAL-FACTS" in f for f in check(root, facts_override=mutatedD)):
            return False, "SENSITIVITY: a source role contradicting CANONICAL-FACTS was not caught"
    else:
        print("[calibration] the 2 canon-outranks-source probes were SKIPPED — CANONICAL-FACTS.md\n"
              "              is not in this checkout (untracked on purpose). Every other probe ran.")

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

    return True, ("sensitivity OK (classic drift, canon-vs-source title + role, lying "
                  "provenance, book bypassing the source) "
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
