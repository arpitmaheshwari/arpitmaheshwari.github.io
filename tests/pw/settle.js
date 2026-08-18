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

  // TWO SOURCES OF NON-DETERMINISM IN THE NAV, both fixed here.
  //
  // 1. backdrop-filter: blur(10px). GPU blur is not reproducible run to run —
  //    this was 1,899 pixels across the nav bar failing 1 run in 3, on the one
  //    page short enough for the nav to dominate the diff. The BLUR EFFECT is
  //    therefore not pixel-verified; everything it sits on top of still is.
  // 2. #nav gains .scrolled past 60px, changing background, padding and
  //    border. Pinned to the un-scrolled state — what a visitor sees on
  //    arrival, and identical on every run.
  await page.addStyleTag({ content: `
    *, *::before, *::after { backdrop-filter: none !important;
                             -webkit-backdrop-filter: none !important; }
    #nav.scrolled { padding: 24px 48px !important; border-bottom: 0 !important; }
  `});
  await page.evaluate(() => {
    const nav = document.getElementById('nav');
    if (!nav) return;
    nav.classList.remove('scrolled');
    const cl = nav.classList, add = cl.add.bind(cl), tog = cl.toggle.bind(cl);
    cl.add = (...a) => add(...a.filter(x => x !== 'scrolled'));
    cl.toggle = (n, f) => (n === 'scrolled' ? false : tog(n, f));
  });
};
