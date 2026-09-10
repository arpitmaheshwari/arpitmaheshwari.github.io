import sys, base64, io, json
sys.path.insert(0,'tools')
from cdp import Browser, ensure_server
from PIL import Image, ImageDraw
ensure_server(8000)

CSS = """
.dirF .sub{display:none}
.dirF .cred{display:none}
.dirF .vid-hero-k,.dirF .vid-hero-cap{display:none}
/* the film returns to the right rail it already occupies — but small, and top-aligned
   with the claim, so the rail has a role for its full height instead of one band. */
.dirF .hero-split{grid-template-columns:1.35fr .65fr !important;align-items:start;
  column-gap:56px}
.dirF .hero-widget{display:block;width:100%;max-width:340px;margin-left:auto;
  align-self:end;padding-bottom:6px}
.dirF .hero-widget .vid-main,.dirF .hero-widget figure{width:100%;max-width:none;margin:0}
.dirF .film-k{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;
  color:var(--dim);margin:0 0 8px}
.dirF .vid-frame{border-radius:8px;overflow:hidden;border:1px solid var(--line);
  box-shadow:0 18px 44px rgba(0,0,0,.45)}
.dirF .hero-widget video{width:100%;height:auto;display:block}
.dirF h1{max-width:22ch}

/* the strip spans the whole hero, under both columns */
.dirF .strip{grid-column:1 / -1;display:grid;grid-template-columns:repeat(4,1fr);
  grid-template-rows:auto auto;gap:0 28px;margin-top:48px;padding-top:22px;
  border-top:1px solid var(--line)}
/* display:contents makes every name share row 1 and every caption row 2, so the
   captions align to one another at EVERY width instead of only where nothing wraps */
.dirF .strip > div{display:contents}
.dirF .strip b{grid-row:1;font-family:var(--sans),system-ui;font-size:16px;font-weight:600;
  color:var(--ink);line-height:1.35;letter-spacing:.005em}
.dirF .strip span{grid-row:2;font-family:var(--mono);font-size:11.5px;letter-spacing:.01em;
  color:var(--ink-dim);line-height:1.65;padding-top:9px}
.dirF .strip span i{font-style:normal;color:var(--amber)}
@media(max-width:900px){
  .dirF .hero-split{grid-template-columns:1fr !important}
  .dirF .hero-widget{max-width:none;margin-left:0;margin-top:28px}
  .dirF h1{max-width:none}
  /* two columns, but the rows stay SHARED so the two captions in a row still
     align even when one client name wraps and its neighbour does not */
  .dirF .strip{grid-template-columns:repeat(2,1fr);grid-template-rows:auto auto auto auto;
    gap:0 22px}
  .dirF .strip > div:nth-child(-n+2) b{grid-row:1}
  .dirF .strip > div:nth-child(-n+2) span{grid-row:2}
  .dirF .strip > div:nth-child(n+3) b{grid-row:3;padding-top:22px}
  .dirF .strip > div:nth-child(n+3) span{grid-row:4}
}
@media(max-width:520px){
  /* one column: each client becomes its own two-line block again, so the shared
     rows above must be released or four clients pair up into two rows */
  .dirF .strip{grid-template-columns:1fr;grid-template-rows:none;margin-top:34px;gap:18px 0}
  .dirF .strip > div{display:grid}
  .dirF .strip b,.dirF .strip span{grid-row:auto}
  .dirF .strip > div:nth-child(n+3) b{padding-top:0}
  .dirF .strip b{font-size:15px}
}
"""

CELLS = [
  ('Talon Outdoor',       'six AI systems &middot; <i>2 wks &rarr; 3 hrs</i>'),
  ('PE &amp; VC platforms','deal screening &middot; <i>60% faster</i>'),
  ('PTC',                 'engineers at NASA, Boeing, Toyota, Airbus &amp; Apple'),
  ('Telef&oacute;nica O2','two products &middot; <i>4M+ people</i>'),
]
ITEMS = ''.join('<div><b>%s</b><span>%s</span></div>' % c for c in CELLS)

JS = """
  document.body.classList.add('dirF');
  document.querySelector('.hero-widget').insertAdjacentHTML('afterbegin',
    '<p class="film-k">THE PROCESS, ON FILM &mdash; 4:58</p>');
  document.querySelector('.hero-split')
    .insertAdjacentHTML('beforeend','<div class="strip">%s</div>');
""" % ITEMS.replace("'", "\\'")

MEASURE = r"""
(() => {
  const vh=innerHeight;
  let wc=0;
  const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); let n;
  while(n=walk.nextNode()){
    const t=n.nodeValue.trim(); if(!t) continue;
    const p=n.parentElement; if(!p) continue;
    const cs=getComputedStyle(p);
    if(cs.display==='none'||cs.visibility==='hidden'||cs.opacity==='0') continue;
    if(p.closest('.visually-hidden,[aria-hidden="true"]')) continue;
    const r=p.getBoundingClientRect();
    if(r.top>=vh||r.bottom<=0||r.width===0) continue;
    wc+=t.split(/\s+/).filter(Boolean).length;
  }
  const R=s=>{const e=document.querySelector(s);return e?e.getBoundingClientRect():null};
  const names=[...document.querySelectorAll('.strip b')].map(e=>Math.round(e.getBoundingClientRect().top));
  const caps=[...document.querySelectorAll('.strip span')].map(e=>Math.round(e.getBoundingClientRect().top));
  const strip=R('.strip'), hero=R('.hero'), copy=R('.hero-copy'), wid=R('.hero-widget'),
        ctas=R('.ctas'), h1=R('h1');
  // the void the layout rule cares about: the empty box under the shorter column
  const leftBottom=ctas.bottom, rightBottom=wid.bottom;
  return {aboveFoldWords:wc, vh,
    h1:[Math.round(h1.top),Math.round(h1.bottom)],
    ctasBottom:Math.round(ctas.bottom),
    widget:[Math.round(wid.top),Math.round(wid.bottom),Math.round(wid.width)],
    strip:[Math.round(strip.top),Math.round(strip.bottom)],
    heroBottom:Math.round(hero.bottom),
    tailGap:Math.round(hero.bottom-strip.bottom),
    voidUnderShorter:Math.round(strip.top-Math.max(leftBottom,rightBottom)),
    nameRows:[...new Set(names)].length, capRows:[...new Set(caps)].length,
    stripTextRight:(()=>{let mx=0;
      document.querySelectorAll('.strip b,.strip span').forEach(c=>{
        const r=document.createRange(); r.selectNodeContents(c);
        [...r.getClientRects()].forEach(q=>mx=Math.max(mx,q.right));});
      return Math.round(mx);})()};
})()
"""

for width,height in ((390,844),(768,1024),(1024,900),(1440,900)):
    b=Browser(); b.viewport(width,height)
    b.navigate('http://localhost:8000/index.html', settle=2.0); b.pump(1.0)
    b.eval("(()=>{const s=document.createElement('style');s.textContent=%s;document.head.appendChild(s);})()" % json.dumps(CSS))
    b.eval("(()=>{%s})()" % JS)
    b.eval("(()=>{const t=document.createElement('style');t.textContent='*{transition:none!important;animation:none!important}';document.head.appendChild(t);})()")
    b.pump(0.8)
    m=b.eval_json(MEASURE)
    print('%5dpx %3dw | h1 %s | film %s | strip %s | void under shorter col %4d | tail %4d | name rows %d cap rows %d | text->%d/%d'
          % (width,m['aboveFoldWords'],m['h1'],m['widget'],m['strip'],
             m['voidUnderShorter'],m['tailGap'],m['nameRows'],m['capRows'],
             m['stripTextRight'],width))
    hh=max(m['heroBottom']+40,height)
    r=b.cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True,
            clip={'x':0,'y':0,'width':width,'height':hh,'scale':1})
    img=Image.open(io.BytesIO(base64.b64decode(r['data']))).convert('RGB')
    b.close()
    d=ImageDraw.Draw(img)
    d.line([(0,height),(img.width,height)],fill=(255,90,90),width=2)
    d.text((8,height+4),'FOLD %dpx'%height,fill=(255,90,90))
    out='prototypes/renders/hero/cplus-clients-%d.png'%width
    img.save(out); print('   -> %s'%out)
