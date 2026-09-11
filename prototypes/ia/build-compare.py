#!/usr/bin/env python3
"""Build an openable, clickable comparison of the four IA ideas.

Two files:
  live.html     — the REAL homepage with all four directions inlined, choosing
                  one from location.hash. Standalone-openable.
  compare.html  — the chrome: direction buttons, width buttons, and a
                  side-by-side mode that puts today's page next to the chosen
                  idea at the SAME width. Widths are real iframes, not a CSS
                  max-width, because media queries answer to the viewport and a
                  narrowed container would leave the desktop layout in place.

ONLY THE UNSHIPPED DIRECTIONS ARE OFFERED. live.html is generated FROM
index.html, so once a direction ships into the real page its injection runs a
SECOND time on top of itself. Driving every button on 2026-09-11 caught exactly
that: with positions 1-3 already live, "Position 1+2+3" read 1,710 words against
today's 1,562 — a second scope line under every card, a second scope band, a
second provenance note. A comparison that shows a doubled page is worse than no
comparison. When a direction ships, delete it from DIRECTIONS and DIRS here.

PATHS. live.html sits two directories down, so every relative asset reference
has to move with it. Generating hero-cplus.html taught this three times:
rewriting only href and src 404s the video poster; requiring the "./" prefix
404s every bare filename; and the only proof is a page load with ZERO failed
requests, which build-compare verifies at the end.
"""
import os, re, sys, json, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# one source of truth for the directions: import them from the render script
spec = importlib.util.spec_from_file_location('ideas', os.path.join(HERE, 'ideas.py'))
sys.argv = [sys.argv[0], '--import-only']
src = open(os.path.join(HERE, 'ideas.py')).read()
ns = {}
exec(src[:src.index('WORDS = r"""')], {'__file__': os.path.join(HERE, 'ideas.py'),
                                       'sys': sys, 'os': os, 'json': json,
                                       'base64': __import__('base64'),
                                       'io': __import__('io')}, ns)
CSS, I1, I3, I4 = ns['CSS'], ns['I1'], ns['I3'], ns['I4']
B1, B2, B3, BALL = ns['B1'], ns['B2'], ns['B3'], ns['BALL']
P1, P2, P3, PALL = ns['P1'], ns['P2'], ns['P3'], ns['PALL']

# ── rewrite every relative reference for a page two levels down ───────────────
ATTRS = ('href', 'src', 'poster', 'data-src', 'content')
SKIP = re.compile(r'^(?:[a-z]+:|//|/|#|\{\{)', re.I)

def fix(html):
    def one(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        if SKIP.match(val.strip()):
            return m.group(0)
        # "./assets/x.jpg" and "assets/x.jpg" both have to move — the optional
        # "./" is the fix for the second round of 404s.
        return '%s=%s%s%s' % (attr, q, '../../' + re.sub(r'^\./', '', val), q)
    out = html
    for a in ATTRS:
        out = re.sub(r'\b(%s)=(["\'])([^"\']+)\2' % a, one, out)
    # srcset is a comma-separated list, so it needs its own pass
    def srcset(m):
        parts = []
        for p in m.group(3).split(','):
            p = p.strip()
            if not p:
                continue
            bits = p.split(None, 1)
            u = bits[0]
            if not SKIP.match(u):
                u = '../../' + re.sub(r'^\./', '', u)
            parts.append(' '.join([u] + bits[1:]))
        return '%s=%s%s%s' % (m.group(1), m.group(2), ', '.join(parts), m.group(2))
    out = re.sub(r'\b(srcset)=(["\'])([^"\']+)\2', srcset, out)
    return out

html = fix(open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())

# SHIPPED, so deliberately absent: I1 (artifact index), B1 (voices frame),
# P1/P2/P3 (card scope, scope band, role line). They are on index.html, which is
# this page's own source, so injecting them again doubles them.
DIRECTIONS = {'now': '', 'i3': I3, 'i4': I4, 'b2': B2, 'b3': B3,
              'rest': I4 + B2 + B3 + I3}

BOOT = """
<style id="ia-css">%(css)s
/* the prototype says so, in every direction */
#ia-flag{position:fixed;left:0;right:0;top:0;z-index:99999;background:#FFB478;color:#120B14;
  font:600 11px/1.9 "Source Sans 3",system-ui,sans-serif;letter-spacing:.12em;
  text-align:center;text-transform:uppercase}
body{padding-top:22px !important}
</style>
<div id="ia-flag">prototype &mdash; <span id="ia-which">as it ships today</span></div>
<script id="ia-boot">
(() => {
  const FN = %(fns)s;
  const NAME = {now:'as it ships today', i1:'idea 1 \\u2014 ask the artifact, not me',
    i3:'idea 3 \\u2014 one engagement, one object', i4:'idea 4 \\u2014 the eligibility line',
    b2:'brand 2 - the forward-looking slot (PLACEHOLDER copy)',
    b3:'brand 3 - the back half comes down',
    rest:'everything still unshipped, together'};
  const key = () => {
    const k = (location.hash || '#now').slice(1).split('&')[0];
    return FN[k] !== undefined ? k : 'now';
  };
  const apply = k => {
    document.getElementById('ia-which').textContent = NAME[k];
    if (k !== 'now') { try { new Function(FN[k])(); } catch (e) { console.error('direction failed', k, e); } }
  };
  // a direction mutates the DOM, so switching means a reload, not an undo
  let current = key();
  addEventListener('hashchange', () => { if (key() !== current) location.reload(); });
  if (document.readyState === 'loading')
    addEventListener('DOMContentLoaded', () => apply(current));
  else apply(current);
})();
</script>
"""
boot = BOOT % {'css': CSS, 'fns': json.dumps(DIRECTIONS)}
assert '</body>' in html, 'no </body> in index.html'
open(os.path.join(HERE, 'live.html'), 'w', encoding='utf-8').write(
    html.replace('</body>', boot + '\n</body>'))

COMPARE = """<!doctype html>
<meta charset="utf-8">
<title>IA ideas — compare</title>
<style>
 :root{--bg:#0C070D;--ink:#F2EAF2;--dim:#9C8FA4;--amber:#FFB478;--line:#3A2F40}
 *{box-sizing:border-box}
 html,body{height:100%%}
 body{margin:0;background:var(--bg);color:var(--ink);overflow:hidden;
   font:14px/1.5 "Source Sans 3",system-ui,-apple-system,sans-serif}
 header{background:#140D16;border-bottom:1px solid var(--line);
   padding:9px 14px;display:flex;flex-wrap:wrap;gap:8px 26px;align-items:center}
 .grp{display:flex;gap:6px;align-items:center}
 .grp>b{font:600 10px/1.8 ui-monospace,monospace;letter-spacing:.16em;color:var(--dim);
   text-transform:uppercase;margin-right:2px}
 button{font:600 12px/1 "Source Sans 3",system-ui,sans-serif;color:var(--ink);
   background:transparent;border:1px solid var(--line);border-radius:999px;
   padding:7px 12px;cursor:pointer}
 button[aria-pressed=true]{background:var(--amber);color:#120B14;border-color:var(--amber)}
 .note{font:11px/1.6 ui-monospace,monospace;color:var(--dim);margin-left:auto;text-align:right}
 main{display:flex;gap:18px;align-items:flex-start;justify-content:center;padding:14px}
 figure{margin:0}
 /* A FIXED CAPTION HEIGHT, because the two panes must start at the same y.
    "TODAY" is one line and "IDEA 3 · ENGAGEMENT OBJECT · 1396 WORDS" is two, so
    with flex-start the taller caption pushed its viewport 23px down and the
    side-by-side comparison was off by 23px at every scroll position. */
 figcaption{display:flex;flex-direction:column;justify-content:flex-end;gap:1px;
   height:38px;padding-bottom:5px;
   font:600 11px/1.5 ui-monospace,monospace;letter-spacing:.09em;
   color:var(--amber);text-transform:uppercase;overflow:hidden}
 figcaption i{font-style:normal;color:var(--dim);letter-spacing:.04em}
 .vp{overflow:hidden;border:1px solid var(--line);border-radius:8px;background:#0C070D}
 iframe{border:0;display:block;transform-origin:top left}
</style>
<header>
  <div class="grp" id="dirs"><b>direction</b></div>
  <div class="grp" id="wids"><b>width</b></div>
  <div class="grp" id="views"><b>view</b></div>
  <div class="grp" id="jumps"><b>jump to</b></div>
  <div class="grp" id="drafts" hidden><b>brand 2 draft</b></div>
  <div class="grp" id="rolev" hidden><b>role line</b></div>
  <span class="note" id="note"></span>
</header>
<main id="stage"></main>
<script>
const DIRS=[['now','Today (as shipped)'],
            ['i4','Idea 4 \u00b7 eligibility line'],
            ['b2','Brand 2 \u00b7 what I want next'],
            ['b3','Brand 3 \u00b7 shorter back half'],
            ['i3','Idea 3 \u00b7 engagement object'],
            ['rest','All four']];
const DRAFTS=[['a','Draft A \u00b7 the product'],['b','Draft B \u00b7 the thesis'],
              ['c','Draft C \u00b7 the function']];
const ROLEV=[['a','A \u00b7 minimal'],['b','B \u00b7 explicit'],['c','C \u00b7 additive']];
const WIDS=[390,768,1024,1440];
const VIEWS=[['side','Side by side with today'],['solo','On its own']];
const JUMPS=[['','Top'],['#h-hero','Hero'],['#how-i-lead','Act 02'],
             ['#how-i-build','Code band'],['#voices','Voices'],
             ['#thoughts','Writing'],['#contact','Closing']];
let dir='i4', wid=390, view='side', jump='', draft='a', rolev='a', panes=[], lockUntil=0;

const mk=(host,items,get,set)=>{
  host.querySelectorAll('button').forEach(b=>b.remove());
  items.forEach(([v,l])=>{
    const b=document.createElement('button');
    b.textContent=l; b.setAttribute('aria-pressed', String(get()===v));
    b.onclick=()=>{set(v); draw();};
    host.appendChild(b);
  });
};

function pane(d,label,scale,vh){
  const f=document.createElement('figure');
  f.style.width=(wid*scale)+'px';
  const c=document.createElement('figcaption');
  c.innerHTML='<span>'+label+'</span><i data-w>&hellip;</i>';
  const box=document.createElement('div');
  box.className='vp';
  box.style.width=(wid*scale)+'px'; box.style.height=(vh*scale)+'px';
  const i=document.createElement('iframe');
  // A REAL viewport width, then scaled. A CSS max-width would leave the desktop
  // media queries in force and show the wrong layout at 390.
  i.width=wid; i.height=vh; i.style.transform='scale('+scale+')';
  i.src='live.html#'+d+'&draft='+draft+'&role='+rolev+(jump?jump:'');
  i.onload=()=>{
    try{
      const doc=i.contentDocument, win=i.contentWindow;
      // the number that actually decides this: visible words on load
      const shown=el=>el&&!el.closest('[hidden]')&&!el.closest('.visually-hidden')
        &&!el.closest('[aria-hidden="true"]')
        &&(el.checkVisibility?el.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})
                             :el.getClientRects().length>0);
      let w=0; const k=doc.createTreeWalker(doc.body,NodeFilter.SHOW_TEXT); let n;
      while(n=k.nextNode()){ const t=n.nodeValue.trim(); if(!t) continue;
        if(n.parentElement.closest('#ia-flag')) continue;
        if(!shown(n.parentElement)) continue;
        w+=t.split(/\s+/).filter(Boolean).length; }
      c.querySelector('[data-w]').textContent=w+' words \u00b7 '
        +Math.round(doc.documentElement.scrollHeight/100)/10+'k px tall';
      // Scroll both panes together, so the same band is under the eye in each.
      // The lock is a TIMESTAMP, not a boolean released on the next frame: the
      // scroll event from a programmatic scrollTo arrives a frame or more later,
      // so a rAF-released flag was already false when the echo came back. Pane A
      // pushed B, B's echo pushed A to B's stale offset, and the two oscillated
      // down to zero — scrollTo(0,1200) settled at 8, and driving A to 2400 left
      // A at 2093 and B at 49.
      win.addEventListener('scroll',()=>{
        const t=performance.now();
        if(t<lockUntil) return;
        lockUntil=t+150;
        // behavior:'instant' or the follower ANIMATES. This site sets
        // scroll-behavior:smooth, so a plain scrollTo starts a ~400ms animation
        // in the other pane; that animation fires its own scroll events, each
        // pushing the first pane to a mid-flight offset. Driving one pane to
        // 1200 left the pair at 303/613 and to 3000 at 2361/697 — two panes
        // chasing each other's half-finished animations, never a sync.
        panes.forEach(o=>{ if(o!==win && Math.abs(o.scrollY-win.scrollY)>1)
          try{o.scrollTo({top:win.scrollY,left:0,behavior:'instant'});}catch(e){} });
      },{passive:true});
      panes.push(win);
    }catch(e){ c.querySelector('[data-w]').textContent='—'; }
  };
  box.appendChild(i); f.appendChild(c); f.appendChild(box);
  return f;
}

function draw(){
  mk(document.getElementById('dirs'),DIRS,()=>dir,v=>dir=v);
  mk(document.getElementById('wids'),WIDS.map(w=>[w,w+'px']),()=>wid,v=>wid=+v);
  mk(document.getElementById('views'),VIEWS,()=>view,v=>view=v);
  mk(document.getElementById('jumps'),JUMPS,()=>jump,v=>jump=v);
  // the draft picker only means anything while brand 2 is on screen
  const dh=document.getElementById('drafts');
  dh.hidden = !(dir==='b2'||dir==='rest');
  if(!dh.hidden) mk(dh,DRAFTS,()=>draft,v=>draft=v);
  const rh=document.getElementById('rolev');
  rh.hidden = true;   // the role line shipped; no variant left to pick
  if(!rh.hidden) mk(rh,ROLEV,()=>rolev,v=>rolev=v);
  const s=document.getElementById('stage'); s.textContent=''; panes=[]; lockUntil=0;
  const two = view==='side' && dir!=='now';
  const avail = innerWidth - 28 - (two?18:0);
  // never clip a pane: scale so the panes always fit the window
  const scale = Math.min(1, avail/((two?2:1)*wid));
  // 38 caption + 28 padding + 4 border — measured, not guessed; the first
  // version reserved 62 and overflowed the clipped body by 12px.
  const vh = Math.round((innerHeight - document.querySelector('header').offsetHeight - 70)/scale);
  if(two) s.appendChild(pane('now','Today',scale,vh));
  s.appendChild(pane(dir,(DIRS.find(d=>d[0]===dir)||[])[1]||dir,scale,vh));
  document.getElementById('note').textContent =
    'each pane is a real '+wid+'px viewport'+(scale<1?' at '+Math.round(scale*100)+'%%':'')
    +' \u00b7 panes scroll together \u00b7 idea 3\u2019s rows are clickable';
}
draw();
addEventListener('resize',()=>{clearTimeout(window._t);window._t=setTimeout(draw,180);});
</script>
"""
open(os.path.join(HERE, 'compare.html'), 'w', encoding='utf-8').write(COMPARE)
print('wrote prototypes/ia/live.html and prototypes/ia/compare.html')
