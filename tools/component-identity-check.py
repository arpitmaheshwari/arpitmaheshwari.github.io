#!/usr/bin/env python3
"""One component must look the same on every page it appears on.

The gate that was missing. Every other visual gate here asks about ONE element
on ONE page: is it readable, does it overflow, is it reachable. None of them
compares a component to ITSELF on another page, so a button could render as a
flat gold slab on six pages and a gradient pill on three and every gate stayed
green. Arpit found it by looking at two case studies side by side.

It reports, per component class, the distinct rendered appearances and which
pages hold each one. Any component with more than one appearance is a finding.
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

# Components whose appearance is a design-system promise, not a page decision.
COMPONENTS = ['btn-a', 'btn-primary', 'btn-a-ghost', 'lbl-pill-bg', 'lbl-badge-bg',
              'btn-label', 'nav-cta', 'site-footer', 'nav-links']
# Properties that define "the same button". Size/position are layout, not identity.
PROPS = ['background-image', 'background-color', 'color', 'border-radius',
         'font-family', 'font-weight', 'letter-spacing', 'text-transform']

JS = """(()=>{const want=%s, props=%s, out=[];
document.querySelectorAll('*').forEach(e=>{
  const cl=[...e.classList]; const hit=want.filter(w=>cl.includes(w));
  if(!hit.length) return;
  const r=e.getBoundingClientRect(); if(!r.width||!r.height) return;
  const c=getComputedStyle(e);
  const sig={}; props.forEach(p=>sig[p]=c.getPropertyValue(p));
  hit.forEach(h=>out.push({comp:h, sig:JSON.stringify(sig)}));
});
return out;})()""" % (json.dumps(COMPONENTS), json.dumps(PROPS))


def main():
    base = os.environ.get('BASE', 'http://localhost:8899')
    pages = sorted(p for p in glob.glob('**/*.html', recursive=True)
                   if not p.startswith(('partials/', 'node_modules/', 'tests/', 'prototypes/'))
                      and not os.path.basename(p).startswith('__'))
    seen = collections.defaultdict(lambda: collections.defaultdict(list))
    with cdp.Browser() as b:
        b.viewport(1440, 900)
        for p in pages:
            try:
                b.navigate(f'{base}/{p}', settle=1.0)
            except RuntimeError as e:
                print(f'  ! {p}: {e}')
                continue
            for r in b.eval_json(JS) or []:
                seen[r['comp']][r['sig']].append(p)

    findings = 0
    for comp in COMPONENTS:
        variants = seen.get(comp)
        if not variants or len(variants) == 1:
            continue
        findings += 1
        print(f'\nDRIFT  .{comp} — {len(variants)} distinct appearances')
        rows = sorted(variants.items(), key=lambda kv: -len(kv[1]))
        # Only print the properties that actually differ — a truncated fill
        # made two identical-looking gradients read as the same variant when
        # the real drift was in letter-spacing.
        parsed = [json.loads(sig) for sig, _ in rows]
        differing = [k for k in PROPS
                     if len({d[k] for d in parsed}) > 1]
        for (sig, pgs), d in zip(rows, parsed):
            print(f'   {len(pgs):>3} page(s)  '
                  + '  '.join(f'{k}={d[k][:44]}' for k in differing))
            print(f'        {", ".join(sorted(set(pgs))[:6])}'
                  f'{" …" if len(set(pgs)) > 6 else ""}')
    print(f'\n{findings} component(s) render inconsistently across pages.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
