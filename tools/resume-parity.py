#!/usr/bin/env python3
"""resume-parity.py — keep every résumé file honest, and readable by scanning software.

Since 2026-11-05 there is ONE content source, portfolio-sources/resume-content.js, and ONE
résumé rendered from it by make-resume.js (resume.html printed to PDF by make-pdfs.py, and
the plain .docx for job-site uploads):

  Arpit-Maheshwari-Resume.pdf + .docx          THE résumé ("Product Manager & Designer"), on the site
  Arpit-Maheshwari-Resume-Design.pdf + .docx   backup for design-only roles, private folder only

Before that, the designed PDF and the .docx were two hand-written sources and drifted
(2026-10-28: the .docx was missing two skills groups, repeated a sentence, said
"Available · available on", and carried a retired product count). One source removes the
cause; this gate still checks the class of fault, because a PDF is printed from a browser
and a browser can lose spaces, reorder blocks, embed Type 3 fonts, or hyphenate a word
across a line so the text layer reads "dataheavy".

Exit 0 = clean, 1 = a defect, 2 = the check could not run (treat as a failure).
"""
import html
import re
import subprocess
import sys
import zipfile
from pathlib import Path

# The résumés live in the PRIVATE folio-private repo, gitignored here. This gate SKIPS
# rather than fails when it is not checked out — CI does not have it.
SRC = Path(__file__).resolve().parent.parent / "portfolio-sources"
RESUMES = {   # name -> (file base, rendered page it was printed from)
    "resume": (SRC / "Arpit-Maheshwari-Resume", "resume.html"),
    "design": (SRC / "Arpit-Maheshwari-Resume-Design", "resume-design.html"),
}
RETIRED = [SRC / "Arpit-Maheshwari-Resume-PM.pdf", SRC / "Arpit-Maheshwari-Resume-PM.docx",
           SRC / "resume-pm.html"]   # the "-PM" naming, dropped 2026-11-05; must not come back
SITE_ROOT = SRC.parent
SITE_COPY = SRC.parent / "Arpit-Maheshwari-Resume.pdf"   # linked from the homepage

# Claims locked in CANONICAL-FACTS.md §3, in the résumé's PLAIN spelling (Arpit's call,
# 2026-11-05: no arrows on a document a parser reads first). Both files.
LOCKED = [
    "two weeks to three hours", "£69,000", "60% faster", "three weeks to four days",
    "$1M a year", "0% to 64%", "4M+", "150k learners", "550k+",
    "200 people", "4-person", "16 analysis dimensions",
    "100% of UK bookings", "Solution Consultant",          # employer title, canon §title honesty
    "4 weeks’ notice",
]

# Scanner-hostile glyphs: an arrow or a curly-quote headline is noise to keyword matching.
BANNED = {"→": "arrow", "←": "arrow", "“": "quote-as-headline", "”": "quote-as-headline"}

# Keyword blocks ATS scoring reads. Each must appear in both files.
SKILL_GROUPS = ["Product management", "AI product design", "Product design", "Engineering & domains"]  # order differs per résumé
SECTIONS = ["Professional Summary", "Highlights", "Professional Experience", "Skills", "Education"]

# Each job title, with the opening words of the first achievement that belongs to it.
# In the PDF's text layer the achievement must appear AFTER its own title and BEFORE
# the next one. `position:relative` on a list item silently breaks this (Chrome paints
# positioned boxes last, so every bullet lands after Skills and Education).
ROLE_ORDER = [
    ("· Sahaj AI", "£400M revenue"),   # in the first Sahaj bullet of BOTH résumés; "Talon Outdoor" alone also sits in the design summary
    ("· PTC Inc.", "Consolidated five independent learning products"),
    ("· Equal Experts", "Co-designed and hand-coded the front-end"),
]

failures = []


def fail(msg):
    failures.append(msg)


def pdf_text(pdf):
    out = subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True, text=True)
    if out.returncode != 0:
        print("CALIBRATION: pdftotext failed —", out.stderr.strip(), file=sys.stderr)
        sys.exit(2)
    return out.stdout


def docx_text(docx, where):
    with zipfile.ZipFile(docx) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        names = set(z.namelist())
    if any(n.startswith("word/header") or n.startswith("word/footer") for n in names):
        fail(f"{where}: content in a header or footer — many parsers never read it")
    if "<w:tbl>" in xml:
        fail(f"{where}: contains a table — a classic ATS parsing failure")
    if "w:txbxContent" in xml:
        fail(f"{where}: contains a text box — its words are invisible to parsers")
    text = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def check_fonts(pdf, where):
    out = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True)
    if out.returncode != 0:
        print("CALIBRATION: pdffonts failed", file=sys.stderr)
        sys.exit(2)
    rows = out.stdout.splitlines()[2:]
    kinds = {" ".join(r.split()[1:3]) for r in rows if r.strip()}
    if not kinds:
        print("CALIBRATION: no embedded fonts found — pdffonts output unreadable", file=sys.stderr)
        sys.exit(2)
    for k in kinds:
        if "Type 3" in k:
            fail(f"{where}: a Type 3 font is embedded — scrambles copy-paste and some parsers "
                 "(cause: two weights of a variable font; see build-fonts.py)")


def check_reading_order(txt, where):
    flat = " ".join(txt.split())
    for i, (title, first_bullet) in enumerate(ROLE_ORDER):
        t, b = flat.find(title), flat.find(first_bullet)
        if t < 0:
            fail(f"{where}: job title {title!r} not in the text layer"); continue
        if b < 0:
            fail(f"{where}: achievement {first_bullet!r} not in the text layer"); continue
        if b < t:
            fail(f"{where}: the achievement {first_bullet!r} is read BEFORE its own job "
                 f"({title}) — a parser will attach it to the wrong employer")
        nxt = ROLE_ORDER[i + 1][0] if i + 1 < len(ROLE_ORDER) else None
        if nxt and 0 < flat.find(nxt) < b:
            fail(f"{where}: the achievement {first_bullet!r} is read after the NEXT job "
                 f"({nxt}) — a parser will attach it to the wrong employer")


def check_spacing(txt, where):
    """Chrome drops the spaces out of a text run when tracking is tightened on some
    faces, so a whole line extracts as one unreadable word."""
    for m in re.finditer(r"[A-Za-z]{4,}\.[A-Z][a-z]{3,}", txt):
        fail(f"{where}: words run together in the text layer — {m.group(0)!r}")


def check_hyphen_breaks(txt, where, vocabulary):
    """A hyphenated compound broken at a line end comes out of the text layer as one word
    with the hyphen gone ("data-heavy" -> "dataheavy"), and a keyword search for the real
    word then fails. Every word in the PDF must exist in the content source."""
    for w in sorted({w for w in re.findall(r"[A-Za-z][A-Za-z’'-]*[A-Za-z]", txt)}):
        if w.lower() not in vocabulary:
            fail(f"{where}: {w!r} is not a word on the rendered page — a line break ate a hyphen, "
                 "or the PDF was printed from a stale .html")


def check_doubled_words(txt, where):
    for m in re.finditer(r"\b(\w{3,})[\s·|]+\1\b", txt, flags=re.I):
        fail(f"{where}: doubled word — {m.group(0)!r}")


def check_repeated_sentences(txt, where):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", txt) if len(s.strip()) > 60]
    seen = set()
    for s in sentences:
        key = re.sub(r"\W+", " ", s.lower()).strip()
        if key in seen:
            fail(f"{where}: the same sentence appears twice — {s[:70]!r}…")
        seen.add(key)


FIGURE = re.compile(r"\$\d[\d,.]*|£\d[\d,.]*|\d+%|\b\d+k\b")


def check_restated_facts(txt, where):
    """Within ONE job, the same figure in two different bullets means the fact is told twice.
    (Summary vs Experience repetition is deliberate; this only looks inside a role.)"""
    body = txt.split("Professional Experience", 1)[-1]   # Highlights repeat figures on purpose
    blocks = re.split(r"(?=(?:Solution Consultant ·|Solution Consultant  \||Product & Design Lead|Designer and Front-End|Systems Analyst))", body)
    for block in blocks:
        if len(block) < 200:
            continue
        role = block[:40].strip()
        bullets = [b for b in re.split(r"(?<=[.])\s+(?=[A-Z])", block) if len(b) > 60]
        seen = {}
        for i, b in enumerate(bullets):
            for fig in set(FIGURE.findall(b)):
                if fig in seen and seen[fig] != i:
                    fail(f"{where}: {fig!r} is stated twice under {role!r} — the same fact told in two bullets")
                seen.setdefault(fig, i)


def vocabulary(page_name):
    """Words of the rendered page (tags stripped), NOT of the source files: a code comment in
    the template that describes the defect ("parsers read it as dataheavy") put the defect's
    own spelling into the word list, and a planted "dataheavy" sailed through (2026-11-05)."""
    page = (SRC / page_name).read_text(encoding="utf-8")
    page = re.sub(r"<style>.*?</style>", "", page, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z’'-]*[A-Za-z]|[A-Za-z]", text)}


def check_resume(name, base, vocab):
    pdf, docx = base.with_suffix(".pdf"), base.with_suffix(".docx")
    for f in (pdf, docx):
        if not f.exists():
            print(f"CALIBRATION: {f.name} missing", file=sys.stderr)
            sys.exit(2)
    P, D = f"{name}/PDF", f"{name}/DOCX"
    p, d = pdf_text(pdf), docx_text(docx, D)
    pf, df = " ".join(p.split()), " ".join(d.split())

    check_fonts(pdf, P)
    check_reading_order(p, P)
    check_hyphen_breaks(p, P, vocab)
    for txt, where in ((pf, P), (df, D)):
        check_spacing(txt, where)
        check_doubled_words(txt, where)
        check_repeated_sentences(txt, where)
        check_restated_facts(txt, where)
        for glyph, why in BANNED.items():
            if glyph in txt:
                fail(f"{where}: contains {glyph!r} ({why}) — plain words only on a scanned document")
        for sec in SECTIONS:
            if sec not in txt:
                fail(f"{where}: section {sec!r} missing — a parser needs the standard heading")
        for group in SKILL_GROUPS:
            if group not in txt:
                fail(f"{where}: skills group {group!r} missing — lost keyword coverage")
        for handle in ("linkedin.com/in/arpitmaheshwariprofile", "substack.com/@arpitmaheshwari",
                       "github.com/arpitmaheshwari"):
            if handle not in txt:
                fail(f"{where}: {handle} is not present as parseable text — an icon is not a URL")
        if "arpitmaheshwari88" in txt:
            fail(f"{where}: the retired LinkedIn handle 'arpitmaheshwari88' is printed")

    for claim in LOCKED:
        in_p, in_d = claim in pf, claim in df
        if in_p and not in_d:
            fail(f"{name}: DRIFT — {claim!r} is on the PDF but not the .docx")
        elif in_d and not in_p:
            fail(f"{name}: DRIFT — {claim!r} is on the .docx but not the PDF")
        elif not in_p and not in_d:
            fail(f"{name}: MISSING — {claim!r} is on neither file")


def main():
    if not SRC.is_dir():
        print("resume-parity: SKIP — portfolio-sources/ is not checked out")
        return 0
    for name, (base, page) in RESUMES.items():
        check_resume(name, base, vocabulary(page))

    # The homepage links a copy of THE résumé at the repo root; it must be the same bytes.
    main_pdf = RESUMES["resume"][0].with_suffix(".pdf")
    if not SITE_COPY.exists() or SITE_COPY.read_bytes() != main_pdf.read_bytes():
        fail("site copy ../Arpit-Maheshwari-Resume.pdf differs from portfolio-sources/ — run make-pdfs.py resume")
    # The design backup stays private (Arpit, 2026-11-05): never a copy at the site root.
    for stray in SITE_ROOT.glob("Arpit-Maheshwari-Resume-*"):
        fail(f"{stray.name} sits at the site root — the design backup is private, delete the copy")
    for f in RETIRED:
        if f.exists():
            fail(f"{f.name} exists — the '-PM' naming was retired; the PM résumé IS Arpit-Maheshwari-Resume")

    if failures:
        print(f"resume-parity: {len(failures)} defect(s)")
        for f in failures:
            print("  ✗", f)
        return 1
    print("resume-parity: clean — both résumés, both files, parse in order and carry the same claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# CANNOT SEE: whether a claim is TRUE (canon-lint's job, and it cannot reach these files
# either), whether the wording is good, how the designed page looks to a human, or whether a
# page's content ran into the footer (make-pdfs.py measures that before it prints).
