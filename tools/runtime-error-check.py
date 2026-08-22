#!/usr/bin/env python3
"""Fail when a page throws, logs an error, or asks for a file it never gets.

The whole gate suite here is about how a page LOOKS. Not one of them opens the
console. A page can render perfectly and still be quietly broken: a script that
threw before wiring up a button, a font or image 404ing, a fetch to a dead
endpoint. A prospect with devtools open — and engineering leaders do open
devtools on an engineer's portfolio — sees red text on a site that claims
craft.

Three failure kinds:
  EXCEPTION      an uncaught JS error
  CONSOLE-ERROR  something the page itself logged at error level
  FAILED-REQUEST a network request that did not deliver (4xx/5xx/blocked)

Third-party analytics is excluded on purpose: it is blocked in this
environment and its failures say nothing about the site.

CALIBRATION
    --selftest loads a page and injects a throw plus a request for a file that
    cannot exist, and requires both to be reported.
"""
import argparse, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp

# Not the site's fault, and not reachable from here.
IGNORE = re.compile(r'googletagmanager|google-analytics|doubleclick|'
                    r'gtag/js|substack\.com|medium\.com|fonts\.gstatic', re.I)


def collect(br):
    out = []
    events = br.drain('Runtime.exceptionThrown', 'Runtime.consoleAPICalled',
                      'Log.entryAdded', 'Network.loadingFailed',
                      'Network.responseReceived', 'Network.requestWillBeSent')
    # loadingFailed carries only a requestId, so a failure arrived as
    # "Fetch — net::ERR_ABORTED" with no way to tell whose request it was, or
    # to exclude analytics. Remember what each id asked for.
    urls = {e['params']['requestId']: e['params'].get('request', {}).get('url', '')
            for e in events if e['method'] == 'Network.requestWillBeSent'}
    for e in events:
        m, p = e['method'], e.get('params', {})
        if m == 'Runtime.exceptionThrown':
            d = p.get('exceptionDetails', {})
            txt = (d.get('exception', {}).get('description')
                   or d.get('text') or 'threw')
            out.append(('EXCEPTION', txt.split('\n')[0][:150]))
        elif m == 'Runtime.consoleAPICalled' and p.get('type') == 'error':
            txt = ' '.join(str(a.get('value', a.get('description', '')))
                           for a in p.get('args', []))[:150]
            if txt.strip():
                out.append(('CONSOLE-ERROR', txt))
        elif m == 'Log.entryAdded' and p.get('entry', {}).get('level') == 'error':
            en = p['entry']
            out.append(('CONSOLE-ERROR',
                        f"{en.get('text','')[:110]} {en.get('url','')[:60]}".strip()))
        elif m == 'Network.loadingFailed':
            u = urls.get(p.get('requestId'), '')
            out.append(('FAILED-REQUEST',
                        f"{p.get('type','')} {p.get('errorText','blocked')} "
                        f"{u[:110]}".strip()))
        elif m == 'Network.responseReceived':
            r = p.get('response', {})
            if r.get('status', 0) >= 400:
                out.append(('FAILED-REQUEST',
                            f"{r['status']} {r.get('url','')[:110]}"))
    return [(k, v) for k, v in out if not IGNORE.search(v)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8899')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('pages', nargs='*')
    a = ap.parse_args()

    pages = a.pages or sorted(
        p for p in glob.glob('**/*.html', recursive=True)
        if not p.startswith(('partials/', 'node_modules/', 'tests/', 'prototypes/'))
           and not os.path.basename(p).startswith('__'))

    bad, total = [], 0
    with cdp.Browser() as br:
        br.cmd('Network.enable'); br.cmd('Log.enable')
        br.viewport(1440, 900)

        if a.selftest:
            br.navigate(f'{a.base}/{pages[0]}', settle=2.0)
            br.drain()
            br.eval("setTimeout(()=>{throw new Error('planted')},0);"
                    "fetch('/__selftest_missing_asset.png').catch(()=>{})")
            br.pump(1.5)
            hits = collect(br)
            ok = (any(k == 'EXCEPTION' for k, _ in hits)
                  and any(k == 'FAILED-REQUEST' for k, _ in hits))
            print(f'[calibration] {"PASS" if ok else "FAIL"} — a planted throw and a '
                  f'404 request are {"caught" if ok else "INVISIBLE"}')
            if not ok:
                for h in hits:
                    print('   saw:', h)
                return 2

        for p in pages:
            total += 1
            try:
                br.navigate(f'{a.base}/{p}', settle=2.5)
            except RuntimeError as e:
                bad.append((p, [('FAILED-REQUEST', str(e))])); continue
            br.scroll_through()           # lazy assets and observers fire too
            br.pump(0.6)
            hits = sorted(set(collect(br)))
            if hits:
                bad.append((p, hits))
                print(f'\n{p}')
                for kind, txt in hits:
                    print(f'   {kind:15} {txt}')

    print(f'\n{sum(len(h) for _, h in bad)} runtime problem(s) on '
          f'{len(bad)} of {total} page(s)')
    print('CANNOT SEE: errors that only occur after a click, warnings (only '
          'error level is failed on), and anything third-party analytics does.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
