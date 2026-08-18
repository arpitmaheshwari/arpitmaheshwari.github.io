const { test, expect } = require('@playwright/test');
const path = require('path');
const { STUBS, stubTarget } = require('./pages');

// Stubs render nothing of their own, so they are excluded from the pixel
// suite. They still have one job worth asserting: land where they claim to.
// A stub that stops forwarding is a dead link that looks alive — and these
// URLs are published in the sitemap and linked from the portfolio PDF.
for (const s of STUBS) {
  test(`${s} forwards where it says it does`, async ({ page }) => {
    const declared = stubTarget(s);
    expect(declared, `${s} has no refresh target`).toBeTruthy();
    // resolve relative targets against the stub's own directory
    const expected = new URL(declared, 'http://localhost:8000/' + s).pathname;
    await page.goto('/' + s, { waitUntil: 'load' });
    await page.waitForURL(u => u.pathname === expected, { timeout: 8000 });
    expect(new URL(page.url()).pathname).toBe(expected);
  });
}
