#!/usr/bin/env python3
"""Regenerate OG share-cards from a registry, through the ONE template every card shares.

Why this exists: an audit on 2026-08-10 found 13 real defects across 25 hand-made PNGs that no
text gate could see — 4 blank/broken cards (patterns/act-review-ignore, ai-failure-states,
confidence-scores, ml-explainability), 4 pattern pages with NO card at all (falling back to a
personal photo as their share image), 1 pattern page silently reusing an essay's card, and 4
cards carrying stale or explicitly-banned facts (47 vs the real 53, banned "n=42"/"90 days",
the retired "trust layer" term, "40+" terms vs the real 15). None of this was a text problem;
it was baked into pixels, invisible to grep, and there was no generator — the only prior
precedent (_book-og.template.html) exists because a rename once had to be rebuilt by hand.

Every field below is sourced from each page's OWN <meta property="og:title">/<og:description>,
not invented. Run with --check to verify every card on disk still matches the registry (wire
this into canon-lint or a CI step); run with no args to regenerate everything.
"""
import argparse, html, os, re, subprocess, sys, time
from urllib.parse import urlencode
import sys as _sys, os as _os
# Trackers are refused for every browser this repo drives — see cdp.py.
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from cdp import NO_TRACKING_FLAG

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE = "assets/og-images/_card.template.html"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome-stable", "google-chrome", "chromium-browser", "chromium",
]

def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.isabs(c) and os.path.exists(c):
            return c
        try:
            r = subprocess.run(["which", c], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
    return None

CHROME = os.environ.get("CHROME") or find_chrome()

# --- registry --------------------------------------------------------------------------------
# out_file, kicker, title, subtitle, byline. Every string here traces to a source noted in the
# comment above each block — CANONICAL-FACTS.md 2026-08-10 has the full audit.

REG = [
    # --- essays. The four essay cards were hand-made and outside this generator until
    #     2026-08-30, when the confidence-scoring essay was rewritten to the attested AdTech
    #     story and its card still carried the retired "How I Design Confidence Scores"
    #     headline. A card outside REG does not change when its page does. The other three
    #     essay cards (explainability, failure-states, human-in-loop) are still unmanaged.
    ("confidence-scoring-og.png", "ESSAY", "The Model Was Right. I Fixed the Wrong Thing.",
     "Adoption is not a function of accuracy.", "Arpit Maheshwari \u00b7 Essay"),
    # --- /fit/ (added 2026-08-17 with the page; a page shipped without a card falls back to
    #     a personal photo as its share image, which is the defect this generator was built for)
    ("fit-og.png", "FIT CHECK", "Paste the role. It answers with evidence, or says it can\u2019t.",
     "Matched against work published on this site \u2014 with the page behind every claim.",
     "Arpit Maheshwari \u00b7 Fit Check"),
    # --- the 4 blank/broken pattern cards (source: each page's own og:title/og:description) ---
    ("act-review-ignore-og.png", "AI DESIGN PATTERNS", "The Act / Review / Ignore Rule",
     "An unexplained 87% is a shrug with decimals.", "Arpit Maheshwari · Pattern Library"),
    ("ai-failure-states-og.png", "AI DESIGN PATTERNS", "AI Failure States: Where the Next Ten Interactions Are Won",
     "Five patterns for communicating AI uncertainty without breaking user trust.",
     "Arpit Maheshwari · Pattern Library"),
    ("confidence-scores-og.png", "AI DESIGN PATTERNS", "Confidence Scores That End in a Verb",
     "How to design interfaces that help users trust algorithmic recommendations.",
     "Arpit Maheshwari · Pattern Library"),
    ("ml-explainability-og.png", "AI DESIGN PATTERNS", "ML Explainability: Reasons on the Card, Not in a Tooltip",
     "Patterns for showing a person why the machine decided, at a depth they can use.",
     "Arpit Maheshwari · Pattern Library"),

    # --- the 4 pattern pages with NO card at all (fell back to a personal photo) ---
    ("capability-contract-og.png", "AI DESIGN PATTERNS", "The Capability Contract",
     "Stating an AI system's limits up front — the honest “no” that makes the "
     "confident answer believable.", "Arpit Maheshwari · Pattern Library"),
    ("calibration-track-record-og.png", "AI DESIGN PATTERNS", "Calibration & Track Record",
     "Showing whether “80% sure” has actually been right 80% of the time.",
     "Arpit Maheshwari · Pattern Library"),
    ("provenance-citations-og.png", "AI DESIGN PATTERNS", "Provenance & Citations",
     "Tracing an AI output back to the evidence behind it.", "Arpit Maheshwari · Pattern Library"),
    ("reversibility-safe-to-act-og.png", "AI DESIGN PATTERNS", "Reversibility: Cheap to Undo Is Cheap to Adopt",
     "Make the model's suggestion cheap to walk back.", "Arpit Maheshwari · Pattern Library"),

    # --- the pattern page silently reusing the WRITING ESSAY'S card (own meta exists, unused) ---
    ("human-in-loop-pattern-og.png", "AI DESIGN PATTERNS", "Human-in-the-Loop: The Override Is Training Data",
     "Five patterns for designing systems where humans and AI work together iteratively.",
     "Arpit Maheshwari · Pattern Library"),

    # --- patterns/index.html's own card (was reusing the broken act-review-ignore-og.png) ---
    ("patterns-index-og.png", "PATTERN LIBRARY", "A Field Guide to Trust",
     "The Act / Review / Ignore rule plus 8 AI design patterns that ran in production.",
     "Arpit Maheshwari · Pattern Library"),

    # --- the 4 stale/banned-fact cards. Sources: resources/ai-design-checklist.html's own item
    # count (53, not the card's stale 47); CANONICAL-FACTS.md's 2026-07-25 display rule banning
    # "n=42"/"90-day window" in print (replacement phrase "measured pre- vs post-rollout" is
    # canon's own prescribed substitute, not invented here); the book's real title "Human in the
    # Loop" (canon §1, "trust layer" retired 2026-08-01); the glossary's real entry count (15).
    ("ai-design-checklist-og.png", "CHECKLIST · SHIPPING", "53 Things to Check Before Shipping AI",
     "Happy-path demo ≠ production ready", "Arpit Maheshwari · Resource"),
    ("fintech-og.png", "FINTECH · PRIVATE EQUITY", "Deal-Screening AI That Cites Its Sources",
     "60% faster screening · measured pre- vs post-rollout", "Arpit Maheshwari · Case Study"),
    ("writing-index-og.png", "WRITING · ESSAYS", "Essays on AI Design",
     "Human in the Loop: notes on designing between people and algorithms", "Arpit Maheshwari · Essay"),
    ("intelligent-systems-glossary-og.png", "REFERENCE · GLOSSARY", "Intelligent Systems Glossary",
     "15 core terms for designing AI products", "Arpit Maheshwari · Resource"),
    # --- case cards (2026-08-15): the F3 hook titles; adtech names Talon ---
    ("adtech-og.png", "ADTECH · TALON OUTDOOR · NAMED", "An Ad Agency Became the Market\u2019s Aggregator",
     "Five systems, one platform \u2014 planning 2 wks \u2192 3 hrs once traders could argue back.", "Arpit Maheshwari \u00b7 Case Study"),
    ("ptc-og.png", "EDTECH · PTC · PUBLIC", "The Redesign That Asked PTC to Kill Four Products",
     "Five platforms to one \u00b7 $1M/yr saved \u00b7 subscription 0% \u2192 64% of new bookings.", "Arpit Maheshwari \u00b7 Case Study"),
    ("o2-og.png", "TELECOM · O2 UK · PUBLIC", "Two O2 UK Products, Four Million People",
     "At 4M+ users a correct system still has to earn the tap.", "Arpit Maheshwari \u00b7 Case Study"),
    ("orgos-og.png", "ORG DESIGN · NDA", "The Software That Replaced the Org Chart",
     "200 people, zero managers, eight modules doing an org chart\u2019s job.", "Arpit Maheshwari \u00b7 Case Study"),
    ("vc-diligence-og.png", "VC/PE · NDA", "Due Diligence You Can\u2019t Rubber-Stamp",
     "The right friction: sign-off locked until the evidence is opened \u00b7 3 wks \u2192 4 days.", "Arpit Maheshwari \u00b7 Case Study"),
    ("planit-og.png", "CONSUMER · PLANIT · 2021", "The App People Broke on Purpose",
     "A transit app that optimised for breathing room \u2014 and an error state users went looking for.",
     "Arpit Maheshwari \u00b7 Case Study"),
    ("plugin-og.png", "THE LAB · 04 · MIT", "The Design System, as a Claude Plugin",
     "Tokens, type scale, spacing grid and ten ship gates \u2014 installable.", "Arpit Maheshwari \u00b7 The Lab"),
]


def render(out_name, kicker, title, subtitle, byline, docroot):
    q = urlencode({"kicker": kicker, "title": title, "subtitle": subtitle, "byline": byline})
    url = f"http://localhost:8000/{TEMPLATE}?{q}"
    out_path = os.path.join(docroot, "assets", "og-images", out_name)
    args = [CHROME, "--headless=new", NO_TRACKING_FLAG, "--disable-gpu", "--hide-scrollbars",
            "--window-size=1200,630", "--virtual-time-budget=4000",
            f"--screenshot={out_path}", url]
    r = subprocess.run(args, capture_output=True, text=True, timeout=60)
    ok = r.returncode == 0 and os.path.exists(out_path)
    return ok, out_path


def serve(docroot):
    """Reuse a server already listening on 8000 (common in dev); only start one if needed."""
    import http.server, socketserver, threading, urllib.request
    try:
        urllib.request.urlopen("http://localhost:8000/", timeout=0.5)
        return None  # already serving — assume it's this docroot, as every tool in this repo does
    except Exception:
        pass
    os.chdir(docroot)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", 8000), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    for _ in range(40):
        try:
            urllib.request.urlopen("http://localhost:8000/", timeout=0.5)
            break
        except Exception:
            time.sleep(0.25)
    return httpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docroot", default=ROOT)
    ap.add_argument("--check", action="store_true",
                     help="verify every registry card exists on disk and is non-trivial in size; "
                          "does not pixel-diff (rendering is nondeterministic across font-load "
                          "timing) — it exists to catch a card going MISSING again, not to lint "
                          "pixel content.")
    a = ap.parse_args()

    if not CHROME:
        sys.exit("generate-og-cards: no Chrome found. Set $CHROME.")

    if a.check:
        missing = []
        for out_name, *_ in REG:
            p = os.path.join(a.docroot, "assets", "og-images", out_name)
            if not os.path.exists(p) or os.path.getsize(p) < 5000:
                missing.append(out_name)
        if missing:
            print(f"MISSING or suspiciously small: {missing}")
            sys.exit(1)
        print(f"  all {len(REG)} registry cards present on disk.")
        sys.exit(0)

    httpd = serve(a.docroot)
    try:
        ok_count = 0
        for out_name, kicker, title, subtitle, byline in REG:
            ok, path = render(out_name, kicker, title, subtitle, byline, a.docroot)
            print(f"  {'✓' if ok else '✗ FAILED'}  {out_name}")
            if ok:
                ok_count += 1
        print(f"\n{ok_count}/{len(REG)} cards rendered.")
        sys.exit(0 if ok_count == len(REG) else 1)
    finally:
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
