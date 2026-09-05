#!/usr/bin/env python3
"""jsonld-check.py — the structured data an LLM actually reads

Nothing here looked inside a <script type="application/ld+json"> block, so two defects
lived in it that are invisible to a human reading the page and fatal to the machine
reading the markup — which, for LLM and answer-engine retrieval, is the only reader
that matters:

  1. "@type":"Organisation".  schema.org has no such type; it is Organization. Both
     worksFor (Sahaj) and the AdTech case's about (Talon) were therefore dropped whole
     by every parser. British spelling is correct English and invalid vocabulary.
  2. HTML entities inside JSON strings. A ld+json block is raw JSON, NOT HTML-parsed,
     so "AI &amp; LLM Products" stays literally that after JSON.parse. The jobTitle
     field — the one that tells a model what he does — read with an escape in it.

Checks: every block parses; every @type is in the vocabulary this site uses (a typo or
a British spelling fails); no HTML entity survives inside any string value.

Exit 0 clean · 1 finding.
"""
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ('prototypes/', 'portfolio-sources/', 'tests/', 'assets/', 'partials/')

# Types this site legitimately uses. Adding one is a deliberate act — which is the point:
# an unlisted type is either a new decision or a typo, and both deserve a human.
KNOWN = {
    'Person', 'Organization', 'PostalAddress', 'CollegeOrUniversity', 'Article',
    'TechArticle', 'BreadcrumbList', 'ListItem', 'FAQPage', 'Question', 'Answer',
    'CollectionPage', 'WebSite', 'WebPage', 'ImageObject', 'Occupation', 'Book',
}
ENTITY = re.compile(r'&(?:[a-zA-Z][a-zA-Z0-9]{1,10}|#\d{1,5}|#x[0-9a-fA-F]{1,5});')
findings = []

def walk(node, path, rel):
    if isinstance(node, dict):
        t = node.get('@type')
        for tv in (t if isinstance(t, list) else [t]):
            if isinstance(tv, str) and tv not in KNOWN:
                findings.append((rel, f'unknown @type "{tv}" at {path}'))
        for k, v in node.items():
            walk(v, f'{path}.{k}', rel)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f'{path}[{i}]', rel)
    elif isinstance(node, str):
        m = ENTITY.search(node)
        if m and html.unescape(m.group(0)) != m.group(0):
            findings.append((rel, f'HTML entity {m.group(0)} inside a JSON string at {path}: "{node[:56]}"'))

blocks = 0
for f in sorted(glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True)):
    # Scratch files: gates plant temp .html into the docroot during their
    # calibration (__canon_canary_a.html, __al_*.html, __tr.html). If the
    # owning gate deletes one between this glob and the open, this gate dies
    # with FileNotFoundError mid-push — which is how image-dimension-check
    # broke a push on 2026-09-05. Every scratch name carries the __ prefix.
    if os.path.basename(f).startswith('__'):
        continue
    rel = os.path.relpath(f, ROOT)
    if rel.startswith(SKIP):
        continue
    for m in re.finditer(r'(?s)<script type="application/ld\+json">(.*?)</script>',
                         open(f, encoding='utf-8').read()):
        blocks += 1
        try:
            data = json.loads(m.group(1))
        except Exception as e:
            findings.append((rel, f'does not parse as JSON: {e}'))
            continue
        walk(data, '$', rel)

for rel, msg in findings:
    print(f'  {rel}\n      {msg}')
if findings:
    print(f'\n{len(findings)} structured-data finding(s) across {blocks} blocks.')
    sys.exit(1)
print(f'{blocks} JSON-LD blocks: all parse, all @types known, no entities in strings.')
print('CANNOT SEE: whether a field is TRUE, a required property that is simply absent,')
print('or whether the entity matches what the page actually says.')
