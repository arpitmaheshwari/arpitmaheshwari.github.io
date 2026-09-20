#!/usr/bin/env python3
"""build-narrow-art.py — portrait companions for the nine landscape diagrams.

WHY. Measured 2026-09-20: every one of these drawings is display:none below 1400px.
A phone, tablet or laptop reader — most of the traffic — got a figcaption and a gap
where the argument was. Above 1400px they render at 692px inside a 3fr|7fr rail grid,
which puts their annotation layer at 7.0px against a 12.5px floor.

Widening the landscape art was tried and reverted: the figure sits in the 7fr track
(hence the 0.7 factor in --art-w), and breaking it out ran the page past the viewport
and put the rail under the drawing — a failure already documented in 04-overrides.css
before I repeated it.

So: a second drawing, drawn FOR the narrow column rather than squeezed into it.
Portrait, 360 units wide, type at 13-23u against a ~0.95 scale, so nothing lands
under 12.5px. Every label is carried over VERBATIM from the landscape original; this
file invents no content. Landscape stays for >=1400px, portrait serves below it.

    python3 tools/build-narrow-art.py            # write the nine
    python3 tools/build-narrow-art.py --check    # fail if any is stale
"""
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'art-narrow')
W = 360

# TYPE SIZED FOR THE SCALE IT ACTUALLY GETS, not the scale the artboard implies.
# A 360-unit artboard renders at ~308px in a 390px phone column — 0.86 — so a
# 13-unit caption lands at 11.1px, under the site's 12.5px floor and no better than
# the 7px landscape drawing this replaces. Measured, not assumed. The smallest type
# is 15 units, which holds 12.8px at that scale. Captions were re-checked for
# overflow afterwards; a wider glyph at the same artboard is how text runs off it.
STYLE = """ .n-ttl{font:400 23px Georgia,serif;fill:#F2EDE4}
 .n-sub{font:400 15px ui-monospace,monospace;fill:#938B81}
 .n-cap{font:400 15px ui-monospace,monospace;fill:#938B81}
 .n-act{font:400 16px ui-monospace,monospace;fill:#D4A85E}
 .n-qn{font:400 17px Georgia,serif;fill:#F2EDE4}
 .n-mv{font:400 19px Georgia,serif;fill:#F2EDE4}
 .n-num{font:400 26px Georgia,serif;fill:#D4A85E}
 .n-quo{font:italic 400 16px Georgia,serif;fill:#D4A85E}
 .n-edge{fill:none;stroke:#D4A85E;stroke-width:1.25}
 .n-dash{fill:none;stroke:#D4A85E;stroke-width:1.25;stroke-dasharray:4 5}
 .n-rule{fill:none;stroke:#5C554A;stroke-width:1}
 /* Composited, not translucent. fill-opacity leaves the DECLARED fill amber, and
    artifact-legibility-check judges each label against the nearest painted fill —
    so amber text on an amber card measured 1:1 and it reported 67 invisible labels.
    The gate was right to refuse: a checker should not have to guess what alpha
    composites to. These are the same colours, stated. */
 .n-card{fill:#181510;stroke:#8A6E3E;stroke-width:1}
 .n-band{fill:#1E1A12;stroke:#D4A85E;stroke-width:1}
 .n-node{fill:#0A0A0A;stroke:#D4A85E;stroke-width:1.5}"""


def esc(t):
    return html.escape(t, quote=False)


class Art:
    """A tiny portrait layout engine: a cursor that only moves down."""

    def __init__(self, aid, title, desc):
        self.aid, self.title, self.desc = aid, title, desc
        self.parts, self.y = [], 0

    def gap(self, n):
        self.y += n
        return self

    def text(self, s, cls='n-cap', x=0, dy=0, anchor=None):
        self.y += dy
        a = f' text-anchor="{anchor}"' if anchor else ''
        self.parts.append(f'<text class="{cls}" x="{x}" y="{self.y}"{a}>{esc(s)}</text>')
        return self

    def raw(self, s):
        self.parts.append(s)
        return self

    def head(self, title, sub_lines):
        self.text(title, 'n-ttl', dy=24)
        for l in sub_lines:
            self.text(l, 'n-sub', dy=19)
        return self

    def rule(self, dy=18):
        self.y += dy
        self.parts.append(f'<path class="n-rule" d="M0 {self.y} L{W} {self.y}"/>')
        return self

    def card(self, h, x=0, w=W, dy=14):
        """A card whose TOP is placed dy below the cursor; cursor lands at its bottom."""
        top = self.y + dy
        self.parts.append(f'<rect class="n-card" x="{x}" y="{top}" width="{w}" height="{h}" rx="6"/>')
        self.y = top
        return self

    def svg(self):
        # NOT class="art-svg": that class carries the LANDSCAPE sizing rules
        # (:is(p-patterns,p-process) figure:has(svg.art-svg) svg.art-svg{width:100%...}
        # and the --art-w breakout), which squeezed the portrait drawing to 308px
        # inside a container that was correctly 358px wide, and put its captions at
        # 11.1px on a phone. The portrait art is its own thing and names itself.
        # PAD = breathing room inside the drawing's own ground. The content is laid out
        # from x=0, so without a negative viewBox origin the title sat flush against the
        # dark plate's edge. Padding the VIEWBOX rather than moving every coordinate keeps
        # the layout arithmetic above honest.
        PAD = 16
        h = self.y + 12
        return (f'<svg id="{self.aid}" class="art-narrow" '
                f'viewBox="{-PAD} {-PAD} {W + PAD * 2} {h + PAD * 2}" '
                f'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" '
                f'role="img" aria-labelledby="{self.aid}-t {self.aid}-d">\n'
                f'<title id="{self.aid}-t">{esc(self.title)}</title>\n'
                f'<desc id="{self.aid}-d">{esc(self.desc)}</desc>\n'
                f'<style>\n{STYLE}\n</style>\n'
                # THE DRAWING PAINTS ITS OWN GROUND, exactly as the landscape original
                # does (<rect width="1280" height="440" fill="#0A0A0A"/>). Without it the
                # portrait art rendered cream-on-cream: this site is a LIGHT page at every
                # width, and the landscape drawing only looks dark because it carries this
                # rect. Found by rendering the real page at 390 and looking at it — every
                # Georgia label was invisible while the monospace ones, being grey, read
                # fine, so the measurements all passed. A screenshot caught what numbers
                # could not.
                f'<rect x="{-PAD}" y="{-PAD}" width="{W + PAD * 2}" height="{h + PAD * 2}" fill="#0A0A0A"/>\n'
                + '\n'.join(self.parts) + '\n</svg>\n')


# ── the nine. Every string below appears in the landscape original. ────────────

def process():
    a = Art('art-index-narrow', 'The method: every turn narrows the bet',
            'Read top to bottom. Three questions — desirable, feasible, viable — converge '
            'into one bet worth making. The bet passes through four repeating stages: '
            'listen, structure, prove, land. The band beside them narrows at every stage. '
            'It ends at ship, where the loop does not close.')
    a.head('Every turn narrows the bet.',
           ['The gap = how big a bet someone else', 'still has to accept'])
    a.text('Act I · the wager', 'n-act', dy=34)
    a.text('Desirable?', 'n-qn', dy=27); q1 = a.y
    a.text('Feasible?', 'n-qn', dy=24); q2 = a.y
    a.text('Viable?', 'n-qn', dy=24); q3 = a.y
    a.raw(f'<path class="n-edge" d="M104 {q1-5} L168 {q2-3}"/>')
    a.raw(f'<path class="n-edge" d="M96 {q2-3} L168 {q2-3}"/>')
    a.raw(f'<path class="n-edge" d="M82 {q3-5} L168 {q2-3}"/>')
    a.raw(f'<circle class="n-node" cx="172" cy="{q2-3}" r="4.5"/>')
    a.text('All three, or it dies in review', 'n-cap', dy=22)
    a.text('Act II · the spiral', 'n-act', dy=34)
    a.text('= one turn: listen, structure,', 'n-cap', dy=20)
    a.text('prove, land', 'n-cap', dy=17)
    top = a.y + 20
    ys = [top + 16 + i * 58 for i in range(4)]
    a.raw(f'<path class="n-band" d="M246 {top} L356 {top} L330 {ys[3]+2} L272 {ys[3]+2} Z"/>')
    a.raw(f'<path class="n-edge" d="M259 {top} L259 {ys[3]}"/>')
    for label, y in zip(('Listen', 'Structure', 'Prove', 'Land'), ys):
        a.raw(f'<circle class="n-node" cx="259" cy="{y}" r="4.5"/>')
        a.raw(f'<text class="n-mv" x="0" y="{y+6}">{label}</text>')
    a.y = ys[3] + 6
    a.text('Research is a rhythm,', 'n-cap', dy=26)
    a.text('not a phase', 'n-cap', dy=16)
    ship = a.y + 52
    a.raw(f'<path class="n-dash" d="M259 {ys[3]} L259 {ship}"/>')
    a.raw(f'<circle class="n-node" cx="259" cy="{ship}" r="4.5"/>')
    a.text('Act III · the open loop', 'n-act', dy=30)
    a.text('Ship', 'n-mv', dy=26)
    a.text('Confidence is earned in loops,', 'n-quo', dy=28)
    a.text('not declared in launches.', 'n-quo', dy=19)
    a.text('Shipping is the first honest data ·', 'n-cap', dy=22)
    a.text('the turns do not stop', 'n-cap', dy=17)
    return a


def calibration():
    a = Art('art-calibration-narrow', 'Calibration & Track Record pattern',
            'A stated confidence of 94 per cent, then the receipts: a reliability line '
            'comparing predicted against actual, and a breakdown by case type showing '
            '96, 91 and 72 per cent.')
    a.head('Calibration & Track Record',
           ['Is the confidence actually right?', 'Show the receipts.'])
    a.card(74, dy=22)
    a.text('Confidence', 'n-act', x=16, dy=26)
    a.text('94%', 'n-num', x=16, dy=32); a.text('High', 'n-cap', x=76, dy=0)
    a.y += 30
    a.text('Reliability', 'n-act', dy=34)
    a.text('stated confidence', 'n-cap', dy=18)
    top = a.y + 14
    a.raw(f'<path class="n-rule" d="M40 {top} L40 {top+120} L340 {top+120}"/>')
    a.raw(f'<path class="n-dash" d="M40 {top+120} L340 {top}"/>')
    a.raw(f'<path class="n-edge" d="M40 {top+120} C 140 {top+74}, 240 {top+36}, 340 {top+8}"/>')
    a.raw(f'<text class="n-cap" x="46" y="{top+12}">perfect</text>')
    a.raw(f'<text class="n-cap" x="232" y="{top+64}">observed</text>')
    a.raw(f'<text class="n-cap" x="0" y="{top+138}">predicted</text>')
    a.raw(f'<text class="n-cap" x="286" y="{top+138}">actual</text>')
    a.y = top + 138
    a.text('Tracks the line: confidence', 'n-quo', dy=32)
    a.text('earns its trust.', 'n-quo', dy=19)
    a.text('By case type', 'n-act', dy=34)
    for name, pct, w in (('Type A', '96%', 288), ('Type B', '91%', 273), ('Type C', '72%', 216)):
        a.y += 26
        a.raw(f'<text class="n-cap" x="0" y="{a.y}">{name}</text>')
        a.raw(f'<rect class="n-band" x="72" y="{a.y-11}" width="{w-72}" height="14" rx="3"/>')
        a.raw(f'<text class="n-cap" x="{w+8}" y="{a.y}">{pct}</text>')
    return a


def confidence():
    a = Art('art-confidence-narrow', 'Confidence Scores pattern',
            'A score of 78 out of 100 sits on a scale, and each band of the scale names '
            'the action it licenses: act at 75 to 100, review at 40 to 74, ignore at 0 to 39. '
            'Beneath it a 30-day track record reports 91 per cent calibration.')
    a.head('Confidence Scores',
           ['A number anchored to an action —', 'with its own track record.'])
    a.card(86, dy=22)
    a.text('Confidence', 'n-act', x=16, dy=26)
    a.text('78', 'n-num', x=16, dy=34); a.text('% confident', 'n-cap', x=58, dy=0)
    bar = a.y + 18
    a.raw(f'<rect class="n-rule" x="16" y="{bar}" width="328" height="8" rx="4"/>')
    a.raw(f'<rect class="n-band" x="16" y="{bar}" width="256" height="8" rx="4"/>')
    a.raw(f'<text class="n-cap" x="16" y="{bar+22}">0</text>')
    a.raw(f'<text class="n-cap" x="330" y="{bar+22}">100</text>')
    a.y = bar + 22
    a.text('Action', 'n-act', dy=34)
    for name, rng in (('Act', '75–100'), ('Review', '40–74'), ('Ignore', '0–39')):
        a.card(38, dy=10)
        a.text(name, 'n-qn', x=16, dy=25)
        a.text(rng, 'n-cap', x=140, dy=0)
        a.y += 13
    a.text('30-day track record', 'n-act', dy=36)
    top = a.y + 14
    a.raw(f'<path class="n-rule" d="M0 {top+56} L340 {top+56}"/>')
    a.raw(f'<path class="n-edge" d="M0 {top+44} C 90 {top+30}, 200 {top+18}, 340 {top+10}"/>')
    a.raw(f'<text class="n-cap" x="0" y="{top+74}">Day 1</text>')
    a.raw(f'<text class="n-cap" x="286" y="{top+74}">Day 30</text>')
    a.y = top + 74
    a.text('Calibration: 91%', 'n-quo', dy=28)
    return a


def explainability():
    a = Art('art-ml-explain-narrow', 'Explainability pattern',
            'Three named drivers carry weights — payment history plus 0.42, account age '
            'plus 0.27, recent inquiries minus 0.15 — and an explanation drawer traces '
            'them back from a risk score of 724. Disagreeing is offered as an action.')
    a.head('Explainability',
           ['Turn a black-box output into', 'an auditable argument.'])
    a.text('Drivers', 'n-act', dy=32)
    for name, w in (('Payment history', 'weight +0.42'), ('Account age', 'weight +0.27'),
                    ('Recent inquiries', 'weight -0.15')):
        a.card(54, dy=10)
        a.text(name, 'n-qn', x=16, dy=26)
        a.text(w, 'n-cap', x=16, dy=17)
        a.y += 12
    a.text('Why this output', 'n-act', dy=36)
    a.card(96, dy=12)
    a.text('Explanation drawer', 'n-cap', x=16, dy=24)
    for name in ('Payment history', 'Account age', 'Recent inquiries'):
        a.text(name, 'n-cap', x=16, dy=21)
    a.y += 22
    a.text('traced back from the score', 'n-cap', dy=24)
    a.card(72, dy=18)
    a.text('Output', 'n-act', x=16, dy=24)
    a.text('724', 'n-num', x=16, dy=32); a.text('risk score', 'n-cap', x=74, dy=0)
    a.y += 28
    a.card(44, dy=16)
    a.text('I disagree', 'n-qn', x=16, dy=27)
    a.y += 30
    a.text('a first-class action, not a footnote', 'n-cap', dy=20)
    return a


def provenance():
    a = Art('art-provenance-narrow', 'Provenance & Citations pattern',
            'A claim — architecture risk 72 — carries three sources: a Q3 filing, an '
            'engineering audit, and a founder call that disagrees. Opening one shows the '
            'source document and the cited passage inside it.')
    a.head('Provenance & Citations', ['Every claim traced to the', 'source behind it.'])
    a.text('Claim', 'n-act', dy=32)
    a.card(76, dy=12)
    a.text('Architecture risk:', 'n-qn', x=16, dy=26)
    a.text('72', 'n-num', x=16, dy=34); a.text('3 sources', 'n-cap', x=58, dy=0)
    a.y += 26
    a.text('Sources', 'n-act', dy=34)
    for name, note in (('Q3 filing', None), ('Eng. audit', None), ('Founder call', 'disagrees')):
        a.card(38, dy=10)
        a.text(name, 'n-qn', x=16, dy=25)
        if note:
            a.text(note, 'n-cap', x=170, dy=0)
        a.y += 13
    mid = a.y + 20
    a.raw(f'<path class="n-dash" d="M24 {mid} L24 {mid+26}"/>')
    a.y = mid + 26
    a.card(92, dy=6)
    a.text('Source doc', 'n-act', x=16, dy=24)
    a.raw(f'<rect class="n-band" x="16" y="{a.y+12}" width="300" height="20" rx="3"/>')
    a.raw(f'<text class="n-cap" x="24" y="{a.y+26}">Cited passage</text>')
    a.y += 62
    return a


def act_review_ignore():
    a = Art('art-act-review-narrow', 'The Act / Review / Ignore rule',
            'Three scores, three different screens. A high score of 92 offers act, with '
            'its signals named. A mixed score of 61 goes to review, with its reasons on '
            'the card. A low score of 23 is ignored — the model declines to bluff.')
    a.head('The Act / Review / Ignore Rule',
           ['One score, one action — a number', 'never reaches the screen alone.'])
    a.card(102, dy=22)
    a.text('Score 92 · high', 'n-cap', x=16, dy=24)
    a.text('→ Act', 'n-mv', x=16, dy=26)
    a.text('signals named · safe to run', 'n-cap', x=16, dy=20)
    a.text('Apply', 'n-act', x=16, dy=20); a.text('Override ↶', 'n-act', x=86, dy=0)
    a.y += 20
    a.card(118, dy=14)
    a.text('Score 61 · mixed', 'n-cap', x=16, dy=24)
    a.text('→ Review', 'n-mv', x=16, dy=26)
    a.text('reasons on the card,', 'n-cap', x=16, dy=20)
    a.text('not a tooltip:', 'n-cap', x=16, dy=16)
    a.text('— recency conflict, panels 12 & 14', 'n-cap', x=16, dy=18)
    a.y += 24
    a.text('— surfaced for a human · never auto-run', 'n-cap', dy=22)
    a.card(60, dy=16)
    a.text('Score 23 · low', 'n-cap', x=16, dy=24)
    a.text('Ignore', 'n-mv', x=16, dy=26)
    a.y += 26
    a.text('below the line, the model declines', 'n-quo', dy=30)
    a.text('to bluff — the honest no is what', 'n-quo', dy=19)
    a.text('makes the act believable.', 'n-quo', dy=19)
    return a


def capability():
    a = Art('art-capability-narrow', 'The Capability Contract pattern',
            'Two columns of a contract stated up front: in scope, scoring standard deals '
            'and pricing liquid assets, handled end to end. Out of scope, illiquid assets '
            'and novel structures, handed to a human and routed to a specialist.')
    a.head('The Capability Contract',
           ['What it does, where it taps out —', 'stated up front.'])
    a.text('In scope', 'n-act', dy=32)
    for name in ('Score standard deals', 'Price liquid assets'):
        a.card(36, dy=10)
        a.text(name, 'n-qn', x=16, dy=24)
        a.y += 12
    a.text('Confident — handled end to end.', 'n-cap', dy=24)
    a.text('Out of scope', 'n-act', dy=36)
    for name in ('Illiquid assets', 'Novel structures'):
        a.card(36, dy=10)
        a.text(name, 'n-qn', x=16, dy=24)
        a.y += 12
    a.text('hand to a human', 'n-cap', dy=24)
    mid = a.y + 16
    a.raw(f'<path class="n-dash" d="M24 {mid} L24 {mid+26}"/>')
    a.y = mid + 26
    a.card(46, dy=6)
    a.text('Hand-off', 'n-act', x=16, dy=22)
    a.text('Routed to a specialist', 'n-qn', x=16, dy=20)
    a.y += 22
    a.text('Re-routed, not abandoned.', 'n-quo', dy=28)
    return a


def failure_states():
    a = Art('art-failure-narrow', 'Failure States pattern',
            'The wrong-answer screen, designed first. Against a question the model is not '
            'confident enough to answer, it says so plainly, reports low confidence, and '
            'offers two ways forward: try another source, or ask a human.')
    a.head('Failure States', ['Design the wrong-answer', 'screen first.'])
    a.card(150, dy=22)
    a.text('Not confident enough', 'n-act', x=16, dy=24)
    a.text('Your question', 'n-cap', x=16, dy=22)
    a.raw(f'<rect class="n-band" x="16" y="{a.y+10}" width="300" height="16" rx="3"/>')
    a.y += 44
    a.text('I’m not sure', 'n-mv', x=16, dy=0)
    a.text('about this one.', 'n-mv', x=16, dy=24)
    a.text('Confidence', 'n-cap', x=16, dy=26); a.text('Low', 'n-act', x=100, dy=0)
    a.y += 26
    a.text('What now?', 'n-act', dy=32)
    for name, note in (('Try another source', 'Search a different reference'),
                       ('Ask a human', 'Route to a person who knows')):
        a.card(48, dy=10)
        a.text(name, 'n-qn', x=16, dy=24)
        a.text(note, 'n-cap', x=16, dy=18)
        a.y += 16
    a.text('A graceful unknown beats a', 'n-quo', dy=32)
    a.text('confident wrong answer.', 'n-quo', dy=19)
    return a


def human_in_loop():
    a = Art('art-human-loop-narrow', 'Human-in-the-Loop pattern',
            'Three steps down the page: the model suggests, the human overrides and edits, '
            'and the next result is improved. The correction becomes the next training '
            'signal, and the three steps close into a loop.')
    a.head('Human-in-the-Loop',
           ['Override should feel like authorship —', 'corrections become the next',
            'training signal.'])
    steps = (('01 · model', 'Suggests'), ('02 · human', 'Overrides & edits'),
             ('03 · next result', 'Improved'))
    tops = []
    for k, v in steps:
        a.card(56, dy=16)
        tops.append(a.y)
        a.text(k, 'n-act', x=16, dy=22)
        a.text(v, 'n-qn', x=16, dy=22)
        a.y += 12
    for t, nxt in zip(tops, tops[1:]):
        a.raw(f'<path class="n-edge" d="M24 {t+56} L24 {nxt}"/>')
        a.raw(f'<path class="n-edge" d="M20 {nxt-7} L24 {nxt} L28 {nxt-7}"/>')
    a.text('correction → next training signal', 'n-cap', dy=26)
    a.text('The loop', 'n-act', dy=34)
    a.text('Suggest → Override → Re-learn', 'n-quo', dy=26)
    return a


ALL = [('process', process), ('calibration', calibration), ('confidence', confidence),
       ('ml-explainability', explainability), ('provenance', provenance),
       ('act-review-ignore', act_review_ignore), ('capability-contract', capability),
       ('ai-failure-states', failure_states), ('human-in-loop', human_in_loop)]


def main():
    check = '--check' in sys.argv
    os.makedirs(OUT, exist_ok=True)
    stale = []
    for name, fn in ALL:
        body = fn().svg()
        path = os.path.join(OUT, name + '.svg')
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old == body:
            continue
        if check:
            stale.append(name)
            continue
        open(path, 'w', encoding='utf-8').write(body)
        print(f'  wrote {os.path.relpath(path, ROOT)}  ({len(body)} bytes)')
    if check and stale:
        print(f'  STALE: {", ".join(stale)} — run without --check')
        return 1
    print(f'{len(ALL)} portrait drawing(s) {"checked" if check else "built"}.')
    print('CANNOT SEE: whether a drawing READS well — only that it was written. '
          'Every one must be rendered and looked at.')
    return 0


if __name__ == '__main__':
    sys.exit(main())


# ── wiring: place each portrait drawing into its page, behind the .artalt hook ──
# The hook already exists in 04-overrides.css and is used by six case studies:
#   @media (max-width:1439px){ .art-svg:has(+ .artalt){display:none}
#                              .art-svg + .artalt{display:grid} }
# so a portrait drawing wrapped in .artalt, placed as the art's NEXT SIBLING,
# swaps itself in below 1440px and needs no new CSS at all. /process additionally
# has `.process-fig:has(> .artalt){display:block;...}`, which un-hides the figure
# it otherwise drops below 1040px.

PAGES = {
    'process': ('process/index.html', 'art-index-1'),
    'calibration': ('patterns/calibration-track-record.html', 'art-calibration--1'),
    'confidence': ('patterns/confidence-scores.html', 'art-confidence-s-1'),
    'ml-explainability': ('patterns/ml-explainability.html', 'art-ml-explainab-1'),
    'provenance': ('patterns/provenance-citations.html', 'art-provenance-c-1'),
    'act-review-ignore': ('patterns/act-review-ignore.html', 'art-act-review-i-1'),
    'capability-contract': ('patterns/capability-contract.html', 'art-capability-c-1'),
    'ai-failure-states': ('patterns/ai-failure-states.html', 'art-ai-failure-s-1'),
    'human-in-loop': ('patterns/human-in-loop.html', 'art-human-in-loo-1'),
}
MARK_OPEN = '<div class="artalt artalt--drawn">'
MARK_CLOSE = '</div>'


def wire(check=False):
    import re
    changed, missing = [], []
    for name, (page, aid) in PAGES.items():
        art = os.path.join(OUT, name + '.svg')
        if not os.path.exists(art):
            missing.append(name)
            continue
        drawing = open(art, encoding='utf-8').read().strip()
        for base in ('', os.path.join('partials', 'pages')):
            path = os.path.join(ROOT, base, page)
            if not os.path.exists(path):
                continue
            s = open(path, encoding='utf-8').read()
            m = re.search(r'<svg[^>]*id="%s"[\s\S]*?</svg>' % re.escape(aid), s)
            if not m:
                missing.append(f'{page}: no {aid}')
                continue
            block = '\n' + MARK_OPEN + '\n' + drawing + '\n' + MARK_CLOSE
            old = re.search(re.escape(MARK_OPEN) + r'[\s\S]*?' + re.escape(MARK_CLOSE),
                            s[m.end():m.end() + len(drawing) + 400])
            new = s[:m.end()] + block + (s[m.end() + old.end():] if old else s[m.end():])
            if new == s:
                continue
            if check:
                changed.append(os.path.relpath(path, ROOT))
                continue
            open(path, 'w', encoding='utf-8').write(new)
            changed.append(os.path.relpath(path, ROOT))
    return changed, missing
