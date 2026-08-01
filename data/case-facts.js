/* ============================================================================
   case-facts.js — THE single source for the locked facts of the six case studies.

   WHY THIS FILE EXISTS
   The same six cases are told on two surfaces: the classic pages under case-studies/
   and the bound book in book/. They were maintained by hand, twice, and on 2026-08-01
   the book was found to have silently gone stale — two job titles left at a superseded
   value, a "the screens are redacted on purpose" line printed directly above visible
   screenshots, and three canon metrics that never crossed over. Nothing contradicted;
   everything had simply stopped being updated in one of the two places.

   THE SEAM
   Only facts that MUST NOT diverge live here: title, tag, role/meta, the metric ledger,
   and the provenance caption. Narrative prose — standfirst, context, the moves, pull
   quotes — deliberately stays in book/portfolio.js, because the book's voice is its own
   and prose was never where the drift happened.

   HOW EACH SURFACE USES IT
   * book/  reads this at runtime (loaded before portfolio.js; plain script, no build
     step — this site ships as static files on purpose and lab/teardown.html says so).
   * case-studies/*.html are hand-written static HTML and cannot read it at runtime
     without introducing a build. So they are held to it MECHANICALLY instead:
     tools/case-sync-check.py fails the build when a classic page disagrees with this
     file, and runs in CI and in the pre-push hook.

   Changing a locked fact = change it HERE, then let the gate tell you which classic page
   still disagrees. Provenance captions are additionally locked by CANONICAL-FACTS §9;
   never describe a screen as something it is not.
   ============================================================================ */
(function (root) {
  var CASE_FACTS = {
  "order": [
    "ptc",
    "o2",
    "fintech",
    "adtech",
    "orgos",
    "vc-diligence"
  ],
  "cases": {
    "ptc": {
      "no": "01",
      "key": "ptc",
      "title": "PTC University — Learning Connector",
      "tag": "EdTech · Non-NDA",
      "meta": [
        [
          "Role",
          "Lead Product Designer"
        ],
        [
          "Span",
          "2014–2019 · the CX team I built"
        ],
        [
          "Surface",
          "Web LMS · 11 languages"
        ],
        [
          "Result",
          "Shipped · in production"
        ]
      ],
      "metrics": [
        [
          "$1M",
          "Saved per year — print + shipping"
        ],
        [
          "5→1",
          "Platforms consolidated"
        ],
        [
          "9→11",
          "Languages, one pipeline"
        ],
        [
          "550k+",
          "Registered · 350k+ active"
        ],
        [
          "0% → 64%",
          "Subscription share of new bookings · Q3 2017 → Q3 2018"
        ]
      ],
      "plateNo": null,
      "provenance": null
    },
    "o2": {
      "no": "02",
      "key": "o2",
      "title": "Telefónica MyO2 & Priority Moments",
      "tag": "Telecom · Non-NDA",
      "meta": [
        [
          "Role",
          "Designer + Front-end"
        ],
        [
          "Team",
          "Equal Experts squad · O2 UK"
        ],
        [
          "Status",
          "Shipped · public"
        ]
      ],
      "metrics": [
        [
          "4M+",
          "MyO2 users served"
        ],
        [
          "2.6M",
          "Priority sign-ups · yr 1"
        ],
        [
          "5★",
          "Priority App Store rating"
        ]
      ],
      "plateNo": "2.1",
      "provenance": "MyO2 self-service app — the 4M-user account area: bills, allowances, data"
    },
    "fintech": {
      "no": "03",
      "key": "fintech",
      "title": "AI-Assisted Private Equity Investing",
      "tag": "FinTech · NDA",
      "meta": [
        [
          "Role",
          "Lead Product Designer"
        ],
        [
          "Team",
          "Engineers · data scientists · PM"
        ],
        [
          "Surface",
          "AI for private-equity investing"
        ],
        [
          "Status",
          "Shipped · under NDA"
        ]
      ],
      "metrics": [
        [
          "60% faster",
          "Per diligence pass · pre/post rollout"
        ],
        [
          "3",
          "Sources behind every score"
        ],
        [
          "Lead",
          "Analysts now open with it"
        ]
      ],
      "plateNo": "3.1",
      "provenance": "AlphaDeals product UI, shown under its own name · synthetic data · client identity under NDA"
    },
    "adtech": {
      "no": "04",
      "key": "adtech",
      "title": "Programmatic Advertising Platform",
      "tag": "AdTech · NDA",
      "meta": [
        [
          "Role",
          "Lead Product Designer"
        ],
        [
          "Team",
          "50+ distributed agile team"
        ],
        [
          "Surface",
          "DSP recommendation UI"
        ],
        [
          "Status",
          "Shipped · under NDA"
        ]
      ],
      "metrics": [
        [
          "2 wks → 3 hrs",
          "Campaign planning time"
        ],
        [
          "£69k",
          "Media-value gain per client"
        ],
        [
          "Why",
          "Reasoning on every call"
        ]
      ],
      "plateNo": "4.1",
      "provenance": "White-labelled reconstruction · synthetic data · bound by NDA"
    },
    "orgos": {
      "no": "05",
      "key": "orgos",
      "title": "OrgOS · Transparent Org Tooling",
      "tag": "Org Design · NDA",
      "meta": [
        [
          "Role",
          "Product & Design Lead"
        ],
        [
          "Team",
          "4 engineering streams + a PM"
        ],
        [
          "Surface",
          "Internal operating system"
        ],
        [
          "Status",
          "Shipped · under NDA"
        ]
      ],
      "metrics": [
        [
          "250",
          "On it today · designed for 200"
        ],
        [
          "0",
          "Managers in the loop"
        ],
        [
          "8",
          "Modules, one grammar"
        ]
      ],
      "plateNo": "5.1",
      "provenance": "Schematic, not a screenshot — the real screens stay under NDA"
    },
    "vc-diligence": {
      "no": "06",
      "key": "vc-diligence",
      "title": "Technical Due Diligence Platform",
      "tag": "VC/PE · NDA",
      "meta": [
        [
          "Role",
          "Product & Design Lead"
        ],
        [
          "Team",
          "Model engineers · data scientists"
        ],
        [
          "Surface",
          "Technical-DD platform · VC + PE"
        ],
        [
          "Status",
          "Shipped · under NDA"
        ]
      ],
      "metrics": [
        [
          "3 wks → 4 days",
          "Diligence cycle time"
        ],
        [
          "VC + PE",
          "Both fund types served"
        ],
        [
          "4",
          "Signal classes scored"
        ]
      ],
      "plateNo": "6.1",
      "provenance": "Schematic, not a screenshot — the real screens stay under NDA"
    }
  }
};

  /* Fail loudly rather than render a half-empty case: a silent undefined here would put a
     blank role or a missing metric in front of a hiring manager, which is the exact failure
     this file exists to prevent. */
  CASE_FACTS.get = function (key) {
    var c = CASE_FACTS.cases[key];
    if (!c) throw new Error('case-facts: unknown case "' + key + '"');
    return c;
  };
  /* meta/metrics are stored as [label, value] pairs so they survive JSON cleanly; the book
     wants objects for its ledger renderer. */
  CASE_FACTS.metrics = function (key) {
    return CASE_FACTS.get(key).metrics.map(function (p) { return { v: p[0], l: p[1] }; });
  };

  root.CASE_FACTS = CASE_FACTS;
  if (typeof module !== 'undefined' && module.exports) { module.exports = CASE_FACTS; }
})(typeof window !== 'undefined' ? window : globalThis);
