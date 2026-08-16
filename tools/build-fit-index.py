#!/usr/bin/env python3
"""Build data/fit-index.json — the corpus the /fit/ matcher reads.

WHY IT IS GENERATED RATHER THAN HAND-WRITTEN
The matcher runs in the recruiter's browser, so whatever it can read is public. Canon
(CANONICAL-FACTS.md) is deliberately untracked because it holds NDA client identities and
private rulings, and it must stay that way. So the index is built only from things that
are already published: data/case-facts.js and the pages under case-studies/, patterns/
and lab/. If a claim cannot be traced to a published page, it does not get into the index.

THE GATE THAT MAKES THAT REAL (not just a promise in a docstring)
  1. every citation URL must resolve to a file in this repo;
  2. every NUMBER in a claim must appear verbatim in one of that claim's cited pages, or
     in the case-facts metric ledger. This is the invented-metric rule, mechanised: a
     figure nobody published cannot survive the build.
  3. every evidence id referenced by the requirement lexicon must exist.
Run it; if it exits non-zero, the index is not written.

The lexicon below (JD phrase -> evidence id) is a judgement about what words mean, and it
is mine. The CLAIMS are not judgement — they are traceable, and rule 2 enforces it.
"""
import re, json, sys, pathlib, html as _html

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "fit-index.json"

# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE. claim = a sentence a human wrote; cites = where a reader verifies it.
# strength: "documented" = a case study or a runnable artifact stands behind it.
#           "thin"       = the site says it, but no case study carries the weight.
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE = [
    dict(id="ai-product", label="AI product design",
         claim="Three of the seven published cases are AI systems — deal screening that cites "
               "its sources, a technical due-diligence platform, and an ad-planning aggregator "
               "— built with model engineers and data scientists, not around them.",
         cites=["/case-studies/fintech.html", "/case-studies/vc-diligence.html",
                "/case-studies/adtech.html", "/patterns/"], strength="documented"),
    dict(id="trust-ux", label="Trust, confidence and explainability UX",
         claim="Nine AI trust patterns written up from production work — confidence scores that "
               "end in a verb, failure states, provenance, calibration, reversibility.",
         cites=["/patterns/", "/patterns/confidence-scores.html",
                "/patterns/ml-explainability.html", "/patterns/provenance-citations.html"],
         strength="documented"),
    dict(id="hitl", label="Human-in-the-loop and review workflows",
         claim="Approve/reject, editable recommendations and expert override, designed in "
               "production and then written as a zero-dependency module with tests.",
         cites=["/patterns/human-in-loop.html", "/lab/loop.html"], strength="documented"),
    dict(id="design-systems", label="Design systems",
         claim="One design system introduced across six Talon products, then encoded as "
               "installable plugins so it applies without anyone remembering it; the public "
               "version is MIT-licensed and audits its own rendered pixels.",
         cites=["/lab/#design-system", "/lab/plugin.html", "/case-studies/adtech.html"],
         strength="documented"),
    dict(id="data-density", label="Data-dense and analytical interfaces",
         claim="An end-to-end aggregator across 6 systems that cut campaign planning from "
               "2 wks to 3 hrs, and a diligence platform analysing 16 dimensions per finding.",
         cites=["/case-studies/adtech.html", "/case-studies/vc-diligence.html"],
         strength="documented"),
    dict(id="zero-to-one", label="0 → 1 and new product definition",
         claim="A consumer travel product taken 0→1 in 6 months, and a technical-DD platform "
               "defined from scratch for two fund types.",
         cites=["/case-studies/planit.html", "/case-studies/vc-diligence.html"],
         strength="documented"),
    dict(id="enterprise-b2b", label="Enterprise and B2B SaaS",
         claim="Private-equity deal screening, technical due diligence for VC and PE, an "
               "internal operating system running 8 modules, and a six-product adtech platform.",
         cites=["/case-studies/fintech.html", "/case-studies/orgos.html",
                "/case-studies/adtech.html"], strength="documented"),
    dict(id="consumer-scale", label="Consumer products at scale",
         claim="Two O2 UK products serving 4M+ users, with 2.6M Priority sign-ups in year one.",
         cites=["/case-studies/o2.html"], strength="documented"),
    dict(id="ships-code", label="Designing and shipping the front-end",
         claim="The interface is shipped as front-end code, not handed over: this site has no "
               "build step, and the lab holds runnable modules with tests.",
         cites=["/lab/teardown.html", "/lab/loop.html", "/lab/eval.html"],
         strength="documented"),
    dict(id="leadership", label="Leading and building design teams",
         claim="Built and led the CX team at PTC across 2014–2019, and led design across "
               "4 engineering streams on an internal operating system.",
         cites=["/case-studies/ptc.html", "/case-studies/orgos.html"], strength="documented"),
    dict(id="strategy", label="Product strategy and killing scope",
         claim="Argued PTC into consolidating 5 platforms into 1, saving $1M / yr on print and "
               "shipping and moving subscription share of new bookings from 0% to 64%.",
         cites=["/case-studies/ptc.html"], strength="documented"),
    dict(id="accessibility", label="Accessibility and legibility",
         claim="Contrast, overflow and legibility are measured from rendered pixels on every "
               "push, and the published system states the ground each ratio was measured on.",
         cites=["/lab/teardown.html", "/lab/plugin.html"], strength="documented"),
    dict(id="edtech", label="EdTech and learning platforms",
         claim="A web LMS in 11 languages with 550k+ registered and 350k+ active learners.",
         cites=["/case-studies/ptc.html"], strength="documented"),
    dict(id="fintech-dom", label="FinTech, VC and private equity",
         claim="Deal screening for private-equity investing, and a diligence platform that cut "
               "the cycle from 3 wks to 4 days.",
         cites=["/case-studies/fintech.html", "/case-studies/vc-diligence.html"],
         strength="documented"),
    dict(id="adtech-dom", label="AdTech, media and marketing platforms",
         claim="An agency turned into the market's aggregator, worth £69k media-value gain "
               "per client.",
         cites=["/case-studies/adtech.html"], strength="documented"),
    dict(id="telecom", label="Telecom",
         claim="Two O2 UK products, built inside an Equal Experts squad.",
         cites=["/case-studies/o2.html"], strength="documented"),
    dict(id="brand", label="Brand, logo and mascot design",
         claim="The PlanIt identity — logo, mascots and tone — designed alongside the product.",
         cites=["/case-studies/planit.html"], strength="documented"),
    dict(id="mobile-web", label="Mobile web",
         claim="PlanIt shipped on mobile web and desktop.",
         cites=["/case-studies/planit.html"], strength="documented"),
    dict(id="research", label="Usability and user research",
         claim="PlanIt launched with 0 usability complaints in the launch window; the site "
               "publishes how that was tested rather than asserting it.",
         cites=["/case-studies/planit.html"], strength="thin"),
    dict(id="agile", label="Working in distributed agile teams",
         claim="A 50+ person distributed agile team on the adtech platform; 4 engineering "
               "streams plus a PM on the operating system.",
         cites=["/case-studies/adtech.html", "/case-studies/orgos.html"], strength="documented"),
]

# ─────────────────────────────────────────────────────────────────────────────
# THE LEXICON. Left: the words job descriptions actually use. Right: evidence id,
# or None when the honest answer is "nothing is published about this."
# A term with None is not a claim that he cannot do it — it is the tool refusing
# to answer beyond what is on the site. That distinction is stated in the UI.
# ─────────────────────────────────────────────────────────────────────────────
LEXICON = {
    # DISCIPLINE: single generic words are banned. A control JD for a pastry chef matched
    # "leadership" on the word "manage" and "edtech" on "train two apprentices" — the tool
    # was taking credit for business English. Every term here has to mean the thing in a
    # job description and nowhere else, which is why most of them are phrases:
    #   "model"    -> operating model, business model, role model
    #   "engineer" -> "work with engineers" (which is not the same as writing code)
    #   "lead"     -> "lead generation", "lead the effort"
    #   "training" -> training data
    #   "identity" -> identity management
    #   "education"-> the Education section of the JD itself
    "ai-product": ["ai", "a.i.", "artificial intelligence", "machine learning", "ml", "llm",
                   "llms", "genai", "gen ai", "generative ai", "ai-native", "ai native",
                   "ai-first", "ai product", "ai products", "ai features", "ai agents",
                   "autonomous agents", "agentic", "copilot", "rag", "prompt engineering",
                   "model output", "model outputs", "foundation model", "ml models"],
    "trust-ux": ["explainability", "explainable", "interpretability", "user trust",
                 "trust in ai", "model confidence", "confidence score", "confidence scores",
                 "model transparency", "hallucination", "hallucinations", "uncertainty",
                 "provenance", "citations", "calibration", "failure state", "failure states",
                 "error state", "error states", "black box"],
    "hitl": ["human-in-the-loop", "human in the loop", "hitl", "human oversight",
             "human review", "review workflow", "review workflows", "approve/reject",
             "expert override", "override", "feedback loop", "annotation", "labelling",
             "labeling"],
    "design-systems": ["design system", "design systems", "component library",
                       "design tokens", "style guide", "styleguide", "figma library",
                       "storybook", "pattern library"],
    "data-density": ["dashboard", "dashboards", "data-dense", "data dense",
                     "data visualisation", "data visualization", "information density",
                     "complex data", "data tables", "reporting tools", "analytics product"],
    "zero-to-one": ["0 to 1", "0-1", "0\u21921", "zero to one", "greenfield", "new product",
                    "from scratch", "mvp", "early stage", "founding designer"],
    "enterprise-b2b": ["b2b", "b2b saas", "enterprise", "enterprise saas", "saas",
                       "internal tools", "internal platform"],
    "consumer-scale": ["b2c", "consumer", "millions of users", "mass market"],
    "ships-code": ["front-end", "frontend", "react", "html", "css", "javascript",
                   "typescript", "prototyping", "prototype in code", "writes code",
                   "ships code", "production code", "code-literate", "design engineer"],
    "leadership": ["leadership", "design leadership", "team lead", "head of design",
                   "mentor", "mentoring", "hiring designers", "people management", "line management",
                   "director of design", "lead a team", "build a team", "manage designers",
                   "grow the team"],
    "strategy": ["product strategy", "strategic", "roadmap", "prioritisation",
                 "prioritization", "trade-off", "tradeoff", "business impact", "north star"],
    "accessibility": ["accessibility", "a11y", "wcag", "inclusive design", "screen reader",
                      "colour contrast", "color contrast"],
    "edtech": ["edtech", "ed-tech", "lms", "learning management", "e-learning",
               "learning platform", "online learning"],
    "fintech-dom": ["fintech", "financial services", "banking", "investment",
                    "private equity", "venture capital", "vc", "due diligence", "trading",
                    "payments"],
    "adtech-dom": ["adtech", "ad-tech", "advertising", "campaign", "campaigns", "dsp",
                   "programmatic", "marketing platform", "martech", "publisher",
                   "media owner", "media planning"],
    "telecom": ["telecom", "telco", "carrier", "network operator"],
    "brand": ["brand", "branding", "visual identity", "brand identity", "logo",
              "illustration", "mascot"],
    "mobile-web": ["mobile web", "mobile-first", "mobile first", "responsive design",
                   "responsive web"],
    "research": ["user research", "usability", "usability testing", "user testing",
                 "ux research", "user interviews", "generative research"],
    "agile": ["agile", "scrum", "sprint", "sprints", "cross-functional", "distributed team",
              "remote team", "remote-first"],
    # \u2500\u2500 asks that decide it before skills are even weighed \u2500\u2500
    # Kept separate from "nothing published": these are not gaps in the portfolio, they are
    # facts about the arrangement. A tool that buried them under a long list of green ticks
    # would be wasting the reader's time, which is the one thing it is meant to save.
    "!blocker": ["on-site", "onsite", "on site", "in-office", "in office", "hybrid",
                 "relocate", "relocation", "must be based", "based in the us",
                 "work authorisation", "work authorization", "authorized to work",
                 "authorised to work", "green card", "us citizen", "security clearance",
                 "h1b", "h-1b", "visa sponsorship", "no visa", "eligible to work"],
    # \u2500\u2500 recognised asks with nothing published behind them \u2500\u2500
    None: ["ios", "android", "swift", "kotlin", "react native", "flutter", "native app",
           "native apps", "mobile app development", "3d", "ar", "vr", "xr", "unity",
           "game design", "motion design", "animation", "after effects", "video editing",
           "print design", "packaging", "industrial design", "hardware",
           "design ops", "designops", "service blueprint", "conversion rate optimisation",
           "seo", "growth marketing", "paid acquisition", "sales enablement",
           "healthcare", "pharma", "clinical", "biotech", "medical device",
           "e-commerce", "ecommerce", "marketplace", "logistics", "supply chain",
           "gaming", "crypto", "blockchain", "web3", "nft",
           "conference speaking", "community building"],
}

# Hard facts about working with him, shown before the JD is typed rather than buried
# in the result. All three are already stated on the site.
CONSTRAINTS = [
    ["Location", "India, GMT+5:30 — remote, with daily overlap with both US coasts."],
    ["Work authorisation", "No US work authorisation. Roles requiring on-site US presence or "
                           "US employment eligibility are not a fit, whatever the skills match."],
    ["Confidentiality", "Four of the seven cases are under NDA. Outcomes and decisions are "
                        "published; client screens and identities are not."],
]

CONTRACT = dict(
    can=["Match a job description against work that is published on this site.",
         "Show you the page behind every claim, so you can check it yourself.",
         "Tell you plainly where nothing is published — including where that is a real gap."],
    cannot=["Tell you whether he would be good at your job. It has never seen your team.",
            "Read anything that is not on this site — no CV parsing, no scoring, no ranking.",
            "Generate text. It matches your words against a fixed index and shows what it hit."],
)


def page_text(url):
    """The visible text of a published page, for the numbers gate."""
    p = url.split("#")[0].lstrip("/")
    path = ROOT / (p + "index.html" if p.endswith("/") else p)
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return _html.unescape(re.sub(r"<[^>]+>", " ", raw))


def main():
    facts = json.loads(re.search(r"var CASE_FACTS = (\{.*?\});\n",
                                 (ROOT / "data" / "case-facts.js").read_text(encoding="utf-8"),
                                 re.S).group(1))
    ledger = " ".join(f"{a} {b}" for c in facts["cases"].values() for a, b in c["metrics"])
    errs = []

    for e in EVIDENCE:
        corpus = ledger
        for u in e["cites"]:
            t = page_text(u)
            if t is None:
                errs.append(f"{e['id']}: cites {u} — no such page in the repo")
            else:
                corpus += " " + t
        # every number in a claim must be printed somewhere published
        for num in re.findall(r"\d[\d,]*(?:\.\d+)?%?", e["claim"]):
            num = num.rstrip(",.")          # "2014\u20132019," hands back "2019," — punctuation, not digits
            if num and num not in corpus:
                errs.append(f"{e['id']}: claim says {num!r}, which appears on none of its "
                            f"cited pages nor in the metric ledger")

    # Spelled-out counts slip past the digits rule above: "Four of the seven published cases"
    # survived it while being wrong about both halves. Any claim that counts the case studies
    # must agree with the ledger, which is the one place the case list is defined.
    WORDS = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
             "nine":9,"ten":10,"eleven":11,"twelve":12}
    ncases = len(facts["order"])
    for e in EVIDENCE:
        m = re.search(r"of the (\w+) (?:published )?cases", e["claim"], re.I)
        if m:
            said = WORDS.get(m.group(1).lower())
            if said != ncases:
                errs.append(f"{e['id']}: claim says \"of the {m.group(1)} cases\" but "
                            f"case-facts defines {ncases}")

    ids = {e["id"] for e in EVIDENCE}
    for k in LEXICON:
        if k is not None and not k.startswith("!") and k not in ids:
            errs.append(f"lexicon references unknown evidence id {k!r}")
    for e in EVIDENCE:
        if e["id"] not in LEXICON:
            errs.append(f"evidence {e['id']!r} has no terms — nothing can ever match it")

    if errs:
        print("fit-index NOT written — %d problem(s):" % len(errs))
        for x in errs:
            print("  ✗", x)
        return 1

    terms = []
    for eid, words in LEXICON.items():
        for w in words:
            terms.append([w, eid])
    terms.sort(key=lambda t: -len(t[0]))          # longest phrase wins the match

    OUT.write_text(json.dumps(dict(
        generated=str(pathlib.Path(__file__).name),
        note="Generated from this site's published pages. Nothing here is unpublished.",
        constraints=CONSTRAINTS, contract=CONTRACT,
        evidence={e["id"]: e for e in EVIDENCE}, terms=terms,
    ), indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"data/fit-index.json  {len(EVIDENCE)} claims  {len(terms)} terms  "
          f"({sum(1 for t in terms if t[1] is None)} unpublished, "
          f"{sum(1 for t in terms if t[1] == '!blocker')} blocking)")
    print("  every citation resolves; every number traced to a published page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
