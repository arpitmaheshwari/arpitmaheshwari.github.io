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

# Guarantee the server these gates assume. Every one of them hard-codes
# http://localhost:8000 and none checked it was there; when it was not, they did not report
# "no server", they reported findings (see cdp.ensure_server). Idempotent: reuses a server
# that is already listening, so a dev server is never disturbed or double-bound.
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
# Trackers are refused for every browser this repo drives — see cdp.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG
import sys
import os

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
]

VIEWPORT_H = 900             # a REAL viewport: 100vh sections must lay out as a reader sees them.
MAX_PAGE_PX = 24000          # Chrome refuses absurd window heights; clamp and report truncation.
CANARY_TEXT = "calibration canary do not ship"
# grey-on-grey, ~1.1:1 — unambiguously failing at any size.
CANARY_HTML = (
    "<div id='__ca_canary' style='position:absolute;left:0;top:0;z-index:2147483647;"
    "background:#777777;color:#8A8A8A;font-size:14px;font-weight:400;padding:6px'>"
    + CANARY_TEXT + "</div>"
)
# ":root *" not "*": the hide rule must WIN ties against class-level color:..!important
# (the theme-swap extraction moved inline colors into single-class !important rules, which
# beat a zero-specificity hide rule — text polluted its own background samples and six
# phantom contrast failures appeared on elements that render identically; measured 2026-08-13).
HIDE_TEXT_CSS = (":root *{color:transparent!important;text-shadow:none!important;"
                 "text-decoration-color:transparent!important;caret-color:transparent!important}"
                 # SVG <text> is painted by `fill`, NOT by `color`, so the rule above left every
                 # label inside an inlined diagram STILL DRAWN in the background pass — and the
                 # tool then sampled the glyph as if it were its own ground. On ptc.html that read
                 # the label 'IoTU' as #2C2722 on #5A544B (1.97:1, a failure) when the tile behind
                 # it is cream #EEE4CE and the true ratio is about 11:1. Every SVG label on the
                 # site was measured this way. Scoped to text/tspan: filling the SHAPES would
                 # erase the very background we are trying to photograph.
                 ":root svg text,:root svg tspan{fill:transparent!important}")

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
        [CHROME, "--headless", NO_TRACKING_FLAG, "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
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
      // SVG <text>/<tspan> is painted by `fill`, NOT `color`. Reading `color` here reported the
      // INHERITED page ink for every label inside an inlined SVG artifact — 344 phantom failures
      // across six case studies, each claiming cream-on-cream while the element actually painted
      // a dark warm grey. It held CI red for four days and hid whatever was really broken.
      // `fill` can be a url()/gradient paint-server; those are not flat colours, so skip rather
      // than guess (a paint-server needs pixel sampling, which is a different instrument).
      var ink = cs.color;
      if (el.ownerSVGElement || el.namespaceURI === 'http://www.w3.org/2000/svg') {
        var f = cs.fill;
        if (!f || f === 'none' || f.indexOf('url(') === 0) return;
        ink = f;
      }
      // GRADIENT TEXT is painted by the BACKGROUND, not by `color`. `background-clip:text` with
      // color:transparent survives the pass-B hide rule untouched (that rule only sets `color`),
      // so pass B samples the glyph's own paint and calls it "background" — foreground and
      // background come back identical and the ratio is EXACTLY 1.00. The 404 headline read
      // 1.00 that way on 2026-08-16 while actually rendering at 7.5-8.5:1. An exactly-1.00
      // reading is the signature of this instrument failing, never of a real defect, so refuse
      // to guess: flag the node as UNMEASURABLE and say what would be needed instead.
      /* WCAG's 3:1 large-text allowance is about PAINTED size. computed fontSize for SVG
         text is in USER UNITS, so a 40px label inside a viewBox rendered at 0.385 paints
         at 15.4px — and this gate graded it on the LENIENT threshold, exactly backwards.
         Real case: 'The Act / Review / Ignore Rule' was judged 1.29 against 3.0 when it
         owed 4.5. getScreenCTM gives the true element-to-screen scale. */
      function paintedSize(el, cs) {
        var px = parseFloat(cs.fontSize);
        if (el.ownerSVGElement && el.getScreenCTM) {
          var m = el.getScreenCTM();
          if (m) {
            var sc = Math.sqrt(Math.abs(m.a * m.d - m.b * m.c));
            if (sc > 0 && isFinite(sc)) return px * sc;
          }
        }
        return px;
      }
      var clip = cs.webkitBackgroundClip || cs.backgroundClip;
      var fill = cs.webkitTextFillColor;
      var transparentInk = /rgba\(0, 0, 0, 0\)|transparent/.test(fill || '')
                        || /rgba\(0, 0, 0, 0\)|transparent/.test(ink || '');
      if (clip === 'text' && transparentInk) {
        out.push({ t: own.trim().slice(0, 44), size: paintedSize(el, cs),
                   wt: cs.fontWeight, color: ink, unmeasurable: 'gradient text (background-clip:text)',
                   ex: !!(EX && el.closest(EX)),
                   r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
        return;
      }
      out.push({ t: own.trim().slice(0, 44), size: paintedSize(el, cs),
                 wt: cs.fontWeight, color: ink,
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

# The iframe wrapper that used to RENDER the page was removed on 2026-08-30, when audit()
# moved to CDP. WRAPPER itself is KEPT: collect_js() extracts the measurement JS from it,
# so it is the single source of that logic rather than a page that is rendered any more.

# ---------------------------------------------------------------- page probe
# The measurement JS is EXTRACTED from WRAPPER rather than retyped, so there is exactly one
# copy of logic that took several rounds to get right (SVG fill vs color, painted size via
# getScreenCTM, gradient text, own-text-node collection). If the anchors ever move this
# raises rather than silently measuring nothing.
_COLLECT_START = "var collect = function () {"
_COLLECT_END = "document.title = 'CA:'"


def collect_js(exempt=None):
    i = WRAPPER.find(_COLLECT_START)
    j = WRAPPER.find(_COLLECT_END)
    if i < 0 or j < 0 or j <= i:
        raise RuntimeError("contrast-audit: could not extract the collect body from WRAPPER — "
                           "the anchors moved. Fix this rather than measuring nothing.")
    body = WRAPPER[i + len(_COLLECT_START):j]
    body = body.replace("__EXEMPT__", json.dumps(exempt) if exempt else "null")
    return ("(function(){var d=document,w=window;" + body +
            "return {h:d.documentElement.scrollHeight,els:out};})()")

DOCROOT = None   # accepted for compatibility; unused since audit() drives the page over CDP
                 # and no longer writes a wrapper file into the served tree.

# ---------------------------------------------------------------------- audit

def audit(url, width, exempt=None, canary=False, force_visible=None):
    """Measure one URL at one width. Returns (rows, truncated_bool) or (None, False) on failure.

    ONE browser, ONE layout, a REALISTIC viewport, and a full-page capture over CDP.

    What this replaced, and why: the tool used to load the page in an IFRAME sized to the
    page's own height, then screenshot that. Pages here use 100vh sections, so the page
    height depends on the viewport height and sizing the iframe to the page just grows the
    page again — there is no fixed point. The capture was therefore sized from a 900px
    probe while the content laid out taller, and every node below the image was dropped:
    198 of 231 homepage text nodes at 1440px, on EVERY run, reported as "UNMEASURED ...
    contrast is UNKNOWN, not passing" beside a "0 failures" verdict. The message even
    contradicted itself ("page 10417px tall, screenshot 10417px") because it printed the
    intended height, not the height the content actually needed.

    Holding the viewport at a real 900px removes the feedback loop entirely: the page lays
    out once, the way a reader sees it, and Page.captureScreenshot(captureBeyondViewport)
    photographs the whole scrollable document WITHOUT resizing anything. Both passes now run
    against the SAME loaded page, so the rects and the pixels cannot disagree.
    """
    from PIL import Image
    import base64, io as _io
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cdp

    with cdp.Browser() as br:
        br.viewport(width, VIEWPORT_H)
        try:
            br.navigate(url, settle=2.2)
        except Exception:
            return None, False
        if canary:
            br.eval("(function(){var s=document.createElement('div');s.innerHTML=%s;"
                    "document.body.appendChild(s.firstChild);})()" % json.dumps(CANARY_HTML))
        if force_visible:
            br.eval("(function(){var st=document.createElement('style');st.textContent=%s+"
                    "'{opacity:1!important;transform:none!important;visibility:visible!important;"
                    "transition-property:none!important}';document.head.appendChild(st);})()"
                    % json.dumps(force_visible))
        # Same settle discipline as the wrapper had: webfonts, then running animations.
        br.eval("document.fonts && document.fonts.ready", await_promise=False)
        # RACED against a deadline, never awaited outright. /book/ is a React app with a
        # looping animation, so a bare await on getAnimations().finished never resolves and
        # the CDP socket times out after 90s — the audit hung on the book page every run.
        # A settle wait must be bounded: the point is to avoid sampling mid-fade, not to
        # prove the page ever stops moving.
        br.eval("(async()=>{const deadline=new Promise(r=>setTimeout(r,1800));"
                "const settled=(async()=>{try{await document.fonts.ready;}catch(e){}"
                "try{await Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>0)));}"
                "catch(e){}})();"
                "await Promise.race([settled,deadline]);})()", await_promise=True)
        br.pump(0.6)
        br.eval("window.scrollTo(0,0)")          # rects are then document coordinates
        data = br.eval_json(collect_js(exempt))
        if not data or not data.get("els"):
            return None, False
        full = int(data["h"])
        truncated = full > MAX_PAGE_PX

        # Pass B: the SAME page, ink removed, so what is photographed is the true ground.
        br.eval("(function(){var st=document.createElement('style');st.textContent=%s;"
                "document.head.appendChild(st);})()" % json.dumps(HIDE_TEXT_CSS))
        br.pump(0.35)
        shot = br.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=True)
        im = Image.open(_io.BytesIO(base64.b64decode(shot["data"]))).convert("RGB")

    sx = im.width / float(width)
    rows = []
    # SILENT DROP GUARD. Every node whose sample points fall outside the captured image used to
    # be skipped by a bare `continue`, and the printed total was len(rows) — so a screenshot
    # shorter than the page reported "32 text nodes measured" on a homepage that really has 224,
    # and its "0 failures" verdict covered only the first screen (measured 2026-08-16).
    # A node that could not be sampled is an UNMEASURED node, and must be said out loud.
    dropped = []
    for e in data["els"]:
        if e.get("unmeasurable"):
            rows.append({"width": width, "text": e["t"], "size": e["size"],
                         "fg": "-", "bg": "-", "ratio": 0.0,
                         "need": required_ratio(e["size"], e["wt"]),
                         "ok": True, "exempt": e["ex"],
                         "unmeasurable": e["unmeasurable"]})
            continue
        x, y, w, h = e["r"]
        # DENSITY SCALES WITH THE BOX. A fixed 5x3 grid is 15 samples, which on a short label
        # ('IoTU', 24x13px) lands mostly ON the glyph and its antialiased edge, so the winning
        # bucket was edge-blend #5A544B instead of the cream tile #EEE4CE underneath — a
        # 1.97:1 false failure on text that really runs about 11:1.
        cols = max(5, min(17, int(w / 6) or 5))
        rows_n = max(3, min(9, int(h / 4) or 3))
        pts = []
        for i in range(1, cols + 1):
            for j in range(1, rows_n + 1):
                px = int((x + w * i / (cols + 1.0)) * sx)
                py = int((y + h * j / (rows_n + 1.0)) * sx)
                if 0 <= px < im.width and 0 <= py < im.height:
                    pts.append(im.getpixel((px, py)))
        if not pts:
            # OFF-CANVAS BY DESIGN is not the same as UNMEASURED. A skip link is parked above
            # the document (y = -100) until it is focused, so it has no pixels to sample and
            # never will on load. Reporting that as "contrast UNKNOWN, not passing" printed a
            # permanent false alarm on every page, on every run — and a warning that is always
            # on is one nobody reads. The focused state is covered by interaction-state-check,
            # which forces :focus-visible.
            if y + h <= 0 or x + w <= 0:
                rows.append({"width": width, "text": e["t"], "size": e["size"],
                             "fg": "-", "bg": "-", "ratio": 0.0,
                             "need": required_ratio(e["size"], e["wt"]),
                             "ok": True, "exempt": e["ex"],
                             "unmeasurable": "off-canvas until focused (skip link)"})
                continue
            dropped.append(e["t"])
            continue
        # The MEAN of a grid inside a glyph box is not the background — it is the background
        # blended with however much of the glyph the grid happened to land on. On bold 16px
        # text in a small chip that is ~30% coverage, which dragged a real 8.72:1 label down
        # to a reported 3.96 and sent me darkening colours that were never wrong. The MODE is
        # the honest estimator: on any solid ground most sampled pixels ARE the ground, and
        # the glyph pixels are the minority that the mean was quietly folding in.
        # Quantised to 8 levels per channel first, so antialiased near-matches count together.
        fg, alpha = parse_rgb(e["color"])
        # The GROUND is the mode of the pixels that are NOT the ink. Glyph and antialiased
        # edge pixels are a systematic contaminant, not noise, so dropping the ones close to
        # the known ink removes them by construction instead of hoping the mode outvotes them.
        # If almost every sample is ink-like there is no ground to find and the text really IS
        # low-contrast — so fall back to all samples rather than discard the evidence.
        near_ink = lambda p: sum(abs(int(p[k]) - int(fg[k])) for k in range(3)) < 60
        ground_pts = [p for p in pts if not near_ink(p)]
        if len(ground_pts) < max(3, len(pts) // 4):
            ground_pts = pts
        buckets = {}
        for pnt in ground_pts:
            key = tuple(v // 32 for v in pnt)
            buckets.setdefault(key, []).append(pnt)
        winner = max(buckets.values(), key=len)
        bgc = tuple(sum(p[k] for p in winner) // len(winner) for k in range(3))
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
    if dropped:
        rows.append({"width": width, "text": "", "size": 0, "fg": "-", "bg": "-",
                     "ratio": 0.0, "need": 0, "ok": True, "exempt": False,
                     "dropped": dropped,
                     "geom": f"page {full}px tall, screenshot {im.height}px "
                             f"({im.width}x{im.height} at sx={sx:.2f})"})
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

def discover_pages(base="http://localhost:8000"):
    """Every tracked .html a visitor can reach. Archives, templates and the private repo out."""
    import subprocess
    out = subprocess.run("git ls-files '*.html'", shell=True, capture_output=True, text=True).stdout
    urls = []
    # .split() breaks on any filename containing a space (e.g. prototypes/reference-concepts/
    # "Theme 1 - Warm Gallery.dc.html") — it shreds ONE path into several fake single-word
    # "files" ('1', '-', 'Warm', ...) that pass the prototypes/ exclusion (only the FIRST
    # fragment starts with "prototypes/"), so they get audited as real pages and 404.
    # Measured 2026-08-11: this is what actually broke CI run 31526918220 ("localhost:8000/1").
    for f in out.splitlines():
        if f.startswith(("prototypes/", "assets/", "portfolio-sources/")):
            continue
        # Meta-refresh redirect stubs (lab/hitl.html, lab/trustlayer.html) have no real
        # content to audit — and auditing one is actively harmful: this tool loads the
        # target in a same-origin iframe and samples it after a fixed settle delay, so the
        # stub's own <meta http-equiv="refresh"> can navigate the iframe to its destination
        # DURING that window. The result is destination-page text (measured 2026-08-13:
        # loop.html's calibration demo — "600ms", "Was right", "Underconfident") reported
        # under the STUB's URL, intermittently, because it's a timing race against the
        # stub's own navigation. CI run #49 failed on exactly this. Skip stubs outright.
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                if 'http-equiv="refresh"' in fh.read():
                    continue
        except OSError:
            pass
        urls.append(base + "/" if f == "index.html"
                    else f"{base}/{f[:-10]}" if f.endswith("/index.html")
                    else f"{base}/{f}")
    return sorted(set(urls))


def main():
    ap = argparse.ArgumentParser(description="Pixel-truth WCAG contrast audit.")
    ap.add_argument("urls", nargs="*")
    # Enumerate, never trust a typed list. On 2026-08-07 the CI list named 9 pages by hand, so
    # 11 shipped pages had NEVER been contrast-checked — including lab/loop.html, the largest
    # page in the Lab. A hand-maintained scope silently stops covering whatever gets added next.
    ap.add_argument("--all", action="store_true",
                    help="discover every shipped page from git and check all of them")
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
    ap.add_argument("--base", default="http://localhost:8000",
                    help="origin --all builds its URLs from. Passed explicitly by the\n                          pre-push hook so the sweep cannot depend on the hook happening\n                          to serve the port this file defaults to.")
    ap.add_argument("--selftest", action="store_true", help="run calibration only, then exit")
    ap.add_argument("--no-selftest", action="store_true",
                    help="skip calibration (a green result then proves nothing)")
    a = ap.parse_args()
    if a.all:
        a.urls = discover_pages(a.base.rstrip("/"))
        print(f"  --all: discovered {len(a.urls)} shipped pages")
    if not a.urls:
        ap.error("give URLs, or use --all")
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
        bad, exempt_bad, notes, unmeasurable = [], [], [], []
        for width in widths:
            rows, truncated = audit(url, width, exempt=a.exempt,
                                    force_visible=a.force_visible)
            if rows is None:
                notes.append(f"@{width}px could not be measured")
                continue
            measured += len(rows)
            for r in rows:
                if r.get("dropped"):
                    notes.append(f"UNMEASURED: {len(r['dropped'])} text node(s) at {width}px "
                                 f"fell outside the captured image — {r['geom']}. "
                                 f"Their contrast is UNKNOWN, not passing. "
                                 f"First few: {r['dropped'][:5]}")
            rows = [r for r in rows if not r.get("dropped")]
            unmeasurable += [r for r in rows if r.get("unmeasurable")]
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
            print(f"  FAIL {r['ratio']:5.2f}/{r['need']}  {r['size']:>6.1f}px  "
                  f"{r['fg']} on {r['bg']}  @{r['width']}px  {r['text']!r}")
        # Surface each failure as an annotation so a CI failure is diagnosable without log access.
        # Capped: annotations are rate-limited per run and a wall of them buries the signal.
        for r in bad[:15]:
            gh("error", f"CONTRAST {r['ratio']:.2f}:1 (needs {r['need']}) — {r['size']:.1f}px "
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
        if unmeasurable:
            print(f"  UNMEASURABLE by this instrument ({len(unmeasurable)}) — NOT a verdict, "
                  f"these need pixel sampling of the glyph paint itself:")
            seen_u = set()
            for r in unmeasurable:
                k = (r["text"], r["unmeasurable"])
                if k in seen_u:
                    continue
                seen_u.add(k)
                print(f"    {r['unmeasurable']}  {r['size']:>6.1f}px  @{r['width']}px  {r['text']!r}")
        if not bad:
            print("  0 failures. Blind spots of this method: text inside <canvas>, <video>, "
                  "cross-origin iframes, and any state not reachable on load (hover, focus, open "
                  "menus) are NOT measured.")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
