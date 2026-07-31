# Design System — arpitmaheshwari.com + the book

The single source of truth for typography, color, spacing, and section layout on the
**classic site** (dark, gold): homepage, case studies, pattern library, utility pages.

**The book is out of scope.** It already has its own coherent, deliberate design system
(Spectral body, ember/cream palette, fixed spreads) and is left as-is. This document governs
the classic site only.

> Rule of the system: **one scale, one grammar.** Every heading, every section, every metric
> pulls from the tokens below. No inline font-sizes. No per-page invention. If a value isn't
> in this file, it doesn't ship.

Built on **Option C** (approved): a bold hero that leads, calm and consistent section titles
underneath. Ratio ≈ 1.25 (major third) for the display ramp; a flat 12/13/14 scale underneath.

---

## 1. Type scale (the ramp)

One ordered ramp. Every text element maps to exactly one step.

| Token | Value | Role |
|---|---|---|
| `--fs-eyebrow` | **12px** | eyebrow / kicker / label / meta / nav / button (mono) — ONE size |
| `--fs-caption` | **13px** | caption, secondary meta |
| `--fs-ui` | **14px** | secondary body, UI text, card body |
| `--fs-body` | **16px** | body base (line-height 1.7, measure ≤ 62ch) |
| `--fs-lead` | **21px** | standfirst / lede / deck (one size) |
| `--fs-card` | **24px** | card title, sub-heading |
| `--fs-title` | **clamp(24px, 3.2vw, 31px)** | **SECTION TITLE — the default for every section, every surface** |
| `--fs-title-lg` | **clamp(28px, 3.6vw, 39px)** | prominent title — chapter / act opener ONLY, never ad hoc |
| `--fs-hero` | **clamp(36px, 5.5vw, 52px)** | hero H1 |
| `--fs-display-xl` | **clamp(44px, 6vw, 64px)** | cover / display maximum (book cover, rare big moments) |
| `--fs-metric` | **clamp(38px, 4.4vw, 48px)** | stat / metric number (standard) |
| `--fs-metric-sm` | **24px** | inline / card-level metric number |

**Retired:** every other size (46/50/56/60/72/33/32/30/28/27/26/23/22/20/19/18/17/16.5/15.5/13.5/12.5/11/10px …).
They all map onto the ramp above.

## 2. Type roles (how each step is dressed)

| Role | Font | Size | Weight | Line-height | Tracking | Case | Color |
|---|---|---|---|---|---|---|---|
| Hero H1 | Newsreader | `--fs-hero` | 300 | 1.08 | -.02em | — | ink (accent em = gold, italic) |
| Display / cover | Newsreader | `--fs-display-xl` | 300 | 1.1 | -.02em | — | ink |
| **Section eyebrow** | IBM Plex Mono | `--fs-eyebrow` | 500 | 1.4 | .15em | UPPER | gold |
| **Section title** | Newsreader | `--fs-title` | 400 | 1.15 | -.01em | — | ink |
| Prominent title | Newsreader | `--fs-title-lg` | 400 | 1.12 | -.015em | — | ink |
| Standfirst / lede | Newsreader | `--fs-lead` | 300 | 1.4 | — | — | ink (italic only when set apart) |
| Card title | Newsreader | `--fs-card` | 400 | 1.3 | — | — | ink |
| Body | IBM Plex Sans | `--fs-body` | 400 | 1.7 | normal | — | ink-muted (ink for lead paras) |
| Secondary body / UI | IBM Plex Sans | `--fs-ui` | 400 | 1.6 | — | — | ink-muted |
| Caption / meta | IBM Plex Mono | `--fs-caption`/`--fs-eyebrow` | 400 | 1.45 | .08em | UPPER | ink-muted |
| Metric number | Newsreader | `--fs-metric` | 300 | .92 | -.02em | — | gold (dark) / ink (cream) |
| Quote / pull-quote | Newsreader | `--fs-card` | 400 italic | 1.5 | — | — | ink |
| Nav link | IBM Plex Mono | `--fs-eyebrow` | 500 | 1 | .1em | UPPER | ink-muted |
| Button | IBM Plex Mono | `--fs-eyebrow` | 500 | 1 | .1em | UPPER | (see components) |

**Weight rule:** Newsreader headings are **400**. Reserve **300** for hero/display/metric only. Never 500/600 for headings on the classic site.

**One display serif:** Newsreader everywhere. `Fraunces` / `Cormorant Garamond` are **removed** (they were declared but never loaded → silent Georgia fallback). Testimonials use Newsreader.

## 3. Fonts

| Family | Token | Use |
|---|---|---|
| Newsreader | `--ff-display` | all display, headings, standfirsts, metrics, quotes |
| IBM Plex Sans | `--ff-sans` | body, UI, forms |
| IBM Plex Mono | `--ff-mono` | eyebrows, labels, meta, nav, buttons, folios |
| Spectral | `--bk-serif` | **book body only** (its second-skin reading voice) |
| Caveat | `--bk-hand` | **book only** — margin/sticky notes |

**Remove/repair:** `--ff-serif` (Fraunces) and Cormorant declarations; Lexend stays wired to the dyslexia toggle **only** (and its `<link>` removed from pages that don't toggle). Book PAIRINGS that reference unloaded fonts (Instrument/Playfair/EB Garamond/DM Serif) → drop to the two loaded serifs.

## 4. Color

### Dark theme (classic site — canonical)
```
--bg #0A0A0A   --bg-soft #111111   --bg-card #141414
--ink #F2EDE4  --ink-muted rgba(242,237,228,.62)     /* ONE muted — --ink-dim is retired (merge into --ink-muted) */
--gold #D4A85E   --gold-light #E8C88A   --gold-dark #A07835
--border rgba(255,255,255,.07)   --border-accent rgba(212,168,94,.30)   --hairline rgba(212,168,94,.22)
```
- **One accent:** gold. `--copper #4A6B5C` is the **sanctioned "In production / shipped" status token** (the pattern-page "In production" badge) — a defined semantic need, kept.
- **No hardcoded hex** that duplicates a token (`#D4A85E`, `#5ED48E`, `#ff6464`, `#2F5D52` → tokens).
- Status colors get real tokens: `--ok #5ED48E`, `--warn #E8C88A` (caution / "watch"), `--err #E0736B` (error).

### Exempt surfaces (NOT governed by the type scale)
These are controlled surfaces that deliberately mimic other UIs; they use their own internal sizing and are **out of scope** for the ramp:
- **Product-screenshot reconstructions** — the `.plate` / `.plM` / `.plV` device mockups (role="img"): era-honest app screens that need sub-11px micro-type to read as real.
- **Interactive product simulations** — the `#recon-*` widgets: they simulate a product interface, not page chrome.
- **Wireframe mock boxes** — illustrative "here's the interaction" sketches on pattern pages.
- **Decorative oversized numerals/ornament** — e.g. the 404 background "404" watermark (`.ghost`, ~clamp(220px,42vw,420px)): a design ornament, not readable heading text.
The scale governs **page chrome** (headings, sections, body, real navigation/buttons), never a simulated screen or ornament. (Same principle as the book being its own system.)

### Header clearance
The nav is `position:fixed` (~88px tall at page top). Every page's first content band clears it — top padding ≥ 104px on desktop (matches the homepage hero). Never let an eyebrow/title tuck under the nav.

### Cream "act" (governed — classic site)
Cream is a **peak**, used **only twice** on the homepage (the receipts band + the one-idea band) and nowhere else unless this file adds it. It re-points tokens:
```
--bg #F1E8D6  --bg-card #EAE0CA  --ink #20180C  --ink-muted #6E6250
--gold #7E5A14 (= gold-dark on cream; 4.77:1 on the darkest card cream)  --border rgba(32,24,12,.16)
```
A cream section uses the **same** `--fs-title` (31px) and the **same** grammar as every dark section — only the background/ink change. It must never be the only place a big title appears.

### Book — out of scope
The book keeps its own established system (paper/ember palette, Spectral body, fixed spreads).
Do **not** apply this document to `book/`.

## 5. Spacing, rhythm, geometry

```
--space: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 90   (px steps — snap all margins/padding/gap to these)
--section-y: 90px  (desktop)   64px (tablet ≤900)   48px (mobile ≤600)
--page-x: 64px (desktop)   32px (tablet)   24px (mobile)
--inner-max: 1180px            --measure: 62ch (body reading width)
--radius: 4px                  (the ONLY radius; dots use 50%)
```
- **One section rhythm** (`--section-y`). Retire the 120/96/64 mix and the identity-strip's inline 64.
- **One heading bottom-margin rule:** eyebrow→title 14px; title→body 18px; title→grid 36px.
- Retire the 6/8/12/…/60px margin scatter — snap to `--space`.
- Reading measures: body 62ch; no more 20/760px/1000px page-to-page jumps.

## 6. Section grammar (the core fix)

**Every section, every surface, is built the same way:**
```html
<section class="section">            <!-- --section-y padding, --page-x, hairline top border (dark) -->
  <div class="section-inner">         <!-- max-width --inner-max, centered -->
    <p class="eyebrow">Selected Work</p>          <!-- 12px mono gold, .15em, UPPER -->
    <h2 class="section-title">Three AI products, one problem</h2>  <!-- --fs-title -->
    …content…
  </div>
</section>
```
- The **visible headline of a section is always the `.section-title`** (31px), never a stray `<p>`/`<h3>` while the real H2 is an 11px whisper. This kills the #1 inconsistency (10px→56px section headings).
- Cream acts use the same block with `class="section act-cream"`.
- Prominent openers (a page hero-adjacent chapter head) may use `.section-title--lg` (39px) — sparingly.

## 7. Components (consolidated)

- **Button** — one spec: `--ff-mono`, `--fs-eyebrow`, weight 500, .1em, UPPER, padding 14px/28px, `--radius`. Primary = gold fill / bg text; secondary = gold text / `--border-accent` outline. (Retire the sans-vs-mono, 3-padding, 2-radius drift.)
- **Card** — `--bg-card`, `1px --border`, `--radius`, padding 26px; title = `.card-title` (24px); body = `--fs-ui`. Hover: `border-accent` + translateY(-4px).
- **Metric block** — top rule 2px, number `--fs-metric`, caption `--fs-ui` 500, meta `.eyebrow`/caption. One treatment site-wide.
- **Callout** — one inset family: `border-left 3px` accent, padding 24/28, `--bg-card`. (Retire the border-left/full-border/floating-label mix.)
- **Eyebrow** — one token: 12px mono, .15em, UPPER, gold (or ember in book). Never recolor per-slot.

## 8. Migration map (old → new)

| Old | New |
|---|---|
| section H2 at 10/11px mono kicker + separate big `<p>` | `.eyebrow` + `.section-title` (31px) |
| cream `.proof-title` clamp(30-46) | `.section-title` (31px) |
| ~40 inline case-study H2 clamp(26-34) | `.section-title` |
| pattern H2 28/32 oscillation | `.section-title` |
| hire 10px mono section head | `.eyebrow` + `.section-title` |
| book title--l 56 / title--m 30 (peer heads) | `.section-title` (both), `--lg` for hub openers only |
| hero variants (64/56/60/52/44/38) | `--fs-hero` (52) |
| metric variants (72/50/46/44/42/…/21) | `--fs-metric` (48) or `--fs-metric-sm` (24) |
| body 12.5/13/13.5/14/15/15.5/16 | `--fs-body` 16 / `--fs-ui` 14 / `--fs-caption` 13 |
| eyebrow ~25 variants | one `.eyebrow` token |
| `--ink-dim` | `--ink-muted` |
| Fraunces/Cormorant | Newsreader |

## 9. Rollout order (classic site only)

1. ✅ **Foundation** — tokens + utility classes in `styles.css`.
2. ✅ **Homepage** — `index.html` on the §6 grammar + §1 scale. (Verified.)
3. **Case studies** — the 6 files in `case-studies/`. Retire the ~40 hand-copied inline H2s → `.section-title`; case hero H1 → `--fs-hero`; hooks/standfirsts → `.lead`; stats → `.metric-num`; one content measure (62ch); one hero composition.
4. **Patterns** — `patterns/index.html` + the 9 pattern pages. One hero composition; prose H2 (28/32 oscillation) → `.section-title`; standfirst variants A/B → one `.lead`; eyebrow color drift → one gold token; kill the double-padding main wrapper.
5. **Utility pages** — hire/screen/process/resources/now/writing/404 (follow-up; same grammar).
6. **QA** — every page at 1280 + 375: zero horizontal overflow, one section grammar, console clean, no unloaded-font fallback.

## 10. Marginalia — the personality layer (added 2026-07-29, Arpit's pick: direction B)
A handwritten annotation layer OVER the system, never instead of it. The site should read as one
person's annotated argument, not an agency deliverable.
- **Face:** Caveat 600 (Google Fonts), 20–22px body notes, 30px signature. Color `--gold`
  (or `--ink-muted` via `.hand--muted`). Tilt ±2° max. Class: `.hand` (styles.css).
- **Scribbles:** hand-authored SVG paths (`.scr`) — pen ellipse, arrows, ring — stroke `--gold`,
  round caps, no fill. Never generated/filtered imagery.
- **Rules:** every note states an existing fact (canon-traceable); ≤1 note per section;
  `aria-hidden="true"` on decorative notes; notes in animated contexts reuse the hero's
  `reveal` treatment. Current homepage set (8): hero ellipse + six-years note, try-it nudge,
  photo pen-ring + "that's me", favourite-receipt, patterns origin, lab nudge, — Arpit signature.
- Extended 2026-07-29 (Arpit's instruction) to the six case studies + /hire: one hero-hook note
  per case (PTC gets a second at #the-miss), hire gets a receipts note + the — Arpit signature.
  Case-hero note style: 21px, margin 12px 0 22px (breathing room above the stats grid).
  Extended again 2026-07-29: patterns index + all 9 pattern pages (one doctrine note under the
  hero meta, e.g. "never ship the naked number", "reversibility outranks confidence") and the
  4 lab pages (one note after the hero lede). Extended 2026-07-29 again: writing index + 4 essays
  (note after the meta line, grounded in each essay's own opening — e.g. "the demo always goes
  perfectly — that's the trap") and /screen ("I set the exam — only fair I sit it").
  Extended 2026-07-29 (final): /now ("updated monthly — hold me to it") and /process ("smaller
  bets, better evidence — the whole method"). Marginalia now covers every classic-site page except
  404 and resources (skip unless asked). The book keeps its own voice — do NOT extend there.

## 11. Handcraft objects — v2 of the personality layer (2026-07-30, Arpit's brief:
"more handcrafted elements to make the site look unique and original" — NOT a palette change)
Beyond §10's handwritten notes, the site now carries hand-MADE OBJECTS on the dark identity:
- **Stickies** (`.stick`, `.stick--purple`): paper notes with a tape mark, Caveat, rotated ±2.5°,
  real drop shadow (the one sanctioned shadow use). Current: hero "not a theme / not a template /
  real work"; Lab band purple "Open-source with tests".
- **Doodle boxes** (`.doodle-box`): hand-drawn rotated frame with ☑ checklist items. Current:
  the RECEIPT box (Problem/Approach/Evidence/Impact/What failed) beside the receipts title.
- **Spot illustrations** (`.ai-art`): hand-authored gold line-art SVGs on case cards — billboard
  (AdTech), cited document + check (FinTech), signal report + magnifier (DD). Illustrations
  depict the PRODUCT CONCEPT — never fake process artifacts (closed-artifacts rule stands).
- **Marker underlines** (`.mk-ul`): squiggle SVG under select section titles.
All decorative objects aria-hidden; homepage only so far — extend to case/hire/patterns pages
with renders first.
