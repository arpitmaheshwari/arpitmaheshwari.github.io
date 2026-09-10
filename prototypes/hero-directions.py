import sys, base64, io, json
sys.path.insert(0,'tools')
from cdp import Browser, ensure_server
from PIL import Image, ImageDraw
ensure_server(8000)

# Shared CSS for the directions. Only presentation — no new copy anywhere.
CSS = """
/* A — the clients ARE the credential */
.dirA .sub{display:none}
.dirA .hero-widget{display:none}
.dirA .hero-split{grid-template-columns:1fr !important}
.dirA .cred{font-size:26px !important;line-height:1.45 !important;margin-top:32px !important;
  max-width:22ch;color:var(--mut) !important}
.dirA .cred b{color:var(--ink);font-weight:400}
.dirA .cred .cred-m{color:var(--amber)}

/* B — one artifact */
.dirB .sub{display:none}
.dirB .hero-widget{display:block}
.dirB .cred{display:none}
.dirB .vid-main{display:none}
.dirB .hero-split{grid-template-columns:.85fr 1.15fr !important;align-items:center}
.dirB .art-shot{display:block;width:100%;border-radius:10px;overflow:hidden;
  box-shadow:0 30px 70px rgba(0,0,0,.55);border:1px solid var(--line)}
.dirB .art-cap{margin-top:12px;font-family:var(--mono);font-size:11.5px;
  letter-spacing:.02em;color:var(--dim)}

/* C — claim, then the outcomes, nothing else */
.dirC .k.role-line{display:none}
.dirC .sub{display:none}
.dirC .hero-widget{display:none}
.dirC .cred{display:none}
.dirC .hero-split{grid-template-columns:1fr !important}
.dirC h1{max-width:26ch}
.dirC .numstrip{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-top:40px;
  padding-top:24px;border-top:1px solid var(--line)}
.dirC .numstrip div b{display:block;font-family:var(--serif);font-size:34px;
  font-weight:400;color:var(--ink);line-height:1.1}
.dirC .numstrip div span{display:block;font-family:var(--mono);font-size:11px;
  letter-spacing:.02em;color:var(--dim);line-height:1.7;margin-top:8px}
@media(max-width:640px){
  .dirC .numstrip{grid-template-columns:repeat(2,1fr);gap:20px}
  .dirA .cred{font-size:19px !important}
}
"""

A = """
  document.body.classList.add('dirA');
"""

B = """
  document.body.classList.add('dirB');
  const w=document.querySelector('.hero-widget');
  // his own caption, verbatim from case-studies/ptc.html
  w.insertAdjacentHTML('afterbegin',
    '<img class="art-shot" src="./assets/ptc-learning-connector-2026.jpg" '
    + 'alt="PTC Learning Connector, captured live in August 2026">'
    + '<p class="art-cap">learningconnector.ptc.com &mdash; still running seven years '
    + 'after my tenure ended</p>');
"""

C = """
  document.body.classList.add('dirC');
  // the four numbers lifted from the receipts band that is already on this page
  const cells=[...document.querySelectorAll('.rcell')];
  const items=cells.map(c=>{
    const bb=c.querySelector('b').cloneNode(true);
    bb.querySelectorAll('.visually-hidden').forEach(x=>x.remove());
    const n=bb.innerText.replace(/\\s+/g,' ').trim();
    const m=c.querySelector('span').innerText.replace(/\\s+/g,' ').trim();
    return '<div><b>'+n+'</b><span>'+m+'</span></div>';
  }).join('');
  document.querySelector('.hero-copy').insertAdjacentHTML('beforeend',
    '<div class="numstrip">'+items+'</div>');
"""

DIRS = [('NOW  —  96 words above the fold, clients at 12.5px', None),
        ('A  —  the clients ARE the credential  (MetaLab model)', A),
        ('B  —  one artifact  (Ramp model)', B),
        ('C  —  claim, then the outcomes  (Bricx model)', C)]

for width in (1440, 390):
    shots=[]
    for label, js in DIRS:
        b=Browser(); b.viewport(width, 900)
        b.navigate('http://localhost:8000/index.html', settle=2.0); b.pump(1.0)
        b.eval("(()=>{const s=document.createElement('style');s.textContent=%s;document.head.appendChild(s);})()" % json.dumps(CSS))
        if js: b.eval("(()=>{%s})()" % js)
        b.eval("(()=>{const t=document.createElement('style');t.textContent='*{transition:none!important;animation:none!important}';document.head.appendChild(t);})()")
        b.pump(0.8)
        n=b.eval_json("""JSON.stringify((()=>{
          const vis=e=>{const q=e.getBoundingClientRect();return q.width>0&&q.height>0};
          const w=[...document.querySelectorAll('h1,h2,p,li,span,div>b')].filter(e=>{
            const q=e.getBoundingClientRect();
            return q.top<innerHeight&&q.bottom>0&&vis(e)&&!e.children.length})
            .map(e=>e.innerText.trim()).join(' ').split(/\\s+/).filter(Boolean).length;
          return {aboveFoldWords:w};})())""")
        r=b.cmd('Page.captureScreenshot', format='png',
                clip={'x':0,'y':0,'width':width,'height':900,'scale':1})
        shots.append((label + '   [%d words above the fold]' % n['aboveFoldWords'],
                      Image.open(io.BytesIO(base64.b64decode(r['data']))).convert('RGB')))
        b.close()
        print('  %4dpx  %-56s %d words' % (width, label[:56], n['aboveFoldWords']))
    LAB=28; W=max(i.width for _,i in shots)
    sheet=Image.new('RGB',(W,sum(i.height+LAB for _,i in shots)),(12,7,13))
    d=ImageDraw.Draw(sheet); y=0
    for lab,i in shots:
        d.text((10,y+8), lab, fill=(255,176,120)); sheet.paste(i,(0,y+LAB)); y+=i.height+LAB
    sheet.thumbnail((1150,6000))
    out='prototypes/renders/hero/directions-%d.png' % width
    sheet.save(out); print('  -> %s' % out)
