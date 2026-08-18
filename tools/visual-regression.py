#!/usr/bin/env python3
"""Pixel-level regression suite: prove a change altered NOTHING it shouldn't.

WHY THIS EXISTS (2026-08-18)
Arpit: "write a visual or DOM testing suite so that you can test the changes
you are making and don't rely on me." Every gate in tools/ answers a question
about ONE property (contrast, leading, reachability). None answers the question
a refactor actually needs: *did this change what a visitor sees?*

A CSS restructure is only correct if the rendered site is unchanged. That is
not a claim to make by reading a diff — it is a claim to make by comparing
pixels, page by page, width by width.

TWO-SIDED CALIBRATION (--calibrate), because one side alone proves nothing:
  DETERMINISM  capture the same page twice; the images must be IDENTICAL. If
               the harness is noisy, every later "0 changed pixels" is luck and
               every real diff drowns in that noise.
  SENSITIVITY  plant a 1px shift; the diff must go non-zero. A stable harness
               that cannot see a change is a very consistent liar.

DETERMINISM IS ENGINEERED, NOT HOPED FOR: fonts awaited (document.fonts.ready),
every image decoded, transitions and animations killed, caret hidden, the page
scrolled end-to-end first so reveal-on-scroll observers have all fired, then
returned to the top. Without the scroll pass, half the page captures in its
pre-reveal state and the "baseline" is a photograph of a page mid-animation.

USAGE
  visual-regression.py --calibrate            prove the instrument, then stop
  visual-regression.py --baseline             capture tests/visual/baseline/
  visual-regression.py --compare              diff current render vs baseline
  visual-regression.py --compare --write-diff also write red-overlay diff PNGs
  optional: --widths 390,768,1440  --pages index.html,lab/index.html
"""
import argparse, base64, io, json, os, pathlib, shutil, signal, subprocess, sys, tempfile, time, urllib.request
import numpy as np
from PIL import Image
import websocket

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "visual"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SETTLE = r"""
(async () => {
  // 1. fonts — a capture before they load is a capture of fallback metrics
  const cap_ = (pr, ms) => Promise.race([pr, new Promise(r => setTimeout(r, ms))]);
  if (document.fonts && document.fonts.ready) await cap_(document.fonts.ready, 5000);
  // 2. reveal-on-scroll: walk the whole page so every IntersectionObserver fires
  // Scroll the whole page so every IntersectionObserver fires, then WAIT FOR
  // THE REVEAL COUNT TO STOP CHANGING. A fixed sleep is not enough: observer
  // callbacks are async and this page is ~9,000px tall, so one run in three
  // captured before the last elements had gained `.visible` — a reproducible
  // 116,581px difference that looked exactly like noise but was a race.
  // Poll until the count is stable across three consecutive checks, or bail
  // loudly rather than silently photographing a half-revealed page.
  const h = document.body.scrollHeight;
  for (let y = 0; y < h; y += 400) { scrollTo(0, y); await new Promise(r => setTimeout(r, 20)); }
  scrollTo(0, 0);
  const count = () => document.querySelectorAll('.visible,[data-viewed]').length;
  let last = -1, stable = 0, spins = 0;
  while (stable < 3 && spins++ < 100) {
    await new Promise(r => setTimeout(r, 50));
    const c = count();
    stable = (c === last) ? stable + 1 : 0;
    last = c;
  }
  if (spins >= 100) throw new Error('reveal state never settled');
  // 3. kill motion so nothing is caught mid-flight, and hide the caret
  const s = document.createElement('style');
  s.textContent = '*,*::before,*::after{transition:none!important;animation:none!important;' +
                  'animation-duration:0s!important;scroll-behavior:auto!important;' +
                  'caret-color:transparent!important}';
  document.head.append(s);
  // 4. NON-DETERMINISTIC PAINT must be masked, not wished away. The homepage
  //    runs two <canvas> particle systems seeded with Math.random(), so two
  //    captures of the same page differ by ~116,000 px. Hiding the canvas keeps
  //    its BOX in the layout (so any change to its size or position still shows
  //    up as a pixel shift in everything around it) while removing the only
  //    content on the page that is random by design. What is inside a canvas is
  //    therefore NOT covered by this suite — dom-snapshot.py still checks its
  //    geometry, and nothing checks its drawing. Stated, not hidden.
  const mask = document.createElement('style');
  mask.textContent = 'canvas{visibility:hidden!important}';
  document.head.append(mask);
  // 5. every image actually decoded, not merely requested
  // decode() on an image that never finishes loading NEVER SETTLES — one such
  // image on a case-study page hung the whole capture past the socket timeout
  // and looked exactly like "tall pages are slow". Race every decode against a
  // deadline so a single stalled asset cannot hang the suite.
  const withTimeout = (pr, ms) => Promise.race([pr, new Promise(r => setTimeout(r, ms))]);
  await withTimeout(Promise.all([...document.images].map(i =>
    (i.decode ? i.decode().catch(() => {}) : Promise.resolve()))), 4000);
  await new Promise(r => setTimeout(r, 350));
  return document.body.scrollHeight;
})()
"""


class Cap:
    def __init__(self):
        self.port = 9700 + (os.getpid() % 80)
        self.prof = tempfile.mkdtemp(prefix="vr-")
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
             f"--user-data-dir={self.prof}", "--no-first-run", "--remote-allow-origins=*",
             "--hide-scrollbars", "--force-device-scale-factor=1",
             "--font-render-hinting=none", "--disable-lcd-text",
             "--disable-features=PaintHolding"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws_url = None
        for _ in range(90):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(.15)
        if not ws_url:
            raise RuntimeError("chrome never came up")
        self.ws = websocket.create_connection(ws_url, timeout=180)
        self.n = 0
        self.cmd("Page.enable"); self.cmd("Runtime.enable")

    def cmd(self, m, **kw):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": m, "params": kw}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(f"{m}: {r['error']}")
                return r.get("result", {})

    def shoot(self, url, width, extra_css=""):
        self.cmd("Emulation.setDeviceMetricsOverride", width=width, height=1000,
                 deviceScaleFactor=1, mobile=width < 700)
        nav = self.cmd("Page.navigate", url=url)
        if nav.get("errorText"):
            raise RuntimeError(f"did not load: {nav['errorText']}")
        time.sleep(1.4)
        self.cmd("Runtime.evaluate", expression=SETTLE, awaitPromise=True, returnByValue=True)
        if extra_css:
            self.cmd("Runtime.evaluate", returnByValue=True, expression=(
                "(()=>{const s=document.createElement('style');"
                f"s.textContent={json.dumps(extra_css)};document.head.append(s);return 1}})()"))
            time.sleep(.25)
        return self._stitch(width)

    # A full-page capture has two obvious implementations and both are traps.
    #   captureBeyondViewport on a tall page HANGS — /case-studies at 390px is
    #     18,000-23,000px tall and a single capture never returned inside 120s.
    #   Resizing the viewport to the full page height returns in 1.5s, and is
    #     WRONG for this site: the case-study h1 is clamp(38px,min(6vw,8.4vh),82px),
    #     so a taller viewport renders larger type. The screenshot would show
    #     something no visitor ever sees, and the baseline would be a fiction.
    # So: keep the viewport honest (vh units stay correct), capture it a screen
    # at a time, and stitch. Sticky/fixed chrome is hidden after the first slice
    # so the nav does not reprint down the page; visibility:hidden leaves layout
    # untouched.
    VH = 1000

    def _stitch(self, width):
        h = int(self.cmd("Page.getLayoutMetrics")["cssContentSize"]["height"])
        canvas = Image.new("RGB", (width, h), (0, 0, 0))
        y, first = 0, True
        while y < h:
            r = self.cmd("Runtime.evaluate", returnByValue=True, expression=(
                f"(()=>{{scrollTo(0,{y});return Math.round(window.scrollY)}})()"))
            actual = int(r["result"]["value"])
            if first:
                first = False
            else:
                # READ EVERYTHING FIRST, THEN WRITE. The first version called
                # getComputedStyle and setAttribute in the same loop, which
                # forces a synchronous layout per element; on an 18,000px page
                # that turned a 7-second capture into a multi-minute hang that
                # looked for all the world like "tall pages are slow". The
                # slices themselves measure 0.02s each.
                self.cmd("Runtime.evaluate", returnByValue=True, expression=(
                    "(()=>{if(document.getElementById('__vrfix'))return 1;"
                    "const marks=[];"
                    "document.querySelectorAll('body *').forEach(e=>{"
                    "const p=getComputedStyle(e).position;"
                    "if(p==='fixed'||p==='sticky')marks.push(e)});"
                    "marks.forEach(e=>e.setAttribute('data-vrfix',''));"
                    "const s=document.createElement('style');s.id='__vrfix';"
                    "s.textContent='[data-vrfix]{visibility:hidden!important}';"
                    "document.head.append(s);return marks.length})()"))
            time.sleep(.12)
            img = self.cmd("Page.captureScreenshot", format="png",
                           clip={"x": 0, "y": 0, "width": width,
                                 "height": min(self.VH, h - actual), "scale": 1})
            slice_img = Image.open(io.BytesIO(base64.b64decode(img["data"]))).convert("RGB")
            canvas.paste(slice_img, (0, actual))
            if actual + self.VH >= h:
                break
            y = actual + self.VH
        buf = io.BytesIO(); canvas.save(buf, format="PNG")
        return buf.getvalue()

    def close(self):
        try:
            self.proc.send_signal(signal.SIGKILL); self.proc.wait(timeout=10)
        finally:
            shutil.rmtree(self.prof, ignore_errors=True)


def pages(limit=None):
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.startswith(x) for x in ("prototypes/", "portfolio-sources/", ".", "tests/")):
            continue
        if p.name.startswith("__") or "og-images" in rel:
            continue
        out.append(rel)
    if limit:
        want = set(limit)
        out = [p for p in out if p in want]
    return out


def key(rel, w):
    return f"{rel.replace('/', '__').replace('.html', '')}__{w}"


def compare(a: bytes, b: bytes):
    ia = np.array(Image.open(io.BytesIO(a)).convert("RGB"), dtype=np.int16)
    ib = np.array(Image.open(io.BytesIO(b)).convert("RGB"), dtype=np.int16)
    if ia.shape != ib.shape:
        return {"shape": (ia.shape, ib.shape), "changed": -1, "pct": 100.0, "box": None}
    d = np.abs(ia - ib).sum(axis=2)
    mask = d > 0
    changed = int(mask.sum())
    box = None
    if changed:
        ys, xs = np.where(mask)
        box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return {"shape": None, "changed": changed,
            "pct": round(100.0 * changed / mask.size, 4), "box": box, "mask": mask,
            "img": ib}


def write_diff(res, path):
    img = res["img"].astype(np.uint8).copy()
    img[res["mask"]] = [255, 0, 90]
    Image.fromarray(img).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--write-diff", action="store_true")
    ap.add_argument("--widths", default="390,768,1440")
    ap.add_argument("--pages", default="")
    ap.add_argument("--base", default="http://localhost:8000")
    a = ap.parse_args()
    widths = [int(x) for x in a.widths.split(",")]
    pgs = pages([p.strip() for p in a.pages.split(",") if p.strip()] or None)
    base_dir = OUT / "baseline"; diff_dir = OUT / "diff"
    cap = Cap()
    try:
        # ── CALIBRATION ───────────────────────────────────────────────────────
        if a.calibrate:
            url = f"{a.base}/{pgs[0]}"
            one = cap.shoot(url, 1440); two = cap.shoot(url, 1440)
            det = compare(one, two)
            if det["changed"] != 0:
                print(f"[calibration] DETERMINISM FAILED — same page twice differs by "
                      f"{det['changed']} px ({det['pct']}%) at {det['box']}.")
                print("  Every later '0 changed pixels' would be luck. Fix the harness first.")
                return 2
            print("[calibration] DETERMINISM PASS — same page twice is pixel-identical")
            # Sensitivity must be proven with a change that does NOT alter the
            # page's SIZE — otherwise the test passes on the trivial case (a
            # different image height) and says nothing about whether the
            # comparison can see a repaint. A one-step colour shift on body
            # text keeps every box exactly where it was.
            three = cap.shoot(url, 1440, extra_css="p,li,h1,h2,h3{color:#f4ece5!important}")
            sens = compare(one, three)
            if sens["shape"] is not None:
                print("[calibration] SENSITIVITY INCONCLUSIVE — the planted colour change "
                      "altered page size; that tests the wrong thing.")
                return 2
            if sens["changed"] == 0:
                print("[calibration] SENSITIVITY FAILED — a planted colour change at "
                      "IDENTICAL layout was invisible. This suite would pass a repaint bug.")
                return 2
            print(f"[calibration] SENSITIVITY PASS — colour change at identical layout seen "
                  f"({sens['changed']} px, {sens['pct']}%)")
            print("\nBoth sides proven. The suite can be trusted.")
            return 0

        # ── BASELINE ──────────────────────────────────────────────────────────
        if a.baseline:
            base_dir.mkdir(parents=True, exist_ok=True)
            n = 0
            for rel in pgs:
                for w in widths:
                    png = cap.shoot(f"{a.base}/{rel}", w)
                    (base_dir / f"{key(rel, w)}.png").write_bytes(png)
                    n += 1
                print(f"  captured {rel}")
            print(f"\nbaseline: {n} image(s) in {base_dir.relative_to(ROOT)}")
            return 0

        # ── COMPARE ───────────────────────────────────────────────────────────
        if a.compare:
            if not base_dir.exists():
                print("no baseline — run --baseline first"); return 2
            if a.write_diff:
                diff_dir.mkdir(parents=True, exist_ok=True)
            bad, checked, missing = [], 0, 0
            for rel in pgs:
                for w in widths:
                    bp = base_dir / f"{key(rel, w)}.png"
                    if not bp.exists():
                        missing += 1; continue
                    cur = cap.shoot(f"{a.base}/{rel}", w)
                    res = compare(bp.read_bytes(), cur)
                    checked += 1
                    if res["changed"] != 0:
                        bad.append((rel, w, res))
                        if a.write_diff and res["shape"] is None:
                            write_diff(res, diff_dir / f"{key(rel, w)}.png")
            print()
            for rel, w, res in bad:
                if res["shape"]:
                    print(f"FAIL {rel} @{w} — SIZE changed {res['shape'][0]} -> {res['shape'][1]}")
                else:
                    print(f"FAIL {rel} @{w} — {res['changed']} px ({res['pct']}%) "
                          f"changed, region x{res['box'][0]}-{res['box'][2]} "
                          f"y{res['box'][1]}-{res['box'][3]}")
            print(f"\n{checked} image(s) compared, {len(bad)} changed"
                  + (f", {missing} had no baseline" if missing else ""))
            if a.write_diff and bad:
                print(f"diff images (changed pixels in magenta): {diff_dir.relative_to(ROOT)}")
            print("\nCANNOT SEE: anything behind interaction (hover, focus, open menus, "
                  "driven widgets), and the CONTENTS of any <canvas> (masked: the "
                  "homepage particle systems are random by design).")
            return 1 if bad else 0

        ap.print_help(); return 2
    finally:
        cap.close()


if __name__ == "__main__":
    sys.exit(main())
