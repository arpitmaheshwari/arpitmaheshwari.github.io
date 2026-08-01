#!/usr/bin/env python3
"""
VENDORED COPY — the cross-project master lives at
~/.claude/reference/tools/contrast-audit.py

This copy exists because CI checks out only this repository and cannot read ~/.claude.
If you change one, change both. `diff` them if the two ever disagree.
"""
"""
contrast-audit.py — WCAG contrast auditing measured from RENDERED PIXELS, not computed style.

WHY THIS EXISTS
    On 2026-07-31 a style-based contrast checker reported "clean" for eight consecutive QA rounds
    while the primary call-to-action on the most-shared page of a portfolio site sat at 1.18:1 —
    invisible. That checker read `getComputedStyle(el).backgroundColor` and walked up the DOM for the
    first opaque colour. The failing surface painted itself with a background-IMAGE (a gradient) over
    a transparent background-color, so the walk fell straight through to an unrelated ancestor and
    compared cream text against cream. It could not see the defect. Being more careful, or running it
    more times, would never have helped: the instrument had to change.

    This tool measures the real pixels behind every glyph box, so gradients, background images, blend
    modes, filters and stacked opacity are all handled by construction.

HOW IT MEASURES
    Two passes at identical geometry, both inside a same-origin wrapper that hosts the target in an
    iframe sized to the page's full height:
      Pass A — collect each leaf text node's colour, size, weight and rect.
      Pass B — screenshot with `color: transparent` forced everywhere, so the image shows the TRUE
               background under each glyph box. Sample a grid inside each rect, average, compare.

CALIBRATION IS NOT OPTIONAL
    Before reporting anything, the tool plants a ~1.1:1 "canary" element and confirms it gets flagged.
    If the canary is not caught, the tool prints nothing else and exits non-zero. An instrument that
    has never gone red is not evidence.

USAGE
    python3 contrast-audit.py URL [URL ...] [--widths 1440,1024,768] [--exempt "SELECTOR"]
    python3 contrast-audit.py --selftest URL          # calibration only

    --exempt marks text that legitimately has no contrast requirement (WCAG 1.4.3 exempts logotypes
    and incidental text). Exempt failures are still PRINTED — a silent exemption is how real defects
    hide. Requires a same-origin URL (http://localhost/... ), because it reads into the iframe.

REQUIREMENTS  Google Chrome (or set $CHROME), Pillow, pages served over http(s), and
              --docroot pointing at the directory that origin serves (defaults to cwd).
EXIT CODE     0 = calibrated and clean · 1 = failures found, or calibration did not go red.
"""
import argparse, json, html, math, re, os, subprocess, sys, tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
]

MAX_PAGE_PX = 24000          # Chrome refuses absurd window heights; clamp and report truncation.
CANARY_TEXT = "calibration canary do not ship"
# grey-on-grey, ~1.1:1 — unambiguously failing at any size.
CANARY_HTML = (
    "<div id='__ca_canary' style='position:absolute;left:0;top:0;z-index:2147483647;"
    "background:#777777;color:#8A8A8A;font-size:14px;font-weight:400;padding:6px'>"
    + CANARY_TEXT + "</div>"
)
HIDE_TEXT_CSS = ("*{color:transparent!important;text-shadow:none!important;"
                 "text-decoration-color:transparent!important;caret-color:transparent!important}")

# --------------------------------------------------------------------- colour

def _lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

def luminance(c):
    return 0.2126 * _lin(c[0]) + 0.7152 * _lin(c[1]) + 0.0722 * _lin(c[2])

def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def parse_rgb(css):
    n = [float(x) for x in re.findall(r"[\d.]+", css)]
    return tuple(int(round(v)) for v in n[:3]), (n[3] if len(n) > 3 else 1.0)

def required_ratio(px, weight):
    """WCAG 1.4.3: 3:1 for large text (>=24px, or >=18.66px bold); otherwise 4.5:1."""
    try:
        bold = int(weight) >= 700
    except (TypeError, ValueError):
        bold = str(weight).lower() in ("bold", "bolder")
    return 3.0 if (px >= 24 or (px >= 18.66 and bold)) else 4.5

# --------------------------------------------------------------------- chrome

def find_chrome():
    from shutil import which
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
        if which(c):
            return which(c)
    sys.exit("contrast-audit: Chrome not found. Set $CHROME.")

CHROME = os.environ.get("CHROME") or find_chrome()

IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

def gh(level, msg):
    """Emit a GitHub workflow annotation. These are readable via the PUBLIC check-runs
    annotations API, unlike run LOGS which require admin rights on the repo — so when this gate
    fails on CI, the reason is diagnosable from outside without a token. Learned the hard way:
    the first two CI failures of this gate reported nothing but 'exit code 1'."""
    if not IN_CI:
        return
    one_line = str(msg).replace("\r", "").replace("\n", "%0A")
    print(f"::{level}::{one_line}", flush=True)

def chrome(args, timeout=90):
    return subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         # --disable-dev-shm-usage: standard CI hardening. Chrome writes shared memory to /dev/shm,
         # which is small on many CI images; without this it can crash mid-render and return a
         # blank or partial screenshot, which this tool would then measure as garbage.
         "--disable-dev-shm-usage",
         "--force-device-scale-factor=1"] + args,
        capture_output=True, text=True, timeout=timeout)

# The wrapper runs in the PARENT document and reaches into the same-origin iframe. Nothing is
# injected into the target as a <script> (innerHTML-inserted scripts never execute — an earlier
# version of this tool failed its own calibration for exactly that reason).
WRAPPER = """<!doctype html><meta charset="utf-8">
<body style="margin:0;overflow:hidden;background:#000">
<iframe id="f" src="__URL__" style="border:0;display:block;width:__W__px;height:__H__px"></iframe>
<script>
var f = document.getElementById('f');
f.onload = function () {
  var d = f.contentDocument, w = f.contentWindow;
  if (__CANARY__) { var s = d.createElement('div'); s.innerHTML = __CANARY_HTML__;
                    d.body.appendChild(s.firstChild); }
  // Pin scroll-reveal elements to their SETTLED state in BOTH passes. Waiting for the fade is
  // unreliable — the reveal is triggered by a JS-added class, so at the moment we check,
  // getAnimations() is often still empty and we sample a half-faded element. On CI that surfaced
  // as a gold button measured at 33-61% opacity (1.91:1 and 3.89:1) whose settled value is 9.01:1.
  // Pinning removes the timing dependency instead of racing it. Note this deliberately does NOT
  // set `transition:none` globally — that stopped the gold background painting at all.
  if (__FORCE_VISIBLE__) {
    var fv = d.createElement('style');
    fv.textContent = __FORCE_VISIBLE__ +
      '{opacity:1!important;transform:none!important;visibility:visible!important;' +
      'transition-property:none!important}';
    d.head.appendChild(fv);
  }
  if (__HIDE__)   { var st = d.createElement('style'); st.textContent = __HIDE_CSS__;
                    d.head.appendChild(st); }
  // Wait for webfonts before measuring. Font metrics differ between macOS and Linux runners; if
  // layout is still shifting when we sample, a CI gate flakes and gets switched off. fonts.ready
  // removes the biggest source of that nondeterminism.
  var collect = function () {
    var out = [], EX = __EXEMPT__;
    d.querySelectorAll('body *').forEach(function (el) {
      // Collect any element owning a DIRECT non-empty text node — NOT only childless elements.
      // A `el.children.length === 0` test silently skips <button><span class=dot></span>Open…</button>,
      // which is precisely how the 1.18:1 call-to-action that motivated this tool escaped an earlier
      // version of this tool as well. Text beside a decorative child is still text.
      var own = '';
      for (var i = 0; i < el.childNodes.length; i++)
        if (el.childNodes[i].nodeType === 3) own += el.childNodes[i].nodeValue;
      if (!own.trim()) return;
      if (el.closest('script,style,[hidden],[aria-hidden="true"]')) return;
      var cs = w.getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) return;
      var r = el.getBoundingClientRect();
      if (r.width < 3 || r.height < 3) return;
      out.push({ t: own.trim().slice(0, 44), size: parseFloat(cs.fontSize),
                 wt: cs.fontWeight, color: cs.color,
                 ex: !!(EX && el.closest(EX)),
                 r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    });
    document.title = 'CA:' + JSON.stringify({ h: d.documentElement.scrollHeight, els: out });
  };
  // Wait for every running CSS transition/animation to FINISH before measuring, then settle.
  // Without this the tool races the page: on a slower CI runner it sampled a scroll-reveal gold
  // button mid-fade (~61% opacity over a dark page) and reported 3.89:1 against its dark label —
  // the settled value is 9.01:1. Three false failures on a page that was never wrong.
  // getAnimations() is the precise instrument here: it waits for the real end state instead of
  // suppressing animation (an earlier attempt to just force `transition:none` stopped the gold
  // background painting at all, turning three false failures into a different false failure).
  // Capped, because an infinite animation — the cover's pulsing dot — never resolves.
  // Jump every CSS animation straight to its end state before measuring. This is the general
  // form of the problem: the hero CTA is not `.reveal` at all — it is `.hero-cta-row` carrying an
  // inline `opacity:0; animation: reveal .4s ... .35s forwards`. A selector-based pin can never
  // enumerate every such element; finish() needs no selector and covers keyframe animations AND
  // transitions. Infinite animations (the book cover's pulsing dot) throw on finish() — skipped.
  var finishAll = function () {
    try {
      (d.getAnimations ? d.getAnimations() : []).forEach(function (an) {
        try { an.finish(); } catch (e) { /* infinite / unresolved — leave it running */ }
      });
    } catch (e) {}
  };
  var settleThen = function () {
    finishAll();
    var pending = [];
    try {
      pending = (d.getAnimations ? d.getAnimations() : []).map(function (an) {
        return an.finished.catch(function () {});
      });
    } catch (e) {}
    var done = false;
    var fire = function () {
      if (done) return;
      done = true;
      setTimeout(function () { finishAll(); collect(); }, __SETTLE__);
    };
    if (pending.length) { Promise.all(pending).then(fire, fire); }
    setTimeout(fire, 3000);   // hard cap: infinite/looping animations must not hang the run
    if (!pending.length) fire();
  };
  var go = function () { settleThen(); };
  if (d.fonts && d.fonts.ready) { d.fonts.ready.then(go, go); } else { go(); }
};
</script>
"""

def build_wrapper(url, w, h, *, canary=False, hide=False, exempt=None, settle=1400,
                  force_visible=None):
    return (WRAPPER
            .replace("__URL__", html.escape(url, quote=True))
            .replace("__W__", str(w)).replace("__H__", str(h))
            .replace("__CANARY__", "true" if canary else "false")
            .replace("__CANARY_HTML__", json.dumps(CANARY_HTML))
            .replace("__HIDE__", "true" if hide else "false")
            .replace("__HIDE_CSS__", json.dumps(HIDE_TEXT_CSS))
            .replace("__FORCE_VISIBLE__", json.dumps(force_visible) if force_visible else "null")
            .replace("__EXEMPT__", json.dumps(exempt) if exempt else "null")
            .replace("__SETTLE__", str(settle)))

DOCROOT = None   # set from --docroot; the directory served at the URL origin's root.

def run_pass(url, w, h, *, canary=False, hide=False, exempt=None, png=None,
             force_visible=None):
    """Run one measurement pass. Returns parsed data, True (for screenshots), or None on failure.

    The wrapper is written into DOCROOT and fetched over http from the SAME ORIGIN as the target, so
    reading into the iframe needs no --disable-web-security (which hung Chrome, and would have been
    a bad thing to normalise anyway)."""
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    fd, path = tempfile.mkstemp(suffix=".html", prefix="__ca_", dir=DOCROOT)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_wrapper(url, w, h, canary=canary, hide=hide, exempt=exempt,
                                   force_visible=force_visible))
        wrapper_url = origin + "/" + os.path.basename(path)
        args = ["--virtual-time-budget=9000", f"--window-size={w},{h}"]
        args += [f"--screenshot={png}"] if png else ["--dump-dom"]
        try:
            r = chrome(args + [wrapper_url])
        except subprocess.TimeoutExpired:
            return None
        if png:
            return True if os.path.exists(png) else None
        m = re.search(r"<title>CA:(.*?)</title>", r.stdout, re.S)
        return json.loads(html.unescape(m.group(1))) if m else None
    finally:
        if os.path.exists(path):
            os.unlink(path)

# ---------------------------------------------------------------------- audit

def audit(url, width, exempt=None, canary=False, force_visible=None):
    """Measure one URL at one width. Returns (rows, truncated_bool) or (None, False) on failure."""
    from PIL import Image
    probe = run_pass(url, width, 900, exempt=exempt, canary=canary, force_visible=force_visible)
    if not probe:
        return None, False
    full = min(max(int(probe["h"]) + 40, 900), MAX_PAGE_PX)
    truncated = int(probe["h"]) + 40 > MAX_PAGE_PX

    data = run_pass(url, width, full, exempt=exempt, canary=canary, force_visible=force_visible)
    if not data:
        return None, truncated
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "bg.png")
        if not run_pass(url, width, full, canary=canary, hide=True, exempt=exempt, png=png,
                        force_visible=force_visible):
            return None, truncated
        im = Image.open(png).convert("RGB")
        sx = im.width / float(width)
        rows = []
        for e in data["els"]:
            x, y, w, h = e["r"]
            pts = []
            for i in range(1, 6):
                for j in range(1, 4):
                    px, py = int((x + w * i / 6.0) * sx), int((y + h * j / 4.0) * sx)
                    if 0 <= px < im.width and 0 <= py < im.height:
                        pts.append(im.getpixel((px, py)))
            if not pts:
                continue
            bgc = tuple(sum(p[k] for p in pts) // len(pts) for k in range(3))
            fg, alpha = parse_rgb(e["color"])
            if alpha < 1:
                fg = tuple(int(round(f * alpha + b * (1 - alpha))) for f, b in zip(fg, bgc))
            need = required_ratio(e["size"], e["wt"])
            got = ratio(fg, bgc)
            rows.append({"width": width, "text": e["t"], "size": e["size"],
                         "fg": "#%02X%02X%02X" % fg, "bg": "#%02X%02X%02X" % bgc,
                         # FLOOR, never round: a true 4.4996 displayed as "4.50" against a 4.5 floor reads as a
                         # tool bug and gets dismissed. Flooring never overstates a passing value.
                         "ratio": math.floor(got * 100) / 100.0, "need": need,
                         "ok": got >= need, "exempt": e["ex"]})
        return rows, truncated

# ---------------------------------------------------------------- calibration

def selftest(url, width, force_visible=None):
    rows, _ = audit(url, width, canary=True, force_visible=force_visible)
    if rows is None:
        return False, "could not instrument the page at all (is it served same-origin over http?)"
    hits = [r for r in rows if r["text"].startswith(CANARY_TEXT[:18])]
    if not hits:
        return False, "planted canary was never measured — the auditor cannot see injected text"
    if all(h["ok"] for h in hits):
        return False, f"canary measured {hits[0]['ratio']}:1 yet was reported PASSING"
    return True, (f"planted canary correctly flagged at {hits[0]['ratio']}:1 "
                  f"(needs {hits[0]['need']}) — the instrument can go red")

# ------------------------------------------------------------------------ cli

def main():
    ap = argparse.ArgumentParser(description="Pixel-truth WCAG contrast audit.")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--widths", default="1440,1024,768")
    ap.add_argument("--exempt", default=None,
                    help='CSS selector for WCAG 1.4.3-exempt text, e.g. ".logo, .wordmark"')
    ap.add_argument("--docroot", default=os.getcwd(),
                    help="directory served at the URL origin root (default: cwd). The wrapper is "
                         "written here so it is same-origin with the pages under test.")
    ap.add_argument("--force-visible", default=None, metavar="SELECTOR",
                    help="CSS selector for scroll-reveal elements, pinned to their settled visible "
                         "state before measuring (e.g. '.reveal'). Removes the timing race against "
                         "a JS-triggered fade, which otherwise yields false failures on slow runners.")
    ap.add_argument("--selftest", action="store_true", help="run calibration only, then exit")
    ap.add_argument("--no-selftest", action="store_true",
                    help="skip calibration (a green result then proves nothing)")
    a = ap.parse_args()
    widths = [int(w) for w in a.widths.split(",")]
    global DOCROOT
    DOCROOT = os.path.abspath(a.docroot)
    if not os.path.isdir(DOCROOT):
        sys.exit(f"contrast-audit: --docroot is not a directory: {DOCROOT}")

    if not a.no_selftest:
        ok, msg = selftest(a.urls[0], widths[0], force_visible=a.force_visible)
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:
            print("\nRefusing to report results. An instrument that cannot fail is not evidence.")
            gh("error", f"contrast-audit CALIBRATION FAILED — {msg}. No contrast results were "
                        f"produced; the instrument itself is broken in this environment.")
            sys.exit(1)
        if a.selftest:
            sys.exit(0)

    failures = 0
    for url in a.urls:
        measured = 0
        bad, exempt_bad, notes = [], [], []
        for width in widths:
            rows, truncated = audit(url, width, exempt=a.exempt,
                                    force_visible=a.force_visible)
            if rows is None:
                notes.append(f"@{width}px could not be measured")
                continue
            measured += len(rows)
            bad += [r for r in rows if not r["ok"] and not r["exempt"]]
            exempt_bad += [r for r in rows if not r["ok"] and r["exempt"]]
            if truncated:
                notes.append(f"@{width}px page taller than {MAX_PAGE_PX}px — bottom NOT measured")
        failures += len(bad)
        print(f"\n{url}  —  {measured} text nodes measured at {widths}")
        if measured == 0:
            gh("error", f"contrast-audit measured ZERO text nodes on {url} — the page did not "
                        f"render or could not be instrumented in this environment. Notes: "
                        f"{'; '.join(notes) or 'none'}")
        for r in bad:
            print(f"  FAIL {r['ratio']:5.2f}/{r['need']}  {r['size']:>6}px  "
                  f"{r['fg']} on {r['bg']}  @{r['width']}px  {r['text']!r}")
        # Surface each failure as an annotation so a CI failure is diagnosable without log access.
        # Capped: annotations are rate-limited per run and a wall of them buries the signal.
        for r in bad[:15]:
            gh("error", f"CONTRAST {r['ratio']:.2f}:1 (needs {r['need']}) — {r['size']}px "
                        f"{r['fg']} on {r['bg']} @{r['width']}px — {url} — text: {r['text']!r}")
        if len(bad) > 15:
            gh("error", f"...and {len(bad) - 15} further contrast failures on {url} "
                        f"(see the step log for the full list).")
        for n in notes:
            gh("warning", f"contrast-audit on {url}: {n}")
        for r in exempt_bad:
            print(f"  exempt {r['ratio']:5.2f}  @{r['width']}px  {r['text']!r}  "
                  f"(declared 1.4.3-exempt — confirm that is true)")
        for n in notes:
            print(f"  NOTE  {n}")
        if not bad:
            print("  0 failures. Blind spots of this method: text inside <canvas>, <video>, "
                  "cross-origin iframes, and any state not reachable on load (hover, focus, open "
                  "menus) are NOT measured.")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
