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
# The stamped footer region INCLUDES the chant one-liner that precedes <footer>
# in the partial. When the region was only <footer>…</footer>, every build run
# pasted a fresh aside in front while leaving the old ones outside the match —
# five builds put five chant lines on every page (caught by Arpit, 2026-09-01).
# Tempered dot: an aside may not match across its own </aside> or a <footer>.
# With a plain .*? and re.S, a rogue chant aside ANYWHERE on the page anchored the
# match and the replacement swallowed everything between it and the footer —
# main content included (caught by the multiplicity canary's calibration plant).
FOOTER_RE = re.compile(
    r'(?:<aside class="chant chant-line"(?:(?!</aside>|<footer).)*</aside>\s*)*<footer.*?</footer>',
    re.S)

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
    """Which nav link carries aria-current, so it can be put back.

    Nav items may target a hash (#featured-case-studies) or a PAGE (patterns/,
    writing/ — since 2026-09-03 the bar promises pages or main sections only).
    The stored key is the fragment when there is one, else the path tail."""
    m = re.search(r'<a href="([^"]*)"[^>]*aria-current="true"', nav_html)
    if not m:
        return None
    href = m.group(1)
    if "#" in href:
        frag = href.split("#")[-1]
        # legacy markers from before the nav promised pages (2026-09-03)
        return {"patterns": "patterns/", "thoughts": "writing/"}.get(frag, frag)
    return href.rstrip("/").split("/")[-1] + "/"


def footer_note(footer_html):
    m = re.search(r'<div class="footer-note">(.*?)</div>', footer_html, re.S)
    return m.group(1) if m else None


def current_for(rel):
    """The nav destination this page IS, from its path. None if it is not one."""
    if rel == 'index.html':
        return 'index.html'
    top = rel.split('/')[0]
    if top in ('lab', 'patterns', 'writing'):
        return top + '/'
    if top == 'case-studies':
        return '#featured-case-studies'
    return None


def render(rel, existing_nav, existing_footer):
    root = root_for(rel)
    nav = NAV.replace('{{ROOT}}', root)
    # DERIVE the marker from the page's own path rather than copying whatever was
    # there before. Preservation could only ever be as right as the day someone typed
    # it, and it was wrong: /lab/ is a nav item, but lab/index.html and its four
    # sub-pages carried NO aria-current, while patterns/, writing/ and every case study
    # did. A rebuilt nav also dropped the marker silently. Derived, it cannot rot.
    # index.html is deliberately absent here: the bar has no "Home" item (the logo is
    # home), so there is nothing to mark. The book has no shared nav at all.
    cur = current_for(rel) or (current_item(existing_nav) if existing_nav else None)
    if cur:
        # restore the active marker on the same destination it was on
        # The href must END at cur, so a section key never matches a hash link on the
        # same path (index.html vs index.html#featured-case-studies).
        nav = re.sub(r'(<a href="[^"]*' + re.escape(cur) + r'")',
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
# book/book.css was on a HAND-TYPED ?v=69 and shipped stale on 2026-09-03: the mobile
# scroll-fade was added and returning readers would have kept the old stylesheet.
# Same failure as fonts.css earlier this session — a stylesheet outside this list is a
# stylesheet nobody is stamping.
VERSIONED = ('styles.css', 'ember.css', 'fonts.css', 'book/book.css',
             'analytics.js', 'clarity.js', 'attention.js', 'fit.js', 'dyslexia.js', 'nav-inert.js',
             'patterns/demos.js', 'data/case-facts.js',
             'lab/loop.js', 'lab/loop.test.js', 'lab/trustlint.js',
             'book/portfolio.js', 'book/scroll-hint.js')


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
        # Compare version-AGNOSTICALLY. The partial is rendered without ?v= stamps, which
        # are applied further down, so a partial that references a VERSIONED asset (the
        # footer loads dyslexia.js) never matched the stamped page and every page reported
        # drift on every run — including immediately after being written. A drift signal
        # that is always on is not a signal; it would have hidden a real partial change.
        devers = lambda x: re.sub(r'\?v=[A-Za-z0-9.]+', '', x)
        if mn:
            if devers(mn.group(0)) != devers(nav):
                drift.append((rel, 'nav'))
            s = s[:mn.start()] + nav + s[mn.end():]
        mf = FOOTER_RE.search(s)
        if mf:
            if devers(mf.group(0)) != devers(foot):
                drift.append((rel, 'footer'))
            s = s[:mf.start()] + foot + s[mf.end():]
        # A stamped fragment must appear EXACTLY once per stamped page. Five chant
        # lines shipped on every page (2026-09-01) because the stamp region excluded
        # the aside and each build added one more — a class of failure, not an
        # instance: assert multiplicity for every distinctive fragment the partials
        # carry. Pages without a footer (redirect stubs like talon.html) are exempt —
        # the calibration plant surfaced exactly that, which is the assertion working.
        if mf:
            for frag in ('class="chant chant-line"', 'class="footer-logo"', '<footer'):
                n = s.count(frag)
                if n != 1:
                    raise SystemExit(f'STAMP MULTIPLICITY: {rel} carries {n}× {frag!r} (must be exactly 1)')
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
