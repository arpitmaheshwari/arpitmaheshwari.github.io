// Bounded by design. Every previous attempt at this failed the same way: an
// unbounded run that produced no output for hours. Everything here has a
// ceiling, and progress prints per test.
const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: __dirname,
  timeout: 30_000,            // one page can never eat the run
  globalTimeout: 600_000,     // the whole suite dies at 10 minutes, always
  expect: { timeout: 10_000, toHaveScreenshot: { maxDiffPixels: 0, animations: 'disabled' } },
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
    baseURL: 'http://localhost:8000',
    screenshot: 'off',
    trace: 'off',
    viewport: { width: 1440, height: 900 },
  },
});
