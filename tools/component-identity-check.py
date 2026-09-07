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
    # BASE is honoured for standalone runs; the pre-push hook exports it so the gate uses the
    # server the hook already started. This used to hard-code :8899 with no way to override,
    # so it passed only when a dev server happened to be on that port and failed outright on a
    # clean machine — including straight after a reboot, which is exactly when a push matters.
    base = os.environ.get('BASE', 'http://localhost:8899')
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import cdp as _cdp
    _cdp.ensure_server(int(base.rsplit(':', 1)[1]))
    pages = sorted(p for p in glob.glob('**/*.html', recursive=True)
                   if not p.startswith(('partials/', 'node_modules/', 'tests/', 'prototypes/'))
                      and not os.path.basename(p).startswith('__'))
    # A REDIRECT STUB IS NOT A PAGE. Three files on this site exist only to bounce
    # an old URL (case-studies/talon.html, lab/hitl.html, lab/trustlayer.html) and
    # each says so in its own markup. They carry a 0-second meta refresh, so with
    # settle=1.0 this gate was measuring a page mid-navigation — sometimes after
    # the stylesheet applied, sometimes before. Before, everything reads as
    # unstyled: Times New Roman, rgb(0,0,238) links, border-radius 0. On
    # 2026-09-08 that surfaced on the CI runner as ".nav-cta - 2 distinct
    # appearances, 40 pages vs 1", which is a race in the instrument reported as
    # drift in the site. It had been passing on luck.
    # Detected from the markup, not from a list of the three filenames I happen to
    # know about — a rule shaped like the instances you already found can only
    # ever re-find those.
    def is_redirect_stub(path):
        try:
            head = open(path, encoding='utf-8', errors='replace').read(2048)
        except OSError:
            return False
        return 'http-equiv="refresh"' in head.replace("'", '"')
    stubs = [p for p in pages if is_redirect_stub(p)]
    if stubs:
        print(f'  skipping {len(stubs)} redirect stub(s): ' + ', '.join(stubs))
    pages = [p for p in pages if p not in stubs]
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
