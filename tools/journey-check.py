#!/usr/bin/env python3
"""journey-check.py — walk the site the way a reader does, and require every step to land.

WHY (2026-09-13, Arpit: "test the entire journey — navigation, images, content, layout,
negative spacing, accessibility — and test the entire system multiple times"). Fifty-seven
gates here grade a page ON LOAD: its colours, its boxes, its markup. Not one of them
navigates. A reader arrives on the homepage, opens the menu on a phone, taps "Work", lands
on a case, taps a section link in the jump nav, reads to the end, taps "Next case study",
and finally taps Connect. Every one of those steps can fail with every on-load gate green:
a link to a page that moved, an anchor that scrolls under the fixed nav, a drawer that opens
but whose links are inert, a lazy image that never paints once scrolled to, a "next" door
that points at itself.

METHOD. At 390 (mobile emulation, the drawer path) and 1440 (the bar path):
  1. HOME → every primary nav link: click it, require the location to change to its href,
     an <h1> to be present, no uncaught exception, no failed same-origin request, no
     horizontal overflow, and every <img> in the document to have painted (naturalWidth > 0
     after a scroll-through, which is what wakes lazy loading).
  2. On every CASE page: click every jump-nav link; require location.hash to equal its href
     and the target's top edge to sit inside the viewport BELOW the fixed nav (a heading
     hidden under the bar is "not landed"). Then the "Next case study" door: require it to
     point at a different case page that loads with an <h1>.
  3. HOME receipts: click each receipt button; require aria-expanded to flip and the
     controlled panel to become visible with a positive height.
  4. Every internal <a href> on every classic page: fetched once through the page (same
     origin), required to answer 200 — with the fragment, if any, resolving to an element
     on the target page. This is the runtime half of link-integrity-check (which reads files).
  Each step is verified by reading DOM state after the action, never by trusting "clicked".

CALIBRATION. Plants a broken image and a jump link to a missing anchor into the live page
via injected markup and requires both to be reported. Exit 0 clean / 1 defect(s) /
2 calibration failed / 3 could not measure (server down).

CANNOT SEE: whether the destination is the RIGHT one for the reader (copy), anything that
needs a real pointer's timing (hover intent, drag), states behind login or third parties.
"""
import argparse, json, os, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls

import os as _os
BASE = _os.environ.get('BASE', 'http://localhost:8000')   # BASE=https://arpitmaheshwari.com to explore production
SCROLL = ("(async()=>{const h=document.documentElement.scrollHeight;for(let y=0;y<h;y+=600){scrollTo(0,y);"
          "await new Promise(r=>setTimeout(r,25));}scrollTo(0,0);await new Promise(r=>setTimeout(r,120));"
          "await Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r;setTimeout(r,2500)})));return 1})()")
PAGE_STATE = r"""(()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'};
 const imgs=[...document.images].filter(vis);   /* an image inside a collapsed panel has no width: judged when the panel opens (receipts step), never on load */
 const broken=imgs.filter(i=>!(i.naturalWidth>0)).map(i=>(i.currentSrc||i.getAttribute('src')||'?').split('/').pop().slice(0,60));
 return JSON.stringify({url:location.pathname+location.hash,h1:!!document.querySelector('h1'),
   overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
   imgs:imgs.length,broken})})()"""


def state(br):
    br.eval("(()=>{if(!document.getElementById('__jc')){const s=document.createElement('style');s.id='__jc';s.textContent='html,body{scroll-behavior:auto!important}';document.head.appendChild(s)}return 1})()")
    br.eval(SCROLL, await_promise=True)
    return br.eval_json(PAGE_STATE)


def errors(br):
    out = []
    for e in br.drain('Runtime.exceptionThrown', 'Network.loadingFailed', 'Network.responseReceived'):
        m, p = e['method'], e['params']
        if m == 'Runtime.exceptionThrown':
            out.append('EXCEPTION ' + p['exceptionDetails'].get('text', '')[:80])
        elif m == 'Network.responseReceived':
            r = p['response']
            if r['status'] >= 400 and r['url'].startswith(BASE):
                out.append(f"HTTP {r['status']} {r['url'].replace(BASE, '')[:70]}")
    return out


def page_checks(br, label, defects):
    s = state(br)
    if not s['h1']: defects.append((label, 'no <h1> after landing'))
    if s['overflow'] > 1: defects.append((label, f"horizontal overflow {s['overflow']}px"))
    for b in s['broken']: defects.append((label, f'image never painted: {b}'))
    for e in errors(br): defects.append((label, e))
    return s


def click(br, js_find):
    """Click via a real dispatched click on the found element; returns its href/hash before the click."""
    return br.eval_json("(()=>{const e=%s;if(!e)return null;const h=e.getAttribute('href');e.scrollIntoView({block:'center'});e.click();return JSON.stringify({href:h})})()" % js_find)


def journey(br, width, urls, defects, plant=False):
    mobile = width < 700
    br.viewport(width, 844 if mobile else 900)
    br.cmd('Network.enable')

    # 1 · the primary nav from home
    br.navigate(BASE + '/?view=classic', settle=2); br.eval("(()=>{try{localStorage.clear();sessionStorage.clear()}catch(e){}return 1})()")
    # a FRESH reader per pass: the site remembers 'read as a book' (am-view) and, by design, sends a
    # desktop reader who chose the book back to it from the homepage — the previous pass's visit to
    # the book would otherwise redirect this one and every nav query would answer 0.
    br.navigate(BASE + '/?jc=' + str(width), settle=3); errors(br)   # a distinct URL per width forces a real load, not a same-URL reload mid-eval
    nav = []
    for _ in range(20):   # the nav is static markup, but a same-document reload can answer the first query with the unloading page
        nav = br.eval_json("JSON.stringify([...document.querySelectorAll('#nav .nav-links a')].map(a=>a.getAttribute('href')))")
        if nav: break
        time.sleep(0.15)
    if not nav: defects.append((f'home@{width}', 'no primary nav links found'))
    for href in nav:
        if href.startswith('http') and not href.startswith(BASE): continue   # the Connect door leaves the site; link-integrity owns external URLs
        br.navigate(BASE + '/', settle=2.5); errors(br)
        if mobile:
            br.eval("document.getElementById('menuToggle').click()")
            time.sleep(0.4)
            expanded = br.eval("document.getElementById('menuToggle').getAttribute('aria-expanded')")
            vis = br.eval("(()=>{const a=document.querySelector('#nav .nav-links a');const r=a.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(a).visibility!=='hidden'})()")
            if expanded != 'true' or not vis:
                defects.append((f'home@{width}', f'drawer did not open (aria-expanded={expanded}, links visible={vis})')); continue
        click(br, "[...document.querySelectorAll('#nav .nav-links a')].find(a=>a.getAttribute('href')===%s)" % json.dumps(href))
        time.sleep(0.8)
        landed = br.eval('location.href')
        want = urllib.parse.urljoin(BASE + '/', href)
        if landed.split('#')[0].rstrip('/') != want.split('#')[0].rstrip('/'):
            defects.append((f'nav {href}@{width}', f'landed on {landed.replace(BASE, "")}')); continue
        page_checks(br, f'nav {href}@{width}', defects)

    # 2 · every case page: jump nav lands below the fixed bar; next door leads on
    cases = [u for u in urls if '/case-studies/' in u]
    for u in cases:
        br.navigate(u, settle=2.5); errors(br)
        label = u.replace(BASE, '') + f'@{width}'
        page_checks(br, label, defects)
        if plant and u == cases[0]:
            br.eval("(()=>{const j=document.querySelector('.case-jump');if(j){const a=document.createElement('a');a.href='#zz-missing-anchor';a.textContent='plant';j.appendChild(a)}"
                    "const i=document.createElement('img');i.src='/zz-missing.png';i.width=80;i.height=40;document.querySelector('main').appendChild(i);return 1})()")
            page_checks(br, label + ' (plant)', defects)
        jumps = br.eval_json("JSON.stringify([...document.querySelectorAll('.case-jump a')].map(a=>a.getAttribute('href')))")
        navh = br.eval("(()=>{const n=document.getElementById('nav');return n?n.getBoundingClientRect().height:0})()")
        br.eval("(()=>{if(!document.getElementById('__jc')){const s=document.createElement('style');s.id='__jc';s.textContent='html,body{scroll-behavior:auto!important}';document.head.appendChild(s)}return 1})()")
        for j in jumps:
            if not j.startswith('#'): continue
            click(br, "[...document.querySelectorAll('.case-jump a')].find(a=>a.getAttribute('href')===%s)" % json.dumps(j))
            time.sleep(0.9)
            got = br.eval_json("(()=>{const t=document.getElementById(location.hash.slice(1));if(!t)return JSON.stringify({hash:location.hash,found:false});const r=t.getBoundingClientRect();const maxed=Math.ceil(scrollY)>=document.documentElement.scrollHeight-innerHeight-2;return JSON.stringify({hash:location.hash,found:true,top:Math.round(r.top),vh:innerHeight,maxed})})()")
            if got['hash'] != j: defects.append((label, f'jump {j}: hash became {got["hash"] or "(none)"}'))
            elif not got['found']: defects.append((label, f'jump {j}: no element with that id'))
            elif not (navh - 2 <= got['top'] and (got['top'] <= got['vh'] * 0.6 or got['maxed'])): defects.append((label, f'jump {j}: target top at {got["top"]}px (nav is {int(navh)}px, viewport {got["vh"]})'))
        nxt = br.eval("(()=>{const a=[...document.querySelectorAll('a')].find(a=>/next case study/i.test(a.textContent));return a?a.href:null})()")
        if not nxt: defects.append((label, 'no "Next case study" door'))
        elif nxt.split('#')[0] == u: defects.append((label, 'next door points at this page'))
        else:
            br.navigate(nxt, settle=2.5); errors(br)
            if not br.eval("!!document.querySelector('h1')"): defects.append((label, f'next door {nxt.replace(BASE, "")} has no <h1>'))

    # 3 · home receipts open
    br.navigate(BASE + '/', settle=2.5); errors(br)
    n = br.eval("document.querySelectorAll('.rcpt-btn').length")
    for i in range(n):
        r = br.eval_json("(()=>{const b=document.querySelectorAll('.rcpt-btn')[%d];b.scrollIntoView({block:'center'});b.click();return new Promise(res=>setTimeout(()=>{const p=document.getElementById(b.getAttribute('aria-controls'));const rr=p?p.getBoundingClientRect():{height:0};res(JSON.stringify({exp:b.getAttribute('aria-expanded'),h:Math.round(rr.height),vis:p?getComputedStyle(p).visibility:'none'}))},700))})()" % i, await_promise=True)
        if r['exp'] != 'true' or r['h'] < 40 or r['vis'] == 'hidden':
            defects.append((f'home receipt {i+1}@{width}', f"did not open (aria-expanded={r['exp']}, height={r['h']}, {r['vis']})"))
        br.eval("document.querySelectorAll('.rcpt-btn')[%d].click()" % i); time.sleep(0.3)   # close it again

    # 4 · every internal link resolves, fragments included (once per width is enough → 1440 only)
    if not mobile:
        seen = set()
        for u in urls:
            br.navigate(u, settle=2.0); errors(br)
            links = br.eval_json("JSON.stringify([...document.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>h.startsWith(location.origin)&&!h.startsWith('mailto:')))")
            for h in links:
                if h in seen: continue
                seen.add(h)
                base_url, _, frag = h.partition('#')
                res = br.eval_json("(async()=>{try{const r=await fetch(%s,{cache:'no-store'});const t=r.ok?await r.text():'';return JSON.stringify({ok:r.ok,status:r.status,frag:%s?(t.includes('id=\"'+%s+'\"')||t.includes(\"id='\"+%s+\"'\")):true})}catch(e){return JSON.stringify({ok:false,status:0,frag:false})}})()" % (json.dumps(base_url), json.dumps(frag), json.dumps(frag), json.dumps(frag)), await_promise=True)
                if not res['ok']: defects.append((u.replace(BASE, ''), f"link {h.replace(BASE, '')} → HTTP {res['status']}"))
                elif not res['frag']: defects.append((u.replace(BASE, ''), f"link {h.replace(BASE, '')} → fragment #{frag} not on target"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--widths', default='390,1440')
    ap.add_argument('--no-selftest', action='store_true')
    a = ap.parse_args()
    try:
        if 'localhost' in BASE: cdp.ensure_server(8000)
    except Exception as e:
        print('COULD NOT MEASURE:', e); return 3
    urls = page_urls(base=BASE, include_book=False)
    widths = [int(w) for w in a.widths.split(',')]
    with cdp.Browser() as br:
        if not a.no_selftest:
            planted = []
            journey(br, widths[-1], [u for u in urls if '/case-studies/' in u][:1], planted, plant=True)
            red_img = any('zz-missing.png' in d[1] for d in planted)
            red_jump = any('zz-missing-anchor' in d[1] for d in planted)
            if not (red_img and red_jump):
                print(f'CALIBRATION FAILED: planted broken image reported={red_img}, planted dead jump reported={red_jump}')
                for d in planted: print('   ', d)
                return 2
            print('  calibrated: a planted broken image and a planted dead jump link both go red')
        defects = []
        for w in widths:
            journey(br, w, urls, defects)
    for where, what in defects:
        print(f'  DEFECT  {where:44s} {what}')
    print(f'{len(defects)} journey defect(s) across {len(widths)} width(s). CANNOT SEE: whether a destination is the right one for the reader, pointer timing, third-party states.')
    return 1 if defects else 0


if __name__ == '__main__':
    sys.exit(main())
