#!/usr/bin/env python3
"""gatelib.py — the four things every gate needs, defined once.

WHY THIS EXISTS. On 2026-09-04 a template file (partials/nav.html, which ships the
literal string {{ROOT}}assets/logo-ember.svg) was being counted as a shipped page. The
one-line exclusion had to be added to THREE separate files, because asset-load-check.py,
contrast-audit.py and overflow-sweep.py each carried their own private copy of "what
counts as a page". Each copy had drifted: two excluded redirect stubs, one did not.

A definition that lives in three places is three definitions. This is the one.

    from gatelib import pages, page_urls, visible_text, Browser, ensure_server

Tools are run from the repo root, so `sys.path.insert(0, 'tools')` or an
`os.path.dirname(__file__)` insert is the usual import preamble.
"""
import contextlib
import os
import re
import subprocess
import time

# Re-exported so a tool needs one import, not three. cdp owns the Chrome and server
# details; this module owns what a gate is pointed AT.
from cdp import Browser, ensure_server  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that hold no shipped page.
#   prototypes/        working files, gitignored, never deployed
#   assets/            images and the two OG-card generator templates
#   portfolio-sources/ source material and vendored node_modules
#   tests/             the Playwright harness, not the site
#   partials/          TEMPLATES: they contain literal {{ROOT}} placeholders that no
#                      browser can resolve. This is the exclusion that was missing.
NOT_PAGES = ('prototypes/', 'assets/', 'portfolio-sources/', 'tests/', 'partials/')

_REDIRECT = re.compile(r'http-equiv="refresh"', re.I)
_TAG = re.compile(r'<[^>]+>')
_DROP = re.compile(r'(?is)<(script|style|svg|template)[^>]*>.*?</\1>')
_COMMENT = re.compile(r'(?s)<!--.*?-->')


def pages(include_book=True, include_redirects=False):
    """Every shipped HTML page, as repo-relative paths, sorted.

    include_redirects=False drops the meta-refresh stubs (lab/hitl.html and friends).
    They carry no content of their own, and a gate that loads one races against the
    stub's own navigation — contrast-audit was reporting the DESTINATION page's
    content under the stub's URL before it started excluding them.
    """
    out = subprocess.run(['git', 'ls-files', '*.html'], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    found = []
    for rel in out.splitlines():
        if not rel or rel.startswith(NOT_PAGES):
            continue
        if not include_book and rel.startswith('book/'):
            continue
        if not include_redirects:
            try:
                with open(os.path.join(ROOT, rel), encoding='utf-8', errors='ignore') as fh:
                    if _REDIRECT.search(fh.read()):
                        continue
            except OSError:
                pass
        found.append(rel)
    return sorted(set(found))


def page_urls(base='http://localhost:8000', **kw):
    """The same pages as URLs. index.html becomes /, foo/index.html becomes /foo/."""
    urls = []
    for rel in pages(**kw):
        if rel == 'index.html':
            urls.append(base + '/')
        elif rel.endswith('/index.html'):
            urls.append(f'{base}/{rel[:-len("index.html")]}')
        else:
            urls.append(f'{base}/{rel}')
    return sorted(set(urls))


def visible_text(html, keep_attrs=True):
    """Text a reader actually meets, including text only a screen reader speaks.

    keep_attrs pulls alt / title / aria-label / placeholder out BEFORE tags are
    stripped. prose-check reported clean over nine straight apostrophes and an
    unspaced em dash for months because those live in attributes, and most of this
    site's diagrams carry their description in an aria-label on the <svg> — which is
    inside a block that gets dropped whole. Extract first, drop second.
    """
    import html as _html
    s = _COMMENT.sub(' ', html)
    spoken = ''
    if keep_attrs:
        spoken = '\n'.join(
            m.group(2) for m in
            re.finditer(r'\b(title|aria-label|alt|placeholder)="([^"]{2,})"', s))
    s = _DROP.sub(' ', s)
    s = _TAG.sub('\n', s)
    return _html.unescape(s + ('\n' + spoken if spoken else ''))


if __name__ == '__main__':
    import sys
    if '--urls' in sys.argv:
        for u in page_urls():
            print(u)
    else:
        ps = pages()
        print(f'{len(ps)} shipped page(s)')
        for p in ps:
            print(' ', p)


# --------------------------------------------------------------------------- calibration

LOCK = os.path.join(ROOT, '.gate-source-lock')


@contextlib.contextmanager
def planted(path, addition, timeout=300):
    """Append `addition` to a SHARED source file, then restore it — under a lock.

    WHY THE LOCK. Four gates calibrate by planting a rule into ember.css, scanning, and
    writing the original back. Each does read -> modify -> write. Run two at once and the
    restores clobber: gate A reads the pristine file and plants; gate B reads A's plant and
    plants its own; A writes back the pristine text, erasing B's plant; B writes back
    "pristine + A's plant" — and A's planted rule is now on disk permanently.

    That is not theory. Running theme-remnant-check, cta-grammar-check and balance-check
    concurrently leaves TWO planted rules in ember.css and makes theme-remnant report "40
    pages still painting the retired classic palette" — the exact CI failure, reproduced.
    The reported colour #515863 was its own calibration's plant, read back off disk.

    Worse than a flaky gate: it corrupts the WORKING TREE. A push during a run could ship
    planted CSS. So the lock is not an optimisation, and it is not the manifest's `serial`
    flag either — that depends on who schedules the gates, and this must hold whoever does.
    """
    deadline = time.time() + timeout
    fd = None
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise RuntimeError(
                    f'another gate has held {LOCK} for {timeout}s. If no gate is running, '
                    f'a previous one died mid-plant: check the file it names, then delete '
                    f'the lock.')
            time.sleep(0.2)
    try:
        os.write(fd, f'{os.getpid()} {path}\n'.encode())
        os.close(fd)
        fd = None
        original = open(path, encoding='utf-8').read()
        try:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(original + addition)
            yield
        finally:
            # Restore from the text read INSIDE the lock, so nothing else can have
            # touched it in between.
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(original)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(LOCK)
        except FileNotFoundError:
            pass
