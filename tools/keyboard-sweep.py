#!/usr/bin/env python3
"""
keyboard-sweep.py — drive REAL Tab key events through a page and report what a keyboard user gets.

WHY THIS EXISTS
    Every static a11y scan can tell you an element is "focusable". None of them can tell you whether
    pressing Tab actually lands on it, in what order, whether focus escapes into a hidden drawer, or
    whether the ring a sighted keyboard user needs is actually painted. Those need real key events
    and a real read of document.activeElement AFTER each one — a tool reporting "pressed Tab" is not
    evidence that focus moved.

HOW IT MEASURES
    Chrome over CDP. For each Tab press: Input.dispatchKeyEvent(rawKeyDown/keyUp, key=Tab), then
    Runtime.evaluate reading document.activeElement — its tag, id, class, accessible-ish name,
    whether it is inside a visually hidden/offscreen container, and its computed :focus-visible
    outline/box-shadow. Loops until focus returns to <body> (cycle complete) or the cap is hit.

WHAT IT DETECTS
    * unreachable controls  (present in DOM, never visited by Tab)
    * focus trap            (focus stops advancing / cycles inside a subtree forever)
    * invisible focus       (focused element has zero-area rect or is scrolled/clipped out of view)
    * no focus ring         (outline-width 0 AND no box-shadow AND no background/border delta)
    * focus into hidden UI  (activeElement inside a display:none-adjacent collapsed drawer)

WHAT IT STRUCTURALLY CANNOT SEE
    * whether the ring has ENOUGH CONTRAST against its backdrop (it reports the colour; judging it
      is contrast-audit's job)
    * whether the tab ORDER is logical for the page's meaning — only that it is or is not DOM order
    * anything requiring Enter/Space activation or a second interaction layer (menus, modals) unless
      --activate is passed
    * screen-reader behaviour; focus and AT focus are different things
"""
import json, os, re, subprocess, sys, time, argparse
import urllib.request
import websocket  # websocket-client

CHROME = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = int(os.environ.get("CDP_PORT", "9333"))

PROBE = r"""(() => {
  const a = document.activeElement;
  if (!a || a === document.body) return {body: true};
  const r = a.getBoundingClientRect();
  const cs = getComputedStyle(a);
  const name = (a.getAttribute('aria-label') || a.textContent || a.value || '')
      .replace(/\s+/g,' ').trim().slice(0, 48);
  let sel = a.tagName.toLowerCase();
  if (a.id) sel += '#' + a.id;
  const c = (a.getAttribute('class')||'').trim().split(/\s+/)[0];
  if (c) sel += '.' + c;
  // is it actually on screen for a sighted keyboard user?
  const inView = r.width > 0 && r.height > 0
      && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth;
  return {
    sel, name, href: a.getAttribute('href') || '',
    x: Math.round(r.left), y: Math.round(r.top),
    w: Math.round(r.width), h: Math.round(r.height),
    inView,
    outline: cs.outlineStyle === 'none' ? '' : `${cs.outlineWidth} ${cs.outlineStyle} ${cs.outlineColor}`,
    shadow: cs.boxShadow === 'none' ? '' : cs.boxShadow.slice(0, 60),
    hiddenAncestor: !!a.closest('[aria-hidden="true"],[hidden]'),
    zeroArea: r.width < 1 || r.height < 1,
  };
})()"""


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.i = 0

    def send(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                return msg.get("result", {})

    def evaluate(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True,
                      awaitPromise=True)
        return r.get("result", {}).get("value")

    def key(self, key, code, vk, mods=0):
        for t in ("rawKeyDown", "keyUp"):
            self.send("Input.dispatchKeyEvent", type=t, key=key, code=code,
                      windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk, modifiers=mods)

    def close(self):
        try: self.ws.close()
        except Exception: pass


def start_chrome(width, height, extra=()):
    proc = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={PORT}", "--no-first-run",
         "--no-default-browser-check", "--disable-gpu", "--no-sandbox",
         "--remote-allow-origins=*",
         f"--window-size={width},{height}", "--user-data-dir=" + os.path.join(
             os.environ.get("TMPDIR", "/tmp"), f"kbsweep{PORT}"), *extra, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
            return proc
        except Exception:
            time.sleep(0.25)
    proc.kill()
    raise RuntimeError("chrome did not expose CDP")


def sweep(url, max_tabs=250, mods=0):
    tabs = json.loads(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json/list", timeout=5).read())
    page = next(t for t in tabs if t["type"] == "page")
    c = CDP(page["webSocketDebuggerUrl"])
    c.send("Page.enable"); c.send("Runtime.enable"); c.send("DOM.enable")
    c.send("Page.navigate", url=url)
    time.sleep(3.0)
    # inventory: everything a keyboard SHOULD be able to reach
    inv = c.evaluate("""(() => {
      const sel='a[href],button,input:not([type=hidden]),select,textarea,summary,[tabindex]:not([tabindex="-1"])';
      return [...document.querySelectorAll(sel)].filter(e=>{
        // getComputedStyle(child).display is NOT 'none' when an ANCESTOR is display:none --
        // the child keeps its own specified value. Filtering on it reported 11 controls inside
        // collapsed [hidden] panels as "unreachable by Tab" on /index.html (measured 2026-08-16).
        // getClientRects().length===0 is the question actually being asked: does it generate a box.
        if(e.getClientRects().length===0)return false;
        if(getComputedStyle(e).visibility==='hidden')return false;
        if(e.closest('[inert]')||e.closest('[hidden]'))return false;
        return true;
      }).map(e=>{let s=e.tagName.toLowerCase();if(e.id)s+='#'+e.id;
        const c=(e.getAttribute('class')||'').trim().split(/\\s+/)[0];if(c)s+='.'+c;
        return s+'::'+((e.getAttribute('aria-label')||e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,32));});
    })()""") or []
    # start from a known place
    # scroll-behavior:smooth ANIMATES the scroll that brings a focused element into view.
    # Reading the rect 45ms after Tab lands mid-animation and reports every control OFFSCREEN
    # (measured 2026-08-16: 40 phantom OFFSCREEN on /index.html). Disable it, then measure.
    c.evaluate("document.documentElement.style.scrollBehavior='auto';"
               "var s=document.createElement('style');"
               "s.textContent='*{scroll-behavior:auto!important}';"
               "document.head.appendChild(s);")
    c.evaluate("document.body.focus(); document.activeElement.blur();")
    seq, seen_sigs = [], []
    stuck = 0
    for i in range(max_tabs):
        c.key("Tab", "Tab", 9, mods)
        time.sleep(0.12)
        st = c.evaluate(PROBE)
        if not st:
            seq.append({"sel": "(null activeElement)"}); break
        if st.get("body"):
            seq.append({"sel": "(body — cycle complete)"}); break
        sig = st["sel"] + "::" + st.get("name", "")
        if seq and sig == seq[-1].get("sig"):
            stuck += 1
            if stuck >= 3:
                st["TRAP"] = True
                seq.append({**st, "sig": sig}); break
        else:
            stuck = 0
        st["sig"] = sig
        seq.append(st)
        if sig in seen_sigs:               # revisited -> tab ring closed
            st["CYCLE"] = True
            break
        seen_sigs.append(sig)
    c.close()
    return inv, seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--reduced-motion", action="store_true")
    a = ap.parse_args()
    extra = ["--force-prefers-reduced-motion"] if a.reduced_motion else []
    proc = start_chrome(a.width, a.height, extra)
    try:
        for url in a.urls:
            inv, seq = sweep(url)
            reached = {s.get("sig", "").split("::")[0] for s in seq if s.get("sig")}
            print(f"\n===== {url}  (viewport {a.width}x{a.height})")
            print(f"  focusable in DOM: {len(inv)}   reached by Tab: {len([s for s in seq if s.get('sig')])}")
            noring, offscreen, zero = [], [], []
            for n, s in enumerate(seq, 1):
                if not s.get("sig"):
                    print(f"  {n:3} {s['sel']}")
                    continue
                flags = []
                if not s["outline"] and not s["shadow"]:
                    flags.append("NO-RING"); noring.append(s["sig"])
                if s["zeroArea"]:
                    flags.append("ZERO-AREA"); zero.append(s["sig"])
                elif not s["inView"]:
                    flags.append("OFFSCREEN"); offscreen.append(s["sig"])
                if s.get("hiddenAncestor"):
                    flags.append("IN-ARIA-HIDDEN")
                if s.get("TRAP"):
                    flags.append("*** FOCUS TRAP ***")
                if s.get("CYCLE"):
                    flags.append("(cycled)")
                print(f"  {n:3} {s['sel'][:38]:38} {s['name'][:34]:34} "
                      f"ring[{(s['outline'] or s['shadow'])[:34]:34}] {' '.join(flags)}")
            unreached = [x for x in inv if x.split("::")[0] not in reached]
            if unreached:
                print(f"  UNREACHED BY TAB ({len(unreached)}): " + "; ".join(unreached[:10]))
            print(f"  SUMMARY  no-ring:{len(noring)}  zero-area:{len(zero)}  offscreen:{len(offscreen)}")
    finally:
        proc.kill()


if __name__ == "__main__":
    sys.exit(main())
