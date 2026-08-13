# DESIGN SYSTEM — EMBER
*The second design system. Classic (`DESIGN-SYSTEM.md`) remains the first; the two swap.*

**Status:** governing the `ember` branch · established 2026-08-13 · direction chosen by Arpit
from the four-way drafting board (`prototypes/drafting-board.html`), reference build
`prototypes/energy-d-full.html`.

**Thesis of the identity:** energy from heat. Gradient fields, angled seams, layered depth —
the half-second of doubt rendered as temperature. The evidence artifacts (receipt, candidate
facts, boarding pass, stamps, hand notes) survive from Classic as *cream objects on the heat*:
continuity lives in the artifacts, the voice, and the letterforms.

---

## 0 · The theme-swap architecture (why this file can exist twice)

- **One DOM, two stylesheets.** Every shipped page carries theme-neutral markup styled
  entirely by ONE of `classic.css` or `ember.css`. The active theme is declared once:
  `<html data-theme="ember">`. Switching the whole site back = flip the attribute + the
  stylesheet link (one commit; a `tools/theme-swap.py` helper makes it one command).
- **Zero inline styling.** No `style=""` attributes, no per-page `<style>` blocks on shipped
  pages. JS communicates state through classes and CSS custom properties only
  (e.g. `el.style.setProperty('--hd-fill', …)` is the ONE sanctioned channel, and only for
  continuous values a class can't carry). Enforced by the extended inline-style gate.
- **Additive structure.** Ember-only structural elements (seam dividers, decorative fields)
  are theme-neutral markup (`<div class="seam" aria-hidden="true">`) that `classic.css`
  simply hides. Classic-only decorations are likewise hidden by `ember.css`. Neither theme
  may *require* removing the other's nodes.
- **Both themes pass every gate** (contrast, canon, case-sync, assets, spacing) before any
  merge. `classic-v1` git tag marks the last pre-Ember production state.

## 1 · Color tokens

All pairs below are **pre-computed against their stage** and must not be re-tinted casually.
The floor is WCAG 2.2 AA: 4.5:1 body, 3:1 large text (≥24px / ≥18.66px bold) and UI edges.

### Stages (backgrounds)
| Token | Value | Role |
|---|---|---|
| `--bg0` | `#120B14` | base field (near-black plum) |
| `--bg1` | `#1B1320` | alternate band |
| `--card` | `#241830` | raised card |
| `--line` | `rgba(245,237,230,.16)` | hairline on any dark stage |

### Ink on dark stages
| Token | Value | Contrast on bg0 | Use |
|---|---|---|---|
| `--ink` | `#F5EDE6` | ≈15:1 | headings, primary text |
| `--mut` | `rgba(245,237,230,.76)` | ≈9.8:1 | body, captions |
| `--dim` | `rgba(245,237,230,.62)` | ≈6.4:1 | de-emphasised; still AA at any size |

### The four heats (accents on dark stages)
| Token | Value | Contrast on bg0 | Notes |
|---|---|---|---|
| `--ember` | `#FF8A5C` | ≈8.0:1 | primary accent; gradient start |
| `--violet` | `#E86BFF` | ≈7.1:1 | secondary; gradient end |
| `--amber` | `#FFC46B` | ≈11.3:1 | links on dark, focus ring, hand notes |
| `--rose` | `#FF7AA8` | ≈7.6:1 | fourth voice in cycles |

Accent **cycling order** for repeated components: ember → violet → amber → rose (then repeat
with reduced tint). Color never carries meaning alone — every classification (NDA/Public,
pass/fail) is also written as text.

### Gradients
| Token | Value | Rules |
|---|---|---|
| `--g-hot` | `linear-gradient(92deg, var(--ember), var(--violet))` | CTAs, the ONE gradient-text span per screen |
| hero field | two radial glows (ember NE, violet SW) over `linear-gradient(160deg,#1E1022,#120B14 55%,#190D10)` | hero + closer only — fields are bookends, not wallpaper |

**Gradient-text rule:** `background-clip:text` spans get class `.grad`; maximum one per
viewport-height of content; both gradient endpoints must independently clear 4.5:1 on the
darkest pixel beneath (ember 8.0, violet 7.1 on bg0 — re-verify if either endpoint or stage
changes). The pixel contrast auditor cannot measure clipped text (computed color is
transparent) — `.grad` is exempted there and verified by calculation, recorded here.

### The cream artifact set (paper objects on the heat)
| Token | Value | Contrast | Use |
|---|---|---|---|
| `--cream` | `#EFE7D2` | — | artifact background |
| `--cream-ink` | `#221C10` | ≈13:1 on cream | artifact text |
| `--cream-mut` | `#5D5442` | ≈5.6:1 on cream | artifact secondary |
| `--cream-red` | `#A93A24` | ≈4.9:1 on cream | stamps. **Never** `#C2452D` (measured 4.1:1 — fails small text) |

## 2 · Typography

Faces are unchanged from Classic — continuity lives in the letterforms:
Newsreader (display/serif), IBM Plex Sans (UI/body), IBM Plex Mono (labels/data),
Caveat (hand annotations only).

| Style | Spec | Notes |
|---|---|---|
| Display XL (h1) | Newsreader 300 · `clamp(52px, 7.2vw, 106px)` · lh 1.01 · ls −.015em | hero only |
| Display L (h2) | Newsreader 300 · `clamp(30px, 3.6vw, 48px)` · **lh 1.12** | section titles — lh is mandatory; body lh 1.65 leaking into an h2 is a known defect class |
| Display M (h3) | Newsreader 400 · 19–30px · lh 1.2–1.25 | card titles |
| Metric | Newsreader 400 · `clamp(24px, 2.2vw, 46px)` · lh 1.05 · accent color | numerals in lanes/cells |
| Body | Plex Sans 400 · 13.5–16px · lh 1.6–1.75 · `--mut` | |
| Kicker `.k` | Plex Mono · 12px · ls .18em · uppercase · section accent | one per section, accent cycles |
| Data/label | Plex Mono · **≥11.5px** · ls .1–.16em · `--mut` (never `--dim` below 12px) | |
| Hand `.hand` | Caveat 600 · 21–26px · amber · rotate ≤3° | annotations; `aria-hidden` when decorative; rotation removed under reduced-motion |

## 3 · Space, shape, elevation

- **Spacing grid unchanged:** 4·8·12·16·20·24·32·40·48·64·80 px (the existing gate enforces
  it; Ember adds no exceptions). Section rhythm: 88–120px vertical; `.wrap` max 1240px,
  40px gutters (16px ≤640px).
- **Radii:** 2px (focus ring corners), 6px (lanes, small cards), 10–12px (cards, artifacts),
  999px (pills). Nothing else.
- **Seams:** section transitions may use one angled seam
  (`clip-path: polygon(0 62%, 100% 8%, 100% 100%, 0 100%)`, height 110px, or its mirror).
  Max one seam per band boundary; seams are `aria-hidden` decoration.
- **Elevation:** artifacts `0 30px 60px rgba(0,0,0,.5)`; cards flat or `0 16px 36px rgba(0,0,0,.45)`.
  Artifact tilt ≤1.5°, stamp tilt ≤4° — both removed under reduced-motion.

## 4 · Motion & interaction

- Durations 200–250ms, `ease-out`. Hover: translateY(−2px) pills, −6px cards, background
  tint deepen on lanes. No parallax, no scroll-jacking, no autoplaying motion.
- **`prefers-reduced-motion: reduce` contract:** all transitions/transforms/rotations/tilts
  removed; skewed lanes render unskewed; smooth-scroll off. This is part of the component
  definition, not an afterthought.
- **Focus:** `:focus-visible { outline: 2px solid var(--amber); outline-offset: 3px }` on every
  interactive element, on every stage (amber clears 3:1 on all four stages and the cream).
- Hit targets ≥24×24px.

## 5 · Component inventory (the shared DOM contract)

Each component is a markup shape both stylesheets must style. Canonical reference:
`prototypes/energy-d-full.html`.

| Component | Class contract | Ember treatment | A11y notes |
|---|---|---|---|
| Pill CTA | `.pill` + `.pill-hot` / `.pill-line` | gradient fill / ember outline | real `<a>/<button>`; text ≥12.5px |
| Kicker | `.k` | mono caps, section accent | not a heading; precedes the real hN |
| Section head | `.k` + `h2` | lh 1.12, max-width | one h1 per page, ordered hN |
| Receipt cell | `.rcell` + accent modifier | card + 3px accent top rail + accent metric | baseline text in the cell, not color-coded only |
| Case lane | `.lane` + `.l1…l6` | skew −3° (inner counter-skew), accent rail + tint, metric/kick/walk in lane color | whole lane is the link; `:focus-within` lights the walk; unskewed under reduced-motion |
| Memo card | `.memo` + accent modifier | card + accent top rail + mono kicker | |
| Index card | `.idx` | paper card, red index line | link if navigable |
| Artifact | `.facts` `.pass` (cream set) | cream object, tilt, shadow | `role="group"` + `aria-label`; tables of facts as `<dl>` |
| Stamp | `.stamp` / `.ek` | 2px border, mono caps, tilt, `--cream-red` on cream / accents on dark | text carries the meaning, not the color |
| Hand note | `.hand` | Caveat, amber, slight rotate | `aria-hidden` unless content-bearing |
| Seam | `.seam` (+`.seam-up`) | clip-path band divider | `aria-hidden`; hidden by classic.css |
| Field | `.field` | hero/closer radial glows | `aria-hidden`; hidden by classic.css |
| Demo box | `.demo` | card + corner glow; the hero diagnostic reuses this language | fully keyboard-operable; state changes announced (`aria-live="polite"`) |

**The hero diagnostic** ("Where does your AI product lose people?") is a first-class component:
functionality identical to Classic (presets, free-text, reframe, reset), restyled as an Ember
demo box — gradient accents, amber focus, reduced-motion-safe reveal.

## 6 · Page grammar

Scene rhythm (homepage reference): field hero → seam → band (`--bg1`) → base (`--bg0`) →
seam → band → … → field closer. Rules: never two fields adjacent except as bookends; every
band opens with kicker + h2; accent cycling resets per section; **whitespace must be designed
— capped text in a full-width band needs a content-role object in the remaining space**
(rail artifact, demo, diagram) or the text isn't capped.

## 7 · Accessibility floor (WCAG 2.2 AA — hard gate, both themes)

1. Contrast: the token tables above are the only sanctioned pairs; the pixel auditor runs
   calibrated on every page at 1440+390 (real-viewport check for sub-500 findings — headless
   lies below ~500px).
2. Structure: skip link → `<main>`; landmarks (`header/nav/main/footer`); one `h1`;
   no skipped heading levels.
3. Keyboard: everything operable; visible focus per §4; no keyboard traps; skip link first.
4. Motion: reduced-motion contract per §4.
5. Color: never the sole carrier (§1).
6. Forms: visible `<label>` per field; errors as text; submit is a real button.
7. Images/decoration: informative images get alt; decorative layers `aria-hidden="true"`.
8. Zoom: layout survives 200% zoom and 320px-wide viewports without horizontal scroll.

## 8 · Logo & favicon

AM monogram, ember-styled (direction chosen 2026-08-13; final mark pending Arpit's pick from
rendered options). Requirements: works as single-color cream on dark and dark on cream;
gradient version reserved for the mark at ≥24px; favicon legible at 16px (solid accent, no
gradient below 32px); shipped as inline SVG (header), `favicon.svg` + `favicon.ico`.

## 9 · What Ember explicitly does NOT change

- The book edition (`/book/`) and the print PDFs — separate visual systems, stay Classic.
- OG share cards — regenerate only as a follow-up decision, not in this port.
- Copy, canon, and every number — content is theme-independent by definition.
- The spacing grid and the gate suite — both themes answer to the same instruments.

## Retired-palette tokens (added 2026-08-13)

`styles.css` hard-coded the classic gold (`#D4A85E`, `#7E5A14`) inside extracted
per-page classes carrying `!important`. No Ember rule could outrank them, so ten
inner pages still rendered old-theme badges, cards and ghost buttons long after
the port was called complete. Both are now tokens:

| Token | Classic | Ember | Contrast on ember ground |
|---|---|---|---|
| `--goldA` | `#D4A85E` | `#FFC46B` | 11.3:1 |
| `--goldA-dk` | `#7E5A14` | `#C98F3F` | border/dim variant only |

**Rule: a colour that both themes need is a token, never a literal.** A literal in
the shared stylesheet is a remnant waiting to happen.

### Section heat
`#thoughts` used `--heat:#A96BFF`, which measured **4.99:1 at 11px** — legal by the
number, unreadable in practice. Ember section heat must come from the checked
canon set (`--ember` 8.0, `--violet` 7.1, `--amber` 11.3, `--rose` 7.6). Card
titles take `--ink`; colour is for labels and rails, not for the thing you read.

## Gates that guard this file

| Gate | Fails when | Calibration |
|---|---|---|
| `tools/overflow-sweep.py` | any element escapes the viewport at 1440/1024/768/390 | plants a −400px margin, requires red |
| `tools/theme-remnant-check.py` | any element PAINTS a retired classic colour under Ember | plants `#515863` on `h1`, requires red |

Both read rendered geometry and rendered colour, not CSS source — a component the
port never reached cannot hide from them. Scrollable containers (`overflow-x:auto`)
are exempt from the overflow sweep; `overflow:hidden` is **not**, because clipped
content is unreachable content.
