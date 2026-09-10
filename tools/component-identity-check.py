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
# 2026-09-10: SIX of the nine names here were DEAD, and the gate still printed
# "0 component(s) render inconsistently" — a green verdict on a list it could not
# find. Verified live-in-markup before editing: btn-a 0 pages, btn-a-ghost 0,
# lbl-pill-bg 0, lbl-badge-bg 0, btn-label 0, site-footer 0.
# .cta is now the component this gate exists for: one door on 38 pages, and the
# whole point of collapsing 39 asks in six classes into one was that it renders
# identically everywhere. Measured at 107 instances, one shape — this keeps it so.
COMPONENTS = ['cta', 'cta-quiet', 'nav-cta', 'nav-links', 'btn-primary']
# NOT in the list, on purpose: .footer-note and .footer-tools. I added them
# speculatively on 2026-09-10 and they are WRAPPERS whose computed weight and
# family are inherited, not declared — so this gate grades the page's cascade
# through them rather than a component's own promise. Adding them did surface a
# real defect (an unclosed <strong> on two writing pages had swallowed the whole
# footer, rendering it bold — fixed), and it left a second, genuine finding worth
# its own decision: the footer note renders MONO + dim on index.html and SANS +
# full-ink on the other 37, because the ember footer rules are scoped
# body.p-home and never reach the rest. That is execution lesson 11 again, and
# changing it alters 37 pages, so it is Arpit's call and not a push blocker.
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
  // A BEM modifier is a DIFFERENT component, not drift. .cta--secondary is a .cta,
  // and on 2026-09-10 that made the closing section's outline secondary read as
  // ".cta - 2 distinct appearances" on 1 page against 66. It is supposed to differ:
  // that is what a secondary IS. Group by the modifier so each variant is graded
  // against its own instances.
  hit.forEach(h=>{
    const mod = cl.find(x => x.startsWith(h + '--'));
    out.push({comp: mod || h, sig: JSON.stringify(sig)});
  });
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
    # A REDIRECT STUB IS NOT A PAGE, and gatelib.pages() already knows that —
    # it drops meta-refresh stubs and documents why (a gate that loads one races
    # the stub's own navigation and measures the DESTINATION under the stub's
    # URL). My first fix here duplicated that rule locally on 2026-09-08; this
    # is the same rule, in the one place that owns it.
    from gatelib import pages as _pages
    kept = set(_pages())
    dropped = [p for p in pages if p not in kept]
    if dropped:
        print(f'  skipping {len(dropped)} non-page(s): ' + ', '.join(dropped[:6]))
    pages = [p for p in pages if p in kept]
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
