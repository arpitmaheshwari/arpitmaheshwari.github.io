const { test, expect } = require('@playwright/test');
const { PAGES } = require('./pages');
const settle = require('./settle');

// PIXEL REGRESSION. Baselines live beside this file in visual.spec.js-snapshots/
// and are created/updated with:  npx playwright test --update-snapshots
//
// Canvas is MASKED, not captured: the homepage runs two particle systems seeded
// with Math.random(), so its pixels are different on every load by design. What
// is drawn inside a canvas is therefore NOT covered by this suite — stated here
// rather than left as a silent hole.
for (const p of PAGES) {
  for (const w of [390, 1440]) {
    test(`${p} @${w}`, async ({ page }) => {
      // 1400 not 900: a fixed-position nav on a page barely taller than the
      // viewport is the one case Playwright must special-case when stitching a
      // fullPage shot, and 404.html (1079px) failed 1 run in 4 on exactly that
      // element. A viewport taller than the shortest page removes the case.
      await page.setViewportSize({ width: w, height: 1400 });
      // assets/recon-live.js drives a ticking session clock, flash highlights
      // and a ghost cursor inside the .recon mockups on seven case studies. A
      // clock reading "session 0:01" can never match a baseline, and the six
      // failures it caused looked like flaky rendering rather than live
      // content. Blocking the one script renders those mockups in their static
      // initial state, which keeps them FULLY pixel-covered — strictly better
      // than masking the region and going blind to the artwork inside it.
      await page.route('**/recon-live.js*', r => r.abort());
      await page.goto('/' + p, { waitUntil: 'load' });
      await settle(page);
      await expect(page).toHaveScreenshot(`${p.replace(/[\/]/g, '__')}-${w}.png`, {
        fullPage: true,
        animations: 'disabled',
        caret: 'hide',
        mask: [
          page.locator('canvas'),
          // /lab/teardown.html prints the live cache-busting string
          // (styles.css?v=p78) as an example of hand-rolled versioning. That
          // string changes on EVERY css edit by design, so without this mask
          // the page fails the suite on every single change — 19 pixels, one
          // character, always a false alarm. Masking the string keeps the rest
          // of the page covered.
          page.locator('.td-inline', { hasText: /\?v=/ }),
        ],
        // 4, not 0 — see playwright.config.js for why. One pixel of gradient
        // antialiasing is not a change; 19 pixels (one character) still is.
        maxDiffPixels: 4,
      });
    });
  }
}
