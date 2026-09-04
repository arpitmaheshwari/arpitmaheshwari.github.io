#!/usr/bin/env python3
"""One headless-Chrome harness, shared by the gates that need a browser.

WHY (2026-08-19, architecture review)
Five tools each launched their own Chrome and defined their own CDP `cmd()`
helper — roughly 460 lines of the same code, five times. The cost was not the
duplication itself but that every fix had to be made five times, and was not:
the load-failure guard that stops a gate reporting a verdict on a page that
never loaded existed in two tools and was missing from three, so those three
would happily have called a dead server clean.

WHAT IT GUARANTEES, so no caller has to remember
  * navigate() FAILS LOUDLY on a navigation error rather than returning a
    blank page. An empty result must mean "looked and found nothing", never
    "there was nothing to look at".
  * the browser is always killed and its profile removed, even on exception.
  * one place to fix a timeout, a flag, or a protocol change.
"""
import json, os, shutil, signal, socket, subprocess, tempfile, time, urllib.request
import websocket

def _find_chrome():
    """Resolve Chrome, honouring $CHROME first.

    This module hardcoded the macOS bundle path. Every CI runner is Linux, so the
    Contrast gate died with FileNotFoundError on '/Applications/Google Chrome.app/...'
    the moment it was finally able to import — after the websocket-client fix let it get
    that far. The workflow's "Locate Chrome" step had been exporting $CHROME all along
    and nothing here read it. asset-load-check.py already did exactly this; cdp.py, which
    every browser-driving gate imports, did not.
    """
    from_env = os.environ.get("CHROME")
    if from_env and (os.path.isabs(from_env) or shutil.which(from_env)):
        return from_env
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome-stable", "google-chrome", "chromium-browser", "chromium",
        "/usr/bin/google-chrome-stable", "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser", "/usr/bin/chromium",
    ]
    for c in candidates:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            found = shutil.which(c)
            if found:
                return found
    # Nothing found: return the env value or the first candidate so the eventual
    # FileNotFoundError names something real rather than failing silently later.
    return from_env or candidates[0]


CHROME = _find_chrome()


# Every page on this site loads Google Analytics AND Microsoft Clarity, so
# every page a gate opened sent a real pageview and a real session recording.
# One full sweep is ~844 page loads; a day of work is thousands. Arpit reads
# those numbers to judge whether his outreach is landing, so a gate that
# inflates them is worse than no gate — it corrupts the decision the data is
# for. Resolution is refused at the DNS level, which works for every way we
# launch Chrome, including --dump-dom where there is no CDP session to hook.
TRACKER_HOSTS = [
    "www.googletagmanager.com", "googletagmanager.com",
    "www.google-analytics.com", "google-analytics.com",
    "analytics.google.com", "ssl.google-analytics.com",
    "region1.google-analytics.com", "region1.analytics.google.com",
    "*.clarity.ms", "clarity.ms",
    "c.bing.com", "bat.bing.com",
    "stats.g.doubleclick.net", "*.doubleclick.net",
]
NO_TRACKING_FLAG = "--host-resolver-rules=" + ",".join(
    f"MAP {h} ~NOTFOUND" for h in TRACKER_HOSTS)


class Browser:
    """A headless Chrome speaking CDP. Use as a context manager."""

    def __init__(self, port_base=9300, timeout=90, extra_flags=()):
        # ASK THE OS FOR A FREE PORT. This was port_base + (os.getpid() % 200), which is
        # per-PROCESS: six Browser() instances inside one process all computed the SAME
        # port, collided, and five of six died with net::ERR_ABORTED. Even across
        # processes it collides whenever two pids differ by a multiple of 200. Binding to
        # port 0 and reading the assignment back cannot collide with anything.
        with socket.socket() as _s0:
            _s0.bind(('127.0.0.1', 0))
            self.port = _s0.getsockname()[1]
        self.profile = tempfile.mkdtemp(prefix="cdp-")
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
             f"--user-data-dir={self.profile}", "--no-first-run",
             "--remote-allow-origins=*", "--hide-scrollbars",
             "--force-device-scale-factor=1", NO_TRACKING_FLAG,
             # A GitHub runner runs as root in a container: Chrome refuses to start
             # without --no-sandbox, and /dev/shm is 64MB there, which crashes the
             # renderer on a heavy page. asset-load-check.py passed these and worked on
             # CI; cdp.Browser did not, so every gate that imports it died with
             # "chrome never came up" the moment they were wired into CI. Harmless
             # locally, so they are unconditional rather than guarded by a platform test
             # that would itself be one more thing to get wrong.
             "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
             *extra_flags, "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # 13.5s of patience, then RETRY on a fresh port. A CI runner has two cores, and
        # several gates each boot their own Chrome: under that contention startup can
        # exceed the wait, and the port is derived from the pid, so two processes whose
        # pids are 200 apart pick the SAME port and the second one finds the first one's
        # tab list. Three gates failed a build with "chrome never came up" this way.
        # Retrying on a different port costs nothing when Chrome is healthy and is the
        # difference between a flaky suite and a trustworthy one.
        ws_url = None
        for attempt in range(3):
            for _ in range(90):
                try:
                    tabs = json.load(urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/json"))
                    ws_url = next(t["webSocketDebuggerUrl"]
                                  for t in tabs if t["type"] == "page")
                    break
                except Exception:
                    time.sleep(.15)
            if ws_url:
                break
            if attempt < 2:
                try:
                    self.proc.kill()
                except Exception:
                    pass
                with socket.socket() as _s1:      # a fresh OS-assigned port, not a guess
                    _s1.bind(('127.0.0.1', 0))
                    self.port = _s1.getsockname()[1]
                self.proc = subprocess.Popen(
                    [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
                     f"--user-data-dir={self.profile}", "--no-first-run",
                     "--remote-allow-origins=*", "--hide-scrollbars",
                     "--force-device-scale-factor=1", NO_TRACKING_FLAG,
                     "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                     *extra_flags, "about:blank"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not ws_url:
            self.close()
            raise RuntimeError(f"chrome never came up after 3 attempts "
                               f"(last port {self.port}) — {CHROME}")
        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self._id = 0
        # cmd() used to throw away every message that was not the reply it was
        # waiting for — which is every console error, every exception and every
        # failed request Chrome reported. They are kept now so a gate can ask
        # what actually went wrong on the page, not just how it looked.
        self.events = []
        self.cmd("Page.enable")
        self.cmd("Runtime.enable")

    def cmd(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            r = json.loads(self.ws.recv())
            if "method" in r:
                self.events.append(r)
                if len(self.events) > 4000:      # a runaway page must not eat RAM
                    del self.events[:2000]
            if r.get("id") == self._id:
                if "error" in r:
                    raise RuntimeError(f"{method}: {r['error']}")
                return r.get("result", {})

    def viewport(self, width, height=900, mobile=None):
        self.cmd("Emulation.setDeviceMetricsOverride", width=width, height=height,
                 deviceScaleFactor=1,
                 mobile=(width < 700) if mobile is None else mobile)

    def navigate(self, url, settle=1.8):
        """Go to a URL. Raises on a navigation failure — never returns silently.

        This is the guard that was present in two tools and absent from three.
        A dead server used to look like a clean page: Chrome's error page has a
        <body>, so a probe found nothing wrong and the gate printed 'ok'.
        """
        res = self.cmd("Page.navigate", url=url)
        if res.get("errorText"):
            raise RuntimeError(f"did not load: {url} — {res['errorText']}")

        # `settle` is now a CEILING, not a bill. It used to be a blind sleep on
        # every page, so a suite of six gates over 50 pages spent almost all of
        # its wall clock waiting on pages that had been ready for a second and
        # a half — 13% CPU across a 20-minute run. Ask the page instead, and
        # leave as soon as the document, its fonts and its images are done.
        deadline = time.time() + settle
        floor = time.time() + 0.12   # let a first paint and any CSS transition land
        probe = ("document.readyState === 'complete' && "
                 "(!document.fonts || document.fonts.status === 'loaded') && "
                 "[...document.images].every(i => !i.currentSrc || i.complete)")
        while time.time() < deadline:
            time.sleep(0.06)
            if time.time() < floor:
                continue
            try:
                if self.eval(probe) is True:
                    break
            except RuntimeError:
                break   # mid-navigation context swap: fall through to the cap
        return res

    def pump(self, seconds=1.0):
        """Read the socket for a while so events actually arrive.

        cmd() only reads while it waits for its own reply, so between commands
        Chrome's events sit unread in the socket and a plain sleep() collects
        nothing. This is what makes console errors and failed requests visible.
        """
        end = time.time() + seconds
        old_to = self.ws.gettimeout()
        try:
            while time.time() < end:
                self.ws.settimeout(max(0.05, end - time.time()))
                try:
                    r = json.loads(self.ws.recv())
                except Exception:
                    break
                if "method" in r:
                    self.events.append(r)
        finally:
            self.ws.settimeout(old_to)

    def drain(self, *methods):
        """Take the buffered CDP events, optionally only the named methods."""
        got = [e for e in self.events if not methods or e.get("method") in methods]
        self.events = []
        return got

    def eval(self, expression, await_promise=False):
        r = self.cmd("Runtime.evaluate", expression=expression,
                     returnByValue=True, awaitPromise=await_promise)
        if "exceptionDetails" in r:
            raise RuntimeError(f"JS error: {json.dumps(r['exceptionDetails'])[:200]}")
        return r.get("result", {}).get("value")

    def eval_json(self, expression, await_promise=False):
        v = self.eval(expression, await_promise)
        return json.loads(v) if isinstance(v, str) else v

    def scroll_through(self, step=500, pause=12):
        """Walk the page so IntersectionObservers fire, then return to the top."""
        self.eval(
            "(async()=>{const h=document.body.scrollHeight;"
            f"for(let y=0;y<h;y+={step}){{scrollTo(0,y);"
            f"await new Promise(r=>setTimeout(r,{pause}));}}"
            "scrollTo(0,0);await new Promise(r=>setTimeout(r,140));})()",
            await_promise=True)

    def close(self):
        try:
            if getattr(self, "proc", None):
                self.proc.send_signal(signal.SIGKILL)
                self.proc.wait(timeout=10)
        finally:
            shutil.rmtree(self.profile, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

def ensure_server(port=8000, root=None):
    """Guarantee something is serving `root` on `port`; return a stop() callable.

    Eighteen gates hard-code http://localhost:8000 and none of them checked that anything
    was there. When nothing was, they did not say "no server" — they reported findings:
    runtime-error-check announced "100 runtime problem(s) on 100 of 100 page(s)", and
    cta-viewport-check's calibration failed to see its own planted override, which the
    pre-push hook then printed as "a call-to-action renders differently on phone and
    desktop". Both were the absence of a server, described as defects in the site.

    Reuses an existing server if one is already listening, so a developer's own dev server
    is never disturbed and never double-bound.
    """
    import urllib.request, threading, os
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
        return lambda: None
    except Exception:
        pass
    root = root or os.getcwd()

    class Quiet(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)
        def log_message(self, *a):
            pass
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.shutdown
