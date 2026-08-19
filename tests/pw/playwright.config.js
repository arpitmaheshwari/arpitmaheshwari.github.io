// Bounded by design. Every previous attempt at this failed the same way: an
// unbounded run that produced no output for hours. Everything here has a
// ceiling, and progress prints per test.
const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: __dirname,
  timeout: 30_000,            // one page can never eat the run
  globalTimeout: 600_000,     // the whole suite dies at 10 minutes, always
  expect: {
    timeout: 10_000,
    // maxDiffPixels 4, not 0. Zero is stricter than the renderer is stable:
    // /case-studies/o2 differed by exactly ONE pixel, at one coordinate, on
    // three consecutive runs — antialiasing on a gradient edge, not a change.
    // The smallest REAL difference this suite has caught was 19px (a single
    // character in a version string), so 4 keeps every meaningful change
    // visible while removing a permanent false alarm.
    toHaveScreenshot: { maxDiffPixels: 4, animations: 'disabled' },
  },
  // One retry. A genuine visual regression fails again on retry, so this
  // cannot hide a real change — but a screenshot taken while the machine is
  // saturated occasionally differs by a handful of pixels, and that must be
  // reported as "flaky", not as a regression. Observed: 1-2 of 80 under load,
  // 0 of 80 on an idle machine across three consecutive runs.
  retries: 1,
  fullyParallel: true,
  workers: 6,
  reporter: [['line']],       // one line per test as it happens, not at the end
  use: {
    // PW_BASE lets the same suite run against production:
    //   PW_BASE=https://arpitmaheshwari.com npx playwright test
    // Baselines were captured from localhost, so a production run is also a
    // DEPLOY CHECK: if the bytes GitHub Pages serves differ from the bytes
    // here, the pixels say so.
    baseURL: process.env.PW_BASE || 'http://localhost:8000',
    screenshot: 'off',
    trace: 'off',
    viewport: { width: 1440, height: 900 },
  },
});
