#!/usr/bin/env python3
"""Structural regression suite: prove the COMPUTED STYLES did not move.

WHY THIS EXISTS (2026-08-18)
The companion to tools/visual-regression.py. Pixels and structure fail
differently, and a refactor needs both:
  * pixels catch what the DOM cannot — paint order, z-index, a gradient
    overlay, a shadow, anything the browser composites;
  * computed styles catch what pixels cannot — a rule that now wins by
    accident but happens to hold the same value, a property that changed on an
    element currently off-screen or empty, a colour that is identical today
    only because the element has no text in it yet.
A CSS restructure that passes only one of the two has not been verified, it has
been half-verified.

WHAT IT RECORDS
For every element carrying a class or id: its tag, its identity, its position
and size (rounded to the pixel), and the computed values of the properties a
stylesheet actually decides — font, colour, background, border, spacing,
display/position, overflow, z-index, transform, opacity. Keyed by a stable
path (tag + nth-of-type chain), so an element is comparable across runs even
if its class list is what changed.

CALIBRATION is two-sided, same as the visual suite: the same page twice must
snapshot IDENTICALLY (or every later "no change" is noise), and a planted
property change must be reported (or it is a consistent liar).

USAGE
  dom-snapshot.py --calibrate
  dom-snapshot.py --baseline [--widths 390,1440] [--pages a.html,b.html]
  dom-snapshot.py --compare
"""
import argparse, json, os, pathlib, shutil, signal, subprocess, sys, tempfile, time, urllib.request
import websocket

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "dom"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PROPS = ["display", "position", "float", "boxSizing", "fontFamily", "fontSize", "fontWeight",
         "fontStyle", "lineHeight", "letterSpacing", "textAlign", "textTransform",
         "textDecorationLine", "color", "backgroundColor", "backgroundImage", "opacity",
         "borderTopWidth", "borderRightWidth", "borderBottomWidth", "borderLeftWidth",
         "borderTopColor", "borderRadius", "marginTop", "marginRight", "marginBottom",
         "marginLeft", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
         "overflowX", "overflowY", "zIndex", "transform", "flexDirection", "justifyContent",
         "alignItems", "gap", "gridTemplateColumns", "maxWidth", "minWidth", "whiteSpace"]

PROBE = r"""
(async () => {
  const PROPS = %s;
  if (document.fonts && document.fonts.ready) await document.fonts.ready;
  // same reveal race as visual-regression.py: observer callbacks are async, so
  // wait for the revealed-element count to stop moving rather than sleeping a
  // fixed amount and hoping. This suite passed calibration without it, which
  // means it passed by luck.
  const h = document.body.scrollHeight;
  for (let y = 0; y < h; y += 500) { scrollTo(0, y); await new Promise(r => setTimeout(r, 20)); }
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
  const s = document.createElement('style');
  s.textContent = '*,*::before,*::after{transition:none!important;animation:none!important}';
  document.head.append(s);
  await new Promise(r => setTimeout(r, 250));

  // a path that survives the thing we are most likely to change: the class list
  const pathOf = el => {
    const parts = [];
    for (let n = el; n && n.tagName && n.tagName !== 'HTML'; n = n.parentElement) {
      const tag = n.tagName.toLowerCase();
      let i = 1, sib = n;
      while ((sib = sib.previousElementSibling)) if (sib.tagName === n.tagName) i++;
      parts.unshift(tag + (i > 1 ? `:${i}` : ''));
    }
    return parts.join('>');
  };
  const out = {};
  document.querySelectorAll('body *').forEach(el => {
    if (!el.className && !el.id) return;
    if (el.namespaceURI === 'http://www.w3.org/2000/svg') return;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const rec = {
      id: el.id || '',
      cls: (el.className + '').trim().split(/\s+/).sort().join(' '),
      box: [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)],
    };
    PROPS.forEach(p => { rec[p] = cs[p]; });
    out[pathOf(el)] = rec;
  });
  return JSON.stringify(out);
})()
"""


class Snap:
    def __init__(self):
        self.port = 9760 + (os.getpid() % 70)
        self.prof = tempfile.mkdtemp(prefix="ds-")
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
             f"--user-data-dir={self.prof}", "--no-first-run", "--remote-allow-origins=*",
             "--hide-scrollbars", "--force-device-scale-factor=1"],
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

    def take(self, url, width, extra_css=""):
        self.cmd("Emulation.setDeviceMetricsOverride", width=width, height=1000,
                 deviceScaleFactor=1, mobile=width < 700)
        nav = self.cmd("Page.navigate", url=url)
        if nav.get("errorText"):
            raise RuntimeError(f"did not load: {nav['errorText']}")
        time.sleep(1.3)
        if extra_css:
            self.cmd("Runtime.evaluate", returnByValue=True, expression=(
                "(()=>{const s=document.createElement('style');"
                f"s.textContent={json.dumps(extra_css)};document.head.append(s);return 1}})()"))
        r = self.cmd("Runtime.evaluate", expression=PROBE % json.dumps(PROPS),
                     awaitPromise=True, returnByValue=True)
        return json.loads(r["result"]["value"])

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


def diff(old, new):
    """Return (gone, added, changed) — changed is [(path, prop, before, after)]."""
    gone = [k for k in old if k not in new]
    added = [k for k in new if k not in old]
    changed = []
    for k in old:
        if k not in new:
            continue
        a, b = old[k], new[k]
        for p in a:
            if p == "cls":       # a class RENAME is the point of the refactor
                continue
            if a[p] != b.get(p):
                changed.append((k, p, a[p], b.get(p)))
    return gone, added, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--widths", default="390,1440")
    ap.add_argument("--pages", default="")
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--max-report", type=int, default=25)
    a = ap.parse_args()
    widths = [int(x) for x in a.widths.split(",")]
    pgs = pages([p.strip() for p in a.pages.split(",") if p.strip()] or None)
    OUT.mkdir(parents=True, exist_ok=True)
    snap = Snap()
    try:
        if a.calibrate:
            url = f"{a.base}/{pgs[0]}"
            one = snap.take(url, 1440); two = snap.take(url, 1440)
            g, ad, ch = diff(one, two)
            if g or ad or ch:
                print(f"[calibration] DETERMINISM FAILED — same page twice differs: "
                      f"{len(g)} gone, {len(ad)} added, {len(ch)} changed")
                for c in ch[:5]:
                    print(f"    {c[0]} {c[1]}: {c[2]!r} -> {c[3]!r}")
                return 2
            print(f"[calibration] DETERMINISM PASS — {len(one)} elements, identical twice")
            three = snap.take(url, 1440, extra_css="p{letter-spacing:0.01px}")
            g2, a2, c2 = diff(one, three)
            if not c2:
                print("[calibration] SENSITIVITY FAILED — a planted property change "
                      "was not reported.")
                return 2
            print(f"[calibration] SENSITIVITY PASS — planted change reported "
                  f"({len(c2)} property diff(s))")
            print("\nBoth sides proven. The suite can be trusted.")
            return 0

        if a.baseline:
            n = 0
            for rel in pgs:
                for w in widths:
                    data = snap.take(f"{a.base}/{rel}", w)
                    (OUT / f"{rel.replace('/', '__').replace('.html','')}__{w}.json").write_text(
                        json.dumps(data, sort_keys=True, indent=0))
                    n += len(data)
                print(f"  snapshot {rel}")
            print(f"\nbaseline: {n} element records in {OUT.relative_to(ROOT)}")
            return 0

        if a.compare:
            total = 0
            for rel in pgs:
                for w in widths:
                    f = OUT / f"{rel.replace('/', '__').replace('.html','')}__{w}.json"
                    if not f.exists():
                        continue
                    old = json.loads(f.read_text())
                    new = snap.take(f"{a.base}/{rel}", w)
                    g, ad, ch = diff(old, new)
                    if g or ad or ch:
                        total += len(g) + len(ad) + len(ch)
                        print(f"FAIL {rel} @{w} — {len(g)} gone, {len(ad)} added, "
                              f"{len(ch)} property change(s)")
                        for c in ch[:a.max_report]:
                            print(f"      {c[0][-60:]}")
                            print(f"        {c[1]}: {c[2]!r} -> {c[3]!r}")
                        for k in g[:5]:
                            print(f"      GONE  {k[-70:]}")
                    else:
                        print(f"ok   {rel} @{w}")
            print(f"\n{total} structural difference(s).")
            print("CANNOT SEE: paint-level results — compositing, z-order, shadows, "
                  "gradients. That is tools/visual-regression.py's job; run both.")
            return 1 if total else 0

        ap.print_help(); return 2
    finally:
        snap.close()


if __name__ == "__main__":
    sys.exit(main())
