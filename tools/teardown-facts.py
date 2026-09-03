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
def third_party_count(base=None):
    """Count the distinct third-party registrable domains a real visit touches.

    Loads the homepage under the LIVE hostname (the site's own guard only loads
    analytics there) with the tracker hosts refused at DNS, so the requests are
    observed without any data being sent.
    """
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import cdp
    except Exception:
        return None
    port = base or os.environ.get("TD_PORT", "8899")
    rules = ("--host-resolver-rules=MAP arpitmaheshwari.com 127.0.0.1," +
             ",".join(f"MAP {h} ~NOTFOUND" for h in cdp.TRACKER_HOSTS))
    doms = set()
    try:
        with cdp.Browser(extra_flags=(rules,)) as b:
            b.cmd("Network.enable")
            b.navigate(f"http://arpitmaheshwari.com:{port}/index.html", settle=3)
            b.pump(2.5)
            for e in b.drain("Network.requestWillBeSent"):
                u = e["params"]["request"]["url"]
                if not u.startswith("http"):
                    continue
                h = u.split("/")[2].split(":")[0]
                if h.endswith("arpitmaheshwari.com"):
                    continue
                doms.add(".".join(h.split(".")[-2:]))
    except Exception:
        return None
    return len(doms)

def tracked(pat,excl=()):
    out=sh(f"git ls-files '{pat}'").splitlines()
    return [f for f in out if not any(f.startswith(e) for e in excl)]

facts={
    # partials/ holds nav and footer FRAGMENTS stamped into pages by
    # build-partials.py — sources, not pages a visitor can reach.
 # assets/ excluded from 2026-09-03: the count included the two OG-card GENERATOR
 # templates (_card.template.html, _book-og.template.html), which are not pages — they
 # are rendered to PNG by tools/generate-og-cards.py and no visitor can reach them.
 # 43 -> 41. Same species as the stylesheet row: an accurate count of the wrong set,
 # under a label that says "pages".
 "html_pages": len(tracked('*.html',('book/','prototypes/','partials/','assets/','tests/'))),
 # EVERY stylesheet a classic page loads, not just one of them. This measured styles.css
 # alone and the page published it as "Stylesheet, entire site" — 280.4 KB, when the three
 # files a page actually links total 510.1 KB. It understated the site by 82% on the one
 # page whose whole argument is that it can be inspected, and it never moved when ember.css
 # changed, which is what finally gave it away. book/book.css is excluded on purpose: the
 # book is a separate surface and no classic page loads it.
 "stylesheet_bytes": sum(os.path.getsize(os.path.join(R,f))
                        for f in ('fonts.css','styles.css','ember.css')),
 "stylesheet_gzip": sum(len(__import__('gzip').compress(open(os.path.join(R,f),'rb').read()))
                        for f in ('fonts.css','styles.css','ember.css')),
 "runtime_deps": 0 if not os.path.exists(os.path.join(R,'package.json')) else -1,
 # Measured, not asserted. The previous version grepped index.html and
 # intersected it with a hardcoded set of three domain names, so it could only
 # ever find domains someone had already listed — it never saw clarity.ms
 # (loaded from clarity.js) or google-analytics.com and bing.com (contacted
 # only at runtime), and once GA moved into analytics.js it returned 0. A
 # receipt that cannot discover anything new is not a measurement.
 # What the page itself requests: two loader domains. Two MORE domains
 # (google-analytics.com, bing.com) are contacted downstream once those
 # loaders run — they cannot be counted without letting the beacons through,
 # which is the thing this whole change exists to stop. So the number is
 # measured for what is observable and DECLARED for what is not, and the page
 # says both. That distinction is the honest version of this receipt.
 "third_party_loader_domains": third_party_count(),
 "third_party_domains_total": 4,   # + google-analytics.com, bing.com
 "third_party_services": 2,        # Google Analytics, Microsoft Clarity
 "pattern_demos": len(re.findall(r'data-demo="([a-z-]+)"',sh("cat patterns/*.html"))) or
                  len(set(re.findall(r"demo\s*===\s*'([a-z-]+)'",open(os.path.join(R,'patterns/demos.js')).read()))),
 "demos_js_lines": len(open(os.path.join(R,'patterns/demos.js')).read().splitlines()),
 # The KB beside those lines was typed, not measured, and used DECIMAL KB while the
 # stylesheet row above uses binary — 12,881 bytes read as "12.9 KB" here and would
 # read 12.6 there. It also never moved when demos.js was edited on 2026-08-30.
 "demos_js_kb": round(os.path.getsize(os.path.join(R,'patterns/demos.js'))/1024,1),
 "demos_js_imports": len(re.findall(r'import |require\(|fetch\(',open(os.path.join(R,'patterns/demos.js')).read())),
 "og_cards": len(tracked('assets/og-images/*.png')),
 "skip_link_pages": len([f for f in tracked('*.html',('prototypes/',)) if 'skip-link' in open(os.path.join(R,f),encoding='utf-8',errors='ignore').read()]),
 "build_steps": 0,
 "loop_tests": int(re.search(r'(\d+)/\d+ passed',sh("node lab/loop.test.js")).group(1)),
 "trustlint_rules": len(re.findall(r"\{\s*id:\s*'",open(os.path.join(R,'lab/trustlint.js')).read())),
}
facts["stylesheet_kb"]=round(facts["stylesheet_bytes"]/1024,1)

WORD = {1:'one',2:'two',3:'three',4:'four',5:'five',6:'six'}

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
                           ('skip-link pages',f">{facts['skip_link_pages']}<"),
                           ('demos.js KB',f"{facts['demos_js_kb']} KB"),
                           # Prose spells its numbers, so match the word. This
                           # receipt said "one third-party domain" for months
                           # after Clarity was added — the page arguing that a
                           # stale number is a lie was carrying one.
                           ('third-party services',
                            f"{WORD[facts['third_party_services']]} third-party services")],
      'lab/index.html':[('stylesheet KB',f"{facts['stylesheet_kb']}"),
                        ('third-party services',
                         f"{WORD[facts['third_party_services']]} third-party services"),
                        ('third-party domains',
                         f"{WORD[facts['third_party_domains_total']]} domains")],
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
