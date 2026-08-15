---
name: ship-gates
description: The ten self-calibrating checks that decide whether a change may ship on arpitmaheshwari.com — what each one catches, the real defect that caused it to exist, and the discipline that makes a green result mean anything. Load before claiming any work is done, before trusting a passing check, or when building quality gates for another project.
---

# Ship gates — and why a green check is usually worth less than you think

Ten checks run before anything reaches production here. Each exists because a specific defect got
through everything that existed at the time. That history matters more than the list: it tells you
what *kind* of thing gates miss.

## The discipline first

**A check you have not watched fail is not evidence.** Every gate here plants a defect, requires
the check to go red, then removes it. Three separate times a check reported "clean" while
measuring nothing at all — wrong selector, zero elements found, vacuous pass. A gate that cannot
fail is theatre.

**An impossible reading indicts the instrument, not the product.** Contrast of exactly 1.00:1.
A 0-byte diff on a file you just edited. Width 0 on a visible element. Every one of those is your
tool breaking. Chase it to root cause before you "fix" the page — and expect that roughly most of
what an automated audit reports is instrument error or a standards-exempt case. The verification
step is where the value is, not the scan.

**Green does not mean correct.** These gates check whether a page is *right*; almost none check
whether it is *structured*, and none check whether it is *good*. A layout can pass contrast,
spacing and overflow and still be badly composed. Look at the rendered page.

## The ten

| Gate | Catches | Born from |
|---|---|---|
| `canon-lint` | banned or stale facts, invented metrics | prose drifting from the locked source of truth |
| `case-sync-check` | the long-form and short-form telling the same story differently | two surfaces disagreeing about the same project |
| `overflow-sweep` | content escaping the viewport | text running off-screen on real pages |
| `balance-check` | lopsided whitespace — a reading column not centred in its space | a 457px void down one side that shipped on six pages |
| `contrast-audit` | text below WCAG, measured from **rendered pixels** | style-based checks lying about gradients |
| `artifact-legibility-check` | invisible text *inside* inlined SVG diagrams | cream-on-cream text that reached production |
| `asset-load-check` | images that do not actually paint | an invalid SVG that every text-based check passed |
| `inline-style-check` | a repeated component still unnamed; off-grid spacing | one mono label spelled 16 different ways |
| `theme-remnant-check` | colours from a retired palette still painting | a half-finished theme port |
| `css-version-check` | a stylesheet edited without bumping its cache version | the author's browser serving an older file than disk |

## Running them

```bash
python3 tools/canon-lint.py            # facts
python3 tools/case-sync-check.py       # cross-surface agreement
python3 tools/overflow-sweep.py        # layout escape (slow: renders every page)
python3 tools/balance-check.py         # whitespace symmetry (slow)
python3 tools/artifact-legibility-check.py
python3 tools/inline-style-check.py
python3 tools/css-version-check.py
```

A local server must be running for the rendering gates: `python3 -m http.server 8000`.
Most are also wired into `.githooks/pre-push`, so a push runs them.

## Writing a gate that is worth having

1. **State what it CANNOT see**, in its own output. A gate that reports only its verdict teaches
   the reader to over-trust it.
2. **Self-calibrate on every run.** Plant, require red, revert. Print the calibration result above
   the verdict.
3. **Refuse to report on zero measurements.** If the probe found nothing, that is a failure, not a
   pass.
4. **Measure the rendered result**, not the source. Markup being correct proves nothing about what
   a browser painted — and a browser can serve a cached stylesheet that contradicts your file.
5. **Prefer the browser's own answer over your inference.** `document.scrollingElement` beats
   sniffing overflow properties; `getComputedStyle` beats reading the CSS.

## What none of this covers

Whether the writing is any good. Whether the layout is well composed. Whether the claim is honest.
Gates protect the floor; they never raise the ceiling.
