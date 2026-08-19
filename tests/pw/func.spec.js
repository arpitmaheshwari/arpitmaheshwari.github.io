const { test, expect } = require('@playwright/test');

test('mobile menu toggle works', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto('/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  const btn = page.locator('#menuToggle');
  const before = await page.locator('.nav-links').evaluate(e => e.classList.contains('nav-open'));
  await btn.click();
  await page.waitForTimeout(400);
  const after = await page.locator('.nav-links').evaluate(e => e.classList.contains('nav-open'));
  console.log(`MENU: before=${before} after=${after} -> ${before!==after ? 'WORKS' : 'BROKEN'}`);
});

test('dyslexia toggle works', async ({ page }) => {
  await page.goto('/index.html', { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  const t = page.locator('#dyslexiaToggle');
  if (!await t.count()) { console.log('DYSLEXIA: control not present'); return; }
  const before = await page.evaluate(() => document.body.classList.contains('dyslexia-mode'));
  await t.click(); await page.waitForTimeout(400);
  const after = await page.evaluate(() => document.body.classList.contains('dyslexia-mode'));
  console.log(`DYSLEXIA: before=${before} after=${after} -> ${before!==after ? 'WORKS' : 'BROKEN'}`);
});

test('fit check runs', async ({ page }) => {
  await page.goto('/fit/', { waitUntil: 'load' });
  await page.waitForTimeout(3000);
  const sample = page.locator('#fit-sample');
  if (!await sample.count()) { console.log('FIT: sample control missing'); return; }
  await sample.click(); await page.waitForTimeout(600);
  const filled = await page.locator('#fit-jd').inputValue();
  await page.locator('button[type=submit]').click();
  await page.waitForTimeout(1200);
  const shown = await page.locator('#fit-results').evaluate(e => !e.hasAttribute('hidden'));
  console.log(`FIT: sample filled=${filled.length>50} results shown=${shown} -> ${filled.length>50 && shown ? 'WORKS' : 'BROKEN'}`);
});

test('book renders its content', async ({ page }) => {
  await page.goto('/book/', { waitUntil: 'load' });
  await page.waitForTimeout(3500);
  const txt = await page.evaluate(() => document.body.innerText.trim().length);
  console.log(`BOOK: ${txt} chars of text -> ${txt > 200 ? 'RENDERS' : 'BLANK'}`);
});
