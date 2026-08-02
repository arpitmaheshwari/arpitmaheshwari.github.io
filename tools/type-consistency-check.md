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
