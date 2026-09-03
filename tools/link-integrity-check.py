#!/usr/bin/env python3
"""Every link must go somewhere. No gate here has ever checked that.

The most embarrassing possible defect on a portfolio a stranger is reading:
they click, and land on a 404. Or they click an anchor in the contents and the
page does not move because the id was renamed. Or an outbound reference to a
client's press release has rotted. Every existing gate asks about how the page
LOOKS; none asks whether its promises resolve.

Three questions, three failure kinds:
  DEAD-INTERNAL   an href to a page or file that is not in the repo
  DEAD-ANCHOR     an href to #something that no element on that page declares
  DEAD-EXTERNAL   an outbound URL that does not answer, or answers 4xx/5xx

CALIBRATION
    --selftest plants a link to a page that cannot exist and requires it to be
    reported. A gate I have not watched go red is not evidence.
"""
import argparse, os, re, sys, glob, urllib.parse, urllib.request, urllib.error
import concurrent.futures as cf
from html.parser import HTMLParser

SHIPPED = set()
SKIP_SCHEMES = ('mailto:', 'tel:', 'javascript:', 'data:', 'sms:')
EXCLUDE_DIRS = ('node_modules/', 'tests/', 'prototypes/', '.git/')
# Gates write __cv.html / __al.html into the repo root while they run.
TEMP_PAGE = '__'


class Links(HTMLParser):
    """Collect hrefs and every id/name a page declares."""
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('name'):
            self.ids.add(a['name'])
        for key in ('href', 'src'):
            v = a.get(key)
            if v and key == 'href' and tag in ('a', 'area'):
                self.hrefs.append((v.strip(), self.getpos()[0]))


def parse(path):
    p = Links()
    p.feed(open(path, encoding='utf-8', errors='replace').read())
    return p


def resolve(page, href, root):
    """Map an href to a repo path, the way a static host would."""
    target = href.split('#')[0].split('?')[0]
    if not target:
        return None                      # pure fragment: same page
    if target.startswith('/'):
        cand = os.path.join(root, target.lstrip('/'))
    else:
        cand = os.path.normpath(os.path.join(os.path.dirname(page), target))
    if os.path.isdir(cand):
        return os.path.join(cand, 'index.html')
    if not os.path.splitext(cand)[1]:
        # extensionless: a host would try /foo.html then /foo/index.html
        for c in (cand + '.html', os.path.join(cand, 'index.html')):
            if os.path.exists(c):
                return c
        return cand + '.html'
    return cand


def head(url, timeout=12):
    req = urllib.request.Request(url, method='GET',
                                 headers={'User-Agent': 'Mozilla/5.0 link-check',
                                          'Accept': '*/*'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, ''
    except urllib.error.HTTPError as e:
        return e.code, e.reason
    except Exception as e:                                   # DNS, TLS, timeout
        return 0, type(e).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--external', action='store_true',
                    help='also dial outbound URLs (slow, needs network)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    import subprocess
    global SHIPPED
    SHIPPED = set(subprocess.run(['git', 'ls-files'], cwd=root,
                                 capture_output=True, text=True).stdout.split())

    pages = sorted(p for p in glob.glob(os.path.join(root, '**/*.html'),
                                        recursive=True)
                   if not any(d in os.path.relpath(p, root).replace(os.sep, '/')
                              for d in EXCLUDE_DIRS)
                   and not os.path.relpath(p, root).startswith('partials/')
                   and not os.path.basename(p).startswith(TEMP_PAGE))

    ids = {}          # page path -> declared ids
    parsed = {}
    for p in pages:
        parsed[p] = parse(p)
        ids[p] = parsed[p].ids

    findings, external, walled = [], {}, []
    planted = ('__selftest_missing_page.html', 0)
    for p in pages:
        rel = os.path.relpath(p, root)
        hrefs = list(parsed[p].hrefs)
        if a.selftest and rel == os.path.relpath(pages[0], root):
            hrefs.append(planted)
        for href, line in hrefs:
            if href.startswith(SKIP_SCHEMES):
                continue
            if href.startswith(('http://', 'https://')):
                external.setdefault(href, []).append(f'{rel}:{line}')
                continue
            tgt = resolve(p, href, root)
            # A gitignored file exists on this machine and never deploys, so a
            # link to it passes locally and 404s for the reader. This gate used
            # to ask the disk; it has to ask what ships.
            if tgt is not None and os.path.exists(tgt):
                trel = os.path.relpath(tgt, root).replace(os.sep, '/')
                if trel not in SHIPPED and not trel.startswith('..'):
                    findings.append(('DEAD-IN-PRODUCTION', rel, line, href,
                                     f'{trel} is not tracked by git — it will '
                                     f'404 on the live site'))
                    continue
            if tgt is not None and not os.path.exists(tgt):
                findings.append(('DEAD-INTERNAL', rel, line, href,
                                 f'no file at {os.path.relpath(tgt, root)}'))
                continue
            frag = href.split('#', 1)[1] if '#' in href else ''
            if frag:
                home = p if tgt is None else tgt
                if home.endswith('.html') and os.path.exists(home):
                    if home not in ids:
                        ids[home] = parse(home).ids
                    if frag not in ids[home] and frag != 'top':
                        findings.append(('DEAD-ANCHOR', rel, line, href,
                                         f'no id="{frag}" on '
                                         f'{os.path.relpath(home, root)}'))

    if a.external and external:
        print(f'dialling {len(external)} outbound URL(s)…')
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            for url, (code, why) in zip(external, ex.map(head, external)):
                if not (code == 0 or code >= 400):
                    continue
                # Verified by hand in a real browser on 2026-09-03: BOTH Medium
                # citations behind this wall are live and say what the page claims
                # — "Talon Outdoor: An Out of Home evolution" (Digital Bulletin,
                # 5 Jul 2021) and "Transition to SaaS with Case Studies of Autodesk
                # and PTC" (Charlene Lower, 12 Jul 2021). Cloudflare answers curl
                # with a challenge page, so no script here can confirm that.
                # A 401/403 is a bot wall, not a dead page — Medium and several
                # publishers serve humans fine and refuse scripts. Reporting
                # those as failures every run is how a gate teaches you to
                # ignore it, so they are surfaced separately and do not block.
                kind = ('BOT-WALLED' if code in (401, 403, 429)
                        else 'DEAD-EXTERNAL')
                for where in external[url]:
                    pg, ln = where.rsplit(':', 1)
                    rec = (kind, pg, int(ln), url,
                           f'{code or "no answer"} {why}'.strip())
                    (walled if kind == 'BOT-WALLED' else findings).append(rec)

    for kind, pg, line, href, why in sorted(findings):
        print(f'  {kind:14} {pg}:{line}\n                 {href}\n                 -> {why}')

    if a.selftest:
        ok = any(f[0] == 'DEAD-INTERNAL' and planted[0] in f[3] for f in findings)
        print(f'[calibration] {"PASS" if ok else "FAIL"} — a planted dead link is '
              f'{"caught" if ok else "INVISIBLE"}')
        if not ok:
            return 2
        findings = [f for f in findings if planted[0] not in f[3]]

    if walled:
        print('\n  Refused an automated request (NOT a verdict — open these by hand once):')
        for _, pg, line, url, why in sorted(set(walled)):
            print(f'    {why:18} {pg}:{line}  {url[:78]}')

    print(f'\n{len(findings)} broken link(s) across {len(pages)} page(s)'
          f'{"" if a.external else "  (outbound not dialled — pass --external)"}')
    print('CANNOT SEE: whether a working link points at the RIGHT thing, '
          'redirects that land somewhere unhelpful, or links built by JS at runtime.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
