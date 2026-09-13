#!/usr/bin/env python3
"""build-pages.py — the 35 classic pages are rendered from partials/pages/ into one layout. That is the templater.

WHY (2026-09-13, architecture review #7, Arpit: "go ahead with the python templater, classic pages
only"). Every page carried its own copy of the frame — doctype, head wrapper, body, skip link, nav,
footer, closing tags — and build-partials re-stamped nav, footer and cache versions into 41 files on
every stylesheet change. A page's author had to know the whole frame to add a page. Now the frame is
written once, in partials/pages/_layout.html, and a page is only what differs.

A SOURCE PAGE (partials/pages/<same path as the output>) is five verbatim regions and a small header:

    <!--page body_class="p-home" footer_note="No copyright · Design is for all"-->
    <!--head-->      everything between <head> and </head>, exactly as it was
    <!--pre-nav-->   what sits between the skip link and the nav (a sprite, a banner wrapper)
    <!--content-->   from after </nav> to before <footer
    <!--tail-->      after </footer>, before </body>

Nav and footer are NOT in the source: they come from partials/ through build-partials' own
render() (root prefix, aria-current, footer note) and get the same cache stamps. Byte-identity
with the pages as they were on the night of the switch is the first proof (35 of 35); after that
the layout may change and every page follows.

Usage: build-pages.py          write every output page whose bytes would change
       build-pages.py --check  write nothing; exit 1 if any output differs from its build (a gate)
CANNOT SEE: whether a page's HEAD is sensible — heads are still verbatim per page tonight; folding
their shared lines into the layout is the next step and needs the census/pixel proof, not this.
"""
import importlib.util, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / 'partials' / 'pages'
LAYOUT = PAGES / '_layout.html'
_spec = importlib.util.spec_from_file_location('build_partials', ROOT / 'tools' / 'build-partials.py')
bp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(bp)

HEADER = re.compile(r'^<!--page ([^>]*?)-->\n', re.S)
SLOT = {k: re.compile(rf'<!--{k}-->(.*?)<!--/{k}-->', re.S) for k in ('head', 'pre-nav', 'content', 'tail')}


def attrs(header):
    return dict(re.findall(r'([a-z_]+)="([^"]*)"', header))


def sources():
    return sorted(p for p in PAGES.rglob('*.html') if p.name != '_layout.html')


def render(src_path):
    rel = str(src_path.relative_to(PAGES))
    s = src_path.read_text(encoding='utf-8')
    m = HEADER.match(s)
    if not m:
        raise SystemExit(f'{rel}: missing <!--page …--> header')
    a = attrs(m.group(1))
    slots = {}
    for k, rx in SLOT.items():
        mm = rx.search(s)
        if not mm:
            raise SystemExit(f'{rel}: missing <!--{k}--> slot')
        slots[k] = mm.group(1)
    # nav + footer from the partials, exactly as build-partials renders them for this path
    fake_footer = f'<footer><div class="footer-note">{a.get("footer_note", "")}</div></footer>' if a.get('footer_note') else None
    nav, foot = bp.render(rel, None, fake_footer)
    page = (LAYOUT.read_text(encoding='utf-8')
            .replace('{{HEAD}}', slots['head']).replace('{{BODY_CLASS}}', a['body_class'])
            .replace('{{PRE_NAV}}', slots['pre-nav']).replace('{{NAV}}', nav)
            .replace('{{CONTENT}}', slots['content']).replace('{{FOOTER}}', foot)
            .replace('{{TAIL}}', slots['tail']))
    # cache stamps, the same way build-partials applies them
    for name, h in bp.css_versions().items():
        stem, ext = pathlib.Path(name).name.rsplit('.', 1)
        page = re.sub(re.escape(stem) + r'\.' + ext + r'\?v=[A-Za-z0-9.]+', f'{stem}.{ext}?v={h}', page)
    return rel, page


def main():
    check = '--check' in sys.argv
    changed = []
    for src in sources():
        rel, page = render(src)
        out = ROOT / rel
        cur = out.read_text(encoding='utf-8') if out.exists() else None
        if cur != page:
            changed.append(rel)
            if not check:
                out.write_text(page, encoding='utf-8')
    n = len(list(sources()))
    if check:
        for rel in changed: print(f'  DIFFERS  {rel}')
        print(f'{len(changed)} of {n} page(s) differ from their build. CANNOT SEE: whether the layout or a page is good — only that the output is its build.')
        return 1 if changed else 0
    print(f'  pages rendered: {n} · written: {len(changed)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
