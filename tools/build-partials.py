#!/usr/bin/env python3
"""Stamp the shared nav and footer into every page from one source.

WHY (2026-08-19, architecture review)
The nav was inline on 37 pages and the footer on 37, and they had drifted:
37 distinct navs, 29 distinct footers, all supposedly the same component.
That duplication caused real defects — a logo 40px on ten pages and 36px on
twenty-seven, an accessibility toggle present on nineteen pages and missing
from eighteen, a reduced-motion-aware back-to-top button on exactly one.

None of those were decisions. They were the cost of having no single place to
change a shared thing.

HOW IT WORKS
partials/nav.html and partials/footer.html are the source. Each page carries
the rendered result inline, so GitHub Pages still serves plain HTML with no
build at request time and no JavaScript standing between a reader and the
navigation. Running this script re-stamps every page from the partials.

PER-PAGE VALUES ARE PRESERVED, NOT FLATTENED. Before replacing a region the
script reads the values that legitimately differ out of the existing page and
puts them back:
    {{ROOT}}         path depth — ./ or ../ — or absolute for 404.html, which
                     is served from any URL and cannot use relative paths
    aria-current     which nav item is the current section
    {{FOOTER_NOTE}}  the homepage says something different, deliberately

IT ALSO STAMPS CACHE VERSIONS. Every page references styles.css?v=… and
ember.css?v=…; those are computed from the file hash here rather than bumped
by hand across 40 files.

USAGE  build-partials.py [--check]      --check writes nothing, reports drift
"""
import hashlib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAV = (ROOT / 'partials' / 'nav.html').read_text(encoding='utf-8').rstrip('\n')
FOOTER = (ROOT / 'partials' / 'footer.html').read_text(encoding='utf-8').rstrip('\n')

NAV_RE = re.compile(r'<nav id="nav".*?</nav>', re.S)
FOOTER_RE = re.compile(r'<footer.*?</footer>', re.S)

# 404.html is served for any missing URL at any depth, so relative paths break.
ABSOLUTE_PATH_PAGES = {'404.html'}


def all_pages():
    out = subprocess.run(['git', 'ls-files', '*.html'], capture_output=True,
                         text=True, cwd=ROOT).stdout.split()
    return [p for p in out if not p.startswith(('tests/', 'partials/'))
            and 'og-images' not in p]


def pages():
    """Pages that carry the shared nav and footer. The book has neither."""
    return [p for p in all_pages() if not p.startswith('book/')]


def root_for(rel):
    if rel in ABSOLUTE_PATH_PAGES:
        return '/'
    depth = rel.count('/')
    return './' if depth == 0 else '../' * depth


def current_item(nav_html):
    """Which nav link carries aria-current, so it can be put back."""
    m = re.search(r'<a href="([^"]*)"[^>]*aria-current="true"', nav_html)
    return m.group(1).split('#')[-1] if m else None


def footer_note(footer_html):
    m = re.search(r'<div class="footer-note">(.*?)</div>', footer_html, re.S)
    return m.group(1) if m else None


def render(rel, existing_nav, existing_footer):
    root = root_for(rel)
    nav = NAV.replace('{{ROOT}}', root)
    cur = current_item(existing_nav) if existing_nav else None
    if cur:
        # restore the active marker on the same destination it was on
        nav = re.sub(r'(<a href="[^"]*#' + re.escape(cur) + r'")',
                     r'\1 aria-current="true"', nav, count=1)
    # the homepage links its own contact section as a same-page anchor
    if rel == 'index.html':
        nav = nav.replace(f'href="{root}index.html#contact"', 'href="#contact"')
    note = footer_note(existing_footer) if existing_footer else None
    foot = FOOTER.replace('{{ROOT}}', root)
    foot = foot.replace('{{FOOTER_NOTE}}', note if note else
                        'No rights reserved — good patterns should travel')
    return nav, foot


# Scripts were versioned by hand (clarity.js?v=c1, fit.js?v=fit1). Editing
# clarity.js without remembering to bump it shipped the OLD file to every
# reader — Cloudflare keeps serving the cached URL, and the change simply did
# not exist in production. css-version-check has guarded stylesheets against
# exactly this for months; scripts had no such guard. Hash them the same way.
VERSIONED = ('styles.css', 'ember.css', 'fonts.css',
             'analytics.js', 'clarity.js', 'attention.js', 'fit.js',
             'patterns/demos.js', 'data/case-facts.js',
             'lab/loop.js', 'lab/loop.test.js', 'lab/trustlint.js',
             'book/portfolio.js')


def css_versions():
    """A short content hash per versioned asset, so a change always busts the cache."""
    out = {}
    for name in VERSIONED:
        p = ROOT / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()[:8]
    return out


def main():
    check = '--check' in sys.argv
    vers = css_versions()
    changed, drift = [], []
    # The book has no nav or footer to stamp, but it loads portfolio.js and
    # case-facts.js — and a stale script there is the same defect as anywhere
    # else. Partials are stamped on pages(); versions on all_pages().
    partial_pages = set(pages())
    for rel in all_pages():
        p = ROOT / rel
        s = orig = p.read_text(encoding='utf-8')
        if rel not in partial_pages:
            for name, h in css_versions().items():
                base = pathlib.Path(name).name
                stem, ext = base.rsplit('.', 1)
                s = re.sub(re.escape(stem) + r'\.' + ext + r'\?v=[A-Za-z0-9.]+',
                           f'{stem}.{ext}?v={h}', s)
            if s != orig:
                changed.append(rel)
                if not check:
                    p.write_text(s, encoding='utf-8')
            continue
        mn, mf = NAV_RE.search(s), FOOTER_RE.search(s)
        nav, foot = render(rel, mn.group(0) if mn else None,
                           mf.group(0) if mf else None)
        if mn:
            if mn.group(0) != nav:
                drift.append((rel, 'nav'))
            s = s[:mn.start()] + nav + s[mn.end():]
        mf = FOOTER_RE.search(s)
        if mf:
            if mf.group(0) != foot:
                drift.append((rel, 'footer'))
            s = s[:mf.start()] + foot + s[mf.end():]
        for name, h in vers.items():
            base = pathlib.Path(name).name           # book/portfolio.js -> portfolio.js
            stem, ext = base.rsplit('.', 1)
            s = re.sub(re.escape(stem) + r'\.' + ext + r'\?v=[A-Za-z0-9.]+',
                       f'{stem}.{ext}?v={h}', s)
        if s != orig:
            changed.append(rel)
            if not check:
                p.write_text(s, encoding='utf-8')
    print(f"  pages scanned : {len(all_pages())}")
    print(f"  drifted from the partials : {len(drift)}")
    for rel, what in drift[:10]:
        print(f"      {what:<7} {rel}")
    if len(drift) > 10:
        print(f"      ...and {len(drift)-10} more")
    print(f"  css versions  : " + ', '.join(f'{k}={v}' for k, v in vers.items()))
    print(f"  pages rewritten: {len(changed)}" + ("  (--check: nothing written)" if check else ""))
    return 0


if __name__ == '__main__':
    sys.exit(main())
