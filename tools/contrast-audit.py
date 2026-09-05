#!/usr/bin/env python3
"""
VENDORED COPY — the cross-project master lives at
~/.claude/reference/tools/contrast-audit.py

This copy exists because CI checks out only this repository and cannot read ~/.claude.
If you change one, change both. `diff` them if the two ever disagree.
"""
"""
contrast-audit.py v3 — WCAG contrast measured from RENDERED PIXELS, viewport-native.

WHY THIS EXISTS
    On 2026-07-31 a style-based contrast checker reported "clean" for eight consecutive QA rounds
    while the primary call-to-action on the most-shared page of a portfolio site sat at 1.18:1 —
    invisible. Style walks cannot see gradients, overlays, blend modes or stacked opacity, so this
    tool has always measured pixels.

WHY v3 EXISTS (2026-09-03 — Arpit: "the contrast gate is continuously breaking; first principles")
    v2 photographed the WHOLE DOCUMENT as one image and mapped DOM rects onto it in document
    coordinates. Chrome fights that architecture at every turn, and one month of git history reads
    as eleven compensations for it: the 16,384px capture wrap (beacons + tiled stitching),
    capture-triggered relayout, lazy images growing the page under the rects, scroll algebra,
    silent node drops, per-element-type ink branches (SVG fill, gradient text declared
    UNMEASURABLE), and statistical ground-guessing (grid samples, mode-not-mean, near-ink
    exclusion). Each compensation carried its own failure modes; the gate broke monthly.

    A reader never sees the document as one image. v3 grades what the reader sees, where they
    see it, and defines ink by physics instead of by style reading:

      1. VIEWPORT-NATIVE CAPTURE. The page is scrolled in real steps and each screenful is
         photographed with a plain viewport screenshot. Nothing is ever captured beyond the
         viewport, so the texture-cap wrap, capture relayout, beacons and stitching are not
         fixed — they are structurally impossible. Rects are queried FRESH at every stop, in
         viewport coordinates: there is no document-space mapping to drift.
      2. DIFFERENTIAL INK. Every screenful is photographed twice at identical geometry —
         once as shipped, once with all text paint removed. A glyph pixel is DEFINED as a
         pixel the two frames disagree on; its ink is frame A at that pixel, its ground is
         frame B at the same pixel. SVG fill vs color, background-clip:text gradients,
         text-shadow, alpha compositing: all just pixels now. Gradient text — v2's declared
         blind spot — is measured like everything else, and the selftest proves it.
      3. STATE IS THE INSTRUMENT'S JOB. Fonts, animations, lazy images and scroll-reveals are
         settled INSIDE the tool on every run. --force-visible still exists but now has a
         default ('.reveal'); a caller can no longer produce false reds by forgetting a flag
         (which happened the day before this rewrite).
      4. SELF-ACCOUNTING. Every eligible text element must be graded somewhere or explained;
         the ungraded are printed by name. "33 of 231 measured, 0 failures" can't recur.
      5. INVISIBLE INK IS A FINDING. An eligible, visible text element whose two frames do not
         differ paints no legible ink at all (color == ground, or fully obscured). v2 reported
         the closely-related signature "exactly 1.00" as instrument failure; v3 detects it as
         the legibility failure it is.

CALIBRATION IS NOT OPTIONAL
    Before reporting anything the tool plants THREE canaries and requires all three red:
    a plain low-contrast element, a low-contrast background-clip:text gradient element
    (the old blind spot), and a low-contrast element hidden behind a `.reveal` fade
    (the state race). If any canary survives, nothing else is reported.

USAGE
    python3 contrast-audit.py URL [URL ...] [--widths 1440,1024,768] [--exempt "SELECTOR"]
    python3 contrast-audit.py --all [--base http://localhost:8000]
    python3 contrast-audit.py --selftest URL          # calibration only

EXIT CODE     0 = calibrated and clean · 1 = failures found, or calibration did not go red
              2 = the instrument could not measure (distinct from "found a defect")
"""
import argparse, json, math, os, subprocess, sys

# Guarantee the server these gates assume (idempotent; reuses a listening server).
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

VIEWPORT_H = 900             # a REAL viewport: 100vh sections lay out as a reader sees them.
BAND_PAD = 8                 # px of slack inside the unobstructed band
DIFF_T = 24                  # per-pixel channel-sum difference that counts as "ink was here"
ALPHA_CORE = 0.7             # glyph-core coverage: pixels this inked recover the authored colour
ALPHA_FLOOR = 0.5            # below this the un-blend is noise, not a measurement

CANARY_TEXT = "calibration canary do not ship"
CANARY_GT_TEXT = "gradient canary do not ship"
CANARY_RV_TEXT = "reveal canary do not ship"
# Three planted defects. Each exercises a distinct historical failure mode.
CANARY_HTML = (
    "<div id='__ca_c1' style='position:absolute;left:0;top:120px;z-index:2147483647;"
    "background:#777;color:#8A8A8A;font-size:14px;padding:6px'>" + CANARY_TEXT + "</div>"
    # background-clip:text — v2 declared this UNMEASURABLE; v3 must flag it.
    "<div id='__ca_c2' style='position:absolute;left:0;top:160px;z-index:2147483647;"
    "background:#777;padding:6px'><span style='font-size:14px;"
    "background:linear-gradient(90deg,#808080,#8C8C8C);-webkit-background-clip:text;"
    "background-clip:text;color:transparent;-webkit-text-fill-color:transparent'>"
    + CANARY_GT_TEXT + "</span></div>"
    # a .reveal element starting invisible — the settle/pin machinery must surface it.
    "<div class='reveal' id='__ca_c3' style='position:absolute;left:0;top:200px;"
    "z-index:2147483647;background:#777;color:#8A8A8A;font-size:14px;padding:6px'>"
    + CANARY_RV_TEXT + "</div>"
)

# Pass-B ink removal. ":root *" so it WINS ties against single-class !important color rules
# (measured 2026-08-13: a zero-specificity rule lost and text polluted its own ground).
# [data-ca-gt] handles background-clip:text — those glyphs are painted BY the background,
# so the background itself must not paint in pass B.
HIDE_TEXT_CSS = (":root *{color:transparent!important;text-shadow:none!important;"
                 "text-decoration-color:transparent!important;caret-color:transparent!important;"
                 "-webkit-text-fill-color:transparent!important}"
                 ":root svg text,:root svg tspan{fill:transparent!important}"
                 ":root [data-ca-gt]{background:none!important}")

# Pass-C ink replacement: repaint every glyph in KNOWN magenta. Per pixel,
# coverage alpha = how far frame C moved from frame B toward pure magenta —
# which de-aliases frame A by algebra: authored_ink = (A - (1-a)*B) / a.
# Without this, antialiased 10-12px text never paints a fully-inked pixel and
# any pixel-picked estimate reads dark (measured 2026-09-03: three labels with
# authored ratios 5.1-6.1 read as 3.7-4.0 — phantom failures, the exact
# disease this rewrite exists to cure).
MAGENTA = (255, 0, 255)
INK_KEY_CSS = (":root *{color:#FF00FF!important;text-shadow:none!important;"
               "text-decoration-color:transparent!important;caret-color:transparent!important;"
               "-webkit-text-fill-color:#FF00FF!important}"
               ":root svg text,:root svg tspan{fill:#FF00FF!important}"
               ":root [data-ca-gt]{background:#FF00FF!important;"
               "-webkit-background-clip:text!important;background-clip:text!important}")

# --------------------------------------------------------------------- colour

def _lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def luminance(c):
    return 0.2126 * _lin(c[0]) + 0.7152 * _lin(c[1]) + 0.0722 * _lin(c[2])

def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    if la < lb: la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)

def required_ratio(px, weight):
    # WCAG 1.4.3: "large text" is >=24px, or >=18.66px bold — that gets 3:1; the rest 4.5:1.
    try:
        w = int(str(weight))
    except ValueError:
        w = 700 if str(weight) == "bold" else 400
    if px >= 24 or (px >= 18.66 and w >= 700):
        return 3.0
    return 4.5

def gh(level, msg):
    """GitHub Actions annotation; a no-op noise-free print locally."""
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::{level}::{msg}")

# ------------------------------------------------------------------ page prep

# Eligibility: any element owning a DIRECT non-empty text node (NOT only childless elements —
# `children.length===0` once skipped the very CTA that motivated this tool). Painted size for
# SVG text uses getScreenCTM: computed fontSize is in user units and a 40px label in a scaled
# viewBox can paint at 15px, flipping which WCAG threshold it owes (measured 2026-08-17).
PREP_JS = """(function(FORCE){
  var d=document, out=[], id=0;
  // settle aids: instant scrolling for the whole audit
  var st=d.createElement('style'); st.id='__ca_instant';
  st.textContent='html{scroll-behavior:auto!important}';
  d.head.appendChild(st);
  if (FORCE) {
    var fv=d.createElement('style'); fv.id='__ca_fv';
    fv.textContent=FORCE+'{opacity:1!important;transform:none!important;'+
      'visibility:visible!important;transition-property:none!important}';
    d.head.appendChild(fv);
  }
  d.querySelectorAll('body *').forEach(function(el){
    var own='';
    for (var i=0;i<el.childNodes.length;i++)
      if (el.childNodes[i].nodeType===3) own+=el.childNodes[i].nodeValue;
    if (!own.trim()) return;
    if (el.closest('script,style,[hidden],[aria-hidden="true"]')) return;
    var cs=getComputedStyle(el);
    if (cs.visibility==='hidden'||cs.display==='none'||parseFloat(cs.opacity)===0) return;
    var r=el.getBoundingClientRect();
    if (r.width<3||r.height<3) return;
    var px=parseFloat(cs.fontSize);
    if (el.ownerSVGElement && el.getScreenCTM){
      var m=el.getScreenCTM();
      if (m){ var sc=Math.sqrt(Math.abs(m.a*m.d-m.b*m.c));
              if (sc>0&&isFinite(sc)) px=px*sc; }
    }
    var clip=cs.webkitBackgroundClip||cs.backgroundClip;
    if (clip==='text') el.setAttribute('data-ca-gt','1');
    el.setAttribute('data-ca-id', String(id));
    var fx=false, p=el;
    while (p && p!==d.body){ var pcs=getComputedStyle(p);
      if (pcs.position==='fixed'||pcs.position==='sticky'){fx=true;break;} p=p.parentElement; }
    out.push({id:id, t:own.trim().slice(0,44), size:px, wt:cs.fontWeight,
              ex:!!(EXEMPT_SEL && el.closest(EXEMPT_SEL)), fx:fx,
              offcanvas:(r.bottom<=0||r.right<=0),
              // VISUALLY HIDDEN IS NOT A CONTRAST DEFECT. The standard sr-only pattern —
              // a 1x1 clipped box — paints nothing on purpose, and the audit reported the
              // before/after table's <thead> on /case-studies/adtech.html as "paints no
              // visible ink" at 390px. It is correct markup: the thead is dropped from view
              // and every cell below carries its own visible label, which is exactly what
              // the mobile cards show. Convicting it would push someone to "fix" an
              // accessibility affordance by making it visible.
              sronly:(()=>{let n=el;while(n&&n!==document.body){const cs=getComputedStyle(n);
                const cr=n.getBoundingClientRect();
                if((cs.clipPath||'').includes('inset(50%)')) return true;
                if(cs.position==='absolute'&&cr.width<=2&&cr.height<=2&&
                   cs.overflow==='hidden') return true;
                n=n.parentElement;} return false;})()});
    id++;
  });
  // fixed chrome bands: regions a scrolling reader never sees content through
  var top=0, bot=0, vh=innerHeight;
  d.querySelectorAll('body *').forEach(function(el){
    var cs=getComputedStyle(el);
    if (cs.position!=='fixed'&&cs.position!=='sticky') return;
    if (cs.display==='none'||cs.visibility==='hidden') return;
    var r=el.getBoundingClientRect();
    if (r.width<innerWidth*0.5||r.height<8||r.height>vh*0.5) return;
    if (r.top<=2) top=Math.max(top,r.bottom);
    if (r.bottom>=vh-2) bot=Math.max(bot,vh-r.top);
  });
  return {els:out, h:d.documentElement.scrollHeight, top:Math.ceil(top), bot:Math.ceil(bot)};
})"""

RECTS_JS = """(function(ids){
  var out={};
  ids.forEach(function(i){
    var el=document.querySelector('[data-ca-id="'+i+'"]');
    if (!el) return;
    var r=el.getBoundingClientRect();
    out[i]=[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];
  });
  return out;
})"""

SETTLE_JS = """(async()=>{
  const dl=new Promise(r=>setTimeout(r,4000));
  const work=(async()=>{
    try{await document.fonts.ready;}catch(e){}
    // eager-load and decode every image: lazy images once grew the page mid-capture
    try{await Promise.all([].slice.call(document.images).map(i=>{
      try{i.loading='eager';}catch(e){}
      return (i.decode?i.decode():Promise.resolve()).catch(()=>0);}));}catch(e){}
    // jump every animation/transition to its end state; infinite ones are left running
    try{document.getAnimations().forEach(a=>{try{a.finish();}catch(e){}});
        await Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>0)));}catch(e){}
  })();
  await Promise.race([work,dl]);
})()"""


def _measure(im_a, im_b, im_c, rect, band):
    """Grade one element from three frames: A shipped, B ink removed, C ink keyed magenta.

    Per pixel, coverage a = |C - B| / |MAGENTA - B| (channel-wise, well-conditioned
    channels only). Where a >= ALPHA_CORE the AUTHORED ink is recovered exactly:
    ink = (A - (1-a)*B) / a — de-aliasing by algebra, not statistics. The element's
    ratio is the 10th percentile of per-pixel ratios over core pixels, so a gradient
    is graded at its weakest point and uniform ink is graded at its true value.

    Returns (ratio, no_ink, fg_hex, bg_hex, core_count) or None if the rect has no
    area inside the band."""
    x, y, w, h = rect
    x0 = max(x, 0); y0 = max(y, band[0])
    x1 = min(x + w, im_a.width); y1 = min(y + h, band[1])
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None
    a_px = im_a.crop((x0, y0, x1, y1)).load()
    b_px = im_b.crop((x0, y0, x1, y1)).load()
    c_px = im_c.crop((x0, y0, x1, y1)).load()
    W, H = x1 - x0, y1 - y0
    glyphs = []          # (alpha, a_pixel, b_pixel)
    for j in range(H):
        for i in range(W):
            pb, pc = b_px[i, j], c_px[i, j]
            # coverage from frame C: how far this pixel moved toward pure magenta
            alphas = []
            for ch in range(3):
                denom = MAGENTA[ch] - pb[ch]
                if abs(denom) >= 48:
                    al = (pc[ch] - pb[ch]) / float(denom)
                    if -0.15 <= al <= 1.2:
                        alphas.append(min(1.0, max(0.0, al)))
            if not alphas:
                continue
            alpha = sorted(alphas)[len(alphas) // 2]
            if alpha < 0.12:
                continue
            glyphs.append((alpha, a_px[i, j], pb))
    if len(glyphs) < 4:
        # frame C shows no glyphs either: nothing is painted here at all
        # (fully obscured), or frames A and B agree because ink == ground.
        # Either way the reader cannot see this text.
        return (1.0, True, "-", "-", 0)
    # Recover the authored ink from the best-covered pixels. Letter-spaced 11px
    # caps (the nav) never reach 0.7 coverage, so the core bar adapts: at least
    # 0.35, at most ALPHA_CORE, pinned to 85% of the best coverage this element
    # actually painted — the algebra is identical, only noisier at low alpha.
    max_a = max(g[0] for g in glyphs)
    # DO NOT CONVICT ON A NOISY UN-BLEND. The recovery below is
    #     ink = (painted - (1 - alpha) * ground) / alpha
    # which divides by alpha, so every rounding error is multiplied by 1/alpha. At
    # alpha 0.7 the authored colour comes back exactly; at 0.35 a one-step rounding
    # error becomes three, and the "ink" it returns is a colour nobody authored.
    #
    # That is not hypothetical. The nightly sweep on a Linux runner reported the
    # homepage call-to-action at 2.49:1, sampling #B1330C on #F67E99. The authored
    # pair is #1A0D08 on #F67E99 — 7.57:1 — and #B1330C appears in no stylesheet in
    # this repository. Headless Chrome on Linux renders 11-12.5px text thinner than
    # macOS does, every flagged element was 11-12.5px, and the thinner the glyph the
    # lower max coverage goes and the noisier this algebra gets.
    #
    # So below the floor this reports UNMEASURABLE rather than a failure. A gate that
    # cannot see clearly must say so; inventing a colour and convicting the page on it
    # is the worst thing it could do, because the fix would be to damage a design that
    # is already accessible.
    if max_a < ALPHA_FLOOR:
        return (None, False, "-", "-", 0)
    bar = min(ALPHA_CORE, max(0.35, max_a * 0.85))
    core = []
    for alpha, pa, pb in glyphs:
        if alpha < bar:
            continue
        ink = tuple(min(255, max(0, int(round((pa[ch] - (1 - alpha) * pb[ch]) / alpha))))
                    for ch in range(3))
        core.append((ratio(ink, pb[:3]), ink, pb[:3]))
    if not core:
        return (1.0, True, "-", "-", 0)
    core.sort(key=lambda t: t[0])
    pick = core[max(0, int(len(core) * 0.10) - 1)] if len(core) > 4 else core[0]
    got, ink, ground = pick
    return (got, False, "#%02X%02X%02X" % ink, "#%02X%02X%02X" % ground, len(core))


def audit(url, width, exempt=None, canary=False, force_visible=".reveal"):
    """Measure one URL at one width, viewport by viewport.

    Returns (rows, notes) — rows is None only if the page could not be driven at all."""
    from PIL import Image
    import base64, io as _io
    notes = []
    with cdp.Browser() as br:
        br.viewport(width, VIEWPORT_H)
        # The audit grades the SETTLED reading state, and the site's own honesty
        # rail defines one: every self-demo, ghost cursor and session clock dies
        # under prefers-reduced-motion (assets/recon-live.js early-returns). A
        # continuously animating widget flips views BETWEEN this tool's frames and
        # fabricates ink==ground readings (PTC's recon caption, 2026-09-03), so the
        # audit runs as a reduced-motion reader. Colours only shown mid-animation
        # join the stated blind-spot list.
        try:
            br.cmd("Emulation.setEmulatedMedia",
                   features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
        except Exception:
            pass
        try:
            br.navigate(url, settle=2.0)
        except Exception:
            return None, ["navigation failed"]
        if canary:
            br.eval("(function(){var s=document.createElement('div');s.innerHTML=%s;"
                    "while(s.firstChild)document.body.appendChild(s.firstChild);})()"
                    % json.dumps(CANARY_HTML))
        br.eval(SETTLE_JS, await_promise=True)
        br.pump(0.3)
        prep = PREP_JS.replace("EXEMPT_SEL", json.dumps(exempt) if exempt else "null")
        data = br.eval_json("JSON.stringify((%s)(%s))" % (prep, json.dumps(force_visible)))
        if not data or not data.get("els"):
            return None, ["no eligible text found — page did not render?"]
        els = {e["id"]: e for e in data["els"]}
        page_h = int(data["h"])
        band = (int(data["top"]) + BAND_PAD, VIEWPORT_H - int(data["bot"]) - BAND_PAD)
        usable = band[1] - band[0]
        if usable < 200:
            return None, [f"fixed chrome leaves only {usable}px of viewport — refusing to grade"]

        # After settle, future transitions serve nobody and poison the frame set:
        # nav links carry `transition: color .2s`, so restoring ink from the magenta
        # key frame fired a fade that frame A2 caught mid-flight — every nav link
        # read UNSTABLE at every stop (measured 2026-09-03). The settled state is
        # already reached; from here, state changes apply instantly.
        # After settle, future transitions serve nobody: nav links carry
        # `transition: color .2s`, so restoring ink from the magenta key frame fired
        # a fade that frame A2 caught mid-flight — every nav link read UNSTABLE at
        # every stop (2026-09-03). And aria-hidden text is decoration, not content —
        # its glyphs land inside CONTENT rects (the 404's giant ghost watermark
        # overlapped the h1 and the worst-pixel grader attributed the ghost's 1.07 to
        # a cream heading that runs >11:1). Blanked in ALL frames it contributes
        # nothing to any diff; the ground shifts by the decoration's own near-
        # invisible shade — conservative, and stated in the blind-spot line.
        # The blanking must OUTRANK the pass-B/C rules (:root * is 0,1,1): with a
        # tie, the magenta key repainted the aria-hidden ghost in frame C ONLY,
        # minting alpha=1 pixels whose "ink" was the bare background (2026-09-03).
        _audit_css = (":root *{transition-duration:0s!important;transition-delay:0s!important}"
                      ":root [aria-hidden='true'],:root [aria-hidden='true'] *{color:transparent!important;"
                      "-webkit-text-fill-color:transparent!important;text-shadow:none!important;"
                      "fill:transparent!important}")
        br.eval("(function(){var st=document.createElement('style');st.textContent=%s;"
                "document.head.appendChild(st);})()" % json.dumps(_audit_css))
        # pass-B style, present from the start but disabled; toggling `media` swaps ink
        # on/off with zero layout consequence between the paired captures.
        br.eval("(function(){var st=document.createElement('style');st.id='__ca_hide';"
                "st.media='not all';st.textContent=%s;document.head.appendChild(st);})()"
                % json.dumps(HIDE_TEXT_CSS))
        br.eval("(function(){var st=document.createElement('style');st.id='__ca_key';"
                "st.media='not all';st.textContent=%s;document.head.appendChild(st);})()"
                % json.dumps(INK_KEY_CSS))

        def shot():
            r = br.cmd("Page.captureScreenshot", format="png")
            return Image.open(_io.BytesIO(base64.b64decode(
                r.get("result", r)["data"]))).convert("RGB")

        def _frames(br, shot):
            """A, B, C, then A again. The second A frame is the instrument checking
            itself: a widget that self-demos on scroll (PTC's reconstruction does)
            repaints BETWEEN frames, and any element whose two A frames disagree is
            deferred rather than graded from lying pixels."""
            a = shot()
            br.eval("document.getElementById('__ca_hide').media='all'")
            br.pump(0.08)
            b = shot()
            br.eval("document.getElementById('__ca_hide').media='not all';"
                    "document.getElementById('__ca_key').media='all'")
            br.pump(0.08)
            c = shot()
            br.eval("document.getElementById('__ca_key').media='not all'")
            br.pump(0.08)
            a2 = shot()
            return a, b, c, a2

        def _stable(im1, im2, rect, band):
            x, y, w, h = rect
            x0 = max(x, 0); y0 = max(y, band[0])
            x1 = min(x + w, im1.width); y1 = min(y + h, band[1])
            if x1 - x0 < 2 or y1 - y0 < 2:
                return True
            p1 = im1.crop((x0, y0, x1, y1)).load()
            p2 = im2.crop((x0, y0, x1, y1)).load()
            W, H = x1 - x0, y1 - y0
            moved = 0
            for j in range(0, H, 2):
                for i in range(0, W, 2):
                    q1, q2 = p1[i, j], p2[i, j]
                    if abs(q1[0]-q2[0]) + abs(q1[1]-q2[1]) + abs(q1[2]-q2[2]) > DIFF_T:
                        moved += 1
                        if moved * 16 > W * H // 25:   # >4% of the (subsampled) area moved
                            return False
            return True

        # ---- CAMERA CALIBRATION. Everything below reads PIXELS at coordinates the DOM
        # reported in CSS pixels. That equivalence is an ASSUMPTION, and it is the one
        # assumption this tool never checked. If the frame comes back at a different
        # scale or size than the emulated viewport — a deviceScaleFactor the override
        # did not take, a capture that used the window instead of the emulation — then
        # every crop lands somewhere the element is not. The arithmetic stays perfect
        # and the answer is still wrong, which is precisely the shape of the ten Linux
        # "failures": right page, right fonts, right un-blend, wrong pixels.
        # _measure() clamps crops to the image (min(x+w, im.width)), so a mismatch
        # cannot raise — it can only silently grade the wrong region. Hence an explicit
        # assertion, before anything is graded, that refuses rather than reports.
        _probe = shot()
        _vw, _vh, _dpr = br.eval_json(
            "JSON.stringify([innerWidth,innerHeight,devicePixelRatio])")
        if (_probe.width, _probe.height) != (int(_vw), int(_vh)):
            return None, [f"UNCALIBRATED CAMERA: frame is {_probe.width}x{_probe.height} "
                          f"but the viewport reports {_vw}x{_vh} (dpr {_dpr}). Every rect "
                          f"is in CSS pixels; grading would sample the wrong region."]
        if (_probe.width, _probe.height) != (width, VIEWPORT_H):
            notes.append(f"viewport is {_probe.width}x{_probe.height}, asked for "
                         f"{width}x{VIEWPORT_H} — frame and rects agree, so grading is "
                         f"honest, but the page was measured at a size nobody requested")

        graded, rows = set(), []
        # declared non-participants
        for i, e in els.items():
            if e["offcanvas"] or e.get("sronly"):
                rows.append({"width": width, "text": e["t"], "size": e["size"],
                             "fg": "-", "bg": "-", "ratio": 0.0,
                             "need": required_ratio(e["size"], e["wt"]), "ok": True,
                             "exempt": e["ex"],
                             "unmeasurable": ("visually hidden on purpose (sr-only)"
                                              if e.get("sronly") else
                                              "off-canvas until focused (skip link)")})
                graded.add(i)

        step = max(200, usable - 60)          # overlap so band-edge elements land fully inside
        y = 0
        positions = []
        while True:
            positions.append(min(y, max(0, page_h - VIEWPORT_H)))
            if y >= page_h - VIEWPORT_H:
                break
            y += step
        seen_pos = set()
        for pos in positions:
            if pos in seen_pos:
                continue
            seen_pos.add(pos)
            br.eval(f"window.scrollTo(0,{pos})")
            # A scroll that does not scroll is the same defect in motion: this page's
            # rects would then be queried at a position the camera never reached. Rects
            # ARE re-read below, so a stuck scroll cannot mis-grade — but it can loop
            # forever regrading one screenful, so say so once instead of pretending.
            _sy = int(br.eval_json("JSON.stringify([Math.round(window.scrollY)])")[0])
            if abs(_sy - pos) > 2 and pos > 0:
                notes.append(f"scrollTo({pos}) landed at {_sy} — the window is not the "
                             f"scrolling element here; pages below this point may go ungraded")
            # the nav's scroll-shading transition must FINISH before the frame set,
            # or fixed chrome fails its own stability check at every stop
            br.pump(0.4)
            want = [i for i in els if i not in graded]
            if not want:
                break
            rects = br.eval_json("JSON.stringify((%s)(%s))" % (RECTS_JS, json.dumps(want)))
            # fully inside the unobstructed band → gradable at this stop.
            # Fixed/sticky-chrome text rides with the viewport: it is graded at the
            # FIRST stop against the full viewport (its ground is its own chrome).
            here = {}
            for k, r in (rects or {}).items():
                x, ry, w, h = r
                if w < 2 or h < 2:
                    continue
                ik = int(k)
                if els[ik].get("fx"):
                    if 0 <= ry and ry + h <= VIEWPORT_H and x < width and x + w > 0:
                        here[ik] = ("full", r)
                    continue
                if ry >= band[0] and ry + h <= band[1] and x < width and x + w > 0:
                    here[ik] = ("band", r)
            # oversized elements: on the LAST chance (element taller than the band),
            # grade the slice that is visible — the diff method grades partial regions honestly.
            for k, r in (rects or {}).items():
                ik = int(k)
                if ik in here or ik in graded or els[ik].get("fx"):
                    continue
                x, ry, w, h = r
                if h > usable and ry < band[1] and ry + h > band[0]:
                    here[ik] = ("band", r)
            if not here:
                continue
            im_a, im_b, im_c, im_a2 = _frames(br, shot)
            for i, (scope, r) in here.items():
                e = els[i]
                use_band = (0, VIEWPORT_H) if scope == "full" else band
                if not _stable(im_a, im_a2, r, use_band):
                    continue          # animated here; the targeted pass gets another shot
                res = _measure(im_a, im_b, im_c, r, use_band)
                if res is None:
                    continue
                got, no_ink, fg, bg, n = res
                need = required_ratio(e["size"], e["wt"])
                if got is None:
                    # Coverage too low for the un-blend to mean anything — see
                    # ALPHA_FLOOR. Reported through the tool's OWN unmeasurable
                    # row, the same path the skip link uses, so it appears in the
                    # UNMEASURABLE block and is never counted as a failure. My
                    # first version kept a private list and added a note, which
                    # tripped could_not_measure and failed a push over two
                    # elements the tool had simply declined to grade.
                    rows.append({"width": width, "text": e["t"],
                                 "size": e["size"], "fg": "-", "bg": "-",
                                 "ratio": 0.0, "need": need, "ok": True,
                                 "exempt": e["ex"],
                                 "unmeasurable": "glyph coverage below the "
                                                 "un-blend floor (thin anti-aliasing)"})
                    graded.add(i)
                    continue
                if no_ink:
                    # An eligible, visible element whose frames do not differ paints no
                    # legible ink: invisible text or fully obscured. v2's "exactly 1.00"
                    # instrument-failure signature, now detected as the defect it is.
                    rows.append({"width": width, "text": e["t"], "size": e["size"],
                                 "fg": fg, "bg": bg, "ratio": 1.0, "need": need,
                                 "ok": False, "exempt": e["ex"], "noink": True})
                else:
                    rows.append({"width": width, "text": e["t"], "size": e["size"],
                                 "fg": fg, "bg": bg,
                                 # FLOOR, never round: 4.4996 shown as "4.50" against a
                                 # 4.5 floor reads as a tool bug and gets dismissed.
                                 "ratio": math.floor(got * 100) / 100.0, "need": need,
                                 "ok": got >= need, "exempt": e["ex"]})
                graded.add(i)

        # TARGETED PASS: whatever the stops missed (self-mutating content shifts
        # elements across stop boundaries) gets its own private stop, centred.
        leftovers = [i for i in els if i not in graded]
        for i in leftovers:
            for attempt in range(2):
                r0 = br.eval_json("JSON.stringify((%s)([%d]))" % (RECTS_JS, i)).get(str(i))
                if not r0:
                    break
                x, ry, w, h = r0
                doc_y = br.eval_json("JSON.stringify([Math.round(window.scrollY)])")[0] + ry
                br.eval(f"window.scrollTo(0,{max(0, doc_y - VIEWPORT_H // 2)})")
                br.pump(0.15)
                r1 = br.eval_json("JSON.stringify((%s)([%d]))" % (RECTS_JS, i)).get(str(i))
                if not r1 or r1[2] < 2 or r1[3] < 2:
                    break
                use_band = (0, VIEWPORT_H) if els[i].get("fx") else band
                im_a, im_b, im_c, im_a2 = _frames(br, shot)
                if not _stable(im_a, im_a2, r1, use_band):
                    continue
                res = _measure(im_a, im_b, im_c, r1, use_band)
                if res is None:
                    break
                got, no_ink, fg, bg, n = res
                e = els[i]
                need = required_ratio(e["size"], e["wt"])
                if got is None:
                    # Coverage too low for the un-blend to mean anything — see
                    # ALPHA_FLOOR. Reported through the tool's OWN unmeasurable
                    # row, the same path the skip link uses, so it appears in the
                    # UNMEASURABLE block and is never counted as a failure. My
                    # first version kept a private list and added a note, which
                    # tripped could_not_measure and failed a push over two
                    # elements the tool had simply declined to grade.
                    rows.append({"width": width, "text": e["t"],
                                 "size": e["size"], "fg": "-", "bg": "-",
                                 "ratio": 0.0, "need": need, "ok": True,
                                 "exempt": e["ex"],
                                 "unmeasurable": "glyph coverage below the "
                                                 "un-blend floor (thin anti-aliasing)"})
                    continue
                if no_ink:
                    rows.append({"width": width, "text": e["t"], "size": e["size"],
                                 "fg": fg, "bg": bg, "ratio": 1.0, "need": need,
                                 "ok": False, "exempt": e["ex"], "noink": True})
                else:
                    rows.append({"width": width, "text": e["t"], "size": e["size"],
                                 "fg": fg, "bg": bg,
                                 "ratio": math.floor(got * 100) / 100.0, "need": need,
                                 "ok": got >= need, "exempt": e["ex"]})
                graded.add(i)
                break

        missing = [els[i]["t"] for i in els if i not in graded]
        if missing:
            notes.append(f"{len(missing)} text node(s) at {width}px could not be placed in any "
                         f"viewport stop — their contrast is UNKNOWN, not passing. "
                         f"First few: {missing[:5]}")
    return rows, notes

# ---------------------------------------------------------------- calibration

def selftest(url, width, exempt=None, force_visible=".reveal"):
    rows, _ = audit(url, width, exempt=exempt, canary=True, force_visible=force_visible)
    if rows is None:
        return False, "could not instrument the page at all (is it served same-origin over http?)"
    def flagged(prefix):
        hits = [r for r in rows if r["text"].startswith(prefix[:18])]
        if not hits:
            return None
        return next((h for h in hits if not h["ok"]), False)
    checks = [(CANARY_TEXT, "plain low-contrast text"),
              (CANARY_GT_TEXT, "gradient (background-clip:text) low-contrast text"),
              (CANARY_RV_TEXT, "low-contrast text behind a .reveal fade")]
    msgs = []
    for prefix, what in checks:
        hit = flagged(prefix)
        if hit is None:
            return False, f"{what} canary was never measured — the auditor cannot see it"
        if hit is False:
            return False, f"{what} canary was measured yet reported PASSING"
        msgs.append(f"{what} {hit['ratio']:.2f}:1")
    return True, ("all three canaries correctly flagged (" + " · ".join(msgs) +
                  ") — the instrument can go red on the plain case, the old gradient "
                  "blind spot, and the reveal race")

# ------------------------------------------------------------------------ cli

def discover_pages(base="http://localhost:8000"):
    """Delegates to gatelib — see the note there on why this is defined once."""
    from gatelib import page_urls
    return page_urls(base)


def main():
    ap = argparse.ArgumentParser(description="Pixel-truth WCAG contrast audit (viewport-native, differential ink).")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--all", action="store_true",
                    help="discover every shipped page from git and check all of them")
    ap.add_argument("--widths", default="1440,1024,768")
    ap.add_argument("--exempt", default=None,
                    help='CSS selector for WCAG 1.4.3-exempt text, e.g. ".logo, .wordmark"')
    ap.add_argument("--docroot", default=os.getcwd(),
                    help="accepted for hook/CI compatibility; v3 drives pages over CDP and "
                         "writes nothing into the served tree")
    ap.add_argument("--force-visible", default=".reveal", metavar="SELECTOR",
                    help="scroll-reveal selector pinned to its settled state (DEFAULT '.reveal' — "
                         "v2 made this opt-in and a forgotten flag produced false reds; pass '' "
                         "to disable)")
    ap.add_argument("--base", default="http://localhost:8000",
                    help="origin --all builds its URLs from")
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
    fv = a.force_visible or None

    if not a.no_selftest:
        ok, msg = selftest(a.urls[0], widths[0], exempt=a.exempt, force_visible=fv)
        print(f"[calibration] {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:
            print("\nRefusing to report results. An instrument that cannot fail is not evidence.")
            gh("error", f"contrast-audit CALIBRATION FAILED — {msg}. No contrast results were "
                        f"produced; the instrument itself is broken in this environment.")
            sys.exit(2)
        if a.selftest:
            sys.exit(0)

    failures = 0
    could_not_measure = False
    for url in a.urls:
        measured = 0
        bad, exempt_bad, notes, unmeasurable = [], [], [], []
        for width in widths:
            rows, wnotes = audit(url, width, exempt=a.exempt, force_visible=fv)
            notes += [f"@{width}px: {n}" for n in (wnotes or [])]
            if rows is None:
                notes.append(f"@{width}px could not be measured")
                could_not_measure = True
                continue
            measured += len(rows)
            unmeasurable += [r for r in rows if r.get("unmeasurable")]
            bad += [r for r in rows if not r["ok"] and not r["exempt"]
                    and not r.get("unmeasurable")]
            exempt_bad += [r for r in rows if not r["ok"] and r["exempt"]]
        failures += len(bad)
        print(f"\n{url}  —  {measured} text nodes measured at {widths}")
        if measured == 0:
            gh("error", f"contrast-audit measured ZERO text nodes on {url} — the page did not "
                        f"render or could not be instrumented. Notes: {'; '.join(notes) or 'none'}")
            could_not_measure = True
        for r in bad:
            tag = "NO-INK" if r.get("noink") else "FAIL"
            print(f"  {tag} {r['ratio']:5.2f}/{r['need']}  {r['size']:>6.1f}px  "
                  f"{r['fg']} on {r['bg']}  @{r['width']}px  {r['text']!r}"
                  + ("  (paints no visible ink: invisible or obscured)" if r.get("noink") else ""))
        for r in bad[:15]:
            gh("error", f"CONTRAST {r['ratio']:.2f}:1 (needs {r['need']}) — {r['size']:.1f}px "
                        f"{r['fg']} on {r['bg']} @{r['width']}px — {url} — text: {r['text']!r}")
        if len(bad) > 15:
            gh("error", f"...and {len(bad) - 15} further contrast failures on {url}.")
        for r in exempt_bad:
            print(f"  exempt {r['ratio']:5.2f}  @{r['width']}px  {r['text']!r}  "
                  f"(declared 1.4.3-exempt — confirm that is true)")
        for n in notes:
            print(f"  NOTE  {n}")
            gh("warning", f"contrast-audit on {url}: {n}")
        if unmeasurable:
            print(f"  UNMEASURABLE by this instrument ({len(unmeasurable)}) — NOT a verdict:")
            seen_u = set()
            for r in unmeasurable:
                k = (r["text"], r["unmeasurable"])
                if k in seen_u:
                    continue
                seen_u.add(k)
                print(f"    {r['unmeasurable']}  {r['size']:>6.1f}px  @{r['width']}px  {r['text']!r}")
        if not bad:
            print("  0 failures. Blind spots of this method: text inside <canvas>, <video>, "
                  "cross-origin iframes, any state not reachable on load (hover, focus, open "
                  "menus), colours shown only mid-animation (the audit reads as a "
                  "reduced-motion visitor), and two ELIGIBLE text layers overlapping "
                  "the same pixels (graded as one) are NOT measured.")
    if failures:
        sys.exit(1)
    sys.exit(2 if could_not_measure else 0)

if __name__ == "__main__":
    main()
