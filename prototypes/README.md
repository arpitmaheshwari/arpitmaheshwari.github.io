# Prototypes — the design explorations, kept

Every rendered exploration from the hook/object work (2026-08-04), archived so future passes
can see what was tried, what was picked, and **why the rejected ones were rejected**. All files
are `noindex`, unlinked, and outside the sitemap. None is a shipping surface.

**Rules for this directory** (they mirror canon):
- These are ARCHIVES. Do not "fix" their copy to match current canon — a rewritten archive
  falsifies what was explored. Two files carry the retired term "Trust Layer" for exactly this
  reason and are allowlisted in `tools/canon-lint.py` with stated reasons.
- Never link these from a shipping page. To revive an idea, rebuild it on the live surface
  against current canon — don't resurrect the file.
- View any of them at `localhost:8000/prototypes/<file>`.

---

## The reference studies

| File | Study | Outcome |
|---|---|---|
| `paper-first.html` | ChatGPT-spec era: ink-slab + paper-field homepage, REAL canon content on a borrowed skin | **Rejected.** The spec's mechanics shipped separately (inline receipts, four exits); its invented facts (16 yrs / $120M / 8 products / logo wall) are quarantined in canon as POISON. |
| `light-direction.html` | anteelo.com study: warm-light skin, three devices (collage, plain-spoken hero, approachability band) on real content | **Parked** ("outcome is not very impressive"). Finding that survived: the three devices port into the dark identity; live gold `#D4A85E` fails on paper (needs `#7E5C1C`). |
| `dark-direction.html` | Controlled comparison: same devices, live dark identity | **Parked with the light one.** Finding: the cream act-peak IS the approachability band — the identity already owned the device. |

Branch twins: `origin/prototype/light-direction`, `origin/prototype/hook` hold the same files
with their full commit history.

## The energy explorations (2026-08-13) — "the layout is a monologue; bring the vibe"

Brief: sections, swim lanes and layout read as dull; reference shared was a Sahaj Applied
Research page. Four rounds, three rejections, one pick — the rejections are the record.

| File | Study | Outcome |
|---|---|---|
| *(branch `energy-redesign`, commit 5855b90 — index.html edits, no standalone file)* | **energy-1**: accent family + colour-coded lanes + indigo scene changes layered onto the existing skeleton | **Rejected** ("looks worse"). Finding: decorating the old skeleton is not energy; the layout itself was the problem. |
| `energy-v2.html` | **energy-2**: light-first reimagining — cream canvas, navy hero, solid-colour case mosaic, pill everything | **Rejected** ("a cheap copy of sahaj.ai"). Finding: it wore the reference's actual wardrobe (their navy/coral/mustard/pills/blobs). Take the *mechanics* of a reference, never its skin. |
| `energy-v3.html` | **energy-3**: "the evidence desk" — the site's own printed-ephemera props (receipt, QC slip, stamps, manila case files) promoted to architecture | **Rejected** ("tunnelled vision — go back to the drafting board"). Finding: amplifying what the site already was is still one idea deep; exploration has to precede execution. |
| `drafting-board.html` | **energy-4a**: four from-scratch directions side by side — A Broadsheet (typographic violence) · B Signal (acid voltage, live instrument) · C Gallery (monumental plates) · D Ember (heat: gradient fields, angled seams) | **Arpit picked D**, with web accessibility as a hard requirement. |
| `energy-d-full.html` | **energy-4b**: EMBER, the full homepage in direction D — every section, WCAG 2.2 AA built in (palette pre-computed ≥7:1, focus rings, reduced-motion, skip link, landmarks) | **Built and verified** (contrast 0 failures calibrated, real-viewport 375px check). Decision on porting vs. keeping production: pending. |

Process lesson this round burned in: one idea per attempt is tunnel vision by process —
the drafting board (plural, genuinely distinct directions, rendered) comes FIRST.


## The hook concepts (bakery-box mechanism: the frame is witty, the real work completes it)

| File | Concept | Outcome |
|---|---|---|
| `hook-a.html` | "You are the human in the loop" — judge a confident score about Arpit | **Rejected** — "the approach was not original". |
| `hook-b.html` | The till receipt, static | **SHIPPED** — proof act right rail (the TOTAL of the four chips) + download. |
| `hook-c.html` | The die-cut window — lifted dark sheet over a live A/R/I demo | Rejected — most literal, weakest. |
| `hook-d.html` | The boarding pass | **SHIPPED** — contact CTA, as "Loop Air" (this archive predates the rename). |
| `hook-e.html` | The garment inspection slip "№ 15" | **SHIPPED** — errata coda, unstamped… |
| `hook-f.html` | The nutrition label "Candidate Facts" | **SHIPPED** — spec card under the bio. |
| `hook-g.html` | The threshold slider — hold the actual design object | **Rejected** — "hard to understand if you don't have time to read". |
| `hook-h.html` | …with the stamp made performable (hold → HUMAN PASSED) | **SHIPPED** — merged into the errata slip. |
| `hook-i.html` | The receipt printer (print → tear → keep a .txt) | Superseded by static B: the theatre was cut, the download survived on the receipt's footer. |

## The option sheets (decides-by-seeing rounds)

| File | Round | Outcome |
|---|---|---|
| `process-options.html` | Process object, round two: pre-ship checklist / traveler / lab notebook (round one — betting slip / passport / kill board — was rejected whole: it showed process *outcomes*, not a process-oriented person) | **Checklist SHIPPED** on the process rail. |
| `section-options.html` | Testimonials (correspondence cards / reference dossier) + patterns act (seed packets / specimen board) | Neither testimonial direction shipped — Arpit kept the quote cards and chose an **envelope bundle** for the left void. Pattern statics superseded by the working demo. |
| `pattern-demos.html` | Three WORKING interactive candidates: capability contract / A-R-I sorter / reversibility undo | **Demo 1 (capability contract) SHIPPED** on the patterns act rail. Sorter + reversibility remain playable here — strong candidates for pattern pages later. |

## Where the shipped versions live

`index.html`: receipt (proof act) · Candidate Facts (bio) · contract demo (patterns act) ·
slip + stamp (errata) · specimen tag (lab) · pre-ship checklist (process) · envelope bundle
(testimonials) · Loop Air pass (contact). Components in `styles.css` under
"Hook objects (2026-08-04)"; layout grammar: `.editorial--rail` / `.idea-zone` / `.proof-zone`.
