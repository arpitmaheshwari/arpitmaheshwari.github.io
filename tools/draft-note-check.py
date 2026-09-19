#!/usr/bin/env python3
"""draft-note-check.py — an instruction to the writer, published as writing.

WHY THIS EXISTS. On 2026-09-19 an outside review of the live site found this rendered
as the pull-quote in the PTC case study, the page carrying the strongest business
outcomes on the whole portfolio:

    Keep the quote to one line — 'Perpetual was 100% of revenue when I started;
    twelve months on, 64% of new bookings were subscription.' — and move the
    grandfathered-cohort and pricing-stayed-with-leadership sentences into the body
    paragraph above it.

A note Arpit wrote to himself, shipped where a reader expects the strongest line on
the page. It had been live long enough for a stranger to find it.

WHY EVERY EXISTING GATE PASSED IT. Nothing about it is broken. It is grammatical
British English, correctly spelled, properly nested in a valid <blockquote>, at good
contrast, at the right size, with sane leading, no overflow and no console error. Every
gate here asks whether a thing is malformed. None asks whether the sentence is ADDRESSED
TO THE READER OR TO THE AUTHOR — and that is a different question, invisible to all of
them. prose-check is the nearest neighbour and it is a style checker: it grades how a
sentence is written, never who it is written to.

THE SIGNATURE. Not a banned word — "keep", "move" and "cut" are ordinary English, and
a case study about killing four products says "cut" legitimately. What marks an editing
note is an IMPERATIVE EDITING VERB aimed at a DOCUMENT-STRUCTURE NOUN: keep the QUOTE,
move the SENTENCE, shorten this PARAGRAPH, swap the HEADING. A reader is never told to
move a paragraph. Both halves must appear close together in one visible run of text.

Also flagged outright, needing no pairing: TODO, FIXME, TK, XXX, lorem ipsum, and
square-bracket placeholders — none of which is ever deliberate published prose.

    python3 tools/draft-note-check.py            # every shipped page
    python3 tools/draft-note-check.py --selftest # plant one, require RED, remove it

CANNOT SEE: a note that reads as ordinary prose ("this section needs work" without a
structure noun), a stale FACT (a number that silently went out of date — no grammar
marks that), text baked into an image, or a sentence that is merely wrong rather than
unfinished. It finds unfinished DRAFTING, not unfinished THINKING.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gatelib import pages, visible_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# An instruction aimed at whoever is editing the document.
EDIT_VERB = (r"keep|move|shorten|cut|trim|tighten|rewrite|reword|replace|swap|delete|"
             r"remove|merge|split|expand|add|drop|fix|redo|revisit|reorder|renumber")
# ...aimed at a part of the document. A reader is never asked to move a paragraph.
DOC_NOUN = (r"quote|pull-?quote|paragraph|para|sentence|section|heading|subhead|caption|"
            r"eyebrow|standfirst|line|copy|wording|blurb|intro|footnote|callout|bullet|"
            r"list|title|label|figure|table")

INSTRUCTION = re.compile(
    r"\b(?:%s)\s+(?:the|this|that|these|those|a|an|it|them)?\s*"
    r"(?:\w+[\s-]){0,3}(?:%s)s?\b" % (EDIT_VERB, DOC_NOUN), re.I)

# Markers that are never deliberate prose, whatever surrounds them.
BARE = re.compile(r"\b(TODO|FIXME|TKTK|XXX+|lorem ipsum)\b|\bTK\b|\[(?:placeholder|tbd|todo|xx)\]",
                  re.I)

SENTINEL = "__DRAFT_NOTE_CANARY__"


def findings(text):
    out = []
    for raw in text.split("\n"):
        s = raw.strip()
        if len(s) < 12:
            continue
        m = BARE.search(s)
        if m:
            out.append(("draft marker", m.group(0), s))
            continue
        m = INSTRUCTION.search(s)
        if m:
            out.append(("editing instruction", m.group(0), s))
    return out


def scan():
    bad = []
    for p in pages():
        text = visible_text(open(os.path.join(ROOT, p), encoding="utf-8").read())
        for kind, hit, line in findings(text):
            bad.append((p, kind, hit, line))
    return bad


def selftest():
    """A check I have not watched go RED is not evidence."""
    planted = f"Shorten this paragraph before it ships {SENTINEL}"
    hits = findings(planted)
    if not hits:
        print("  SELFTEST FAILED — a planted editing instruction was NOT detected.")
        return 1
    clean = ("Killing a product an executive sponsored is not a design decision. "
             "I cut four of them and kept the line that mattered.")
    if findings(clean):
        print(f"  SELFTEST FAILED — ordinary prose was flagged: {findings(clean)}")
        return 1
    print(f"  calibration OK — planted note caught ({hits[0][1]!r}), legitimate "
          f"prose using 'cut' and 'line' left alone")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if selftest():
        print("\nRefusing to report. An instrument that cannot fail is not evidence.")
        sys.exit(2)
    bad = scan()
    n = len(pages())
    for p, kind, hit, line in bad:
        print(f"  {kind.upper()} in {p}")
        print(f"    matched {hit!r}")
        print(f"    {line[:190]}")
    if bad:
        print(f"\n{len(bad)} draft note(s) published as content across {n} page(s). "
              f"A note to the author, read by a stranger, says the work is unfinished.")
        sys.exit(1)
    print(f"{n} page(s), 0 draft notes published as content.")
    print("CANNOT SEE: a note phrased as ordinary prose, a fact that has gone stale, "
          "text baked into an image, or a sentence that is wrong rather than unfinished.")
    sys.exit(0)


if __name__ == "__main__":
    main()
