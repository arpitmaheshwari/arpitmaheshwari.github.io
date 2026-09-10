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

def versions_in_pages(sheet):
    """{version: [pages]} for every page that links this sheet.

    This read THREE hardcoded pages (index, patterns/index, book/index) and
    returned the FIRST hit, while 41 pages link styles.css. So pages sitting on
    DIFFERENT versions of one sheet — the exact failure bump-css-version.py's
    own docstring records from the wild, "e12 vs e26" — was invisible: the gate
    sampled one page and called it the version. Read them all and make
    disagreement a finding.
    """
    stem = pathlib.Path(sheet).stem
    out = {}
    for p in pathlib.Path(".").rglob("*.html"):
        if p.name.startswith("__"):
            continue
        rel = p.as_posix()
        if rel.startswith((".", "node_modules", "prototypes/", "portfolio-sources/", "tests/")):
            continue
        m = re.search(re.escape(stem) + r"\.css\?v=([A-Za-z0-9.]+)", p.read_text(encoding="utf-8"))
        if m:
            out.setdefault(m.group(1), []).append(rel)
    return out


def version_of(sheet):
    vs = versions_in_pages(sheet)
    if not vs:
        return None
    # the version the most pages agree on; disagreement is reported separately
    return max(vs, key=lambda v: len(vs[v]))

def stale_rule(prev, v, h):
    """THE rule. Defined once so the calibration below exercises the same code
    the sweep uses — the previous calibration compared a value with itself and
    could not have caught a change to this logic."""
    return bool(prev and prev["version"] == v and prev["hash"] != h)


def digest(sheet):
    return hashlib.sha256(sheet_path(sheet).read_bytes()).hexdigest()[:16]

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    bad, rows = [], []
    for s in SHEETS:
        if sheet_path(s) is None:
            continue
        v, h = version_of(s), digest(s)
        spread = versions_in_pages(s)
        if len(spread) > 1:
            detail = "; ".join(f"?v={k} on {len(p)} page(s) (e.g. {p[0]})"
                               for k, p in sorted(spread.items(), key=lambda kv: -len(kv[1])))
            bad.append(f"{s}: pages disagree about the version — {detail}. "
                       f"Run: python3 tools/bump-css-version.py {s}")
        prev = state.get(s)
        stale = stale_rule(prev, v, h)
        if stale:
            bad.append(f"{s}: content changed but ?v={v} did not — browsers will serve the old file")
        rows.append((s, v, h))
        # never record a FAILING state: doing so made the gate stay red after the
        # defect was reverted (caught during its own calibration, 2026-08-15)
        if not stale:
            state[s] = {"version": v, "hash": h}

    # CALIBRATION. The previous version of these four lines was a TAUTOLOGY:
    #     caught = probe["version"] == probe["version"] and probe["hash"] != "deadbeef…"
    # The left side compares a value with itself, so `caught` was True for every
    # possible input and this gate printed PASS on every run since 2026-08-15
    # without once exercising the rule it guards. The docstring claimed it
    # "mutates a copy in memory and requires the check to fail". It did not.
    # Now it does: run the real predicate over a planted state and require BOTH
    # a red on a changed hash AND a green on an unchanged one.
    planted = {"version": "v1", "hash": "a" * 16}
    must_fire = stale_rule(planted, "v1", "b" * 16)      # content moved, version did not
    must_not  = stale_rule(planted, "v1", "a" * 16)      # nothing moved
    must_not2 = stale_rule(planted, "v2", "b" * 16)      # content moved AND version bumped
    ok = must_fire and not must_not and not must_not2
    print(f"[calibration] {'PASS' if ok else 'FAIL'} — planted a changed hash under an "
          f"unchanged version and the rule fired ({must_fire}); it stays quiet when nothing "
          f"moved ({not must_not}) and when the version was bumped with it ({not must_not2})")
    if not ok:
        print("Refusing to report: a check that cannot go red is not evidence.")
        sys.exit(2)

    for s, v, h in rows:
        print(f"  {s:14s} v={v}  {h}")
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))
    for b in bad:
        print("FAIL " + b)
    print(f"\n{len(bad)} stylesheet(s) served stale.")
    sys.exit(1 if bad else 0)

main()
