# Survey C — field notes from 97 domains (corpus_part_ac, g–l)

Method: headless Chrome at 1440x900, ~10s per site plus a second 15s pass with a scroll
nudge for the 47 sites caught behind preloaders. Every verdict below is from looking at the
rendered pixels, not the markup.

## 1. Tallies

- **97 domains → 83 loaded, 14 no-load** (DNS/timeouts: 11; bot walls — Cloudflare on
  johannadarrieta.com, Vercel checkpoint on leoleo.studio; one dead Vercel deploy: halodhimas.com).
- **Ground (of the 86 rendered):** dark 46 · light 33 · flat saturated color field 7 (heurebleue
  cobalt, huncwot red, jameswalsh brick, letude red-orange, landonorris acid yellow, heydaystudio
  acid lime, livesurface salmon). Dark is the default costume of this corpus.
- **Type voice:** quiet 40 · grotesk-caps 21 · mixed 9 · mono 8 · giant-serif 5.
- **Verdicts: ORIGINAL 13 · solid 59 · template 11.**
- **~20 of 83 loaded sites showed a blank or preloader hero even after 15s + scroll** — the
  immersive-WebGL tier (igloo.inc, journey.zajno, joseph-san, karocrafts, landonorris…) locks its
  design behind a loader; unjudgeable headless, logged as solid.

**Most-repeated template patterns, named precisely:**
1. **The Linear costume** — near-black ground, centered grotesk claim, glowing product panel
   below, Sign-up pill top-right (linear.app itself, keywordsai.co, hypercard.com, heyorbi.com,
   joincobalt.com, langbase.com, lapz.io). The single most-cloned layout in the corpus.
2. **Gradient-corner + email-capture waitlist hero** (heyorbi, joincobalt).
3. **The big intro sentence** — "Hi, I'm X — [role] for [audience]" set huge in a grotesk, with
   inline logo pills (kysondana, kevinbhagat, halfpastnine). Competent, interchangeable.
4. **Graph-paper/blueprint grid ground** under a SaaS hero (hex.tech, langbase).
5. **Dark-void portfolio with a preloader percentage** — the loader is now itself a convention
   (numbered counters, "turn on sound", branded loader puns).
6. **Dither/halftone texture** as instant craft-signal (hyperstudio's dot-matrix map,
   several grain overlays) — 2025's noise overlay.

## 2. ORIGINAL standouts

- **gsap.com** — The hero headline animates its own glyphs: letters of "Animate anything"
  swap into flower, lightning and squiggle icons mid-word. The product (an animation library) is
  demonstrated by the typography itself, not described by it.
- **la-caisse-jeu-simulation.com** — A pension fund explained as a bitmap-type
  choose-your-own-adventure game ("La Caisse dont vous êtes le héros"). Institutional finance
  content wearing 8-bit game clothes; the tone inversion is the design.
- **kaisermann.me** — Personal site as an old CRT television: scanlines, chromatic fringe,
  "CHANNEL 00", a date stamp, pixel mono type. One metaphor carried through every pixel.
- **itsmarga.me** — Portfolio as an operating-system desktop: draggable window cards
  carry the copy while a hand-drawn dog chases a fly across the wallpaper. Software-shaped
  structure softened by doodle warmth.
- **inkfishnyc.com** — The work index is a DOS terminal directory: seventeen numbered rows
  (TOYOTA → [01] RAV4 THE WALL) with block-glyph progress bars, "ONLY THE STRONG EVOLVE" as
  a corner motto. An agency reel with zero images on load — pure mono text as spectacle.
- **hugeinc.com** — The entire hero is one giant inflated letter H rendered as pink puffer
  fabric with silver seams. A global agency spending its homepage on a single tactile object.
- **letude.group** — Swiss-poster energy: red-orange field, massive black caps L'ÉTUDE,
  blue rotating badge glyphs orbiting, and a sentence whose words swap live underneath.
  Print-poster rules executed with web motion.
- **leanrada.com** — A software engineer's page built from dithered pixels: a gradient orb
  ringed with circular type, typewriter mono copy, pixel-art glasses and teapot. The craft IS
  the argument that he can build things.
- **guruduttperi.com** — A musician's discography as a drag-to-explore masonry wall of 82
  release artworks with a floating player dock. Navigation replaced by wandering.
- **lafour.com** — Film-production chrome as UI: a running timecode sits inside the nav,
  and full-bleed campaign footage carries mono metadata rows (client × collaborator, format).
  The site pretends to be the edit suite the work was cut in.
- **lisovskiy.work** — A 3D floppy disk labeled "MY BEST IDEAS" floats beside an editorial
  column of single words (Web / Design / Identity / Impact). One nostalgic object plus one
  typographic list — nothing else needed.
- **heyvalentin.club** — The intro sentence is assembled from colored sticker-tags
  ("HEY! I'M [→VALENTIN], A [→PRODUCT DESIGNER]") over doodle illustration on black. The CV
  content everyone has, physicalized into labels you want to peel.
- **kreatives.co** — An orange serif sentence where small photographs and emoji sit inline as
  words ("We are a {c}reative studio → pushing the world forward with strategy [photo] design
  [photo]"). Media grammatically embedded in type.

## 3. What separates original from competent

The originals commit to one governing metaphor — a TV channel, an OS desktop, a terminal
directory, a film slate, a game cartridge — and let it dictate every component, while the
competent sites assemble proven parts (dark ground, big grotesk sentence, product panel,
grain) that each pass review and together belong to nobody. Their signature move lives in the
*structure* — what the nav, the index, or the headline IS — not in a decorative layer applied
over a standard structure, which is why it can't be lifted off as a skin. And they spend
their originality budget in exactly one place while keeping everything else disciplined and
quiet: gsap's page is a plain dark SaaS layout except that the headline performs; lafour is a
normal reel site except the chrome tells the time in timecode.
