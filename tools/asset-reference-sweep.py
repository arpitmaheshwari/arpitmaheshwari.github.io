#!/usr/bin/env python3
"""
asset-reference-sweep.py — diff what the site REFERENCES against what the site HAS.

Two questions, opposite directions, both invisible to every other gate here:
  DANGLING — a reference to a file that does not exist. asset-load-check catches this only for
             <img> on pages it visits; it cannot see CSS url(), preload hrefs, JS fetches,
             srcset candidates the browser didn't pick, or references on pages nobody scanned.
  ORPHAN   — a file in assets/ that nothing references. Dead weight in the repo and in any deploy.

CALIBRATION
    --selftest plants a reference to a file that cannot exist and confirms it is reported. A sweep
    that has never gone red is not evidence that there is nothing to find.

WHAT IT STRUCTURALLY CANNOT SEE
    * references built at runtime by string concatenation ('assets/' + name + '.png')
    * assets referenced only from files outside the scanned set (docs, external sites, email)
    * whether a referenced asset is the RIGHT one, or whether an orphan is intentionally staged
    * anything inside a binary (a filename baked into a PNG is invisible to every text search)
"""
import os, re, sys, argparse
from urllib.parse import urlsplit, unquote

SCAN_EXT = {".html", ".css", ".js", ".json", ".txt", ".xml", ".md", ".svg"}
ASSET_EXT = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".avif", ".gif", ".ico",
             ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".webm", ".pdf", ".js", ".css"}
SKIP_DIRS = {"prototypes", "portfolio-sources", "node_modules", ".git", ".claude",
             ".playwright-mcp", ".requirements", ".github"}

# EXTENSION-DRIVEN, not key-driven. The first version keyed off href|src|url(|srcset|content
# and therefore could not see book/portfolio.js, which carries its assets as plain object values
# (`img: "../assets/visuals/pattern-loop.svg"`). That one missed SYNTAX reported ~20 genuinely
# referenced SVGs as orphans (measured 2026-08-16). Anything that looks like a path ending in an
# asset extension counts as a reference, whatever syntax surrounds it. A false candidate that
# resolves is harmless; a missed reference turns a real asset into a phantom orphan.
# DANGLING uses a STRICT regex, ORPHAN uses the greedy one above. The two questions have
# opposite failure costs. For orphans, over-matching is free (a stray match just means a file is
# correctly called "referenced"), and under-matching invents phantom orphans. For dangling refs,
# over-matching is the whole problem: the greedy pattern matched filenames written in PROSE inside
# comments and .md files ("Ported from monograph.css §7") and reported 42 phantom broken links.
# Only a real attribute or url() position can actually make a browser fetch something.
STRICT_REF_RE = re.compile(
    r"""(?:href|src|srcset|poster|xlink:href)\s*=\s*["']([^"']+)["']"""
    r"""|url\(\s*["']?([^"')]+?)["']?\s*\)""", re.I)
PROSE_EXT = {".md", ".txt"}

REF_RE = re.compile(
    r"""([A-Za-z0-9_./\-~%@][A-Za-z0-9_./\-~%@:]*\."""
    r"""(?:png|jpe?g|svg|webp|avif|gif|ico|woff2?|ttf|otf|mp4|webm|pdf|js|css)\b[^"'\s>),;]*)""",
    re.I)


SELF_ORIGINS = ["https://arpitmaheshwari.com", "http://arpitmaheshwari.com",
                "https://www.arpitmaheshwari.com", "http://localhost:8000"]


def scan_files(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.startswith("_") or f.startswith("tmp"):
                continue
            if os.path.splitext(f)[1].lower() in SCAN_EXT:
                yield os.path.join(dirpath, f)


def collect_refs(root, extra_text=None):
    """-> {abs_asset_path: [(scanfile, lineno, raw)]}, [(scanfile, lineno, raw)] unresolved"""
    found, dangling = {}, []
    items = [(p, open(p, encoding="utf-8", errors="replace").read()) for p in scan_files(root)]
    if extra_text:
        items.append(extra_text)
    for path, text in items:
        prose = os.path.splitext(path)[1].lower() in PROSE_EXT
        for ln, line in enumerate(text.splitlines(), 1):
            strict_hits = {(m.group(1) or m.group(2) or "").strip()
                           for m in STRICT_REF_RE.finditer(line)}
            for m in REF_RE.finditer(line):
                raw = m.group(1)
                if not raw:
                    continue
                # only a strict attribute/url() position can 404 a real browser request
                loadable = (not prose) and any(raw in h or h in raw for h in strict_hits if h)
                for cand in raw.split(","):
                    cand = cand.strip().split()[0] if cand.strip() else ""
                    # og:image and canonical refs are written as ABSOLUTE urls on the site's own
                    # origin. Skipping every absolute url reported all 34 og-images as orphans
                    # (measured 2026-08-16). Strip the site origin and resolve the rest locally.
                    for origin in SELF_ORIGINS:
                        if cand.startswith(origin):
                            cand = "/" + cand[len(origin):].lstrip("/")
                            break
                    if not cand or cand.startswith(("http://", "https://", "data:", "mailto:",
                                                    "tel:", "#", "javascript:")):
                        continue
                    clean = unquote(urlsplit(cand).path)
                    if os.path.splitext(clean)[1].lower() not in ASSET_EXT:
                        continue
                    base = root if clean.startswith("/") else os.path.dirname(path)
                    target = os.path.normpath(os.path.join(base, clean.lstrip("/")))
                    if os.path.exists(target):
                        found.setdefault(os.path.realpath(target), []).append((path, ln, cand))
                    elif loadable:
                        dangling.append((path, ln, cand, target))
    return found, dangling


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--assets", default="assets")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--site", default="https://arpitmaheshwari.com",
                    help="the site's own absolute origin; refs to it resolve locally")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    if a.selftest:
        planted = ("<<planted-canary>>",
                   '<img src="assets/__sweep_canary_does_not_exist.png">\n'
                   '<style>body{background:url(assets/__sweep_canary2.svg)}</style>')
        _, dang = collect_refs(root, extra_text=planted)
        hits = [d for d in dang if "__sweep_canary" in d[2]]
        ok_dangling = len(hits) == 2
        print(f"[calibration] dangling: {'PASS' if ok_dangling else 'FAIL'} — planted 2 "
              f"impossible refs, caught {len(hits)}")
        for h in hits:
            print(f"    caught: {h[2]}")
        # ORPHAN DIRECTION needs its own canary, and one canary is not enough: the failure mode
        # is dropping a whole reference SYNTAX, which makes real files look orphaned. The first
        # version of this calibration probed a single asset referenced by href= and passed while
        # the sweep was blind to JS object values. Probe EVERY syntax the repo uses.
        # Probe with an asset that REALLY EXISTS and ask whether the sweep counts it as
        # referenced (the `found` map) — not whether it lands in the dangling list. Those are
        # different questions, and conflating them made this calibration go red for the wrong
        # reason the moment dangling gained a strict-position filter.
        real = None
        for dp, _d, fs in os.walk(os.path.join(root, a.assets)):
            for f in sorted(fs):
                # a filename containing a SPACE cannot be matched by any URL-shaped regex
                # (assets/Group 1.png picked itself as the probe and made all 8 syntaxes look
                # blind, 2026-08-16). Probe with a normally-named file.
                if f.endswith(".png") and not f.startswith(".") and " " not in f:
                    real = os.path.relpath(os.path.realpath(os.path.join(dp, f)), root)
                    break
            if real: break
        if not real:
            print("[calibration] orphan: FAIL — no probe asset available"); return 1
        rp = os.path.realpath(os.path.join(root, real))
        syntaxes = {
            "src=":      f'<img src="/{real}">',
            "href=":     f'<link href="/{real}">',
            "css url()": f'body{{background:url(/{real})}}',
            "srcset":    f'<img srcset="/{real} 1x, /{real} 2x">',
            "js key:":   f'const c={{img:"/{real}"}};',
            "js concat": f'el.src = "/{real}";',
            "absolute":  f'<meta content="https://arpitmaheshwari.com/{real}">',
            "versioned": f'<img src="/{real}?v=3">',
        }
        missed = []
        for name, snippet in syntaxes.items():
            fnd, _dg = collect_refs(root, extra_text=("<<cal>>", snippet))
            # the probe file may be referenced by the real site too; that would mask a blind
            # spot. Confirm the SNIPPET itself is what produced the hit.
            hits = fnd.get(rp, [])
            if not any(src == "<<cal>>" for src, _ln, _c in hits):
                missed.append(name)
        ok_orphan = not missed
        print(f"[calibration] orphan: {'PASS' if ok_orphan else 'FAIL'} — "
              f"{len(syntaxes)-len(missed)}/{len(syntaxes)} reference syntaxes seen"
              + (f"; BLIND TO: {', '.join(missed)}" if missed else ""))
        return 0 if (ok_dangling and ok_orphan) else 1

    found, dangling = collect_refs(root)

    print("=== DANGLING REFERENCES (file referenced, does not exist) ===")
    if not dangling:
        print("  none")
    for path, ln, cand, target in sorted(dangling):
        print(f"  {os.path.relpath(path, root)}:{ln}  ->  {cand}")

    adir = os.path.join(root, a.assets)
    orphans = []
    for dirpath, dirs, files in os.walk(adir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.startswith("."):
                continue
            p = os.path.realpath(os.path.join(dirpath, f))
            if p not in found:
                orphans.append((os.path.getsize(p), os.path.relpath(p, root)))
    print(f"\n=== ORPHANS in {a.assets}/ (nothing references them) ===")
    tot = 0
    for size, rel in sorted(orphans, reverse=True):
        tot += size
        print(f"  {size/1024:8.0f}KB  {rel}")
    if not orphans:
        print("  none")
    else:
        print(f"  --- {len(orphans)} file(s), {tot/1024/1024:.2f} MB")

    print("\nCANNOT SEE: runtime-concatenated paths, refs from unscanned files, whether an asset "
          "is the CORRECT one, filenames baked into binaries.")
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
