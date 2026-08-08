# CANONICAL FACTS — the single source of truth

**Read this before changing any number, title, name, or date on the site.**
This file is the *master copy* of every fact that appears in more than one place. The rule is simple:

> **Edit the fact HERE first. Then update every place it appears on the site.**
> One value, used everywhere. If a number lives in two places, they must match this file.

When you change something here, search the whole project for the OLD value to find every page that
still shows it (ask Claude: "update <fact> everywhere to match CANONICAL-FACTS.md"). The site drifted
out of sync before precisely because each page kept its own copy of the truth.

_Last reconciled: 2026-06-19._

---

## 1. Who I am (positioning)
- **The line:** "Your model is right. Your users still won't bet on it." That half-second of doubt is the
  only thing I design. (This hero line is locked — do not edit.)
- **"The trust layer" is RETIRED COMPLETELY (2026-08-01 — Arpit's call). Zero occurrences, any casing,
  any context. It is not a positioning phrase, not a brand, not a filename.**
  "AI trust layer" is claimed enterprise vocabulary for governance/security middleware (Salesforce's
  Einstein Trust Layer, UiPath's AI Trust Layer) — a hiring manager searching or hearing that phrase
  reads governance infrastructure, not interface design.
  - **The practice / specialism** → **"human-in-the-loop design"** (lower-case, hyphenated).
  - **The book and the printed portfolio** → **"Human in the Loop"** (title case, a proper noun).
    The portfolio's running header is "Human in the Loop · Selected Works"; the book's cover
    imprint is "Human in the Loop · MMXXVI".
  - **The newsletter** → labelled **"Human in the Loop"** on every surface.
  - **The code module** → `lab/loop.js` + `loop.test.js` + `/lab/loop.html`. The old URL
    `/lab/trustlayer.html` survives ONLY as a silent forwarding stub, because it was published in
    the sitemap and linked from the portfolio PDF. That stub is the single permitted appearance of
    the old string anywhere in the repo — it renders no visible copy.
  - `assets/og-images/book-og.png` had the old title baked into its pixels. Regenerated from
    `_book-og.template.html`, which now exists so the next rename is a one-liner.
  - _History, so this is not re-litigated: on 2026-07-31 only the positioning phrase was changed and
    this file explicitly recorded the brand as "unchanged — never rename these". That instruction is
    what made eight QA passes walk straight past the book cover, which still read "The Trust Layer"
    in 15 places. Arpit overruled it on 2026-08-01. A term audit must grep the bare phrase, never a
    context-qualified pattern._
- **OPEN ACTION (Arpit, external — not doable from the repo):** the Substack publication is still
  literally named "The Trust Layer" at arpitmaheshwari.substack.com. The site now labels every link
  to it "Human in the Loop". Until the publication is renamed in Substack's settings, the site is
  naming it something it is not.
- **Job title — use ONE of these, not a new variant each time:**
  - In page code / structured data (schema `jobTitle`): **Product & Design Leader — AI & Data-Intensive Products**
  - On-page role line (under my name): **Product & Design Leader · AI & Data-Intensive Products**
  - _(Retitled from "Design Leader" on 2026-07-25 — Arpit's call: also owns product management, product definition, roadmapping. PM receipts: AdTech, FinTech + DD, OrgOS — NOT PTC.)_
  - Only exception: the `/hire/` page's browser-tab title may keep its search wording
    "Product & Design Leader, AI Products" — but its on-page role line still uses the canonical above.

## 2. Availability (must read identically everywhere)
- **Available · 4 weeks' notice** (always the digit "4", never "four").
- Fully remote from Indore, India (GMT+5:30) — daily overlap with both US coasts. (SUPERSEDED 2026-08-04: was "4–5 hours of daily overlap with US East Coast"; Arpit works late and covers US West too. Locked phrasing: "daily overlap with both US coasts" — coast-neutral, no hour counts.)
- Looking for ONE role: founding product & design lead at an AI product company of 5–40 people, OR a
  staff / director seat where human-in-the-loop design is the job.

## 3. The six case studies — names + numbers are LOCKED
Use the exact metric strings below on every surface (homepage chip, case-study page, the book, the résumé).

| # | Canonical name | Tag | Headline metric (exact string) | Other locked numbers |
|---|----------------|-----|-------------------------------|----------------------|
| 1 | **PTC University — Learning Connector** | EdTech · Non-NDA · full case | **$1M / yr** (print savings) | 550k+ registered · 350k+ active · subscription **0% → 64%** of new bookings (Q3 2017 → Q3 2018) · 5→1 platforms · 9→11 locales · mobile: 4% of sessions at start, grew after the responsive redesign (endpoint number RETIRED 2026-08-06 — see entry) · **20+ countries** (corrected from "80+" 2026-08-06, Arpit: "safe side make it 20+" — never reprint 80+) · Role: Product & Design Lead (retitled 2026-08-02, PM receipt) · 2014–2019 |
| 2 | **Telefónica MyO2 & Priority Moments** | Telecom · Non-NDA / public | **4M+** (MyO2 users) | Priority Moments **2.6M** sign-ups year one · 2.5M+ active · 5★ App Store · Role: Designer + front-end via **Equal Experts, 2012–14** · **design was SHARED with one co-designer; ALL front-end code his (corrected 2026-08-06 — never claim solo design)** |
| 3 | **AI-Assisted Private Equity Investing** | FinTech · NDA | **60% faster** (deal screening) | measured pre- vs post-rollout · 3 sources behind every score · Role: Lead Product Designer · _(true sample: 42 deals over a 90-day window — DO NOT PUBLISH, see display rule below)_ |
| 4 | **Programmatic Advertising Platform** | AdTech · NDA | **2 wks → 3 hrs** (campaign planning) | Recommended campaign plans with visible KPIs/ROI, easily customizable — **NO confidence scores, ever** (corrected 2026-08-05, see AdTech correction entry) · Role: Lead Product Designer · _(added 2026-07-31, Arpit confirmed real + interview-defensible)_: **45%** reduction in time/effort to plan + book campaigns · **£69,000** average media-value uplift per client · **3x** purchase-intent uplift + **70%** audience uplift vs traditional bookings · £400M media spend transacted through the platform · 50M bids/hr (engineering's infrastructure — attribute, never claim). **RETIRED (2026-07-31, Arpit's call): "2 wks → 1 hr speed to market" — true but confusable with the locked headline; "2 wks → 3 hrs" is the ONLY time metric on any surface. Never re-add the 1-hr variant.** |
| 5 | **OrgOS · Transparent Org Tooling** | Org Design · NDA | **200** (people) | 200 people · 0 managers · 8 modules · **in use by 250 people today (2026)** — the org grew past the 200 it was designed for and the coordination model held · Role: Product & Design Lead (per PM-receipts retitle, 2026-07-25). ("Zero managers" is the *outcome*, never the title.) |
| 6 | **Technical Due Diligence Platform** | VC/PE · NDA | **3 wks → 4 days** (diligence cycle) | 16 analysis dimensions — a finding became a SIGNAL only at sufficient confidence, every signal backed by verified evidence (corrected 2026-08-06, see entry) · VC + PE · Role: Product & Design Lead (per PM-receipts retitle, 2026-07-25) |

**Number-writing rules:** arrow is "→" with a space each side. Never write "−60%" (use "60% faster").
Never abbreviate to "3w → 4d" (use "3 wks → 4 days"). Lowercase "k" in "550k+".

### The documented miss (added 2026-07-22 — Arpit's own account, the one failure story)
On PTC accessibility work: first pass added extensive ARIA labels for visually-impaired users.
Testing with real users exposed the mistake — screen-reader users don't listen through long
sentences; they skim fast, jumping by headings and landmarks, and the verbose labels made the
interface SLOWER for exactly the people they were meant to help. To rebuild empathy he worked
with the monitor off / eyes closed, navigating by screen reader (this is the same fact as the
About line — one week, monitor switched off). Then he re-did the front-end code. Failure → fix.
Use this story wherever a "documented miss" is needed (PTC case, PDF). Never invent metrics
for the redo; the honest arc IS the value.

### Research texture (Arpit's account, 2026-07-22)
- AdTech: research included campaign planners, media sellers, and creative agencies ("a lot" —
  no exact count claimed; the pain-point tables in his old case doc came from these).
- VC diligence: usability testing with investment analysts.
- Trader-observation counts/quotes for the Act/Review/Ignore origin: STILL UNKNOWN — do not invent.

### PlanIt correction (2026-07-22 — Arpit's own account; supersedes "side project" framing)
PlanIt (planitnow.co.uk, 2021, now deprecated) was **NOT a side project**. It was a **main client
project**, built for the client by **leveraging the data generated from the AdTech platform**
(the footfall/audience data). Never call it a side project, personal project, or coda again. **Display rule (2026-07-22):**
the fact that it was client work is TRUE and drives the framing, but do NOT print the label
"Client project" on the PDF — the kicker reads "PlanIt · built on the AdTech platform's data · 2021".
Facts that stay: quietness score 1-10, the mascot, warm palette, London Underground + National
Rail footfall data, ~1,000 monthly visitors / 250 active users (honest small scale), zero-complaints
claim REMOVED earlier (keep removed). Surfaces: portfolio PDF (currently "Coda · Side Project" — fix).

### O2 evidence (updated 2026-07-22)
Primary O2 imagery on all surfaces = **MyO2 self-service app screens** (home, minutes/data
allowances) — Arpit's own files, the genuine 4M-user product. File: assets/shots/o2-app-screens.png.
The earlier Internet Archive capture (o2-mobile-2013.png) was REMOVED at Arpit's instruction once
the real app screens arrived. Caption everywhere: "MyO2 self-service app · the 4M-user account area".

### O2 honesty note (important)
The launch-era O2 figures (July 2011 launch, £6m campaign, 2.6M year-one, 5★) are **O2's public facts**,
not personal KPIs. I joined the Priority programme in **2013** (within my Equal Experts tenure, 2012–14)
and designed + built the reward/offer screens. Keep that distinction wherever O2 is described.

## 4. The patterns library (the "playbook")
The **Act / Review / Ignore** rule (foundational) + **8 patterns**, all marked **In production**:
Confidence Scores · AI Failure States · ML Explainability · Human-in-Loop · and (added 2026-06-19)
**Provenance & Citations** (VC + FinTech) · **The Capability Contract** (AdTech + FinTech) ·
**Calibration & Track Record** (AdTech + FinTech) · **Reversibility / Safe-to-Act** (PTC + AdTech).
Live in BOTH views: classic pages in `/patterns/` + book field-guide spreads. The book's field-guide
opener lists all 8 — it is fit-tuned to 880px, so keep it spill-verified if you add a ninth.
The original four each link to a matching **Writing** essay; the four new ones have no essay yet.
Patterns = the *reference* (do/don'ts, demos); Writing = the *stories*.

## 5. Testimonials (all confirmed genuine — 2026-06-19)
Use real names + titles, verbatim quotes. Current placements:
- **Anant East** — CTO, Talon Outdoor _(homepage + /hire)_
- **Ryan Kershner** — UX Design Leader, managed Arpit directly _(homepage + /hire)_
- **Katie Alterio** — Product Designer _(homepage)_
- **Jonathan Berkey** — Product Design Leader, managed Arpit directly _(currently on no surface — replaced by Kershner on the PTC case page, Arpit's call 2026-08-06; quote remains canon-valid if he wants it back)_
- **Sanjesh Ananda** — Software Engineering Leader _(homepage + AdTech case, added to homepage 2026-07-31 — the only ENGINEERING voice; answers the "can a designer ship?" doubt that the three design voices cannot)_

## 6. The two views (intentional — not a mistake)
- **Book** (`/book/`) — the human front door. Warm "printed-paper" identity: terracotta `#C0512B` +
  cream `#F4ECDA`, Playfair/Spectral type. Reads like a bound book.
- **Classic** (`/`) — the search-engine surface + scrolling read. Dark "screen" identity:
  near-black `#0A0A0A` + gold `#D4A85E`, Fraunces/Inter Tight type.
- They look different **on purpose**. Both must tell the **same facts** (this file) in their own voice.
- **Accessible text tokens (2026-07-22 — measured, not vibes; all body-size text ≥4.5:1):**
  **ERRATA (2026-07-31):** the claim below that "the classic site's tokens already pass" was
  **FALSE for the cream acts.** A full audit (12 pages, 1,004 text nodes, translucent backgrounds
  composited) found **43 failures**: gold `#8A6423` measured **4.39:1** on the act cream `#F1E8D6`
  and **4.06:1** on the card cream `#EAE0CA` — both under the 4.5:1 body floor. Fixed by darkening
  the cream-act gold to **`#7E5A14`** (5.14:1 / 4.77:1). Any future cream gold must clear 4.5:1
  against **`#EAE0CA`** (the darkest cream), not just the act background. Also note `--ink-muted
  #6E6250` passes on that card by only 0.04 (4.542:1) — it breaks if the card ever darkens.
  The `#8A6423` / 4.55:1 pair below remains CORRECT for the documents' lighter cream `#F4ECDA`.
  Book: `--bk-ember-ink #B04A24` and `--bk-ochre-ink #8F5E10` for body-size text; the original
  ember/ochre stay for backgrounds and large display (≥24px) only. Documents (PDF + resume):
  captions/dim `#6F6350` (4.99:1), gold kickers/dates `#8A6423` (4.55:1) on cream `#F4ECDA`.
  Diagram SVGs use the same. Caption rule: sentence case beyond ~40 chars, ≥8pt in documents.
  If you add a new text color, run the contrast math BEFORE shipping — the classic site's
  tokens already pass and must stay passing.

## 7. The narrative spine (every page is a chapter of ONE argument)

The site tells one story. Every edit must advance it, not restate it:

> **Your model is right. Your users still won't bet on it.** (the problem — hero, locked)
> **The half-second of doubt is the only thing I design.** (the specialization)
> **Trust is built from learnable moves** — a verb instead of a naked score, evidence beside
> the number, an honest "I'm not sure," an override that teaches. (the patterns)
> **Six cases prove it** — each owns ONE distinct chapter, below. (the proof)
> **One seat, full-time.** (the ask)

**Each case owns exactly one beat — no case may restate another's moral:**
- **AdTech** owns "the model was right — that was the problem" (the origin of Act/Review/Ignore).
- **FinTech** owns abstention & evidence ("I'd rather it say nothing than hallucinate").
- **VC Diligence** owns provenance & the sign-off gate ("pricing the doubt").
- **PTC** owns "the contract was the broken interface" (design as business argument).
- **O2** owns craft at scale ("drawn by me, then coded by me").
- **OrgOS** owns "coordination is a trust problem between people."

**Hedge policy — honesty with command, not apology:** attribution scoping (what's the ML/DS
team's vs. mine) appears ONCE per case, stated as ownership of the boundary ("The model's
accuracy is their result to defend; the acting-on-it is mine") — never twice, never as a
disclaimer, never in consecutive paragraphs.

**Banned repetitions:** "human-in-the-loop design is the product" (and the retired "the trust layer is the product") and generic restatements of the hero
thesis may appear on the homepage and ONE case (AdTech) only. Each other page closes on its
own beat.

## 8. The design process (canonical framing — added 2026-07-21)
Arpit's process, reframed in the site's voice from his three-layer model. All surfaces
(homepage band, /process page, portfolio PDF, book spread) use THESE names and this order:

> **Every product is a series of bets someone else has to accept.** The process exists
> to make each bet smaller, better-evidenced, and easier to say yes to.

- **Act I — The wager worth making** (his Foundation): three questions before any pixel —
  does the market actually want it (desirability) · can we actually build it (feasibility) ·
  does it sustain a business (viability). The overlap is the product vision; everything
  outside it is a feature that dies in review.
- **Act II — The spiral** (his Engine): not a line, a spiral — 4 moves per loop, each loop
  ending in front of a user: **Listen** (research, problem space) → **Structure** (journeys,
  information architecture) → **Prove** (prototypes, low→high fidelity) → **Land** (visual
  design, brand, tone). Research is a rhythm, not a phase.
- **Act III — The loop that never closes** (his Execution): MVP → V1 → V2 → Vn. Shipping is
  the first honest data — what users DO feeds back into the roadmap, and the spiral keeps
  turning after launch.
- **Philosophy line (verbatim on all surfaces):** "Design is an upward spiral: every turn
  reduces risk and raises the odds of adoption. Confidence is earned in loops, not declared
  in launches." (Ties the process to the human-in-the-loop thesis.)
- **The tooling fact (added 2026-07-22, Arpit's account):** prototypes are AI-assisted
  **working HTML** — not clickable pictures. They go in front of real users for usability
  testing, and when they survive, **the code ships as part of the production codebase**.
  AI is the sounding board throughout the loop — a tireless colleague to argue with before
  spending an engineer's afternoon. Surfaces: /process (Prove move), resume bullets + skills,
  portfolio PDF method page.

Rules: never present as a stock double-diamond; no fabricated loop counts for specific
projects; case references stay qualitative (e.g., Act/Review/Ignore was born in a Listen loop).

## 9. SURFACE FREEZE (2026-07-21 — recruiter audit #2)
**The no-drift rule (2026-07-22):** any change to a canonical fact ships to BOTH views
(classic + book) and the PDF sources **in the same commit** — a surface that lags is a surface
that lies. **The routing rule (2026-07-22):** the classic site is the front door for everyone;
the book opens only by explicit choice ("Read as a book" / ?view=book) and every book spread
has a shareable URL (#deck-index).
**No new pages or surfaces without retiring one.** The estate is complete: home, /hire,
/screen, /process, /patterns, /folio, /book, writing. Every future improvement goes INTO
an existing surface, never beside it. The remaining gaps are evidence, not architecture:
process video, named quotes for the AI metrics, LinkedIn parity, domain email.

**Case facts have ONE home (2026-08-01).** `data/case-facts.js` is the single source for every
locked case fact: title, tag, role/meta, the metric ledger, and the provenance caption. The book
RENDERS from it at runtime (loaded before `portfolio.js`, which throws rather than render a case
with missing facts), so book-vs-source drift is now structurally impossible. The classic pages
under `case-studies/` are hand-written static HTML and cannot read it without introducing a build
step — this site ships as static files on purpose — so they are held to it mechanically instead:
`tools/case-sync-check.py` fails CI and the pre-push hook when a classic page disagrees. Narrative
prose deliberately stays per-surface; prose was never what went stale. **To change a locked fact:
edit `data/case-facts.js`, then let the gate name the classic page that still disagrees.**

**Provenance captions (locked wording):** AdTech screens = "white-labelled" (true — client
brand removed). FinTech screens = "AlphaDeals product UI, shown under its own name · synthetic
data · client identity under NDA" (the product brand is public via Arpit's own materials;
NEVER caption it "white-labelled"). Never claim a screen is something it isn't — provenance
accuracy IS the positioning.

## 10. Housekeeping conventions
- **Cache version (bump on every change so visitors see updates):** classic pages use
  `styles.css?v=pNN` (now **p21**); book uses `book.css?v=NN` (**58**) and `portfolio.js?v=NN` (**107**).
- **Analytics:** Google Analytics ID `G-PFY6ME99K8` (same across all pages).
- **Primary action:** the "Send me the role" form (Formspree). Calendly is the quiet secondary.
  **Email IS public** (changed 2026-07-21 after recruiter feedback — recruiters don't fill forms):
  maheshwari.arpit88@gmail.com, assembled by a small script on the page so bots can't scrape it.
  It appears on the homepage contact section and /hire.
- **Team credits (added 2026-07-21):** every case names its team — AdTech "50+ distributed agile team",
  FinTech "cross-functional: engineers, data scientists, PM", VC "alongside the engineers and data
  scientists who built the model", OrgOS "four engineering streams + a PM". No solo-genius voice.
- **Social handles (LOCKED — docs used a wrong LinkedIn until 2026-07-22):** LinkedIn =
  linkedin.com/in/**arpitmaheshwariprofile** (NEVER "arpitmaheshwari88"). GitHub =
  github.com/arpitmaheshwari. Substack = substack.com/@arpitmaheshwari. Designed resume/portfolio
  show these as small gold monoline icons (not long URLs); the ATS .docx keeps the LinkedIn URL as
  parseable text.
- **Title honesty:** documents and site say **Product & Design Leader — AI & Data-Intensive Products** as
  positioning; the résumé names the official employer title ("Solution Consultant") beside the
  functional one ("Product & Design Lead — AI Products"). PM claims carry receipts only on AdTech,
  FinTech + DD, and OrgOS — never claim product ownership on PTC work. LinkedIn must match this story — never claim
  "Principal" as a conferred rank anywhere.
- **AdTech reference (display rule, updated 2026-07-22):** say only "a named reference for this work
  is available on request." NEVER publicly identify them as "the client's CTO" or tie the reference to
  a specific project/role in writing — Arpit's instruction. The reference exists; who they are is shared
  privately, not printed on the resume/PDF/site.
- **FinTech sample size (display rule, 2026-07-25 — Arpit's instruction):** NEVER publish "42 deals",
  "90-day window", or "n=42" anywhere. The numbers are true and stay in this file for interview use, but
  in print a small denominator invites "only 42?" and reads as weaker than no denominator at all. Where a
  baseline slot needs filling (hire receipts, homepage proof-meta, case stats), use **"measured pre- vs
  post-rollout"** — it keeps the honesty posture without handing over a number that undersells the work.
  The sample, eval design, and baseline are offered on a call instead ("artifacts open").
  The calibration pattern demo keeps a denominator because the pattern requires one — but it uses
  clearly-illustrative figures ("its last 200 calls at this confidence"), never Arpit's real ones.

### OrgOS framing (2026-07-23 — Arpit's instruction)
The moat is NOT scale/headcount ("250 run on it today" / "built for 200"). The primary point is that
OrgOS is a **unique system that makes a radically transparent, flat, manager-less organization actually
work** — a flat hierarchy encoded into the software itself, doing the coordination a management layer
normally would. Lead every OrgOS mention with that; headcount is at most a secondary detail, never the
headline. (Resume already updated; align the OrgOS case study + any homepage mention the same way.)

### Nav IA + React claim (2026-07-27)
- **Site nav (all classic pages):** Work · Patterns · **Lab** · Writing · How I Lead + "Read as a
  book ↗" + CTA "Send me the role ↗". The old "Contact" nav item was REMOVED as a duplicate of the
  CTA (both went to #contact; the CTA is visible on every viewport). Do not re-add it.
- **Wayfinding:** inner pages mark their section with `aria-current="true"` (case-studies→Work,
  patterns→Patterns, lab→Lab, writing→Writing); gold tint via styles.css (`?v=ds2`).
- **View-router rule:** a URL hash always beats the remembered book preference — never let the
  am-view=book redirect swallow #section links (this was a live bug, fixed 2026-07-27).
- **React claim (corrected upward, with receipt):** the book edition is ~150KB of Arpit's own React
  (measured: book/portfolio.js 120,307 B + image-slot.js 31,364 B; 53 hooks — 25 useState,
  13 useRef, 8 useCallback, 7 useEffect). Say "React beyond prototypes", never "React for
  prototypes and component scaffolds" (undersells a shipped app). Boundary that stays: he does not
  claim the backend.

### Email display rule (2026-07-27 — Arpit's instruction, spam prevention)
NEVER render maheshwari.arpit88@gmail.com as visible text or a static mailto: on any public web
surface (site, book, llms.txt, JS headers). The pattern everywhere is click-to-compose: a label
("write to me directly →" / "email — click to write") whose mailto: href is assembled from split
parts INSIDE the click handler — the address never enters the served HTML or the idle DOM.
The PDFs and the .docx keep the address in full (they are handed out deliberately).

### Ownership blocks (2026-07-28 — answer to the convergent "how much did YOU own?" doubt)
Every case-study page carries a 3-row Owned / Shared / Not mine strip directly under the vitals.
The lines are the EXISTING attribution made scannable — never add a claim here that the case
prose doesn't already make. Canonical splits:
- **AdTech** — Owned: product definition, roadmap, end-to-end design (planner, inventory SaaS,
  reporting), the Act/Review/Ignore rule. Shared: eval design + reasoning taxonomy w/ data
  science. Not mine: bidding model, 50M-bids/hr infrastructure (engineering's win).
- **FinTech** — Owned: product definition, interaction design, abstention + citation UX, the
  launch gate. Shared: eval design + threshold tuning w/ data science. Not mine: model accuracy,
  retrieval backend.
- **DD (vc-diligence)** — Owned: product definition + design of the four-signal verdict surface,
  provenance gate. Shared: signal taxonomy w/ engineers + data scientists. Not mine: the model,
  code-analysis pipeline.
- **OrgOS** — Owned: definition + build order of the eight modules, interaction design. Shared:
  roadmap + delivery w/ PM + four engineering streams. Not mine: backend, data-model
  implementation.
- **PTC** — Owned: consolidation argument + IA, subscription-shift design work, the 4-person
  design team. Shared: business-model decision w/ PTC leadership; delivery w/ platform
  engineering. Not mine: LMS backend, commerce infrastructure. (2026-08-02: the "NOT a PM
  receipt" note that stood here is SUPERSEDED — see the dated PTC-is-a-PM-receipt entry below;
  he drove definition, roadmap, consolidation and sunsets, leadership ratified.)
  **The subscription MECHANISM (Arpit's own account, 2026-08-01 — supersedes any narrower
  phrasing):** the 0% → 64% shift ran on a product-led, free-to-premium funnel — free tutorials
  and trainings were the acquisition layer; experiencing them converted learners to paid premium
  subscriptions. Arpit designed that free-to-paid experience. This makes "product-led growth /
  freemium funnel" an HONEST claim on any surface (resume, site, interviews), scoped as: the
  funnel design was his; commercial packaging/pricing stayed with PTC leadership. Earlier notes
  attributing the whole shift to "pricing and sales" recorded the number's ownership, not the
  mechanism, and undersold the design contribution.
- **O2** — Owned: every screen + the front-end code. Shared: delivery within Equal Experts.
  Not mine: launch marketing + public launch numbers (O2's, reported as theirs).

### Process artifacts — corrected 2026-08-02 (the 2026-07-29 "none survive" was too broad)
**SERVICE BLUEPRINTS SURVIVE** — Arpit holds them for PTC, AdTech, OrgOS, VC diligence and
FinTech. He keeps the files himself (not in any repo). Visibility rule, his call: **interview
only** — surfaces may say the walk-through includes service blueprints, but no blueprint is ever
published, hosted, or linked. What remains true from 2026-07-29: no PlanIt mascot sketches, no
whiteboards or module-mapping photos, no rejected-iteration screenshots (incl. the 3-option
recommendation card). NEVER recreate, mock up, or stage those — fabricated process theater is an
instant credibility kill. The live pattern demos and The Lab remain the "watch me work" surfaces.

### Marginalia layer (2026-07-29 — supersedes the single-sign-off restraint)
Arpit's explicit call after the Dominique Cheng reference: the site must read as a personal
creation, not an agency site. Direction B shipped: handwritten (Caveat) fact-notes + pen-drawn
SVG scribbles across the homepage — see DESIGN-SYSTEM.md §10 for the rules. Notes must state
existing canon facts only ("six years watching…", "the rule a trading floor taught me",
"hand-built, code included", "— Arpit"). This is PRESENTATION warmth — the closed-artifacts rule
(no fabricated process evidence) still stands untouched.

### AdTech £69k — surface list (2026-07-31, propagated on Arpit's instruction)
The **headline metric stays "2 wks → 3 hrs"** on every surface; **£69,000 average media-value gain per
client** rides alongside it as the business-value companion (never replacing the headline). Live on:
homepage proof chip + `#receipt-adtech` panel · `/hire` first receipt · `llms.txt` · book AdTech ledger
(both the React spread and the no-script full-text edition) · case page hero stat + receipt table ·
resume.html + make-resume.js + portfolio.html ledger (private repo — already carried it).
The other confirmed numbers (**45%** effort, **3x** intent / **70%** audience) stay **case-page-only
depth** — deliberate, so the scan surfaces keep one headline plus one money number instead of a wall
of figures. (3x/70% additionally rides the portfolio PDF's AdTech ledger, 2026-07-31.)

### Screening-gate summaries on case studies (2026-07-31)
Every case page opens with a `.case-gate` block — "The short version · N seconds" —
before the jump-nav. It must contain three things and nothing else: the **outcome
number in its exact canonical string**, the **constraint**, and **his specific role
including what was NOT his**. 75-90 words. Built from that page's own section
headings, so a skimmer gets the whole argument and a committed reader gets a schema
that improves what they retain from the prose below. **No prose was deleted to make
room** — the deep read is the differentiator; the gate is what buys a reader for it.
Rule: if a metric appears in a gate it uses the locked string ("2 wks → 3 hrs"),
never a prose paraphrase — identical repetition is what makes the number stick.

### Homepage patterns section leads with The Capability Contract (2026-07-31 — Arpit's call)
Arpit's judgement: Act / Review / Ignore, presented as a three-tier taxonomy, "is such a silly
rule that anybody will know it" — obvious once stated, which makes it a good rule and a weak
reveal. It is NOT retired: it remains the foundational rule, it shipped, eight patterns hang off
it, it is tested in `lab/trustlayer.js`, and it stays the AdTech case's origin beat and its own
pattern page. What changed is only what the HOMEPAGE leads with.
The `#patterns` section now headlines **The Capability Contract** (in production: AdTech + FinTech)
— "a language model has no edges, so I draw them" — with the three clauses In scope / Declines /
Hands back, and links out to the contract pattern, to Act / Review / Ignore as "the rule underneath
it", and to the full library. Chosen because it is the least guessable pattern in the library:
almost nobody publishes what their AI *can't* do as a product artifact, and writing the contract
is a decision only someone with product authority gets to make.
All copy is sourced from patterns/capability-contract.html — nothing invented.

### ChatGPT design-spec fact quarantine (2026-07-30 — spec reviewed, mechanics adopted, facts rejected)
A ChatGPT-authored design spec/mockup (a paper-first redesign, titled with the since-retired
"trust layer" name) contained INVENTED
facts. NEVER import these, from that document or anywhere else:
- "16 years" → canon is FIFTEEN (locked hero line)
- "8 AI products shipped" → no basis (8 PATTERNS in production; 6 case studies)
- "$120M ARR platform designed" → fabricated; zero basis in any source
- Title "AI Product Designer" → canon is Product & Design Leader (2026-07-25 retitle)
- Client LOGO walls → text names only (trademark risk; deliberate 2026-07-28 decision)
What WAS adopted from it (2026-07-30, all content canon-sourced): homepage inline receipts
(#receipt-adtech/-fintech/-ptc/-o2, one open at a time, deep-linkable), the Trust Trace strip
(Score → Doubt → Action → Impact), and the four commitment-graded exit rows at contact.

### The boundary statements — one per case (2026-08-02, LOCKED phrasing per surface)
Every case study now carries a "Where this wouldn't transfer" beat: the condition the result
depended on, and where it would NOT hold. This exists because the site argues that AI should
state its confidence honestly and abstain rather than guess — a portfolio that never scopes its
own claims contradicts its own thesis. These are scoping judgements, NOT new facts; each is
derived from what that case already admits, and nothing here may introduce a number.

- **AdTech** — the model was already accurate; the gap closed was trust, not accuracy. If a
  model is genuinely wrong, no interface saves it (upstream fix).
- **FinTech** — holding a launch to build explainability only pays when the user is an expert
  paid to doubt the answer; wrong bet for a low-stakes decision nobody audits.
- **VC diligence** — deliberate friction survives only when the person clicking is personally
  accountable for the verdict; a user with no downside routes around it.
- **OrgOS** — ran inside a company that already believed in radical transparency with no
  management layer defending itself; in a conventional hierarchy it fails on politics first.
- **PTC** — had a year and a direct line to the executives who owned the P&L; the same argument
  in one quarter without that access loses. Design was necessary, never sufficient.
- **O2** — launch figures are O2's public record, not his attribution; 2013 consumer scale does
  not transfer to enterprise AI on its own.

WHERE THEY LIVE: all six classic case pages (block after the receipt, before the principle);
all six book case spreads (after the margin note). The 13-page portfolio PDF cannot fit six —
five of seven case pages have <40px of slack, measured — so it carries ONE synthesis statement
on the Method page instead, pointing to the site. The RESUME deliberately carries none:
"what could prove me wrong" in a bullet reads as hedging in a six-second scan.

### TCS (Tata Consultancy Services, Sep 2010 – Dec 2012) — no facts on record
Canon holds ZERO outcome facts for this role: no metrics, no named clients, no measured result.
The resume therefore states it as a dated header line only ("mobile for Fortune 500 banking &
pharmaceutical clients"), with NO achievement bullet — matching how /hire and the book already
list it. Do not write an achievement bullet for TCS unless Arpit supplies a real, measured
outcome. The dated header MUST stay: 2010 is what anchors the locked "fifteen years" span.

### PTC IS a PM receipt (Arpit's own account, 2026-08-02 — SUPERSEDES the "NOT a PM receipt" note)
The 2026-07-25 pass excluded PTC from the PM-receipts retitle. Arpit has now corrected that
first-hand, with the same scoping discipline as the PLG entry:
- **Ownership of the consolidation decision:** he DROVE it — built the case, defined what
  survives, sequenced the sunsets; PTC leadership's role was ratification. (The old "Shared:
  business-model decision w/ PTC leadership" recorded the ratification, not the driving.)
- **PM activities owned:** product definition of Learning Connector; the release roadmap —
  **quarterly, 2016–2019**; the 5→1 portfolio consolidation strategy; sunset management of the
  four legacy platforms.
- **Title:** the PTC seat is now **Product & Design Lead** (was "Lead Product Designer"),
  matching the DD/OrgOS convention. Locked in data/case-facts.js; every surface renders or is
  gated against that file.

### PTC migration + sunset receipts (2026-08-02, Arpit's account — NEW LOCKED FACTS)
- **150k active users migrated** onto Learning Connector over **24 months**, from the multiple
  legacy platforms. The consolidated platform ended up holding the 550k+ registered / 350k+
  active — so the existing locked numbers remain attached to Learning Connector honestly;
  **150k is the migration receipt** (users actually moved with their data), not a replacement
  for 550k+.
- **A single platform's full switch-off took six months.** Do NOT generalize to "each sunset
  took six months" — the confirmed fact is one platform (the four followed their own clocks
  inside the 24-month window).
- **Learning Connector is still live** at learningconnector.ptc.com under its own name —
  verified HTTP 200 on 2026-08-02, page title "PTC Learning Connector". A 2014–2019 product
  still in production in 2026 is a citable longevity receipt.

### PTC industry-context claim — what is and is NOT sourced (2026-08-02)
Arpit proposed "second best subscription transition after Adobe." His source
(charlenelower.medium.com, "Transition to SaaS with case studies of Autodesk and PTC") does
NOT say that — it never mentions Adobe. What it DOES support, and what surfaces may say,
cited: **PTC's company-wide subscription transition is documented as unusually smooth — no
revenue dip after the 2015 launch, unlike Autodesk's sharp dip.** Scope honestly: the article
is about PTC corporate (CAD/PLM), NOT PTC University; use it only as company-wide context
around the University's own 0% → 64%. The "after Adobe" ranking is QUARANTINED until a source
that actually says it appears.

### The gates, and the one that was missing (2026-08-02)
Four mechanical gates now guard the site. Each one exists because something specific escaped:
- **canon-lint** — a retired term ("trust layer") shipped on the book cover.
- **case-sync-check** — the book silently went stale against the classic case pages.
- **contrast-audit** — the book cover's CTA sat at 1.18:1 because style-based checks read the
  wrong ancestor for a gradient surface.
- **asset-load-check (NEW)** — the /process method diagram had been a BROKEN IMAGE on the live
  site. `assets/visuals/process-method.svg` carried a literal angle-bracket tag inside a CSS
  comment in its `<style>` block; that parses as markup, making the file invalid XML, and an
  SVG loaded through an `img` element must be valid XML or the browser refuses to paint it.
  naturalWidth was 0.

**The lesson worth keeping:** every gate before this one checked TEXT, CROSS-SURFACE AGREEMENT
or COLOUR. Not one asked whether a visual asset loaded at all. A broken asset also hides its
own second defect — because that SVG never rendered, its internal label collisions had never
been seen by anyone either.

**Two rules that follow, both now enforced:**
1. Never write a literal angle-bracket tag anywhere inside an SVG `<style>` block, even in a
   comment. The three process-method SVGs carry this warning in-file.
2. The pre-push hook and CI must trigger on `.svg` changes, not just html/css/js. Before
   2026-08-02 an SVG-only push skipped every gate — which is exactly how this reached prod.

Verified the way this repo requires: the gate was watched going RED against the real restored
defect (exit 1) and GREEN once fixed (exit 0), not merely reasoned about.

### Craft methods — the practice that was never written down (Arpit's account, 2026-08-02)
Audited 2026-08-02: the public site had ZERO occurrences of "user research", "journey map",
"service blueprint", "requirement" or "usability test". Six years of practice, invisible to any
screener grepping a JD's core requirements. Front-end coding was the exception — already
claimed across nine files and in the resume line "the interface I design is the front-end I
ship in the PR"; do NOT add more of it, it is covered.

Now licensed, per his own account:
- **Journey mapping and service blueprinting** — practised across the engagements: PTC, AdTech,
  OrgOS, O2, FinTech and VC diligence. AdTech and OrgOS are the most blueprint-shaped (a
  two-sided marketplace and an org operating system both have explicit front-stage/back-stage).
- **Usability testing** — a STANDING part of the loop on essentially every project, not an
  occasional event. Claim it as method. **Participant counts (Arpit, 2026-08-02): rounds of
  ~10 was his typical size, and the PTC blind-user study specifically was ~10.** Only "~10"/
  "about ten" may be printed, only for those two claims; every other count stays uninvented
  (trader-observation counts remain UNKNOWN).
- **Requirement gathering** — BOTH forms, depending on the client: PRDs/specs he owned and
  engineering built from, and backlog-native work (user stories, acceptance criteria,
  refinement with engineering). Pairs with the PTC roadmap ownership locked earlier today.

**SCOPING (corrected 2026-08-02):** service blueprints SURVIVE (PTC, AdTech, OrgOS, VC,
FinTech — Arpit keeps the files; interview-only, never published). Sketches, whiteboards and
rejected iterations still do not. So: methods are claimed as practice and evidenced by
decisions; the NDA walk-through offer may name service blueprints; nothing is ever linked,
hosted, or recreated as a placeholder.

**The decision-a-method-changed receipt (Arpit, 2026-08-02): the PTC accessibility rewrite WAS
the outcome of a usability study.** The verbose-ARIA approach was his own, shipped with textbook
confidence; a usability study with blind users overturned it (they skim by headings and
landmarks, they don't listen through sentences), and the front-end was re-written from what the
study showed. Every surface that tells the miss should NAME the method — "a usability study
with blind users", not just "I tested" — because that is the claim a screener greps for and the
story already proves it. Second receipt, already in canon: the AdTech live A/B that killed the
three-option recommendation card he had argued for. Both are method-changed-the-decision
stories; neither needs a participant count, and none may be invented.

### The Substack name — an OPEN DEPENDENCY on Arpit (2026-08-03)
The site calls the newsletter **"Human in the Loop"** in 15 places (homepage Writing header and
archive link, /writing, five case-study footers, /hire, llms.txt, the book). As of 2026-08-03
the publication's own metadata reads **"Arpit Maheshwari | Substack"** — verified by fetching
arpitmaheshwari.substack.com and reading og:title. So those 15 references currently describe a
brand that does not exist, and a reader who clicks lands somewhere named differently.

**Arpit's decision (2026-08-03): rename the SUBSTACK, not the site.** Set the publication name
to "Human in the Loop" in Substack settings. That makes all 15 references true at once and
unifies three things under one name — the newsletter, the book (*Human in the Loop, Vol. I*),
and the thesis the whole site argues.

**UNTIL HE DOES IT, THE SITE IS OVERCLAIMING.** Do not treat this as resolved because it was
decided; re-fetch og:title and confirm it reads "Human in the Loop" before calling it done. If
he decides against renaming, the fallback is to rewrite all 15 to "my Substack" / "More on
Substack" — the copy is ready, the decision is not reversed silently.

NOTE: "Human in the Loop" as the BOOK's title and as the site's thesis phrase is INDEPENDENT of
this and stays regardless — those uses were never in question.

### AdTech scale figure — CORRECTED 2026-08-03 (supersedes "$300M")
Arpit's correction: the platform's scale figure is **£400M in media spend transacted through
the platform** — not "$300M". Two things changed and both matter:
- **The number and currency.** $300M → £400M. The client is UK-based, so £ was always the
  right unit; the dollar figure was wrong on both counts.
- **What it MEASURES.** The old copy described the CLIENT ("a $300M media business" — the
  company's size). The correct claim describes THE SYSTEM HE DESIGNED: the media spend flowing
  through the platform. That is a stronger and more defensible claim in an interview, because
  it is about the thing he built rather than the size of who he built it for.

**Locked phrasing, use verbatim:** "a platform transacting £400M in media spend". Do NOT revert
to "media business", do NOT write "$400M", and do NOT describe it as the client's revenue —
that is a different (unrecorded) number and claiming it would be an overclaim.


### Module renamed: hitl.js → loop.js — 2026-08-04
Arpit's call, and the reason matters: *"You are using the abbreviation HITL everywhere, people
may confuse it with Hitler."* A hiring surface cannot carry an abbreviation with that misread.
- Renamed: `lab/hitl.js` → `lab/loop.js`, `hitl.test.js` → `loop.test.js`,
  `/lab/hitl.html` → `/lab/loop.html` (old URL kept as a noindex forwarding stub — it was
  published in the sitemap). CI workflow updated. All 42 tests pass under the new name.
- Copy: the boarding-pass airline is **"Loop Air"** (was "HITL Air" for one commit, never
  pushed); the human-in-loop pattern page spells the term out in full.
- Rule: do NOT write "HITL" on any visible surface. Spell out "human-in-the-loop", or say
  "the loop". The module is `loop.js`; docs may mention "formerly hitl.js" for continuity.


### AdTech — MAJOR CORRECTION + EXPANSION, 2026-08-05 (Arpit is the source; supersedes prior narrative)
**The false thread, removed: Act / Review / Ignore was NOT used in AdTech.** No confidence
score was ever shown — or used. The AI's raw output suggested LISTS OF BILLBOARDS; Arpit's
design recommended **detailed campaign plans with KPIs to measure ROI**, easily customizable by
the trader. The adoption fight was real and stays: traders overrode the RECOMMENDED PLANS, and
customization + visible KPIs/ROI is what earned adoption. Do not re-attach scores, verbs, or
"never a naked 87%" to this case on any surface.

**A/R/I's true origin (Arpit, 2026-08-05): a SYNTHESIS across the AI products — the pattern
kept recurring, then got named.** Never claim a single birthplace. The rule itself stands.

**Client context — REVENUE LEADS (supersedes the 2026-08-03 "media spend transacted" lock):**
the client is **the UK's largest out-of-home advertising company — £400M annual revenue, 40%
of the UK OOH market.** Arpit's explicit call to print despite near-identifiability (his
testimonials name Talon). For an aggregator, gross billings ≈ media spend transacted, so the
old phrasing was not false — but revenue now leads. Do not use both framings in one sentence.

**The platform's anatomy — five systems, all Arpit's product definition + design (2019–2025):**
1. **The aggregator** — positioned the client as a DSP: its own demand side (advertisers/
   agencies) and supply side (media owners), replacing phone calls and Excel sheets.
2. **The data-intelligence platform** — analyzed aggregate movement patterns to profile
   audiences, then profiled billboards against those audiences, targeting people precisely at
   the times they would be near a site. (Phrase as aggregate/audience-level; never as tracking
   individuals.)
3. **The creative management solution.**
4. **The advertisement display reporting system.**
5. **Free SaaS for media owners** — inventory management given away free; media owners share
   their inventory with the aggregator in return. (This is the supply-side PLG mechanism.)

**The transformation arc (the story the case now tells):** an advertising media agency became
the market's aggregator — an adtech company running the workflow end-to-end on one platform
instead of Excel sheets and phone calls.

**Standing numbers, unchanged:** 2 wks → 3 hrs · £69k avg media-value uplift/client · 45% ·
3x purchase intent · 70% audience uplift · 50M bids/hr (engineering's — attribute).

### AdTech tenure phrasing — corrected 2026-08-05
Arpit: *"It was not one product for five years, it was a suite of applications working together
as a smart connected platform."* Locked phrasing: **"one connected platform, five years"** (or
"a suite of applications working together as one connected platform"). Never "one product".
The five systems are enumerated in the 2026-08-05 AdTech correction entry above. Case vitals
Surface: "End-to-end aggregator · 5 systems".


### FinTech (AI-Assisted PE Investing) — EXPANSION, 2026-08-06 (Arpit is the source)
The product had three surfaces, not one — and served ONE analysis in TWO interpretation modes:
1. **The conversational interface** (already on record — cited claims, honest abstention).
2. **The scoring dashboard** — a MULTI-DEAL pipeline overview, deals scored side-by-side,
   sitting above the single-deal screen (the "Risk 62" card is the drill-down, not the whole).
3. **The AI-generated descriptive analysis** — the system wrote a detailed narrative report of
   the deal, scores explained in prose; the analyst reads it, then can interrogate it further
   in conversation.
**The design rationale (his, to print): different reading styles.** Some analysts want the
full written argument to read and annotate; others want to interrogate. The same analysis
served both temperaments — descriptive and conversational — instead of forcing one workflow.
Do not invent numbers for the dashboard or report (none provided).

**CORRECTION (same day): the "rejecting the chatbot" claim is RETIRED.** The published case
said "the first structural call was rejecting the chatbot… move from conversation to
conviction." Arpit's ruling: conversation was NEVER rejected — it was always one of the two
modes. The claim overstated and is corrected on every surface, like AdTech's scores were.
What stays true: the agentic architecture with strict operational boundaries (components as
an orchestra, not one improvising soloist), citations, and honest abstention.


### Due Diligence — "4 signal classes" RETIRED, 2026-08-06 (Arpit is the source)
Arpit challenged the provenance of "4 signal classes scored — architecture, code health,
team, delivery" (it traced to his early source documents, but he did not stand behind it) and
gave the true mechanics: **the AI analyzed a piece of information across 16 DIMENSIONS; only
when it had sufficient confidence did the finding count as a SIGNAL — each signal backed by
intelligence-verified evidence.** Locked framing: "16 dimensions of analysis · a finding
became a signal only at sufficient confidence · every signal carried verified evidence."
Never re-print the four class names — they are not attested. The "no uncited verdict reaches
a report" gate stays (unchanged, attested).


### PTC — perpetual share corrected + REAL IMAGES mandate, 2026-08-06 (Arpit is the source)
1. **"Perpetual was 60% of total revenue when I started" is WRONG — it was 100%.** All revenue
   was perpetual licenses at the start; the 0% → 64% subscription shift started from nothing.
   (The case body's "CRO had 60% of revenue sitting on perpetual licenses" is superseded by
   the same correction — use 100% / "all of it".)
2. **PTC is NOT under NDA — use REAL images from the public web.** The reconstruction plates
   ("screen contents synthetic") are to be replaced with real screenshots (Learning Connector
   is live at learningconnector.ptc.com; older portals via public record/archive where they
   survive). Captions must state the real provenance: URL + retrieval date. Where a real image
   genuinely cannot be recovered (dead pre-2019 portals), a reconstruction may remain but must
   say so.


### PTC — "38% mobile" and "Russian" RETIRED as session fabrications, 2026-08-06
Arpit: "Russian was not a supported language. The mobile usage increased because we made it
responsive. It was 4% in the beginning, but I don't have the latest number — where did you
get 38%?" The trail: NEITHER claim existed on the page before the 2026-05-24 "Phase 11"
session rewrite — both were AUTHORED THERE and inherited into canon. Fabricated, not sourced.
- **RETIRED:** the 38% endpoint, the "2017→2019" window built around it, and Russian as a
  supported/example language.
- **ATTESTED (Arpit, today):** mobile was 4% of sessions at the start; usage grew because the
  platform was MADE RESPONSIVE. No endpoint number may be printed until he provides one.
- **UNDER SUSPICION, same origin — RESOLVED 2026-08-06 (see next entry):** "80+ countries"
  corrected to **20+**; "99% automated pass" ATTESTED accurate by Arpit and kept.

### PTC — the "wrong homepage" story RETIRED; the real story is research, 2026-08-06
Arpit, on §the-cost: "That's not how it happened. I conducted research studies and usability
testing. A pattern emerged that people don't recognize offerings by the individual product
name but they call it PTC University."
The trail: the Pune engineer, "session length fell 19%", "+31% above baseline", and the whole
"I shipped the wrong homepage first" arc entered in `e20957e` (2026-05-24, the same Phase 11
fabrication session as the 38%). "Two lost reviews before the query log won the third" entered
in `3c706d5` (2026-06-26 structure roll) — also session-authored. ALL RETIRED; never reprint
the −19%/+31% pair, the Pune anecdote, or the shipped-wrong-first framing.
- **ATTESTED (Arpit):** research studies + usability testing found customers didn't recognize
  individual product names — they collectively called it **"PTC University."** That insight
  drove BOTH the consolidation under the PTC University name AND the license-keyed personalized
  homepage. The section is **metric-free** by his choice (consistent with the mobile rule:
  no number he can't stand behind).
- **ATTESTED (Arpit):** "99% automated test pass" is accurate — keep.
- **CORRECTED:** "80+ countries" → **"20+ countries"** ("also not an accurate number. safe
  side make it 20+"). Swept: ptc case, index receipt, resume, make-resume.js, portfolio PDF,
  video script.
- **Also removed same day:** the receipt's "added pt-BR, ko, ru" locale list — `ru` is Russian
  (retired 2026-08-06) and the 3-name list contradicts 9→11 anyway. Locale names are NOT canon;
  print only "9 → 11 locales" unless he supplies names.
- **Testimonial swap (his call):** Jonathan Berkey's quote replaced by Ryan Kershner's
  (verbatim from homepage) on the PTC case page.
- **Transfer note rewritten for plain English** (same facts: one year of runway + P&L-owning
  executives were preconditions; design necessary but not sufficient).

### Homepage — provenance tags and the early testimonial REJECTED, 2026-08-06
Both were built from an external review's suggestions and both were cut by Arpit on sight:
- **Per-metric provenance tags** ("Team outcome · I owned the plan UX, not the engine") —
  his verdict: **"nothing but noise."** The chips already carry baseline + window in
  `.proof-meta`, and each receipt already states ownership; a third label on the same object
  was redundancy, not clarity. Do not re-propose per-metric attribution badges.
- **A named testimonial placed above "Who you'd be hiring"** — cut. Testimonials stay in
  their own act. Do not move one above the fold.
The underlying review notes are logged, but these two executions are settled — reopening them
needs new evidence, not another reviewer repeating the suggestion.

### AdTech method diagrams shipped, 2026-08-07
Same treatment as FinTech, from attested mechanics only (plans-with-KPIs, one-click customize,
every edit logged, the five systems, the brief reframe). No client name, no scores anywhere.
- `assets/visuals/adtech-plan-not-pick.svg` — what the engine produced vs what the trader
  received, with the override loop. Footer states plainly: no confidence score ever reached a
  trader. ON: case page (under the-move), book mirror, portfolio PDF page 4 (45% width).
- `assets/visuals/adtech-two-sided.svg` — the five systems as a two-sided marketplace with
  audience intelligence between them. ON: case page (under the-platform), book mirror.
- `assets/visuals/adtech-brief-reframe.svg` — "a billboard on Oxford Street" becoming "reach
  party-lovers on Friday nights". ON: case page (at that paragraph), book mirror.
**Three traps hit, all measured not guessed:**
1. PDF page 4 is text-dense — at 74% the diagram overran the folio by a measured 11.9mm.
   Sized to 45% for 4.8mm clearance. FinTech's went 74% → 68% for the same reason.
2. A folio sweep across all 13 pages then found a PRE-EXISTING violation: the PTC plate
   (resized 2026-08-06) put its caption 3.9mm into the folio band. Plate 45% → 41%.
   All 13 pages now measure zero content in any folio band.
3. Six copies of the same inline figure style in the book mirror tripped the duplicate-signature
   gate, which correctly REFUSED to self-calibrate ("a check that cannot fail is not evidence").
   Extracted to `.nsb-fig`. The gate was right; the fix was the one it was built to force.

### FinTech method diagrams shipped, 2026-08-07 (Arpit picked all three)
The reviewers' one high-value, NDA-safe ask: show the AI depth as diagrams, not prose. Three
built from ATTESTED mechanics only — cited source per number, honest abstention, logged
override, two reading modes over a pipeline dashboard, Outlook entry, 60% pre/post.
No client name, no deal data, no sample size. Options kept at
`prototypes/fintech-method-diagram-options.html`.
- `assets/visuals/fintech-gate.svg` — the launch gate: two conditions + the failure each bought
- `assets/visuals/fintech-pipeline.svg` — the path a document takes, abstention as a real branch
- `assets/visuals/fintech-two-readers.svg` — one analysis, two readings, shared dashboard
SHIPPED ON: the case page (gate under "I held the launch", two-readers beside the modes
paragraph, pipeline before the product plate), the book's no-JS mirror (all three), and the
portfolio PDF page 6 (gate, at 74% width).
**NOT on the interactive book** — its spreads are fixed 880px with 4–34px headroom measured;
a figure clips. Needs a dedicated method spread, not a squeeze. Open item.
**NOT on the résumé** — it is text-only by design, 2pp, ATS-first.
**TWO TRAPS HIT AND FIXED, both worth remembering:**
1. `width:100%` on the PDF put the diagram + caption through the folio band and clipped the
   page number off entirely. Sized to 74%. Same layout contract as the case pages.
2. The SVGs used `ui-sans-serif, system-ui`, which resolves to macOS **San Francisco** — Chrome
   cannot embed it and emitted **31 Type 3 fonts** (baseline 1). Switched to the self-hosted
   `'IBM Plex Sans'`. **Never use a system-font stack in an SVG that a PDF will embed.**

### COVERAGE AUDIT — "what else isn't tested?", 2026-08-07 (Arpit's question)
Measured rather than recalled. Findings:
- **11 of 39 shipped pages had NEVER been contrast-checked** — the CI gate took a hand-typed
  list of 9 URLs. Unchecked: `lab/loop.html` (the largest Lab page), `lab/teardown.html`, all
  four `writing/` posts, all three `resources/` pages, and the two lab stubs.
  All nine real ones were then run: **1,110 text nodes, 0 failures.** No defect — but the gap
  was real and would have grown with every page added.
- **The asset gate had the same shape**: 16 hand-listed pages of 39.
- **`case-sync-check.py` covers `case-studies/` + `book/` only** — by design, but it means
  "in sync" never meant "the whole site agrees".
FIXED: both `contrast-audit.py` and `asset-load-check.py` now take `--all`, which enumerates
shipped pages from `git ls-files` (excluding prototypes/, assets/, portfolio-sources/). CI uses
`--all` for both; contrast timeout raised 25 → 45 min to fit 39 pages × 2 widths.
**The rule this generalises:** any gate whose scope is a typed list will silently stop covering
the site. Scope must be derived, and the derivation must fail loudly — see also
`tools/case-surface-inventory.py`.

### PROCESS RULE — a canon correction is not done until a tripwire ships with it, 2026-08-07
Arpit asked how the retired AdTech story survived multiple QA passes. The forensics:
1. **No enforcement shipped with the correction.** Canon was updated 2026-08-05 (709467c);
   the lint rule that could catch a score attributed to AdTech was added 2026-08-07. For two
   days the only thing preventing regression was memory.
2. **The sync gate is scoped to `case-studies/` + `book/` only** — it cannot see `patterns/`.
3. **The audit scopes I wrote excluded the files.** Both narrative audits were handed an
   explicit surface list naming `patterns/index.html` but not `patterns/*.html`, so they
   truthfully reported "patterns/ clean" after reading one file of ten.
Underneath all three: `patterns/` was filed as reference material. It is a CASE-FACT SURFACE —
nine pages, twenty links into real cases, each making a factual claim.
**THE RULES, from now on:**
- A correction lands in the same commit as the tripwire that enforces it. No tripwire, not done.
- When scoping any audit, use `tools/case-surface-inventory.py` to enumerate surfaces — never
  a hand-written list. That tool fails the build when a file makes case claims and no scope
  owns it (calibrated: it goes red on a planted unscoped page).

### Pattern library — pre-correction AdTech story found and purged, 2026-08-07
The 2026-08-05 AdTech correction (no confidence scores ever; A/R/I was a synthesis, never born
in AdTech) was applied to the case pages and documents but NOT to `patterns/`. Four pattern
pages still credited AdTech in their "See this pattern in action" lists with:
scores that told buyers what to do (`confidence-scores`), acting on "the score"
(`calibration-track-record`), "every call resolved to act, review, or ignore"
(`capability-contract`), and "the exact signals behind every recommendation"
(`ml-explainability`). All four rewritten to the attested story — plans with KPIs and the
reasoning printed on the plan. A PROXIMITY tripwire now guards it (bare "confidence score" is
legitimate on those pages; a score attached to *this client* is not).
**Lesson:** a canon correction must sweep `patterns/` too. It is a third surface family after
the cases and the documents, and it was missed for two days.

### Lab — evidence tiers added, 2026-08-07
The Lab is titled "proof" and shows a passing suite, which invites the fair objection that
tests prove code behaviour, not product outcomes. It now names three tiers explicitly —
**Implementation** (what the 42 assertions actually prove), **Usage** (the rules came from
shipped work; the code is his re-statement, not client source), **Outcome** (a claim about a
product, evidenced on the case with baseline and window, never by a green test). Also states
that thresholds are defaults, not findings. Same device as "Where this wouldn't transfer".

### PlanIt — deliberate asymmetry across surfaces, 2026-08-06 (Arpit's ruling)
An external review flagged "PDF has 7 cases, site has 6" as an inconsistency. **It is
intentional — Arpit: "keep it as is."** PlanIt is a full case in the portfolio PDF, a bullet on
the résumé, and absent from the website. The PDF is the long-form artifact and can carry it;
the site's Selected Work stays at six. Do not "reconcile" this.

### Positioning language — "design system" retired for the pattern work, 2026-08-06
Calling the eight patterns "the design system for trusting and governing AI agents" invites an
easy attack (a design system implies components, tokens, versioning, contribution workflow,
adoption measurement — none of which are claimed). Locked replacement: **"a working system for
trusting and governing AI agents — one decision grammar (Act / Review / Ignore), eight
interaction patterns, and a tested implementation."** Swept: patterns/index.html,
book/portfolio.js, resume, make-resume.js, portfolio PDF.

### PTC clientele — the list standardized, 2026-08-06 (Arpit is the source)
The client names had FIVE different variants across surfaces (homepage/hire/book/resume/PDF)
and appeared nowhere in canon. Arpit's ruling: **all five names are real and defensible.**
- **LOCKED ORDER, every surface:** NASA, Boeing, Toyota, Airbus and Apple.
  (Ampersand form "NASA, Boeing, Toyota, Airbus & Apple" where space is tight.)
- Never drop a name to fit, and never reorder — an inconsistent client list reads as guessing.

### VC Diligence — the four named signals REMOVED, redesign chosen, 2026-08-06
The QA sweep found the retired four-class taxonomy was not just prose: it was the spine of the
case's SVG diagram, its plate mockup, its widget buttons, its alt text and its aria-label.
Prose/data/mirror have been purged (`data/case-facts.js`, `book/*`, `llms.txt`, the receipt row,
the role line, the figcaption). **Arpit's ruling on the artifacts: redesign around the
CONFIDENCE GATE** — drop named signals entirely and demonstrate the attested mechanic instead
(a finding analyzed across 16 dimensions; it becomes a signal only on clearing a confidence
bar; every signal carries verified evidence; no uncited verdict reaches a report). **RESOLVED same day — Arpit picked Direction C, "the evidence trail"** (options rendered at
`prototypes/vc-confidence-gate-options.html`, kept as the record).
- **SHIPPED:** signals are anonymized IDs carrying a confidence value (Signal A-14 / B-02 /
  C-09 / D-05) — never a named risk taxonomy. Each opens to the evidence it was verified
  against. Every surface states the gate: "analyzed across 16 dimensions · 12 further findings
  stayed below the confidence bar and never reached the report." Partner sign-off still unlocks
  only after every trail is opened (attested, unchanged).
- Rebuilt: the `recon-vc` widget, the `plV` plate rows, `assets/visuals/case-vc.svg` (now
  "Evidence → signal → verdict", with the confidence bar drawn as a marked threshold), the
  image alt text, the plate aria-label, the role line and the body prose.
- The IDs and their evidence lines are ILLUSTRATIVE and captioned as a reconstruction. They
  assert no taxonomy — that is the whole point of the redesign. Do not "improve" them into
  category names; that is how the retired four came back.

### O2 / MyO2 — the replatforming story added, 2026-08-06 (Arpit is the source)
Arpit: "myo2 case study is an example where we took a legacy system and made it responsive
across iOS android Microsoft phone and web. Telefonica has millions of active subscriber so
transition was cautious. Also work closely with Telefonica branding marketing and copywriting
team."
- **ATTESTED:** MyO2 was a replatforming of a LEGACY system into one responsive build serving
  iOS, Android, Windows Phone, and desktop web (not "mobile web" alone).
- **ATTESTED:** millions of active subscribers on the legacy system → the transition was
  deliberately cautious. (No rollout mechanics — staging, flags, timelines — may be invented.)
- **ATTESTED:** close collaboration with Telefónica's branding, marketing, and copywriting
  teams.
- **SCOPE (his ruling, same day): MyO2 ONLY.** Priority Moments stays described as app +
  mobile web; the joint phrase "two O2 UK products on mobile web" stays as-is. Do NOT extend
  the responsive/replatforming framing to Priority Moments.

### AdTech — PRIMARY SOURCE acquired: the client's published case study, 2026-08-06
Digital Bulletin, Issue 30, "An Out of Home Evolution" (July 5, 2021) — a published magazine
feature on the client's transformation, naming the client (Talon Outdoor), the partner (Sahaj
Software Solutions), and the platforms (Ada = data management, Plato = trading, Atlas =
programmatic DOOH). Screenshots archived in the PRIVATE repo: `portfolio-sources/talon-article-2021/`.
Live at digitalbulletin.com (/CaseStudies/Technology/2021/July/talon-outdoor/) and on Medium;
YouTube film exists. Verified live 2026-08-06.
- **HIS RULING: the site stays FULLY ANONYMIZED.** Never print Talon / Sahaj / Ada / Plato /
  Atlas on any public surface. Consequence: the article is never linked or named on the site
  (the link de-anonymizes in one click) — on-page attribution is "the client's leadership, in
  a published industry case study," and the case says he'll hand the source over in
  conversation. The article is interview ammunition and a private receipt.
- **HIS ROLE (his words, same day):** "I designed the entire suite of a smart connected
  platforms, along with the supporting platforms for media owner inventory, advertising
  creative copy management, advertisement display consolidation, reporting, mobile web for ad
  booking and others, over the five years" — all three named platforms plus the supporting
  systems.
- **NEW ATTRIBUTED PUBLIC METRICS (always the client's claims, NEVER his KPIs; his ruling:
  use all, keep the existing metrics too):** 53% consideration uplift vs standard OOH
  (Product Strategy Director) · under 5% → 100% of UK bookings through the trading platform
  (Chief Product Officer) · "The things that would normally take us 12-18 months to build,
  were built in six months" (Chief Transformation Officer, verbatim — contains no names) ·
  48 sheets availability lookup: three days → 30 seconds (their example) · programmatic
  platform revenue one month after launch · "clients only pay for confirmed impressions".
  Quote rule: quotation marks ONLY around article sentences containing no client/platform
  names; anything naming Ada/Plato/Atlas is paraphrased, never quote-edited.
- Article corroborates existing canon: partner engaged after 2018 CTO hire; Plato MVP in
  four months; "best OOH data management platform in the UK, if not the world" (their claim).

### O2 — "every screen drawn by me" corrected: design was shared, code was solo, 2026-08-06
Arpit: "Not every screen was designed by me, I had a co-designer, but every screen was coded
by me." The site's signature O2 line ("Every screen drawn by me, then coded by me") overclaimed
the design half. RETIRED on all surfaces (case hero/gate/standfirst/receipt/honest-line/meta,
homepage receipt + card + proof chip, book x5, portfolio PDF title/TOC/body).
- **Canonical formula:** every screen designed WITH ONE CO-DESIGNER; every screen / all
  front-end CODED BY HIM ALONE. The solo claim attaches to the CODE only.
- The co-designer is unnamed (he hasn't named them — do not invent a name or split of work).
- **Same day, ATTESTED:** Priority Moments used GEOLOCATION to show a list of offers in the
  nearby area — the mechanism behind retention and loyalty. (Narrated on the case's Priority
  card paragraph, 2026-08-06.)

## 2026-08-07 — Method diagrams for OrgOS, PTC, O2, VC (shipped) + a PDF legibility finding

Five diagrams shipped to the **case pages and the book's no-JS mirror**:
`orgos-said-no` (the assign/approve/escalate refusal → visibility), `ptc-switch-off-ladder`,
`ptc-funnel` (0% → 64%), `o2-replatforming` (one build, four surfaces), `vc-signoff`
(sign-off locked until every evidence trail is opened). Every element attested; no rollout
staging invented for O2, no governance mechanics invented for OrgOS, no VC taxonomy printed.

**NOT in the portfolio PDF — measured, not assumed.** These diagrams are drawn on a 1180-unit
viewBox for a full web column. On a 170mm A4 page their smallest labels render at **2.8–4.5pt**
against a document minimum of 7.4pt: unreadable. The four case pages (08–11) also have only
2–6mm of folio headroom, so a taller print redraw does not fit either. Adding them would have
replaced readable prose with grey smudges.

**RESOLVED same day — both PDF figures redrawn for print.** `fintech-gate-print.svg` (600x134)
and `adtech-plan-not-pick-print.svg` (600x98) replace the web drawings in the PDF only; the web
originals stay on the case pages and in the book, where they are read at full column width.
Measured after the swap: smallest label **8.0pt** (was 1.8 and 3.1), both figures at the full
170mm column, both pages at 6.4mm folio clearance. The duplicated captions beneath them were
removed — a print figure carries its own headline, so the caption was a double ending.

**RULE (new):** a diagram bound for the PDF must be measured in **points at its rendered page
width** before it ships, not merely checked for folio clearance. Clearing the folio band and
being legible are two different gates.

## 2026-08-08 — Positioning + bounded claims (ChatGPT review #4, Arpit ruled on all four)

**Role positioning (SUPERSEDES "Founding / Staff / Director" as equal targets).** Canonical line:
**"Staff / Principal or founding product-design lead — open to hands-on Director roles."**
Rationale accepted from review: the evidence supports Staff/Principal and founding strongly;
Director-scale people-management evidence (managing managers, budget, org design) is not on the
record, so Director is stated as secondary and hands-on. Applies to: Classic contact, Book cover,
Book status list, Book contact prose, portfolio PDF contact.

**Bounded claims (all four reworded, Arpit's explicit pick "All four, everywhere"):**
1. "Every one of them runs the same four beats" → the four beats are the lens for the AI cases;
   the earlier work (PTC, O2) shows the range that led there. Never reprint the universal form.
2. "The contract behind every screen I ship" → "the contract I write when a capability needs
   an explicit boundary." The absolute was indefensible across 15 years of screens.
3. Act/Review/Ignore universality ("every confidence surface … exactly one of three verbs") →
   observed grammar, not law: outputs should resolve to an explicit next state; in shipped work
   three verbs covered the production cases.
4. "Three things I'll refuse" → "Three risks I won't let a team discover in production."
   List items unchanged (each is evidence-backed); only the combative frame goes.

**Review fact-check (recorded so nobody re-litigates):** review #4 quoted two claims that do NOT
exist on the shipped site — "80+ countries" (site says 20+ everywhere; the review's own fix would
have RE-PRINTED the banned figure) and "every screen drawn by me" (site says co-designed
everywhere). It also asked for system-evidence diagrams that shipped this week. Reviewer was
reading a stale copy; always fact-check a pasted review against the live files before executing.

**Hero — RESOLVED 2026-08-08, Arpit picked Option C (readdressed) from three rendered options.**
The diagnostic stays as the hero rail. Its tag now reads "Building AI? — name your problem" and a
one-line escape sits under the free-text input: "Hiring? Skip this — see the strongest work →"
(data-cta="skip-diagnostic"). Options A (evidence rail) and B (two doors) live in
prototypes/hero-option-{a,b}.html as archived rejected directions — do not ship them.

**Open (Arpit said yes, pending his input):** "what I got wrong" rows on 2-3 more cases —
the misses MUST come from Arpit, never invented.

## 2026-08-08 — Homepage scan-layer options (Krishanth/Zalzberg reference review) — Arpit's ruling: none shipped

Reviewed two external portfolios on Arpit's request: sreekrishanth.in (fast-scan maker portfolio —
face at scale, glanceable case index, no business outcomes — praised for pacing, discounted for
having zero verifiable evidence) and shirzalzberg.com (strong third-party institutional proof —
Forbes 30u30, talks, press — praised for warmth and external validation, discounted for illegible
type and no scoped outcomes).

Three options were rendered from the live homepage and archived as reference, per Arpit's explicit
instruction — **NONE shipped, all three held as future reference only:**
- `prototypes/scan-option-1-face.html` — 56px avatar chip → 150x190 grayscale portrait
- `prototypes/scan-option-2-index.html` — six case cards → six scannable index rows (name + metric,
  paragraphs dropped to the case pages)
- `prototypes/scan-option-3-human.html` — S1's portrait + Anant East's letter pulled up to a
  centered pull-quote right after the receipts, plus an "Elsewhere" line (Substack/LinkedIn/Lab)

**RULE:** these three files are archived prototypes, allowlisted like every other rejected
direction in prototypes/ — do not resurrect or ship without a fresh explicit instruction, and do
not let canon-lint or case-sync flag them as drift.

## 2026-08-08 — Production-readiness QA sweep (website + book + both documents)

**Bounded-claim propagation was INCOMPLETE.** The 2026-08-08 bounding pass fixed the homepage,
book, /hire and patterns/index.html but MISSED four surfaces carrying the same universal claim:
- `patterns/act-review-ignore.html` — the rule's OWN page, in 6 places (meta description, twitter
  card, JSON-LD, lead paragraph, and two body sentences). Same failure class as the 2026-08-05
  pattern-library miss: the audit named `index.html`, not `*.html`.
- `portfolio-sources/resume.html` — "every model score and agent action resolves to one verb"
- `portfolio-sources/portfolio.html` — "every score resolves to Act, Review, or Ignore" and
  "every score lands on exactly one verb"
All bounded. **RULE: a claim-bounding pass must end with a WRAP-TOLERANT regex sweep across every
surface INCLUDING both documents — an exact-phrase grep misses line-wrapped and letter-spaced text.**

**Book cover contradicted the bounded narrative.** `book/portfolio.js` said "6 AI case studies
inside" while the site now states only the first three are AI. Corrected to "6 case studies";
portfolio.js bumped to v=131.

**Gate interference bug found and fixed.** `contrast-audit.py` writes its canary to a temp file
INSIDE the docroot (`__ca_*.html`, required for same-origin instrumentation).
`inline-style-check.py` was scanning it and reporting a phantom 6px off-grid failure in code that
does not exist. Fixed by excluding `__ca_*` from the style gate's file list, then calibrated:
temp file present -> clean; real planted 7px -> RED; restored -> clean.

**Verified this pass:** all 5 static gates green (each self-calibrated); portfolio PDF 13pp and
resume 2pp unchanged; Type 3 = 1 (the documented ghost numeral) and 0 respectively; both print
diagrams legible at 150dpi in the real PDF; contrast 0 failures across 1,171 text nodes at
1440/1024/768; no banned token in either document's text layer.

**KNOWN OPEN (not a defect, needs Arpit's ruling):** the homepage case cards still show the
score-doubt-action-impact tracker on PTC, O2 and OrgOS, while the section prose now says those
cases "are read on their own terms". Prose and card labels disagree.

## 2026-08-08 — Case-study section relaid out as the S2 index (Arpit's pick)

`prototypes/scan-option-2-index.html` (S2, the Krishanth-derived scan layer, previously archived
as "reviewed, none shipped") was **recalled and SHIPPED** to the homepage case section.

Six cards -> six scannable rows. Left rail carries BOTH identifiers, stacked: **industry**
(`.ai-case-kick`) above the **metric** (`.ai-case-num`) — Arpit asked explicitly for the industry
to be kept. Case name in display type at clamp(26px,3vw,42px), walk-through right. Row direction
flips to column at <=860px, where industry and metric sit on one line.

**The per-card prose and the beat tracker are now hidden** (`.ai-case>p,.ai-case .beats,
.ai-case .beat-lbl{display:none}`) — the paragraphs live on the case pages, where they always
read better. **This also RESOLVES the open contradiction logged in the 2026-08-08 QA sweep:**
the section prose said PTC and O2 "are read on their own terms" while their cards still carried
the score-doubt-action-impact tracker. No card carries it now.

**Two things the layout change broke, caught on render and fixed:**
1. The section eyebrow read "How to read the six cases below" and the aria-label described the
   beat notation — a reading key for a notation the index no longer displays. Reframed to
   "The method behind the AI cases"; the four-beats statement and its flow diagram still stand.
2. The prototype CSS was never grid-snapped (it was a quick overlay): 30/6/10/22/14px all failed
   the spacing gate. Snapped to 32/8/12/24/16px. **RULE: a prototype's CSS is a sketch — snap it
   to the design grid before it ships, and expect the style gate to catch it if you don't.**

Rules were REWRITTEN in place, not layered as `!important` overrides. styles.css -> v=p63.
