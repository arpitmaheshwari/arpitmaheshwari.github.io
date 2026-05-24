# Portfolio Revamp & Conversion Optimization Roadmap

This roadmap translates our comprehensive strategic audit into an actionable, prioritized execution plan to maximize visibility, clean up your content hierarchy, optimize CTAs, and convert Series Seed-B founders.

---

## 1. The Core Brand Narrative Audit
Your current positioning as a **"Founding Designer for AI Products"** focusing on **"Designing for Distrust, Trust Second"** is exceptionally strong and highly differentiated. The "Act I, Act II" case study structure reads beautifully—like a high-end design journal rather than a generic portfolio.

### Opportunities for Narrative Polish:
*   **Cognitive Load:** The reading flow is frequently broken by excessive `<abbr>` tags (dotted underlines). While useful, these create a high reading friction, particularly on mobile touch targets.
*   **Visual Pacing:** The editorial Acts have excellent narratives but need more visual breaks (white space, inline pull quotes, and interactive intermissions) to break up dense walls of text.

---

## 2. Content Hierarchy Optimization Plan

### A. The Homepage (`index.html`)
The homepage currently features 12 distinct sections. While thorough, it creates scroll fatigue. We want to consolidate it into a streamlined, high-converting flow:

*   [ ] **Action 1: Merge Thesis (§05) & Philosophy (§07)**
    *   *Why:* Both cover identical conceptual ground. Merge them into a single, punchy **"Design Manifesto"** section that outlines your stance on "distrust-first" and failure states.
*   [ ] **Action 2: Merge How I Work (§08), Process (§09) & Skills**
    *   *Why:* These are currently spread out. Combine them into an **"Engagement Blueprint"** section that incorporates:
        *   The interactive Confidence Widget (your proof-of-code).
        *   Your 6-week engagement timeline.
        *   Your timezone-flexibility and remote workflow tools.
*   [ ] **Action 3: Reposition Testimonials (§06)**
    *   *Why:* Social proof is currently buried near the bottom. Move the "Voices" section to sit immediately below your **Selected Work** section to validate your case studies instantly.

### B. Case Study Pages (`case-studies/*.html`)
*   [ ] **Action 1: Subtly Embed the Mid-Article CTA**
    *   *Why:* The boxy, explicit "Book a 30-min call" banner in the middle of Act III/IV breaks the immersion of your storytelling. 
    *   *How:* Convert it into a beautifully integrated, styled text-link or pull-quote style card instead of an aggressive sales banner.
*   [ ] **Action 2: Fluid-Grid Refactor for HTML Wireframes**
    *   *Why:* Wireframe boxes (like the "Contextual Override" diagram) use absolute widths (`width: 150px`, etc.) which break or wrap awkwardly on mobile viewports.
    *   *How:* Refactor the inline-styles to use modern CSS Flexbox and Grid with fluid percentages.

### C. Design Pattern Library (`patterns/*.html`)
*   [ ] **Action 1: Convert Tables to Responsive Cards on Mobile**
    *   *Why:* The pattern trade-off matrices use standard `<table>` elements with `overflow-x: auto`. Scrolling sideways on mobile is poor UX.
    *   *How:* Use CSS media queries to hide tables and display a clean stack of grid cards on screens below 768px.

---

## 3. Call-to-Action (CTA) Strategy Refinement

### The Problem: The "Calendly Monopoly"
Almost every CTA button across all 15 pages redirects to a single Calendly booking link. Booking a live, synchronous 30-minute meeting is a **high-friction action** for passive, late-night visitors.

```
[ High Friction ]  --> "Book a 30-Min Zoom Call" (Calendly)
[ Low Friction  ]  --> "Asynchronous UI Teardown" OR "Download Handbook PDF"
```

### The Solution: Introduce a "Middle-of-Funnel" (MoFu) CTA
*   [ ] **Action 1: Add a Low-Friction Async CTA**
    *   Offer a secondary button next to your primary booking CTA: **"Get a 5-Min Video Teardown of Your AI Interface"**.
    *   *Mechanic:* Users fill out a 2-field form (Email + Link/Screenshot of their UI). You send them a quick Loom pointing out 2-3 UX wins. This proves your expertise immediately and converts at a much higher rate.
*   [ ] **Action 2: Context-Aware CTA Labels**
    *   Instead of generic "Book a call" buttons in the footer of every case study, align the labels to the specific work:
        *   On `fintech.html`: *“Review your FinTech AI interface with me ↗”*
        *   On `adtech.html`: *“Optimize your AdTech dashboard ↗”*
        *   On Pattern pages: *“Apply this pattern to your product ↗”* (Currently looks great on some pages, should be unified).

---

## 4. Phase-by-Phase Execution Plan

### Phase 1: Clean Wins & Info Architecture (1-2 Days)
*   [ ] Remove high-frequency `<abbr>` tags or transition them to tap-to-expand inline notes for mobile.
*   [ ] Move the "Voices" (Testimonials) section on the homepage directly under Selected Work.
*   [ ] Merge "Thesis" and "Philosophy" into a unified "Design Manifesto" section.

### Phase 2: Visual and Mobile Polish (3-5 Days)
*   [ ] Refactor all hardcoded HTML wireframe widths in case studies to use fluid Flexbox styles.
*   [ ] Apply responsive CSS overrides to the patterns tables, turning them into readable text cards on mobile screens.
*   [ ] Refine line heights and margins on mobile headings to improve readable rhythm.

### Phase 3: Conversions & CTA Upgrades (2 Days)
*   [ ] Integrate the low-friction **Asynchronous Teardown** form option next to the primary Calendly CTAs.
*   [ ] Rewrite CTA copy in all footers to match the contextual pages (FinTech, AdTech, Telecom, etc.).
*   [ ] Retarget the exit-intent popup to serve this low-friction offer instead of just a passive newsletter subscription.
