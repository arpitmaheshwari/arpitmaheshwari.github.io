# Portfolio Revamp Roadmap

This roadmap translates the growth analysis into an actionable, prioritized execution plan to maximize visibility and conversion for Series Seed-B roles.

---

## Phase 1: Quick Wins & Information Architecture
**Goal:** Improve navigation, reduce cognitive load, and highlight the strongest inbound assets.
**Timeline:** 1-2 Days

- [ ] **Elevate the Patterns Library:**
  - Move the "AI Design Patterns Library" section from the bottom of `index.html` to sit immediately below the Hero section or right after the Case Studies.
  - Frame it as your primary value proposition ("The definitive guide to AI UX").
- [ ] **Elevate Newsletter Capture:**
  - Move the Substack email capture form out of the Contact footer.
  - Place a soft capture banner near the Patterns Library ("Get 1 AI UX pattern in your inbox every month").
- [ ] **Positioning Tweak:**
  - Update the Hero H1/H2 to lead strongly with "Founding Designer" while keeping "Staff-level expertise" as a descriptor of quality, clarifying your target ICP.
- [ ] **Reading Mode (Accessibility):**
  - Implement a CSS toggle for a "Light Mode" specifically tailored for long-form reading in the case studies and patterns to reduce eye strain.

---

## Phase 2: Visual Evidence (Breaking the "Wall of Text")
**Goal:** Address the lack of visual artifacts in the case studies without violating NDAs.
**Timeline:** 1 Week

- [ ] **Abstract UI Diagrams for AdTech Case Study:**
  - Design 2-3 "clean room" wireframes or abstract UI diagrams (using Figma) that show the *structure* of your solution.
  - E.g., An abstract diagram showing the "Confidence Score" placement relative to the "Why" reasoning section.
  - Embed these into `adtech.html`.
- [ ] **Abstract UI Diagrams for FinTech Case Study:**
  - Create abstract wireframes showing the "Comparative Context" UI and the "Respectful Override" interaction.
  - Embed these into `fintech.html`.
- [ ] **Formatting Upgrades:**
  - Break up long paragraphs in all case studies using pull-quotes, callout boxes for key insights, and bulleted lists.

---

## Phase 3: Interactive Proof
**Goal:** Prove the "I code in HTML/CSS/JS" claim instantly to technical founders.
**Timeline:** 3-5 Days

- [ ] **Build a Live UI Component:**
  - Develop a standalone, interactive "Confidence Score" UI component using vanilla HTML/CSS/JS.
  - It should demonstrate a hover state that reveals the "Why?" (explainability pattern).
- [ ] **Embed on Homepage:**
  - Embed this component (via iframe or direct code) directly on `index.html` within the "How I Work" or "Patterns" section.
  - Let founders click and interact with it to immediately validate your technical prototyping skills.

---

## Phase 4: Growth, SEO & Distribution
**Goal:** Drive inbound footfall and build an audience.
**Timeline:** Ongoing

- [ ] **Productize the Patterns Library:**
  - Compile the existing patterns into a single downloadable PDF or a dedicated standalone landing page (e.g., "The AI UX Pattern Handbook").
- [ ] **SEO Optimization:**
  - Update meta titles and descriptions on the pattern pages (`confidence-scores.html`, `ai-failure-states.html`) to target high-intent, long-tail keywords (e.g., "How to design AI confidence scores").
- [ ] **Launch Strategy:**
  - Launch the packaged Patterns Library on Product Hunt, Hacker News, and Designer News.
- [ ] **LinkedIn Content Flywheel:**
  - Repurpose the "AI Failure States" pattern into a 5-slide LinkedIn carousel.
  - Post with a CTA driving traffic back to the specific pattern page on your portfolio.
