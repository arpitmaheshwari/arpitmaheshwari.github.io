#!/usr/bin/env python3
"""Re-skin the classic-era SVG artifacts into the Ember brand and INLINE them.

Why inline: the artifacts load via <img>, where webfonts cannot apply — the
brand fonts would silently fall back. Inlined, they inherit the page's real
fonts and, through CSS custom properties, render correctly under BOTH themes:
every color becomes var(--art-*, CLASSIC-VALUE), so the classic theme (the
production fallback) still sees the original palette, while ember.css
overrides the tokens to the dark instrument language Arpit picked (2026-08-15,
option A for diagrams / option C for document exhibits, scope: everything).

The original files in assets/visuals/ are NOT modified — the book edition
(deliberately classic) keeps using them via <img>.

Zero content drift by construction: only colors, fonts and weights are
rewritten; geometry and every text node pass through untouched.
"""
import pathlib, re, sys

# fill/stroke → token (classic value stays as the var() fallback)
TOKENS = {  # classic hex → token name
    '#F4ECDA': 'art-bg', '#EEE4CE': 'art-card', '#FBF4E6': 'art-card2',
    '#EFE6D2': 'art-card3', '#F2F7F4': 'art-cardgood',
    '#2C2620': 'art-ink', '#22201C': 'art-ink2',
    '#6A6052': 'art-mut', '#6F6350': 'art-mut2', '#5C5346': 'art-mut3',
    '#B6A98D': 'art-dim',
    '#C0512B': 'art-heat', '#2F5D52': 'art-good',
    '#CE9230': 'art-gold', '#D4A85E': 'art-gold', '#A06C0E': 'art-gold',
}
# #998D78 splits by attribute: labels (fill) vs arrows/rules (stroke)
SPLIT = {'#998D78': ('art-label', 'art-arrow')}

# document exhibits (option C): hardcoded rebranded paper, both themes
C_MAP = {
    '#F4ECDA': '#F5EDE6', '#EEE4CE': '#EFE3D7', '#FBF4E6': '#FAF3EC',
    '#EFE6D2': '#EFE3D7', '#F2F7F4': '#EAF0EA',
    '#2C2620': '#241830', '#22201C': '#241830',
    '#6A6052': 'rgba(36,24,48,.65)', '#6F6350': 'rgba(36,24,48,.6)',
    '#5C5346': 'rgba(36,24,48,.55)', '#B6A98D': 'rgba(36,24,48,.35)',
    '#C0512B': '#B84A1F', '#2F5D52': '#2F6B4F',
    '#CE9230': '#9A6A14', '#D4A85E': '#9A6A14', '#A06C0E': '#9A6A14',
}
C_SPLIT = {'#998D78': ('#B84A1F', 'rgba(36,24,48,.4)')}

FONTS = [
    (re.compile(r'font-family="Georgia[^"]*"'), 'font-family="\'Source Serif 4\', Georgia, serif"'),
    (re.compile(r'font-family="ui-sans-serif[^"]*"'), 'font-family="\'Source Sans 3\', system-ui, sans-serif"'),
    (re.compile(r'font-family="[^"]*mono[^"]*"'), 'font-family="\'JetBrains Mono\', ui-monospace, monospace"'),
    (re.compile(r'font-weight="bold"'), 'font-weight="600"'),
]

def translate(svg: str, mode: str) -> str:
    if mode == 'A':
        for hexv, tok in TOKENS.items():
            svg = re.sub(re.escape(hexv), f'var(--{tok}, {hexv})', svg, flags=re.I)
        for hexv, (ftok, stok) in SPLIT.items():
            svg = re.sub(r'fill="' + re.escape(hexv) + '"', f'fill="var(--{ftok}, {hexv})"', svg, flags=re.I)
            svg = re.sub(r'stroke="' + re.escape(hexv) + '"', f'stroke="var(--{stok}, {hexv})"', svg, flags=re.I)
        svg = re.sub(r'rgba\(44,\s*38,\s*32,\s*(0?\.\d+)\)', r'var(--art-line-alpha, rgba(44,38,32,\1))', svg)
        # line alphas keep their own alpha per theme via color-mix-free trick:
        # a single token can't carry per-use alpha, so lines use currentColor-free direct swap:
        svg = svg.replace('var(--art-line-alpha, ', 'var(--art-line, ').replace('var(--art-line, rgba(44,38,32,', 'ARTLINE(')
        svg = re.sub(r'ARTLINE\((0?\.\d+)\)\)', r'rgba(var(--art-line-rgb, 44,38,32),\1)', svg)
        svg = re.sub(r'rgba\(192,\s*81,\s*43,\s*(0?\.\d+)\)', r'rgba(var(--art-heat-rgb, 192,81,43),\1)', svg)
    else:  # C — paper exhibit
        for hexv, val in C_MAP.items():
            svg = re.sub(re.escape(hexv), val, svg, flags=re.I)
        for hexv, (fv, sv) in C_SPLIT.items():
            svg = re.sub(r'fill="' + re.escape(hexv) + '"', f'fill="{fv}"', svg, flags=re.I)
            svg = re.sub(r'stroke="' + re.escape(hexv) + '"', f'stroke="{sv}"', svg, flags=re.I)
        svg = re.sub(r'rgba\(44,\s*38,\s*32,\s*(0?\.\d+)\)', r'rgba(36,24,48,\1)', svg)
        # the ember top rule, sized from the viewBox
        m = re.search(r'viewBox="0 0 (\d+)', svg)
        if m:
            w = m.group(1)
            svg = re.sub(r'(<rect[^>]*fill="#F5EDE6"[^>]*/>)', r'\1<rect x="0" y="0" width="' + w + '" height="8" fill="#FF8A5C"/>', svg, count=1)
    for rx, rep in FONTS:
        svg = rx.sub(rep, svg)
    return svg

def inline(page: pathlib.Path, asset: str, mode: str) -> bool:
    html = page.read_text()
    # find the img tag for this asset
    rx = re.compile(r'<img([^>]*?)src="[^"]*visuals/' + re.escape(asset) + r'(?:\?[^"]*)?"([^>]*?)>')
    m = rx.search(html)
    if not m:
        return False
    attrs = m.group(1) + m.group(2)
    cls = (re.search(r'class="([^"]*)"', attrs) or [None, ''])[1]
    alt = (re.search(r'alt="([^"]*)"', attrs) or [None, ''])[1]
    svg = pathlib.Path('assets/visuals/' + asset).read_text()
    svg = translate(svg, mode)
    # strip xml prolog if any; add class + width styling; keep internal title/desc for a11y
    svg = re.sub(r'^<\?xml[^>]*>\s*', '', svg)
    inject = f'class="{cls}" ' if cls else ''
    if alt and '<title' not in svg:
        inject += f'role="img" aria-label="{alt}" '
    svg = svg.replace('<svg ', f'<svg {inject}style="width:100%;height:auto;display:block" ', 1)
    html = html[:m.start()] + svg + html[m.end():]
    page.write_text(html)
    return True

JOBS = [
    # (page, asset, mode)
    *[(f'patterns/{p}.html', f'pattern-{a}.svg', 'A') for p, a in [
        ('act-review-ignore','act-review-ignore'),('calibration-track-record','calibration'),
        ('capability-contract','capability'),('confidence-scores','confidence'),
        ('ml-explainability','explainability'),('ai-failure-states','failure'),
        ('human-in-loop','loop'),('provenance-citations','provenance'),
        ('reversibility-safe-to-act','reversibility')]],
    *[('patterns/index.html', f'pattern-{a}.svg', 'A') for a in
      ['act-review-ignore','calibration','capability','confidence','explainability',
       'failure','loop','provenance','reversibility']],
    ('case-studies/adtech.html','adtech-plan-not-pick.svg','C'),
    ('case-studies/adtech.html','adtech-brief-reframe.svg','A'),
    ('case-studies/fintech.html','fintech-gate.svg','C'),
    ('case-studies/fintech.html','fintech-two-readers.svg','A'),
    ('case-studies/fintech.html','fintech-pipeline.svg','A'),
    ('case-studies/fintech.html','case-fintech.svg','A'),
    ('case-studies/orgos.html','orgos-said-no.svg','A'),
    ('case-studies/o2.html','o2-replatforming.svg','A'),
    ('case-studies/ptc.html','case-ptc-before.svg','A'),
    ('case-studies/ptc.html','ptc-funnel.svg','A'),
    ('case-studies/ptc.html','ptc-switch-off-ladder.svg','A'),
    ('case-studies/vc-diligence.html','case-vc.svg','A'),
    ('case-studies/vc-diligence.html','vc-signoff.svg','A'),
    ('process/index.html','process-method.svg','A'),
]

if __name__ == '__main__':
    ok = miss = 0
    for page, asset, mode in JOBS:
        if inline(pathlib.Path(page), asset, mode):
            ok += 1; print(f'inlined {mode} {asset} → {page}')
        else:
            miss += 1; print(f'MISS         {asset} in {page}')
    print(f'\n{ok} inlined, {miss} missed')
