/* book-content.jsx — content model + spread renderers for A Working Book.
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
  title: "PTC University",
  metric: "$1M/yr",
  desc: "Consolidated seven overlapping platforms into one learning system across eleven languages. The redesign was easy; the political case for killing six products was the work."
}, {
  tag: "FinTech · NDA",
  title: "AI-Assisted Due Diligence",
  metric: "−60%",
  desc: "Refused to ship the model without an \u201Cexplain this score\u201D surface. PE analysts went from ignoring it to leading with it."
}, {
  tag: "AdTech · NDA",
  title: "Programmatic Advertising",
  metric: "15\u219263%",
  desc: "Designed confidence into the recommendation before the recommendation. Media buyers finally acted on the algorithm."
}, {
  tag: "Telecom · NDA",
  title: "O2 Priority Billing",
  metric: "−40%",
  desc: "Bills were correct and unreadable. Three decisions cut \u201Cexplain my bill\u201D tickets by two-fifths."
}, {
  tag: "Org Design · Non-NDA",
  title: "OrgOS",
  metric: "120",
  desc: "Eight modules that let a 120-person team self-organise. Zero managers; transparency as the coordination layer."
}];
const PRINCIPLES = [{
  h: "I design for business outcomes, not just user friction.",
  p: "I read the evals and sit in on customer calls before I open a design file. I shape what gets measured, then I ship the front-end."
}, {
  h: "I design the wrong-answer screen first.",
  p: "If I don't know how the system fails gracefully, the happy path doesn't matter. Trust is built in the error states."
}, {
  h: "The org chart is the hardest wireframe.",
  p: "Most UX problems are actually just symptoms of misaligned internal teams. I design for the organization before I design the interface."
}];
const PATTERNS = [{
  k: "gauge",
  h: "Confidence scores",
  p: "How much certainty to show, and the threshold at which a number earns the right to drive a business decision."
}, {
  k: "alert",
  h: "Failure states",
  p: "The designed moment the model is wrong — preventing user abandonment by handling errors gracefully."
}, {
  k: "branch",
  h: "Explainability",
  p: "\u201CWhy this?\u201D surfaces that turn a black-box output into a reviewable, business-justified argument."
}, {
  k: "loop",
  h: "Human-in-the-loop",
  p: "Where the person overrides the system — creating a workflow that scales without increasing overhead."
}];
const WRITING = [{
  d: "2026 · Essay",
  h: "The trust layer is the product",
  p: "Why the surface where users decide to act on a model matters more than the model."
}, {
  d: "2025 · Field note",
  h: "I argued for three options and lost",
  p: "The A/B test that changed how I design every recommendation."
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
const STATUS = ["Available · 4-wk notice", "Founding / Staff / Director", "Remote · GMT+5:30"];

/* ---- CURRICULUM VITAE (the printable appendix) ---- */
const CV_SKILLS = ["Design leadership", "AI / ML UX", "Design systems", "Research & evals", "Prototyping", "Org design"];
const CV_EXP = [{
  yr: "2021\u2014",
  role: "Principal Product Designer",
  org: "Independent / fractional \u00B7 AI & data products (under NDA)"
}, {
  yr: "2018\u201321",
  role: "Lead Product Designer",
  org: "PTC University \u00B7 EdTech learning platform"
}, {
  yr: "2015\u201318",
  role: "Senior Product Designer",
  org: "FinTech & AdTech platforms (NDA)"
}, {
  yr: "2012\u201315",
  role: "Product Designer",
  org: "Telecom (O2 Priority) & early-stage SaaS"
}, {
  yr: "2009\u201312",
  role: "Designer",
  org: "Editorial & print production"
}];
const CV_EDU = [{
  yr: "\u2014",
  role: "B.Des, Communication Design",
  org: "India"
}, {
  yr: "\u2014",
  role: "Selected writing & talks",
  org: "See Chapter IV \u00B7 Notes & Writing"
}];

/* ---- CASE STUDIES (the two non-NDA projects, in full) ------ */
const CASES = {
  ptc: {
    key: "ptc",
    no: "01",
    tag: "EdTech · Non-NDA",
    title: "PTC\u00A0University",
    standfirst: "Seven overlapping learning platforms, eleven languages, one furious procurement line. The redesign was the easy part.",
    meta: [["Role", "Lead Product Designer"], ["Span", "14 months · two squads"], ["Surface", "Web LMS · 11 languages"], ["Result", "Shipped · in production"]],
    context: "PTC had grown its training into seven separate portals — product certifications, partner enablement, internal onboarding — each with its own login, its own taxonomy, its own translation pipeline. Learners bounced between them; eleven localisation teams duplicated the same work. The brief on my desk read \u201Credesign the LMS.\u201D The real problem was that there were seven of them.",
    fig1: {
      no: "1.1",
      label: "before — seven disconnected portals, eleven sign-in screens"
    },
    tension: "Every portal had a VP, a budget line, and a reason why it was 'special'. Consolidation meant telling six executives their product was now a tab. The real design work was a political case made in the language of risk and P&L—I couldn't draw my way past the org chart.",
    note1: "the org chart was the real wireframe",
    decisionLede: "Three decisions did the load-bearing work:",
    moves: [{
      h: "One data model before one UI",
      p: "I rebuilt the content model first — a single skill graph every portal mapped onto — so the merge became a data migration, not a turf war over screens."
    }, {
      h: "Localisation as a default state",
      p: "Designed the eleven-language experience as the baseline, not an afterthought, so no region could argue it needed its own fork."
    }, {
      h: "A switch-off ladder",
      p: "Sequenced the seven shutdowns so each VP watched their users land softly in the new system before their portal went dark."
    }],
    fig2: {
      no: "1.2",
      label: "after — one skill graph, one shell, eleven languages"
    },
    outcome: [{
      v: "$1M",
      l: "Saved per year — licensing + localisation"
    }, {
      v: "7\u21921",
      l: "Platforms consolidated"
    }, {
      v: "11",
      l: "Languages, one pipeline"
    }, {
      v: "4 days",
      l: "Content publish, down from ~3 weeks"
    }],
    quote: {
      t: "The redesign took a quarter. The case for deleting six products took a year — and that was the actual design work.",
      cite: "— PTC University, project note"
    },
    note2: "killed six products. proudest deletion of my career."
  },
  orgos: {
    key: "orgos",
    no: "02",
    tag: "Org Design · Non-NDA",
    title: "OrgOS",
    standfirst: "A 120-person company with zero managers. The job: make a flat org legible without quietly installing a hierarchy to do it.",
    meta: [["Role", "Founding Designer"], ["Span", "Ongoing · 8 modules"], ["Surface", "Internal web app"], ["Result", "Live across the org"]],
    context: "A 120-person consultancy ran with no managers. Coordination happened in hallway conversations and a sprawl of spreadsheets — which works at forty people and snaps at a hundred. They wanted software that made the flat org legible, without the software smuggling a boss back in through the side door.",
    fig1: {
      no: "2.1",
      label: "before — coordination by spreadsheet + hallway conversation"
    },
    tension: "Every obvious feature carried a hierarchy inside it. Dashboards imply someone watching; approvals imply someone approving; assignments imply someone assigning. The real constraint was to build coordination tools that never curdled into control tools — to let transparency do the job a manager usually does, without anyone holding the authority a manager usually has.",
    note1: "every feature wanted to grow a boss",
    decisionLede: "I kept deleting features that worked. Three survived as the spine:",
    moves: [{
      h: "Read access is the feature",
      p: "Everything visible by default — who's on what, who's overloaded, what's stalled — so coordination came from information, not instruction."
    }, {
      h: "Commitments, not assignments",
      p: "People pull work and publish commitments in the open. The system tracks promises kept; it never hands out tasks."
    }, {
      h: "Eight modules, one grammar",
      p: "Staffing, comp, OKRs, onboarding all speak the same object model — so the org can recompose its own process without me in the room."
    }],
    fig2: {
      no: "2.2",
      label: "the eight modules sharing one object model"
    },
    outcome: [{
      v: "120",
      l: "People coordinating, self-serve"
    }, {
      v: "0",
      l: "Managers in the loop"
    }, {
      v: "8",
      l: "Modules, one shared grammar"
    }, {
      v: "100%",
      l: "Of the org, in production"
    }],
    quote: {
      t: "I kept deleting features that worked, because each one quietly reintroduced a boss.",
      cite: "— OrgOS, design log"
    },
    note2: "transparency as the coordination layer ♥"
  }
};

/* ---- NDA WALK-THROUGHS (the three under-NDA projects, redacted) ---- */
const NDA_CASES = [{
  no: "03",
  tag: "FinTech · NDA",
  title: "AI-Assisted Due Diligence",
  standfirst: "A risk model the analysts wouldn't touch \u2014 until it learned to show its work.",
  meta: [["Role", "Lead Product Designer"], ["Surface", "PE diligence platform"], ["Status", "Shipped \u00B7 under NDA"]],
  context: "Private-equity analysts had an AI that scored deal risk and an instinct to ignore it. A confident number with no account of itself is just another opinion \u2014 and theirs was better paid. The model was good; the trust was missing.",
  moves: [{
    h: "Explain before score",
    p: "Put the three documents that moved the number next to the number \u2014 before the verdict, not buried behind it."
  }, {
    h: "Design the decline",
    p: "Shipped a visible \u201CI'm not sure about this one\u201D state so the model could refuse to bluff."
  }, {
    h: "Disagreement on record",
    p: "Made \u201CI disagree\u201D a first-class, logged action that fed the next eval."
  }],
  plateNo: "3.1",
  plateCn: "explanation drawer \u2014 output traced to source documents",
  ledger: [{
    v: "\u221260%",
    l: "Time per diligence pass"
  }, {
    v: "3",
    l: "Sources behind every score"
  }, {
    v: "Lead",
    l: "Analysts now open with it"
  }],
  note: "trust = the model declining to bluff"
}, {
  no: "04",
  tag: "AdTech · NDA",
  title: "Programmatic Advertising",
  standfirst: "Media buyers ignored the algorithm until the algorithm remembered its own track record.",
  meta: [["Role", "Lead Product Designer"], ["Surface", "DSP recommendation UI"], ["Status", "Shipped \u00B7 under NDA"]],
  context: "A demand-side platform recommended bids no one acted on. The recommendation was confident and amnesiac \u2014 it never said how it had done last month, so buyers trusted their gut over the box.",
  moves: [{
    h: "Confidence with memory",
    p: "Sat each recommendation beside its own 30-day hit rate. Confidence that remembers gets acted on."
  }, {
    h: "Act / review / ignore",
    p: "Anchored every score to one of three actions, never a bare percentage."
  }, {
    h: "Override teaches",
    p: "A buyer's override visibly retrained next week's call \u2014 correcting felt like teaching, not rework."
  }],
  plateNo: "4.1",
  plateCn: "recommendation card + 30-day track record",
  ledger: [{
    v: "15\u219263%",
    l: "Recommendations acted on"
  }, {
    v: "30d",
    l: "Track record, always shown"
  }, {
    v: "1",
    l: "Scale, one meaning"
  }],
  note: "a score with a memory got acted on"
}, {
  no: "05",
  tag: "Telecom · NDA",
  title: "O2 Priority Billing",
  standfirst: "The bills were correct and unreadable. Three decisions cut \u201Cexplain my bill\u201D tickets by two-fifths.",
  meta: [["Role", "Senior Product Designer"], ["Surface", "Billing \u00B7 web + app"], ["Status", "Shipped \u00B7 under NDA"]],
  context: "Accurate bills that no one could parse generated the same support load as wrong ones. 'Why is my bill higher?' was the single largest call driver. The answer was on the screen, just buried.",
  moves: [{
    h: "Lead with the delta",
    p: "Answered 'why more than last month?' in plain text at the top, preempting the support call before the user even scrolled to the line-item table."
  }, {
    h: "Plain-language lines",
    p: "Rewrote charge labels in the words customers used, not the billing system's."
  }, {
    h: "One tap to the cause",
    p: "Every change traced to the event behind it \u2014 a roaming day, a plan change."
  }],
  plateNo: "5.1",
  plateCn: "bill summary \u2014 the delta, explained first",
  ledger: [{
    v: "\u221240%",
    l: "\u2018Explain my bill\u2019 tickets"
  }, {
    v: "#1",
    l: "Was the top call driver"
  }, {
    v: "2",
    l: "Surfaces, one model"
  }],
  note: "correct isn't the same as legible"
}];
const PATTERN_PAGES = {
  gauge: {
    no: "01",
    k: "gauge",
    h: "Confidence scores",
    principle: "A number people can act on \u2014 not just read.",
    def: "How much certainty to show, in what form, and the threshold at which a score has earned the right to drive a decision rather than merely decorate one.",
    note: "a percentage is a feeling until it's anchored to an action",
    dos: ["Anchor the score to an action — act, review, or ignore — not just a bare number.", "Show the score's own track record so people can calibrate their trust.", "Round to the precision you'd be willing to defend out loud."],
    donts: ["Render 87.3% when what you actually mean is \u201Cprobably.\u201D", "Let a high score auto-execute with no visible way to override.", "Reuse one confidence scale across decisions of wildly different stakes."],
    instTag: "AdTech · Programmatic",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "Media buyers ignored the recommendation until the score sat beside ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "what it had gotten right last month"), ". Confidence with a memory got acted on; confidence alone never did."),
    fig: {
      no: "3.1",
      label: "confidence chip + 30-day track record"
    }
  },
  alert: {
    no: "02",
    k: "alert",
    h: "Failure states",
    principle: "If you can't design the wrong answer, the feature isn't ready.",
    def: "The designed moment the model is wrong — how it admits it, what it offers instead, and how a miss costs trust slowly instead of all at once.",
    note: "I design the wrong-answer screen first now",
    dos: ["Design the wrong-answer screen before you design the happy path.", "Make recovery from a miss cheaper than the mistake itself.", "Say what the system doesn't know, plainly and early."],
    donts: ["Hide uncertainty behind a confident-looking default.", "File \u201Cwhat if it's wrong\u201D as an edge case to handle later.", "Apologise for an error without offering the next step."],
    instTag: "FinTech · Due Diligence",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "We shipped the ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "\u201CI'm not sure about this one\u201D"), " state first. Analysts trusted the confident answers more once they'd watched the model decline to bluff."),
    fig: {
      no: "3.2",
      label: "graceful low-confidence / model-declines state"
    }
  },
  branch: {
    no: "03",
    k: "branch",
    h: "Explainability",
    principle: "Turn a black-box output into a reviewable argument.",
    def: "The \u201Cwhy this?\u201D surface that lets a person inspect, challenge, and either endorse or reject the model's reasoning — the difference between obeying a score and owning a decision.",
    note: "an output you can argue with is an output you'll stand behind",
    dos: ["Show the two or three inputs that actually moved the result.", "Let the user trace from the output back to the evidence.", "Make \u201CI disagree\u201D a first-class, recorded action."],
    donts: ["Dump every feature weight on screen and call it transparency.", "Explain after the decision instead of before it.", "Mistake a tooltip for an account of the reasoning."],
    instTag: "FinTech · Due Diligence",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "Analysts went from ignoring the risk score to ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "leading their memos with it"), " \u2014 once \u201Cexplain this score\u201D surfaced the three documents behind the number."),
    fig: {
      no: "3.3",
      label: "explanation drawer — output traced to source documents"
    }
  },
  loop: {
    no: "04",
    k: "loop",
    h: "Human-in-the-loop",
    principle: "Override should feel like authorship, not babysitting.",
    def: "Where and how the person corrects, overrides, or teaches the system — designed so the human stays the author of the decision, not the janitor of the model's mistakes.",
    note: "correcting the model should feel like teaching, not cleanup",
    dos: ["Make the human's edit visibly improve the next result.", "Put the control where the decision happens, never buried in settings.", "Default to the human's last call when the stakes are high."],
    donts: ["Ask for approval on everything until approval means nothing.", "Treat corrections as exceptions instead of as training signal.", "Make overriding feel like a fight with the product."],
    instTag: "AdTech · Programmatic",
    inst: /*#__PURE__*/React.createElement(React.Fragment, null, "When a buyer's override visibly retrained the next week's recommendation, correcting the model ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "stopped feeling like rework"), " and started feeling like teaching."),
    fig: {
      no: "3.4",
      label: "override → feedback → next recommendation"
    }
  }
};
window.BOOK_META = {
  spine: 11
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
    fill: "none"
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
  label
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-figure"
  }, /*#__PURE__*/React.createElement("span", {
    className: "bk-figure__tag"
  }, "Fig. ", no), /*#__PURE__*/React.createElement("div", {
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
  wide
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "bk-plate" + (redacted ? " bk-plate--redacted" : "") + (wide ? " bk-plate--wide" : "")
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-plate__img"
  }, redacted ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
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
    }, c.note2))
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
      no: c.plateNo,
      cn: c.plateCn,
      ph: "Screens under NDA \u2014 full walk-through on request",
      redacted: true,
      wide: true
    })),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement(Beat, {
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
    }, c.note))
  };
}

/* ---- pattern spread builder -------------------------------- */
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
    }, "From the work \xB7 ", p.instTag), /*#__PURE__*/React.createElement("p", null, p.inst)), /*#__PURE__*/React.createElement(Figure, {
      no: p.fig.no,
      label: p.fig.label
    }))
  };
}

/* ---- contact form (own state) ------------------------------ */
function ContactForm() {
  const [email, setEmail] = React.useState("");
  const [sent, setSent] = React.useState(false);
  if (sent) return /*#__PURE__*/React.createElement("div", {
    className: "bk-ok"
  }, "Noted. Your five-minute teardown arrives within 48 hours.");
  return /*#__PURE__*/React.createElement("form", {
    className: "bk-form",
    onSubmit: e => {
      e.preventDefault();
      if (email.trim()) setSent(true);
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "email",
    required: true,
    placeholder: "you@company.com",
    value: email,
    onChange: e => setEmail(e.target.value)
  }), /*#__PURE__*/React.createElement("input", {
    type: "url",
    placeholder: "A link to your product (optional)"
  }), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    className: "bk-btn"
  }, "Request the teardown \u2192"));
}

/* ---- runheads ---------------------------------------------- */
const VERSO = "Arpit Maheshwari";
function buildBook(ctx) {
  const go = ctx.go; // jump within the spine
  const enter = ctx.enter; // open a section a level deeper: enter(key, idx)
  const TOC = [{
    n: "—",
    name: "About the Author",
    sub: "Who's writing, and why",
    pg: "p. ii",
    to: 2
  }, {
    n: "I",
    name: "Selected Work",
    sub: "Overview → five cases",
    pg: "p. 2",
    to: 3
  }, {
    n: "II",
    name: "How I Lead",
    sub: "Principles & one confession",
    pg: "p. 4",
    to: 4
  }, {
    n: "III",
    name: "A Field Guide to Trust",
    sub: "Overview → four patterns",
    pg: "p. 6",
    to: 5
  }, {
    n: "IV",
    name: "Notes & Writing",
    sub: "Essays, talks, field notes",
    pg: "p. 8",
    to: 6
  }, {
    n: "V",
    name: "Colophon & Contact",
    sub: "How this was made; write to me",
    pg: "p. 10",
    to: 7
  }, {
    n: "—",
    name: "Curriculum Vitæ",
    sub: "The printable appendix",
    pg: "p. 12",
    to: 8
  }];
  const ptcA = caseSpreadA(CASES.ptc),
    ptcB = caseSpreadB(CASES.ptc);
  const orgA = caseSpreadA(CASES.orgos),
    orgB = caseSpreadB(CASES.orgos);
  const ndaPages = NDA_CASES.map(c => caseWalk(c));
  const patPages = ["gauge", "alert", "branch", "loop"].map(k => patternSpread(PATTERN_PAGES[k]));

  /* ----- THE SPINE — seven spreads, the only linear flow ----- */
  const spine = [/* 0 · COVER */
  {
    kind: "cover",
    cover: /*#__PURE__*/React.createElement("div", {
      className: "bk-cover"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__imprint"
    }, "A Working Book \xB7 Vol. I \xB7 MMXXVI"), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__emblem"
    }, /*#__PURE__*/React.createElement(Emblem, null)), /*#__PURE__*/React.createElement("h1", {
      className: "bk-cover__title"
    }, "Arpit", /*#__PURE__*/React.createElement("br", null), "Maheshwari"), /*#__PURE__*/React.createElement("div", {
      className: "bk-cover__rule"
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-cover__sub"
    }, "Designing trust into AI & data products.", /*#__PURE__*/React.createElement("br", null), "Fifteen years, five industries, measured."), /*#__PURE__*/React.createElement("button", {
      className: "bk-cover__open",
      onClick: () => go(1)
    }, /*#__PURE__*/React.createElement("span", {
      className: "dot"
    }), " Open the book"))
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
    }, "A Working Book"), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        width: 70,
        height: 70,
        marginBottom: 22
      }
    }, /*#__PURE__*/React.createElement(Emblem, {
      stroke: "var(--bk-ember)"
    })), /*#__PURE__*/React.createElement("h1", {
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
    }, "Design leader for AI & data-intensive products. Frameworks public, products under NDA, outcomes measured."), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        fontSize: 13,
        color: "var(--bk-ink-faint)"
      }
    }, "First edition \xB7 set in Instrument Serif & Newsreader \xB7 Indore, India \xB7 MMXXVI")),
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
    }, TOC.map((tc, i) => /*#__PURE__*/React.createElement("div", {
      className: "bk-toc__item",
      key: i,
      onClick: () => go(tc.to)
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
    }, "turn pages across \u2192 open items to go deeper \u2197"))
  }, /* 2 · About the Author (front matter) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "About the Author",
    folioL: "ii",
    folioR: "iii",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "About the author"), /*#__PURE__*/React.createElement("div", {
      className: "bk-plate",
      style: {
        marginTop: 16
      }
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-plate__img",
      style: {
        aspectRatio: "1 / 1",
        maxWidth: 300
      }
    }, /*#__PURE__*/React.createElement("image-slot", {
      id: "about-portrait",
      placeholder: "Drop a portrait",
      shape: "rect"
    })), /*#__PURE__*/React.createElement("div", {
      className: "bk-plate__cap"
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-plate__no"
    }, "Frontispiece"), /*#__PURE__*/React.createElement("span", {
      className: "bk-plate__cn"
    }, "the author, such as he is"))), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        marginTop: 18
      }
    }, "Arpit Maheshwari"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        marginTop: 8
      }
    }, "Design leader for AI & data-intensive products. Fifteen years, five industries, one stubborn idea: the interface is where trust is won or lost."), /*#__PURE__*/React.createElement("div", {
      className: "bk-chips",
      style: {
        marginTop: 16
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-chip"
    }, "Indore, India"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chip"
    }, "15 years"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chip"
    }, "AI / Data UX"))),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "The longer story"), /*#__PURE__*/React.createElement("p", {
      className: "bk-lede bk-drop",
      style: {
        marginTop: 12
      }
    }, "I started in newspaper production \u2014 laying out pages against a press deadline \u2014 which is where I learned that typography is an argument and the deadline is not negotiable."), /*#__PURE__*/React.createElement(Beat, {
      n: "01",
      label: "How I got here"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "Software started needing both the argument and the deadline, so I followed it in. Fifteen years later I've designed across EdTech, FinTech, AdTech, telecom and org design \u2014 usually the first or only designer in the room when the model and the interface had to be argued about together.")), /*#__PURE__*/React.createElement(Beat, {
      n: "02",
      label: "What I believe"
    }, /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "That an AI product is only as good as whether a person will act on it; that the wrong-answer screen matters more than the happy path; and that the most senior thing a designer can do is write the system down, so the next one inherits more than my taste.")), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 16
      }
    }, "I set type for fun. it shows."))
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
    }, "Five industries, one throughline: I make machine intelligence legible enough that people will actually act on it. Two cases open in full; three more travel as redacted walk-throughs."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        margin: "22px 0 18px"
      }
    }, "the one I'm proudest of \u2193"), /*#__PURE__*/React.createElement("div", {
      className: "bk-feature bk-feature--link",
      onClick: () => enter("cases", 0)
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
        marginTop: 16
      }
    }, WORK.slice(1).map((w, i) => {
      const openIdx = [4, 5, 6, 2][i];
      return /*#__PURE__*/React.createElement("div", {
        className: "bk-item bk-item--link",
        key: i,
        onClick: () => enter("cases", openIdx)
      }, /*#__PURE__*/React.createElement("div", {
        className: "bk-item__top"
      }, /*#__PURE__*/React.createElement("span", {
        className: "bk-item__tag"
      }, w.tag), /*#__PURE__*/React.createElement("span", {
        className: "bk-item__metric"
      }, w.metric)), /*#__PURE__*/React.createElement("h4", null, w.title, /*#__PURE__*/React.createElement("span", {
        className: "bk-item__case"
      }, "open \u2197")), /*#__PURE__*/React.createElement("p", null, w.desc));
    })))
  }, /* 3 · CHAPTER II — HOW I LEAD */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "II · How I Lead",
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
    }, "How I", /*#__PURE__*/React.createElement("br", null), "Lead"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body bk-drop"
    }, "I lead from inside the work, not above it. I'd rather pair with an engineer on an eval than present a roadmap, and I think the best design decision in an AI product is usually about ", /*#__PURE__*/React.createElement("span", {
      className: "bk-mark"
    }, "what the system admits it doesn't know"), "."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 22
      }
    }, "credibility = the misses, written down \u2192")),
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
    }, String(i + 1).padStart(2, "0")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h4", null, p.h), /*#__PURE__*/React.createElement("p", null, p.p))))), /*#__PURE__*/React.createElement("div", {
      className: "bk-confession"
    }, /*#__PURE__*/React.createElement("span", {
      className: "bk-confession__label"
    }, "When I was wrong"), /*#__PURE__*/React.createElement("p", null, "I argued the recommendation card should show three ranked options. Engineering wanted one. I lost the argument."), /*#__PURE__*/React.createElement("p", null, "Next quarter's test: the one-option version converted ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "2.3\xD7 better"), ". Three options made people freeze. I redesigned how I approach every recommendation surface after that.")))
  }, /* 4 · CHAPTER III — A FIELD GUIDE TO TRUST (hub) */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "III · A Field Guide to Trust",
    folioL: "6",
    folioR: "7",
    left: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Chapter Three"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 III"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--l",
      style: {
        margin: "4px 0 16px"
      }
    }, "A Field", /*#__PURE__*/React.createElement("br", null), "Guide to", /*#__PURE__*/React.createElement("br", null), "Trust"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body bk-drop"
    }, "A working catalogue of the interface patterns I reach for when the product is only as good as whether people believe it. Each is a small argument about where certainty belongs on the screen \u2014 open one to read it in full."), /*#__PURE__*/React.createElement("div", {
      className: "bk-note",
      style: {
        marginTop: 22
      }
    }, "open a pattern to go a level deeper \u2197")),
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
      onClick: () => enter("patterns", i)
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
    runheadR: "IV · Notes & Writing",
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
    }, "Chapter Four"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 IV"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--l",
      style: {
        margin: "4px 0 20px"
      }
    }, "Notes &", /*#__PURE__*/React.createElement("br", null), "Writing"), /*#__PURE__*/React.createElement("blockquote", {
      className: "bk-pull"
    }, "If you can't design what happens when the model is wrong, you haven't designed the feature yet.", /*#__PURE__*/React.createElement("cite", null, "\u2014 from \u201CThe trust layer is the product\u201D")), /*#__PURE__*/React.createElement("div", {
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
    }, w.d), /*#__PURE__*/React.createElement("h4", null, w.h), /*#__PURE__*/React.createElement("p", null, w.p)))))
  }, /* CHAPTER VI — COLOPHON & CONTACT */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "V · Colophon & Contact",
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
    }, "Chapter Five"), /*#__PURE__*/React.createElement("span", {
      className: "bk-chno"
    }, "\u2116 V"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "4px 0 16px"
      }
    }, "Colophon"), /*#__PURE__*/React.createElement("p", {
      className: "bk-body"
    }, "This book was set in ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "Playfair Display"), " and ", /*#__PURE__*/React.createElement("span", {
      className: "bk-em"
    }, "Spectral"), ", with margin notes in Caveat and folios in Spline Sans Mono. Bound, printed, and maintained by its author."), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        marginTop: 12
      }
    }, "No analytics. No cookies. No newsletter to join. If something here is useful, take it and build."), /*#__PURE__*/React.createElement("div", {
      className: "bk-chips",
      style: {
        marginTop: 22
      }
    }, STATUS.map((s, i) => /*#__PURE__*/React.createElement("span", {
      className: "bk-chip",
      key: i
    }, s))), /*#__PURE__*/React.createElement("div", {
      className: "bk-spacer"
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-note"
    }, "thanks for reading to the end \u2665")),
    right: /*#__PURE__*/React.createElement("div", {
      className: "bk-reveal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-kicker"
    }, "Write to me"), /*#__PURE__*/React.createElement("h2", {
      className: "bk-title bk-title--m",
      style: {
        margin: "8px 0 10px"
      }
    }, "A free read on", /*#__PURE__*/React.createElement("br", null), "your AI UX."), /*#__PURE__*/React.createElement("p", {
      className: "bk-body",
      style: {
        marginBottom: 14
      }
    }, "Send a link to your product and I'll record a five-minute teardown \u2014 three concrete improvements, within 48 hours, no strings."), /*#__PURE__*/React.createElement(ContactForm, null), /*#__PURE__*/React.createElement("div", {
      className: "bk-contactlinks",
      style: {
        marginTop: 26
      }
    }, /*#__PURE__*/React.createElement("a", null, "hello@arpitmaheshwari.com ", /*#__PURE__*/React.createElement("span", null, "EMAIL")), /*#__PURE__*/React.createElement("a", null, "linkedin.com/in/arpitmaheshwari ", /*#__PURE__*/React.createElement("span", null, "LINKEDIN")), /*#__PURE__*/React.createElement("a", null, "Book a 30-min call ", /*#__PURE__*/React.createElement("span", null, "CALENDAR \u2197"))))
  }, /* 10 · APPENDIX — CURRICULUM VITAE */
  {
    kind: "spread",
    runheadL: VERSO,
    runheadR: "Appendix · Curriculum Vitæ",
    folioL: "12",
    folioR: "13",
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
    }, "The short, printable version. Fifteen years across five industries, leading design from the model layer to the front end."), /*#__PURE__*/React.createElement("div", {
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
        crumb: "OrgOS",
        idxLabel: "1 / 2",
        runheadR: "OrgOS",
        folioL: "1",
        folioR: "2",
        ...orgA
      }, {
        crumb: "OrgOS",
        idxLabel: "2 / 2",
        runheadR: "OrgOS",
        folioL: "3",
        folioR: "4",
        ...orgB
      }, {
        crumb: "Due Diligence",
        idxLabel: "walk-through",
        runheadR: "AI-Assisted Due Diligence",
        folioL: "1",
        folioR: "2",
        ...ndaPages[0]
      }, {
        crumb: "Programmatic",
        idxLabel: "walk-through",
        runheadR: "Programmatic Advertising",
        folioL: "1",
        folioR: "2",
        ...ndaPages[1]
      }, {
        crumb: "O2 Priority",
        idxLabel: "walk-through",
        runheadR: "O2 Priority Billing",
        folioL: "1",
        folioR: "2",
        ...ndaPages[2]
      }]
    },
    patterns: {
      parent: 6,
      label: "A Field Guide to Trust",
      kind: "Pattern",
      items: [{
        crumb: "Confidence Scores",
        idxLabel: "1 / 4",
        runheadR: "Confidence Scores",
        folioL: "1",
        folioR: "2",
        ...patPages[0]
      }, {
        crumb: "Failure States",
        idxLabel: "2 / 4",
        runheadR: "Failure States",
        folioL: "1",
        folioR: "2",
        ...patPages[1]
      }, {
        crumb: "Explainability",
        idxLabel: "3 / 4",
        runheadR: "Explainability",
        folioL: "1",
        folioR: "2",
        ...patPages[2]
      }, {
        crumb: "Human-in-the-Loop",
        idxLabel: "4 / 4",
        runheadR: "Human-in-the-Loop",
        folioL: "1",
        folioR: "2",
        ...patPages[3]
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
  "accent": "#8E3942",
  "pairing": "Playfair \u00b7 Spectral",
  "warmth": 70,
  "density": "comfy",
  "headline": "Arpit\u003cbr\/>Maheshwari"
};
const PAIRINGS = {
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
  }, it.sub) : null))));
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
    "aria-label": dir
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
  const mq = "(max-width: 820px)";
  const [mobile, setMobile] = useState(() => window.matchMedia(mq).matches);

  // ---- location in the IA tree: which deck, which spread index ----
  const readLoc = () => {
    try {
      const s = JSON.parse(localStorage.getItem("bk-loc"));
      if (s && typeof s.i === "number" && (s.deck === "spine" || s.deck === "cases" || s.deck === "patterns")) return s;
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
  const animating = useRef(false);
  const locRef = useRef(loc);
  locRef.current = loc;
  const mobileRef = useRef(mobile);
  mobileRef.current = mobile;
  const mLeafRef = useRef(mLeaf);
  mLeafRef.current = mLeaf;
  const bookRef = useRef(null);
  const zoomCount = useRef(0);
  const reduce = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const persist = l => localStorage.setItem("bk-loc", JSON.stringify(l));

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
    const coverInvolved = l.deck === "spine" && (l.i === 0 || target === 0);
    if (coverInvolved || reduce()) {
      animating.current = true;
      const nl = {
        deck: l.deck,
        i: target
      };
      setLoc(nl);
      persist(nl);
      setTimeout(() => {
        animating.current = false;
      }, 280);
      return;
    }
    animating.current = true;
    setAnim({
      dir: target > l.i ? "next" : "prev",
      from: l.i,
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
  const pr = PAIRINGS[t.pairing] || PAIRINGS["Instrument · Newsreader"];
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
    enter
  });
  bookRef.current = book;
  const inSection = loc.deck !== "spine";
  const section = inSection ? book.sections[loc.deck] : null;
  const deck = inSection ? section.items : book.spine;
  const curSpread = Math.min(Math.max(loc.i, 0), deck.length - 1);

  // a single desktop page face (used by base spread + flipping leaf)
  const PageFace = (sp, side) => /*#__PURE__*/React.createElement("div", {
    className: "bk-page bk-page--" + side
  }, /*#__PURE__*/React.createElement("div", {
    className: "bk-runhead"
  }, side === "l" ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, sp.runheadL || VERSO), /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: 0.6
    }
  }, "A Working Book")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    style: {
      opacity: 0
    }
  }, "\xB7"), /*#__PURE__*/React.createElement("span", null, sp.runheadR))), side === "l" ? sp.left : sp.right, /*#__PURE__*/React.createElement("div", {
    className: "bk-folio"
  }, side === "l" ? sp.folioL : sp.folioR));
  function renderDesktop() {
    const sp = deck[curSpread];
    let inner;
    if (!inSection && curSpread === 0 && !anim) {
      inner = book.spine[0].cover;
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
      }, "A Working Book")), sp.left, /*#__PURE__*/React.createElement("div", {
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
    return /*#__PURE__*/React.createElement("div", {
      className: "bk-stage" + (inSection ? " bk-stage--deep" : "")
    }, inSection && /*#__PURE__*/React.createElement("button", {
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
      className: "bk-book" + (inSection ? " bk-book--deep" : ""),
      style: {
        transform: `scale(${scale})`
      }
    }, inner)), /*#__PURE__*/React.createElement("button", {
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
    }, deck.map((_, i) => /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__dot" + (i === curSpread ? " on" : ""),
      key: i,
      onClick: () => goIndex(i)
    }))), /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__esc",
      onClick: exitSection
    }, "esc \u21A9 ", section.label)) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, curSpread === 0 ? "Cover" : sp.runheadR), /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__dots"
    }, book.spine.map((_, i) => /*#__PURE__*/React.createElement("span", {
      className: "bk-progress__dot" + (i === curSpread ? " on" : ""),
      key: i,
      onClick: () => goIndex(i)
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
    }, Caret("prev"), " ", section.label) : /*#__PURE__*/React.createElement("span", {
      className: "name"
    }, "Arpit Maheshwari"), isCover ? /*#__PURE__*/React.createElement("span", null, "A Working Book") : /*#__PURE__*/React.createElement("button", {
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
      className: "bk-m-stage"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bk-m-page" + (isCover ? " bk-m-page--cover" : ""),
      key: loc.deck + ":" + idx,
      style: {
        "--m-from": mDir > 0 ? "24px" : "-24px"
      }
    }, isCover ? pg.cover : /*#__PURE__*/React.createElement(React.Fragment, null, pg.content, pg.folio && pg.folio !== "\u2014" ? /*#__PURE__*/React.createElement("div", {
      className: "bk-m-folio"
    }, "\xB7 ", pg.crumb ? pg.crumb + " " + pg.folio : pg.folio, " \xB7") : null)), (idx > 0 || inSection) && /*#__PURE__*/React.createElement("div", {
      className: "bk-m-tap bk-m-tap--prev",
      onClick: () => stepMobile(-1)
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-m-tap bk-m-tap--next",
      onClick: () => stepMobile(1)
    }), /*#__PURE__*/React.createElement("div", {
      className: "bk-m-nav"
    }, /*#__PURE__*/React.createElement("button", {
      className: "bk-m-btn",
      onClick: () => stepMobile(-1),
      disabled: !inSection && idx === 0,
      "aria-label": "previous page"
    }, Caret("prev")), /*#__PURE__*/React.createElement("span", {
      className: "bk-m-label"
    }, inSection ? pg.crumb + " · " + pg.idxLabel : isCover ? "Cover · tap to begin →" : pg.chapter), /*#__PURE__*/React.createElement("button", {
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
