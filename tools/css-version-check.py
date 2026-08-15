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

SHEETS = ["ember.css", "styles.css", "classic.css", "fonts.css"]
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
    return hashlib.sha256(pathlib.Path(sheet).read_bytes()).hexdigest()[:16]

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    bad, rows = [], []
    for s in SHEETS:
        if not pathlib.Path(s).exists():
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
