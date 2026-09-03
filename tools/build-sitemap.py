#!/usr/bin/env python3
"""Regenerate sitemap.xml with a per-page <lastmod> derived from git.

Every one of the 36 URLs carried the same hard-coded lastmod, 2026-08-16, which was 18 days
stale by 2026-09-03 and identical across pages that had plainly changed at different times.
A crawler reads lastmod as a claim about the page; one date for everything is either ignored
or believed, and both are bad.

The date is the last revision whose VISIBLE PROSE inside <main> actually differs — the same
definition tools/freshness-check.py uses, so the sitemap and the on-page "Last updated" line
can never disagree about what an update is. Version stamps and footer partials do not count.

  python3 tools/build-sitemap.py           rewrite sitemap.xml
  python3 tools/build-sitemap.py --check   fail if any lastmod is stale (used by the gate)
"""
import html, os, re, subprocess, sys
import xml.etree.ElementTree as ET

NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://arpitmaheshwari.com/'
MAX_WALK = 60


def visible_main(blob):
    m = re.search(r'(?is)<main\b[^>]*>(.*)</main>', blob)
    if not m:
        return ''
    s = re.sub(r'(?is)<(script|style|svg)\b[^>]*>.*?</\1>', ' ', m.group(1))
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s))).strip()


def last_prose_change(path):
    log = [l.split() for l in subprocess.run(
        ['git', 'log', '--format=%H %cs', '--', path], cwd=ROOT,
        capture_output=True, text=True).stdout.strip().split('\n') if l.strip()]
    prev, newest = None, None
    for sha, date in log[:MAX_WALK]:
        blob = subprocess.run(['git', 'show', f'{sha}:{path}'], cwd=ROOT,
                              capture_output=True, text=True).stdout
        cur = visible_main(blob)
        if prev is None:
            prev, newest = cur, date
            continue
        if cur != prev:
            break
        newest = date
    return newest


def path_for(url):
    rel = url.replace(SITE, '')
    if rel == '':
        return 'index.html'
    if rel.endswith('/'):
        return rel + 'index.html'
    return rel


def main():
    check = '--check' in sys.argv
    ET.register_namespace('', NS)
    tree = ET.parse(os.path.join(ROOT, 'sitemap.xml'))
    root = tree.getroot()
    stale, updated = [], 0
    for url in root.iter(f'{{{NS}}}url'):
        loc = url.find(f'{{{NS}}}loc').text.strip()
        rel = path_for(loc)
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        real = last_prose_change(rel)
        if not real:
            continue
        node = url.find(f'{{{NS}}}lastmod')
        if node is None:
            node = ET.SubElement(url, f'{{{NS}}}lastmod')
            node.text = ''
        if node.text != real:
            if check:
                stale.append((rel, node.text, real))
            else:
                node.text = real
                updated += 1
    if check:
        for rel, was, real in stale:
            print(f"  STALE  {rel}\n         sitemap says {was}, prose last changed {real}")
        print(f"\n{len(stale)} stale <lastmod> entr(ies) in sitemap.xml")
        print("Run: python3 tools/build-sitemap.py")
        return 1 if stale else 0
    tree.write(os.path.join(ROOT, 'sitemap.xml'), encoding='UTF-8', xml_declaration=True)
    print(f"sitemap.xml: {updated} <lastmod> entr(ies) rewritten from git")
    return 0


if __name__ == '__main__':
    sys.exit(main())
