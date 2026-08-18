# Regression suite

Two questions, answered by one tool (Playwright, MIT).

    npx playwright test                      # everything
    npx playwright test visual.spec.js       # pixels only
    npx playwright test --update-snapshots   # accept the current render as correct
    npx playwright show-report               # side-by-side diffs after a failure

## What it covers

`visual.spec.js`  every page (40) at 390 and 1440, full height, compared pixel
for pixel against a stored baseline. 80 tests, ~35 seconds.

`redirects.spec.js`  the three forwarding stubs land on the right page. They
render nothing themselves, so they are excluded from the pixel suite — but a
stub that stops forwarding is a dead link that looks alive.

## What it deliberately does NOT cover — read this before trusting a green run

* **Anything behind interaction.** Hover, focus, open menus, driven widgets.
  On-load render only.
* **The inside of a `<canvas>`.** The homepage runs two particle systems seeded
  with `Math.random()`; they are masked. Their box is covered, their drawing is
  not.
* **Live reconstruction behaviour.** `assets/recon-live.js` is blocked during
  tests — it drives a ticking session clock, flash highlights and a ghost
  cursor. The mockups are captured in their static initial state, which is
  fully covered; the animation is not.

## Why the baselines are committed

They are the contract. A refactor is correct when these images do not change.
Regenerate deliberately with `--update-snapshots`, never to make a red run go
green.
