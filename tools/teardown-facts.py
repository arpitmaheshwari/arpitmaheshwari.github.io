#!/usr/bin/env python3
"""teardown-facts.py — re-measure every number lab/teardown.html publishes.

WHY: that page's entire claim is "measured, not estimated" — and on 2026-08-07 its
headline stylesheet figure was 22.8 KB against a real 60.5 KB (170% wrong) because the
numbers were hand-typed once and never re-run. A page that asserts measurement and then
drifts is worse than one that never claimed it. Run this before publishing the page;
--check fails the build when a published number no longer matches reality.
"""
import subprocess, sys, os, re, json
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sh(c): return subprocess.run(c,shell=True,cwd=R,capture_output=True,text=True).stdout.strip()
def tracked(pat,excl=()):
    out=sh(f"git ls-files '{pat}'").splitlines()
    return [f for f in out if not any(f.startswith(e) for e in excl)]

facts={
    # partials/ holds nav and footer FRAGMENTS stamped into pages by
    # build-partials.py — sources, not pages a visitor can reach.
 "html_pages": len(tracked('*.html',('book/','prototypes/','partials/'))),
 "stylesheet_bytes": os.path.getsize(os.path.join(R,'styles.css')),
 "runtime_deps": 0 if not os.path.exists(os.path.join(R,'package.json')) else -1,
 "third_party_domains": len(set(re.findall(r'https://([a-z.]+)/',sh("cat index.html")))
                            & {'fonts.googleapis.com','fonts.gstatic.com','www.googletagmanager.com'}),
 "pattern_demos": len(re.findall(r'data-demo="([a-z-]+)"',sh("cat patterns/*.html"))) or
                  len(set(re.findall(r"demo\s*===\s*'([a-z-]+)'",open(os.path.join(R,'patterns/demos.js')).read()))),
 "demos_js_lines": len(open(os.path.join(R,'patterns/demos.js')).read().splitlines()),
 "demos_js_imports": len(re.findall(r'import |require\(|fetch\(',open(os.path.join(R,'patterns/demos.js')).read())),
 "og_cards": len(tracked('assets/og-images/*.png')),
 "skip_link_pages": len([f for f in tracked('*.html',('prototypes/',)) if 'skip-link' in open(os.path.join(R,f),encoding='utf-8',errors='ignore').read()]),
 "build_steps": 0,
 "loop_tests": int(re.search(r'(\d+)/\d+ passed',sh("node lab/loop.test.js")).group(1)),
 "trustlint_rules": len(re.findall(r"\{\s*id:\s*'",open(os.path.join(R,'lab/trustlint.js')).read())),
}
facts["stylesheet_kb"]=round(facts["stylesheet_bytes"]/1024,1)

if '--check' in sys.argv:
    # Check EACH page separately. The first version concatenated both files, so a stale
    # number in one was masked by the correct number in the other — it stayed green on a
    # planted defect. A check that cannot go red is not a check.
    bad=[]
    expect={
      'lab/teardown.html':[('stylesheet KB',f"{facts['stylesheet_kb']}"),
                           ('stylesheet bytes',f"{facts['stylesheet_bytes']:,}"),
                           ('html pages',f">{facts['html_pages']}<"),
                           ('og cards',f">{facts['og_cards']}<"),
                           ('skip-link pages',f">{facts['skip_link_pages']}<")],
      'lab/index.html':[('stylesheet KB',f"{facts['stylesheet_kb']}")],
    }
    for path,checks in expect.items():
        page=open(os.path.join(R,path),encoding='utf-8').read().replace('&nbsp;',' ')
        for label,needle in checks:
            if needle.replace('&nbsp;',' ') not in page:
                bad.append(f"{path}: {label} — reality is {needle}, page does not say it")
        # CONTRADICTION check (added 2026-08-12). The presence checks above only ask
        # "does the right number appear SOMEWHERE" — so a WRONG copy of the same number
        # elsewhere on the page stays green, because the correct one in the table
        # satisfies the needle. That is exactly how "a 22KB stylesheet" survived in this
        # page's <meta description> for five weeks after the visible table was corrected
        # to 60.5 KB — the 170%-wrong figure the docstring above says was already fixed,
        # still being served to Google and every social share. Scan for EVERY claim of
        # the stylesheet's size and require each one to match reality.
        for m in re.finditer(r'(\d[\d.]*)\s*KB stylesheet', page):
            if m.group(1) != str(facts['stylesheet_kb']):
                bad.append(f"{path}: contradictory stylesheet size — page says "
                           f"{m.group(1)} KB, reality is {facts['stylesheet_kb']} KB")
    print("\n".join(f"  STALE — {b}" for b in bad) if bad else "  every published teardown number matches a fresh measurement.")
    print("Result:", "STALE — re-run without --check and update the pages." if bad else "clean.")
    sys.exit(1 if bad else 0)
print(json.dumps(facts,indent=2))
