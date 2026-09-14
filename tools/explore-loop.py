#!/usr/bin/env python3
"""explore-loop.py — unscripted reader sessions, photographed, with a human's eye to follow.

WHY (2026-09-13, Arpit: "create a loop of EXPLORATORY testing … and test the entire system
multiple times"). The gate loop (qa-loop.py) asserts the defect classes we already know. Every
defect Arpit has found by hand this month — the black boarding pass, the jump nav's alignment,
the pastel button, the 200px voids between acts — was found by USING the site, not by a gate.
Exploratory testing is that: an unscripted walk with real actions at real sizes, and eyes on
every screen. This tool does the walking and the photographing; a person (or I) does the
looking. It also keeps a notebook of things a reader would trip on that no gate owns.

METHOD. A seeded random walk. Each session: pick a width from the reader mix (390, 412, 768,
820, 1024, 1280, 1440), start on the homepage as a fresh reader, then take N steps, each a real
reader action chosen at random:
    follow a visible internal link · tap a nav item (through the drawer on a phone) · scroll a
    random distance · open a random disclosure or receipt · Tab a few times · rotate/resize to
    another width · go back.
After every step: a viewport screenshot (into a contact sheet per session) and a notebook of
OBSERVATIONS — each a fact about this screen, never a verdict:
    TAP-TARGET   a link/button smaller than 44×44 on a touch width
    REPEATED-DEVICE  more than five painted horizontal rules on one screen (boxes and ledgers excluded)
    CLIPPED      text inside an element that hides its own overflow while its content is wider
    DISTORTED    an image drawn at an aspect ratio >5% off its natural one
    TOUCHING     two text-bearing siblings whose boxes intersect
    VOID         a screenful in which >45% of the height carries no content box
    SIDEWAYS     the document is wider than the viewport
    CONSOLE      an uncaught exception during the step
    STUCK        a click that changed nothing (no navigation, no hash, no expanded state)
The notebook is not a gate: a VOID may be a designed pause, a TAP-TARGET may be a text link in
prose. The contact sheets are the deliverable; the notebook tells the looker where to look.

REPEAT. --sessions N runs N walks with seeds 1..N. Output: prototypes/explore/<ts>/
    session-<seed>@<width>.png     contact sheet, one tile per step, captioned
    notebook.md                    every observation with its step and tile
Exit 0 always (it explores; it does not judge). CANNOT SEE: whether what it photographed is
GOOD — that is the point of the tool, and the reason it ends with a sheet and not a number.
"""
import argparse, base64, datetime, io, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from PIL import Image, ImageDraw

import os as _os
BASE = _os.environ.get('BASE', 'http://localhost:8000')   # BASE=https://arpitmaheshwari.com to explore production
WIDTHS = [390, 412, 768, 820, 1024, 1280, 1440]
OBSERVE = r"""(()=>{const vw=innerWidth,vh=innerHeight,touch=vw<820;const out=[];
 const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.bottom>0&&r.top<vh&&getComputedStyle(e).visibility!=='hidden'};
 const hasText=e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
 if(touch) for(const e of document.querySelectorAll('a[href],button')){ if(!vis(e))continue; const r=e.getBoundingClientRect();
   if((r.width<44||r.height<44)&&!e.closest('p,li,td,dd,figcaption')&&hasText(e)) out.push(['TAP-TARGET',`${Math.round(r.width)}×${Math.round(r.height)} “${e.textContent.trim().slice(0,28)}”`]); }
 for(const e of document.querySelectorAll('main *')){ if(!vis(e))continue; const c=getComputedStyle(e);
   if(/hidden|clip/.test(c.overflowX)&&e.scrollWidth>e.clientWidth+2&&hasText(e)&&!e.matches('pre,code,.recon,.recon *,.visually-hidden,.sr-only')) out.push(['CLIPPED',`${e.tagName.toLowerCase()}.${(e.className||'').toString().split(' ')[0]} content ${e.scrollWidth}px in ${e.clientWidth}px`]); }
 for(const i of document.images){ if(!vis(i)||!i.naturalWidth||/\.svg(\?|$)/.test(i.currentSrc))continue;   /* an SVG keeps its own aspect inside any box */ const cs=getComputedStyle(i); const pw=parseFloat(cs.paddingLeft)+parseFloat(cs.paddingRight)+parseFloat(cs.borderLeftWidth)+parseFloat(cs.borderRightWidth), ph=parseFloat(cs.paddingTop)+parseFloat(cs.paddingBottom)+parseFloat(cs.borderTopWidth)+parseFloat(cs.borderBottomWidth); const r=i.getBoundingClientRect(); const a=(r.width-pw)/(r.height-ph),   /* the CONTENT box — a framed image with 24px side padding is not distorted, its frame is */b=i.naturalWidth/i.naturalHeight;
   if(Math.abs(a/b-1)>0.05&&getComputedStyle(i).objectFit==='fill') out.push(['DISTORTED',`${(i.currentSrc||'').split('/').pop().slice(0,40)} drawn ${a.toFixed(2)} vs natural ${b.toFixed(2)}`]); }
 /* REPEATED-DEVICE (2026-09-15, Arpit: 'it's about repetitive patterns'): painted horizontal rules in THIS viewport, boxes and ledgers excluded — more than five on one screen is a grid of lines, not a layout */
 {const ys=[];for(const e of document.querySelectorAll('main *')){if(!vis(e)||e.closest('table,.rcpt-rows,.rcpt-r,.rcpt-r-tight,.rcpt-box,.fr,.td-block,.ia-toc,.lh-log,.lint-findings,.rule-list,pre,code,button,.cta,[class*="-chrome"]'))continue;const c=getComputedStyle(e);const r=e.getBoundingClientRect();if(r.width<vw*0.4)continue;if(parseFloat(c.borderLeftWidth)>=1&&parseFloat(c.borderRightWidth)>=1)continue;
   if(parseFloat(c.borderTopWidth)>=1&&c.borderTopStyle!=='none')ys.push(Math.round(r.top));if(parseFloat(c.borderBottomWidth)>=1&&c.borderBottomStyle!=='none')ys.push(Math.round(r.bottom));}
  const d=[...new Set(ys)].sort((a,b)=>a-b).filter((y,i,a)=>i===0||y-a[i-1]>2);if(d.length>5)out.push(['REPEATED-DEVICE',`${d.length} horizontal rules on one screen`]);}
 const boxes=[...document.querySelectorAll('main h1,main h2,main h3,main p,main li,main a.cta,main button,main figcaption,main dt,main dd')].filter(vis).map(e=>({e,r:e.getBoundingClientRect()}));
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const A=boxes[i],B=boxes[j]; if(A.e.contains(B.e)||B.e.contains(A.e))continue; if(getComputedStyle(A.e).position==='absolute'||getComputedStyle(B.e).position==='absolute')continue; /* an overlay control (a Close button) sits on its panel by design */
   const ox=Math.min(A.r.right,B.r.right)-Math.max(A.r.left,B.r.left), oy=Math.min(A.r.bottom,B.r.bottom)-Math.max(A.r.top,B.r.top);
   if(ox>4&&oy>4) out.push(['TOUCHING',`${A.e.tagName.toLowerCase()} “${A.e.textContent.trim().slice(0,20)}” ∩ ${B.e.tagName.toLowerCase()} “${B.e.textContent.trim().slice(0,20)}” ${Math.round(ox)}×${Math.round(oy)}`]); if(out.length>40)break;}
 // void: rows of the viewport with no content box at all
 // content = anything a reader would see as a thing: a text leaf, a picture, a painted box (bg or border) — anywhere on the page, footer included
 const rows=new Uint8Array(vh); const mark=r=>{for(let y=Math.max(0,r.top|0);y<Math.min(vh,r.bottom|0);y++)rows[y]=1;};
 for(const e of document.body.querySelectorAll('*')){ if(e.closest('#nav')||!vis(e))continue; const c=getComputedStyle(e);
   const painted=(c.backgroundColor!=='rgba(0, 0, 0, 0)'&&e!==document.body&&e.tagName!=='MAIN'&&e.tagName!=='SECTION'&&e.tagName!=='FOOTER'&&!e.matches('.wrap,.section-inner,.measure-c'))||(parseFloat(c.borderTopWidth)>0&&c.borderTopStyle!=='none');
   if(hasText(e)||/^(IMG|VIDEO|SVG|CANVAS)$/.test(e.tagName)||painted) mark(e.getBoundingClientRect()); }
 let empty=0;for(const v of rows)if(!v)empty++; if(scrollY>50&&empty/vh>0.45) out.push(['VOID',`${Math.round(100*empty/vh)}% of this screen carries no content box`]);
 if(document.documentElement.scrollWidth>vw+1) out.push(['SIDEWAYS',`document ${document.documentElement.scrollWidth}px in a ${vw}px viewport`]);
 return JSON.stringify({obs:out.slice(0,40),url:location.pathname+location.hash,scrollY:Math.round(scrollY),title:document.title.slice(0,40)})})()"""


def settled(br, tries=25):
    """A real document, not a redirect stub mid-flight: production's /?view=classic hands over by script,
    and an eval that lands during that hand-over sees no <body> and throws (2026-09-13)."""
    for _ in range(tries):
        try:
            if br.eval("!!(document.body && document.head) && document.readyState==='complete'"):
                return True
        except RuntimeError:
            pass
        time.sleep(0.2)
    return False


def fresh_reader(br, width):
    br.viewport(width, 844 if width < 700 else 900)
    br.navigate(BASE + '/?view=classic', settle=2); settled(br)
    br.eval("(()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}return 1})()")
    br.navigate(BASE + '/', settle=3); settled(br)


def shot(br):
    r = br.cmd('Page.captureScreenshot', format='png')
    return Image.open(io.BytesIO(base64.b64decode(r['data']))).convert('RGB')


def step(br, rng, width, log):
    """One reader action. Returns (label, width) — width may change on a resize."""
    before = br.eval_json("JSON.stringify({u:location.href,exp:[...document.querySelectorAll('[aria-expanded=\"true\"]')].length,y:scrollY})")
    kind = rng.choice(['link', 'link', 'nav', 'scroll', 'scroll', 'open', 'tab', 'resize', 'back'])
    label = kind
    try:
        if kind == 'link':
            links = br.eval_json("JSON.stringify([...document.querySelectorAll('main a[href]')].filter(a=>{const r=a.getBoundingClientRect();return r.width>0&&r.height>0&&a.href.startsWith(location.origin)&&!/\\.(pdf|zip|vtt|mp4)$/.test(a.href)&&!/\\/book\\//.test(a.href)}).map((a,i)=>{a.setAttribute('data-xp',i);return a.textContent.trim().slice(0,30)||a.getAttribute('aria-label')||'?'}))")
            if not links: return step(br, rng, width, log)
            i = rng.randrange(len(links)); label = f'link “{links[i]}”'
            br.eval(f"(()=>{{const a=document.querySelector('[data-xp=\"{i}\"]');a.scrollIntoView({{block:'center'}});a.click();return 1}})()"); time.sleep(1.2)
        elif kind == 'nav':
            if width < 700:
                br.eval("(()=>{const t=document.getElementById('menuToggle');if(t&&t.getAttribute('aria-expanded')!=='true')t.click();return 1})()"); time.sleep(0.5)
            items = br.eval_json("JSON.stringify([...document.querySelectorAll('#nav .nav-links a')].map(a=>a.textContent.trim()))")
            if not items:
                log.append(('NO-NAV', f"no primary nav on {br.eval('location.pathname')}")); fresh_reader(br, width); return 'no nav → home', width
            i = rng.randrange(len(items)); label = f'nav “{items[i]}”'
            br.eval(f"document.querySelectorAll('#nav .nav-links a')[{i}].click()"); time.sleep(1.2)
        elif kind == 'scroll':
            d = rng.choice([300, 600, 900, 1400, -400]); label = f'scroll {d:+d}'
            br.eval(f"scrollBy({{top:{d},behavior:'instant'}})"); time.sleep(0.5)
        elif kind == 'open':
            n = br.eval("[...document.querySelectorAll('[aria-expanded=\"false\"],details:not([open]) > summary')].filter(e=>e.getBoundingClientRect().width>0).length")
            if not n: return step(br, rng, width, log)
            i = rng.randrange(n); label = f'open disclosure #{i+1}'
            br.eval(f"(()=>{{const e=[...document.querySelectorAll('[aria-expanded=\"false\"],details:not([open]) > summary')].filter(e=>e.getBoundingClientRect().width>0)[{i}];e.scrollIntoView({{block:'center'}});e.click();return 1}})()"); time.sleep(0.8)
        elif kind == 'tab':
            k = rng.randrange(2, 7); label = f'tab ×{k}'
            for _ in range(k):
                for t in ('rawKeyDown', 'keyUp'):
                    br.cmd('Input.dispatchKeyEvent', type=t, key='Tab', code='Tab', windowsVirtualKeyCode=9, nativeVirtualKeyCode=9)
            time.sleep(0.4)
        elif kind == 'resize':
            width = rng.choice([w for w in WIDTHS if w != width]); label = f'resize → {width}'
            br.viewport(width, 844 if width < 700 else 900); time.sleep(0.8)
        elif kind == 'back':
            label = 'back'; br.eval("history.back()"); time.sleep(1.2)
    except RuntimeError as e:
        log.append(('ERROR', f'{label}: {str(e)[:80]}'))
    settled(br)
    after = br.eval_json("JSON.stringify({u:location.href,exp:[...document.querySelectorAll('[aria-expanded=\"true\"]')].length,y:scrollY})")
    if kind in ('link', 'nav', 'open') and after == before:
        log.append(('STUCK', f'{label} changed nothing'))
    for e in br.drain('Runtime.exceptionThrown'):
        log.append(('CONSOLE', e['params']['exceptionDetails'].get('text', '')[:90]))
    return label, width


def session(seed, steps, out_dir):
    rng = random.Random(seed)
    width = rng.choice(WIDTHS)
    tiles, notebook = [], []
    with cdp.Browser() as br:
        br.cmd('Network.enable')
        fresh_reader(br, width)
        label = 'start'
        for n in range(steps + 1):
            notebook_step = []
            if n: label, width = step(br, rng, width, notebook_step)
            settled(br)   # on a real network a click may still be navigating
            o = br.eval_json(OBSERVE)
            im = shot(br)
            scale = 420 / im.width
            im = im.resize((420, int(im.height * scale)))
            cap = Image.new('RGB', (420, im.height + 34), (30, 30, 30)); cap.paste(im, (0, 34))
            d = ImageDraw.Draw(cap)
            d.text((6, 4), f"{n:02d} {label[:38]}", fill=(255, 255, 255))
            d.text((6, 18), f"{width}px  {o['url'][:34]}  y={o['scrollY']}" + (f"  ⚑{len(o['obs'])+len(notebook_step)}" if o['obs'] or notebook_step else ''), fill=(255, 200, 120))
            tiles.append(cap)
            for kind, what in notebook_step + [tuple(x) for x in o['obs']]:
                notebook.append((n, label, width, o['url'], kind, what))
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    th = max(t.height for t in tiles)
    sheet = Image.new('RGB', (cols * 426, rows * (th + 6)), (60, 60, 60))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * 426, (i // cols) * (th + 6)))
    fn = os.path.join(out_dir, f'session-{seed}.png'); sheet.save(fn)
    return fn, notebook


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sessions', type=int, default=3)
    ap.add_argument('--steps', type=int, default=14)
    a = ap.parse_args()
    if 'localhost' in BASE: cdp.ensure_server(8000)
    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prototypes', 'explore', ts)
    os.makedirs(out_dir, exist_ok=True)
    lines = [f'# Exploratory sessions — {ts}', '', 'Observations are facts about a screen, not verdicts. Look at the tile named in each row.', '']
    total = 0
    for seed in range(1, a.sessions + 1):
        fn, notebook = session(seed, a.steps, out_dir)
        total += len(notebook)
        print(f'  session {seed}: {a.steps} steps, {len(notebook)} observation(s) → {os.path.relpath(fn)}')
        lines += [f'## session {seed} — {os.path.basename(fn)}', '', '| step | action | width | page | kind | what |', '|---|---|---|---|---|---|']
        for n, label, width, url, kind, what in notebook:
            lines.append(f'| {n:02d} | {label} | {width} | {url} | {kind} | {what} |')
        lines.append('')
    open(os.path.join(out_dir, 'notebook.md'), 'w').write('\n'.join(lines))
    print(f'{total} observation(s) across {a.sessions} session(s). Notebook: {os.path.relpath(os.path.join(out_dir, "notebook.md"))}')
    print('CANNOT SEE: whether a screen is GOOD. Look at the sheets.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
