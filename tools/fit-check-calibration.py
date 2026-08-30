#!/usr/bin/env python3
"""Drive the real /fit/ page in a real browser and assert what it says.

WHY THIS EXISTS
The fit check is the one page on this site that makes a claim ABOUT ARPIT in response to
a stranger's input. If it over-matches it becomes a bragging machine; if it under-matches
it is useless. Neither failure is visible by looking at the page with a JD you chose to
flatter it. So the cases below include CONTROLS that must come back empty — the first
version matched "leadership" on a pastry chef's "manage the ovens" and "edtech" on
"train two apprentices", and nothing on the page revealed that.

This runs the shipped fit.js in Chrome against the shipped index. It does not re-implement
the matching in Python — a second implementation would only prove the two agree.

USAGE  fit-check-calibration.py [base-url]      (default http://localhost:8000)
"""
import json, os, re, shutil, signal, subprocess, sys, tempfile, time, urllib.request
import websocket

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

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# (name, jd, assertion) — assertion gets the parsed result dict
CASES = [
    ("control: pastry chef — must match NOTHING",
     "We are hiring a pastry chef for our seaside bakery. You will bake bread each morning, "
     "manage the ovens, train two apprentices in laminated dough, lead the early shift and "
     "take ownership of quality and consistency.",
     lambda r: r["documented"] == 0 and r["thin"] == 0 and r["unpublished"] == 0),

    ("control: generic business English — must match NOTHING",
     "You will manage stakeholders, lead cross-team initiatives, drive outcomes, own the "
     "operating model, work with engineers, and build trust across the organisation. "
     "Education: bachelor's degree. Training will be provided.",
     lambda r: r["documented"] == 0 and r["thin"] == 0),

    ("bad fit: on-site US, native mobile, healthcare — must go RED",
     "Senior Mobile Designer, Healthcare. On-site in Boston, hybrid three days a week. Must "
     "be authorized to work in the US; no visa sponsorship. Design native iOS and Android "
     "apps for clinical workflows at a medical device company. Heavy motion design and 3D.",
     lambda r: r["documented"] == 0 and r["blocking"] >= 3 and r["unpublished"] >= 5),

    ("good fit: AI product design — must find real evidence, WITH citations",
     "Senior Product Designer, AI. Design AI-native experiences for a B2B SaaS platform. "
     "Partner with ML engineers on explainability, confidence scores and human-in-the-loop "
     "review. Own data-dense dashboards. Evolve our design system and design tokens. "
     "Prototyping in React and TypeScript. Strong accessibility practice (WCAG).",
     lambda r: r["documented"] >= 6 and r["blocking"] == 0 and r["allCited"]),

    ("mixed: right skills, wrong arrangement — blockers must lead",
     "AI Product Designer. Work with ML engineers on explainability and model confidence. "
     "Must relocate to New York. Security clearance required.",
     lambda r: r["documented"] >= 1 and r["blocking"] >= 2 and r["firstGroup"] == "block"),
]

READ = r"""
(async () => {
  const jd = %s;
  document.getElementById('fit-jd').value = jd;
  document.getElementById('fit-form').dispatchEvent(new Event('submit', {cancelable:true}));
  await new Promise(r => setTimeout(r, 220));
  const g = k => document.querySelector('.fit-group--' + k);
  const n = k => g(k) ? parseInt(g(k).querySelector('.fit-group-n').textContent, 10) : 0;
  const first = document.querySelector('.fit-group');
  const docItems = [...document.querySelectorAll('.fit-group--doc .fit-item')];
  return JSON.stringify({
    documented: n('doc'), thin: n('thin'), unpublished: n('none'), blocking: n('block'),
    firstGroup: first ? (first.className.match(/fit-group--(\w+)/)||[])[1] : null,
    allCited: docItems.length > 0 && docItems.every(li => li.querySelectorAll('.fit-cites a').length > 0),
    labels: docItems.map(li => li.querySelector('.fit-item-h').textContent),
    emptyShown: !!document.querySelector('.fit-empty'),
  });
})()
"""


def main():
    port = 9600 + (os.getpid() % 180)
    prof = tempfile.mkdtemp(prefix="fitcal-")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", NO_TRACKING_FLAG, f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
         "--no-first-run", "--remote-allow-origins=*", "--hide-scrollbars", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(80):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(.15)
        if not ws_url:
            print("chrome never came up"); return 2
        ws = websocket.create_connection(ws_url, timeout=60); n = [0]

        def cmd(method, **params):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == n[0]:
                    if "error" in m:
                        raise RuntimeError(f"{method}: {m['error']}")
                    return m.get("result", {})

        cmd("Page.enable"); cmd("Runtime.enable")
        cmd("Page.navigate", url=f"{BASE}/fit/")
        time.sleep(2.0)
        loaded = cmd("Runtime.evaluate", expression="!!document.querySelector('#fit-can li')",
                     returnByValue=True)["result"]["value"]
        if not loaded:
            print("✗ the index never loaded — the page cannot be calibrated"); return 2

        bad = 0
        for name, jd, ok in CASES:
            raw = cmd("Runtime.evaluate", expression=READ % json.dumps(jd),
                      returnByValue=True, awaitPromise=True)["result"]["value"]
            r = json.loads(raw)
            passed = ok(r)
            bad += 0 if passed else 1
            print(("  ✓ " if passed else "  ✗ ") + name)
            print(f"      {r['documented']} documented · {r['thin']} thin · "
                  f"{r['unpublished']} unpublished · {r['blocking']} blocking"
                  + ("" if passed else f"   <-- FAILED   {r['labels']}"))
        print()
        if bad:
            print(f"{bad} calibration case(s) failed — the matcher is not saying what it should.")
        else:
            print(f"all {len(CASES)} calibration cases pass "
                  "(2 of them REQUIRE the matcher to find nothing).")
        return 1 if bad else 0
    finally:
        proc.send_signal(signal.SIGKILL); proc.wait(timeout=10)
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
