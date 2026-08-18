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
      await page.setViewportSize({ width: w, height: 900 });
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
        mask: [page.locator('canvas')],
        maxDiffPixels: 0,
      });
    });
  }
}
