# Design System — arpitmaheshwari.com + the book

The single source of truth for typography, color, spacing, and section layout across
**both** properties: the classic site (dark, gold) and the interactive book (cream, ember).
The book keeps its own *skin* (Spectral body, ember/cream palette) but shares the **same
numeric type scale and spacing steps**, so the two read as one system, not two.

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
| `--fs-display` | **clamp(44px, 6vw, 64px)** | cover / display maximum (book cover, rare big moments) |
| `--fs-metric` | **clamp(38px, 4.4vw, 48px)** | stat / metric number (standard) |
| `--fs-metric-sm` | **24px** | inline / card-level metric number |

**Retired:** every other size (46/50/56/60/72/33/32/30/28/27/26/23/22/20/19/18/17/16.5/15.5/13.5/12.5/11/10px …).
They all map onto the ramp above.

## 2. Type roles (how each step is dressed)

| Role | Font | Size | Weight | Line-height | Tracking | Case | Color |
|---|---|---|---|---|---|---|---|
| Hero H1 | Newsreader | `--fs-hero` | 300 | 1.08 | -.02em | — | ink (accent em = gold, italic) |
| Display / cover | Newsreader | `--fs-display` | 300 | 1.1 | -.02em | — | ink |
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
- **One accent:** gold. `--copper` is retired unless a semantic need is defined.
- **No hardcoded hex** that duplicates a token (`#D4A85E`, `#5ED48E`, `#ff6464`, `#2F5D52` → tokens or a new named status token).
- Status colors (success/warn/error for wireframes) get real tokens: `--ok #5ED48E`, `--warn #E8C88A`, `--err #E0736B`.

### Cream "act" (governed — classic site)
Cream is a **peak**, used **only twice** on the homepage (the receipts band + the one-idea band) and nowhere else unless this file adds it. It re-points tokens:
```
--bg #F1E8D6  --bg-card #EAE0CA  --ink #20180C  --ink-muted #6E6250
--gold #8A6423 (= gold-dark on cream)  --border rgba(32,24,12,.16)
```
A cream section uses the **same** `--fs-title` (31px) and the **same** grammar as every dark section — only the background/ink change. It must never be the only place a big title appears.

### Book (second skin — same scale, own palette)
```
paper #F4ECDA/#EEE4CE  desk #2A1712→#170C09  ink #2C2620  ink-soft #6A6052
ember #C0512B (primary accent, replaces gold)  ochre #CE9230  pine #2F5D52
AA text variants: ember-ink #B04A24, ochre-ink #8F5E10
```
Book inherits the **numeric type scale + spacing** from §1/§5; only fonts (Spectral body) and palette differ.

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

## 9. Rollout order

1. **Foundation** — tokens + utility classes in `styles.css`.
2. **Flagships** — `index.html` (homepage) + the book (`book.css`, `portfolio.js`). Render + approve.
3. **Sweep** — 6 case studies, 10 pattern pages, utility pages (hire/screen/process/resources/now/writing/404), `folio`. Each refactored to §6 grammar + §1 scale.
4. **QA** — every page at 1280 + 375: zero horizontal overflow, one section grammar, console clean, no unloaded-font fallback.
