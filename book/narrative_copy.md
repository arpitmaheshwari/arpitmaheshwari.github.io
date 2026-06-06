# The "Business-Minded Designer" Narrative Framework

This narrative strategy is designed for the "Working Book" theme. It shifts the focus from "look at my pretty screens" to "look at how I solve expensive business problems." 

By following this framework, any designer using your theme will position themselves as a high-impact, senior-level thinker that hiring managers trust.

---

## 1. The Cover & Spine (The Hook)

**The Strategy:** Don't use a generic job title. State your niche, your tenure, and the specific value you bring. 

**Template:** 
`[Years of experience] designing [what you design] for [target audience/industry].`

**Examples to use in `portfolio.js` (`Title / Description`):**
*   *Product Growth:* "Eight years designing the activation layer for B2B SaaS products. Selected work, conversion patterns, and the cutting-room floor."
*   *Enterprise:* "A decade of untangling enterprise complexity. How I turn legacy workflows into competitive advantages."
*   *Generalist:* "Ten years bridging the gap between engineering constraints and human behavior."

---

## 2. Selected Work / Case Studies (The Evidence)

**The Strategy:** Hiring managers skim. Skip the long-winded "My Role" and "Design Thinking Process" intros. Get straight to the **Tension**, the **Decision**, and the **Outcome**. 

### The Case Study Arc

*   **The Standfirst (TL;DR):** 1-2 sentences summarizing the impossible situation and what you did.
*   **The Context:** What was broken? Why couldn't it be solved with just "better UI"?
*   **The Tension:** The political, technical, or business roadblock that made this hard. *(e.g., "Every feature request carried a hidden agenda.")*
*   **The Moves (Decisions):** 3 load-bearing decisions you made. Frame them as strategic choices, not UI updates.
*   **The Ledger (Outcomes):** Hard numbers. Time saved, revenue gained, clicks reduced.

**Example Copy for a Case Study (`portfolio.js > CASES`):**

```javascript
{
  title: "The Legacy System Migration",
  standfirst: "A ten-year-old codebase, three angry enterprise clients, and a timeline of six months. We rebuilt the plane while it was flying.",
  context: "The core product was a maze of technical debt. Sales were stalling because the UI looked like 1998, but engineering couldn't touch the front-end without breaking the backend. The prompt was 'refresh the CSS'. The real job was decoupling the architecture.",
  tension: "We had to ship visible progress to appease the board, but the real work was invisible. If we only painted the surface, it would collapse in a year.",
  decisionLede: "Three decisions kept the project alive:",
  moves: [
    {
      h: "A shadow design system",
      p: "I built a parallel component library that engineering could adopt piece-by-piece, without a massive 'big bang' release."
    },
    {
      h: "Kill the sacred cows",
      p: "Identified and removed 40% of legacy features that accounted for 2% of usage, saving months of engineering migration time."
    },
    {
      h: "Design for the API, not the screen",
      p: "Structured the new UI around the new data models, forcing a cleaner separation of concerns."
    }
  ],
  outcome: [
    { v: "6 Mo", l: "Time to market" },
    { v: "-40%", l: "Feature bloat removed" },
    { v: "$2M", l: "Saved in engineering time" }
  ]
}
```

---

## 3. Principles / How I Lead (The Mindset)

**The Strategy:** Show how you approach the work when things get messy. Avoid generic fluff like "I am empathetic." Instead, make declarative statements about your professional boundaries and methodologies.

**Example Copy (`portfolio.js > PRINCIPLES`):**

```javascript
[
  {
    h: "I design the wrong-answer screen first.",
    p: "If I don't know how the system fails gracefully, the happy path doesn't matter. Trust is built in the error states."
  },
  {
    h: "The org chart is the hardest wireframe.",
    p: "Most UX problems are actually just symptoms of misaligned internal teams. I design for the organization before I design the interface."
  },
  {
    h: "Writing is my primary design tool.",
    p: "I write down the logic, the constraints, and the trade-offs before opening Figma. If it doesn't work in plain text, a drop-shadow won't save it."
  }
]
```

---

## 4. The Field Guide / Patterns (The Playbook)

**The Strategy:** Show that you don't just solve problems once—you extract repeatable systems. This proves you are a force multiplier for the whole team.

**Example Copy (`portfolio.js > PATTERN_PAGES`):**

```javascript
{
  h: "Friction as a Feature",
  principle: "Sometimes the user needs to slow down.",
  def: "The deliberate introduction of UI friction to prevent destructive actions, force cognitive engagement, or build perceived value.",
  dos: [
    "Use friction when the cost of an error is high (e.g., deleting a database).",
    "Add 'artificial waiting' to make complex algorithms feel like they are working hard.",
  ],
  donts: [
    "Don't add friction to high-frequency, low-risk daily habits.",
    "Don't confuse dark patterns with helpful friction."
  ]
}
```

---

## 5. The Cutting-Room Floor (Vulnerability)

**The Strategy:** Junior designers hide their mistakes. Senior designers document them. Showing what you tried and killed proves you are driven by reality, not ego.

**Example Copy (`portfolio.js > FLOOR`):**

```javascript
[
  {
    tag: "E-commerce",
    h: "The Mega-Menu",
    p: "Looked gorgeous in Figma. Tested terribly. Users couldn't find the search bar. Killed it after one sprint."
  },
  {
    tag: "Onboarding",
    h: "The 10-Step Wizard",
    p: "Tried to gather all user data upfront. Conversion dropped 30%. Replaced it with progressive profiling."
  }
]
```

---

## How to use this template

To implement this narrative, designers simply need to:
1. Open `portfolio.js` (or their source `.jsx` file).
2. Locate the corresponding arrays (`WORK`, `PRINCIPLES`, `CASES`, `FLOOR`).
3. Replace the text using the structural templates above.
4. Focus on **verbs, metrics, and tension** rather than adjectives and lists of tools.
