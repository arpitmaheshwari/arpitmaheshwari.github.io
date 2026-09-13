#!/usr/bin/env python3
"""extract-pages.py — ONE-OFF: cut every classic page into its pages/ source, then prove the round trip.

For each classic page (gatelib.pages, book excluded) it writes pages/<rel> holding the five verbatim
regions build-pages.py expects, plus the layout. Then build-pages.py --check must report 0 of 35
differing — that is the proof the split lost nothing. Run once on 2026-09-13; kept for the record.
"""
import pathlib, re, sys, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gatelib import pages

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / 'partials' / 'pages'
_spec = importlib.util.spec_from_file_location('build_partials', ROOT / 'tools' / 'build-partials.py')
bp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(bp)

LAYOUT = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n{{HEAD}}</head>\n'
          '<body class="{{BODY_CLASS}}">\n<a href="#main" class="skip-link">Skip to content</a>\n'
          '{{PRE_NAV}}{{NAV}}{{CONTENT}}{{FOOTER}}{{TAIL}}</body>\n</html>\n')


def split(s, rel):
    assert s.startswith('<!DOCTYPE html>\n<html lang="en">\n<head>\n'), rel
    head_end = s.index('</head>')
    head = s[len('<!DOCTYPE html>\n<html lang="en">\n<head>\n'):head_end]
    m = re.search(r'</head>\n<body class="([^"]*)">\n<a href="#main" class="skip-link">Skip to content</a>\n', s)
    assert m and m.start() == head_end, rel
    body_class = m.group(1)
    after_skip = m.end()
    mn = bp.NAV_RE.search(s); mf = bp.FOOTER_RE.search(s)
    assert mn and mf and mn.start() >= after_skip, rel
    pre_nav = s[after_skip:mn.start()]
    content = s[mn.end():mf.start()]
    tail_all = s[mf.end():]
    assert tail_all.endswith('</body>\n</html>\n'), rel
    tail = tail_all[:-len('</body>\n</html>\n')]
    note = bp.footer_note(mf.group(0)) or ''
    return body_class, note, head, pre_nav, content, tail


def main():
    PAGES.mkdir(exist_ok=True)
    (PAGES / '_layout.html').write_text(LAYOUT, encoding='utf-8')
    n = 0
    for rel in pages(include_book=False):
        s = (ROOT / rel).read_text(encoding='utf-8')
        body_class, note, head, pre_nav, content, tail = split(s, rel)
        for k, v in (('head', head), ('pre-nav', pre_nav), ('content', content), ('tail', tail)):
            assert f'<!--/{k}-->' not in v and f'<!--{k}-->' not in v, (rel, k)
        src = (f'<!--page body_class="{body_class}" footer_note="{note}"-->\n'
               f'<!--head-->{head}<!--/head-->\n<!--pre-nav-->{pre_nav}<!--/pre-nav-->\n'
               f'<!--content-->{content}<!--/content-->\n<!--tail-->{tail}<!--/tail-->\n')
        out = PAGES / rel; out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(src, encoding='utf-8'); n += 1
    print(f'{n} page(s) extracted into partials/pages/ + partials/pages/_layout.html; now: python3 tools/build-pages.py --check')


if __name__ == '__main__':
    sys.exit(main())
