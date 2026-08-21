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
import json, os, shutil, signal, subprocess, tempfile, time, urllib.request
import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class Browser:
    """A headless Chrome speaking CDP. Use as a context manager."""

    def __init__(self, port_base=9300, timeout=90, extra_flags=()):
        self.port = port_base + (os.getpid() % 200)
        self.profile = tempfile.mkdtemp(prefix="cdp-")
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
             f"--user-data-dir={self.profile}", "--no-first-run",
             "--remote-allow-origins=*", "--hide-scrollbars",
             "--force-device-scale-factor=1", *extra_flags, "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws_url = None
        for _ in range(90):
            try:
                tabs = json.load(urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/json"))
                ws_url = next(t["webSocketDebuggerUrl"]
                              for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(.15)
        if not ws_url:
            self.close()
            raise RuntimeError("chrome never came up")
        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self._id = 0
        self.cmd("Page.enable")
        self.cmd("Runtime.enable")

    def cmd(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            r = json.loads(self.ws.recv())
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
        time.sleep(settle)
        return res

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
