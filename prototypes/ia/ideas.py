#!/usr/bin/env python3
"""Rendered prototypes of ideas 1, 3 and 4 from the IA review.

Built by injecting into the REAL page over CDP, never by hand-writing a mockup —
so every direction inherits the live type scale, tokens and breakpoints, and the
word counts printed below are measured on the same page they will ship to.

NO INVENTED CONTENT. Every string is lifted from a file in this repo; the source
is named in a comment beside it. Numbers come from tools/teardown-facts.py's own
measurement or from tools/gates.json, not from the page's prose (idea 2 exists
because the prose drifts).
"""
import sys, os, base64, io, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
from cdp import Browser, ensure_server
from PIL import Image, ImageDraw
ensure_server(8000)
OUT = 'prototypes/renders/ia'
os.makedirs(OUT, exist_ok=True)

CSS = r"""
/* ══ BRAND CHANGE 1 — the frame stops apologising ═════════════════════════ */
.b1 .voices .chap-i{display:none !important}

/* ══ BRAND CHANGE 2 — the forward-looking slot ════════════════════════════ */
/* PLACEHOLDER COPY. Three candidate drafts, each RECOMBINED from sentences
   already on this page — not Arpit's stated ambition, which only he can supply.
   The design being prototyped is the SLOT: where it sits, how big it is, what
   weight it carries. The words are his to write. */
/* text-align DECLARED: the closing section centres its children, so a slot that
   did not say otherwise came out centred with a left rule beside it. */
.b2 .nxt{margin:0 0 40px;padding:0 0 0 18px;border-left:2px solid var(--amber);
  max-width:52ch;text-align:left}
.b2 .nxt-k{margin:0 0 8px;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:10.5px;letter-spacing:.16em;line-height:1.7;color:var(--amber);
  text-transform:uppercase}
.b2 .nxt-p{margin:0;font-family:var(--ff-serif),Georgia,serif;font-size:21px;
  line-height:1.5;color:var(--ink)}
.b2 .nxt-d{margin:10px 0 0;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:10.5px;letter-spacing:.06em;line-height:1.7;color:var(--ink-dim)}
@media(max-width:560px){ .b2 .nxt-p{font-size:18px} }

/* ══ BRAND CHANGE 3 — the back half comes down ════════════════════════════ */
/* The article PREVIEWS go, the articles stay: three titles, all three still one
   click away, and "Writing" is a nav destination in its own right. */
.b3 #thoughts .ixp,.b3 #thoughts .lede{display:none !important}
/* the voices band spends 1,488px on a phone to show ONE 380px quote — the other
   seven are behind the radio group. The frame comes down, not the evidence. */
.b3 .voices .chap-i,.b3 .voices .lede{display:none !important}

/* ══ POSITION 1 — a scope line on every case card ═════════════════════════ */
/* Every phrase is verbatim from that case's own page — file and line in the JS
   below. Six of seven carry product-ownership language; O2 does not, and says
   so, which is what makes the other six readable as claims rather than padding. */
.p1 .bcard-own{margin:6px 0 0;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:11px;letter-spacing:.02em;line-height:1.6;color:var(--amber)}

/* ══ POSITION 2 — the portfolio-scope band ════════════════════════════════ */
.p2 .scope{margin-top:48px;padding-top:24px;border-top:1px solid var(--line);
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
  grid-template-rows:auto auto;column-gap:32px;row-gap:0}
.p2 .scope-k{grid-column:1 / -1;margin:0 0 20px;
  font-family:var(--ff-mono),ui-monospace,monospace;font-size:10.5px;
  letter-spacing:.16em;line-height:1.7;color:var(--amber);text-transform:uppercase}
.p2 .scope > div{display:contents}
.p2 .scope > div > b{grid-row:2;font-family:var(--ff-serif),Georgia,serif;
  font-size:30px;font-weight:400;line-height:1.15;color:var(--ink)}
.p2 .scope > div > span{grid-row:3;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:11px;letter-spacing:.01em;line-height:1.65;color:var(--ink-dim);
  padding-top:9px}
@media(max-width:900px){
  .p2 .scope{grid-template-columns:repeat(2,minmax(0,1fr));column-gap:24px}
  .p2 .scope > div:nth-child(-n+3) > b{grid-row:2}
  .p2 .scope > div:nth-child(-n+3) > span{grid-row:3}
  .p2 .scope > div:nth-child(n+4) > b{grid-row:4;padding-top:24px}
  .p2 .scope > div:nth-child(n+4) > span{grid-row:5}
}
@media(max-width:520px){
  .p2 .scope{grid-template-columns:minmax(0,1fr);grid-template-rows:none;row-gap:20px}
  .p2 .scope > div{display:grid}
  .p2 .scope > div > b,.p2 .scope > div > span{grid-row:auto}
  .p2 .scope > div:nth-child(n+4) > b{padding-top:0}
  .p2 .scope > div > b{font-size:26px}
}

/* ══ POSITION 3 — the role line itself ════════════════════════════════════ */
.p3 .role-line{max-width:62ch}

/* ── IDEA 4 — the eligibility filter gets its own line ───────────────────── */
/* It sits in the hero GRID, not in .hero-copy — inside the left column its rule
   stopped at 748px while the client strip's rule below ran the full 1160, two
   adjacent hairlines of different lengths. */
.i4 .elig{grid-column:1 / -1;display:flex;flex-wrap:wrap;gap:8px 20px;align-items:baseline;
  margin-top:32px;padding:12px 0 0;border-top:1px solid var(--line)}
/* and it REPLACES the availability clause rather than sitting beside it —
   "4 weeks' notice" was landing twice within 90px, which is the very defect
   idea 2's gate exists to catch. */
.i4 .cta-status{display:none !important}
.i4 .elig b{font-family:"Source Sans 3",var(--sans),system-ui;font-size:15px;
  font-weight:600;line-height:1.4;color:var(--ember);letter-spacing:.005em}
.i4 .elig span{font-family:var(--ff-mono),ui-monospace,monospace;font-size:12px;
  line-height:1.5;color:var(--ink-dim);letter-spacing:.02em}
/* it replaces the clause it was buried in, and the copy in act 02 */
.i4 .role-line em{font-style:normal;opacity:.32}
.i4 .who .meta{display:none}

/* ── IDEA 1 — ask the artifact, not me ───────────────────────────────────── */
.i1 .wl-lead h2,.i1 .who .skim,.i1 .who .fs,.i1 .aiwork-prose .lede,
.i1 .aiwork-close,.i1 .chap-i{display:none !important}
/* The three memos keep their label and their headline and lose the body: "Five
   calls in week one" IS the claim, and the 40 words under it restate it. The
   six-second paragraph goes whole — it is about this website, not about how he
   leads, and it already has a home in /writing/. */
.i1 .memo p:not(.mk){display:none !important}
/* The six-second paragraph is a bare <p> in .who — and the writing index 4,000px
   lower already previews it ("The six-second scan is a myth — I traced it to…").
   So it is a paraphrased duplicate, the kind idea 2's gate is blind to. The
   artifact index links it; the essay goes. */
.i1 .who .wrap p:not([class]){display:none !important}
.i1 .arts{margin-top:32px;border-top:1px solid var(--line)}
.i1 .aiwork-two{margin-top:40px}
.i1 .aiwork-prose{display:none !important}
.i1 .art{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr) auto;
  gap:8px 24px;align-items:baseline;padding:16px 0;border-bottom:1px solid var(--line)}
.i1 .art b{font-family:"Source Sans 3",var(--sans),system-ui;font-size:16px;
  font-weight:600;line-height:1.4;color:var(--ink)}
.i1 .art i{font-style:normal;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:11.5px;line-height:1.65;color:var(--ink-dim);letter-spacing:.01em}
.i1 .art a{font-family:"Source Sans 3",var(--sans),system-ui;font-size:11.5px;
  font-weight:600;letter-spacing:.08em;line-height:1.6;color:var(--violet);
  white-space:nowrap;text-decoration:none;border-bottom:1px solid currentColor}
@media(max-width:760px){
  .i1 .art{grid-template-columns:minmax(0,1fr);gap:4px 0;padding:14px 0}
  .i1 .art a{justify-self:start;margin-top:4px}
}

/* ── IDEA 3 — one engagement, one object, expanding in place ─────────────── */
.i3 .cred-strip > div > b{cursor:pointer}
.i3 .eng{grid-column:1 / -1;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
  column-gap:32px;row-gap:0;margin-top:clamp(32px,4.4vh,48px);padding-top:24px;
  border-top:1px solid var(--line)}
.i3 .engc{display:contents}
.i3 .engb{grid-row:1;display:flex;align-items:baseline;gap:8px;background:none;
  border:0;padding:0;text-align:left;cursor:pointer;font:inherit}
.i3 .engb b{font-family:"Source Sans 3",var(--sans),system-ui;font-size:16px;
  font-weight:600;line-height:1.4;color:var(--ink)}
.i3 .engb u{text-decoration:none;font-family:var(--ff-mono),ui-monospace,monospace;
  font-size:13px;line-height:1;color:var(--amber)}
.i3 .engw{grid-row:2;font-family:var(--ff-mono),ui-monospace,monospace;font-size:11.5px;
  line-height:1.65;color:var(--ink-dim);padding-top:9px;letter-spacing:.01em}
.i3 .engo{grid-column:1 / -1;grid-row:3;margin-top:24px;padding:24px 0 0;
  border-top:1px solid var(--border-accent)}
.i3 .engo-g{display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px 24px}
.i3 .engo-l{font-family:var(--ff-mono),ui-monospace,monospace;font-size:10.5px;
  letter-spacing:.16em;line-height:1.7;color:var(--amber);text-transform:uppercase;
  white-space:nowrap}
.i3 .engo-v{font-size:15px;line-height:1.6;color:var(--mut)}
.i3 .engo-v b{color:var(--ink);font-weight:600}
.i3 .engo-more{margin-top:20px;display:inline-block;font-family:"Source Sans 3",var(--sans);
  font-size:11.5px;font-weight:600;letter-spacing:.08em;color:var(--violet);
  text-decoration:none;border-bottom:1px solid currentColor}
/* The three bands this object replaces. !important because the live rules are
   html[data-theme="ember"] body.p-home .receipts{...} — three levels more
   specific than a prototype class, so a plain display:none loses silently and
   the prototype would show the replacement AND the thing it replaces. */
.i3 .receipts,.i3 .cred-strip{display:none !important}
/* and only the FOUR cards that duplicate the object. The first prototype hid
   .caseboard, which deleted three products that have no receipt and never
   appeared in the hero — a saving bought by losing content. */
.i3 .bcard.dup{display:none !important}
@media(max-width:900px){ .i3 .eng{grid-template-columns:repeat(2,minmax(0,1fr));
    grid-template-rows:auto auto auto auto;column-gap:24px}
  .i3 .engc:nth-child(-n+2) .engb{grid-row:1} .i3 .engc:nth-child(-n+2) .engw{grid-row:2}
  .i3 .engc:nth-child(n+3) .engb{grid-row:3;padding-top:24px}
  .i3 .engc:nth-child(n+3) .engw{grid-row:4}
  .i3 .engo{grid-row:5}}
@media(max-width:520px){ .i3 .eng{grid-template-columns:minmax(0,1fr);
    grid-template-rows:none;row-gap:20px}
  .i3 .engc{display:grid} .i3 .engb,.i3 .engw{grid-row:auto}
  .i3 .engc:nth-child(n+3) .engb{padding-top:0} .i3 .engo{grid-row:auto}}
"""

# ── IDEA 4 ────────────────────────────────────────────────────────────────────
# strings: role-line "fully remote (GMT+5:30)" · .who .meta "Fully remote · GMT+5:30
# · both US coasts, daily" · .cta-status "open to offers · 4 weeks' notice" ·
# the closing boarding pass "one full-time seat"
I4 = """
  document.body.classList.add('i4');
  const strip=document.querySelector('.cred-strip');
  const el=document.createElement('p'); el.className='elig';
  el.innerHTML='<b>Remote from India &middot; GMT+5:30</b>'
    + '<span>both US coasts, daily &middot; full overlap with UK</span>'
    + '<span>open to offers &middot; 4 weeks&rsquo; notice &middot; one full-time seat</span>';
  strip.parentNode.insertBefore(el, strip);
  // and it comes OUT of the role line, where it was a grey clause
  const r=document.querySelector('.role-line');
  r.innerHTML = r.innerHTML.replace(' \\u00b7 fully remote (GMT+5:30)','');
"""

# ── IDEA 1 ────────────────────────────────────────────────────────────────────
# every receipt below is a MEASURED number: loop_tests 42 · loop_assertions 76 ·
# trustlint_rules 7 · pattern_demos 9 · build_steps 0  (tools/teardown-facts.py)
# 36 = gates declared for stage pre-push in tools/gates.json (the page says 23)
# "8 patterns in production" and the six-second audit's "twenty-three
# practitioner and eight academic sources" are the page's own words.
ARTS = [
 ("The front-end I own ships in the PR",
  "/lab/ &mdash; 42 tests, 76 assertions, 7 lint rules, written before the code",
  "The code", "./lab/"),
 ("The quality bar is code, and the code is checked",
  "36 gates before every push &mdash; contrast from rendered pixels, not tokens",
  "The teardown", "./lab/teardown.html"),
 ("Patterns, not opinions",
  "8 in production &middot; 9 of them working demos you can drive",
  "The patterns", "./patterns/"),
 ("This same site again, in my own React",
  "self-hosted from the repo &mdash; no CDN, no third-party runtime",
  "The book edition", "./book/"),
 ("The claim I check hardest is my own",
  "the famous six-second scan does not exist &mdash; 23 practitioner + 8 academic sources",
  "The audit", "./writing/"),
]
I1 = """
  document.body.classList.add('i1');
  const two=document.querySelector('.aiwork-two');
  const d=document.createElement('div'); d.className='arts';
  d.innerHTML=%s;
  two.parentNode.insertBefore(d, two);
""" % json.dumps(''.join(
    '<div class="art"><b>%s</b><i>%s</i><a href="%s">%s &rarr;</a></div>' % (a, b, h, c)
    for a, b, c, h in ARTS))

# ── IDEA 3 ────────────────────────────────────────────────────────────────────
# WHO each client is: every phrase below is verbatim from that engagement's own
# receipt panel in index.html — nothing is characterised, only quoted.
ENG = [
 ("Talon Outdoor", "the UK&rsquo;s largest out-of-home advertiser &middot; 40% of the UK market",
  "adtech", "2 wks &rarr; 3 hrs",
  "Planning fell from two weeks to three hours, with an average media-value gain of &pound;69,000 per client.",
  "Per campaign, against the ~2-week manual planning baseline.",
  "Owned product definition, roadmap and end-to-end design across all six systems.",
  "./case-studies/adtech.html"),
 ("PE &amp; VC platforms", "an LLM over deal documents &middot; under NDA",
  "fintech", "60% faster",
  "Private-equity deal screening ran 60% faster once analysts stopped re-verifying the machine.",
  "Pre- vs post-rollout. Sources were exposed beside every score.",
  "Product definition, the interaction design, and the abstention + citation UX.",
  "./case-studies/fintech.html"),
 ("PTC", "engineers at NASA, Boeing, Toyota, Airbus &amp; Apple",
  "ptc", "$1M / yr",
  "$1M saved every year off the print budget; subscriptions went 0% &rarr; 64% of new bookings in a year.",
  "Recurring savings measured against the 2016 print budget.",
  "The 5&rarr;1 consolidation strategy and its four sunsets, and the 4-person design team.",
  "./case-studies/ptc.html"),
 ("Telef&oacute;nica O2", "MyO2 and Priority Moments &middot; publicly reported",
  "o2", "4M+ users",
  "MyO2 served 4M+ users across two O2 products.",
  "Publicly reported by O2 UK.",
  "Co-designed, then coded &mdash; the parts that were mine are named in the case.",
  "./case-studies/o2.html"),
]
ROWS = ''.join(
 '<div class="engc"><button class="engb" data-k="%s"><b>%s</b><u>+</u></button>'
 '<span class="engw">%s</span></div>' % (k, name, who)
 for name, who, k, _m, _c, _h, _r, _u in ENG)
PANELS = json.dumps({k: {
    'm': m, 'claim': c, 'how': h, 'role': r, 'url': u, 'name': name}
    for name, _w, k, m, c, h, r, u in ENG})
I3 = """
  document.body.classList.add('i3');
  ['adtech','fintech','ptc','o2'].forEach(k=>{
    const a=document.querySelector('.bcard a[href*="case-studies/'+k+'.html"]');
    if(a) a.closest('.bcard').classList.add('dup');
  });
  const split=document.querySelector('.hero-split');
  const box=document.createElement('div'); box.className='eng';
  box.innerHTML=%s;
  split.appendChild(box);
  const P=%s;
  box.addEventListener('click',e=>{
    const btn=e.target.closest('.engb'); if(!btn) return;
    const open=box.querySelector('.engo');
    const was=open && open.dataset.k===btn.dataset.k;
    if(open) open.remove();
    box.querySelectorAll('.engb u').forEach(u=>u.textContent='+');
    if(was) return;
    btn.querySelector('u').textContent='\\u2212';
    const p=P[btn.dataset.k];
    const o=document.createElement('div'); o.className='engo'; o.dataset.k=btn.dataset.k;
    o.innerHTML='<div class="engo-g">'
      +'<div class="engo-l">What changed</div><div class="engo-v"><b>'+p.m+'</b> &mdash; '+p.claim+'</div>'
      +'<div class="engo-l">Baseline</div><div class="engo-v">'+p.how+'</div>'
      +'<div class="engo-l">My role</div><div class="engo-v">'+p.role+'</div>'
      +'</div><a class="engo-more" href="'+p.url+'">The full case, with the receipt &rarr;</a>';
    // Insert after the row that was tapped, not at the end of the box. On a
    // phone the strip is one column, so appending put PTC's answer three rows
    // and ~250px below the row you touched — off-screen. At desktop the panel
    // is forced to grid-row 3, so DOM position does not move it.
    btn.parentNode.insertAdjacentElement('afterend', o);
  });
""" % (json.dumps(ROWS), PANELS)


B1 = '\n  document.body.classList.add(\'b1\');\n  // his own words, recombined: "eight people, eight vantage points" (the chapeau\n  // this replaces) and "The full set, unedited, on LinkedIn" (the band\'s own\n  // closing link). Same evidence, declarative frame.\n  const h = document.querySelector(\'#h-voices\');\n  h.textContent = \'Eight people who worked with me, unedited.\';\n'
B2 = '\n  document.body.classList.add(\'b2\');\n  const D = [["A &middot; the product", "What I want next: one AI product to own end to end &mdash; the eval layer, what gets measured, and the interface that ships.", "recombined from &ldquo;I read the model at the eval layer. I shape what gets measured. I ship the front-end.&rdquo; (act 02)"], ["B &middot; the thesis", "What I want next: to draw the edges on a model that millions of people will actually bet on.", "recombined from the h1 and &ldquo;A language model has no edges. So I draw them.&rdquo; (act 03)"], ["C &middot; the function", "What I want next: to build the design function around a product like these &mdash; the patterns, the bar in CI, and the team that keeps both.", "recombined from &ldquo;8 patterns in production&rdquo;, &ldquo;The quality bar is code&rdquo; and &ldquo;the 4-person design team&rdquo;"]];\n  const i = (location.hash.match(/draft=([abc])/i) || [,\'a\'])[1].toLowerCase();\n  const d = D[\'abc\'.indexOf(i)] || D[0];\n  const host = document.querySelector(\'.close .wrap\') || document.querySelector(\'.close\');\n  host.insertAdjacentHTML(\'afterbegin\',\n    \'<div class="nxt"><p class="nxt-k">Draft \' + d[0] + \' &mdash; placeholder, not his words</p>\'\n    + \'<p class="nxt-p">\' + d[1] + \'</p>\'\n    + \'<p class="nxt-d">\' + d[2] + \'</p></div>\');\n'
B3 = "\n  document.body.classList.add('b3');\n"
BALL = '\n  document.body.classList.add(\'b1\');\n  // his own words, recombined: "eight people, eight vantage points" (the chapeau\n  // this replaces) and "The full set, unedited, on LinkedIn" (the band\'s own\n  // closing link). Same evidence, declarative frame.\n  const h = document.querySelector(\'#h-voices\');\n  h.textContent = \'Eight people who worked with me, unedited.\';\n\n  document.body.classList.add(\'b2\');\n  const D = [["A &middot; the product", "What I want next: one AI product to own end to end &mdash; the eval layer, what gets measured, and the interface that ships.", "recombined from &ldquo;I read the model at the eval layer. I shape what gets measured. I ship the front-end.&rdquo; (act 02)"], ["B &middot; the thesis", "What I want next: to draw the edges on a model that millions of people will actually bet on.", "recombined from the h1 and &ldquo;A language model has no edges. So I draw them.&rdquo; (act 03)"], ["C &middot; the function", "What I want next: to build the design function around a product like these &mdash; the patterns, the bar in CI, and the team that keeps both.", "recombined from &ldquo;8 patterns in production&rdquo;, &ldquo;The quality bar is code&rdquo; and &ldquo;the 4-person design team&rdquo;"]];\n  const i = (location.hash.match(/draft=([abc])/i) || [,\'a\'])[1].toLowerCase();\n  const d = D[\'abc\'.indexOf(i)] || D[0];\n  const host = document.querySelector(\'.close .wrap\') || document.querySelector(\'.close\');\n  host.insertAdjacentHTML(\'afterbegin\',\n    \'<div class="nxt"><p class="nxt-k">Draft \' + d[0] + \' &mdash; placeholder, not his words</p>\'\n    + \'<p class="nxt-p">\' + d[1] + \'</p>\'\n    + \'<p class="nxt-d">\' + d[2] + \'</p></div>\');\n\n  document.body.classList.add(\'b3\');\n'


P1 = '\n  document.body.classList.add(\'p1\');\n  const OWN = [["adtech", "Product definition &middot; roadmap &middot; 6 systems"], ["fintech", "Product definition &middot; the abstention + citation UX"], ["vc-diligence", "Product definition &middot; the verdict surface + provenance gate"], ["ptc", "Product definition &middot; quarterly roadmap 2016&ndash;19 &middot; 5&rarr;1 consolidation &middot; 4-person team"], ["o2", "Design + front-end only &mdash; on contract through Equal Experts"], ["orgos", "Product &amp; Design Lead &middot; roadmap with the PM and 4 eng streams"], ["planit", "Product definition &middot; all of the UI"]];\n  OWN.forEach(([k, line]) => {\n    const a = document.querySelector(\'.bcard a[href*="case-studies/\' + k + \'.html"]\');\n    if (!a) return;\n    const s = a.closest(\'.bcard\').querySelector(\'.bcard-s\');\n    if (!s) return;\n    s.insertAdjacentHTML(\'afterend\', \'<p class="bcard-own">\' + line + \'</p>\');\n  });\n'
P2 = '\n  document.body.classList.add(\'p2\');\n  const host = document.querySelector(\'.receipts .wrap\');\n  host.insertAdjacentHTML(\'beforeend\',\n    \'<div class="scope"><p class="scope-k">What I owned, not only what I drew</p>\'\n    + "<div><b>6 systems</b><span>product definition and the roadmap, on one platform &middot; AdTech &middot; 50+ distributed team</span></div><div><b>5 &rarr; 1</b><span>four sunsets, 150k learners migrated in 24 months &middot; EdTech</span></div><div><b>0% &rarr; 64%</b><span>of new bookings &mdash; perpetual licence to subscription, in a year &middot; EdTech</span></div><div><b>4 streams</b><span>roadmap and delivery with the PM and four engineering streams &middot; Org Design</span></div>" + \'</div>\');\n'
P3 = '\n  document.body.classList.add(\'p3\');\n  const R = [["A &middot; minimal", "Staff / Principal &middot; Product &amp; Design &middot; AI &amp; LLM Products &middot; fully remote (GMT+5:30)", "drops one word. \\"Product &amp; Design\\" is his own title on the org-design case."], ["B &middot; explicit", "Product &amp; Design Lead &middot; AI &amp; LLM Products &middot; definition, roadmap, and the interface that ships &middot; fully remote (GMT+5:30)", "\\"Product &amp; Design Lead\\" is verbatim from case-studies/orgos.html; \\"definition, the quarterly roadmap\\" from case-studies/ptc.html"], ["C &middot; additive", "Staff / Principal Product Designer &middot; product definition &amp; roadmap &middot; AI &amp; LLM Products &middot; fully remote (GMT+5:30)", "keeps his title exactly and adds the scope beside it"]];\n  const i = (location.hash.match(/role=([abc])/i) || [,\'a\'])[1].toLowerCase();\n  const r = R[\'abc\'.indexOf(i)] || R[0];\n  const el = document.querySelector(\'.role-line\');\n  el.innerHTML = r[1];\n  el.insertAdjacentHTML(\'afterend\',\n    \'<p style="margin:6px 0 0;font:400 10.5px/1.7 var(--ff-mono),monospace;\'\n    + \'letter-spacing:.06em;color:var(--ink-dim)">variant \' + r[0] + \' &mdash; \' + r[2] + \'</p>\');\n'
PALL = '\n  document.body.classList.add(\'p3\');\n  const R = [["A &middot; minimal", "Staff / Principal &middot; Product &amp; Design &middot; AI &amp; LLM Products &middot; fully remote (GMT+5:30)", "drops one word. \\"Product &amp; Design\\" is his own title on the org-design case."], ["B &middot; explicit", "Product &amp; Design Lead &middot; AI &amp; LLM Products &middot; definition, roadmap, and the interface that ships &middot; fully remote (GMT+5:30)", "\\"Product &amp; Design Lead\\" is verbatim from case-studies/orgos.html; \\"definition, the quarterly roadmap\\" from case-studies/ptc.html"], ["C &middot; additive", "Staff / Principal Product Designer &middot; product definition &amp; roadmap &middot; AI &amp; LLM Products &middot; fully remote (GMT+5:30)", "keeps his title exactly and adds the scope beside it"]];\n  const i = (location.hash.match(/role=([abc])/i) || [,\'a\'])[1].toLowerCase();\n  const r = R[\'abc\'.indexOf(i)] || R[0];\n  const el = document.querySelector(\'.role-line\');\n  el.innerHTML = r[1];\n  el.insertAdjacentHTML(\'afterend\',\n    \'<p style="margin:6px 0 0;font:400 10.5px/1.7 var(--ff-mono),monospace;\'\n    + \'letter-spacing:.06em;color:var(--ink-dim)">variant \' + r[0] + \' &mdash; \' + r[2] + \'</p>\');\n\n  document.body.classList.add(\'p2\');\n  const host = document.querySelector(\'.receipts .wrap\');\n  host.insertAdjacentHTML(\'beforeend\',\n    \'<div class="scope"><p class="scope-k">What I owned, not only what I drew</p>\'\n    + "<div><b>6 systems</b><span>product definition and the roadmap, on one platform &middot; AdTech &middot; 50+ distributed team</span></div><div><b>5 &rarr; 1</b><span>four sunsets, 150k learners migrated in 24 months &middot; EdTech</span></div><div><b>0% &rarr; 64%</b><span>of new bookings &mdash; perpetual licence to subscription, in a year &middot; EdTech</span></div><div><b>4 streams</b><span>roadmap and delivery with the PM and four engineering streams &middot; Org Design</span></div>" + \'</div>\');\n\n  document.body.classList.add(\'p1\');\n  const OWN = [["adtech", "Product definition &middot; roadmap &middot; 6 systems"], ["fintech", "Product definition &middot; the abstention + citation UX"], ["vc-diligence", "Product definition &middot; the verdict surface + provenance gate"], ["ptc", "Product definition &middot; quarterly roadmap 2016&ndash;19 &middot; 5&rarr;1 consolidation &middot; 4-person team"], ["o2", "Design + front-end only &mdash; on contract through Equal Experts"], ["orgos", "Product &amp; Design Lead &middot; roadmap with the PM and 4 eng streams"], ["planit", "Product definition &middot; all of the UI"]];\n  OWN.forEach(([k, line]) => {\n    const a = document.querySelector(\'.bcard a[href*="case-studies/\' + k + \'.html"]\');\n    if (!a) return;\n    const s = a.closest(\'.bcard\').querySelector(\'.bcard-s\');\n    if (!s) return;\n    s.insertAdjacentHTML(\'afterend\', \'<p class="bcard-own">\' + line + \'</p>\');\n  });\n'

WORDS = r"""
(() => {

  const shown = el => {
    if (!el) return false;
    if (el.closest('[hidden]') || el.closest('.visually-hidden')) return false;
    if (el.closest('[aria-hidden="true"]')) return false;
    if (el.checkVisibility) return el.checkVisibility({checkOpacity:true, checkVisibilityCSS:true});
    return el.getClientRects().length > 0;
  };
  const count = root => { if(!root) return 0;
    let w=0; const k=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); let n;
    while(n=k.nextNode()){ const t=n.nodeValue.trim(); if(!t) continue;
      if(!shown(n.parentElement)) continue;
      w+=t.split(/\s+/).filter(Boolean).length; }
    return w; };
  const q=s=>document.querySelector(s);
  // the census that produced the review's table keyed sections by their FIRST
  // class name, and `.labrow` names TWO different sections — the code band and
  // the writing index — so their words were reported as one 293-word block.
  // Identify by the element, never by a shared class name.
  return {memos:count(q('.memos')), sixsec:count(q('.who .fs')),
          facts:count(q('.facts')), prose:count(q('.aiwork-prose')),
          hero:count(q('.hero')), who:count(q('.who')), aiwork:count(q('.labrow.aiwork')),
          writing:count(q('#thoughts')), contract:count(q('.contract')),
          receipts:count(q('.receipts')), work:count(q('.work')),
          voices:count(q('.voices')), close:count(q('.close')),
          page:count(document.body)};
})()
"""

DIRS = [('NOW  —  as it ships today', None, '.hero'),
        ('IDEA 4  —  the eligibility filter gets its own line', I4, '.hero'),
        ('IDEA 3  —  one engagement, one object  (collapsed)', I3, '.hero'),
        ('IDEA 3  —  the same object, PTC opened in place', I3 + """
  box.querySelector('[data-k="ptc"]').click();""", '.hero'),
        ('NOW  —  act 02 + the code band, as they ship', None, '.aiwork'),
        ('IDEA 1  —  ask the artifact, not me', I1, '.aiwork')]

for width, height in ((390, 844), (768, 1024), (1440, 900)):
    for label, js, anchor in DIRS:
        b = Browser(); b.viewport(width, height)
        b.navigate('http://localhost:8000/index.html', settle=2.0); b.pump(1.0)
        b.eval("(()=>{const s=document.createElement('style');s.textContent=%s;document.head.appendChild(s);})()" % json.dumps(CSS))
        if js: b.eval("(()=>{%s})()" % js)
        b.eval("(()=>{const t=document.createElement('style');t.textContent='*{transition:none!important;animation:none!important}';document.head.appendChild(t);})()")
        b.pump(0.8)
        w = b.eval_json(WORDS)
        r = b.eval_json("(()=>{const e=document.querySelector('%s');const q=e.getBoundingClientRect();"
                        "return {y:Math.round(q.top+scrollY),h:Math.round(q.height)};})()" % anchor)
        print('%5dpx  %-52s hero %3d · rcpt %3d · work %3d · who %3d (memos %3d, 6sec %2d, facts %2d) · code %3d || PAGE %4d  (h=%d)'
              % (width, label[:52], w['hero'], w['receipts'], w['work'], w['who'],
                 w['memos'], w['sixsec'], w['facts'], w['aiwork'], w['page'], r['h']))
        sh = b.cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
                   clip={'x': 0, 'y': r['y'], 'width': width, 'height': min(r['h'] + 24, 4200), 'scale': 1})
        img = Image.open(io.BytesIO(base64.b64decode(sh['data']))).convert('RGB')
        b.close()
        pad = Image.new('RGB', (img.width, img.height + 30), (12, 7, 13))
        d = ImageDraw.Draw(pad)
        d.text((10, 9), label + '    [%s: %d words]' % (
            'hero' if anchor == '.hero' else 'code band', w['hero'] if anchor == '.hero' else w['aiwork']),
            fill=(255, 176, 120))
        pad.paste(img, (0, 30))
        key = label.split('—')[0].strip().lower().replace(' ', '-').replace('(', '').replace(')', '')
        extra = 'open' if 'opened' in label else ('act02' if anchor == '.aiwork' else '')
        pad.thumbnail((1180, 6000))
        pad.save('%s/%s%s-%d.png' % (OUT, key, ('-' + extra) if extra else '', width))
print('\nrenders -> %s' % OUT)
