---
name: ember-design-system
description: The Ember design system used on arpitmaheshwari.com — colour tokens with measured contrast, one type scale, an 8px-derived spacing grid, and the component grammar. Load before writing or reviewing any UI for this site, or when adapting the system elsewhere. Covers the rules that are NOT visible in the values, which is where design systems actually fail.
---

# Ember — the system, and the reasoning under it

A token list is not a design system. Anyone can paste hex codes. What makes a system hold is the
set of decisions that explain *why* a value is what it is, and which mistakes it exists to
prevent. Those decisions are below, each with the failure it was written against — most were
learned by shipping the failure first.

## 1 · Colour

Ground and ink:

| Token | Value | Job |
|---|---|---|
| `--bg` | `#120B14` | page ground |
| `--bg-soft` | `#1B1320` | alternating band |
| `--bg-card` | `#241830` | raised surface |
| `--ink` | `#F5EDE6` | primary text |
| `--ink-muted` | `rgba(245,237,230,.76)` | body text |
| `--ink-dim` | `rgba(245,237,230,.62)` | captions, labels |
| `--border` | `rgba(245,237,230,.14)` | hairlines |

The four heats — each measured against `--bg`, not guessed:

| Token | Value | Contrast | Means |
|---|---|---|---|
| `--ember` | `#FF8A5C` | 8.0:1 | the primary heat; action, emphasis |
| `--violet` | `#E86BFF` | 7.1:1 | secondary heat; contrast within a set |
| `--amber` | `#FFC46B` | 11.3:1 | links, CTAs, kickers — the safest heat |
| `--rose` | `#FF7AA8` | 7.6:1 | the fourth voice, used sparingly |

`--g-hot: linear-gradient(92deg,#FF8A5C,#E86BFF)` is the CTA fill.

**Rules that are not in the values:**

- **Heat is semantic, never decorative.** A colour marks a *kind* of thing. If two elements share
  a heat they should share a meaning; if they don't, one of them is wrong.
- **Never state a contrast ratio you have not measured on the rendered pixels.** Style-based
  checks lie in two specific ways this system has been bitten by: gradient text
  (`background-clip:text` with `color:transparent` reports the transparent fallback — a real
  8:1 headline measured as 1.00:1) and translucent backgrounds (an `rgba()` tint must be
  composited over what is behind it before the ratio means anything).
- **A component declares its own ink on its own ground.** Never inherit colour and hope. A
  page-level selector will eventually match your element and win — that produced invisible text
  three separate times here, including once in production.

## 2 · Type

Three families, one job each. Never mix jobs:

- `--ff-display` → **Source Serif 4** — headlines and pull quotes. Weight 300 at display sizes.
- `--ff-sans` → **Source Sans 3** — body, UI, everything read rather than announced.
- `--ff-label` → **Source Sans 3, 600 weight, uppercase, letter-spacing .08em** — kickers, eyebrows, CTAs.
- `--ff-mono` → **JetBrains Mono** — code, and *only* code. Mono is not a label style.

Scale (clamped, so it holds from phone to desktop):

| Role | Size |
|---|---|
| Hero h1 | `clamp(38px, 6vw, 83px)` |
| Case h1 | `clamp(32px, 5vw, 76px)` |
| Section h2 | `clamp(28px, 3.2vw, 44px)` |
| Sub-head h3 | `clamp(22px, 2.2vw, 30px)` |
| Body | `16px / 1.7` |
| Caption, label | `12–13.5px` |

**Rules:** one scale, no improvised sizes. Body copy caps at ~70 characters — but a capped column
inside a full-width container is a layout defect, not a virtue (see §4). Uppercase always carries
letter-spacing; lowercase never does.

## 3 · Spacing

The grid: **4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80**.

Below 4px is an optical nudge and exempt. Above 80px is structural and exempt. **Anything between
those that is off-grid needs a reason** — a gate enforces this, because "just 6px here" is how a
system dies by a thousand small mercies.

## 4 · Layout

- **Whitespace is designed or it is a defect.** Capped text inside a wider container is a decision
  about the remaining space: give that space a content role, or don't cap the text. "Empty because
  the column ended" is a bug.
- **A section is one object.** Its kicker, headline, body and content share one left edge and one
  measure. Centring the parts individually instead of narrowing the container is the classic error.
- **Rows align to each other, not just inside correct bounds.** Every cell in a row must align to
  its siblings; every row must align to the row above. Outer-box checks pass layouts that look
  visibly wrong.
- **Test the range, not the breakpoints.** 1440 and 390 prove two points. Grids break in between —
  always check ~1024 and ~768 as well.
- **`grid-column: 2` needs a column 2.** When a mobile override collapses a grid to one track,
  reset the children's placements too, or the browser creates an implicit second track and your
  "one column" is silently two.

## 5 · Components

- **Artifacts (inline SVG diagrams).** Inlined so brand fonts apply. Each carries `class="art-svg"`
  and its own `id`, **and its internal `<style>` must be scoped to that id.** Unscoped, an
  artifact's generic class names (`.ik`, `.lb`) become page-wide rules and the second diagram on a
  page overwrites the first's ink. That shipped to production once.
- **Document exhibits stay paper.** A diagram that represents a printed thing — a plan, a receipt,
  a ticket — keeps a light ground inside the dark page. Material carries meaning; don't flatten it.
- **CTAs speak one grammar.** Uppercase label face, `.08em` tracking, arrow bound to the last word
  (`word&nbsp;→`) so it never orphans onto its own line.

## 6 · Working on this codebase

- No build step. Hand-written HTML, one stylesheet per theme, vanilla JS.
- **Every stylesheet edit must bump its `?v=` cache version** (`python3 tools/bump-css-version.py`).
  Editing CSS without bumping means browsers serve the old file under the same URL — that cost a
  full misdiagnosis where the author's browser and the disk disagreed.
- Facts are locked in `CANONICAL-FACTS.md`. Never invent a metric, a date, or a client name. If a
  number is not in canon, it does not go on the page.
