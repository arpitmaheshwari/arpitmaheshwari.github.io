#!/usr/bin/env python3
"""render-census.py — every element's position and computed style, before and after.

WHY THIS EXISTS (2026-09-12). Three stylesheets are being folded into one and moved
onto cascade layers. Execution lesson 12 says a structural change needs a BEFORE
measurement, not an after-check: wrapping the nav in <header> once pushed `main`
down 183px on five pages and only a before/after diff caught it. This is that diff,
for CSS — it records, for every element on every page at four widths, where it sits
and what it computes, and reports what changed between two captures.

It is the instrument the consolidation is judged by. "The page looks the same" is
an opinion; "0 of 41,000 elements moved and 12 changed colour, all of them the ones
the change was meant to recolour" is a measurement.

WHAT IT CANNOT SEE, stated so nobody mistakes a clean diff for a clean page:
  * pseudo-elements (::before/::after) — their boxes are not in the DOM walk. A glow
    painted by a ::before that stops painting shows up only as the parent's pixels
    changing, which contrast-audit sees and this does not.
  * post-interaction state — a drawer opened, a receipt toggled. It captures the
    loaded page after one scroll-through.
  * pixels. It reads computed values. Two captures with identical values can render
    differently only if the browser changed, which is why both captures run in the
    same Chrome.

USAGE
    render-census.py capture OUTDIR [--widths 390,768,1024,1440] [URL ...]
    render-census.py diff BEFORE_DIR AFTER_DIR [--ignore color,background-color,...]
    render-census.py --selftest        # a capture must differ from itself by 0 and
                                       # from a perturbed page by >0, or it is not
                                       # an instrument

Exit codes (repo convention): 0 clean / 1 differences found / 2 calibration failed /
3 could not measure.
"""
import argparse, gzip, json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
from gatelib import page_urls

PROPS = ['color', 'background-color', 'background-image', 'border-top-color',
         'border-top-width', 'border-top-style', 'border-right-width',
         'border-bottom-width', 'border-left-width', 'border-bottom-color',
         'border-left-color', 'border-right-color', 'border-radius', 'box-shadow',
         'font-family', 'font-size', 'font-weight', 'font-style', 'line-height',
         'letter-spacing', 'text-transform', 'text-decoration-line', 'opacity',
         'display', 'position', 'padding-top', 'padding-right', 'padding-bottom',
         'padding-left', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
         'gap', 'text-align', 'visibility', 'filter', 'outline-color', 'fill',
         'stroke', 'max-width', 'grid-template-columns', 'flex-direction',
         'align-items', 'justify-content']

# Transitions and reveal animations are frozen before the read: a capture must not
# depend on how far a 400ms fade had got. Both sides of a diff get the same freeze.
FREEZE = ("(()=>{const s=document.createElement('style');s.id='__census_freeze';"
          "s.textContent='*,*::before,*::after{transition:none!important;"
          "animation-duration:0s!important;animation-delay:0s!important}';"
          "document.head.appendChild(s);return true})()")

CENSUS = r"""
(()=>{
  const P=%s;
  const path=el=>{const parts=[];
    while(el&&el.nodeType===1&&el!==document.body){
      const p=el.parentElement;let i=1;
      if(p){for(const s of p.children){if(s===el)break;i++}}
      parts.unshift(el.tagName.toLowerCase()+(el.id?'#'+el.id:'')+':'+i);el=p}
    return parts.join('>')};
  const skip=new Set(['SCRIPT','STYLE','LINK','META','TEMPLATE','NOSCRIPT']);
  const out=[];
  for(const el of document.body.querySelectorAll('*')){
    if(skip.has(el.tagName))continue;
    // SVG interiors are drawings, not layout; the <svg> box itself is kept.
    if(el.namespaceURI==='http://www.w3.org/2000/svg'&&el.tagName.toLowerCase()!=='svg')continue;
    if(el.id==='__census_freeze')continue;
    const r=el.getBoundingClientRect(),cs=getComputedStyle(el);
    const cls=(typeof el.className==='string')?el.className.trim().split(/\s+/).slice(0,3).join(' '):'';
    out.push({p:path(el),c:cls,
      r:[Math.round(r.left+scrollX),Math.round(r.top+scrollY),Math.round(r.width),Math.round(r.height)],
      s:P.map(k=>{const v=cs.getPropertyValue(k);return v.length>90?v.slice(0,90)+'…':v}).join('|')});
  }
  return JSON.stringify({h:document.documentElement.scrollHeight,n:out.length,els:out});
})()
""" % json.dumps(PROPS)


def slug(url):
    s = re.sub(r'^https?://[^/]+/', '', url).strip('/') or 'index'
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s)


def capture_page(br, url, width):
    br.viewport(width, 900)
    br.navigate(url, settle=3.0)
    br.eval(FREEZE)
    br.scroll_through(step=600, pause=8)
    br.eval("scrollTo(0,0)")
    data = br.eval_json(CENSUS)
    if not data or data.get('n', 0) < 5:
        raise RuntimeError(f"census read {data and data.get('n')} elements at {url}@{width} — not a page")
    return data


def capture(outdir, urls, widths):
    os.makedirs(outdir, exist_ok=True)
    total = 0
    with cdp.Browser() as br:
        for url in urls:
            for w in widths:
                data = capture_page(br, url, w)
                fn = os.path.join(outdir, f"{slug(url)}@{w}.json.gz")
                with gzip.open(fn, 'wt', encoding='utf-8') as fh:
                    json.dump(data, fh, separators=(',', ':'))
                total += data['n']
                print(f"  {slug(url):48s} @{w:<5} {data['n']:5d} elements  h={data['h']}")
    print(f"captured {len(urls)} pages x {len(widths)} widths, {total:,} elements -> {outdir}")


def load_dir(d):
    out = {}
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.json.gz'):
            with gzip.open(os.path.join(d, fn), 'rt', encoding='utf-8') as fh:
                out[fn[:-len('.json.gz')]] = json.load(fh)
    return out


def diff(before_dir, after_dir, ignore=(), geo_tol=1, show=40):
    A, B = load_dir(before_dir), load_dir(after_dir)
    keys = sorted(set(A) | set(B))
    ign = set(ignore)
    prop_groups = collections.Counter()
    prop_examples = collections.defaultdict(list)
    geo = collections.Counter()
    geo_examples = collections.defaultdict(list)
    missing = collections.Counter()
    heights = []
    total_el = 0
    for k in keys:
        if k not in A or k not in B:
            print(f"  ONLY IN {'before' if k in A else 'after'}: {k}")
            continue
        a = {e['p']: e for e in A[k]['els']}
        b = {e['p']: e for e in B[k]['els']}
        total_el += len(a)
        if A[k]['h'] != B[k]['h']:
            heights.append((k, A[k]['h'], B[k]['h']))
        only_a = set(a) - set(b); only_b = set(b) - set(a)
        if only_a or only_b:
            missing[k] = len(only_a) + len(only_b)
        for p in a.keys() & b.keys():
            ea, eb = a[p], b[p]
            if any(abs(x - y) > geo_tol for x, y in zip(ea['r'], eb['r'])):
                geo[k] += 1
                if len(geo_examples[k]) < 3:
                    geo_examples[k].append((p.split('>')[-1], ea['c'], ea['r'], eb['r']))
            if ea['s'] != eb['s']:
                sa, sb = ea['s'].split('|'), eb['s'].split('|')
                for name, va, vb in zip(PROPS, sa, sb):
                    if va != vb and name not in ign:
                        g = (name, va, vb)
                        prop_groups[g] += 1
                        if len(prop_examples[g]) < 2:
                            prop_examples[g].append(f"{k} {ea['c'] or p.split('>')[-1]}")
    n_geo = sum(geo.values()); n_prop = sum(prop_groups.values())
    print(f"\n{len(keys)} captures, {total_el:,} elements compared"
          f"{' (ignoring ' + ','.join(sorted(ign)) + ')' if ign else ''}")
    print(f"  page heights changed : {len(heights)}")
    for k, h0, h1 in heights[:show]:
        print(f"    {k:52s} {h0:6d} -> {h1:6d}  ({h1-h0:+d}px)")
    print(f"  elements moved/resized: {n_geo} across {len(geo)} captures")
    for k, n in geo.most_common(show):
        print(f"    {k:52s} {n:5d}")
        for tag, cls, r0, r1 in geo_examples[k]:
            print(f"        {tag:14s} {cls[:28]:28s} {r0} -> {r1}")
    print(f"  elements added/removed: {sum(missing.values())} across {len(missing)} captures")
    print(f"  property changes      : {n_prop} in {len(prop_groups)} distinct (property, before -> after) groups")
    for (name, va, vb), n in prop_groups.most_common(show):
        print(f"    x{n:<5} {name:22s} {va[:34]:34s} -> {vb[:34]}")
        for ex in prop_examples[(name, va, vb)]:
            print(f"           e.g. {ex}")
    return 1 if (n_geo or n_prop or heights or missing) else 0


def selftest():
    """A capture must equal itself and differ from a perturbed page."""
    import tempfile
    url = 'http://localhost:8000/'
    with cdp.Browser() as br:
        d1 = capture_page(br, url, 1024)
        d2 = capture_page(br, url, 1024)
        br.eval("(()=>{const s=document.createElement('style');s.textContent='p{margin-top:3px !important;color:rgb(1,2,3)!important}';document.head.appendChild(s);return 1})()")
        d3 = br.eval_json(CENSUS)
    same = sum(1 for a, b in zip(d1['els'], d2['els']) if a['s'] != b['s'] or a['r'] != b['r'])
    a = {e['p']: e for e in d1['els']}; c = {e['p']: e for e in d3['els']}
    changed = sum(1 for p in a.keys() & c.keys() if a[p]['s'] != c[p]['s'] or a[p]['r'] != c[p]['r'])
    print(f"  self vs self : {same} differences (must be 0)")
    print(f"  self vs plant: {changed} differences (must be >0)")
    if same != 0 or changed == 0:
        print("CALIBRATION FAILED"); return 2
    print("calibrated"); return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', nargs='?', choices=['capture', 'diff'])
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--widths', default='390,768,1024,1440')
    ap.add_argument('--ignore', default='')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    cdp.ensure_server(8000)
    if a.selftest:
        return selftest()
    if a.mode == 'capture':
        outdir, urls = a.paths[0], a.paths[1:] or page_urls(include_book=False)
        capture(outdir, urls, [int(w) for w in a.widths.split(',')])
        return 0
    if a.mode == 'diff':
        return diff(a.paths[0], a.paths[1], ignore=[x for x in a.ignore.split(',') if x])
    ap.print_help(); return 3


if __name__ == '__main__':
    sys.exit(main())
