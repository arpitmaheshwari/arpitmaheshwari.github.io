#!/usr/bin/env python3
"""Bump a stylesheet's cache-busting ?v= on EVERY page, whatever version each page is on.

Why this exists (bug 1): bumps were done with `sed s/v=eN/v=eN+1/`, which only touches
pages already on eN. Pages drifted onto different versions (e12 vs e26 in the wild), so a
bump silently missed most of the site and CSS fixes "did not apply" — twice.

Why it was rewritten (bug 2, 2026-08-16): it only ever knew about ember.css. Its docstring
said "the cache version", its name said "css", but a styles.css edit bumped nothing. Anyone
who edited styles.css, ran this, and trusted it shipped a stale stylesheet — the exact
failure tools/css-version-check.py was written to catch after it cost a whole diagnosis.
A tool that silently covers one of four inputs is worse than no tool, because it answers.

USAGE
    bump-css-version.py                      bump every sheet the gate reports STALE
    bump-css-version.py styles.css           force-bump one sheet
    bump-css-version.py ember.css styles.css force-bump several
    bump-css-version.py --all                force-bump every sheet present
    bump-css-version.py styles.css --version p99   set an explicit version (one sheet only)

Version strings are per-sheet and keep their own letter prefix (ember=e, styles=p, fonts=f),
discovered from the pages themselves rather than hardcoded — the next sheet added needs no
change here. The new number is max(existing)+1 across ALL pages, so drift converges upward
instead of forking.

STATE: this script never writes .cssver.json. tools/css-version-check.py is the single
writer of that file; it records a sheet's hash only once the sheet is NOT stale. Two writers
would race and re-introduce the "gate stays red after a revert" bug. Run the gate after this.
"""
import re, sys, json, pathlib, hashlib

def discover_sheets():
    """Every stylesheet the pages actually link with a ?v= cache key.

    This was a hardcoded list of four while the docstring above claimed the
    sheets were "discovered from the pages themselves". book/book.css was not
    on the list, so editing the book's styles bumped nothing and returning
    visitors were served the cached copy. A list that must be edited by hand
    is a list that will be wrong the first time someone adds a file — which is
    exactly what happened.
    """
    found = set()
    for p in pathlib.Path(".").rglob("*.html"):
        rel = p.as_posix()
        if rel.startswith((".", "node_modules", "prototypes/", "portfolio-sources/", "tests/")):
            continue
        for m in re.finditer(r'href="[^"]*?([A-Za-z0-9_-]+\.css)\?v=', p.read_text(encoding="utf-8")):
            found.add(m.group(1))
    return sorted(found)

def sheet_path(name):
    """Where a linked sheet actually lives.

    Discovery yields bare filenames as the pages link them, but book.css sits
    in book/. The old code did pathlib.Path("book.css").exists() -> False and
    skipped it without a word, which is why editing the book's styles bumped
    nothing. Resolve it, and if it genuinely cannot be found, SAY SO rather
    than continue past it.
    """
    p = pathlib.Path(name)
    if p.exists():
        return p
    for cand in pathlib.Path(".").rglob(name):
        s = cand.as_posix()
        if s.startswith((".", "node_modules", "prototypes/", "tests/")):
            continue
        return cand
    return None


SHEETS = discover_sheets()
STATE = pathlib.Path(".cssver.json")
# the three pages css-version-check.py reads a version from; a bump that misses all of
# them is invisible to the gate, so we assert against exactly this set
GATE_PAGES = ("index.html", "patterns/index.html", "book/index.html")


def pages():
    return [p for p in pathlib.Path(".").rglob("*.html")
            if not any(x.startswith(".") or x in ("prototypes", "node_modules", "portfolio-sources")
                       for x in p.parts)]


def versions_of(sheet, files):
    """Every ?v= value this sheet is referenced with, across the whole site."""
    stem = re.escape(pathlib.Path(sheet).stem)
    found = set()
    for p in files:
        found.update(re.findall(stem + r"\.css\?v=([A-Za-z0-9.]+)", p.read_text()))
    return found


def next_version(sheet, current):
    """Keep the sheet's own letter prefix; increment the highest number seen anywhere."""
    parsed = [(m.group(1), int(m.group(2)))
              for m in (re.fullmatch(r"([A-Za-z]*)(\d+)", v) for v in current) if m]
    if not parsed:
        # no numeric version to build on (or the sheet is referenced without ?v= at all)
        return pathlib.Path(sheet).stem[0] + "1"
    prefix = max(parsed, key=lambda t: t[1])[0]
    return f"{prefix}{max(n for _, n in parsed) + 1}"


def stale_sheets(files):
    """Sheets whose bytes changed since the version last recorded — the gate's own rule."""
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    out = []
    for s in SHEETS:
        path = sheet_path(s)
        if path is None:
            print(f"  {s:14s} LINKED BUT NOT FOUND — check the path")
            continue
        prev = state.get(s)
        if not prev:
            # never recorded: a sheet added since the state file was written.
            # Skipping silently is how book.css went unbumped for weeks.
            print(f"  {s:14s} not yet tracked — bumping so it starts being watched")
            out.append(s)
            continue
        cur = versions_of(s, files)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        if prev["version"] in cur and prev["hash"] != digest:
            out.append(s)
    return out


def bump(sheet, files, explicit=None):
    stem = re.escape(pathlib.Path(sheet).stem)
    current = versions_of(sheet, files)
    if not current:
        print(f"  {sheet:14s} SKIPPED — no ?v= reference found on any page")
        return None
    new = explicit or next_version(sheet, current)
    if current == {new}:
        print(f"  {sheet:14s} already on {new}, nothing to do")
        return new
    n = 0
    for p in files:
        s = p.read_text()
        s2 = re.sub(stem + r"\.css\?v=[A-Za-z0-9.]+", f"{pathlib.Path(sheet).stem}.css?v={new}", s)
        if s2 != s:
            p.write_text(s2)
            n += 1
    # A replace that matched nothing still "succeeds". Assert we actually moved the pages
    # the gate inspects, or this is a silent no-op wearing a success message.
    seen = versions_of(sheet, [pathlib.Path(g) for g in GATE_PAGES if pathlib.Path(g).exists()])
    assert n > 0, f"{sheet}: matched {sorted(current)} but wrote 0 files — aborting"
    assert seen in ({new}, set()), \
        f"{sheet}: gate pages still read {sorted(seen)}, expected {new} — aborting"
    print(f"  {sheet:14s} {sorted(current)} -> {new} on {n} page(s)")
    return new


def main():
    argv = sys.argv[1:]
    explicit = None
    if "--version" in argv:
        i = argv.index("--version")
        explicit = argv[i + 1]
        del argv[i:i + 2]
    force_all = "--all" in argv
    argv = [a for a in argv if a != "--all"]

    for a in argv:
        if a not in SHEETS:
            sys.exit(f"unknown sheet {a!r} — known: {', '.join(SHEETS)}")
    if explicit and len(argv) != 1:
        sys.exit("--version applies to exactly one sheet")

    files = pages()
    if argv:
        targets = argv
    elif force_all:
        targets = [s for s in SHEETS if sheet_path(s) is not None]
    else:
        targets = stale_sheets(files)
        if not targets:
            print("No stylesheet is stale — nothing to bump.")
            print("(Name a sheet, or pass --all, to bump anyway.)")
            return
        print(f"Stale per {STATE}: {', '.join(targets)}")

    for s in targets:
        bump(s, files, explicit)
    print("\nNow run: python3 tools/css-version-check.py   (it records the new hashes)")


main()
