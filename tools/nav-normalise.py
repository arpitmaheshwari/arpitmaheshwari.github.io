"""Normalise every generated class inside the nav onto real components.

The lookup must NOT require a rule to start at a line beginning — styles.css
packs several rules onto shared lines, and an earlier version of this script
used `^\s*\.NAME{` with re.M, decided a live rule was dead, and stripped
.xi-case-studies-planit-003{width:40px;height:40px} off the logo. Eleven
renders changed. Same shape as the line-height regex that could not see `1.1`.
"""
import re, subprocess, collections

files = subprocess.run(['git','ls-files','*.html'], capture_output=True, text=True).stdout.split()
sheets = {p: open(p, encoding='utf-8').read() for p in ('styles.css', 'ember.css')}

def body(cls):
    """Every declaration block for this class, from either stylesheet, wherever it sits."""
    out = []
    for css in sheets.values():
        for m in re.finditer(r'(?<![\w-])\.' + re.escape(cls) + r'\s*\{([^}]*)\}', css):
            out.append(m.group(1).strip())
    return out

KNOWN = {
    'display:flex;align-items:center;gap:12px': 'row-ic',
    'text-decoration:none;color:inherit': 'nav-home',
    'text-decoration:none;color:inherit;display:flex;align-items:center;gap:12px': 'row-ic nav-home',
    'font-family:var(--ff-sans);font-size:14px;font-weight:600;letter-spacing:-0.5px': 'nav-name',
    'width:40px;height:40px': 'site-logo',
    'height:40px;width:40px': 'site-logo',
}

changed, unmapped, dead = 0, collections.Counter(), []
for f in files:
    s = open(f, encoding='utf-8').read()
    m = re.search(r'<nav id="nav".*?</nav>', s, re.S)
    if not m:
        continue
    nav = orig = m.group(0)
    for c in sorted(set(re.findall(r'xi-[a-z0-9-]+', nav))):
        bs = body(c)
        if not bs:
            dead.append((f, c)); nav = re.sub(r'\s*\b' + re.escape(c) + r'\b', '', nav); continue
        if len(bs) == 1 and bs[0] in KNOWN:
            nav = nav.replace(c, KNOWN[bs[0]])
        else:
            unmapped[c] = ' | '.join(b[:60] for b in bs)
    nav = re.sub(r'class="\s+', 'class="', nav)
    nav = re.sub(r'\s+"', '"', nav)
    nav = re.sub(r'class="([\w-]+(?: [\w-]+)*)"', lambda mm: 'class="' + ' '.join(dict.fromkeys(mm.group(1).split())) + '"', nav)
    if nav != orig:
        open(f, 'w', encoding='utf-8').write(s.replace(orig, nav, 1)); changed += 1

print(f"pages normalised: {changed}")
print(f"classes with no rule anywhere (removed): {len(dead)}  {[c for _, c in dead][:4]}")
if unmapped:
    print(f"UNMAPPED — left alone, needs a decision: {len(unmapped)}")
    for c, b in list(unmapped.items())[:6]:
        print(f"    {c}: {b}")
