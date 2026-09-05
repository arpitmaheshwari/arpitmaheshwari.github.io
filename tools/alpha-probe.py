#!/usr/bin/env python3
"""alpha-probe.py — dump the contrast audit's own arithmetic for ONE element.

WHY. The nightly sweep reports ten homepage contrast failures that are not real: every
authored pair measures 6.4:1 to 10.7:1 from the stylesheet, and every ratio reported is
roughly half that. Three hypotheses are dead, each killed by measurement rather than
argument:

  * not the page   — the runner renders identically to macOS, both drivers agreeing
  * not the fonts  — fonts.ready 54ms, real faces, authored computed colours
  * not coverage   — the ALPHA_FLOOR guard never fires on these elements

What is left is the recovery arithmetic itself:

    alpha = |C - B| / |MAGENTA - B|          coverage, from the magenta-keyed frame
    ink   = (A - (1 - alpha) * B) / alpha    the authored colour, de-aliased

The grounds it reports are all real page colours, so B is right. The inks are wrong, and
wrong in ONE direction — each is a muted, darkened version of the authored colour, which
is what you get when alpha is overestimated toward 1 and the correction is never applied.
Every flagged element is 11-12.5px; nothing larger on the same pages is flagged.

So this prints, for one named element, the actual numbers: the alpha distribution, and for
the best-covered pixels the painted A, the ground B, the keyed C, the recovered ink and
the ratio that recovery produces — beside the authored colour it should have returned.

    python3 tools/alpha-probe.py "What the two weeks held" [url] [width]

Not a gate. It grades nothing and blocks nothing.
"""
import base64
import io as _io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp  # noqa: E402

TEXT = sys.argv[1] if len(sys.argv) > 1 else "What the two weeks held"
URL = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("BASE", "http://localhost:8000") + "/"
WIDTH = int(sys.argv[3]) if len(sys.argv) > 3 else 1440

# Imported from the audit so the probe cannot drift from the thing it is probing.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "ca", os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrast-audit.py"))
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)          # safe: main() is behind if __name__ == "__main__"

FIND_JS = """(t=>{const e=[...document.querySelectorAll('*')]
  .find(x=>(x.textContent||'').trim().startsWith(t) && x.children.length===0);
 if(!e) return JSON.stringify({missing:true});
 const s=getComputedStyle(e);
 // DOCUMENT coordinates, and the frames are captured beyond the viewport. Neither
 // scrollIntoView nor window.scrollTo moves this page — it scrolls in a container — so
 // scrolling the element into a 900px viewport silently did nothing and the crop box
 // landed off-screen. Capturing the whole page instead removes the scroll from the
 // problem entirely.
 const r=e.getBoundingClientRect();
 return JSON.stringify({x:Math.round(r.left+window.scrollX), y:Math.round(r.top+window.scrollY),
   w:Math.round(r.width), h:Math.round(r.height),
   css:s.color, size:s.fontSize, weight:s.fontWeight,
   font:s.fontFamily.split(',')[0].replace(/"/g,'')});})"""


def main():
    from PIL import Image
    out = [f"element : {TEXT!r}", f"url     : {URL}  @{WIDTH}", f"platform: {sys.platform}"]

    with cdp.Browser() as br:
        br.viewport(WIDTH, ca.VIEWPORT_H)
        br.navigate(URL, settle=2.5)
        try:
            br.eval(ca.SETTLE_JS, await_promise=True)
        except Exception:
            pass
        br.eval("(function(){var st=document.createElement('style');st.id='__ca_hide';"
                "st.media='not all';st.textContent=%s;document.head.appendChild(st);})()"
                % json.dumps(ca.HIDE_TEXT_CSS))
        br.eval("(function(){var st=document.createElement('style');st.id='__ca_key';"
                "st.media='not all';st.textContent=%s;document.head.appendChild(st);})()"
                % json.dumps(ca.INK_KEY_CSS))

        info = json.loads(br.eval(f"({FIND_JS})({json.dumps(TEXT)})"))
        if info.get("missing"):
            out.append("NOT FOUND on this page")
            print("\n".join(out))
            return
        out.append(f"authored: {info['css']}  {info['size']}  w{info['weight']}  {info['font']}")
        out.append(f"box     : x{info['x']} y{info['y']} {info['w']}x{info['h']} (document coords)")

        def shot():
            r = br.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=True)
            return Image.open(_io.BytesIO(base64.b64decode(
                r.get("result", r)["data"]))).convert("RGB")

        a = shot()
        br.eval("document.getElementById('__ca_hide').media='all'"); br.pump(0.08)
        b = shot()
        br.eval("document.getElementById('__ca_hide').media='not all';"
                "document.getElementById('__ca_key').media='all'"); br.pump(0.08)
        c = shot()
        br.eval("document.getElementById('__ca_key').media='not all'")

    x0, y0 = max(info["x"], 0), max(info["y"], 0)
    x1, y1 = min(info["x"] + info["w"], a.width), min(info["y"] + info["h"], a.height)
    ap, bp, cp = (im.crop((x0, y0, x1, y1)).load() for im in (a, b, c))
    W, H = x1 - x0, y1 - y0
    out.append(f"crop    : {W}x{H}")

    rows = []
    for j in range(H):
        for i in range(W):
            pb, pc, pa = bp[i, j], cp[i, j], ap[i, j]
            alphas = []
            for ch in range(3):
                denom = ca.MAGENTA[ch] - pb[ch]
                if abs(denom) >= 48:
                    al = (pc[ch] - pb[ch]) / float(denom)
                    if -0.15 <= al <= 1.2:
                        alphas.append(min(1.0, max(0.0, al)))
            if not alphas:
                continue
            alpha = sorted(alphas)[len(alphas) // 2]
            if alpha < 0.12:
                continue
            rows.append((alpha, pa, pb, pc))

    if not rows:
        out.append("NO GLYPH PIXELS — frame C shows no keyed ink here at all")
        print("\n".join(out))
        return

    rows.sort(key=lambda r: -r[0])
    al = [r[0] for r in rows]
    out.append(f"pixels  : {len(rows)} with alpha>=0.12   "
               f"max={max(al):.2f} p90={al[int(len(al)*0.10)]:.2f} "
               f"median={al[len(al)//2]:.2f} min={min(al):.2f}")
    out.append(f"          ALPHA_CORE={ca.ALPHA_CORE}  "
               f"bar would be {min(ca.ALPHA_CORE, max(0.35, max(al) * 0.85)):.2f}")
    out.append("")
    out.append("  the eight best-covered pixels — A painted, B ground, C keyed, recovered ink")
    for alpha, pa, pb, pc in rows[:8]:
        ink = tuple(min(255, max(0, int(round((pa[ch] - (1 - alpha) * pb[ch]) / alpha))))
                    for ch in range(3))
        out.append(f"    a={alpha:.3f}  A={pa}  B={pb}  C={pc}"
                   f"  ->ink=#{ink[0]:02X}{ink[1]:02X}{ink[2]:02X}"
                   f"  ratio={ca.ratio(ink, pb):.2f}")

    body = "\n".join(out)
    print(body)
    if os.environ.get("GITHUB_ACTIONS"):
        print("::error title=alpha-probe::" +
              "%0A".join(l.replace("%", "%25") for l in body.splitlines()))


if __name__ == "__main__":
    main()
