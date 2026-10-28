#!/usr/bin/env python3
"""resume-parity.py — keep the two résumés honest, and keep both readable by scanning software.

There are two résumé files and they are built from two different sources:
  resume.html    -> Arpit-Maheshwari-Resume.pdf   (the designed one, for people)
  make-resume.js -> Arpit-Maheshwari-Resume.docx  (the plain one, for job sites)

Nothing used to compare them, so they drifted: on 2026-10-28 the .docx was missing
two whole skills groups, repeated a sentence, said "Available · available on", and
carried a product count canon had retired in August. This checks the class of fault
rather than those four instances.

Exit 0 = clean, 1 = a defect, 2 = the check could not run (treat as a failure).
"""
import re
import subprocess
import sys
import zipfile
from pathlib import Path

# The two résumés live in the PRIVATE folio-private repo, gitignored here. This gate
# SKIPS rather than fails when it is not checked out — CI does not have it, the same
# way design-doc-mirror and canon-lint cannot see what lives there.
SRC = Path(__file__).resolve().parent.parent / "portfolio-sources"
PDF = SRC / "Arpit-Maheshwari-Resume.pdf"
DOCX = SRC / "Arpit-Maheshwari-Resume.docx"

# Claims locked in CANONICAL-FACTS.md §3. Both documents must carry every one of them,
# spelled identically — a figure that exists on only one surface is drift.
LOCKED = [
    "2 wks → 3 hrs", "£69,000", "60% faster", "3 wks → 4 days",
    "$1M / yr", "0% → 64%", "4M+", "150k learners", "550k+",
    "200 people", "4-person", "16 analysis dimensions",
    # the headline, spelled out — it is the line that lost every space in the PDF
    "Six systems. One platform. Two weeks → three hours.",
]

# Keyword blocks ATS scoring reads. Each must appear in both documents.
SKILL_GROUPS = ["AI product design", "Product & systems", "Design foundations",
                "Craft & tools", "Domains"]

# Each job title, with the opening words of the first achievement that belongs to it.
# In the PDF's text layer the achievement must appear AFTER its own title and BEFORE
# the next one. `position:relative` on a list item silently breaks this (Chrome paints
# positioned boxes last, so every bullet lands after Skills and Education).
ROLE_ORDER = [
    ("· Sahaj AI", "Turned the UK’s largest independent"),
    ("· PTC Inc.", "Consolidated five learning platforms"),
    ("· Equal Experts", "Shipped reward and offer screens"),
]

failures = []


def fail(msg):
    failures.append(msg)


def pdf_text():
    out = subprocess.run(["pdftotext", "-raw", str(PDF), "-"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print("CALIBRATION: pdftotext failed —", out.stderr.strip(), file=sys.stderr)
        sys.exit(2)
    return out.stdout


def docx_text():
    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        names = set(z.namelist())
    if any(n.startswith("word/header") or n.startswith("word/footer") for n in names):
        fail("DOCX: content in a header or footer — many parsers never read it")
    if "<w:tbl>" in xml:
        fail("DOCX: contains a table — a classic ATS parsing failure")
    if "w:txbxContent" in xml:
        fail("DOCX: contains a text box — its words are invisible to parsers")
    text = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", text)
    import html
    return html.unescape(text)


def check_fonts():
    out = subprocess.run(["pdffonts", str(PDF)], capture_output=True, text=True)
    if out.returncode != 0:
        print("CALIBRATION: pdffonts failed", file=sys.stderr)
        sys.exit(2)
    rows = out.stdout.splitlines()[2:]
    kinds = {" ".join(r.split()[1:3]) for r in rows if r.strip()}
    if not kinds:
        print("CALIBRATION: no embedded fonts found — pdffonts output unreadable",
              file=sys.stderr)
        sys.exit(2)
    for k in kinds:
        if "Type 3" in k:
            fail("PDF: a Type 3 font is embedded — scrambles copy-paste and some parsers "
                 "(cause: two weights of a variable font; see build-fonts.py)")


def check_reading_order(txt):
    flat = " ".join(txt.split())
    for i, (title, first_bullet) in enumerate(ROLE_ORDER):
        t = flat.find(title)
        b = flat.find(first_bullet)
        if t < 0:
            fail(f"PDF: job title {title!r} not in the text layer")
            continue
        if b < 0:
            fail(f"PDF: achievement {first_bullet!r} not in the text layer")
            continue
        if b < t:
            fail(f"PDF: the achievement {first_bullet!r} is read BEFORE its own job "
                 f"({title}) — a parser will attach it to the wrong employer")
        nxt = ROLE_ORDER[i + 1][0] if i + 1 < len(ROLE_ORDER) else None
        if nxt:
            n = flat.find(nxt)
            if 0 < n < b:
                fail(f"PDF: the achievement {first_bullet!r} is read after the NEXT job "
                     f"({nxt}) — a parser will attach it to the wrong employer")


def check_spacing(txt, where):
    """Chrome drops the spaces out of a text run when tracking is tightened on some
    faces, so a whole line extracts as one unreadable word. Catch any long run of
    letters with sentence punctuation inside it."""
    # dot followed by a capital = a sentence boundary that lost its space.
    # Lowercase after the dot is an email or a domain, not a defect.
    for m in re.finditer(r"[A-Za-z]{4,}\.[A-Z][a-z]{3,}", txt):
        fail(f"{where}: words run together in the text layer — {m.group(0)!r}")


def check_doubled_words(txt, where):
    """A separator between the two copies still reads as a stutter to a human:
    'Available · available on 4 weeks' notice' sat in the .docx for weeks because
    the first version of this rule only allowed whitespace between them."""
    # NOT dashes: "Product & systems — systems thinking" is the skills grammar,
    # not a stutter, and allowing "—" here made this rule cry wolf on it.
    for m in re.finditer(r"\b(\w{3,})[\s·|]+\1\b", txt, flags=re.I):
        fail(f"{where}: doubled word — {m.group(0)!r}")


def check_repeated_sentences(txt, where):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", txt) if len(s.strip()) > 60]
    seen = {}
    for s in sentences:
        key = re.sub(r"\W+", " ", s.lower()).strip()
        if key in seen:
            fail(f"{where}: the same sentence appears twice — {s[:70]!r}…")
        seen[key] = True


FIGURE = re.compile(r"\$\d[\d,.]*|£\d[\d,.]*|\d+%|\b\d+\s*→\s*\d+\b|\b\d+k\b")


def check_restated_facts(txt, where):
    """Verbatim-duplicate detection cannot see a fact restated in fresh words —
    the .docx carried 'mobile grew from 4% of sessions' in two consecutive PTC
    bullets, worded differently. Within ONE job, the same figure appearing in two
    different bullets means the fact is being told twice.
    (Across jobs, and between Selected Results and Experience, repetition is
    deliberate, so this deliberately only looks inside a single role.)"""
    blocks = re.split(r"(?=(?:Product & Design Lead|Designer \+ Front-End|Systems Analyst))", txt)
    for block in blocks:
        if len(block) < 200:
            continue
        role = block[:48]
        bullets = [b for b in re.split(r"(?<=[.])\s+(?=[A-Z])", block) if len(b) > 60]
        seen = {}
        for i, b in enumerate(bullets):
            for fig in set(FIGURE.findall(b)):
                if fig in seen and seen[fig] != i:
                    fail(f"{where}: {fig!r} is stated twice under {role.strip()!r} — "
                         f"the same fact told in two bullets")
                seen.setdefault(fig, i)


def main():
    if not SRC.is_dir():
        print("resume-parity: SKIP — portfolio-sources/ is not checked out")
        return 0
    for f in (PDF, DOCX):
        if not f.exists():
            print(f"CALIBRATION: {f.name} missing", file=sys.stderr)
            sys.exit(2)

    p, d = pdf_text(), docx_text()
    pf, df = " ".join(p.split()), " ".join(d.split())

    check_fonts()
    check_reading_order(p)
    check_spacing(pf, "PDF")
    check_spacing(df, "DOCX")
    check_doubled_words(pf, "PDF")
    check_doubled_words(df, "DOCX")
    check_repeated_sentences(pf, "PDF")
    check_repeated_sentences(df, "DOCX")
    check_restated_facts(pf, "PDF")
    check_restated_facts(df, "DOCX")

    for claim in LOCKED:
        in_p, in_d = claim in pf, claim in df
        if in_p and not in_d:
            fail(f"DRIFT: {claim!r} is on the PDF but not the .docx")
        elif in_d and not in_p:
            fail(f"DRIFT: {claim!r} is on the .docx but not the PDF")
        elif not in_p and not in_d:
            fail(f"MISSING: {claim!r} is on neither document")

    for group in SKILL_GROUPS:
        if group not in pf:
            fail(f"PDF: skills group {group!r} missing")
        if group not in df:
            fail(f"DOCX: skills group {group!r} missing — lost keyword coverage")

    # The masthead shows the socials as icons, which no parser can read, so BOTH
    # documents carry them spelled out in the closing line instead (2026-10-28).
    # Handles are locked in CANONICAL-FACTS.md §3.
    for handle in ("linkedin.com/in/arpitmaheshwariprofile",
                   "substack.com/@arpitmaheshwari",
                   "github.com/arpitmaheshwari"):
        if handle not in pf:
            fail(f"PDF: {handle} is not present as parseable text — an icon is not a URL")
        if handle not in df:
            fail(f"DOCX: {handle} is not present as parseable text")
    if "arpitmaheshwari88" in pf or "arpitmaheshwari88" in df:
        fail("The retired LinkedIn handle 'arpitmaheshwari88' is printed somewhere")

    if failures:
        print(f"resume-parity: {len(failures)} defect(s)")
        for f in failures:
            print("  ✗", f)
        return 1
    print("resume-parity: clean — both documents parse in order and carry the same claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# CANNOT SEE: whether a claim is TRUE (canon-lint's job, and it cannot reach these files
# either), whether the wording is good, or anything about the designed page as a human
# reads it. It checks that a machine reads both documents in order and that the two tell
# the same story.
