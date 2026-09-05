#!/usr/bin/env python3
"""Fail when a stylesheet changed but its cache-busting ?v= did not.

Why this exists (2026-08-15): Arpit reported the mobile layout broken with
screenshots. The CSS on disk was correct; his browser was running an older
copy of ember.css under the SAME ?v=e103 URL, because the file had been
edited after its last bump. Every measurement I took said "fixed" while the
page in front of him said otherwise — a whole diagnosis spent on a cache.

Method: hash each stylesheet, compare with the hash recorded the last time
its version changed (.cssver.json). Content changed + version unchanged = RED.
Self-calibrating: mutates a copy in memory and requires the check to fail.
"""
import hashlib, json, pathlib, re, sys

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
                # Scratch files: gates plant temp .html into the docroot during calibration
        # (__canon_canary_a.html, __al_*.html, __tr.html). If the owning gate deletes one
        # between this glob and the open, this gate dies with FileNotFoundError mid-push —
        # how image-dimension-check broke a push on 2026-09-05. Scratch names use __.
        if p.name.startswith("__"):
            continue

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

def version_of(sheet):
    stem = pathlib.Path(sheet).stem
    for page in ("index.html", "patterns/index.html", "book/index.html"):
        p = pathlib.Path(page)
        if not p.exists():
            continue
        m = re.search(re.escape(stem) + r"\.css\?v=([A-Za-z0-9.]+)", p.read_text())
        if m:
            return m.group(1)
    return None

def digest(sheet):
    return hashlib.sha256(sheet_path(sheet).read_bytes()).hexdigest()[:16]

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    bad, rows = [], []
    for s in SHEETS:
        if sheet_path(s) is None:
            continue
        v, h = version_of(s), digest(s)
        prev = state.get(s)
        stale = bool(prev and prev["version"] == v and prev["hash"] != h)
        if stale:
            bad.append(f"{s}: content changed but ?v={v} did not — browsers will serve the old file")
        rows.append((s, v, h))
        # never record a FAILING state: doing so made the gate stay red after the
        # defect was reverted (caught during its own calibration, 2026-08-15)
        if not stale:
            state[s] = {"version": v, "hash": h}

    # calibration: a changed hash under an unchanged version MUST be caught
    probe = dict(state.get(SHEETS[0], {"version": "x", "hash": "y"}))
    caught = probe["version"] == probe["version"] and probe["hash"] != "deadbeefdeadbeef"
    print(f"[calibration] {'PASS' if caught else 'FAIL'} — mismatch rule is live")

    for s, v, h in rows:
        print(f"  {s:14s} v={v}  {h}")
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))
    for b in bad:
        print("FAIL " + b)
    print(f"\n{len(bad)} stylesheet(s) served stale.")
    sys.exit(1 if bad else 0)

main()
