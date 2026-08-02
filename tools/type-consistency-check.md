# Component-level type consistency — the check the first typography review missed

**Date recorded: 2026-08-02, after Arpit caught two identically-classed `<dl>` lists rendering
differently in one section — gold serif terms in one, ink terms + muted bodies in the other.**

## Why the first review failed
The font census measured GLOBAL style diversity (how many family/size/weight combos exist per
page) and checked each against the scale. Every style in the broken screenshot was scale-legal.
The failure was RELATIONAL: the same component, styled twice. A census cannot see that; only a
per-component cross-instance diff can.

## The method (Playwright, in-browser)
For each repeated component selector (dt, dd, blockquote, figcaption, h2.section-title, h3,
.case-stat b/span, cite), group instances by computed signature
(family|size|weight|style|color) and report any selector with >1 group.

## Known false positives — read before acting on output
1. **Cream-act sections re-point colour tokens BY DESIGN** — section-titles legitimately render
   dark-on-cream there. Same size+family+weight, different colour = check the section first.
2. **Container-style ghosts**: a figcaption/blockquote whose text lives entirely in styled
   spans reports the CONTAINER's unused computed style. Measure the first rendered TEXT NODE's
   parent, not the element.
3. **/folio/ is a 39-line redirect stub** — it forwards to /, so any check on it double-counts
   the homepage.
4. **Distinct components sharing a tag**: a testimonial's serif attribution and a plate's mono
   caption are both <figcaption> but are different components. Judge by role, not tag alone.

## The fix pattern
When two instances of one component diverge: define the component ONCE in styles.css and strip
every inline copy (the 2026-08-02 fix moved .lead-dl dt/dd into the stylesheet and reduced 12
inline style attributes to zero). Inline-duplicated component styles are where drift breeds.

## Root cause to avoid repeating
Inline styles on repeated components = each instance is a fork waiting to drift. New repeated
component → class in styles.css, no exceptions.

---

## Round 2 (2026-08-02, same day) — the census was still too narrow

Arpit rejected round 1: "look at the case study pages, pattern pages, other standalone pages,
and you will still see a lot of font patterns." He was right again. Round 1 diffed 8 selectors
WITHIN single pages. It never looked ACROSS pages, and never at the actual disease.

### What a complete audit has to measure
1. **Static**: every inline `font-*` declaration in every HTML file. (Found: 1,231 across 28
   files; 562 belonged to repeated signatures = unnamed components.)
2. **Repeated inline signatures**: the same style string written N times = a component nobody
   named. Fix by defining it once in CSS.
3. **Cross-page rendered census, by ROLE not tag**: group every mono-uppercase label across ALL
   pages by computed `size/weight/letter-spacing`. Found **27 treatments** for one component.
4. **Off-scale sizes**: anything not on the token scale. Found 9.5/10/10.5/11px all in use.
5. **Browser defaults nobody chose**: `<th>` renders bold-700 unless told otherwise — 32 labels
   were 700 by accident, matching nothing.

### The root finding
The design system was INCOMPLETE, not merely disobeyed. The site genuinely needs a tier below
`--fs-eyebrow` (vitals labels, jump nav, footer notes, tags). Because that tier was never
named, it grew at four sizes simultaneously. Naming `--fs-micro: 11px` and collapsing all four
onto it fixed more inconsistency than any amount of policing would have.

Second finding: tracking. One component was spelled 16 ways (.08/.1/.12/.15em × weights
400/500/600). DESIGN-SYSTEM §3 already sanctions exactly THREE, by role. Normalising to those
three — plus one notation (`.15em`, never `0.15em`, so grep tells the truth) — took the
rendered census from 27 treatments to 11, all legal.

**Result: 27 → 11 treatments, 0 off-scale.** Each of the 11 is a sanctioned track at a
sanctioned size; the spread that remains is legitimate role variety, not drift.
