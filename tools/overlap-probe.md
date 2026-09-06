# overlap-probe.js — TRIAGE AID, not a gate

Finds pairs of text elements whose *painted lines* cross. Run it by pasting the
JS into a page context (or via cdp `eval_json`), at each width you care about.

## Why it is not in the gate suite
It reports one geometric overlap that is **invisible**: on the case pages at
≤768px the restacked before/after table leaves its desktop column header
(`<th>The advertiser asks`) underneath the stacked card. Measured with a pixel
sample inside that header's own box: **0 painted pixels**. Nothing a reader can
see is obscured, so failing a build over it would train everyone to ignore the
gate. To become a gate it needs a pixel-confirmation step — report an overlap
only when BOTH elements' ink is actually painted.

## What it took to make its output trustworthy (three revisions)
1. **Union boxes lie.** An inline element that wraps returns one box spanning
   every line it touches, which overlaps its neighbours on those lines. First
   run: 4 pages of phantom defects, including "pattern library" × "paste the
   role into the fit check" — two links in the same sentence.
2. **Per-line rects via `Range`.** One rect per rendered line over the element's
   own text nodes. That cut 4 pages to 1 candidate.
3. **Pixels settle it.** The surviving candidate was geometric only.

## What it found that mattered
Nothing, across 8 pages × 4 widths (390/768/1024/1440) — the site has no visible
crossing text. The one real overlap this session was inside an SVG (a gauge
needle passing through its own label, 2.11:1) and no DOM-rect tool could have
seen it: it was found by rendering the figure and looking at it.
