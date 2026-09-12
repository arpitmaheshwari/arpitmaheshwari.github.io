#!/usr/bin/env python3
"""css-adopt-tokens.py — site.css stops speaking its own colour names and speaks the
design system's roles. The value pass that follows the structural fold.

WHY (2026-09-12). After the fold, site.css still carried three palettes: the 2026-07
classic (:root, dark), the ember dark theme (:root, plum), and my bridge mapping the
site's forty names onto the system's roles — written three times over because a
custom property resolves where it is DECLARED, so a map on `main` did not reach a
bookend. Three palettes is how a card ended up unreadable on AdTech and two Connect
buttons ended up different colours.

The fix is not a fourth map. It is to make every rule read the system's role
directly — `var(--text-body)`, not `var(--ink)` — so the bookend, the tinted card and
the paper all resolve the SAME rule against their own tier 2, and the map disappears.

WHAT IT DOES, in order, each step asserted:
  1. RENAME every var() reference from a site name to a system role (RENAME table).
  2. DELETE every declaration that re-declared a site colour name with a literal —
     the two old :root palettes, the cream-act palette, the homepage's nineteen, the
     contract demo's two — EXCEPT inside the reconstruction plates and paper objects,
     which are evidence of somebody else's product and keep their own palette (their
     declarations are renamed, not removed, so their interiors still read them).
  3. Turn each page family's `--heat` literal into `--act: var(--acc-<family>)` —
     the system's interchangeable act accents, one stop for all.
  4. REPLACE raw colours in paint declarations outside the plates with the role
     they were standing in for (LITERALS table: light inks on dark become primary
     ink, .76 alphas become muted, .37 borders become strong edges, heats become act
     accents, dark grounds become surfaces, black lifts become --elev-2).
  5. Mid-page radial fields are deleted; bookend fields read var(--glow), which the
     system resolves to none on paper and to the fields on a bookend.
  6. The bridge's map blocks go. What survives of the bridge is rewritten by hand
     as a short adoption block: the plate palette, the instrument panels, the chart
     tracks, and the act accents per band and per page family.
  7. Tinted surfaces get data-tint in the markup so colors.css's one-stop rule
     applies to them — the system's hook, not a class list of my own.

ACCEPTANCE (tools/render-census.py diff, ignoring colour properties): zero elements
moved, zero page heights changed. Everything that changed is a colour, and the
contrast sweep says whether each change was right.

USAGE  css-adopt-tokens.py [--check]
"""
import pathlib, re, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import csslib as L

SITE = ROOT / 'site.css'

# 1 · site name -> system role. Exact-name matches only (a trailing [-\w] is a different token).
RENAME = {
    '--ink': '--text-body', '--ink-muted': '--text-muted', '--ink-dim': '--text-faint',
    '--bg': '--surface-page', '--bg-soft': '--surface-sunken', '--bg-card': '--surface-card',
    '--border': '--border-strong', '--hairline': '--border-hairline', '--border-accent': '--accent',
    '--gold': '--accent-text', '--gold-light': '--accent-text', '--gold-dark': '--accent-fill',
    '--goldA': '--accent-text', '--goldA-dk': '--accent-fill',
    '--copper': '--acc-copper', '--copper-light': '--acc-copper', '--ember': '--acc-copper',
    '--violet': '--acc-violet', '--amber': '--acc-amber', '--rose': '--acc-rose',
    '--link': '--link-ink', '--link-hover': '--link-ink-hover',
    '--heat': '--act', '--heat2': '--act-2',
    '--cta-ink': '--btn-fill-ink', '--g-hot': '--cta-grad',
    '--ok': '--status-positive', '--warn': '--status-caution', '--err': '--status-negative',
    '--bg0': '--surface-page', '--bg1': '--surface-sunken', '--card': '--surface-card',
    '--line': '--border-strong', '--mut': '--text-muted', '--dim': '--text-faint',
    '--cream': '--surface-page', '--cream-ink': '--text-body', '--cream-mut': '--text-muted',
    '--cream-red': '--acc-copper',
}
# declarations of these (post-rename) names are deleted outside plates; --act and --cta-grad
# are legitimately declared by the site (per family / in the tokens layer), so they stay.
DELETE_DECL = set(RENAME.values()) - {'--act', '--cta-grad'}

# scopes that are somebody else's product, or a paper OBJECT on the page: they own their palette
PLATE = re.compile(r'\.pl[AFMOPV]\b|\.recon|\.rx[a-z0-9]|\.rl-|-app\b|-paper\b|\.fig-paper|\.pass\b|'
                   r'\.rcpt-box|\.slip\b|\.stamp|\.ticket|\.letter|\.qc\b|\.psc|\.env\b|\.lug\b|'
                   r'\.spec-hole|\.paper\b|\.stick\b')

# 3 · page family -> act accent (hue family preserved where the system has one; o2 and writing
#     were indigo until cta-grammar-check showed their doors speaking a second voice — violet)
FAMILY_ACT = {
    'body[class*="p-case-studies"]': 'copper', 'body.p-case-studies-adtech': 'copper',
    'body.p-case-studies-fintech': 'violet', 'body.p-case-studies-vc-diligence': 'amber',
    'body.p-case-studies-ptc': 'rose', 'body.p-case-studies-o2': 'violet',
    'body.p-case-studies-orgos': 'copper', 'body.p-patterns': 'amber',
    ':is(body[class*="p-lab"],body.p-fit)': 'violet', 'body.p-screen': 'rose',
    'body[class*="p-writing"]': 'violet', 'body[class*="p-resources"]': 'copper',
    'body.p-home #thoughts': 'violet',
}

# 4 · raw colour -> role, for paint declarations outside the plates. Keys are upper-case hex
# or whitespace-stripped rgba. A value may be a role or a callable(prop) -> role.
def _alpha_role(alpha, prop):
    a = float(alpha)
    if prop.startswith('background'):
        if a >= .3: return '--border-hairline'
        return '--bar-track' if a >= .06 else '--ink-wash'   # a .09 track is a track, not a 5% wash
    if a >= .7: return '--text-muted'
    if a >= .55: return '--text-faint'
    if a >= .4: return '--text-disabled'
    if a >= .3: return '--border-strong'
    if a >= .08: return '--border-hairline'
    return '--ink-wash'

LITERALS = {
    # the light ink and its variants — the "ink" role, whichever ground it sits on
    '#F5EDE6': '--text-primary', '#F5EDE5': '--text-primary', '#F2EDE4': '--text-primary',
    '#F5EEE3': '--text-primary', '#F9F1E7': '--text-primary', '#FAF2E8': '--text-primary',
    '#F7EFE7': '--text-primary', '#E2DBD3': '--text-body',   # the long-form reading ink, softened for dark 
    # the heats -> act accents
    '#FF8A5C': '--acc-copper', '#FF6A3D': '--acc-copper', '#FFB08E': '--acc-copper',
    '#E86BFF': '--acc-violet', '#C64BFF': '--acc-violet',
    '#A96BFF': '--acc-indigo',
    '#FF7AA8': '--acc-rose', '#FF5FA2': '--acc-rose', '#FF9DC6': '--acc-rose',
    '#FFC46B': '--acc-amber', '#FFD28A': '--acc-amber', '#FFE0A8': '--acc-amber',
    '#C98F3F': '--accent-fill', '#D4A85E': '--accent-text', '#E8C88A': '--accent-text',
    '#A07835': '--accent-fill', '#7E5A14': '--accent-text', '#7A5410': '--accent-fill',
    '#6E4E1C': '--accent-fill', '#F2A3FF': '--link-ink-hover',
    # status
    '#7FCF9E': '--status-positive', '#5ED48E': '--status-positive', '#2E6A46': '--status-positive',
    '#FF9F8A': '--status-negative', '#E0736B': '--status-negative', '#894540': '--status-negative',
    '#6D5E40': '--status-caution',
    # dark grounds -> surfaces
    '#120B14': '--surface-page', '#0A0A0A': '--surface-page',
    '#1B1320': '--surface-sunken', '#111111': '--surface-sunken',
    '#241830': '--surface-card', '#141414': '--surface-card', '#1E1022': '--surface-card',
    '#1A0D08': '--btn-fill-ink',
    # the cream act's own palette -> the same roles on paper
    '#F1E8D6': '--surface-page', '#EFE7D2': '--surface-page',
    '#EAE0CA': '--surface-sunken', '#E6DCC3': '--surface-sunken',
    '#20180C': '--text-primary', '#221C10': '--text-primary', '#2C2620': '--text-primary',
    '#635848': '--text-muted', '#5D5442': '--text-muted', '#463E33': '--text-muted',
    '#A93A24': '--acc-copper',
    '#FFFFFF': '--surface-card', '#FFF': '--surface-card',
    # accent alphas
    'rgba(255,138,92,.54)': '--accent', 'rgba(255,138,92,.28)': '--border-hairline',
    'rgba(255,138,92,.07)': '--act-wash', 'rgba(255,138,92,.12)': '--act-wash',
    'rgba(232,107,255,.10)': '--act-wash', 'rgba(255,196,107,.1)': '--act-wash',
    'rgba(255,196,107,.10)': '--act-wash', 'rgba(255,196,107,.5)': '--accent',
    'rgba(126,90,20,.75)': '--accent',
    # ink alphas on the cream act
    'rgba(32,24,12,.49)': '--border-strong', 'rgba(32,24,12,.5)': '--border-strong',
    'rgba(34,28,16,.5)': '--border-strong', 'rgba(32,24,12,.14)': '--border-hairline',
    'rgba(32,24,12,.2)': '--border-hairline', 'rgba(32,24,12,0.2)': '--border-hairline',
    'rgba(34,28,16,.18)': '--border-hairline', 'rgba(44,38,32,.16)': '--border-hairline',
    'rgba(255,255,255,0.34)': '--border-strong',
    # the long tail, read one by one (2026-09-12)
    'rgba(255,255,255,.07)': '--ink-wash', 'rgba(255,138,92,.55)': '--accent',
    'rgba(126,90,20,0.08)': '--act-wash', '#5C420E': '--accent-fill',
    '#8A3A1C': '--status-negative', '#5A4A2A': '--text-muted', '#EEE4CE': '--surface-sunken',
    'rgba(44,38,32,.24)': '--border-hairline', 'rgba(34,28,16,.14)': '--border-hairline',
    'rgba(27,25,23,0.15)': '--border-hairline', 'rgba(27,25,23,0.25)': '--border-hairline',
    'rgba(32,24,12,0.25)': '--border-hairline', 'rgba(32,24,12,0.35)': '--border-strong',
    '#F7F1E4': '--surface-card', '#FFFDF8': '--surface-card',
    'rgba(224,115,107,0.14)': '--status-neg-bg', 'rgba(232,200,138,0.14)': '--status-cau-bg',
    # the menu bar is a bookend surface with the page showing through
    'rgba(10,10,10,.6)': 'MIX:--surface-page:60', 'rgba(10,10,10,.92)': 'MIX:--surface-page:92',
    'rgba(10,10,10,0.97)': 'MIX:--surface-page:97',
    # the ember nav and its drawer: the page ground showing through, on whichever ground
    'rgba(18,11,20,.97)': 'MIX:--surface-page:97', 'rgba(18,11,20,.92)': 'MIX:--surface-page:92',
    'rgba(18,11,20,.72)': 'MIX:--surface-page:72',
    # the loop figure is a bookend object: it paints its ground solid, not a 60% plum over paper
    'rgba(27,19,32,.6)': '--surface-page',
    # the thesis card: an accent edge and a two-accent wash
    'rgba(255,122,168,.05)': 'MIX:--acc-rose:6',   # the counter's rose wash
    'rgba(232,107,255,.4)': 'MIX:--acc-violet:60',  # the case pages' dashed back-link rule
    'rgba(224,115,107,0.25)': 'MIX:--status-negative:40',   # a wireframe card's warning edge
    'rgba(94,212,142,0.13)': '--status-pos-bg', 'rgba(224,115,107,0.12)': '--status-neg-bg',   # status washes
    'rgba(255,196,107,.4)': '--accent', 'rgba(255,196,107,.07)': '--act-wash', 'rgba(232,107,255,.05)': '--ink-wash',
}
ALPHA_INK = re.compile(r'rgba\((?:245,237,230|242,237,228|245,237,232),(0?\.\d+)\)')
LIFT = re.compile(r'rgba\(0,0,0,0?\.\d+\)')
HEX_OR_RGBA = re.compile(r'#[0-9A-Fa-f]{3,8}\b|rgba?\([^)]*\)')

ADOPTION = '''
/* ── SYSTEM ADOPTION — what the bridge used to do, now stated once and by role ──
   A reconstruction plate quotes somebody else's product; it owns its whole interior,
   ink and edges alike, and the system's roles are re-pointed at ITS palette so every
   rule inside it resolves against the plate rather than the page. */
:is(.plA, .plF, .plM, .plO, .plP, .plV, .recon, [class*="-app"], [class*="-paper"],
    .plA-caption, .plF-caption, .plM-caption, .plO-caption, .plP-caption, .plV-caption, .recon-caption) {
  --text-body: #16181D; --text-muted: #282B31; --text-faint: #3C4148;
  --border-hairline: #E3E6EA; --border-strong: #C6CBD2;
  --accent-text: #5C420E; --accent-fill: #5C420E; --acc-amber: #7A5410;   /* the plate's own gold: a caption over its grey chrome read 2.83:1 in the page amber */
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--text-primary) 14%, transparent),
              0 1px 2px color-mix(in srgb, var(--text-primary) 8%, transparent);
  filter: none;
}
/* A PAPER OBJECT paints paper wherever it sits. The boarding pass in the closing bookend read
   var(--cream) → the page ground, which on a bookend is dark: a cream ticket went black (Arpit
   caught it, 2026-09-12). Objects read the object tokens, and re-point the roles their
   interiors use so nothing inside them follows the page. */
:is(.pass, .bp, .qc, .psc, .cf, .env, .spec-tag, .lug) {
  background: var(--obj-paper); color: var(--obj-paper-ink);
  --surface-page: var(--obj-paper); --surface-card: var(--obj-paper-2); --text-primary: var(--obj-paper-ink);
  --text-body: var(--obj-paper-ink); --text-muted: var(--obj-paper-soft); --text-faint: var(--obj-paper-soft);
  --border-strong: var(--obj-paper-rule); --border-hairline: var(--obj-paper-rule);
  --acc-copper: var(--stamp-red); --accent-text: var(--stamp-red);
}
/* the site's own instruments are charts, not screenshots: on paper a bar needs a track.
   Not scoped to main: on the case pages the panels sit outside it (found live, 2026-09-12). */
.vg { background: var(--surface-card); border: 1px solid var(--border-strong);
  --a: var(--act); }
.vg-hero .vg { background: var(--surface-card); }
.vg .vg-hd { border-bottom-color: var(--border-hairline); }
.vg :is(.vg-verdict, .vg-note, .vg-after, .vg-bill) { border-top-color: var(--border-hairline); }
.vg :is(.vg-met s, .vg-sig span, .vg-conf span, .vg-allows span) { background: var(--bar-track); }
.vg .vg-met s::after { background: linear-gradient(90deg, transparent, var(--bar-track), transparent); }
.vg :is(.vg-row b, .vg-plats li) { border-color: var(--border-hairline); background: var(--ink-wash); }
.vg .vg-spine span { background: var(--surface-sunken); color: var(--text-body); }
.vg .vg-allows .nobar span {
  background: repeating-linear-gradient(90deg, var(--bar-track) 0 3px, transparent 3px 7px); }
:is(.hd-track, .plM-track, .lug-meter) { background: var(--bar-track); }
/* the homepage's acts each name an act accent — the system's six are interchangeable */
body.p-home .work     { --act: var(--acc-copper); }
body.p-home .who      { --act: var(--acc-violet); }
body.p-home .aiwork   { --act: var(--acc-amber);  }
body.p-home .voices   { --act: var(--acc-rose);   }
body.p-home .contract { --act: var(--acc-amber);  }
body.p-home .labrow   { --act: var(--acc-violet); }
'''

TOKENS_LAYER = '''
@layer tokens {
/* ── the site's own tokens, declared on every carrier the system re-derives tier 2 on,
   so they resolve against THAT carrier's roles: paper on the page, light on a bookend,
   one stop deeper on a tint. A custom property resolves where it is declared. */
:root, [data-ground="bookend"], [data-tint], .a-tinted {
  --act-2: var(--acc-violet);                 /* the second stop of a two-accent gradient */
  --cta-grad: linear-gradient(92deg, var(--acc-copper), var(--acc-amber));
  --cta-grad-hover: linear-gradient(92deg, var(--copper-700), var(--amber-700));   /* one stop deeper on paper */
  --cta-fill-hover-copper: var(--copper-700);   /* F: one stop deeper on paper */
  --ink-wash: color-mix(in srgb, var(--text-primary) 5%, transparent);   /* a raised fill */
  --act-wash: color-mix(in srgb, var(--act) 8%, transparent);            /* a hover fill */
  --link-ink: var(--acc-violet);              /* this site's links are violet, by decision */
  --door-ink: var(--violet-700);              /* a quiet door: one stop deeper than a link, so it reads the same on paper and on a tint (cta-grammar-check saw two inks for one component) */
  --link-ink-hover: color-mix(in srgb, var(--acc-violet) 78%, var(--text-primary));
}/* a control edge on the bookend owes 1.4.11 its 3:1; the system's 37% cream measured 2.83:1
   on this site's #140C16 (nontext-contrast-check) — 42% clears it. Logged for the system. */
[data-ground="bookend"]{--border-strong:color-mix(in srgb, var(--neutral-100) 42%, transparent); --door-ink:var(--violet-100);
  --cta-grad-hover:linear-gradient(92deg, var(--copper-50), var(--amber-50)); --cta-fill-hover-copper:var(--copper-50)}   /* one stop lighter on a bookend */
}
'''


OBJ_RENAME = [('--paper-rule', '--obj-paper-rule'), ('--paper-soft', '--obj-paper-soft'),
              ('--paper-ink', '--obj-paper-ink'), ('--paper-2', '--obj-paper-2'), ('--paper', '--obj-paper')]


def rename_paper_objects(css):
    """9. The receipts, boarding pass and QC slip are paper OBJECTS with their own five tokens
    named --paper*. The system's tier-1 ground token is ALSO --paper, and the site's :root
    declaration shadowed it: --surface-page became #F7F3EC everywhere (found by the sweep:
    830 prose nodes at 1.24:1). Objects keep their palette under a name that says so."""
    for old, new in OBJ_RENAME:
        css = re.sub(re.escape(old) + r'(?![A-Za-z0-9_-])', new, css)
    return css


def blank(css):
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def rename_refs(css):
    for old, new in sorted(RENAME.items(), key=lambda kv: -len(kv[0])):
        css = re.sub(re.escape(old) + r'(?![A-Za-z0-9_-])', new, css)
    return css


def rewrite_rule(head, body, ctx, stats):
    """One rule: rename, delete, replace. Returns new body or None to drop the rule."""
    bare = re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()
    in_plate = bool(PLATE.search(bare))
    in_print = 'print' in ctx
    out = []
    for d in body.split(';'):
        if ':' not in d:
            if d.strip(): out.append(d)
            continue
        prop, val = d.split(':', 1)
        p, v = re.sub(r'/\*@@\d+@@\*/', '', prop).strip(), val.strip()
        lead = prop[:len(prop) - len(prop.lstrip())] + ''.join(re.findall(r'/\*@@\d+@@\*/', prop))
        # 3 · the page family's heat becomes its act accent
        if p == '--heat' and bare in FAMILY_ACT and not v.startswith('var('):
            out.append(f'--act:var(--acc-{FAMILY_ACT[bare]})'); stats['act'] += 1; continue
        if p == '--heat2':
            stats['deleted'] += 1; continue
        if p == '--lt':
            out.append('--lt:color-mix(in srgb, var(--lc) 10%, transparent)'); continue
        p2 = rename_refs(p)
        v2 = rename_refs(v)
        d2 = f'{lead}{p2}:{v2}'
        # self-reference after rename = a bridge map line; drop it
        if p2.startswith('--') and v2 == f'var({p2})':
            stats['selfref'] += 1; continue
        # 2 · the old palettes go, outside the plates
        if p2 in DELETE_DECL and not in_plate:
            if not v2.startswith('var(') or HEX_OR_RGBA.search(v2):
                stats['deleted'] += 1; continue
        if in_print or in_plate:
            out.append(d2); continue
        # 5 · fields: mid-page ones die, bookend ones read --glow
        if 'radial-gradient' in v2 and p2.startswith('background'):
            if '::' in bare and not any(k in bare for k in ('.hero', '.close', 'case-hero', 'first-of-type')):
                stats['glow-deleted'] += 1; return None
            out.append(f'{p2}:var(--glow)'); stats['glow'] += 1; continue
        # 4 · raw colours -> roles
        if p2.startswith('box-shadow') and LIFT.search(v2):
            out.append(f'{p2}:var(--elev-2)'); stats['lift'] += 1; continue
        if p2.startswith('box-shadow') and '#fff' in v2.lower():
            stats['deleted'] += 1; continue
        def sub(m):
            lit = m.group(0)
            key = lit.upper() if lit.startswith('#') else lit.replace(' ', '')
            am = ALPHA_INK.match(key)
            if am:
                stats['literal'] += 1; return f'var({_alpha_role(am.group(1), p2)})'
            if key in LITERALS:
                stats['literal'] += 1
                role = LITERALS[key]
                if role.startswith('MIX:'):
                    _, tok, pct = role.split(':'); return f'color-mix(in srgb, var({tok}) {pct}%, transparent)'
                return f'var({role})'
            stats['kept'][key] += 1
            stats['kept_where'][key].append(f'{bare[:50]} {p2}')
            return lit
        if p2.startswith('--') or p2 in ('color', 'background', 'background-color', 'background-image',
                                          'border-color', 'outline-color', 'fill', 'stroke', 'accent-color',
                                          'text-decoration-color') or p2.startswith('border'):
            v3 = HEX_OR_RGBA.sub(sub, v2)
            out.append(f'{p2}:{v3}'); continue
        out.append(d2)
    return ';'.join(x.strip() for x in out if x.strip())


def walk(css, ctx, stats):
    out = []
    for kind, head, body in L.split_rules(css):
        bare = re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()
        if kind == 'rule':
            nb = rewrite_rule(head, body, ctx, stats)
            if nb is None: continue
            if not nb.strip():
                stats['emptied'] += 1; continue
            out.append(f'{head}{{{nb}}}')
        elif kind == 'at' and bare.startswith(('@media', '@supports', '@container', '@layer', '@keyframes')):
            out.append(f'{head}{{{walk(body, ctx + " " + bare, stats)}}}')
        elif kind == 'at':
            out.append(f'{head}{{{body}}}')
        else:
            out.append(head)
    return '\n'.join(out)


def protect(css):
    table = []
    def sub(m):
        table.append(m.group(0)); return f'/*@@{len(table)-1}@@*/'
    return re.sub(r'/\*.*?\*/', sub, css, flags=re.S), table


def restore(css, table):
    return re.sub(r'/\*@@(\d+)@@\*/', lambda m: table[int(m.group(1))], css)


TINT_CLASSES = ['bcard', 'rcpt-r', 'rcpt-r-tight', 'card-p28', 'card-p32', 'hd-card', 'case-vitals',
                'measure-t', 'lab-body', 'td-block', 'lint-grid', 'section-inner', 'philosophy-cards', 'card-wire', 'thesis', 'scr-close']


def stamp_tints(check):
    n = 0; per = collections.Counter()
    pat = re.compile(r'<([a-z0-9]+)([^>]*?)\sclass="([^"]*)"([^>]*)>')
    for p in ROOT.rglob('*.html'):
        if any(x in p.parts for x in ('prototypes', 'node_modules', '.claude', 'portfolio-sources', 'book')):
            continue
        s = p.read_text(encoding='utf-8')
        def sub(m):
            nonlocal n
            classes = m.group(3).split()
            hit = [c for c in TINT_CLASSES if c in classes]
            if not hit or 'data-tint' in m.group(0): return m.group(0)
            n += 1; per[hit[0]] += 1
            return f'<{m.group(1)}{m.group(2)} class="{m.group(3)}"{m.group(4)} data-tint>'
        t = pat.sub(sub, s)
        if t != s and not check: p.write_text(t, encoding='utf-8')
    print(f"  data-tint stamped on {n} elements: " + ', '.join(f'{k} {v}' for k, v in per.most_common()))
    return n


def rename_outside(check):
    """8. Page <style> blocks and script-injected CSS speak the same names. Found by the
    census: patterns/demos.js drew its demo buttons with `border:1px solid var(--border)`,
    and once --border was no longer declared anywhere the whole border shorthand became
    invalid and the buttons lost their edge — a 5px shift on nine pages."""
    import subprocess
    files = subprocess.run(['git', 'ls-files', '*.html', '*.js'], cwd=ROOT, capture_output=True, text=True).stdout.split()
    total = 0
    for f in files:
        if f.startswith(('prototypes/', 'book/', 'portfolio-sources/')): continue
        fp = ROOT / f; s = fp.read_text(encoding='utf-8')
        t = rename_refs(s)
        if t != s:
            n = sum(1 for a, b in zip(s.split('var('), t.split('var(')) if a != b)
            total += n; print(f'  {f}: {n} reference(s) renamed')
            if not check: fp.write_text(t, encoding='utf-8')
    left = 0
    for f in files:
        if f.startswith(('prototypes/', 'book/', 'portfolio-sources/')): continue
        s = (ROOT / f).read_text(encoding='utf-8')
        left += sum(len(re.findall(r'var\(' + re.escape(n) + r'(?![A-Za-z0-9_-])', s)) for n in RENAME)
    print(f'  old names referenced outside site.css after: {left}')
    return left == 0


def main():
    check = '--check' in sys.argv
    if '--outside-only' in sys.argv:
        return 0 if rename_outside(check) else 1
    src = SITE.read_text(encoding='utf-8')
    # the bridge section is replaced wholesale by the hand-written adoption block
    i = src.index('/* ── from amber-bridge.css ── */')
    j = src.index('\n}\n\n@layer utilities {', i)
    src = src[:i] + src[j:]     # the adoption block is appended to the END of overrides below
    prot, table = protect(src)
    stats = collections.Counter(); stats['kept'] = collections.Counter(); stats['kept_where'] = collections.defaultdict(list)
    out = walk(prot, '', stats)
    out = restore(out, table)
    out = rename_paper_objects(out)
    # 10. under the dark theme the case hero was transparent so the dark body showed through;
    #     under amber the body is paper, so a bookend that does not paint is a paper hero
    out, n = re.subn(r'(body\[class\*="p-case-studies"\] \.case-hero\{[^}]*?)background:transparent;?', r'\1', out)
    stats['hero-transparent'] = n
    # 11. --act resolves where it is declared: set on <body> it is the PAPER value by the time a
    #     bookend inherits it (2.99:1 on a hero statistic). Every bookend and tint beneath a
    #     family re-declares it — generated from the table, never scraped from the text.
    fam = dict(FAMILY_ACT); fam.update({'body.p-home .work': 'copper', 'body.p-home .who': 'violet',
        'body.p-home .aiwork': 'amber', 'body.p-home .voices': 'rose', 'body.p-home .contract': 'amber',
        'body.p-home .labrow': 'violet', 'body.p-home .qvoices': 'rose'})
    act_block = ('\n/* ── THE ACT ACCENT RE-RESOLVES BENEATH ITS FAMILY (see css-adopt-tokens.py, step 11) ── */\n'
                 + '\n'.join(f'{sel} [data-ground="bookend"], {sel} [data-tint]{{--act:var(--acc-{acc})}}'
                              for sel, acc in fam.items()) + '\n')
    ob = blank(out).rindex('}')                      # the overrides layer's closing brace
    out = out[:ob] + ADOPTION + act_block + out[ob:]   # adoption LAST, so its tracks and panels win
    # 12. THE TYPE SCALE IS THE SYSTEM'S (Arpit, 2026-09-12: "B — adopt the system's scale").
    #     DESIGN-SYSTEM.md recorded body 16 / section 31; the system measured 18 / 35–46 for
    #     reading comfort on its pilots and he chose it. The site's --fs-* names stay (hundreds
    #     of rules read them) and now point at the system's stops, declared where the old
    #     :root declared them so nothing else has to change.
    TYPE = {'--fs-body': '18px', '--fs-lead': '21px', '--fs-card': '22px', '--fs-title': 'clamp(35px,2.9vw,46px)',
            '--fs-title-lg': 'clamp(40px,5vw,55px)', '--fs-hero': 'clamp(40px,5.5vw,64px)', '--fs-ui': '14px',
            '--fs-caption': '13px', '--fs-eyebrow': '12px', '--fs-micro': '12px'}
    for name, val in TYPE.items():
        out, n = re.subn(r'(?<![\w-])' + re.escape(name) + r':[^;}]+', f'{name}:{val}', out, count=1)
        stats['type-scale'] += n
    out = out.replace(':is(.t-body,.u-body){font-size:17px;', ':is(.t-body,.u-body){font-size:var(--fs-body);')
    # the homepage body was pinned to 16px while every other page reads at --fs-body (18): one
    # reading size, and the nav stops computing two trackings (component-identity-check)
    out, n = re.subn(r'(body\.p-home\{[^}]*?)font-size:16px', r'\1font-size:var(--fs-body)', out, count=1); stats['type-scale'] += n
    # 13. THE HEADLINE INK ON A BOOKEND (my call, asked for by Arpit 2026-09-12 with "WOW factor,
    #     accessibility and legibility"): the warmest light stop, neutral-50, 15.9:1 on the
    #     bookend — the reading ink neutral-200 read grey at display size.
    ob = blank(out).rindex('}')
    out = out[:ob] + '\n/* the display ink on a bookend: the warm white, not the reading grey */\n[data-ground="bookend"] :is(h1, .case-hero h1, .hero h1){color:var(--neutral-50)}\n' + out[ob:]
    # 14. THE HOMEPAGE ACT GROUNDS, translated. Arpit's 2026-09-01 pick: "each act sits on a
    #     ground cast from its own accent, fading back to base". On the dark theme that was a
    #     plum cast; on paper the same idea is a faint wash of the act accent fading to paper —
    #     the ink follows the paper and the acts still hand over quietly. (Found on the phone
    #     walk: act headings were dark ink on the dark cast, invisible.)
    cast = 'linear-gradient(180deg, color-mix(in srgb, var(--act) 7%, var(--surface-page)), var(--surface-page))'
    out, n = re.subn(r'(body\.p-home \.(?:receipts|work|who|aiwork|voices|thoughts)(?:,\s*body\.p-home \.\w+)*)\{background:linear-gradient\(180deg,#[0-9A-Fa-f]{6},var\(--surface-sunken\)\)\}',
                     lambda m: f'{m.group(1)}{{background:{cast}}}', out)
    stats['act-grounds'] = n
    # the tokens layer goes right after the layer-order statement
    k = out.index('@layer reset, tokens, ground, type, layout, components, utilities, overrides;\n')
    k += len('@layer reset, tokens, ground, type, layout, components, utilities, overrides;\n')
    out = out[:k] + TOKENS_LAYER + out[k:]

    ok = True
    def assert_(c, msg):
        nonlocal ok; print(('  ok   ' if c else '  FAIL ') + msg); ok = ok and c
    code = blank(out)
    left = sorted({m for m in re.findall(r'var\((--[A-Za-z0-9_-]+)', code) if m in RENAME})
    assert_(not left, f'no site colour name referenced any more ({len(left)}: {", ".join(left[:10])})')
    self_ref = re.findall(r'(--[\w-]+)\s*:\s*var\(\1\)', code)
    assert_(not self_ref, f'no self-referencing declarations ({len(self_ref)})')
    depth = 0; bad = None
    for ch in code:
        depth += (ch == '{') - (ch == '}')
        if depth < 0: bad = 'orphan }'; break
    assert_(bad is None and depth == 0, 'braces balanced')
    amber = (ROOT / 'amber.css').read_text(encoding='utf-8')
    declared = set(re.findall(r'(--[A-Za-z0-9_-]+)\s*:', amber + out))
    inline = set()
    for hp in ROOT.rglob('*.html'):
        if any(x in hp.parts for x in ('node_modules', '.claude', 'prototypes')): continue
        inline |= set(re.findall(r'style="[^"]*?(--[A-Za-z0-9_-]+)\s*:', hp.read_text(encoding='utf-8', errors='ignore')))
    unresolved = sorted({n for n, sep in re.findall(r'var\((--[A-Za-z0-9_-]+)\s*([,)])', code)
                         if n not in declared and n not in inline and sep == ')'})
    assert_(set(unresolved) <= {'--ff-serif', '--ink-faint', '--o'}, f'no new unresolved var() ({unresolved})')
    print(f"  renamed refs; deleted {stats['deleted']} palette declarations, {stats['selfref']} map lines, "
          f"{stats['emptied']} emptied rules; {stats['act']} families -> --act; "
          f"{stats['literal']} raw colours -> roles; {stats['lift']} lifts -> --elev-2; "
          f"{stats['glow']} fields -> --glow, {stats['glow-deleted']} mid-page fields deleted; "
          f"hero transparent removed x{stats['hero-transparent']}; --act re-declared beneath {len(fam)} families; "
          f"type tokens re-pointed {stats['type-scale']}")
    kept = stats['kept']
    print(f"  raw colours still painted outside plates/print: {sum(kept.values())} in {len(kept)} literals")
    for lit, n in kept.most_common(30):
        print(f"     x{n:<3} {lit:22s} {' | '.join(stats['kept_where'][lit][:2])[:100]}")
    print(f"  site.css: {out.count(chr(10)):,} lines")
    scratch = pathlib.Path('/private/tmp/claude-501/-Users-arpit-Code-git/91c61cad-dfbf-4e82-be35-f03d6fd108c1/scratchpad/site.adopt.check.css')
    scratch.write_text(out)
    if not ok:
        print(f'NOT WRITTEN (inspectable copy at {scratch})'); return 1
    if check:
        print('--check: nothing written'); return 0
    SITE.write_text(out, encoding='utf-8'); print('  written site.css')
    stamp_tints(check)
    return 0 if rename_outside(check) else 1


if __name__ == '__main__':
    sys.exit(main())
