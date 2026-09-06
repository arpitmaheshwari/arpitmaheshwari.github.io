#!/usr/bin/env python3
"""Two structural properties of a long page that no gate in this repo measured.

Both were found by hand on 2026-09-07, on /case-studies/o2 — a page that was
green on contrast, heading-rank, a11y-sweep, reflow, target-size and leading:

  A. HEADING UNIQUENESS. o2 carried the h2 "The stakes: two screens carried
     O2's whole retention story." TWICE — once correctly in §01, once as a
     copy-paste over §04's own thesis. Every gate here asks about ONE element's
     properties (its ink, its size, its rank, its leading). None compares two
     elements' TEXT, so a duplicated heading is invisible to all of them, and a
     reader scrolling past §04 is told they are back in §01.

  B. NAV COMPLETENESS. Five of eight case studies had a section with its own h2
     that the page's own jump nav did not list: o2 #the-honest-line, fintech
     #cost, ptc #the-cost, vc-diligence #the-cost, orgos #the-move AND
     #the-principle. On a 2,000-word page the jump nav IS the table of
     contents; a section missing from it is only reachable by scrolling past
     it. "Present" and "reachable by the page's own navigation" are different
     properties — the same distinction reachability-check draws for content
     parked behind a sideways scroll.

Rule B is deliberately generous about WHERE the target sits: an h2 counts as
reachable if it is a jump target itself, or lives inside one. That is how the
`recon-*` demo sections are reachable through the mechanism section that holds
them, with no name-shaped exemption list — a list built from the instances I
already found can only ever re-find those.

Self-calibrating: plants a duplicate heading and an unlisted section, and
requires the gate to go red on each.
"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
cdp.ensure_server(8000)
from cdp import Browser
import gatelib

JS = r"""JSON.stringify((function(){
  var main = document.querySelector('main') || document.body;

  // ---- A: every heading's text, normalised
  var heads = [];
  main.querySelectorAll('h1,h2,h3,h4,[role="heading"]').forEach(function(e){
    if (!e.getBoundingClientRect().height) return;
    var t = e.textContent.replace(/\s+/g,' ').trim();
    if (!t) return;
    heads.push({tag:e.tagName.toLowerCase(), lvl:e.getAttribute('aria-level')||'',
                text:t, id:e.id||''});
  });

  // ---- B: the page's own in-page nav, and the h2s it must reach
  var nav = main.querySelector('.case-jump') ||
            document.querySelector('.case-jump');
  var targets = [];
  if (nav) nav.querySelectorAll('a[href^="#"]').forEach(function(a){
    targets.push(a.getAttribute('href').slice(1));
  });
  var tset = {}; targets.forEach(function(t){ tset[t]=1; });

  var unreached = [];
  if (nav) main.querySelectorAll('h2').forEach(function(h){
    if (!h.getBoundingClientRect().height) return;
    if (h.closest('.case-jump,.vslip,.vplate,figure,aside')) return;  // chrome, not spine
    var hit = false;
    for (var n = h; n && n !== document.body; n = n.parentElement) {
      if (n.id && tset[n.id]) { hit = true; break; }
    }
    if (!hit) unreached.push({text:h.textContent.replace(/\s+/g,' ').trim().slice(0,58),
                              id:h.id||'', sec:(h.closest('section[id]')||{}).id||''});
  });

  return {heads:heads, has_nav:!!nav, targets:targets, unreached:unreached};
})())"""


def check(br, url, plant=None):
    br.navigate(url, settle=1.6)
    if plant:
        br.eval(plant); br.pump(0.3)
    d = br.eval_json(JS)
    if not d:
        return [("could not read the page", "")]
    findings = []
    seen = {}
    for h in d["heads"]:
        key = h["text"].lower()
        if key in seen:
            findings.append(("DUPLICATE HEADING",
                             f"{seen[key]} and {h['tag']}{h['lvl']} both say “{h['text'][:62]}”"))
        else:
            seen[key] = h["tag"] + h["lvl"]
    for u in d["unreached"]:
        where = f" (section #{u['sec']})" if u["sec"] else ""
        findings.append(("NOT IN THE JUMP NAV", f"“{u['text']}”{where}"))
    return findings


def sweep(br, pages, plant=None, quiet=False):
    total = []
    for url in pages:
        f = check(br, url, plant=plant)
        total += [(url, k, m) for k, m in f]
        if not quiet:
            tag = "FAIL" if f else "ok  "
            print(f"{tag} {url.split('localhost:8000')[-1]}")
            for k, m in f:
                print(f"       {k}: {m}")
    return total


def main():
    pages = gatelib.page_urls("http://localhost:8000")
    with Browser() as br:
        br.viewport(1440, 900)

        # ---- calibration: this gate is not evidence until it has gone red.
        cal_url = "http://localhost:8000/case-studies/o2.html"
        dup = ("(function(){var h=document.querySelectorAll('main h2');"
               "if(h.length>1)h[1].textContent=h[0].textContent;})()")
        got = check(br, cal_url, plant=dup)
        if not any(k == "DUPLICATE HEADING" for k, _ in got):
            print("[calibration] FAIL — planted a duplicate h2 and the gate stayed green."); sys.exit(2)
        hide = ("(function(){var n=document.querySelector('.case-jump');"
                "if(n)n.querySelectorAll('a')[1].remove();})()")
        got = check(br, cal_url, plant=hide)
        if not any(k == "NOT IN THE JUMP NAV" for k, _ in got):
            print("[calibration] FAIL — removed a jump link and the gate stayed green."); sys.exit(2)
        print("[calibration] PASS — red on a duplicated heading and on an unlisted section")

        bad = sweep(br, pages)

    print()
    print("CANNOT SEE: whether a heading is the RIGHT heading for its section (only that "
          "no two on a page are identical), whether a jump label describes its target, or "
          "whether the nav's ORDER matches the document's.")
    if bad:
        print(f"\n{len(bad)} finding(s) across {len(pages)} page(s).")
        sys.exit(1)
    print(f"\nclean across {len(pages)} page(s).")


if __name__ == "__main__":
    main()
