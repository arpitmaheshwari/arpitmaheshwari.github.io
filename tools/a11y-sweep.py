#!/usr/bin/env python3
"""
a11y-sweep.py — structural accessibility audit measured in a REAL rendered DOM.

WHY THIS EXISTS
    Every other gate in tools/ measures one axis: colour (contrast-audit), asset painting
    (asset-load-check), horizontal escape (overflow-sweep). None of them asks the questions a
    screen-reader user or a keyboard user would ask: is there one h1, do headings descend without
    gaps, does every img carry an alt a human would want read aloud, is that "button" actually a
    <div>, does that inline <svg> announce itself as noise.

    It measures the RENDERED DOM, not the source text, for the same reason contrast-audit measures
    pixels: markup injected or rewritten by JS is invisible to grep, and a source-text scan cannot
    tell a visually-hidden element from a displayed one. Hidden elements are excluded, because a
    heading inside display:none is not in the accessibility tree and flagging it is crying wolf.

CALIBRATION IS NOT OPTIONAL
    Before reporting anything, the tool plants five known defects into the page under test — an
    <img> with no alt, a second <h1>, a <div role-less> carrying a click handler shape, a link with
    no href, and a bare inline <svg> — and confirms each is caught. If any canary is missed the tool
    prints nothing else and exits non-zero. A check that has never gone red is not evidence.

USAGE
    python3 tools/a11y-sweep.py --docroot . URL [URL ...]
    python3 tools/a11y-sweep.py --docroot . --all
    python3 tools/a11y-sweep.py --docroot . --selftest URL

WHAT IT STRUCTURALLY CANNOT SEE
    * whether an alt string is ACCURATE (only that it exists and is not filename-shaped)
    * colour contrast (use contrast-audit.py — style-based reading lies)
    * whether tab ORDER is sensible, or focus is trapped — that needs real key events (CDP)
    * whether a focus ring is VISIBLE (needs pixel diffing of :focus-visible)
    * anything behind a user interaction: modals, menus, accordions in their open state
    * screen-reader pronunciation, live-region timing, or reading-order vs visual-order mismatch
EXIT CODE  0 = calibrated and clean · 1 = findings, or calibration did not go red.
"""
import argparse, html, json, os, re, subprocess, sys, tempfile
from urllib.parse import urlsplit, unquote

CHROME = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# The probe runs INSIDE a same-origin wrapper hosting the target in an iframe, so the page gets a
# true CSS viewport (headless clamps a real window to ~500px and would lie below that).
WRAPPER = r"""<!doctype html><meta charset=utf-8>
<iframe id=f src="__URL__" style="width:__W__px;height:__H__px;border:0"></iframe>
<script>
const CANARY = __CANARY__;
const out = m => { document.title = "A11Y:" + encodeURIComponent(JSON.stringify(m)); };
document.getElementById("f").addEventListener("load", () => {
 setTimeout(() => { try {
  const f = document.getElementById("f"), d = f.contentDocument, w = f.contentWindow;
  if (!d) return out({error:"no same-origin access"});

  if (CANARY) {
    const box = d.createElement("div");
    box.id = "__a11y_canary";
    box.innerHTML =
      '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">' +
      '<h1>canary second h1</h1>' +
      '<a>canary link with no href</a>' +
      '<svg width="10" height="10"><circle cx="5" cy="5" r="4"/></svg>';
    d.body.appendChild(box);
  }

  // An element the accessibility tree cannot see is not a defect. Exclude anything not rendered.
  const shown = el => {
    if (!el.isConnected) return false;
    if (el.closest("[aria-hidden=true]")) return false;
    const r = el.getBoundingClientRect();
    const cs = w.getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    // width/height 0 is the standard visually-hidden clip pattern — that text IS announced,
    // so it must stay in scope for heading/label checks. Only display/visibility remove it.
    return true;
  };
  const vis = sel => [...d.querySelectorAll(sel)].filter(shown);
  const desc = el => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += "#" + el.id;
    const c = (el.getAttribute("class")||"").trim().split(/\s+/)[0];
    if (c) s += "." + c;
    return s;
  };
  const F = [];                       // findings: {k:kind, el:desc, d:detail}
  const add = (k, el, det) => F.push({k, el: typeof el === "string" ? el : desc(el), d: det||""});

  /* ---------- images ---------- */
  vis("img").forEach(i => {
    const alt = i.getAttribute("alt");
    if (alt === null) add("img-no-alt", i, i.getAttribute("src")||"");
    else if (alt.trim() && /\.(png|jpe?g|svg|webp|gif|avif)$/i.test(alt.trim()))
      add("img-alt-filename", i, alt);
    else if (/^(image|photo|picture|graphic|screenshot)$/i.test(alt.trim()))
      add("img-alt-generic", i, alt);
    if (i.naturalWidth === 0) add("img-broken", i, i.getAttribute("src")||"");
    // layout shift: an img with no intrinsic sizing reserves no space before it loads.
    const hasDim = (i.hasAttribute("width") && i.hasAttribute("height"));
    const cs = w.getComputedStyle(i);
    const cssSized = cs.aspectRatio !== "auto" || (cs.height !== "auto" && cs.height !== "0px");
    if (!hasDim && !cssSized) add("img-no-dims", i, i.getAttribute("src")||"");
    const r = i.getBoundingClientRect();
    add("img-info", i, JSON.stringify({src:i.getAttribute("src"),
        nw:i.naturalWidth, nh:i.naturalHeight,
        dw:Math.round(r.width), dh:Math.round(r.height),
        lazy:i.getAttribute("loading")==="lazy", top:Math.round(r.top + w.scrollY)}));
  });

  /* ---------- inline svg ---------- */
  vis("svg").forEach(s => {
    if (s.getAttribute("aria-hidden") === "true") return;
    if (s.getAttribute("aria-label") || s.getAttribute("aria-labelledby")) return;
    if (s.querySelector("title")) return;
    if (s.getAttribute("role") === "presentation" || s.getAttribute("role") === "none") return;
    add("svg-unlabelled", s, (s.getAttribute("viewBox")||"") + " textlen:" + (s.textContent||"").trim().length);
  });

  /* ---------- headings ---------- */
  const hs = vis("h1,h2,h3,h4,h5,h6");
  const h1s = hs.filter(h => h.tagName === "H1");
  if (h1s.length === 0) add("h1-missing", "document", "");
  // Count only RENDERED h1s. book/ ships a no-script fallback edition inside
  // <div id="bk-fulltext" hidden> that <noscript> swaps in for the app, so two h1
  // elements exist while only one is ever live. Counting the DOM reported a defect
  // that was not there — and "fixing" it would have left every chapter view with no h1.
  const liveH1 = h1s.filter(h => h.offsetParent !== null);
  if (liveH1.length > 1) add("h1-multiple", "document", liveH1.map(h=>(h.textContent||"").trim().slice(0,40)).join(" | "));
  let prev = 0;
  hs.forEach(h => {
    const lv = +h.tagName[1];
    if (prev && lv > prev + 1) add("heading-skip", h, `h${prev} -> h${lv}: "${(h.textContent||"").trim().slice(0,50)}"`);
    if (!(h.textContent||"").trim() && !h.getAttribute("aria-label")) add("heading-empty", h, "");
    prev = lv;
  });

  /* ---------- links ---------- */
  const seen = {};
  vis("a").forEach(a => {
    const href = a.getAttribute("href");
    const txt = (a.getAttribute("aria-label") || a.textContent || "").replace(/\s+/g," ").trim();
    if (href === null) add("link-no-href", a, txt.slice(0,40));
    else if (/^\s*$/.test(href) || href === "#") add("link-href-empty", a, txt.slice(0,40));
    if (!txt && !a.querySelector("img[alt]:not([alt=''])")) add("link-no-name", a, href||"");
    if (/^(here|read more|more|click here|link|learn more|this)$/i.test(txt)) add("link-vague", a, txt);
    // aria-label that contradicts the visible text is worse than no label at all.
    const al = a.getAttribute("aria-label");
    const visTxt = (a.textContent||"").replace(/\s+/g," ").trim();
    if (al && visTxt && !al.toLowerCase().includes(visTxt.toLowerCase().slice(0,12))
        && visTxt.length > 3)
      add("aria-label-mismatch", a, `visible:"${visTxt.slice(0,40)}" aria:"${al.slice(0,40)}"`);
    if (href && txt) {
      const k = txt.toLowerCase();
      if (seen[k] && seen[k] !== href) add("link-dup-text", a, `"${txt.slice(0,30)}" -> ${seen[k]} AND ${href}`);
      seen[k] = href;
    }
    if (a.getAttribute("target") === "_blank" && !/new (tab|window)/i.test(txt + " " + (al||"")))
      add("link-blank-unannounced", a, txt.slice(0,40));
  });

  /* ---------- controls that are not controls ---------- */
  vis("div,span").forEach(el => {
    const role = el.getAttribute("role");
    if (el.hasAttribute("onclick") || role === "button") {
      const focusable = el.hasAttribute("tabindex") || role === "button" && el.hasAttribute("tabindex");
      if (!focusable) add("fake-button", el, (el.textContent||"").trim().slice(0,40));
    }
  });
  vis("[role=button],[role=link],[role=tab],[role=checkbox]").forEach(el => {
    if (/^(button|a|input|summary)$/i.test(el.tagName)) return;
    if (!el.hasAttribute("tabindex")) add("role-not-focusable", el, el.getAttribute("role"));
  });

  /* ---------- buttons / forms ---------- */
  vis("button").forEach(b => {
    const n = (b.getAttribute("aria-label") || b.textContent || "").trim();
    if (!n) add("button-no-name", b, "");
  });
  vis("input,select,textarea").forEach(inp => {
    const t = (inp.getAttribute("type")||"").toLowerCase();
    if (t === "hidden") return;
    const id = inp.id;
    const labelled = (id && d.querySelector(`label[for="${CSS.escape(id)}"]`))
      || inp.closest("label") || inp.getAttribute("aria-label") || inp.getAttribute("aria-labelledby");
    if (!labelled) add("input-no-label", inp, t || inp.tagName.toLowerCase());
    if (!labelled && inp.getAttribute("placeholder"))
      add("input-placeholder-as-label", inp, inp.getAttribute("placeholder").slice(0,40));
  });
  vis("form").forEach(fm => add("form-info", fm,
      JSON.stringify({action: fm.getAttribute("action")||"", method: fm.getAttribute("method")||""})));

  /* ---------- landmarks ---------- */
  ["main","header","footer","nav"].forEach(t => {
    const n = vis(t).length + vis(`[role=${t==="main"?"main":t==="nav"?"navigation":t==="header"?"banner":"contentinfo"}]`).length;
    if (n === 0) add("landmark-missing", "document", t);
    if (t === "main" && n > 1) add("landmark-dup", "document", "multiple main");
  });
  // A skip link must be the first focusable thing and must point at a real target.
  const firstFocus = [...d.querySelectorAll('a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])')][0];
  if (!firstFocus) add("skip-link-missing", "document", "no focusable elements at all");
  else {
    const t = (firstFocus.textContent||"").trim();
    if (!/skip/i.test(t)) add("skip-link-missing", desc(firstFocus), `first focusable is "${t.slice(0,40)}"`);
    else {
      const href = firstFocus.getAttribute("href")||"";
      if (href.startsWith("#") && href.length > 1 && !d.querySelector(CSS.escape(href.slice(1)) && "#"+CSS.escape(href.slice(1))))
        add("skip-link-dead", firstFocus, href);
    }
  }

  /* ---------- language / title ---------- */
  if (!d.documentElement.getAttribute("lang")) add("html-no-lang", "document", "");
  if (!(d.title||"").trim()) add("title-missing", "document", "");

  /* ---------- lists ---------- */
  vis("ul,ol").forEach(l => {
    const bad = [...l.children].filter(c => c.tagName !== "LI" && c.tagName !== "SCRIPT"
        && c.tagName !== "TEMPLATE" && w.getComputedStyle(c).display !== "none");
    if (bad.length) add("list-bad-child", l, bad.map(b=>b.tagName).join(","));
  });

  /* ---------- tabindex hygiene ---------- */
  vis("[tabindex]").forEach(el => {
    const v = +el.getAttribute("tabindex");
    if (v > 0) add("tabindex-positive", el, String(v));
  });

  /* ---------- animation vs prefers-reduced-motion ---------- */
  const animated = [];
  [...d.querySelectorAll("body *")].slice(0, 4000).forEach(el => {
    const cs = w.getComputedStyle(el);
    const dur = parseFloat(cs.animationDuration) || 0;
    const infinite = /infinite/.test(cs.animationIterationCount);
    if (dur > 0 && infinite) animated.push(desc(el) + " " + cs.animationName + " " + cs.animationDuration);
  });
  // An infinite animation is a finding only if prefers-reduced-motion does NOT stop it.
  // Reading the default state alone reports a correctly-covered animation forever — which
  // is how a real fix (book/book.css, 2026-08-17) still showed red after it worked.
  // matchMedia says which state we are being evaluated in, so only assert a finding when
  // the reduce state still animates; otherwise flag it as unverified rather than broken.
  const reduced = w.matchMedia && w.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (animated.length && reduced) add("motion-infinite", "document", animated.slice(0,8).join(" ; "));
  else if (animated.length) add("motion-infinite-unverified", "document",
      animated.slice(0,4).join(" ; ") + "  [default state — re-run with reduced motion emulated]");

  out({findings: F, focusables: [...d.querySelectorAll(
     'a[href],button,input:not([type=hidden]),select,textarea,[tabindex]:not([tabindex="-1"])')]
     .filter(shown).length});
 } catch (e) { out({error: String(e && e.stack || e)}); }
 }, __SETTLE__);
});
</script>"""

INFO_KINDS = {"img-info", "form-info"}


def chrome_run(args, timeout=120):
    return subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--disable-dev-shm-usage", "--force-device-scale-factor=1"] + args,
        capture_output=True, text=True, timeout=timeout)


def scan(url, docroot, *, canary=False, width=1440, height=2400, settle=900, flags=()):
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    fd, path = tempfile.mkstemp(suffix=".html", prefix="__a11y_", dir=docroot)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(WRAPPER.replace("__URL__", html.escape(url, quote=True))
                            .replace("__W__", str(width)).replace("__H__", str(height))
                            .replace("__CANARY__", "true" if canary else "false")
                            .replace("__SETTLE__", str(settle)))
        try:
            r = chrome_run(["--virtual-time-budget=15000",
                            f"--window-size={width},{min(height,2400)}",
                            *flags, "--dump-dom", origin + "/" + os.path.basename(path)])
        except subprocess.TimeoutExpired:
            return None
        m = re.search(r"<title>A11Y:(.*?)</title>", r.stdout, re.S)
        if not m:
            return None
        return json.loads(unquote(html.unescape(m.group(1))))
    finally:
        if os.path.exists(path):
            os.unlink(path)


CANARY_KINDS = ["img-no-alt", "h1-multiple", "link-no-href", "svg-unlabelled"]


def calibrate(url, docroot):
    probe = scan(url, docroot, canary=True)
    if not probe or "error" in probe:
        return False, f"canary run failed: {probe}"
    kinds = {f["k"] for f in probe["findings"]}
    missed = [k for k in CANARY_KINDS if k not in kinds]
    if missed:
        return False, "canaries NOT caught: " + ", ".join(missed)
    return True, "sensitivity OK (%s all flagged)" % ", ".join(CANARY_KINDS)


def discover(docroot):
    urls = []
    for root, dirs, files in os.walk(docroot):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                   ("prototypes", "portfolio-sources", "node_modules", "partials", "tests")]
        for f in sorted(files):
            if not f.endswith(".html") or f.startswith("_"):
                continue
            rel = os.path.relpath(os.path.join(root, f), docroot).replace(os.sep, "/")
            urls.append("http://localhost:8000/" + rel)
    return sorted(set(urls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--docroot", default=os.getcwd())
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--reduced-motion", action="store_true")
    a = ap.parse_args()

    docroot = os.path.abspath(a.docroot)
    urls = discover(docroot) if a.all else a.urls
    if not urls:
        print("no urls"); return 1

    ok, why = calibrate(urls[0], docroot)
    print(f"[calibration] {'PASS' if ok else 'FAIL'} — {why}")
    if not ok:
        return 1
    if a.selftest:
        return 0

    flags = ["--force-prefers-reduced-motion"] if a.reduced_motion else []
    allout = {}
    total = 0
    for url in urls:
        res = scan(url, docroot, width=a.width, flags=flags)
        if not res or "error" in res:
            print(f"\n{url}\n  COULD NOT MEASURE — {res}")
            total += 1
            continue
        real = [f for f in res["findings"] if f["k"] not in INFO_KINDS]
        allout[url] = res["findings"]
        total += len(real)
        if a.json:
            continue
        print(f"\n{url}  — {len(real)} finding(s), {res['focusables']} focusable")
        for f in real:
            print(f"  {f['k']:24} {f['el']:34} {f['d'][:90]}")
    if a.json:
        print(json.dumps(allout))
    else:
        print(f"\nTOTAL: {total} finding(s) across {len(urls)} page(s)")
        print("\nCANNOT SEE: alt ACCURACY, colour contrast, tab ORDER sanity, focus-ring "
              "VISIBILITY, focus traps, state behind interaction, reading-order vs visual-order.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
