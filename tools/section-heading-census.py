#!/usr/bin/env python3
"""section-heading-census — is there ONE section-heading component, and does it
survive fast scrolling?

Arpit, after a fix that moved one number: "apply first principles, review the
design system, review all the section headings across the website, make sure
they're easily distinguishable while fast scrolling, and fix them throughout.
Think like an information architect and a visual designer; currently we are
thinking like a clerk."

So this does not check a size against a floor. It asks the four questions a
scanning reader's eye actually asks, and it asks them of EVERY section heading
on EVERY page:

  DOMINANCE   is the heading clearly the largest thing in its own band? During
              fast scrolling small differences vanish — 35px against 30px is
              not a hierarchy, it is a coincidence. Ratio to the largest
              competing text in the same section.
  ISOLATION   does it have air? A heading 6px from its body text reads as the
              body text's first line, at any speed.
  ANCHOR      is it in the same place every time? A scanning eye locks onto a
              constant left edge; a heading that moves horizontally between
              sections cannot be tracked.
  CONSISTENCY is it ONE component? Count the distinct (size, weight, family,
              colour, tracking) signatures site-wide. More than one per page
              family means there is no component, only instances.

Thresholds are derived from the two sections on this site that already read
correctly (aiwork and thoughts: ratio 1.59, 40px of air), not invented.

CANNOT SEE: whether the heading's WORDS say where you are, reading order,
or salience during real motion — a screenshot has no motion blur. It measures
the properties that survive it.
"""
import sys, glob, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as _cdp
_cdp.ensure_server(8000)
from cdp import Browser

DOMINANCE = 1.40
ISOLATION = 36

JS = r"""JSON.stringify((()=>{
  const out=[];
  document.querySelectorAll('main > section, main > header, body > section').forEach(s=>{
    const sr=s.getBoundingClientRect();
    if(sr.height < 260) return;                       // not a band
    // A HERO IS NOT A SECTION HEADING. It is the page's opening claim, governed
    // by the claim step, and its subtitle sits deliberately close to it. Counting
    // heroes reported seven ISOLATION failures at 16-22px that were all correct
    // by design — the component being censused here is the one that says "a new
    // act starts", not the one that says "this is the page".
    if(/\bhero\b|lab-hero|pat-hero/.test((s.className+'')+' '+(s.id||''))) return;
    // the section's own heading: the first h2/h1 that is VISIBLE and >=24px
    // AN H1 IS THE PAGE TITLE, not a section heading. There is one per page and
    // it is governed by the claim step; its lede sits deliberately close to it,
    // which is correct proximity for a page opener. Counting it reported
    // /lab/plugin's h1.section-title as a tight section heading when its 16px
    // gap to .lab-lede is the intended pairing. The component censused here is
    // the h2-level "a new act starts" heading.
    let h=null;
    for(const c of s.querySelectorAll('h2')){
      const cs=getComputedStyle(c), q=c.getBoundingClientRect();
      if(cs.visibility==='hidden'||cs.display==='none') continue;
      if(q.width<=1||q.height<=1) continue;
      if(/visually-hidden|sr-only/.test(c.className+'')) continue;
      if(parseFloat(cs.fontSize)<24) continue;
      if(/card-title|rcpt-h|t-card-title/.test(c.className+'')) continue;
      // ARTIFACTS ARE NOT SECTION HEADINGS. A video plate, a claim ticket or a
      // product reconstruction reproduces someone else's typography and is
      // exempt by name in tools/heading-rank-check.py. Counting them here
      // reported "3 distinct signatures site-wide" including 7 at
      // 31px/400/Inter — which looked like v1.3.0 drift and was in fact
      // .vband h2 inside .vplate, correctly exempt. Two probes disagreed and
      // the narrower, spec-aware one was right.
      if(c.closest('.vslip,.vplate,.pass,.lug,.vband-film,[class^="plA-"],[class^="plF-"],'+
                   '[class^="plM-"],[class^="plO-"],[class^="plP-"],[class^="plV-"],'+
                   '[id^="recon-"]')) continue;
      h=c; break;
    }
    const name=(s.className+'').split(' ').slice(0,2).join('.')||s.id||s.tagName.toLowerCase();
    // A STATEMENT BAND is a pause, not a section. /lab carries bands whose whole
    // content is a 12px label plus one short principle ("A design opinion
    // becomes falsifiable the day it compiles"). That is a deliberate breath in
    // a long document and it identifies itself; giving it a heading would be
    // filling a form rather than designing. Recognised by shape: little text,
    // no sub-structure, no list or grid inside.
    const words = (s.textContent||'').trim().split(/\s+/).length;
    const hasStructure = !!s.querySelector('ul,ol,table,[class*="grid"],[class*="row"],[class*="card"]');
    const isStatementBand = words < 45 && !hasStructure;
    // A band that carries the page's H1 is headed by the page title itself —
    // excluding h1 from the component census must not then report its band as
    // headless. /lab/plugin is exactly that shape.
    const hasPageTitle = !!s.querySelector('h1');
    const isArtifactBand = hasPageTitle || /vband|film|recon/.test(name) ||
      !!s.querySelector('.vslip,.vplate,.pass,.lug,[id^="recon-"]') || isStatementBand;
    if(!h){ if(!isArtifactBand) out.push({sec:name, missing:true, h:Math.round(sr.height)}); return; }
    const cs=getComputedStyle(h), hr=h.getBoundingClientRect();
    // largest competing text in the same band
    // Measured against the PROSE it introduces, not against display-register
    // peers. A heading's job is to out-rank the text it heads; a 43px gold
    // figure or a 30px pull-quote is a different register, separated by colour
    // and family — that is this site's own grammar (numbers take the accent,
    // words take ink). Judging a heading against a figure produced nine
    // "failures" of which none was actionable: the only way to pass would have
    // been to shrink the data, which is the content the section exists for.
    let big=0, peak=0, peakTxt='';
    s.querySelectorAll('*').forEach(e=>{
      if(e===h||h.contains(e)) return;
      let own=false; for(const n of e.childNodes) if(n.nodeType===3&&n.textContent.trim().length>1){own=true;break;}
      if(!own) return;
      const c2=getComputedStyle(e); if(c2.visibility==='hidden') return;
      const r=e.getBoundingClientRect(); if(r.height<4) return;
      const sz=parseFloat(c2.fontSize);
      if(sz>peak){peak=sz;peakTxt=(e.textContent||'').trim().slice(0,20);}
      if(sz>24) return;                    // display register: a peer, not a rival
      big=Math.max(big, sz);});
    // air, counting only things that HORIZONTALLY OVERLAP the heading
    let above=1e9, below=1e9;
    s.querySelectorAll('*').forEach(e=>{
      if(e===h||h.contains(e)||e.contains(h)) return;
      const r=e.getBoundingClientRect(); if(r.height<4||r.width<4) return;
      const ov=Math.min(r.right,hr.right)-Math.max(r.left,hr.left);
      if(ov < Math.min(60, hr.width*0.25)) return;
      if(r.bottom<=hr.top+1) above=Math.min(above,hr.top-r.bottom);
      if(r.top>=hr.bottom-1) below=Math.min(below,r.top-hr.bottom);});
    out.push({sec:name, size:Math.round(parseFloat(cs.fontSize)), weight:cs.fontWeight,
      family:cs.fontFamily.split(',')[0].replace(/["']/g,''), colour:cs.color,
      track:cs.letterSpacing, left:Math.round(hr.left),
      big:Math.round(big), ratio:+(parseFloat(cs.fontSize)/(big||1)).toFixed(2),
      peak:Math.round(peak), peakTxt:peakTxt,
      airA:above>9000?null:Math.round(above), airB:below>9000?null:Math.round(below),
      txt:(h.textContent||'').trim().slice(0,30)});
  });
  return out;})())"""


def main():
    pages = sorted(p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
                   if not p.startswith(("prototypes", "partials", "book",
                                        "portfolio-sources", "__")))
    sigs = collections.Counter()
    lefts = collections.defaultdict(set)
    weak, missing, tight, licensed = [], [], [], []
    rows_by_page = {}
    with Browser() as br:
        br.viewport(1440, 1000)
        for p in pages:
            br.navigate(f"http://localhost:8000/{p}", settle=1.5)
            if br.eval_json("JSON.stringify([location.pathname])")[0].lstrip("/") != p:
                continue
            br.eval("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'))")
            br.pump(0.3)
            rows = br.eval_json(JS) or []
            rows_by_page[p] = rows
            for r in rows:
                if r.get("missing"):
                    missing.append((p, r)); continue
                # The contact close holds a documented display license
                # (DESIGN-SYSTEM-EMBER.md: "The contact close alone holds a
                # display license"). It is counted separately and PRINTED, not
                # folded into the component or quietly excused.
                if "close" in r["sec"]:
                    licensed.append((p, r)); continue
                sigs[(r["size"], r["weight"], r["family"], r["colour"], r["track"])] += 1
                lefts[p].add(r["left"])
                if r["ratio"] < DOMINANCE:
                    weak.append((p, r))
                if r["airB"] is not None and r["airB"] < ISOLATION:
                    tight.append((p, r))

    print(f"censused {len(rows_by_page)} pages\n")
    print(f"CONSISTENCY — distinct section-heading signatures site-wide: {len(sigs)}")
    for (sz, w, fam, col, tr), n in sigs.most_common():
        print(f"   {n:4} x  {sz}px / {w} / {fam} / {col} / tracking {tr}")
    for p, r in licensed:
        print(f"   licensed display: {p} .close at {r['size']}px "
              f"(DESIGN-SYSTEM-EMBER.md grants the contact close a display license)")
    print(f"\nDOMINANCE — headings not clearly largest in their band (<{DOMINANCE}x): {len(weak)}")
    for p, r in weak[:12]:
        print(f"   {p:40} {r['sec'][:14]:14} {r['size']}px vs {r['big']}px prose = "
              f"{r['ratio']}x  '{r['txt'][:24]}'")
        if r.get("peak", 0) > r["size"]:
            print(f"        (a {r['peak']}px display peer sits in this band: "
                  f"'{r['peakTxt']}' — different register, not counted)")
    print(f"\nISOLATION — less than {ISOLATION}px of air below: {len(tight)}")
    for p, r in tight[:12]:
        print(f"   {p:40} {r['sec'][:14]:14} air below {r['airB']}px")
    print(f"\nMISSING — bands taller than 260px with no visible section heading: {len(missing)}")
    for p, r in missing[:12]:
        print(f"   {p:40} {r['sec'][:20]:20} {r['h']}px tall")
    print(f"\nANCHOR — pages whose headings do not share one left edge:")
    moved = {p: sorted(v) for p, v in lefts.items() if len(v) > 1}
    for p, v in list(moved.items())[:10]:
        print(f"   {p:40} left edges {v}")
    print(f"   ({len(moved)} of {len(lefts)} pages)")
    bad = len(weak) + len(tight) + len(missing) + len(moved) + max(0, len(sigs) - 1)
    print(f"\n{bad} finding(s). A component has ONE signature, is dominant in its band, "
          f"has air, and lands in the same place every time.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
