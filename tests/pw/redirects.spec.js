const { test, expect } = require('@playwright/test');
const { STUBS } = require('./pages');
// The stubs are excluded from the pixel suite because they render nothing of
// their own. They still have a job, and it is worth asserting: land on the
// right page. A stub that silently stops forwarding is a dead link that looks
// alive.
const TARGETS = {
  'case-studies/talon.html': '/case-studies/adtech.html',
  'lab/hitl.html': '/lab/loop.html',
  'lab/trustlayer.html': '/lab/loop.html',
};
for (const s of STUBS) {
  test(`${s} forwards`, async ({ page }) => {
    await page.goto('/' + s, { waitUntil: 'load' });
    await page.waitForURL(u => !u.pathname.endsWith(s.split('/').pop()), { timeout: 8000 });
    expect(new URL(page.url()).pathname).toBe(TARGETS[s]);
  });
}
