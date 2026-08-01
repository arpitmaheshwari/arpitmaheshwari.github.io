/* book-content.jsx — content model + spread renderers for Human in the Loop.
   Exposes window.buildBook(ctx) -> { spine:[7 spreads], sections:{cases,patterns} },
   and window.BOOK_META. ctx = { headline, go, enter }.

   Two-level information architecture:
     SPINE (level 0, linear flip) — Cover · Contents · Selected Work ·
       How I Lead · Field Guide · Notes & Writing · Colophon
     SECTIONS (level 1, opened from a hub, returned via Back):
       cases    — PTC University (2), OrgOS (2)   [under Selected Work]
       patterns — 4 trust patterns                [under Field Guide]
*/

const WORK = [{
  tag: "EdTech · Non-NDA",
  title: "PTC University — Learning Connector",
  metric: "$1M/yr",
  desc: "Five learning platforms, one survivor, eleven languages. Drawing the screens was easy; the case for retiring four products was the work that mattered."
}, {
  tag: "Telecom · Non-NDA",
  title: "Telefónica MyO2 & Priority Moments",
  metric: "4M+",
  desc: "Two O2 UK products at national scale. Every screen drawn by me, then coded by me — mobile web."
}, {
  tag: "FinTech · NDA",
  title: "AI-Assisted Private Equity Investing",
  metric: "60% faster",
  desc: "Analysts are paid to doubt confident numbers, so I held the launch until the score could explain itself."
}, {
  tag: "AdTech · NDA",
  title: "Programmatic Advertising Platform",
  metric: "2 wks → 3 hrs",
  desc: "Traders watched the algorithm win and still played hunches. The fix was the interface, not the model."
}, {
  tag: "Org Design · NDA",
  title: "OrgOS · Transparent Org Tooling",
  metric: "200",
  desc: "Eight modules doing the coordination work a management layer usually does — built for 200 people, zero managers; 250 run on it today."
}, {
  tag: "VC/PE · NDA",
  title: "Technical Due Diligence Platform",
  metric: "3 wks → 4 days",
  desc: "Partners stake millions on claims they can't verify. Extracting the signals was the model's job; trusting it was theirs."
}];
const PRINCIPLES = [{
  h: "What gets measured is a design decision.",
  p: "By Friday of week one I've read your evals and sat in your customer calls. I shape what gets measured, then I ship the front-end under my own name in the PR."
}, {
  h: "I design the wrong-answer screen first.",
  p: "No AI feature ships until I've watched someone fail to use it. If I can't draw how the system fails, the happy path doesn't matter — trust is built in the error states."
}, {
  h: "The org chart is the hardest wireframe.",
  p: "Most UX problems are misaligned teams wearing UX clothes, so I design the organization before the interface. Then I write the system down — the next designer should inherit more than my taste."
}, {
  h: "Override is a feature, not a failure.",
  p: "A user correcting the model is the training data the next version needs. I design the override as a first-class move — logged, visible, fed back, so people see their fingerprints on next week's calls."
}, {
  h: "I read the data before I open Figma.",
  p: "SQL, raw support tickets, model evals — I want the signal before the summary. Decisions grounded in the data survive the review; the ones I made on instinct don't."
}];
const PATTERNS = [{
  k: "gauge",
  h: "Confidence Score Patterns",
  p: "Five ways to put a number on certainty, and when each one earns or burns the trust to drive a decision."
}, {
  k: "alert",
  h: "Failure States",
  p: "What the screen says when the model can't deliver — and how saying it honestly keeps users from leaving."
}, {
  k: "branch",
  h: "Explainability",
  p: "Showing a non-technical person why the machine decided, at a depth they can use without a stats degree."
}, {
  k: "loop",
  h: "Human-in-the-Loop",
  p: "Keeping the person in command when the stakes outgrow the model's confidence."
}, {
  k: "trace",
  h: "Provenance & Citations",
  p: "The exact source behind every claim — one click from the number to the document that produced it."
}, {
  k: "bounds",
  h: "The Capability Contract",
  p: "Saying what the system can't do, up front — so the rest of it earns belief."
}, {
  k: "calib",
  h: "Calibration & Track Record",
  p: "Showing whether the confidence has actually been right before, so trust is earned, not assumed."
}, {
  k: "undo",
  h: "Reversibility",
  p: "Making the model's suggestion cheap to walk back, so people dare to act on it."
}];
const WRITING = [{
  d: "2026 · Essay",
  h: "The Agentic MVP: Why Your Next Launch Will Be Lovable",
  p: "How the rise of agentic systems is rewriting what 'minimum viable' means — and why lovability is now the bar."
}, {
  d: "2026 · Field note",
  h: "The AI Fight Club",
  p: "Weaponizing Claude and Gemini for Bulletproof Products. A practical method for stress-testing AI interfaces."
}, {
  d: "2025 · Talk",
  h: "Designing for the eval, not the mock",
  p: "What changes when designers own what gets measured."
}, {
  d: "2024 · Essay",
  h: "Transparency as coordination",
  p: "What a zero-manager org taught me about interface design."
}, {
  d: "2024 · Field note",
  h: "Reading the support tickets myself",
  p: "The cheapest research method nobody on the design team wants to do."
}];
const STATUS = ["Available · 4 weeks' notice", "Product & design lead · AI", "Remote · GMT+5:30"];

/* ---- CURRICULUM VITAE (the printable appendix) ---- */
const CV_SKILLS = ["Model-Layer Design", "Product Definition & Roadmaps", "Data-Intensive UI", "Design Leadership", "Organizational Design", "Research & Evals", "System Architecture"];
const CV_EXP = [{
  yr: "2019—",
  role: "Product & Design Lead — AI Products",
  org: "Sahaj AI · AdTech, HRTech & Private Equity"
}, {
  yr: "2014–19",
  role: "Lead Product Designer",
  org: "PTC Inc. · PTC University — Learning Connector · 550k+ registered, 350k+ active · NASA, Apple, Boeing, Airbus & more"
}, {
  yr: "2012–14",
  role: "Front End Specialist",
  org: "Equal Experts · O2 UK consumer apps · 4M+ users"
}, {
  yr: "2010–12",
  role: "Systems Analyst",
  org: "Tata Consultancy Services · mobile for Fortune 500"
}, {
  yr: "2009",
  role: "Intern",
  org: "Nokia Networks · Indore"
}];
const CV_EDU = [{
  yr: "2017–18",
  role: "Executive MBA, Business Analytics",
  org: "Institute of Management Technology · Ghaziabad"
}, {
  yr: "2006–10",
  role: "B.E., Electronics & Communication",
  org: "Shri Vaishnav Institute of Technology & Science · Indore"
}];

/* ---- CASE STUDY (PTC — non-NDA, shown in full) ------ */
/* ---- locked facts come from data/case-facts.js (loaded before this file) --------------
   Title, tag, role/meta, metrics and the provenance caption are NOT written here any more:
   they are read from the single source so the book and the classic case pages cannot drift
   apart again. Narrative prose below stays local to the book on purpose — that is its voice,
   and prose was never what went stale. See data/case-facts.js for the full reasoning. */
var CF = (typeof window !== 'undefined' && window.CASE_FACTS) || null;
if (!CF) {
  throw new Error('portfolio.js: data/case-facts.js must load before portfolio.js — ' +
                  'refusing to render case studies with missing facts.');
}
var cfMeta = function (k) { return CF.get(k).meta.map(function (p) { return [p[0], p[1]]; }); };

const CASES = {
  ptc: {
    key: "ptc",
    no: "01",
    tag: CF.get("ptc").tag,
    title: CF.get("ptc").title,
    standfirst: "Five platforms, one survivor. The redesign took a quarter — the case for killing four products took a year. That was the design work.",
    meta: cfMeta("ptc"),
    context: "The brief said “redesign the UX.” Three weeks in the customer-success recordings said the navigation was fine — so I made the call that the contract was the broken interface: kill four of five learning platforms (LearningExchange, Precision LMS, Digital Guides, IoTU) and move the survivor off perpetual licenses — onto a product-led funnel where free tutorials and trainings converted learners to premium subscriptions.",
    fig1: {
      no: "1.1",
      label: "before — five disconnected platforms, five sign-in screens"
    },
    tension: "The cost was political, not visual: telling four executives their product was now a tab, against a CRO with 60% of revenue on perpetual. Get it wrong and you ship a prettier version of a product no one returns to.",
    note1: "the org chart was the real wireframe",
    decisionLede: "Three decisions did the load-bearing work:",
    moves: [{
      h: "One data model before one UI",
      p: "Rebuilt the content model first — one skill graph every platform mapped onto — so merging was a data migration, not a turf war."
    }, {
      h: "Localisation as an architecture call",
      p: "Built knowing German and Russian run 30% longer: short labels, shallow hierarchy, no text in images."
    }, {
      h: "A switch-off ladder",
      p: "Sequenced the four shutdowns so each VP watched users land softly before the portal went dark."
    }],
    fig2: {
      no: "1.2",
      label: "after — one skill graph, one shell, eleven languages"
    },
    outcome: CF.metrics("ptc"),
    quote: {
      t: "The redesign took a quarter. The case for deleting four products took a year — and that was the actual design work.",
      cite: "— PTC University, project note"
    },
    note2: "killed four products to ship the one that worked.",
    boundary: "I had a year and a direct line to the executives who owned the P&L. The same argument made in a single quarter, without that access, loses."
  }
};

/* ---- NDA WALK-THROUGHS (the three under-NDA projects, redacted) ---- */
const NDA_CASES = [{
  no: "02",
  img: "../assets/shots/o2-app-screens.png",
  tag: CF.get("o2").tag,
  redacted: false,
  ph: "MyO2 account dashboard + Priority Moments rewards — O2 UK mobile web",
  title: CF.get("o2").title,
  standfirst: "Drawn by me, then coded by me — every screen of two O2 UK products on mobile web, at a scale where rounding errors have populations.",
  meta: cfMeta("o2"),
  context: "The one move: own both sides of the handoff — draw every screen, then code the front-end that ships it, so nothing is lost in translation. The cost of that scale: a rounding error has a population. The proof isn't sign-ups; it's the 2.5M who came back.",
  moves: [{
    h: "MyO2 — the whole account, alone",
    p: "O2 UK's self-service app: data and usage, the bill, a tariff change, an upgrade — the whole account without dialing anyone. The math is blunt: every self-service task that lands is a contact-centre call that never happens. It went on to serve more than four million users."
  }, {
    h: "Priority Moments — a reason to open it",
    p: "O2's loyalty programme: rewards from Odeon, M&S, Caffè Nero, matched by interest, behaviour and location. Launched July 2011; 2.6M registrations in year one, 2.5M+ active. The launch figures are O2's record — I joined in 2013 and owned the reward and offer screens."
  }, {
    h: "Same designer, same stack, opposite job",
    p: "MyO2 is a utility; Priority is a habit. Both on mobile web under a top UK brand, where small things stop being small — a tap target, a spinner, an exact billing figure lands on a stadium at once. The outcome figures are public, reported by O2 and Equal Experts. The claim is the work."
  }],
  plateNo: CF.get("o2").plateNo,
  plateCn: CF.get("o2").provenance,
  ledger: CF.metrics("o2"),
  note: "designed every screen, then built it — mobile web",
  boundary: "Consumer scale from 2013 doesn’t transfer to enterprise AI on its own.",
  stamp: { t: "5★ APP", v: "ok" }
}, {
  no: "03",
  img: "../assets/shots/fintech-screening.png",
  tag: CF.get("fintech").tag,
  title: CF.get("fintech").title,
  standfirst: "I held the release until the LLM could defend its own scores. Then screening sped up 60%.",
  meta: cfMeta("fintech"),
  context: "An LLM read the deal docs and scored the risk. I held the launch until it grounded every claim in a cited source (retrieval) and abstained on thin cases — a confident hallucination nobody signs is dead on arrival. I owned product definition, the abstention and citation UX, and the launch gate; the model's accuracy is the ML team's result to defend. The 60% is analysts no longer re-verifying by hand.",
  moves: [{
    h: "Explain before the verdict",
    p: "An “explain this score” surface: pull a rating into its signals, challenge the weighting, watch it answer — sources beside the number."
  }, {
    h: "Design the decline",
    p: "A visible “I'm not sure about this one” state, so the model could refuse to bluff instead of guessing."
  }, {
    h: "Disagreement on record",
    p: "A logged override when the analyst disagreed — fed the next eval."
  }],
  plateNo: CF.get("fintech").plateNo,
  plateCn: CF.get("fintech").provenance,
  ledger: CF.metrics("fintech"),
  note: "trust = the model declining to bluff",
  boundary: "Weeks of delay bought explainability, and that trade only pays when the user is an expert paid to doubt the answer. For a low-stakes decision nobody audits, holding the launch would have been wrong.",
  stamp: { t: "Trusted", v: "r" }
}, {
  no: "04",
  img: "../assets/shots/adtech-planner.png",
  tag: CF.get("adtech").tag,
  title: CF.get("adtech").title,
  standfirst: "The algorithm beat the traders, and they played their hunches anyway. A missing interface, not a bad model.",
  meta: cfMeta("adtech"),
  context: "The engine beat the buyers; adoption sat near zero. I left the model and rebuilt the interface around it. Once traders acted on it: 45% less time and effort to plan and book a campaign, and 3x uplift in purchase intent with 70% audience uplift against traditional bookings.",
  moves: [{
    h: "A score tied to one action",
    p: "Each recommendation resolved to one verb — act, review, or ignore — never a naked 87% on the screen."
  }, {
    h: "Reasons named out loud",
    p: "A reasoning panel named the exact signals behind each call — not a tooltip, the actual argument a buyer could check like an analyst's."
  }, {
    h: "An override that teaches",
    p: "The override logged the correction and fed next week's model. Watching their pushback land flipped fighting into coaching."
  }],
  plateNo: CF.get("adtech").plateNo,
  plateCn: CF.get("adtech").provenance,
  ledger: CF.metrics("adtech"),
  note: "software did the speed; design did the acting-on-it",
  boundary: "The model was already accurate — the gap I closed was trust, not accuracy. If your model is genuinely wrong, no interface will save it; that’s an upstream fix.",
  stamp: { t: "Shipped", v: "" }
}, {
  no: "05",
  img: "../assets/visuals/case-orgos.svg",
  tag: CF.get("orgos").tag,
  title: CF.get("orgos").title,
  standfirst: "Two hundred people. No managers. Eight modules doing the job of an org chart — coordination that never smuggles a boss back in.",
  meta: cfMeta("orgos"),
  context: "The decision: refuse every feature with a manager hiding inside it. Transparency coordinates — salaries, finances, assignments, open to all — but holds only to forty; at two hundred the hallway stops scaling. Assignment, approval, escalation were each a boss in disguise.",
  moves: [{
    h: "Read access is the feature",
    p: "Who's on what, who's blocked, who decides — visible to everyone, always. Pull, not push. Coordination came from information, not instruction."
  }, {
    h: "Commitments, not assignments",
    p: "People pull work and publish commitments in the open. The system tracks promises kept; it never hands out tasks."
  }, {
    h: "Eight modules, one grammar",
    p: "Staffing, comp, OKRs, onboarding all spoke one object model, so the org could rebuild its own process with nobody in the room."
  }],
  plateNo: CF.get("orgos").plateNo,
  plateCn: CF.get("orgos").provenance,
  ledger: CF.metrics("orgos"),
  note: "the org's numbers, the founders' philosophy — my tooling held at scale",
  boundary: "This ran inside a company that already believed in radical transparency, with no management layer defending its own existence. In a conventional hierarchy it fails on politics long before it fails on product.",
  stamp: { t: "0 Managers", v: "ok" }
}, {
  no: "06",
  img: "../assets/visuals/case-vc.svg",
  tag: CF.get("vc-diligence").tag,
  title: CF.get("vc-diligence").title,
  standfirst: "Partners bet millions on claims they'll never check. An LLM extracted the evidence; the design made them stand on it.",
  meta: cfMeta("vc-diligence"),
  context: "An LLM read the code and docs. No verdict ships without a cited source (retrieval) — unaudited, it's a confident hallucination.",
  moves: [{
    h: "Score at the signal level",
    p: "Confidence on each signal — code quality, architecture risk, team velocity, founder credibility — not one opaque verdict."
  }, {
    h: "Provenance on every claim",
    p: "Each score named the signals that drove it, with a clean drill from summary to source, before a partner committed capital."
  }, {
    h: "Dissent on record",
    p: "Analyst overrides fed back into the model; partner sign-off was real workflow, not a rubber stamp."
  }],
  plateNo: CF.get("vc-diligence").plateNo,
  plateCn: CF.get("vc-diligence").provenance,
  ledger: CF.metrics("vc-diligence"),
  note: "made the model's verdict auditable enough to bet on",
  boundary: "Deliberate friction survives only when the person clicking is personally accountable for the verdict. A user with no downside routes around it.",
  stamp: { t: "4-Day DD", v: "" }
}];
const PATTERN_PAGES = {
  gauge: {
    no: "01",
    k: "gauge",
    h: "Confidence Score Patterns",
    principle: "A bare 87% leaves the user two bad options — over-trust it or ignore it. The score has to offer a third.",
    def: "How much certainty to show, in what form, and the threshold at which a number earns the right to drive a decision instead of decorating a dashboard.",
    note: "a percentage is a feeling until it's anchored to a business action",
    dos: ["Anchor the score to an action — act, review, or ignore — not just a bare number.", "Show the score's own track record so people can calibrate their trust.", "Round to the precision you'd be willing to defend out loud."],
    donts: ["Render 87.3% when what you actually mean is \u201Cprobably.\u201D", "Let a high score auto-execute with no visible way to override.", "Reuse one confidence scale across decisions of wildly different stakes."],
    instTag: "AdTech · Programmatic",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "Media buyers ignored the recommendation until the score sat beside ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "what it had gotten right last month"), ". Confidence with a memory got acted on; confidence alone never did."),
    fig: {
      no: "3.1",
      img: "../assets/visuals/pattern-confidence.svg",
      label: "confidence chip + 30-day track record"
    },
    demo: /*#__PURE__*/React.createElement(GaugeDemo)
  },
  alert: {
    demo: /*#__PURE__*/React.createElement(AlertDemo),
    no: "02",
    k: "alert",
    h: "Failure States",
    principle: "A model that bluffs one confident wrong answer loses the user for good. Design that moment before the happy path.",
    def: "What the screen says when the model can't deliver \u2014 and how saying it honestly makes recovery cheaper than the mistake itself.",
    note: "I design the error recovery first now",
    dos: ["Design the wrong-answer screen before you design the happy path.", "Make recovery from a miss cheaper than the mistake itself.", "Say what the system doesn't know, plainly and early."],
    donts: ["Hide uncertainty behind a confident-looking default.", "File \u201Cwhat if it's wrong\u201D as an edge case to handle later.", "Apologise for an error without offering the next step."],
    instTag: "FinTech · Due Diligence",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "We shipped the ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "\u201CI'm not sure about this one\u201D"), " state first. Analysts trusted the confident answers more once they'd watched the model decline to bluff."),
    fig: {
      no: "3.2",
      img: "../assets/visuals/pattern-failure.svg",
      label: "graceful low-confidence / model-declines state"
    }
  },
  branch: {
    demo: /*#__PURE__*/React.createElement(BranchDemo),
    no: "03",
    k: "branch",
    h: "Explainability",
    principle: "A correct answer nobody can audit loses to a gut nobody can question.",
    def: "Showing a non-technical person why the machine decided, at a depth they can use without a stats degree \u2014 the difference between obeying a score and owning the decision.",
    note: "an output you can audit is an output you'll stand behind",
    dos: ["Show the two or three inputs that actually moved the result.", "Let the user trace from the output back to the evidence.", "Make \u201CI disagree\u201D a first-class, recorded action."],
    donts: ["Dump every feature weight on screen and call it transparency.", "Explain after the decision instead of before it.", "Mistake a tooltip for an account of the reasoning."],
    instTag: "FinTech · Due Diligence",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "Analysts went from ignoring the risk score to ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "leading their memos with it"), " \u2014 once \u201Cexplain this score\u201D surfaced the three documents behind the number."),
    fig: {
      no: "3.3",
      img: "../assets/visuals/pattern-explainability.svg",
      label: "explanation drawer — output traced to source documents"
    }
  },
  loop: {
    demo: /*#__PURE__*/React.createElement(LoopDemo),
    no: "04",
    k: "loop",
    h: "Human-in-the-Loop",
    principle: "Throw away the human's correction and the model never learns — the person just babysits it forever.",
    def: "Where and how the person corrects the system \u2014 turning corrections into the training signal the next version needs, so the workflow scales without growing overhead.",
    note: "correcting the model should feel like teaching, not cleanup",
    dos: ["Make the human's edit visibly improve the next result.", "Put the control where the decision happens, never buried in settings.", "Default to the human's last call when the stakes are high."],
    donts: ["Ask for approval on everything until approval means nothing.", "Treat corrections as exceptions instead of as training signal.", "Make overriding feel like a fight with the product."],
    instTag: "AdTech · Programmatic",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "When a buyer's override visibly retrained the next week's recommendation, correcting the model ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "stopped feeling like rework"), " and started feeling like teaching."),
    fig: {
      no: "3.4",
      img: "../assets/visuals/pattern-loop.svg",
      label: "override → feedback → next recommendation"
    }
  },
  trace: {
    demo: /*#__PURE__*/React.createElement(TraceDemo),
    no: "05",
    k: "trace",
    h: "Provenance & Citations",
    principle: "A citation you can't open is a rumour with a footnote — so the analyst re-checks it by hand anyway.",
    def: "Explainability says why the model decided; provenance says where the evidence came from — the exact source behind every claim, one click from the number to the document that produced it.",
    note: "the score and its sources travel together, or not at all",
    dos: ["Put the source next to the claim, not behind a 'details' link.", "Let a person open the original document the model read, unedited.", "Say how many sources back a number — and flag the one that disagreed."],
    donts: ["Cite a source the user can't actually open and verify.", "Summarise the evidence so heavily that the trail goes cold.", "Reveal provenance only after the answer is challenged."],
    instTag: "VC \xB7 Technical Diligence",
    inst: React.createElement(React.Fragment, null, "Partners signed off faster once every score carried a clean drill from summary to the source document — ", React.createElement("span", { className: "bk-em" }, "they'll stand on an extraction they can open"), ", never one they can't."),
    fig: { no: "3.5", img: "../assets/visuals/pattern-provenance.svg", label: "claim → the sources behind it" }
  },
  bounds: {
    demo: /*#__PURE__*/React.createElement(BoundsDemo),
    no: "06",
    k: "bounds",
    h: "The Capability Contract",
    principle: "Imply the product can do anything and it fails silently the first time it can't — taking the user's trust with it.",
    def: "The model's promise, stated up front: what this system is for, where it taps out, and what it hands back to a human — set before the first use, not after the first complaint.",
    note: "say where it taps out, before it taps out",
    dos: ["State the model's limits in the interface, not just the docs.", "Hand off to a human the moment a request leaves the model's competence.", "Make the boundary specific — 'I can't price illiquid assets,' not 'results may vary.'"],
    donts: ["Imply the product can do things it can't, then degrade silently.", "Bury scope in a terms page nobody reads.", "Treat 'out of scope' as an error instead of an honest answer."],
    instTag: "AdTech \xB7 Programmatic",
    inst: React.createElement(React.Fragment, null, "Each call resolved to act, review, or ignore — and ", React.createElement("span", { className: "bk-em" }, "“ignore” was the model admitting it had nothing worth saying"), ". The honest no is what made buyers believe the act."),
    fig: { no: "3.6", img: "../assets/visuals/pattern-capability.svg", label: "in-scope / out-of-scope, drawn before launch" }
  },
  calib: {
    demo: /*#__PURE__*/React.createElement(CalibDemo),
    no: "07",
    k: "calib",
    h: "Calibration & Track Record",
    principle: "A confident score with no track record is a stranger asking you to bet your reputation on their word.",
    def: "A confidence number is a claim; its track record is the evidence. Show whether “80% sure” has actually been right about 80% of the time — so a person learns how hard to lean, and watches that judgment improve as the history grows.",
    note: "confidence with a memory gets acted on; confidence alone doesn't",
    dos: ["Show the model's hit rate beside its current confidence.", "Break the record down by the kind of case, not one global average.", "Let the history update in the open, so trust is earned, not assumed."],
    donts: ["Show a confidence number with no past to back it.", "Average away the cases where the model is reliably wrong.", "Reset the track record silently every time the model changes."],
    instTag: "FinTech \xB7 Due Diligence",
    inst: React.createElement(React.Fragment, null, "Ninety days and forty-two deals in, the score had been right often enough that analysts ", React.createElement("span", { className: "bk-em" }, "stopped re-checking the confident calls"), ". The history earned the trust the number alone couldn't."),
    fig: { no: "3.7", img: "../assets/visuals/pattern-calibration.svg", label: "confidence beside its own hit rate" }
  },
  undo: {
    demo: /*#__PURE__*/React.createElement(UndoDemo),
    no: "08",
    k: "undo",
    h: "Reversibility",
    principle: "When a suggestion can't be walked back, the safe move is to ignore it. Adoption stalls on fear, not accuracy.",
    def: "Adoption stalls when acting feels risky, not when the model is wrong. Make the action cheap to undo — one click to reverse, a clear path back, no permanent damage — and people will try the recommendation they'd otherwise ignore.",
    note: "reversibility buys the first action; accuracy keeps the rest",
    dos: ["Make acting on a recommendation one click to reverse.", "Show the way back before the person commits.", "Stage risky changes so they can be halted, not just rolled back."],
    donts: ["Hide undo, or make reversing cost more than the original action.", "Make a wrong call feel permanent.", "Force an irreversible commit to get any value from the model."],
    instTag: "EdTech \xB7 PTC University",
    inst: React.createElement(React.Fragment, null, "Retiring four products, I sequenced the shutdowns so every team ", React.createElement("span", { className: "bk-em" }, "watched their users land softly before the lights went out"), " — a migration you could halt beats a leap you can't take back."),
    fig: { no: "3.8", img: "../assets/visuals/pattern-reversibility.svg", label: "act → undo, one move each" }
  }
};
window.BOOK_META = {
  spine: 10
};

/* ---- small SVG bits ---------------------------------------- */
function Emblem() {
  return /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 100 100",
    width: "100%",
    height: "100%",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M49 31 C35 23 24 26 24 26 L24 69 C24 69 36 66 49 75 Z",
    fill: "#F4ECDA"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M51 31 C65 23 76 26 76 26 L76 69 C76 69 64 66 51 75 Z",
    fill: "#F4ECDA"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "50",
    cy: "49",
    r: "6",
    fill: "#CE9230"
  }));
}
/* recurring monogram — the "AM" device + a tiny caption (styled via .bk-device) */
function Device({
  label,
  on,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-device" + (on === "dark" ? " bk-device--on-dark" : ""),
    style: style
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-device__mark"
  }, "AM"), label && /*#__PURE__*/React.createElement("span", {
    className: "bk-device__label"
  }, label));
}
function Dia({
  kind
}) {
  const e = "var(--bk-ember)",
    p = "var(--bk-pine)",
    o = "var(--bk-ochre)";
  const props = {
    width: "100%",
    height: "100%",
    viewBox: "0 0 54 54",
    fill: "none",
    "aria-hidden": "true",
    focusable: "false"
  };
  if (kind === "gauge") return /*#__PURE__*/React.createElement("svg", props, /*#__PURE__*/React.createElement("path", {
    d: "M10 40 A18 18 0 0 1 44 40",
    stroke: p,
    strokeWidth: "3",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "27",
    y1: "40",
    x2: "38",
    y2: "26",
    stroke: e,
    strokeWidth: "3",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "27",
    cy: "40",
    r: "3",
    fill: e
  }));
  if (kind === "alert") return /*#__PURE__*/React.createElement("svg", props, /*#__PURE__*/React.createElement("path", {
    d: "M27 12 L46 44 H8 Z",
    stroke: e,
    strokeWidth: "3",
    strokeLinejoin: "round"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "27",
    y1: "24",
    x2: "27",
    y2: "34",
    stroke: e,
    strokeWidth: "3",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "27",
    cy: "39",
    r: "1.8",
    fill: e
  }));
  if (kind === "branch") return /*#__PURE__*/React.createElement("svg", props, /*#__PURE__*/React.createElement("circle", {
    cx: "14",
    cy: "27",
    r: "5",
    stroke: p,
    strokeWidth: "3"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "40",
    cy: "15",
    r: "4",
    stroke: o,
    strokeWidth: "3"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "40",
    cy: "39",
    r: "4",
    stroke: e,
    strokeWidth: "3"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M19 24 L36 16 M19 30 L36 38",
    stroke: p,
    strokeWidth: "2.4"
  }));
  if (kind === "trace") return React.createElement("svg", props, React.createElement("circle", {
    cx: "27", cy: "12", r: "4", stroke: e, strokeWidth: "3"
  }), React.createElement("line", {
    x1: "27", y1: "16", x2: "27", y2: "26", stroke: p, strokeWidth: "3", strokeLinecap: "round"
  }), React.createElement("rect", {
    x: "16", y: "26", width: "22", height: "18", rx: "2", stroke: p, strokeWidth: "3"
  }), React.createElement("line", {
    x1: "21", y1: "33", x2: "33", y2: "33", stroke: o, strokeWidth: "2.4", strokeLinecap: "round"
  }), React.createElement("line", {
    x1: "21", y1: "38", x2: "30", y2: "38", stroke: o, strokeWidth: "2.4", strokeLinecap: "round"
  }));
  if (kind === "bounds") return React.createElement("svg", props, React.createElement("rect", {
    x: "10", y: "14", width: "26", height: "26", rx: "4", stroke: p, strokeWidth: "3"
  }), React.createElement("circle", {
    cx: "23", cy: "27", r: "3.4", fill: e
  }), React.createElement("circle", {
    cx: "44", cy: "40", r: "3", stroke: o, strokeWidth: "2.6"
  }));
  if (kind === "calib") return React.createElement("svg", props, React.createElement("circle", {
    cx: "27", cy: "27", r: "16", stroke: p, strokeWidth: "3"
  }), React.createElement("circle", {
    cx: "27", cy: "27", r: "9", stroke: o, strokeWidth: "2.6"
  }), React.createElement("circle", {
    cx: "27", cy: "27", r: "3.4", fill: e
  }));
  if (kind === "undo") return React.createElement("svg", props, React.createElement("path", {
    d: "M40 20 A14 14 0 1 0 40 34", stroke: p, strokeWidth: "3", fill: "none", strokeLinecap: "round"
  }), React.createElement("path", {
    d: "M40 14 L40 22 L32 22", stroke: e, strokeWidth: "3", fill: "none", strokeLinecap: "round", strokeLinejoin: "round"
  }), React.createElement("circle", {
    cx: "14", cy: "27", r: "3.4", fill: o
  }));
  return /*#__PURE__*/React.createElement("svg", props, /*#__PURE__*/React.createElement("path", {
    d: "M14 20 A14 14 0 1 1 14 34",
    stroke: p,
    strokeWidth: "3",
    fill: "none",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M14 14 L14 22 L22 22",
    stroke: e,
    strokeWidth: "3",
    fill: "none",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "40",
    cy: "27",
    r: "3.4",
    fill: o
  }));
}

/* ---- reusable page pieces ---------------------------------- */
function Figure({
  no,
  label,
  img
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-figure",
    style: img ? { minHeight: 0 } : null
  }, img ? null : /*#__PURE__*/React.createElement("span", {
    className: "bk-figure__tag"
  }, "Fig. ", no), img ? /*#__PURE__*/React.createElement("img", {
    src: img,
    alt: label,
    loading: "lazy",
    style: { width: "100%", height: "auto", display: "block" }
  }) : /*#__PURE__*/React.createElement("div", {
    className: "bk-figure__mid"
  }, "[ ", label, " ]"));
}
/* a photographic plate — fillable image-slot, or a redacted (NDA) banner */
function Plate({
  id,
  no,
  cn,
  ph,
  redacted,
  wide,
  img
}) {
  const [zoom, setZoom] = React.useState(false);
  const dlgRef = React.useRef(null);
  const returnRef = React.useRef(null);
  React.useEffect(() => {
    if (!zoom) return;
    returnRef.current = document.activeElement;
    if (dlgRef.current) dlgRef.current.focus();
    const h = e => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setZoom(false);
      } else if (e.key === "Tab") {
        e.preventDefault(); // nothing else to tab to — the dialog is the only stop
      }
    };
    window.addEventListener("keydown", h, true);
    return () => {
      window.removeEventListener("keydown", h, true);
      if (returnRef.current && returnRef.current.focus) returnRef.current.focus();
    };
  }, [zoom]);
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-plate" + (redacted ? " bk-plate--redacted" : "") + (wide ? " bk-plate--wide" : "")
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-plate__img"
  }, img ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-label": "Enlarge: " + (cn || "screenshot"),
    onClick: () => setZoom(true),
    style: { all: "unset", display: "block", width: "100%", height: "100%", cursor: "zoom-in", boxSizing: "border-box" }
  }, /*#__PURE__*/React.createElement("img", {
    src: img,
    alt: cn,
    loading: "lazy",
    title: "Click to enlarge",
    style: { width: "100%", height: "100%", objectFit: "cover", display: "block" }
  })), zoom && /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    "aria-label": (cn || "plate") + " \u2014 enlarged. Escape or click to close.",
    tabIndex: -1,
    ref: dlgRef,
    onClick: () => setZoom(false),
    style: { position: "fixed", inset: 0, zIndex: 9999, background: "rgba(20,16,12,.92)", display: "flex", alignItems: "center", justifyContent: "center", cursor: "zoom-out", padding: "3vh 3vw", outline: "none" }
  }, /*#__PURE__*/React.createElement("img", {
    src: img,
    alt: cn,
    style: { maxWidth: "94vw", maxHeight: "92vh", objectFit: "contain", borderRadius: 6, boxShadow: "0 24px 80px rgba(0,0,0,.6)" }
  }))) : redacted ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "bk-plate__ph"
  }, ph), /*#__PURE__*/React.createElement("span", {
    className: "bk-stamp bk-stamp--r",
    style: {
      position: "absolute",
      top: 10,
      right: 10,
      zIndex: 2,
      fontSize: 10,
      padding: "3px 8px"
    }
  }, "Redacted \xB7 NDA")) : /*#__PURE__*/React.createElement("image-slot", {
    id: id,
    placeholder: ph,
    shape: "rect"
  })), /*#__PURE__*/React.createElement("div", {
    className: "bk-plate__cap"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-plate__no"
  }, "Plate ", no), /*#__PURE__*/React.createElement("span", {
    className: "bk-plate__cn"
  }, cn)));
}
function Beat({
  n,
  label,
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-beat"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-beat__label"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-beat__n"
  }, n), /*#__PURE__*/React.createElement("span", {
    className: "bk-beat__t"
  }, label)), children);
}
function DoDont({
  dos,
  donts
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-dodont"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-dd bk-dd--do"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-dd__head"
  }, "Do"), /*#__PURE__*/React.createElement("ul", null, dos.map((d, i) => /*#__PURE__*/React.createElement("li", {
    key: i
  }, d)))), /*#__PURE__*/React.createElement("div", {
    className: "bk-dd bk-dd--dont"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-dd__head"
  }, "Don't"), /*#__PURE__*/React.createElement("ul", null, donts.map((d, i) => /*#__PURE__*/React.createElement("li", {
    key: i
  }, d)))));
}

/* ---- case-study spread builders ---------------------------- */
function caseSpreadA(c) {
  return {
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Case Study \xB7 No. ", c.no), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, c.tag), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "6px 0 0"
      },
      dangerouslySetInnerHTML: {
        __html: c.title
      }
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-standfirst"
    }, c.standfirst), /*#__PURE__*/React.createElement("dl", {
      className: "bk-meta"
    }, c.meta.map(([k, v], i) => /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, /*#__PURE__*/React.createElement("dt", null, k), /*#__PURE__*/React.createElement("dd", null, v)))), /*#__PURE__*/React.createElement(Beat, {
      n: "01",
      label: "Context"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, c.context))),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement(Beat, {
      n: "02",
      label: "The tension"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, c.tension)), /*#__PURE__*/React.createElement(Plate, {
      id: "pl-" + c.key + "-" + c.fig1.no,
      no: c.fig1.no,
      cn: c.fig1.label,
      wide: true,
      img: "../assets/visuals/case-ptc-before.svg",
      ph: "Drop a screenshot \u00b7 " + c.fig1.label
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 18
      }
    }, c.note1))
  };
}
function caseSpreadB(c) {
  return {
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement(Beat, {
      n: "03",
      label: "The decision"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        marginBottom: 2
      }
    }, c.decisionLede)), /*#__PURE__*/React.createElement("div", {
      className: "bk-moves"
    }, c.moves.map((m, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-move",
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-move__n"
    }, i + 1), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", null, m.h), /*#__PURE__*/React.createElement("p", null, m.p))))), /*#__PURE__*/React.createElement(Plate, {
      id: "pl-" + c.key + "-" + c.fig2.no,
      no: c.fig2.no,
      cn: c.fig2.label,
      wide: true,
      img: "../assets/shots/ptc-portal.png",
      ph: "Drop a screenshot \u00b7 " + c.fig2.label
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement(Beat, {
      n: "04",
      label: "The outcome"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-metrics"
    }, c.outcome.map((o, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-metric",
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-metric__v"
    }, o.v), /*#__PURE__*/React.createElement("div", {
      className: "bk-metric__l"
    }, o.l)))), /*#__PURE__*/React.createElement("blockquote", {
      className: "bk-pull",
      style: {
        fontSize: 26
      }
    }, c.quote.t, /*#__PURE__*/React.createElement("cite", null, c.quote.cite)), /*#__PURE__*/React.createElement("div", {
      className: "bk-note bk-note--r",
      style: {
        marginTop: 16
      }
    }, c.note2), c.boundary && /*#__PURE__*/React.createElement("div", {
      className: "bk-boundary",
      style: {
        marginTop: 14,
        paddingTop: 8,
        borderTop: "1px solid var(--bk-rule)"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: "block",
        fontFamily: "var(--bk-mono)",
        fontSize: 9.5,
        letterSpacing: ".12em",
        textTransform: "uppercase",
        color: "var(--bk-ember-deep)",
        marginBottom: 5
      }
    }, "Where this wouldn’t transfer"), /*#__PURE__*/React.createElement("p", {
      style: {
        margin: 0,
        fontSize: 12,
        lineHeight: 1.55,
        color: "var(--bk-ink-soft)"
      }
    }, c.boundary)))
  };
}

/* ---- NDA walk-through (single redacted spread) ------------- */
function caseWalk(c) {
  return {
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Case Study \xB7 No. ", c.no), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, c.tag), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "6px 0 0"
      }
    }, c.title), /*#__PURE__*/React.createElement("p", {
      className: "bk-standfirst"
    }, c.standfirst), /*#__PURE__*/React.createElement("dl", {
      className: "bk-meta"
    }, c.meta.map(([k, v], i) => /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, /*#__PURE__*/React.createElement("dt", null, k), /*#__PURE__*/React.createElement("dd", null, v)))), /*#__PURE__*/React.createElement(Beat, {
      n: "01",
      label: "The problem"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, c.context)), /*#__PURE__*/React.createElement(Plate, {
      id: "pl-case-" + c.no + "-" + c.plateNo,
      no: c.plateNo,
      cn: c.plateCn,
      ph: c.redacted === false ? c.ph || c.plateCn : "Screens under NDA \u2014 full walk-through on request",
      redacted: c.redacted !== false,
      wide: true,
      img: c.img
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal",
      style: {
        position: "relative"
      }
    }, c.stamp && /*#__PURE__*/React.createElement("span", {
      className: "bk-stamp" + (c.stamp.v === "r" ? " bk-stamp--r" : c.stamp.v === "ok" ? " bk-stamp--ok" : ""),
      style: {
        position: "absolute",
        top: -6,
        right: 0,
        zIndex: 3
      }
    }, c.stamp.t), /*#__PURE__*/React.createElement(Beat, {
      n: "02",
      label: "What I did"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-moves"
    }, c.moves.map((m, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-move",
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-move__n"
    }, i + 1), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", null, m.h), /*#__PURE__*/React.createElement("p", null, m.p))))), /*#__PURE__*/React.createElement(Beat, {
      n: "03",
      label: "The outcome"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-ledger"
    }, c.ledger.map((l, i) => /*#__PURE__*/React.createElement("div", {
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-ledger__fig"
    }, l.v), /*#__PURE__*/React.createElement("div", {
      className: "bk-ledger__lbl"
    }, l.l)))), /*#__PURE__*/React.createElement("div", {
      className: "bk-note bk-note--r",
      style: {
        marginTop: 16
      }
    }, c.note), c.boundary && /*#__PURE__*/React.createElement("div", {
      className: "bk-boundary",
      style: {
        marginTop: 14,
        paddingTop: 8,
        borderTop: "1px solid var(--bk-rule)"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: "block",
        fontFamily: "var(--bk-mono)",
        fontSize: 9.5,
        letterSpacing: ".12em",
        textTransform: "uppercase",
        color: "var(--bk-ember-deep)",
        marginBottom: 5
      }
    }, "Where this wouldn’t transfer"), /*#__PURE__*/React.createElement("p", {
      style: {
        margin: 0,
        fontSize: 12,
        lineHeight: 1.55,
        color: "var(--bk-ink-soft)"
      }
    }, c.boundary)), c.redacted !== false ? /*#__PURE__*/React.createElement("p", {
      className: "bk-nda-foot",
      style: {
        marginTop: 14,
        fontSize: 11.5,
        lineHeight: 1.5,
        fontStyle: "italic",
        color: "var(--bk-ink-faint)"
      }
    }, "What you see is a reconstruction or a schematic, never a client's live screen: names and figures on it are synthetic and the client is unnamed. The moves, outcomes and principles are public; I'll walk through the real artifacts and numbers on a call under mutual NDA.") : null)
  };
}

/* ---- pattern spread builder -------------------------------- */
/* Field Guide live demo — Gauge: one confidence score, three stakes, tap to see it resolve to an action (no slider) */
function GaugeDemo() {
  const [stake, setStake] = React.useState(1);
  const MAP = [{
    k: "Low",
    verb: "Act on it",
    sub: "87% clears the bar — let it run.",
    cls: "act"
  }, {
    k: "Medium",
    verb: "Review first",
    sub: "87% is close — a human glances before it ships.",
    cls: "review"
  }, {
    k: "High",
    verb: "Hand to a human",
    sub: "87% isn't enough when the downside is real.",
    cls: "ignore"
  }];
  const m = MAP[stake];
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-demo"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-demo__lead"
  }, "The same score, three stakes — tap one"), /*#__PURE__*/React.createElement("div", {
    className: "bk-demo__row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-demo__chip"
  }, "87%"), /*#__PURE__*/React.createElement("div", {
    className: "bk-demo__seg",
    role: "group",
    "aria-label": "Choose the stakes"
  }, MAP.map((o, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    type: "button",
    className: "bk-demo__seg-btn" + (i === stake ? " is-on" : ""),
    onClick: () => setStake(i),
    "aria-pressed": i === stake
  }, o.k)))), /*#__PURE__*/React.createElement("div", {
    className: "bk-demo__verdict bk-demo__verdict--" + m.cls
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-demo__verb"
  }, "→ ", m.verb), /*#__PURE__*/React.createElement("span", {
    className: "bk-demo__sub"
  }, m.sub)));
}

/* Field Guide — Failure States: flip between a confident read and an honest "I can't" */
function AlertDemo() {
  const h = React.createElement;
  const [ok, setOk] = React.useState(false);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "Tap to see it deliver — or admit it can't"),
    h("div", { className: "bk-demo__seg", role: "group", "aria-label": "Model state" },
      h("button", { type: "button", className: "bk-demo__seg-btn" + (ok ? " is-on" : ""), onClick: () => setOk(true), "aria-pressed": ok }, "Confident"),
      h("button", { type: "button", className: "bk-demo__seg-btn" + (!ok ? " is-on" : ""), onClick: () => setOk(false), "aria-pressed": !ok }, "Unsure")),
    h("div", { className: "bk-demo__verdict" + (ok ? " bk-demo__verdict--act" : "") },
      h("span", { className: "bk-demo__verb" }, ok ? "Risk 7.2 / 10" : "“I can't price this one.”"),
      h("span", { className: "bk-demo__sub" }, ok ? "Confident read — here's the breakdown." : "Illiquid asset — handing you to a human →")));
}

/* Field Guide — Explainability: tap to unfold the reasons behind the number */
function BranchDemo() {
  const h = React.createElement;
  const [open, setOpen] = React.useState(false);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "A number you can audit"),
    h("div", { className: "bk-demo__scoreline" },
      h("span", { className: "bk-demo__chip" }, "Risk 7.2"),
      h("button", { type: "button", className: "bk-demo__btn", onClick: () => setOpen(!open), "aria-expanded": open }, "Why this score? ", h("span", { className: "bk-demo__chev" + (open ? " is-open" : "") }, "▸"))),
    open && h("ul", { className: "bk-demo__panel" },
      h("li", null, "One client is 60% of revenue"),
      h("li", null, "Founder is the sole code owner"),
      h("li", null, "Churn up three quarters running")));
}

/* Field Guide — Human-in-the-Loop: your correction visibly becomes training */
function LoopDemo() {
  const h = React.createElement;
  const [done, setDone] = React.useState(false);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "Correcting it should feel like teaching"),
    h("div", { className: "bk-demo__verdict" + (done ? " bk-demo__verdict--act" : "") },
      h("span", { className: "bk-demo__verb" }, done ? "Noted — you're teaching it" : "Recommend: raise bid 12%"),
      h("span", { className: "bk-demo__sub" }, done ? "Next week's model retrains on your call →" : "Not sure the model's right?")),
    h("button", { type: "button", className: "bk-demo__btn", onClick: () => setDone(!done) }, done ? "↺ start over" : "I disagree"));
}

/* Field Guide — Provenance: the claim and the sources behind it travel together */
function TraceDemo() {
  const h = React.createElement;
  const [open, setOpen] = React.useState(false);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "The score and its sources travel together"),
    h("div", { className: "bk-demo__scoreline" },
      h("span", { className: "bk-demo__verb" }, "“Valuation looks stretched”"),
      h("button", { type: "button", className: "bk-demo__btn", onClick: () => setOpen(!open), "aria-expanded": open }, h("span", { className: "bk-demo__chev" + (open ? " is-open" : "") }, "▸"), " 3 sources")),
    open && h("ul", { className: "bk-demo__panel bk-demo__panel--src" },
      h("li", null, "Cap table · row 14 ↗"),
      h("li", null, "Board deck Q3 · p. 8 ↗"),
      h("li", null, "Auditor's note · §2.1 ↗")));
}

/* Field Guide — Capability Contract: switch between what it does and what it declines */
function BoundsDemo() {
  const h = React.createElement;
  const [inScope, setIn] = React.useState(true);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "An honest “no”, drawn up front"),
    h("div", { className: "bk-demo__seg", role: "group", "aria-label": "Scope" },
      h("button", { type: "button", className: "bk-demo__seg-btn" + (inScope ? " is-on" : ""), onClick: () => setIn(true), "aria-pressed": inScope }, "In scope"),
      h("button", { type: "button", className: "bk-demo__seg-btn" + (!inScope ? " is-on" : ""), onClick: () => setIn(false), "aria-pressed": !inScope }, "Out of scope")),
    h("div", { className: "bk-demo__verdict" + (inScope ? " bk-demo__verdict--act" : "") },
      h("span", { className: "bk-demo__verb" }, inScope ? "✓ Price liquid public equities" : "✗ Illiquid, pre-revenue assets"),
      h("span", { className: "bk-demo__sub" }, inScope ? "Confident here — this is the job." : "Out of range — handed to a human, not guessed.")));
}

/* Field Guide — Calibration: reveal whether the confidence has been right before */
function CalibDemo() {
  const h = React.createElement;
  const [show, setShow] = React.useState(false);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "Confidence with a memory"),
    h("div", { className: "bk-demo__scoreline" },
      h("span", { className: "bk-demo__chip" }, "80% sure"),
      h("button", { type: "button", className: "bk-demo__btn", onClick: () => setShow(!show), "aria-expanded": show }, show ? "hide track record" : "Show its track record ▸")),
    show && h("div", { className: "bk-demo__panel" },
      h("div", { className: "bk-demo__stat" }, h("b", null, "Right 82% of the time"), h("span", null, " · across its last 200 calls at this confidence")),
      h("div", { className: "bk-demo__bar" }, h("span", { style: { width: "82%" } }))));
}

/* Field Guide — Reversibility: watch how a way-back changes whether people act */
function UndoDemo() {
  const h = React.createElement;
  const [safe, setSafe] = React.useState(true);
  return h("div", { className: "bk-demo" },
    h("div", { className: "bk-demo__lead" }, "Reversibility buys the first action"),
    h("div", { className: "bk-demo__seg", role: "group", "aria-label": "Reversibility" },
      h("button", { type: "button", className: "bk-demo__seg-btn" + (safe ? " is-on" : ""), onClick: () => setSafe(true), "aria-pressed": safe }, "1-click undo"),
      h("button", { type: "button", className: "bk-demo__seg-btn" + (!safe ? " is-on" : ""), onClick: () => setSafe(false), "aria-pressed": !safe }, "No way back")),
    h("div", { className: "bk-demo__verdict" + (safe ? " bk-demo__verdict--act" : "") },
      h("span", { className: "bk-demo__verb" }, safe ? "Act now — undo anytime" : "Act now — permanent"),
      h("span", { className: "bk-demo__sub" }, safe ? "Cheap to walk back, so people try it." : "Feels risky — so most won't act at all.")));
}

function patternSpread(p) {
  return {
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Pattern \xB7 No. ", p.no), /*#__PURE__*/React.createElement("div", {
      className: "bk-pat-hero"
    }, /*#__PURE__*/React.createElement(Dia, {
      kind: p.k
    })), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "2px 0 0"
      }
    }, p.h), /*#__PURE__*/React.createElement("p", {
      className: "bk-principle-stmt"
    }, p.principle), /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, p.def), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 18
      }
    }, p.note)),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Do & don't"), /*#__PURE__*/React.createElement(DoDont, {
      dos: p.dos,
      donts: p.donts
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-instance"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-instance__label"
    }, "From the work \xB7 ", p.instTag), /*#__PURE__*/React.createElement("p", null, p.inst)), p.demo || /*#__PURE__*/React.createElement(Figure, {
      no: p.fig.no,
      label: p.fig.label,
      img: p.fig.img
    }))
  };
}

/* ---- contact form (own state) ------------------------------ */
function ContactForm() {
  const [email, setEmail] = React.useState("");
  const [product, setProduct] = React.useState("");
  const [sent, setSent] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  if (sent) return /*#__PURE__*/React.createElement("div", {
    className: "bk-ok"
  }, "Got it — I reply within 48 hours.");
  return /*#__PURE__*/React.createElement("form", {
    className: "bk-form",
    onSubmit: e => {
      e.preventDefault();
      if (!email.trim()) return;
      setLoading(true);
      setError("");
      fetch("https://formspree.io/f/xpqednyy", {
        method: "POST",
        headers: { "Accept": "application/json" },
        body: new FormData(e.target)
      }).then(r => r.json()).then(data => {
        setLoading(false);
        if (data.ok) setSent(true);
        else setError("Something went wrong — please try again.");
      }).catch(() => {
        setLoading(false);
        setError("Could not connect — please try again.");
      });
    }
  }, /*#__PURE__*/React.createElement("label", {
    className: "bk-form__label",
    htmlFor: "bk-email",
    style: { fontFamily: "var(--bk-mono)", fontSize: "11px", letterSpacing: ".04em", textTransform: "uppercase", color: "var(--bk-ink-faint)", marginBottom: "3px" }
  }, "Your work email"), /*#__PURE__*/React.createElement("input", {
    type: "email",
    id: "bk-email",
    name: "email",
    required: true,
    placeholder: "you@company.com",
    value: email,
    onChange: e => setEmail(e.target.value)
  }), /*#__PURE__*/React.createElement("label", {
    className: "bk-form__label",
    htmlFor: "bk-product",
    style: { fontFamily: "var(--bk-mono)", fontSize: "11px", letterSpacing: ".04em", textTransform: "uppercase", color: "var(--bk-ink-faint)", marginBottom: "3px" }
  }, "Link to the role or your company (optional)"), /*#__PURE__*/React.createElement("input", {
    type: "url",
    id: "bk-product",
    name: "product",
    placeholder: "https://… the role you're hiring for",
    value: product,
    onChange: e => setProduct(e.target.value)
  }), error ? /*#__PURE__*/React.createElement("p", {
    role: "alert",
    style: { color: "var(--bk-ember)", fontSize: "12px", margin: "4px 0 0", fontFamily: "var(--bk-mono)" }
  }, error) : null, /*#__PURE__*/React.createElement("button", {
    type: "submit",
    className: "bk-btn bk-btn--ghost",
    disabled: loading
  }, loading ? "Sending…" : "Send me the role →"));
}

/* ---- runheads ---------------------------------------------- */
const VERSO = "Arpit Maheshwari";
function buildBook(ctx) {
  const go = ctx.go; // jump within the spine
  const jumpTo = ctx.jumpTo || go; // mobile-aware jump
  const enter = ctx.enter; // open a section a level deeper: enter(key, idx)
  const TOC = [{
    n: "ii",
    name: "How I Lead",
    sub: "Principles & approach",
    pg: "p. ii",
    to: 2
  }, {
    n: "iv",
    name: "The Method",
    sub: "How the work gets made",
    pg: "p. iv",
    to: 3
  }, {
    n: "I",
    name: "Selected Work",
    sub: "Case studies",
    pg: "p. 2",
    to: 4
  }, {
    n: "II",
    name: "A Field Guide to Trust",
    sub: "AI UX patterns",
    pg: "p. 4",
    to: 5
  }, {
    n: "III",
    name: "Notes & Writing",
    sub: "Essays, talks, field notes",
    pg: "p. 6",
    to: 6
  }, {
    n: "IV",
    name: "Curriculum Vitæ",
    sub: "The printable appendix",
    pg: "p. 8",
    to: 7
  }, {
    n: "V",
    name: "Contact",
    sub: "Write to me — let's talk",
    pg: "p. 10",
    to: 8
  }];
  const ptcA = caseSpreadA(CASES.ptc),
    ptcB = caseSpreadB(CASES.ptc);
  const ndaPages = NDA_CASES.map(c => caseWalk(c));
  const patPages = ["gauge", "alert", "branch", "loop", "trace", "bounds", "calib", "undo"].map(k => patternSpread(PATTERN_PAGES[k]));

  /* ----- THE SPINE — seven spreads, the only linear flow ----- */
  const spine = [/* 0 · COVER */
  {
    kind: "cover",
    cover: /*#__PURE__*/React.createElement("div", {
      className: "bk-cover"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__imprint"
    }, "Human in the Loop \xB7 MMXXVI"), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__emblem"
    }, /*#__PURE__*/React.createElement(Device, {
      on: "dark",
      label: "Human in the Loop"
    })), /*#__PURE__*/React.createElement("h1", {
      className: "bk-cover__title"
    }, "The half-second where a person decides to ", /*#__PURE__*/React.createElement("em", null, "bet"), " on a machine."), /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__rule"
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-cover__byline"
    }, "Arpit Maheshwari"), /*#__PURE__*/React.createElement("p", { className: "bk-cover__skim" }, "Product & design leader for AI products \xB7 shipped to 4M+"), /*#__PURE__*/React.createElement("a", { className: "bk-cover__skimlink", href: "../index.html?view=classic", onClick: e => { e.stopPropagation(); try { localStorage.setItem("am-view", "classic"); } catch (err) {} } }, "Read the classic site instead \u2192"), /*#__PURE__*/React.createElement("button", {
      className: "bk-cover__open",
      onClick: () => go(1),
      "aria-label": "Open the book \u2014 tap or press space"
    }, /*#__PURE__*/React.createElement("span", {
      className: "dot"
    }), " Open \u2014 6 AI case studies inside \u2192"), /*#__PURE__*/React.createElement("span", {
      className: "bk-cover__openhint",
      style: {
        display: "block",
        marginTop: 8,
        fontSize: 11,
        letterSpacing: ".04em",
        opacity: 0.6
      }
    }, "tap or press space"))
  }, /* 1 · TITLE / CONTENTS */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "Contents",
    folioL: "—",
    folioR: "i",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal",
      style: {
        display: "flex",
        flexDirection: "column",
        height: "100%"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__imprint",
      style: {
        color: "var(--bk-ink-faint)"
      }
    }, "Human in the Loop"), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement(Device, {
      label: "the monogram",
      style: {
        marginBottom: 22
      }
    }), /*#__PURE__*/React.createElement("h1", {
      className: "bk-title bk-title--l",
      dangerouslySetInnerHTML: {
        __html: ctx.headline
      }
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-lede",
      style: {
        marginTop: 18,
        maxWidth: "30ch"
      }
    }, "Fifteen years, five industries, the same half-second: the model surfaces something true, and the person at the screen pauses — not because the model is wrong, but because they don’t know how to bet on it yet. This book is everything I’ve worked out about that pause."), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        fontSize: 13,
        color: "var(--bk-ink-faint)"
      }
    }, "Set in Newsreader & Spectral \xB7 Indore, India \xB7 MMXXVI")),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Table of Contents"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "10px 0 18px"
      }
    }, "Contents"), /*#__PURE__*/React.createElement("div", {
      className: "bk-toc"
    }, TOC.map((tc, i) => /*#__PURE__*/React.createElement("button", {
      className: "bk-toc__item",
      key: i,
      onClick: () => jumpTo(tc.to),
      onKeyDown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); jumpTo(tc.to); } },
      "aria-label": tc.name
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-toc__num"
    }, tc.n), /*#__PURE__*/React.createElement("span", {
      className: "bk-toc__name"
    }, tc.name, /*#__PURE__*/React.createElement("small", null, tc.sub)), /*#__PURE__*/React.createElement("span", {
      className: "bk-toc__pg"
    }, tc.pg)))), /*#__PURE__*/React.createElement("div", {
      className: "bk-note bk-note--r",
      style: {
        marginTop: 26
      }
    }, "arrows, \u2190 \u2192 keys, or swipe to turn \u2014 open an item to go deeper \u2197"))
  }, /* 2 · How I Lead (front matter) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "How I Lead",
    folioL: "ii",
    folioR: "iii",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "How I lead"), /*#__PURE__*/React.createElement("div", {
      className: "bk-plate bk-tape",
      style: { marginTop: 14, marginBottom: 32 }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-plate__img",
      style: { aspectRatio: "1 / 1", maxWidth: 220 }
    }, /*#__PURE__*/React.createElement("image-slot", {
      id: "about-portrait",
      placeholder: "Drop a portrait",
      shape: "rect",
      src: "../arpit-maheshwari.jpg"
    })), /*#__PURE__*/React.createElement("div", {
      className: "bk-plate__cap"
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-plate__no"
    }, "Frontispiece"), /*#__PURE__*/React.createElement("span", {
      className: "bk-plate__cn"
    }, "the author"))), /*#__PURE__*/React.createElement("p", {
      className: "bk-lede bk-drop",
      style: {
        marginTop: 0
      }
    }, "Hire me and week one looks like this: reading eval results before opening a design file, sitting silent on customer calls, writing the diagnosis nobody assigned. The best call in an AI product is rarely the interface — it's ", /*#__PURE__*/React.createElement("span", {
      className: "bk-mark"
    }, "what the system admits it doesn't know"), "."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 22
      }
    }, "the miss, written down: my first accessibility pass buried screen-reader users in verbose ARIA labels — they skim, not listen. A week with the monitor off, then I recoded it."), /*#__PURE__*/React.createElement("div", {
      className: "bk-coffee",
      "aria-hidden": "true",
      style: {
        marginTop: 34
      }
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Principles"), /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 14
      }
    }, PRINCIPLES.map((p, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-principle",
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-principle__n"
    }, String(i + 1).padStart(2, "0")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", null, p.h), /*#__PURE__*/React.createElement("p", null, p.p))))))
  }, /* 2b · The Method (front matter) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "The Method",
    folioL: "iv",
    folioR: "v",
    left: /*#__PURE__*/React.createElement("div", { className: "bk-reveal" },
      /*#__PURE__*/React.createElement("div", { className: "bk-kicker" }, "The Method"),
      /*#__PURE__*/React.createElement("p", { className: "bk-lede bk-drop", style: { marginTop: 14 } },
        "Every product is a series of bets someone else has to accept. The process isn\u2019t a ritual for making screens \u2014 it\u2019s a machine for making each bet ",
        /*#__PURE__*/React.createElement("span", { className: "bk-mark" }, "smaller, better-evidenced, and easier to say yes to"), "."),
      /*#__PURE__*/React.createElement("img", {
        src: "../assets/visuals/method-book.svg",
        alt: "The method in three acts: the wager (desirable, feasible, viable), the spiral of four moves, and the open loop from MVP to version n",
        style: { width: "100%", maxWidth: 430, display: "block", margin: "22px 0 0" }
      }),
      /*#__PURE__*/React.createElement("div", { className: "bk-note", style: { marginTop: 20 } },
        "the same shape on every project, whatever the industry")),
    right: /*#__PURE__*/React.createElement("div", { className: "bk-reveal" },
      /*#__PURE__*/React.createElement("div", { className: "bk-kicker" }, "The four moves of the spiral"),
      /*#__PURE__*/React.createElement("div", { style: { marginTop: 14 } },
        [["01", "Listen", "Research the problem space in its own words, not mine. Act / Review / Ignore was born here \u2014 watching traders override a correct model."],
         ["02", "Structure", "Journeys and information architecture: what the product is, before what it looks like."],
         ["03", "Prove", "AI-assisted working HTML, not clickable pictures \u2014 tested with users, and when it survives, shipped as part of the codebase."],
         ["04", "Land", "Visual design, brand, tone \u2014 where PlanIt's downcast mascot lived; the layer people mistake for the whole job."]
        ].map((m, i) => /*#__PURE__*/React.createElement("div", { className: "bk-principle", key: i },
          /*#__PURE__*/React.createElement("span", { className: "bk-principle__n" }, m[0]),
          /*#__PURE__*/React.createElement("div", null,
            /*#__PURE__*/React.createElement("h4", null, m[1]),
            /*#__PURE__*/React.createElement("p", null, m[2]))))),
      /*#__PURE__*/React.createElement("p", { className: "bk-lede", style: { marginTop: 20, fontStyle: "italic" } },
        "\u201CConfidence is earned in loops, not declared in launches.\u201D"))
  }, /* 4 · CHAPTER I — SELECTED WORK (hub) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "I · Selected Work",
    folioL: "2",
    folioR: "3",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Chapter One"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 I"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--l",
      style: {
        margin: "4px 0 16px"
      }
    }, "Selected", /*#__PURE__*/React.createElement("br", null), "Work"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body bk-drop"
    }, "Every brief opened with “improve the UX.” Every diagnosis ended somewhere else. Fifteen years of this work mostly lives behind NDAs; the six here are the shape of all of it — two told in full, four as decision walkthroughs."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        margin: "22px 0 18px"
      }
    }, "begin here \u2193"), /*#__PURE__*/React.createElement("div", {
      className: "bk-feature bk-feature--link",
      role: "button",
      tabIndex: 0,
      onClick: () => enter("cases", 0),
      onKeyDown: e => { if (e.key === "Enter" || e.key === " ") { if (e.key === " ") e.preventDefault(); enter("cases", 0); } }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-item__tag"
    }, WORK[0].tag), /*#__PURE__*/React.createElement("h4", {
      className: "bk-serifhead",
      style: {
        margin: "6px 0 8px"
      }
    }, WORK[0].title), /*#__PURE__*/React.createElement("div", {
      className: "bk-feature__metric"
    }, WORK[0].metric), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        fontSize: 13.5,
        marginTop: 8
      }
    }, WORK[0].desc), /*#__PURE__*/React.createElement("div", {
      className: "bk-feature__more"
    }, "Open the case study ", /*#__PURE__*/React.createElement("span", null, "\u2197 go deeper")))),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Also in this volume"), /*#__PURE__*/React.createElement("div", {
      className: "bk-list",
      style: {
        marginTop: 8
      }
    }, WORK.slice(1).map((w, i) => {
      const openIdx = [2, 3, 4, 5, 6][i];
      return /*#__PURE__*/React.createElement("div", {
        className: "bk-item bk-item--link",
        key: i,
        role: "button",
        tabIndex: 0,
        onClick: () => enter("cases", openIdx),
        onKeyDown: e => { if (e.key === "Enter" || e.key === " ") { if (e.key === " ") e.preventDefault(); enter("cases", openIdx); } }
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-item__top"
      }, /*#__PURE__*/React.createElement("span", {
        className: "bk-item__tag"
      }, w.tag), /*#__PURE__*/React.createElement("span", {
        className: "bk-item__metric"
      }, w.metric)), /*#__PURE__*/React.createElement("h4", null, w.title, /*#__PURE__*/React.createElement("span", {
        className: "bk-item__case"
      }, "open \u2197")), /*#__PURE__*/React.createElement("p", null, w.desc));
    })), /*#__PURE__*/React.createElement("div", {
      className: "bk-note bk-note--r",
      style: {
        marginTop: 22
      }
    }, "four are redacted — the logos are just shy."))
  }, /* 4 · CHAPTER III — A FIELD GUIDE TO TRUST (hub) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "II · A Field Guide to Trust",
    folioL: "4",
    folioR: "5",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Chapter Two"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 II"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--l",
      style: {
        margin: "4px 0 16px"
      }
    }, "A Field", /*#__PURE__*/React.createElement("br", null), "Guide to", /*#__PURE__*/React.createElement("br", null), "Trust"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body bk-drop"
    }, "A design system for trusting and governing AI agents. Everything here ran in production, failed somewhere specific, and came back stronger — the tradeoffs are written down because I paid for them once, so you don’t have to."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 22
      }
    }, "open a pattern to go a level deeper \u2197"), /*#__PURE__*/React.createElement(Device, {
      label: "prior art: PAIR \u00B7 HAX \u2014 this is the production-side report",
      style: {
        marginTop: 30
      }
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "The patterns"), /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 12
      }
    }, PATTERNS.map((p, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-pattern bk-pattern--link",
      key: i,
      role: "button",
      tabIndex: 0,
      onClick: () => enter("patterns", i),
      onKeyDown: e => { if (e.key === "Enter" || e.key === " ") { if (e.key === " ") e.preventDefault(); enter("patterns", i); } }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-pattern__dia"
    }, /*#__PURE__*/React.createElement(Dia, {
      kind: p.k
    })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", null, p.h, " ", /*#__PURE__*/React.createElement("span", {
      className: "bk-pattern__go"
    }, "open \u2197")), /*#__PURE__*/React.createElement("p", null, p.p))))))
  }, /* 5 · CHAPTER IV — WRITING */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "III · Notes & Writing",
    folioL: "6",
    folioR: "7",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal",
      style: {
        display: "flex",
        flexDirection: "column",
        height: "100%"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Chapter Three"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 III"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--l",
      style: {
        margin: "4px 0 20px"
      }
    }, "Notes &", /*#__PURE__*/React.createElement("br", null), "Writing"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "These notes live on ", /*#__PURE__*/React.createElement("a", {
      href: "https://arpitmaheshwari.substack.com",
      target: "_blank",
      rel: "noopener",
      className: "bk-em"
    }, "Human in the Loop ", Icon({ name: "external", cls: "bk-icon--sm" })), ". One idea per issue, on getting humans to act on machines. The fastest way to know how I think before you hire me."), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-note"
    }, "I write to find out what I think.")),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Selected pieces"), /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 14
      }
    }, WRITING.map((w, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-writing",
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-writing__date"
    }, w.d), /*#__PURE__*/React.createElement("h4", null, w.h), /*#__PURE__*/React.createElement("p", null, w.p), /*#__PURE__*/React.createElement("a", {
      href: "https://arpitmaheshwari.substack.com",
      target: "_blank",
      rel: "noopener",
      className: "bk-em bk-writing__link"
    }, "View on Substack ", Icon({ name: "arrow-right", cls: "bk-icon--sm" }))))))
  }, /* APPENDIX - CURRICULUM VITAE */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "Appendix · Curriculum Vitæ",
    folioL: "8",
    folioR: "9",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal",
      style: {
        display: "flex",
        flexDirection: "column",
        height: "100%"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Appendix"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "8px 0 12px"
      }
    }, "Curriculum Vit\xE6"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "The facts, in order — for the founder who checks the work before the call. Every number arrives holding its baseline."), /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__sub"
    }, "What I do"), /*#__PURE__*/React.createElement("div", {
      className: "bk-chips"
    }, CV_SKILLS.map((s, i) => /*#__PURE__*/React.createElement("span", {
      className: "bk-chip",
      key: i
    }, s))), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 18
      }
    }, "the rest travels by walk-through.")),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__sub",
      style: {
        marginTop: 0
      }
    }, "Experience"), /*#__PURE__*/React.createElement("div", {
      className: "bk-cv"
    }, CV_EXP.map((r, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__row",
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__yr"
    }, r.yr), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", {
      className: "bk-cv__role"
    }, r.role), /*#__PURE__*/React.createElement("p", {
      className: "bk-cv__org"
    }, r.org))))), /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__sub"
    }, "Education & recognition"), /*#__PURE__*/React.createElement("div", {
      className: "bk-cv"
    }, CV_EDU.map((r, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__row",
      key: i
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cv__yr"
    }, r.yr), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", {
      className: "bk-cv__role"
    }, r.role), /*#__PURE__*/React.createElement("p", {
      className: "bk-cv__org"
    }, r.org))))))
  }, /* COLOPHON & CONTACT */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "Contact",
    folioL: "10",
    folioR: "11",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal",
      style: {
        display: "flex",
        flexDirection: "column",
        height: "100%"
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Let's talk"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "4px 0 14px"
      }
    }, "Building in AI?"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "Your model is right. Your users still won’t bet on it. That half-second of doubt is the only thing I design. Founding product & design lead for AI products — also open to a staff or director human-in-the-loop seat. Available."), /*#__PURE__*/React.createElement(React.Fragment, null), /*#__PURE__*/React.createElement("div", {
      className: "bk-social",
      style: {
        marginTop: 24
      }
    }, /*#__PURE__*/React.createElement("a", {
      className: "bk-social__btn",
      href: "https://www.linkedin.com/in/arpitmaheshwariprofile/",
      target: "_blank",
      rel: "noopener",
      "aria-label": "LinkedIn"
    }, Icon({
      name: "linkedin"
    })), /*#__PURE__*/React.createElement("a", {
      className: "bk-social__btn",
      href: "https://arpitmaheshwari.substack.com",
      target: "_blank",
      rel: "noopener",
      "aria-label": "Substack — Human in the Loop"
    }, Icon({
      name: "rss"
    })), /*#__PURE__*/React.createElement("a", {
      className: "bk-social__btn",
      href: "https://github.com/arpitmaheshwari/",
      target: "_blank",
      rel: "noopener",
      "aria-label": "GitHub"
    }, Icon({
      name: "github"
    }))), /*#__PURE__*/React.createElement("div", {
      className: "bk-chips",
      style: { marginTop: 20 }
    }, STATUS.map((st, i) => /*#__PURE__*/React.createElement("span", {
      className: "bk-chip",
      key: i
    }, st))), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: { marginTop: 16 }
    }, "prefer to talk first? ", /*#__PURE__*/React.createElement("a", {
      href: "https://calendly.com/arpitmaheshwari",
      target: "_blank",
      rel: "noopener",
      style: { color: "var(--bk-ember-ink, #B04A24)" }
    }, "book 30 minutes \u2197")), /*#__PURE__*/React.createElement("p", { style: { marginTop: 14, fontSize: 12.5, fontStyle: "italic", lineHeight: 1.5, color: "var(--bk-ink-faint)" } }, "I do human-in-the-loop design for AI products — the surface where a person decides to act on the model."), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement(Device, {
      label: "fin.",
      style: {
        marginBottom: 14
      }
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Hiring?"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "8px 0 10px"
      }
    }, "Send me", /*#__PURE__*/React.createElement("br", null), "the role."), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        marginBottom: 14
      }
    }, "A line about the role and the stage, or just a link — I reply within 48 hours. Prefer email? ", /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: function (e) { var u = "maheshwari.arpit" + "88", d = "gmail.com"; e.currentTarget.href = "mailto:" + u + "@" + d + "?subject=Role%20for%20Arpit"; },
      style: { color: "var(--bk-ember-ink, #B04A24)" }
    }, "write to me directly \u2192")), /*#__PURE__*/React.createElement(ContactForm, null), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: { marginTop: "auto", textAlign: "center", paddingTop: 16 }
    }, "thanks for reading to the end ♥"))
  }];

  /* ----- SECTIONS — one level deeper, opened from a hub ----- */
  const sections = {
    cases: {
      parent: 4,
      label: "Selected Work",
      kind: "Case study",
      items: [{
        crumb: "PTC University",
        idxLabel: "1 / 2",
        runheadR: "PTC University",
        folioL: "1",
        folioR: "2",
        ...ptcA
      }, {
        crumb: "PTC University",
        idxLabel: "2 / 2",
        runheadR: "PTC University",
        folioL: "3",
        folioR: "4",
        ...ptcB
      }, {
        crumb: "MyO2 & Priority Moments",
        idxLabel: "in brief",
        runheadR: "Telefónica MyO2 & Priority Moments",
        folioL: "1",
        folioR: "2",
        ...ndaPages[0]
      }, {
        crumb: "Private Equity Investing",
        idxLabel: "walk-through",
        runheadR: "AI-Assisted Private Equity Investing",
        folioL: "1",
        folioR: "2",
        ...ndaPages[1]
      }, {
        crumb: "Programmatic",
        idxLabel: "walk-through",
        runheadR: "Programmatic Advertising Platform",
        folioL: "1",
        folioR: "2",
        ...ndaPages[2]
      }, {
        crumb: "OrgOS",
        idxLabel: "walk-through",
        runheadR: "OrgOS",
        folioL: "1",
        folioR: "2",
        ...ndaPages[3]
      }, {
        crumb: "Technical Due Diligence",
        idxLabel: "walk-through",
        runheadR: "Technical Due Diligence Platform",
        folioL: "1",
        folioR: "2",
        ...ndaPages[4]
      }]
    },
    patterns: {
      parent: 6,
      label: "A Field Guide to Trust",
      kind: "Pattern",
      items: [{
        crumb: "Confidence Score Patterns",
        idxLabel: "1 / 8",
        runheadR: "Confidence Score Patterns",
        folioL: "1",
        folioR: "2",
        ...patPages[0]
      }, {
        crumb: "Failure States",
        idxLabel: "2 / 8",
        runheadR: "Failure States",
        folioL: "1",
        folioR: "2",
        ...patPages[1]
      }, {
        crumb: "Explainability",
        idxLabel: "3 / 8",
        runheadR: "Explainability",
        folioL: "1",
        folioR: "2",
        ...patPages[2]
      }, {
        crumb: "Human-in-the-Loop",
        idxLabel: "4 / 8",
        runheadR: "Human-in-the-Loop",
        folioL: "1",
        folioR: "2",
        ...patPages[3]
      }, {
        crumb: "Provenance & Citations",
        idxLabel: "5 / 8",
        runheadR: "Provenance & Citations",
        folioL: "1",
        folioR: "2",
        ...patPages[4]
      }, {
        crumb: "The Capability Contract",
        idxLabel: "6 / 8",
        runheadR: "The Capability Contract",
        folioL: "1",
        folioR: "2",
        ...patPages[5]
      }, {
        crumb: "Calibration & Track Record",
        idxLabel: "7 / 8",
        runheadR: "Calibration & Track Record",
        folioL: "1",
        folioR: "2",
        ...patPages[6]
      }, {
        crumb: "Reversibility",
        idxLabel: "8 / 8",
        runheadR: "Reversibility",
        folioL: "1",
        folioR: "2",
        ...patPages[7]
      }]
    }
  };
  return {
    spine,
    sections
  };
}
window.buildBook = buildBook;

/* ===== APP ===== */

const {
  useState,
  useRef,
  useEffect,
  useCallback,
  useLayoutEffect
} = React;
const SPREAD_W = 1180,
  SPREAD_H = 880,
  COVER_W = 620,
  COVER_H = 880;
const TWEAK_DEFAULTS = {
  "accent": "#C0512B",
  "pairing": "Newsreader \u00b7 Spectral",
  "warmth": 70,
  "density": "comfy",
  "headline": "Arpit\u003cbr\/>Maheshwari"
};
const PAIRINGS = {
  "Newsreader · Spectral": {
    d: "'Newsreader', Georgia, serif",
    s: "'Spectral', Georgia, serif"
  },
  "Instrument · Newsreader": {
    d: "'Instrument Serif', Georgia, serif",
    s: "'Newsreader', Georgia, serif"
  },
  "Cormorant · Garamond": {
    d: "'Cormorant Garamond', Georgia, serif",
    s: "'EB Garamond', Georgia, serif"
  },
  "Playfair · Spectral": {
    d: "'Playfair Display', Georgia, serif",
    s: "'Spectral', Georgia, serif"
  },
  "DM Serif · Newsreader": {
    d: "'DM Serif Display', Georgia, serif",
    s: "'Newsreader', Georgia, serif"
  },
  "Spectral, all": {
    d: "'Spectral', Georgia, serif",
    s: "'Spectral', Georgia, serif"
  },
  "Newsreader, all": {
    d: "'Newsreader', Georgia, serif",
    s: "'Newsreader', Georgia, serif"
  }
};
const DEEP = {
  "#AE4B2E": "#83341B",
  // terracotta
  "#2F5D52": "#1F4339",
  // pine
  "#B07C24": "#875D14",
  // amber
  "#8E3942": "#6A2A30",
  // claret
  "#C0512B": "#97391A",
  // coral (book default)
  "#3D4F86": "#2A395F",
  // indigo
  "#236E6B": "#154F4D" // teal
};
function mix(a, b, t) {
  const p = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const A = p(a),
    B = p(b);
  return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join("");
}
function ChapterMenu({
  spine,
  onPick,
  onClose
}) {
  const panelRef = useRef(null);
  useEffect(() => {
    const el = panelRef.current;
    if (el) {
      const first = el.querySelector("button");
      if (first) first.focus();
    }
    const onKey = e => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    document.addEventListener("keydown", onKey, true);
    return () => document.removeEventListener("keydown", onKey, true);
  }, [onClose]);
  const items = [{
    i: 0,
    label: "Cover",
    sub: "Home"
  }].concat(spine.slice(1).map((sp, k) => ({
    i: k + 1,
    label: sp.runheadR,
    sub: null
  })));
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-menu",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-menu__panel",
    ref: panelRef,
    role: "dialog",
    "aria-modal": "true",
    "aria-label": "Jump to a chapter",
    onClick: e => e.stopPropagation()
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-menu__head"
  }, "Jump to a chapter"), items.map(it => /*#__PURE__*/React.createElement("button", {
    key: it.i,
    className: "bk-menu__item",
    onClick: () => onPick(it.i)
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-menu__label"
  }, it.label), it.sub ? /*#__PURE__*/React.createElement("span", {
    className: "bk-menu__sub"
  }, it.sub) : null)), /*#__PURE__*/React.createElement("button", {
    className: "bk-menu__exit",
    onClick: () => { try { localStorage.setItem('am-view', 'classic'); } catch (e) {} location.href = '../index.html?view=classic'; }
  }, "Switch to the classic website ", Icon({ name: "arrow-up-right", cls: "bk-icon--sm" }))));
}
function Icon(props) {
  var name = props.name;
  var has = typeof window !== "undefined" && window.MonographIcons && MonographIcons.has && MonographIcons.has(name);
  var html = has ? MonographIcons.markup(name, props.cls ? {
    "class": props.cls
  } : {}) : "";
  return /*#__PURE__*/React.createElement("span", {
    className: "bk-iconwrap",
    dangerouslySetInnerHTML: {
      __html: html
    }
  });
}
function Arrow({
  dir,
  onClick,
  disabled
}) {
  return /*#__PURE__*/React.createElement("button", {
    className: "bk-arrow bk-arrow--" + dir,
    onClick: onClick,
    disabled: disabled,
    "aria-label": dir === "prev" ? "Previous page" : "Next page"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, dir === "prev" ? /*#__PURE__*/React.createElement("polyline", {
    points: "15 18 9 12 15 6"
  }) : /*#__PURE__*/React.createElement("polyline", {
    points: "9 18 15 12 9 6"
  })));
}
function Caret(d) {
  return /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, d === "prev" ? /*#__PURE__*/React.createElement("polyline", {
    points: "15 18 9 12 15 6"
  }) : /*#__PURE__*/React.createElement("polyline", {
    points: "9 18 15 12 9 6"
  }));
}
function App() {
  const t = TWEAK_DEFAULTS;
  const setTweak = function () {};
  const mq = "(max-width: 1024px)";
  const [mobile, setMobile] = useState(() => window.matchMedia(mq).matches);

  // ---- location in the IA tree: which deck, which spread index ----
  const readLoc = () => {
    // a shared link (#deck-i) outranks the reader's saved place
    try {
      const h = /^#(spine|cases|patterns)-(\d+)$/.exec(window.location.hash || "");
      if (h) return { deck: h[1], i: Math.max(0, parseInt(h[2], 10) || 0) };
    } catch (e) {}
    try {
      const s = JSON.parse(localStorage.getItem("bk-loc"));
      if (s && typeof s.i === "number" && (s.deck === "spine" || s.deck === "cases" || s.deck === "patterns")) return { deck: s.deck, i: Math.max(0, Math.floor(s.i)) };
    } catch (e) {}
    return {
      deck: "spine",
      i: 0
    };
  };
  const [loc, setLoc] = useState(readLoc);
  const [anim, setAnim] = useState(null); // lateral flip {dir, from, to}
  const [zoom, setZoom] = useState({
    key: 0,
    dir: null
  }); // depth change transition
  const [mLeaf, setMLeaf] = useState(0); // mobile flat-page index
  const [mDir, setMDir] = useState(1);
  const [scale, setScale] = useState(1);
  const [menu, setMenu] = useState(false);
  // ---- opening ritual: closed book that clicks open (plays once) ----
  const readOpened = () => {
    try {
      // arriving via a shared deep link skips the cover ritual
      if (/^#(spine|cases|patterns)-\d+$/.test(window.location.hash || "") && window.location.hash !== "#spine-0") return true;
      return localStorage.getItem("bk-opened") === "1";
    } catch (e) {
      return false;
    }
  };
  const [opened, setOpened] = useState(readOpened); // ritual already played?
  const [opening, setOpening] = useState(false); // cover currently swinging open
  const animating = useRef(false);
  const touchRef = useRef(null); // swipe tracking for mobile
  const locRef = useRef(loc);
  locRef.current = loc;
  const mobileRef = useRef(mobile);
  mobileRef.current = mobile;
  const mLeafRef = useRef(mLeaf);
  mLeafRef.current = mLeaf;
  const menuRef = useRef(menu);
  menuRef.current = menu;
  const bookRef = useRef(null);
  const zoomCount = useRef(0);
  const reduce = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // ---- analytics (added 2026-08-01: the book previously had none at all) ----
  // maxSpineRef tracks the deepest SPINE spread reached this visit, independent of the reader
  // wandering into a section deck and back — "how far into the book did they get" should not
  // reset just because they detoured through the case-study section.
  const maxSpineRef = useRef(0);
  const openedAtRef = useRef(Date.now());
  const lastFiredRef = useRef(null); // dedupe: persist() can be called with an unchanged loc
  const track = (name, params) => {
    try {
      if (typeof gtag === "function") gtag("event", name, params || {});
    } catch (e) {}
  };
  const persist = l => {
    localStorage.setItem("bk-loc", JSON.stringify(l));
    try {
      // every spread gets a shareable URL; the cover keeps a clean one
      const h = l.deck === "spine" && l.i === 0 ? window.location.pathname + window.location.search : "#" + l.deck + "-" + l.i;
      window.history.replaceState(null, "", h);
    } catch (e) {}
    try {
      var b = bookRef.current, lbl = "";
      if (b) lbl = l.deck === "spine" ? (b.spine[l.i] && b.spine[l.i].runheadR) || "Cover" : (b.sections[l.deck] && b.sections[l.deck].items[l.i] && b.sections[l.deck].items[l.i].crumb) || "";
      var live = document.getElementById("bk-live");
      if (live && lbl) live.textContent = lbl;
      var key = l.deck + "-" + l.i;
      if (b && key !== lastFiredRef.current) {
        lastFiredRef.current = key;
        if (l.deck === "spine") maxSpineRef.current = Math.max(maxSpineRef.current, l.i);
        var spineTotal = b.spine ? b.spine.length : 0;
        track("book_navigate", {
          deck: l.deck,
          spread: l.i,
          label: lbl,
          spine_progress_pct: spineTotal ? Math.round(maxSpineRef.current / (spineTotal - 1) * 100) : 0
        });
      }
    } catch (e) {}
  };

  // ---- deck helpers (read the fresh book from a ref) ----
  const deckArr = d => d === "spine" ? bookRef.current.spine : bookRef.current.sections[d].items;
  const hasCover = d => d === "spine";
  const firstPageOf = (d, i) => hasCover(d) ? i === 0 ? 0 : 2 * i - 1 : i * 2;
  const spreadOfPage = (d, p) => hasCover(d) ? p === 0 ? 0 : Math.ceil(p / 2) : Math.floor(p / 2);
  const flatten = d => {
    const out = [];
    deckArr(d).forEach(sp => {
      if (sp.kind === "cover") out.push({
        cover: sp.cover,
        chapter: "Cover"
      });else {
        out.push({
          content: sp.left,
          chapter: sp.runheadR,
          folio: sp.folioL,
          crumb: sp.crumb,
          idxLabel: sp.idxLabel
        });
        out.push({
          content: sp.right,
          chapter: sp.runheadR,
          folio: sp.folioR,
          crumb: sp.crumb,
          idxLabel: sp.idxLabel
        });
      }
    });
    return out;
  };
  useEffect(() => {
    const m = window.matchMedia(mq);
    const on = e => setMobile(e.matches);
    m.addEventListener ? m.addEventListener("change", on) : m.addListener(on);
    return () => {
      m.removeEventListener ? m.removeEventListener("change", on) : m.removeListener(on);
    };
  }, []);

  // restore mobile page from saved spread on mount
  useEffect(() => {
    setMLeaf(firstPageOf(locRef.current.deck, locRef.current.i));
  }, []);

  // ---- analytics: one view event on mount, one depth beacon on the way out ----
  useEffect(() => {
    const l = locRef.current;
    maxSpineRef.current = l.deck === "spine" ? l.i : 0;
    track("book_view", {
      entry_deck: l.deck,
      entry_spread: l.i,
      entry_via: window.location.hash ? "deep_link" : "cover"
    });
    const sendDepth = () => {
      try {
        var b = bookRef.current;
        var spineTotal = b && b.spine ? b.spine.length : 0;
        // gtag('config', ..., {transport_type:'beacon'}) makes this fire-and-forget on unload —
        // regular fetch/XHR calls get cancelled by the browser mid-navigation, which is exactly
        // when this event matters most.
        track("book_depth", {
          max_spread: maxSpineRef.current,
          spine_total: spineTotal,
          spine_progress_pct: spineTotal ? Math.round(maxSpineRef.current / (spineTotal - 1) * 100) : 0,
          seconds: Math.round((Date.now() - openedAtRef.current) / 1000)
        });
      } catch (e) {}
    };
    const onVis = () => {
      if (document.visibilityState === "hidden") sendDepth();
    };
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("pagehide", sendDepth);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("pagehide", sendDepth);
    };
  }, []);

  // ---- depth change: zoom into / out of a section ----
  const changeLevel = (nl, dir) => {
    animating.current = true;
    zoomCount.current += 1;
    setAnim(null);
    setZoom({
      key: zoomCount.current,
      dir
    });
    setLoc(nl);
    persist(nl);
    setMLeaf(firstPageOf(nl.deck, nl.i));
    setTimeout(() => {
      animating.current = false;
    }, 440);
  };
  const enter = useCallback((key, idx) => {
    if (animating.current) return;
    changeLevel({
      deck: key,
      i: idx || 0
    }, "in");
  }, []);
  const exitSection = useCallback(() => {
    const l = locRef.current;
    if (l.deck === "spine") return;
    const parent = bookRef.current.sections[l.deck].parent;
    changeLevel({
      deck: "spine",
      i: parent
    }, "out");
  }, []);

  const openRitualRef = useRef(null); // points at the latest openRitual; lets goIndex route cover-opens through the swing without a definition-order/stale-closure trap
  // ---- lateral flip within the current deck (desktop) ----
  const goIndex = useCallback(target => {
    if (animating.current) return;
    const l = locRef.current;
    const arr = deckArr(l.deck);
    if (target < 0 || target >= arr.length) {
      // past an edge of a section → surface back up
      if (l.deck !== "spine") exitSection();
      return;
    }
    if (target === l.i) return;
    // opening from the cover: route EVERY forward affordance (right arrow, → key,
    // the "Open" button) through the same cover swing that clicking the cover body plays.
    // Without this they hit the instant-swap branch below and skip the flip entirely.
    if (l.deck === "spine" && l.i === 0 && target === 1 && !mobileRef.current && !reduce() && openRitualRef.current) {
      openRitualRef.current();
      return;
    }
    const coverInvolved = l.deck === "spine" && (l.i === 0 || target === 0);
    if (coverInvolved || reduce()) {
      animating.current = true;
      const nl = {
        deck: l.deck,
        i: target
      };
      setLoc(nl);
      persist(nl);
      // On mobile the visible flat page is driven by mLeaf, not loc — this branch updated loc/the
      // URL hash but never mLeaf, so tapping "Open" on the cover silently changed the hash while the
      // screen kept showing the cover. Every real tap looked like nothing happened (2026-08-01,
      // found by Playwright: locator.click() succeeded, hash advanced, but .bk-m-page kept
      // rendering .bk-m-page--cover). changeLevel already does this correctly for section
      // enter/exit; this was the one caller of the instant-jump path that didn't.
      if (mobileRef.current) {
        setMDir(target > l.i ? 1 : -1);
        setMLeaf(firstPageOf(nl.deck, nl.i));
      }
      setTimeout(() => {
        animating.current = false;
      }, 280);
      return;
    }
    animating.current = true;
    setAnim({
      dir: target > l.i ? "next" : "prev",
      from: Math.min(Math.max(l.i, 0), arr.length - 1),
      to: target
    });
    setTimeout(() => {
      const nl = {
        deck: l.deck,
        i: target
      };
      setLoc(nl);
      persist(nl);
      setAnim(null);
      animating.current = false;
    }, 840);
  }, [exitSection]);

  // jump within the spine (cover button + contents); exits a section first if needed
  const go = useCallback(i => {
    const l = locRef.current;
    if (l.deck === "spine") goIndex(i);else changeLevel({
      deck: "spine",
      i
    }, "out");
  }, [goIndex]);

  // unified quick-jump used by the Chapters menu (desktop + mobile) + Home
  const jumpTo = useCallback(i => {
    if (animating.current) return;
    if (locRef.current.deck !== "spine") {
      changeLevel({
        deck: "spine",
        i
      }, "out");
      return;
    }
    if (mobileRef.current) {
      const nl = {
        deck: "spine",
        i
      };
      setLoc(nl);
      persist(nl);
      setMDir(1);
      setMLeaf(firstPageOf("spine", i));
      return;
    }
    goIndex(i);
  }, [goIndex]);

  // ---- opening ritual: swing the cover open on its left hinge, once ----
  const openRitual = useCallback(() => {
    if (animating.current || opening) return;
    try {
      localStorage.setItem("bk-opened", "1");
    } catch (e) {}
    setOpened(true);
    if (reduce()) {
      // reduced motion: skip the animation, go straight to the first spread
      go(1);
      return;
    }
    animating.current = true;
    // Clean lift + reveal: mount the first spread IMMEDIATELY (so there is a real page
    // underneath — no empty flash, no hard blink), then let the cover overlay fade + lift
    // away over it while the spread fades in. `opening` keeps the overlay mounted for the
    // dissolve; the width change (cover 620 → spread 1180) is hidden inside the cross-fade.
    const nl = {
      deck: "spine",
      i: 1
    };
    setLoc(nl);
    persist(nl);
    setMLeaf(firstPageOf("spine", 1));
    setOpening(true);
    setTimeout(() => {
      setOpening(false);
      animating.current = false;
    }, 520);
  }, [opening, go]);
  openRitualRef.current = openRitual; // keep the ref current so goIndex always calls the live handler

  // ---- mobile paging ----
  const stepMobile = useCallback(dir => {
    if (animating.current) return;
    const l = locRef.current;
    const flat = flatten(l.deck);
    const np = mLeafRef.current + dir;
    if (np < 0 || np >= flat.length) {
      if (l.deck !== "spine") exitSection();
      return;
    }
    setMDir(dir);
    setMLeaf(np);
    const nl = {
      deck: l.deck,
      i: spreadOfPage(l.deck, np)
    };
    setLoc(nl);
    persist(nl);
  }, [exitSection]);
  useEffect(() => {
    const onKey = e => {
      if (e.key === "Escape") {
        if (menuRef.current) {
          setMenu(false);
          return;
        }
        exitSection();
        return;
      }
      const fwd = e.key === "ArrowRight",
        back = e.key === "ArrowLeft";
      if (!fwd && !back) return;
      if (mobileRef.current) stepMobile(fwd ? 1 : -1);else goIndex(locRef.current.i + (fwd ? 1 : -1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goIndex, stepMobile, exitSection]);

  // in-book deep links: a hash change navigates instead of dying silently
  useEffect(() => {
    const onHash = () => {
      const m = /^#(spine|cases|patterns)-(\d+)$/.exec(window.location.hash || "");
      if (!m) return;
      const nl = { deck: m[1], i: Math.max(0, parseInt(m[2], 10) || 0) };
      const cur = locRef.current;
      if (nl.deck === cur.deck && nl.i === cur.i) return;
      setOpened(true);
      if (animating.current) return;
      if (nl.deck === "spine") {
        if (cur.deck !== "spine") changeLevel(nl, "out");
        else if (mobileRef.current) { setLoc(nl); persist(nl); setMDir(1); setMLeaf(firstPageOf("spine", nl.i)); }
        else goIndex(nl.i);
      } else {
        changeLevel(nl, "in");
      }
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [goIndex]);
  useLayoutEffect(() => {
    if (mobile) return;
    const fit = () => {
      const l = locRef.current;
      const isCover = l.deck === "spine" && l.i === 0;
      const w = isCover ? COVER_W : SPREAD_W;
      let s = Math.min((window.innerWidth - 72) / w, (window.innerHeight - 72) / COVER_H, 1.2);
      if (l.deck !== "spine") s *= 0.96; // sit a touch smaller a level down
      setScale(s > 0.2 ? s : 0.3);
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [mobile, loc, anim]);
  const accentDeep = DEEP[t.accent] || t.accent;
  const pr = PAIRINGS[t.pairing] || PAIRINGS["Newsreader · Spectral"];
  const wrapVars = {
    "--bk-ember": t.accent,
    "--bk-ember-deep": accentDeep,
    "--bk-ribbon": t.accent,
    "--bk-display": pr.d,
    "--bk-serif": pr.s,
    "--bk-paper": mix("#F1EEE6", "#F7E7C6", t.warmth / 100),
    "--bk-paper-2": mix("#ECE8DC", "#F1DFBE", t.warmth / 100),
    "--bk-pad": {
      compact: "42px",
      regular: "54px",
      comfy: "66px"
    }[t.density] || "54px"
  };
  const book = buildBook({
    headline: t.headline,
    go,
    jumpTo,
    enter
  });
  bookRef.current = book;
  const inSection = loc.deck !== "spine";
  const section = inSection ? book.sections[loc.deck] : null;
  const deck = inSection ? section.items : book.spine;
  const curSpread = Math.min(Math.max(loc.i, 0), deck.length - 1);

  // a single desktop page face (used by base spread + flipping leaf)
  const PageFace = (sp, side) => !sp ? /*#__PURE__*/React.createElement("div", {
    className: "bk-page bk-page--" + side
  }) : /*#__PURE__*/React.createElement("div", {
    className: "bk-page bk-page--" + side
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-runhead"
  }, side === "l" ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, sp.runheadL || VERSO), /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: 0.6
    }
  }, "")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: 0
    }
  }, "\xB7"), /*#__PURE__*/React.createElement("span", null, sp.runheadR))), side === "l" ? sp.left : sp.right, /*#__PURE__*/React.createElement("div", {
    className: "bk-folio"
  }, side === "l" ? sp.folioL : sp.folioR));
  function renderDesktop() {
    const sp = deck[curSpread];
    // opening ritual is live only on the cover, before it has played (or while
    // it is mid-swing), on desktop. `opening` keeps it mounted during the swing
    // even though `opened` flips to true the instant the click is registered.
    const ritual = !inSection && curSpread === 0 && !anim; // cover is always the interactive closed-book, so it swings on every click (not just first visit)
    let inner;
    if (!inSection && curSpread === 0 && !anim) {
      if (ritual) {
        // closed book: a fixed-size sizer keeps .bk-book at cover dimensions
        // while the cover overlays it (position:absolute) and swings open.
        inner = /*#__PURE__*/React.createElement("div", {
          className: "bk-cover-sizer",
          style: {
            position: "relative",
            width: COVER_W,
            height: COVER_H,
            cursor: "pointer"
          },
          // capture phase: run the ritual before the cover's own "Open the book"
          // button fires go(1), and stop that bubble so the swing always plays
          onClickCapture: e => {
            e.stopPropagation();
            openRitual();
          }
        }, book.spine[0].cover, /*#__PURE__*/React.createElement("div", {
          className: "bk-opencue"
        }, "Click to open"));
      } else {
        inner = book.spine[0].cover;
      }
    } else if (anim) {
      const from = deck[anim.from],
        to = deck[anim.to];
      inner = /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
        className: "bk-ribbon"
      }), /*#__PURE__*/React.createElement("div", {
        className: "bk-spread",
        style: {
          width: SPREAD_W,
          height: SPREAD_H
        }
      }, anim.dir === "next" ? PageFace(from, "l") : PageFace(to, "l"), anim.dir === "next" ? PageFace(to, "r") : PageFace(from, "r"), /*#__PURE__*/React.createElement("div", {
        className: "bk-leaf bk-leaf--" + anim.dir
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-leaf__face bk-leaf__front"
      }, PageFace(from, anim.dir === "next" ? "r" : "l"), /*#__PURE__*/React.createElement("div", {
        className: "bk-leaf__gloss"
      })), /*#__PURE__*/React.createElement("div", {
        className: "bk-leaf__face bk-leaf__back"
      }, PageFace(to, anim.dir === "next" ? "l" : "r"), /*#__PURE__*/React.createElement("div", {
        className: "bk-leaf__gloss"
      })))));
    } else {
      inner = /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
        className: "bk-ribbon"
      }), /*#__PURE__*/React.createElement("div", {
        className: "bk-spread",
        style: {
          width: SPREAD_W,
          height: SPREAD_H
        },
        key: loc.deck + ":" + curSpread
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-page bk-page--l"
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-runhead"
      }, /*#__PURE__*/React.createElement("span", null, sp.runheadL || VERSO), /*#__PURE__*/React.createElement("span", {
        style: {
          opacity: 0.6
        }
      }, "")), sp.left, /*#__PURE__*/React.createElement("div", {
        className: "bk-folio"
      }, sp.folioL), /*#__PURE__*/React.createElement("div", {
        className: "bk-corner bk-corner--prev",
        onClick: () => goIndex(curSpread - 1),
        title: "Previous"
      })), /*#__PURE__*/React.createElement("div", {
        className: "bk-page bk-page--r"
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-runhead"
      }, /*#__PURE__*/React.createElement("span", {
        style: {
          opacity: 0
        }
      }, "\xB7"), /*#__PURE__*/React.createElement("span", null, sp.runheadR)), sp.right, /*#__PURE__*/React.createElement("div", {
        className: "bk-folio"
      }, sp.folioR), /*#__PURE__*/React.createElement("div", {
        className: "bk-corner bk-corner--next",
        onClick: () => goIndex(curSpread + 1),
        title: "Next"
      }))));
    }
    const prevDisabled = !inSection && curSpread === 0;
    const nextDisabled = !inSection && curSpread === book.spine.length - 1;

    // ---- thumb-index tabs (right edge): FRONT / WORK / GUIDE / END ----
    // i = spine index of each region's hub. Hidden on the cover.
    const TABS = [{
      label: "Front",
      color: "var(--bk-ink)",
      i: 1
    }, {
      label: "Work",
      color: "var(--bk-ember)",
      i: 4
    }, {
      label: "Guide",
      color: "var(--bk-pine)",
      i: 5
    }, {
      label: "Contact",
      color: "var(--bk-ochre)",
      i: 8
    }];
    // which tab reads as active: in a section, light its hub; else the spine spread
    const activeTab = inSection ? loc.deck === "cases" ? 4 : loc.deck === "patterns" ? 5 : -1 : curSpread;
    const onCover = !inSection && curSpread === 0;
    const thumbTabs = onCover ? null : /*#__PURE__*/React.createElement("div", {
      className: "bk-thumbtabs"
    }, TABS.map(tb => /*#__PURE__*/React.createElement("button", {
      className: "bk-tab" + (activeTab === tb.i ? " on" : ""),
      key: tb.i,
      style: {
        "--tab": tb.color
      },
      tabIndex: 0,
      "aria-label": "Jump to " + tb.label,
      onClick: () => jumpTo(tb.i),
      onKeyDown: e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          jumpTo(tb.i);
        }
      }
    }, tb.label)));

    return /*#__PURE__*/React.createElement("div", {
      className: "bk-stage" + (inSection ? " bk-stage--deep" : "")
    }, !inSection && /*#__PURE__*/React.createElement("a", {
      href: "../index.html",
      className: "bk-logo-mark",
      "aria-label": "Arpit Maheshwari — back to portfolio"
    }, /*#__PURE__*/React.createElement("img", {
      src: "../assets/logo.svg",
      alt: "AM",
      width: 32, height: 32,
      style: { display: "block" }
    })), inSection && /*#__PURE__*/React.createElement("button", {
      className: "bk-back",
      onClick: exitSection
    }, /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      style: {
        width: 14,
        height: 14
      }
    }, /*#__PURE__*/React.createElement("polyline", {
      points: "15 18 9 12 15 6"
    })), section.label), inSection && /*#__PURE__*/React.createElement("div", {
      className: "bk-crumb"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: exitSection
    }, section.label), /*#__PURE__*/React.createElement("span", {
      className: "bk-crumb__sep"
    }, "\u27E9"), /*#__PURE__*/React.createElement("span", {
      className: "bk-crumb__cur"
    }, section.kind, " \xB7 ", sp.crumb)), /*#__PURE__*/React.createElement("div", {
      className: "bk-zoomer",
      key: zoom.key,
      "data-z": zoom.dir || undefined
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-book" + (inSection ? " bk-book--deep" : "") + (ritual ? " bk-openbook" : "") + (opening ? " is-opening" : ""),
      style: {
        transform: `scale(${scale})`
      }
    }, inner, opening && /*#__PURE__*/React.createElement("div", {
      className: "bk-coverlift",
      "aria-hidden": "true"
    }, book.spine[0].cover), thumbTabs)), /*#__PURE__*/React.createElement("button", {
      className: "bk-menu-btn",
      onClick: () => setMenu(true),
      "aria-label": "Open chapter menu"
    }, /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round"
    }, /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "7",
      x2: "20",
      y2: "7"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "12",
      x2: "20",
      y2: "12"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "17",
      x2: "14",
      y2: "17"
    })), "Chapters"), /*#__PURE__*/React.createElement(Arrow, {
      dir: "prev",
      onClick: () => goIndex(curSpread - 1),
      disabled: prevDisabled
    }), /*#__PURE__*/React.createElement(Arrow, {
      dir: "next",
      onClick: () => goIndex(curSpread + 1),
      disabled: nextDisabled
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-progress"
    }, inSection ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, sp.crumb, " \xB7 ", sp.idxLabel), /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__dots"
    }, deck.map((_, i) => /*#__PURE__*/React.createElement("button", {
      className: "bk-progress__dot" + (i === curSpread ? " on" : ""),
      key: i,
      "aria-label": "Go to spread " + (i + 1),
      "aria-current": i === curSpread ? "true" : undefined,
      onClick: () => goIndex(i),
      onKeyDown: e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          goIndex(i);
        }
      }
    }))), /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__esc",
      onClick: exitSection
    }, "esc \u21A9 ", section.label)) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, curSpread === 0 ? "Cover" : sp.runheadR), /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__dots"
    }, book.spine.map((_, i) => /*#__PURE__*/React.createElement("button", {
      className: "bk-progress__dot" + (i === curSpread ? " on" : ""),
      key: i,
      "aria-label": "Go to spread " + (i + 1),
      "aria-current": i === curSpread ? "true" : undefined,
      onClick: () => goIndex(i),
      onKeyDown: e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          goIndex(i);
        }
      }
    }))), /*#__PURE__*/React.createElement("span", null, curSpread === 0 ? "" : sp.folioL === "\u2014" ? "\u2014 \u00b7 " + sp.folioR : "pp. " + sp.folioL + "\u2013" + sp.folioR))));
  }
  function renderMobile() {
    const flat = flatten(loc.deck);
    const idx = Math.min(Math.max(mLeaf, 0), flat.length - 1);
    const pg = flat[idx];
    const isCover = !!pg.cover;
    return /*#__PURE__*/React.createElement("div", {
      className: "bk-mobile" + (inSection ? " bk-mobile--deep" : "")
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-m-top"
    }, inSection ? /*#__PURE__*/React.createElement("button", {
      className: "bk-m-back",
      onClick: exitSection
    }, Caret("prev"), " ", section.label) : /*#__PURE__*/React.createElement("div", {
      style: { display: "flex", alignItems: "center", gap: "10px" }
    }, /*#__PURE__*/React.createElement("img", {
      src: "../assets/logo.svg",
      alt: "",
      "aria-hidden": "true",
      width: 28, height: 28,
      style: { display: "block" }
    }), /*#__PURE__*/React.createElement("span", {
      className: "name"
    }, "ARPIT MAHESHWARI")), /*#__PURE__*/React.createElement("button", {
      className: "bk-m-jump",
      onClick: () => setMenu(true),
      "aria-label": "Open chapter menu"
    }, /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round"
    }, /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "7",
      x2: "20",
      y2: "7"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "12",
      x2: "20",
      y2: "12"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "4",
      y1: "17",
      x2: "14",
      y2: "17"
    })), "Chapters")), /*#__PURE__*/React.createElement("div", {
      className: "bk-m-stage",
      onTouchStart: e => { touchRef.current = e.touches[0].clientX; },
      onTouchEnd: e => {
        if (touchRef.current === null) return;
        const diff = touchRef.current - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 30) { if (diff > 0) stepMobile(1); else stepMobile(-1); }
        touchRef.current = null;
      }
    }, /*#__PURE__*/React.createElement("div", { className: "bk-m-underneath" }), /*#__PURE__*/React.createElement("div", {
      className: "bk-m-page" + (isCover ? " bk-m-page--cover" : ""),
      key: loc.deck + ":" + idx,
      style: {
        "--m-rot":         mDir > 0 ? "90deg" : "-90deg",
        "--m-origin":      mDir > 0 ? "100% 50%" : "0% 50%",
        "--m-shadow-grad": mDir > 0
          ? "linear-gradient(to right, rgba(0,0,0,0.32) 0%, transparent 50%)"
          : "linear-gradient(to left,  rgba(0,0,0,0.32) 0%, transparent 50%)"
      }
    }, isCover ? pg.cover : /*#__PURE__*/React.createElement(React.Fragment, null, pg.content, pg.folio && pg.folio !== "\u2014" ? /*#__PURE__*/React.createElement("div", {
      className: "bk-m-folio"
    }, "\xB7 ", pg.crumb ? pg.crumb + " " + pg.folio : pg.folio, " \xB7") : null)), /*#__PURE__*/React.createElement("div", {
      className: "bk-m-nav"
    }, /*#__PURE__*/React.createElement("button", {
      className: "bk-m-btn",
      onClick: () => stepMobile(-1),
      disabled: !inSection && idx === 0,
      "aria-label": "previous page"
    }, Caret("prev")), /*#__PURE__*/React.createElement("span", {
      className: "bk-m-label"
    }, inSection ? pg.crumb + " · " + pg.idxLabel : isCover ? /*#__PURE__*/React.createElement(React.Fragment, null, "Cover · tap to begin ", Icon({ name: "arrow-right", cls: "bk-icon--sm" })) : pg.chapter), /*#__PURE__*/React.createElement("button", {
      className: "bk-m-btn",
      onClick: () => stepMobile(1),
      disabled: !inSection && idx === flat.length - 1,
      "aria-label": "next page"
    }, Caret("next")))));
  }
  return /*#__PURE__*/React.createElement("div", {
    style: wrapVars
  }, mobile ? renderMobile() : renderDesktop(), menu && /*#__PURE__*/React.createElement(ChapterMenu, {
    spine: book.spine,
    onPick: i => {
      setMenu(false);
      jumpTo(i);
    },
    onClose: () => setMenu(false)
  }));
}
ReactDOM.createRoot(document.getElementById("app")).render(/*#__PURE__*/React.createElement(App, null));
