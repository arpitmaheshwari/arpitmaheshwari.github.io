#!/usr/bin/env python3
"""
asset-load-check — does every image on the page ACTUALLY RENDER?

WHY THIS EXISTS
On 2026-08-02 the method diagram on /process was found to have been a broken image.
assets/visuals/process-method.svg carried a literal angle-bracket tag inside a CSS comment
in its <style> block; that parses as markup, which makes the file invalid XML — and an SVG
loaded through an img element must be valid XML or the browser silently refuses to paint it.
naturalWidth was 0. Nothing caught it, for two reasons worth stating plainly:

  * every existing gate checks TEXT (canon-lint), CROSS-SURFACE AGREEMENT (case-sync) or
    COLOUR (contrast-audit). None of them asks whether a visual asset loaded at all.
  * the file's own layout had therefore never been seen by anyone, so nobody could notice
    that its labels collided either. A broken asset hides its own second defect.

A design portfolio that ships a broken diagram is worse off than one that ships a wrong
number, because the reader draws a conclusion about craft before reading a word.

WHAT IT CHECKS
  1. STATIC  — every .svg in the tree parses as XML. Catches the exact 2026-08-02 root cause
               with no browser, in milliseconds, and catches it in files no page references yet.
  2. RUNTIME — every <img> on the given pages reports naturalWidth > 0 in a real browser.
               Lazy-loading is defeated first (see below) so a below-the-fold image is never
               reported broken merely for being below the fold.

CALIBRATION (this tool refuses to report until it has gone red)
  * sensitivity: plants an <img> pointing at a file that does not exist, and a deliberately
    malformed .svg, and confirms BOTH are flagged.
  * precision: re-runs the same pages untouched and confirms they report nothing.
  A check that cannot fail is not evidence.

USAGE
  python3 tools/asset-load-check.py --docroot . URL [URL...]
  python3 tools/asset-load-check.py --docroot . --selftest URL      # calibration only
  python3 tools/asset-load-check.py --docroot . --static-only       # no browser needed

EXIT CODE   0 = calibrated and clean · 1 = broken assets found, or calibration did not go red.
"""
import argparse, html, json, os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
]

def find_chrome():
    from shutil import which
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
        if which(c):
            return which(c)
    return None

CHROME = os.environ.get("CHROME") or find_chrome()
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

def gh(level, msg):
    """GitHub workflow annotation — readable via the public check-runs API, unlike run logs."""
    if not IN_CI:
        return
    print(f"::{level}::{str(msg).replace(chr(13),'').replace(chr(10),'%0A')}", flush=True)

# --------------------------------------------------------------- 1. static SVG validity

def svg_xml_errors(root, extra_files=()):
    """Every .svg in the tree must parse as XML. Returns [(path, message)]."""
    bad = []
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip every dot-directory and node_modules. This deliberately excludes .git, .github
        # and .claude/worktrees — the last one holds full copies of the repo for background
        # tasks, and reporting a stale copy's SVG as a shipped defect would be a false alarm
        # that trains everyone to ignore this gate.
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        for fn in filenames:
            if fn.lower().endswith(".svg"):
                paths.append(os.path.join(dirpath, fn))
    paths.extend(extra_files)
    for p in sorted(set(paths)):
        try:
            ET.parse(p)
        except Exception as e:
            bad.append((os.path.relpath(p, root), str(e)))
    return bad, len(paths)

# --------------------------------------------------------------- 2. runtime image loading

WRAPPER = """<!doctype html><meta charset="utf-8">
<body style="margin:0;overflow:hidden;background:#111">
<iframe id="f" src="__URL__" style="border:0;display:block;width:__W__px;height:__H__px"></iframe>
<script>
// Runs in the PARENT and reaches into the same-origin iframe. Nothing is injected into the
// target as a <script> tag — innerHTML-inserted scripts never execute.
const CANARY = __CANARY__;
const out = m => { document.title = "AL:" + encodeURIComponent(JSON.stringify(m)); };
const f = document.getElementById("f");
f.addEventListener("load", async () => {
  try {
    const d = f.contentDocument;
    if (!d) return out({error: "no same-origin access to the target document"});

    if (CANARY) {
      // sensitivity probe: an image that cannot possibly resolve
      const c = d.createElement("img");
      c.id = "__al_canary"; c.src = "__asset_load_canary_does_not_exist.png";
      c.style.cssText = "position:absolute;left:0;top:0;width:10px;height:10px";
      d.body.appendChild(c);
    }

    // Defeat lazy-loading BEFORE measuring. A below-the-fold img[loading=lazy] legitimately
    // reports naturalWidth 0 until it nears the viewport; reporting that as "broken" would
    // make this gate cry wolf on exactly the pages it is meant to protect.
    d.querySelectorAll('img[loading="lazy"]').forEach(i => { i.loading = "eager"; });
    d.querySelectorAll("img").forEach(i => { if (!i.complete) { const s = i.src; i.src = ""; i.src = s; } });

    const settle = ms => new Promise(r => setTimeout(r, ms));
    await Promise.all([...d.images].map(i => i.complete ? null : new Promise(r => {
      i.addEventListener("load", r, {once:true});
      i.addEventListener("error", r, {once:true});
      setTimeout(r, 5000);                      // never hang the gate on one slow asset
    })));
    await settle(__SETTLE__);

    const rows = [...d.images].map(i => ({
      src: i.getAttribute("src") || "(no src)",
      alt: (i.getAttribute("alt") || "").slice(0, 60),
      w: i.naturalWidth, h: i.naturalHeight,
      lazy: i.getAttribute("loading") === "lazy",
    }));
    out({ total: rows.length, broken: rows.filter(r => !(r.w > 0)) });
  } catch (e) { out({error: String(e && e.message || e)}); }
});
</script>
"""

def chrome_run(args, timeout=90):
    return subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--disable-dev-shm-usage", "--force-device-scale-factor=1"] + args,
        capture_output=True, text=True, timeout=timeout)

def scan_page(url, docroot, *, canary=False, width=1440, height=2400, settle=700):
    """Load one URL in Chrome and report which <img> elements failed to paint."""
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    fd, path = tempfile.mkstemp(suffix=".html", prefix="__al_", dir=docroot)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(WRAPPER
                     .replace("__URL__", html.escape(url, quote=True))
                     .replace("__W__", str(width)).replace("__H__", str(height))
                     .replace("__CANARY__", "true" if canary else "false")
                     .replace("__SETTLE__", str(settle)))
        wrapper_url = origin + "/" + os.path.basename(path)
        try:
            r = chrome_run(["--virtual-time-budget=12000",
                            f"--window-size={width},{height}", "--dump-dom", wrapper_url])
        except subprocess.TimeoutExpired:
            return None
        m = re.search(r"<title>AL:(.*?)</title>", r.stdout, re.S)
        if not m:
            return None
        from urllib.parse import unquote
        return json.loads(unquote(html.unescape(m.group(1))))
    finally:
        if os.path.exists(path):
            os.unlink(path)

# --------------------------------------------------------------------- calibration

def calibrate(urls, docroot):
    """Prove the instrument can go red, and that it stays quiet when it should."""
    # (a) static sensitivity — a malformed SVG must be caught
    fd, bad_svg = tempfile.mkstemp(suffix=".svg", prefix="__al_canary_", dir=docroot)
    os.close(fd)
    with open(bad_svg, "w", encoding="utf-8") as fh:
        # the exact 2026-08-02 shape: a tag inside a style comment
        fh.write('<svg xmlns="http://www.w3.org/2000/svg"><style>/* <img> */</style></svg>')
    try:
        errs, _ = svg_xml_errors(docroot, extra_files=[bad_svg])
        if not any(os.path.basename(bad_svg) in e[0] for e in errs):
            return False, "planted a malformed SVG and the static check did not flag it"
    finally:
        os.unlink(bad_svg)

    if not urls:
        return True, "static only — sensitivity OK (malformed SVG caught)"

    # (b) runtime sensitivity — a missing image must be caught
    probe = scan_page(urls[0], docroot, canary=True)
    if probe is None or "error" in probe:
        return False, f"could not read the page during calibration ({probe})"
    if not any("canary_does_not_exist" in b["src"] for b in probe["broken"]):
        return False, "planted a missing image and the runtime check did not flag it"

    # (c) runtime precision — untouched, the same page must report nothing
    clean = scan_page(urls[0], docroot, canary=False)
    if clean is None or "error" in clean:
        return False, f"could not re-read the page during calibration ({clean})"
    if clean["broken"]:
        # This is not a calibration failure to hide — it means the page is genuinely broken.
        return True, ("sensitivity OK (missing image + malformed SVG caught); precision could not "
                      "be confirmed because the page ALREADY has broken assets — reported below")
    return True, "sensitivity OK (missing image + malformed SVG caught) + precision OK (clean page reports nothing)"

# --------------------------------------------------------------------------- main

def discover_pages(base="http://localhost:8000"):
    import subprocess
    out = subprocess.run("git ls-files '*.html'", shell=True, capture_output=True, text=True).stdout
    urls = []
    for f in out.split():
        if f.startswith(("prototypes/", "assets/", "portfolio-sources/")):
            continue
        urls.append(base + "/" if f == "index.html"
                    else f"{base}/{f[:-10]}" if f.endswith("/index.html")
                    else f"{base}/{f}")
    return sorted(set(urls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true",
                    help="discover every shipped page from git (same rationale as "
                         "contrast-audit --all: a typed list stops covering new pages)")
    ap.add_argument("--docroot", default=os.getcwd())
    ap.add_argument("--selftest", action="store_true", help="run calibration only, then exit")
    ap.add_argument("--no-selftest", action="store_true")
    ap.add_argument("--static-only", action="store_true", help="SVG XML validity only; no browser")
    a = ap.parse_args()
    if a.all:
        a.urls = discover_pages()
        print(f"  --all: discovered {len(a.urls)} shipped pages")
    docroot = os.path.abspath(a.docroot)

    if not a.static_only and a.urls and not CHROME:
        print("asset-load-check: Chrome not found (set $CHROME) — falling back to --static-only",
              file=sys.stderr)
        a.static_only = True

    urls = [] if a.static_only else a.urls

    if not a.no_selftest:
        ok, why = calibrate(urls, docroot)
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {why}\n")
        if not ok:
            gh("error", f"asset-load-check calibration failed: {why}")
            print("Refusing to report results. A check that cannot fail is not evidence.")
            return 1
        if a.selftest:
            return 0

    failures = 0
    unmeasured = 0

    svg_bad, svg_n = svg_xml_errors(docroot)
    print(f"static: {svg_n} SVG file(s) parsed as XML")
    for p, e in svg_bad:
        failures += 1
        print(f"  BROKEN  {p}\n          {e}")
        gh("error", f"{p}: invalid XML — renders as a broken image via img ({e})")
    if not svg_bad:
        print("  all valid.")

    for url in urls:
        res = scan_page(url, docroot)
        if res is None or "error" in res:
            failures += 1
            unmeasured += 1
            # Distinguish "could not look" from "asset is broken": a dead local server was
            # reported as "1 broken asset" on 2026-08-03, sending me after a defect that
            # did not exist.
            print(f"\n{url}\n  COULD NOT MEASURE — no response from the page."
                  f"\n  Is the local server running? (raw: {res})")
            gh("error", f"{url}: asset-load-check could not measure the page")
            continue
        print(f"\n{url}  —  {res['total']} image(s) checked")
        for b in res["broken"]:
            failures += 1
            print(f"  BROKEN  naturalWidth=0  {b['src']}")
            print(f"          alt: {b['alt'] or '(none)'}")
            gh("error", f"{url}: broken image {b['src']}")
        if not res["broken"]:
            print("  all rendered.")

    print("\nNOT covered by this gate: CSS background-image, images injected by JS after settle,")
    print("srcset/<picture> variants the browser did not choose, <video> posters, cross-origin")
    print("assets, and whether a rendered image is the CORRECT one — only that something painted.")
    if not failures:
        print("\nResult: clean — every asset painted.")
    elif unmeasured == failures:
        print(f"\nResult: INCONCLUSIVE — {unmeasured} page(s) could not be measured "
              f"(server down?). This is NOT a broken-asset finding.")
    else:
        print(f"\nResult: {failures - unmeasured} broken asset(s)"
              + (f" and {unmeasured} unmeasurable page(s)" if unmeasured else "")
              + ". A broken diagram reads as broken craft.")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
