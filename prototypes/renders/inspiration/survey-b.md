# Field survey — shard B (97 domains, c–g)

Method: headless Chrome at 1440x900, JPEG capture per site; blank/JS-gated pages got a second pass with 8s settle plus a scroll nudge. Every verdict is from looking at the rendered pixels.

## 1. Tallies

- 97 domains attempted; **72 loaded** to something assessable, **25 did not** (12 never painted past a flat ground even on retry, 6 loader/counter screens that never resolved, 3 hard timeouts — cursor.com, frame.io/v4, danilosierra — plus a 404, a parked domain, a TLS failure, and a bot-check interstitial).
- Ground (of 72 loaded): **dark 38 (53%), light 27 (37%), saturated single color 7 (10%)**. Dark-by-default is now the house style of studio/portfolio sites.
- Type voice: quiet 31, mixed grotesk+serif 16, grotesk-caps 14, giant-serif 8, mono 3.
- Motion (visible in a static capture): none 39, kinetic-type 12, canvas/WebGL 9, 3D object 9, grain/film 3.
- Verdict: **ORIGINAL 14, solid 46, template 12**.

**Most-repeated template patterns, named precisely:**
1. **The centered-claim SaaS formula** — pill badge above a centered two-line grotesk claim, two rounded CTAs, star-rating row, logo wall, cookie banner (eleken.co, fora.so, coreframework.com, eleveight.supply, droplette.app, framer.studio).
2. **The dark-portfolio intro sentence** — near-black ground, giant gray "I'm X, a product designer specialized in..." with a live city clock/temperature widget and an awards tab (gokulkrishnan.com is the canonical instance).
3. **The italic-serif pivot word** — a grotesk headline that swaps to swash italic serif for one emotive word ("web *technologies*", "полного *цикла*", "for *B2B* brands", "*forward-thinking*"). Four independent sites in this shard alone (funkhaus, cp-agency, griflan, designmill); it has crossed from move to mannerism.
4. **Loader-as-hero counter** — black or white void with only a percentage/counter composed into a corner (federicopian, gianlucagradogna, gregorylalle, eseagency, des.obys, drone.riotters). So common that six sites in one shard greet a first visit with arithmetic.
5. **Design-tool cosplay** — selection handles, crosshairs, or registration marks drawn around real headlines (framer.university's selected-text frame; eduardbodak and davidanthonychenault use press marks far more deliberately).

## 2. ORIGINAL standouts (14)

- **cyphr.studio** — The hero photograph is sliced into a descending comb of vertical strips, a staircase mask that turns one concert image into rhythm; a condensed caps claim runs the full bottom edge like a chyron. The grid itself is the signature, not a layout for other signatures.
- **companypolicy.studio** — Portfolio as poster wall: risograph-textured run-club posters in cobalt and red sit in a strict three-column rhythm on black, and a live "CURRENTLY CREATING:" ticker crawls along the bottom edge. The work is the interface; the studio never describes itself.
- **davidanthonychenault.com** — A colossal three-line name is stamped over a glitch-scanned self-portrait with a red cross overlay and mirrored UV botanicals, with registration x-marks scattered like a proof sheet. The corner motto "DECLARE MUTINY ON THE MONOTONOUS" is the design brief, executed.
- **designbomb.it** — A festival site that behaves like its own gig poster: italic ultra-black "DESIGN BOMB!!!" at viewport scale, a crooked sticker-stack date badge, googly-eye mascot, hot-pink TICKET pill. Maximalist, but every element is one voice.
- **dionpieters.dev** — Alarm-orange field, mint condensed caps squeezed edge-to-edge, and a giant black line-art smiley half-buried behind the name. Two colors, one glyph, total recall; the footer metadata is set like a museum label.
- **dottxt.ai** — An AI-infrastructure company styled as a terminal zine: bitmap pixel display type ("NO BAD OUTPUTS"), numbered mono eyebrows, a dithered noise panel, and a retro window-chrome frame around a live CLI demo. Aesthetic and product argument are the same thing.
- **drxlr.com** — The logotype is set so large that only "Dre" fits the viewport, cropped mid-glyph, with a tiny pink underlined DREXLER floating mid-left and the footnote "A few skilled humans doing the work of many.™". Confidence expressed as scale plus restraint everywhere else.
- **eduardbodak.com** — Colossal condensed caps with a hard CSS reflection under the baseline, crosshair registration marks scattered like a press sheet, and a mono price chip ("PRO MONAT €3.245,-") doing the sales pitch. Print-production furniture becomes web ornament with a purpose.
- **electronicmaterialsoffice.com** — Product noir: a keyboard barely emerges from true black under a roman serif "Altar II / Mechanical miracle." and a glowing red Reserve pill with a struck-through price. Luxury-watch cinematography applied to a mechanical keyboard.
- **erinfeeproductions.com** — The whole viewport is the logotype: a brick-red field with a giant white rounded-grid EFP monogram cropped at the top-left. No claim, no nav bar as furniture — identity at architectural scale.
- **evanfasquelle.com** — Portfolio as trading-card binder: a tilted grid of card backs fans behind "TRADING *Cards* PORTFOLIO" (caps with a script interleave), and even the loader percentage is set in serif. A collector's metaphor carried through every element.
- **fernandopuente.es** — The entire site is one oxblood-maroon serif index sheet: five columns of projects, services, clients, and awards over a giant indented serif paragraph, with a swallow mark as the only image. Reads like the colophon of a fine book, works like a resume.
- **festina.vc** — A VC fund as still-life: an anchor coin, one gray sentence with inline founder-avatar chips, and giant grainy 3D squiggle sculptures rising from below the fold. It replaces the entire "thesis / portfolio / team" formula with three objects.
- **fiddle.digital** — The UI is chopped into floating rounded slabs — logo slab, nav slab, a blue 3D spring film — with a katakana sub-brand, mono annotations, and a giant page-turn arrow glyph parked in the empty quarter. The negative space between slabs is designed, not left over.

## 3. What separates original from competent

The originals commit to one concrete metaphor drawn from outside web design — a trading-card binder, a press sheet, a gig poster, a terminal zine, a book's colophon — and let that single idea dictate type, color, layout, and even the loader, whereas the competent sites assemble the same proven parts (centered claim, pill CTA, italic pivot word, counter-loader) in tasteful proportion. Originality here is almost always structural rather than decorative: the signature move lives in the grid itself (a comb-sliced photo, a logotype cropped by the viewport, a poster wall as navigation), so it cannot be extracted as a reusable component the way a gradient or a font pairing can. And the originals accept a cost the templates refuse — cropped glyphs, empty quarters, a name you must scroll to finish reading — which is exactly the felt risk that makes a page read as authored by a person instead of assembled from a kit.
