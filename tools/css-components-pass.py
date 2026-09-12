#!/usr/bin/env python3
"""Phase B, part 1 — ONE button, one card edge, and the dead button classes go.

Runs against site.css in place. Decisions recorded in the commit message; the
button's fill/face default to the SYSTEM's (flat accent fill, label face) until
Arpit picks from prototypes/amber-buttons.html — switching is two token lines.
"""
import re, sys, pathlib, subprocess, collections
ROOT = pathlib.Path('/Users/arpit/Code/git'); sys.path.insert(0, str(ROOT / 'tools'))
import csslib as L
SITE = ROOT / 'site.css'
src = SITE.read_text(encoding='utf-8')

# comments -> placeholders so braces in prose cannot fool the splitter
table = []
def prot(m): table.append(m.group(0)); return f'/*@@{len(table)-1}@@*/'
prot_src = re.sub(r'/\*.*?\*/', prot, src, flags=re.S)

BUTTON_ONLY = re.compile(r'^(\.cta(?![\w-])(::before|:hover|:focus-visible)?|\.cta--[\w-]+(::before)?|\.cta-quiet(:hover)?|'
                         r'\.btn-a(-ghost)?|\.btn-b|\.btn-label|button\[type="submit"\]\.btn-label|\.hk-btn(\[disabled\])?|'
                         r'\.hd-case-btn|\[data-cta="send-role"\]|\[data-cta="[\w-]+"\]\[data-location="hero"\]|'
                         r':is\(\.btn-a-ghost,\.btn-b\)|:is\(\.btn-a,\.lbl-badge-bg,\.lbl-pill-bg\)|:is\(\.btn-a,\.lbl-pill-bg,\.btn-label,\.lbl-badge-bg\)|'
                         r'body\.p-home \.pill(-hot|-line)?|:where\(body\.p-home,body\.p-patterns\) \.hd-case-btn|'
                         r':is\(body\[class\*="p-case-studies"\],body\.p-screen\) \.(btn-a|lbl-pill-bg|lbl-badge-bg|btn-label)|\.nav-links \.nav-cta-sm a:not\(\.cta\)|'
                         r'\.lbl-(pill|badge)-bg|body\.p-screen \.lbl-badge-bg|:where\(body\.p-home,body\.p-patterns\) \.hd-case-btn(:hover)?)$')

stats = collections.Counter()
def walk(css, depth=0):
    out = []
    for kind, head, body in L.split_rules(css):
        bare = re.sub(r'/\*@@\d+@@\*/', '', head).strip()
        if kind == 'rule':
            parts = [p.strip() for p in re.split(r',(?![^(]*\))', bare)]
            if parts and all(BUTTON_ONLY.match(p) for p in parts):
                stats['button rules removed'] += 1; continue
            # dead button classes inside live selector lists: drop the token, keep the rule
            DEADTOK = r'\.(btn-a-ghost|btn-a|lbl-pill-bg|lbl-badge-bg|hd-case-btn|hk-btn|btn-label|pill-hot|pill-line|pill)(?![\w-])'
            if re.search(DEADTOK, bare):
                h2 = re.sub(r':not\(' + DEADTOK + r'\)', '', head)                # :not(.dead) chains
                h2 = re.sub(r'(?<=[(,])\s*' + DEADTOK + r'\s*(?=[,)])', '', h2)    # tokens inside :is()/lists
                while re.search(r',\s*,', h2): h2 = re.sub(r',\s*,', ',', h2)   # two dead tokens in a row leave ',,,' — collapse until none (a ',,' made the browser drop a whole rule)
                h2 = re.sub(r'\(\s*,', '(', h2); h2 = re.sub(r',\s*\)', ')', h2)
                if h2 != head: stats['dead tokens stripped from lists'] += 1; head = h2
            # card edges: one radius for a card-like surface
            if re.search(r'\.(bcard|hd-card|case-stat|case-vitals|framed|rcpt-box|lab-note|scr-q|ccd|hire-receipt|framed-blk|ckl|fit-col|vslip|artalt|card-gold)(?![\w-])', bare) \
               and '::' not in bare and ':hover' not in bare and 'border-radius' in body:
                body2 = re.sub(r'border-radius\s*:\s*[^;]+', 'border-radius:var(--radius-2)', body)
                if body2 != body: stats['card radii -> --radius-2'] += 1; body = body2
            if bare == '.thoughts-grid > *' and 'border-radius' in body:
                body = re.sub(r'border-radius\s*:\s*[^;]+', 'border-radius:var(--radius-2)', body); stats['card radii -> --radius-2'] += 1
            # the last dark-idiom literals on site components
            if bare.startswith('.lstep') and 'rgba(18,11,20,.8)' in body:
                body = body.replace('rgba(18,11,20,.8)', 'color-mix(in srgb, var(--surface-card) 80%, transparent)'); stats['literal'] += 1
            if bare == '.artalt' and '#F4ECDA' in body:
                body = body.replace('#F4ECDA', 'var(--surface-card)'); stats['literal'] += 1
            if 'rgba(32,24,12,0.22)' in body:
                body = re.sub(r'box-shadow\s*:\s*[^;]+', 'box-shadow:var(--elev-2)', body); stats['literal'] += 1
            if 'inset 0 1px 0 rgba(245,237,230' in body or 'inset 0 1px 0 color-mix(in srgb, #fff' in body:
                body = re.sub(r'box-shadow\s*:\s*inset[^;]+;?', '', body); stats['literal'] += 1
            out.append(f'{head}{{{body}}}')
        elif kind == 'at' and bare.startswith(('@media', '@supports', '@layer', '@container')):
            out.append(f'{head}{{{walk(body, depth + 1)}}}')
        elif kind == 'at':
            out.append(f'{head}{{{body}}}')
        else:
            out.append(head)
    return '\n'.join(out)

out = walk(prot_src)

BUTTON = '''
/* ── THE BUTTON. One component, 110 instances, 38 pages; it declares every critical
   property itself (execution lessons 4 and 11) and reads only the system's tokens, so
   the bookend and the paper resolve the same rule against their own roles.
   Variants: .cta (fill) · .cta--secondary (outline) · .cta-quiet (a text link that
   behaves like a control). Icon via --cta-icon on a modifier (.cta--linkedin, .cta--doc);
   .cta--bare drops it.
   Fill and face are the two decisions still open to Arpit (prototypes/amber-buttons.html);
   these two tokens are where his pick lands. */
:root, [data-ground="bookend"], [data-tint] {
  --cta-fill: var(--acc-copper);            /* F — Arpit, 2026-09-12: the copper fill (copper-600, cream label on paper) */
  --cta-fill-hover: var(--cta-fill-hover-copper);
  --cta-face: var(--type-label);           /* D: the system's label face */
}
/* B — Arpit, 2026-09-13: on a dark ground the system's "read upward" rule had stepped the
   fill to copper-100, a pastel that reads as disabled; hover went paler still. The bookend
   now takes the bright copper (copper-500, dark label 4.49:1) and hover brightens. */
[data-ground="bookend"] { --cta-fill: color-mix(in srgb, var(--copper-500) 90%, var(--copper-400)); --cta-fill-hover: var(--copper-400); }
/* 90/10 toward copper-400: pure copper-500 under the dark label measured 4.48:1 in contrast-audit (the token note said 4.49); the mix reads 4.63:1 and is not a visible shift */
/* a.cta/button.cta: (0,1,1), so a generic `body.p-home a{color:inherit}` (0,1,1) declared
   earlier can no longer strip the label — the button outranks element selectors, lesson 4. */
a.cta, button.cta, .cta {
  display:inline-flex; align-items:center; justify-content:center; gap:10px;
  /* G3 — Arpit, 2026-09-13 ("linkedin icon is not legible"): a 1.35em solid glyph centred on
     the label's x-height, and the pill lifts on hover. Chosen from three rendered directions. */
  min-height:46px; padding:0 26px; box-sizing:border-box;   /* one 46px pill whether or not it carries a glyph; centre alignment does the rest */
  font:var(--cta-face); font-size:15px; font-weight:600; line-height:1; letter-spacing:.02em; text-transform:none;
  white-space:nowrap; text-decoration:none; cursor:pointer;
  border:1px solid transparent; border-radius:var(--radius-pill);
  background:var(--cta-fill); color:var(--btn-fill-ink);
  transition:background var(--dur-quick) var(--ease-standard), color var(--dur-quick) var(--ease-standard), transform var(--dur-quick) var(--ease-standard), box-shadow var(--dur-quick) var(--ease-standard);
}
a.cta:hover, button.cta:hover, .cta:hover { background:var(--cta-fill-hover); color:var(--btn-fill-ink); filter:none; transform:translateY(-2px); box-shadow:0 10px 24px -10px color-mix(in srgb, var(--copper-500) 70%, transparent); }
@media (prefers-reduced-motion:reduce) { a.cta:hover, button.cta:hover, .cta:hover { transform:none; } }
a.cta:focus-visible, button.cta:focus-visible, .cta:focus-visible { outline:2px solid var(--border-focus); outline-offset:3px; }
.cta::before {
  content:""; flex:0 0 auto; display:block; background-color:currentColor;
  --cta-icon-ar:1; --cta-ico:1.35em;   /* G3: the glyph is legible at a glance — 20px beside a 15px label */
  height:var(--cta-ico); width:calc(var(--cta-ico) * var(--cta-icon-ar));
  -webkit-mask:var(--cta-icon) center/100% 100% no-repeat; mask:var(--cta-icon) center/100% 100% no-repeat;
}
.cta:not([class*="cta--"])::before, .cta--bare::before { display:none; }
.cta--linkedin::before { --cta-icon-ar:1; }
.cta--doc::before { --cta-icon-ar:0.8; }
.cta--linkedin { --cta-icon:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%3E%3Cpath%20d='M20.45%2020.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85%200-2.14%201.45-2.14%202.94v5.67H9.35V9h3.41v1.56h.05c.48-.9%201.64-1.85%203.37-1.85%203.6%200%204.27%202.37%204.27%205.46v6.28zM5.34%207.43a2.06%202.06%200%201%201%200-4.13%202.06%202.06%200%200%201%200%204.13zM7.12%2020.45H3.56V9h3.56v11.45zM22.22%200H1.77C.79%200%200%20.77%200%201.73v20.54C0%2023.23.79%2024%201.77%2024h20.45c.98%200%201.78-.77%201.78-1.73V1.73C24%20.77%2023.2%200%2022.22%200z'/%3E%3C/svg%3E"); }
.cta--doc { --cta-icon:url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2020'%3E%3Cpath%20fill-rule='evenodd'%20d='M2%200h8l6%206v12a2%202%200%200%201-2%202H2a2%202%200%200%201-2-2V2a2%202%200%200%201%202-2zm7%201.5V7h5.5L9%201.5zM3.5%2010h9v1.5h-9zm0%203.5h9V15h-9z'/%3E%3C/svg%3E"); }
a.cta--secondary, button.cta--secondary, .cta--secondary { background:none; border-color:var(--btn-line); color:var(--btn-line-ink); }
a.cta--secondary:hover, button.cta--secondary:hover, .cta--secondary:hover { background:var(--ink-wash); color:var(--btn-line-ink); box-shadow:none; }
a.cta-quiet, button.cta-quiet, .cta-quiet {
  display:inline-block; min-height:24px; padding:4px 0; border:0; background:none; border-radius:0;
  font:var(--type-label); font-weight:600; letter-spacing:.02em; color:var(--door-ink); text-decoration:none;
  /* Arpit, 2026-09-12: coloured, no underline. The colour is the affordance; hover deepens it. */
}
a.cta-quiet:hover, button.cta-quiet:hover, .cta-quiet:hover { color:var(--text-primary); }
/* the nav door composes .cta; only its placement is local */
.nav-cta { transition:background .3s, color .3s; }
.nav-cta:hover { transform:translateY(-2px); }
@media (prefers-reduced-motion:reduce) { .nav-cta:hover { transform:none; } }
'''
# the button block goes at the END of the components layer, after every page rule
# the button is the last word: END of the overrides layer, after the homepage's own
# body.p-home a{color:inherit} (0,1,1), which would otherwise strip its label
DEAD_RULES = [r'body\.p-home \.who \.meta\{[^}]*\}']   # 2026-09-13: Arpit — the remote/time-zone line in Act 02 repeated the hero eyebrow and the boarding pass; the element went, so does its rule
for _pat in DEAD_RULES:   # positional edits below: remove text BEFORE measuring any position
    out, _n = re.subn(_pat, '', out); assert _n == 1, ('dead rule not found once', _pat, _n)
_blank = re.sub(r'/\*@@\d+@@\*/', lambda m: ' ' * len(m.group(0)), out)
k = _blank.rindex('}')   # overrides' closing brace (comments are placeholders here)
out = out[:k] + '\n' + BUTTON + '\n' + out[k:]
# ── PHASE C · composition fixes found on the walk (each names the defect it answers) ──
FIXES = '''
/* ── RHYTHM (Arpit, 2026-09-13: "the negative space between and within sections is not
   proper"). The system names ONE act rhythm (--act-rhythm, 80px; the hero exempt) and
   says every act in a sequence shares it — nothing on the site consumed it. Measured:
   homepage acts carried 84/88/92/96/120 and the seam line added 96px of its own on top,
   so the blank between two acts ran ~200px at phone and desktop alike; case chapters sat
   120px apart at every width, pattern chapters 64, writing chapters 68; the Lab's first
   card in a section added 40px to the section's 88. Two numbers now, each stepping with
   the viewport: the ACT (between bands) and the CHAPTER (between h2 groups inside one
   article). A first child never adds its own top margin to the band's padding. */
:root { --rhythm-act: var(--act-rhythm); --rhythm-chapter: 64px; --section-y: var(--rhythm-act); }
@media (max-width:900px) { :root { --rhythm-act: 64px; --rhythm-chapter: 56px; } }
@media (max-width:600px) { :root { --rhythm-act: 48px; --rhythm-chapter: 48px; } }
body.p-home :is(.receipts, .work, .who, .contract, .labrow, .voices, .close) { padding-top: var(--rhythm-act); padding-bottom: var(--rhythm-act); }
body.p-home section:has(> :is(.seam, .seam-up)) { padding-top: 0; }           /* the seam line sits on the boundary… */
body.p-home :is(.seam, .seam-up) { margin-bottom: var(--rhythm-act); }         /* …and carries the act's top space itself */
body.p-home .wrap > :first-child, .section > :first-child, .section-inner > :first-child, .lab-wrap > :first-child, .measure-c > :first-child { margin-top: 0; }
body.p-home .wrap > :last-child, .section > :last-child, .section-inner > :last-child, .lab-wrap > :last-child, .measure-c > :last-child { margin-bottom: 0; }   /* nor a last child to its bottom */
main > :is([class]) > section { margin-bottom: var(--rhythm-chapter); }           /* case + pattern chapters (was 80 / 64, fixed) */
.measure-c > section[class*="xi-case-studies-"] { padding-top: 24px; }           /* a ruled chapter: the line sits 24 above its heading (was 40) */
main > :is([class]) > h2.section-title { margin-top: var(--rhythm-chapter); }
/* journey-check, 2026-09-13: jump anchors landed 8px UNDER the 94px fixed nav — the site carried
   scroll-margin-top 80/96/120 in three places. One clearance for every anchor target: the bar plus a
   breath, so the heading a reader jumped to is the first thing they see. */
main [id] { scroll-margin-top: 120px; }
/* Arpit, 2026-09-13 (copy review, group B): a case chapter's spine label — The stakes / The test /
   The mechanism / Falsifiable evidence — used to be glued to the heading with a colon, so the H2
   read as a form field. It is now the chapter's eyebrow, same words, and the sentence stands alone.
   The span declares every property it needs (lesson 11); it inherits nothing from the display face. */
.section-title > .chapter-k { display:block; font-family:var(--ff-mono); font-size:var(--fs-eyebrow); font-weight:500; letter-spacing:.02em; line-height:1.5; color:var(--accent-text); margin:0 0 10px; text-transform:none; }     /* writing + resources chapters (was 48, fixed) */
:is([class*="p-lab"], .p-fit) main > :is(section, header).section:not(.lab-hero) { padding-top: var(--rhythm-act); padding-bottom: var(--rhythm-act); }   /* Lab + Fit acts (was 88 fixed) */
/* Arpit, 2026-09-13: "#CFC4B4 is looking dull". On a dark ground the system's reading ink
   is neutral-200 and everything below the headline shared it. Lift each ink one stop so the
   hero reads in three levels: headline (50) · names and body (100) · quiet mono lines (200).
   Contrast only rises (14.29 / 11.16:1). */
[data-ground="bookend"] { --text-body:var(--neutral-100); --text-muted:var(--neutral-100); --text-faint:var(--neutral-200); }
body.p-home .hero .cred-strip > div > b { color:var(--neutral-50); }
/* /patterns/ — the rule block's meta ("Read the rule", the date) sat centred in the
   300px column beside a 66ch prose block: an element centred in leftover space. It is
   a metadata RAIL: it starts at the top of the prose and reads as a margin note. */
@media (min-width:861px){
  body[class*="p-patterns"] :is(.xi-patterns-012,.xi-patterns-018).is-paper{display:grid}
  body[class*="p-patterns"] :is(.xi-patterns-012,.xi-patterns-018).is-paper{grid-template-columns:minmax(0,66ch) 300px;justify-content:space-between;column-gap:48px}   /* the grid had been switched off by a display:block that outranked it — measured: display:block at 1440, so its areas never applied */
  body[class*="p-patterns"] .xi-patterns-017{grid-area:meta;align-self:start;align-items:flex-start;text-align:left;padding-top:4px}   /* an extracted grid-row:1/span 20 had overridden the named area */
  body[class*="p-patterns"] :is(.xi-patterns-012,.xi-patterns-018) > :is(.eyebrow,.section-title){grid-column:1/-1}
}
/* CASE HERO, desktop: the solo variant capped an 880px column and let the paragraph run
   ~500px wide beside nothing — half the band empty (layout rule: whitespace is designed
   or it is a defect). The stats already belong to the hero; they become its right rail,
   stacked, top-aligned with the paragraph. Kicker and headline still span the band.
   The hero's content sits in ONE inner wrapper, so the grid is declared on that. */
@media (min-width:1100px){
  body[class*="p-case-studies"] .case-hero__in--solo{max-width:1180px;grid-template-columns:1fr}
  body[class*="p-case-studies"] .case-hero__in--solo > div{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(300px,.85fr);column-gap:clamp(40px,5vw,72px);row-gap:0;align-items:start}
  body[class*="p-case-studies"] .case-hero__in--solo > div > :is(.case-hero__kicker,h1){grid-column:1/-1}
  body[class*="p-case-studies"] .case-hero__in--solo > div > .case-hero__hook{grid-column:1;grid-row:3;margin-top:0}
  body[class*="p-case-studies"] .case-hero__in--solo > div > .hand{grid-column:1;grid-row:4}
  body[class*="p-case-studies"] .case-hero__in--solo > div > .case-stats{grid-column:2;grid-row:3/span 2;display:flex;flex-direction:column;flex-wrap:nowrap;gap:16px;margin-top:0}
  body[class*="p-case-studies"] .case-hero__in--solo > div > .case-stats > .case-stat{flex:0 0 auto;min-width:0}
}
/* card titles: 22px at 1.15 was under the 1.25 floor on two-line titles (line-height-check);
   the system's title leading is 1.3 */
.card-title{line-height:1.3}
/* lab/eval severity chips: amber ink on the amber soft fill read 4.03:1 — the chip's ink is
   one stop deeper than the word colour, the same one-stop rule a tint obeys */
:where(body.p-lab-eval) .sev-medium{color:var(--amber-800)}
:where(body.p-lab-eval) .sev-high{color:var(--rose-800)}
/* the nav links declare their tracking; inheriting the page's -0.003em made the same nav
   compute two values across 35 pages (component-identity-check) */
#nav .nav-links{letter-spacing:0}
#nav .nav-links a:not(.cta){letter-spacing:.02em}
/* a control edge owes 3:1: the lab door's 58% link-ink border read 2.47:1 */
.lab-links a:not(.cta){border-color:var(--link-ink)}
/* the teardown's measured table held min-width:520px through the phone restack (overflow-sweep
   at 390: 520px in 294px) — the restack's own selector loses to :where(body) table.td-table on
   specificity; released here, where the layer decides */
@media (max-width:860px){:where(body.p-lab-teardown) table.td-table{min-width:0}}
/* the two caption doors (the film caption on the hero, the method's receipts link on /process/)
   spoke at 11.5px against the house 14px — one door grammar (cta-grammar-check) */
body.p-home .hero .vid-hero-cap a, .contract-links a{font-size:var(--fs-ui);letter-spacing:.02em;color:var(--door-ink)}   /* 16 of 21 doors track at .02em; these two held .08em */
/* two ledger lines on the homepage — the receipts line and the "rather read first?" links —
   were capped at 720px with 580px of nothing beside them at 1440 (balance-check). They are
   rows of short items, not reading prose; they span the wrap. */
body.p-home .lab-row, body.p-home .contact-read, body.p-home .voices .lede{max-width:none}   /* the voices lede takes the work act's own treatment (.work .lede{max-width:none}) rather than a cap with a void */
/* ── HOMEPAGE, as information architecture (Arpit, 2026-09-12: "sections looking orphaned") ──
   1 · the hero filled the viewport and then padded 120px more under the client strip: a dead
       dark band before act 01. The band ends with the strip. */
body.p-home .hero{padding-bottom:clamp(32px,5vh,64px)}
/* 2 · one opener rhythm for every act and sub-act: eyebrow, 16px, title, 20px, lede — the
       eyebrow→title gap ran 80px on the acts and 40px on the sub-acts, so each opener read as
       three floating lines instead of one unit. */
body.p-home .chap{margin-bottom:16px}
body.p-home :is(.work,.who,.contract,.aiwork,.voices) .wrap > h2,
body.p-home .chap + h2, body.p-home .chap + .chap-i + h2{margin-top:0}
body.p-home .chap-i{margin:0 0 20px}
body.p-home .k{margin-bottom:12px}
body.p-home .wrap > .k + :is(h2,h3,.lede){margin-top:0}
/* 3 · the work sub-act now opens like 02·2, 03·2 and 04·2: its eyebrow uses its own first clause.
       The index chip takes the act's accent, like its siblings. */
body.p-home .k-idx-ember{color:var(--acc-copper)}
body.p-home .work .lede{max-width:none}   /* under its eyebrow the sub-act lede spans the band, as the voices lede does; a 66ch cap left 710px of nothing beside it (balance-check) */
/* 4 · one card grammar in act 01: the case cards took a muddy tint while the receipt cards
       beside them are paper with a coloured top rule. Normalised to the receipt card. */
.bcard{background:var(--surface-card);border-top:3px solid var(--a)}
/* ── CASE PAGES: the section links (case-jump) sat 186px left of the reading column and wore
   underlines; they align to the column and speak the door ink, no underline (Arpit). */
body[class*="p-case-studies"] .case-jump{width:auto;max-width:656px;margin:0 auto 32px;padding:0;box-sizing:border-box;transform:none;left:auto}   /* 656 = the 704 column minus its 24px paddings: the first link starts where the prose starts */
/* eight links in a 656px column wrapped 7 + 1 and orphaned "The public record": two rows of four */
@media (min-width:560px){body[class*="p-case-studies"] .case-jump:has(> a:nth-child(7)){display:grid;grid-template-columns:repeat(4,minmax(0,1fr));column-gap:16px;row-gap:4px}}
.case-jump a{border-bottom:0;color:var(--door-ink);font-weight:600;padding:8px 0}
.case-jump a:hover{color:var(--text-primary)}
/* the errata box stopped 200px short of the memo columns above it (balance-check): it shares their width */
body.p-home .wl-lead .errata-block{max-width:none}
/* the close band's heading is display type too */
[data-ground="bookend"] .close h2, [data-ground="bookend"] .page-head h1{color:var(--neutral-50)}
'''
out = out[:k] + FIXES + out[k:]
out = re.sub(r'/\*@@(\d+)@@\*/', lambda m: table[int(m.group(1))], out)

# assertions
code = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), out, flags=re.S)
depth = 0
for ch in code:
    depth += (ch == '{') - (ch == '}'); assert depth >= 0
assert depth == 0
for dead in ('.btn-a', '.hk-btn', '.pill-hot', '.lbl-pill-bg', '.lbl-badge-bg', '.btn-label', '.hd-case-btn'):
    left = re.findall(re.escape(dead) + r'(?![\w-])', code)
    print(f'  {dead:14s} selectors left: {len(left)}')
assert code.count('.cta {') == 1 or code.count('.cta{') + code.count('.cta {') == 1, 'exactly one .cta definition'
print(dict(stats))
pathlib.Path('/private/tmp/claude-501/-Users-arpit-Code-git/91c61cad-dfbf-4e82-be35-f03d6fd108c1/scratchpad/site.components.check.css').write_text(out)
if '--check' not in sys.argv:
    SITE.write_text(out, encoding='utf-8'); print('written')

# markup: the nine Subscribe buttons become the secondary variant of the one button
if '--check' not in sys.argv:
    n = 0
    for f in (ROOT / 'patterns').glob('*.html'):
        s = f.read_text(encoding='utf-8')
        t = re.sub(r'class="lbl-eyebrow-500 btn-b ', 'class="cta cta--secondary ', s)
        if t != s: f.write_text(t, encoding='utf-8'); n += 1
    print(f'  .btn-b -> .cta cta--secondary on {n} pages')
    f = ROOT / 'patterns/index.html'; s2 = f.read_text(encoding='utf-8')
    assert s2.count('class="hd-case-btn"') <= 1
    f.write_text(s2.replace('class="hd-case-btn"', 'class="cta"'), encoding='utf-8'); print('  .hd-case-btn -> .cta (patterns/index.html)')
