#!/usr/bin/env python3
"""IDEA 2 — one fact, one home.

A PROTOTYPE, deliberately outside tools/: tooling-budget-check has 20 lines of
headroom, and a 150-line gate does not fit. If this idea is adopted it earns its
place by replacing something, not by being added.

WHAT DEFECT IT CATCHES — a fact stated in two different SECTIONS of one page,
where the second mention should have been a link to the first. Not a style
opinion: `4M+` appears in four sections of the homepage and the single best line
on the site ("no AI feature ships until I've personally watched someone fail to
use it") appears verbatim in two. A reader meeting a claim twice does not believe
it twice; they think they have already read it.

WHAT IT CANNOT SEE — whether the repetition is GOOD (a chorus, a callback), and
whether two differently-worded sentences make the same claim. It only catches
verbatim repeats and repeated number tokens. Paraphrase is invisible to it.

DELIBERATE REPEATS are excluded structurally, not by taste:
  * .visually-hidden — a screen-reader expansion of a visual shorthand is
    SUPPOSED to restate it ("2 wks→3 hrs" + "Campaign planning fell from two
    weeks to three hours"). Counting those would make the gate punish accessibility.
  * [hidden] panels — not visible on load, so no reader meets them twice.
  * nav and footer — navigation repeats by design.
  * a repeat INSIDE one section — an eyebrow echoing its own heading is a local
    typographic choice, not an IA defect.

EXIT — 0 clean · 1 found a defect · 2 calibration failed · 3 could not measure.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
import cdp

PHRASE_WORDS = 6          # a 6-word verbatim repeat is not an accident
BASE = os.environ.get('BASE', 'http://localhost:8000')

HARVEST = r"""
(() => {
  const secOf = el => {
    if (el.closest('nav')) return null;            // navigation repeats by design
    if (el.closest('footer')) return null;
    const s = el.closest('section');
    if (!s) return null;
    const n = s.querySelector('.chap-n');
    return (n ? n.textContent.trim() + ' · ' : '') +
           ((s.className || '').split(' ')[0] || s.id || 'section');
  };
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while (n = w.nextNode()) {
    const t = n.nodeValue.replace(/\s+/g, ' ').trim();
    if (!t) continue;
    const p = n.parentElement; if (!p) continue;
    const cs = getComputedStyle(p);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
    if (p.closest('[hidden]')) continue;
    if (p.closest('.visually-hidden')) continue;   // the sr expansion is the point
    if (p.closest('[aria-hidden="true"]')) continue;
    const sec = secOf(p); if (!sec) continue;
    out.push({sec: sec, t: t, y: Math.round(p.getBoundingClientRect().top + scrollY)});
  }
  return out;
})()
"""

# a number that carries a unit or a scale suffix — a bare "3" is not a fact
NUM = re.compile(r'(?:£|\$)?\d[\d,.]*\s*(?:wks?|hrs?|weeks?|hours?|%|M\+?|k\+?|KB|yrs?|years?|/\s*yr)')
WORD = re.compile(r"[A-Za-z£$%\d’'–-]+")


def findings(nodes, allow):
    """Return (numbers, phrases) each as {fact: {section: first_y}}."""
    nums = collections.defaultdict(dict)
    phrs = collections.defaultdict(dict)
    for nd in nodes:
        for m in NUM.finditer(nd['t']):
            f = re.sub(r'\s+', ' ', m.group(0)).strip()
            if f.lower() in allow:
                continue
            nums[f].setdefault(nd['sec'], nd['y'])
        ws = WORD.findall(nd['t'].lower())
        for i in range(len(ws) - PHRASE_WORDS + 1):
            f = ' '.join(ws[i:i + PHRASE_WORDS])
            if f in allow:
                continue
            phrs[f].setdefault(nd['sec'], nd['y'])
    keep = lambda d: {k: v for k, v in d.items() if len(v) > 1}
    return keep(nums), keep(phrs)


def longest(phrases):
    """Merge overlapping n-grams back into the sentence they came from.

    Without this, one duplicated 12-word sentence reports EIGHT times: a 6-word
    window slid across it eight times, every window is a distinct finding of the
    SAME length, so filtering by containment removes nothing and pairwise
    greedy stitching stalls halfway. Walk it instead: an n-gram is a START when
    nothing else ends where it begins, and from a start you extend while some
    n-gram begins where the tail ends. That reconstructs each run exactly once."""
    by_pair = collections.defaultdict(set)
    for f, secs in phrases.items():
        by_pair[tuple(sorted(secs))].add(tuple(f.split()))
    out = {}
    for pair, grams in by_pair.items():
        heads = collections.defaultdict(list)     # first n-1 words -> n-grams
        for g in grams:
            heads[g[:-1]].append(g)
        tails = {g[1:] for g in grams}            # last n-1 words of every n-gram
        for g in sorted(grams):
            if g[:-1] in tails:
                continue                          # something ends where this begins
            run = list(g)
            while True:
                nxt = heads.get(tuple(run[-(PHRASE_WORDS - 1):]))
                if not nxt:
                    break
                run.append(nxt[0][-1])
            f = ' '.join(run)
            out[f] = {p: phrases[' '.join(run[:PHRASE_WORDS])][p] for p in pair}
    return out


def main():
    pages = sys.argv[1:] or ['/index.html']
    allow = set()
    ap = os.path.join(os.path.dirname(__file__), 'fact-allow.txt')
    if os.path.exists(ap):
        allow = {l.strip().lower() for l in open(ap) if l.strip() and not l.startswith('#')}

    cdp.ensure_server(int(BASE.rsplit(':', 1)[1]))
    b = cdp.Browser(); b.viewport(1440, 900)
    bad = 0
    try:
        # ---- CALIBRATION: plant a duplicate of one section's sentence into another
        b.navigate(BASE + pages[0], settle=2.0)
        # eval_json json.loads() a string result, so a bare sentence would not
        # survive the trip — hand it back inside an object.
        planted = b.eval_json("""(() => {
          const secs=[...document.querySelectorAll('section')].filter(s=>s.querySelector('p'));
          if (secs.length < 2) return {stub: null};
          const src = secs[0].querySelector('p').textContent.trim();
          const p = document.createElement('p'); p.textContent = src;
          secs[1].appendChild(p);
          return {stub: src.split(/\\s+/).slice(0, 8).join(' ')};})()""")['stub']
        if not planted:
            print('COULD NOT MEASURE — the page has fewer than two sections with prose.')
            return 3
        _, ph = findings(b.eval_json(HARVEST), allow)
        if not longest(ph):
            print('[calibration] FAIL — a sentence copied from one section into another '
                  'was NOT reported. The rule cannot go red, so its green means nothing.')
            return 2
        b.navigate(BASE + pages[0], settle=1.4)      # reload: drop the plant
        nm, ph = findings(b.eval_json(HARVEST), allow)
        if longest(ph) and planted.lower() in ' '.join(longest(ph)):
            print('[calibration] FAIL — the planted sentence survived the reload.')
            return 2
        print('[calibration] PASS — a sentence copied across sections is caught, '
              'and the finding disappears when the copy does.')

        for page in pages:
            b.navigate(BASE + page, settle=2.0); b.pump(0.6)
            nodes = b.eval_json(HARVEST)
            nums, phrases = findings(nodes, allow)
            phrases = longest(phrases)
            secs = len({n['sec'] for n in nodes})
            print('\n%s  —  %d visible text node(s) across %d section(s)' % (page, len(nodes), secs))
            if nums:
                print('  A NUMBER STATED IN MORE THAN ONE SECTION (%d):' % len(nums))
                for f, s in sorted(nums.items(), key=lambda kv: -len(kv[1])):
                    print('    %-12s %d sections — %s' % (
                        f, len(s), ', '.join('%s (y%d)' % (k, v) for k, v in sorted(s.items(), key=lambda kv: kv[1]))))
            if phrases:
                print('  A %d+ WORD PHRASE STATED IN MORE THAN ONE SECTION (%d):' % (PHRASE_WORDS, len(phrases)))
                for f, s in sorted(phrases.items(), key=lambda kv: -len(kv[0])):
                    print('    "%s…"' % f[:72])
                    print('      %s' % ', '.join('%s (y%d)' % (k, v) for k, v in sorted(s.items(), key=lambda kv: kv[1])))
            bad += len(nums) + len(phrases)
            if not nums and not phrases:
                print('  clean — every fact has one home on this page.')
    finally:
        b.close()

    print('\nCANNOT SEE: whether a repeat is a deliberate chorus, or two sentences that')
    print('make the same claim in different words. Verbatim and numeric only.')
    print('\nResult: %s' % ('clean.' if not bad else '%d fact(s) with more than one home.' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
