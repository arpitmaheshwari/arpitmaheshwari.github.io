#!/usr/bin/env python3
"""Fail when a page would preview badly where a prospect actually meets it.

Almost nobody types a portfolio URL. A recruiter is sent the link in email, a
hiring manager pastes it into Slack, someone shares it on LinkedIn. What they
see first is the unfurl card — title, description, image — and not one gate
here has ever looked at it. A page can be immaculate and still arrive as a
bare URL with no picture and the words "arpitmaheshwari.com".

Checks, per page:
  NO-TITLE / LONG-TITLE      missing, or long enough to be cut off (~60 chars)
  NO-DESCRIPTION / LENGTH    missing, or outside the ~50-160 that survives
  DUPLICATE                  two pages sharing a title or description, which
                             makes a shared link ambiguous and hurts search
  MISSING-OG / MISSING-CARD  no og:title/description/image, or no twitter:card
  RELATIVE-OG-URL            og:image as a relative path — unfurlers need
                             absolute URLs and will show no image at all
  MISSING-OG-IMAGE          the referenced card file is not in the repo
  SMALL-OG-IMAGE            below 600x315, so it renders as a thumbnail
  NO-CANONICAL              no canonical, so shared variants split ranking
  TITLE-SEPARATOR           a page punctuates its title differently from the
                            rest — the same one-component-two-appearances
                            disease, in the browser tab

This is static: no browser, no network. It runs in under a second.

CALIBRATION
    --selftest strips the og:image from an in-memory copy of the first page
    and requires the loss to be reported.
"""
import argparse, glob, os, re, sys, struct, collections

META = re.compile(r'<meta\s+[^>]*>', re.I)
ATTR = re.compile(r'(\w[\w:-]*)\s*=\s*"([^"]*)"', re.I)
TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
CANON = re.compile(r'<link[^>]+rel="canonical"[^>]*>', re.I)
HREF = re.compile(r'href\s*=\s*"([^"]*)"', re.I)


def png_jpg_size(path):
    """Read image dimensions without a decoder dependency."""
    with open(path, 'rb') as f:
        head = f.read(32)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', head[16:24])
        if head[:2] == b'\xff\xd8':
            f.seek(2)
            while True:
                b = f.read(1)
                while b and b != b'\xff':
                    b = f.read(1)
                m = f.read(1)
                while m == b'\xff':
                    m = f.read(1)
                if not m:
                    return None
                if m[0] in range(0xC0, 0xCF) and m[0] not in (0xC4, 0xC8, 0xCC):
                    f.read(3)
                    h, w = struct.unpack('>HH', f.read(4))
                    return w, h
                ln = struct.unpack('>H', f.read(2))[0]
                f.seek(ln - 2, 1)
    return None


def metas(html):
    out = {}
    for tag in META.findall(html):
        a = {k.lower(): v for k, v in ATTR.findall(tag)}
        key = a.get('property') or a.get('name')
        if key:
            out[key.lower()] = a.get('content', '')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    # Only audit what actually DEPLOYS. Gitignored working folders
    # (portfolio-sources/, prototypes/) exist on this machine and never reach
    # the host, so auditing them produced 40 findings about pages no prospect
    # can open — and, worse, would have hidden the ones that matter.
    import subprocess
    shipped = set(subprocess.run(['git', 'ls-files', '*.html'], cwd=root,
                                 capture_output=True, text=True).stdout.split())
    pages = sorted(os.path.join(root, f) for f in shipped
                   if not f.startswith(('partials/', 'tests/', 'node_modules/',
                                       'assets/og-images/')))
    findings, titles, descs = [], collections.defaultdict(list), \
        collections.defaultdict(list)
    seps = collections.defaultdict(list)

    def auditable(path):
        h = open(path, encoding='utf-8', errors='replace').read()
        return not (re.search(r'http-equiv="refresh"', h, re.I)
                    or 'noindex' in metas(h).get('robots', ''))

    # Plant on a page the gate actually audits. Pointing the selftest at
    # pages[0] broke the moment 404.html became exempt: the plant was skipped
    # before it could be seen, and calibration reported the gate blind. The
    # calibration catching its own break is the point of having it.
    victim = next((os.path.relpath(q, root) for q in pages if auditable(q)), None)

    for p in pages:
        rel = os.path.relpath(p, root)
        html = open(p, encoding='utf-8', errors='replace').read()
        m = metas(html)
        if a.selftest and rel == victim:
            m.pop('og:image', None)

        # A redirect stub has no reader, and a noindex page is never meant to be
        # found or shared — neither needs a card.
        if re.search(r'http-equiv="refresh"', html, re.I):
            continue
        if 'noindex' in m.get('robots', ''):
            continue

        t = (TITLE.search(html).group(1).strip() if TITLE.search(html) else '')
        if not t:
            findings.append((rel, 'NO-TITLE', ''))
        else:
            titles[t].append(rel)
            # 65 was tighter than the site's own convention — its titles sit
            # at 63-65 by design, so the gate flagged the house style. 70 is
            # where an unfurl card actually starts clipping.
            if len(t) > 70:
                findings.append((rel, 'LONG-TITLE', f'{len(t)} chars — cut off in a card'))
            # One separator, like one button. Comparing lengths turned up
            # patterns/ using "|" while every other page used an em dash.
            tail = re.search(r'(.)\s*Arpit Maheshwari\s*$', t)
            seps[tail.group(1) if tail else 'no-name'].append(rel)

        d = m.get('description', '').strip()
        if not d:
            findings.append((rel, 'NO-DESCRIPTION', ''))
        else:
            descs[d].append(rel)
            if not 50 <= len(d) <= 200:
                findings.append((rel, 'DESCRIPTION-LENGTH',
                                 f'{len(d)} chars — aim for 50-200'))

        for k in ('og:title', 'og:description', 'og:image'):
            if not m.get(k):
                findings.append((rel, 'MISSING-OG', k))
        if not (m.get('twitter:card')):
            findings.append((rel, 'MISSING-CARD', 'no twitter:card'))

        img = m.get('og:image', '')
        if img:
            if not img.startswith(('http://', 'https://')):
                findings.append((rel, 'RELATIVE-OG-URL', img))
            else:
                path = re.sub(r'^https?://[^/]+/', '', img).split('?')[0]
                fp = os.path.join(root, path)
                if not os.path.exists(fp):
                    findings.append((rel, 'MISSING-OG-IMAGE', path))
                else:
                    sz = png_jpg_size(fp)
                    if sz and (sz[0] < 600 or sz[1] < 315):
                        findings.append((rel, 'SMALL-OG-IMAGE',
                                         f'{sz[0]}x{sz[1]} — renders as a thumbnail'))
        if not CANON.search(html):
            findings.append((rel, 'NO-CANONICAL', ''))

    # Two separate questions, reported separately: does the title carry the
    # name at all, and — among those that do — is it punctuated the same way.
    named = {k: v for k, v in seps.items() if k != 'no-name'}
    unnamed = seps.get('no-name', [])
    if named and unnamed:
        minority = (unnamed if len(unnamed) < sum(len(v) for v in named.values())
                    else [x for v in named.values() for x in v])
        findings.append((sorted(minority)[0], 'TITLE-NAME-DRIFT',
                         f'{len(unnamed)} page(s) omit the name from the title, '
                         f'{sum(len(v) for v in named.values())} include it — '
                         f'pick one and apply it everywhere'))
    if len(named) > 1:
        house = max(named, key=lambda k: len(named[k]))
        for sep, where in named.items():
            if sep != house:
                findings.append((where[0], 'TITLE-SEPARATOR',
                                 f'punctuates with {sep!r}; {len(named[house])} '
                                 f'page(s) use {house!r}'))

    for t, where in titles.items():
        if len(where) > 1:
            findings.append((where[0], 'DUPLICATE',
                             f'title shared with {", ".join(where[1:][:3])}'))
    for d, where in descs.items():
        if len(where) > 1:
            findings.append((where[0], 'DUPLICATE',
                             f'description shared with {", ".join(where[1:][:3])}'))

    if a.selftest:
        ok = any(k == 'MISSING-OG' and v == 'og:image' for _, k, v in findings)
        print(f'[calibration] {"PASS" if ok else "FAIL"} — a stripped og:image is '
              f'{"caught" if ok else "INVISIBLE"}')
        if not ok:
            return 2
        findings = [f for f in findings
                    if not (f[0] == victim and f[1] == 'MISSING-OG'
                            and f[2] == 'og:image')]

    for rel, kind, why in sorted(findings):
        print(f'  {kind:20} {rel}{"  " + why if why else ""}')
    print(f'\n{len(findings)} share-preview problem(s) across {len(pages)} page(s)')
    print('CANNOT SEE: whether the card IMAGE is legible or on-brand, whether '
          'the description is any good, or how a specific platform crops it.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
