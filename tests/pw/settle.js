// Everything the hand-rolled harness learned the hard way, in one helper.
module.exports = async function settle(page) {
  // fonts, with a ceiling — a stalled font must not hang the test
  await Promise.race([
    page.evaluate(() => document.fonts.ready),
    page.waitForTimeout(4000),
  ]);
  // reveal-on-scroll: walk the page so every IntersectionObserver fires, then
  // wait for the revealed count to STOP MOVING. A fixed sleep here produced a
  // 1-in-3 flake that was always the identical pixel count — the tell that it
  // was a race, not noise.
  await page.evaluate(async () => {
    const h = document.body.scrollHeight;
    for (let y = 0; y < h; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 12)); }
    scrollTo(0, 0);
    const count = () => document.querySelectorAll('.visible,[data-viewed]').length;
    let last = -1, stable = 0, spins = 0;
    while (stable < 3 && spins++ < 60) {
      await new Promise(r => setTimeout(r, 40));
      const c = count();
      stable = (c === last) ? stable + 1 : 0;
      last = c;
    }
  });
};
