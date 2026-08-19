// Everything the hand-rolled harness learned the hard way, in one helper.
module.exports = async function settle(page) {
  // Never let a test run show up in Arpit's own numbers. Against production
  // this suite loads ~78 pages; without this they would land in GA and
  // Clarity as real traffic and quietly corrupt the attention data the site
  // is built to measure. Blocked on every run, local included, so the local
  // and production renders stay comparable.
  await page.route(/googletagmanager|google-analytics|clarity\.ms|doubleclick/, r => r.abort());

  // fonts, with a ceiling — a stalled font must not hang the test
  await Promise.race([
    page.evaluate(() => document.fonts.ready),
    page.waitForTimeout(4000),
  ]);
  // WAIT FOR THE DOM TO STOP MOVING. /book/ is a React view that mounts its
  // content asynchronously, and it once differed from its baseline by 744,000
  // pixels on one run and 71 on the retry — a capture taken mid-mount. Polling
  // until the node count holds steady covers any async render, not just this
  // one, and costs ~150ms on a static page.
  // STABLE IS NOT THE SAME AS LOADED. The first version of this waited for the
  // node count to stop changing — and a React view that has not begun mounting
  // has a perfectly stable node count, so it sailed through and photographed a
  // BLANK PAGE. /book/ failed 2 runs in 6 that way, differing by 744,000
  // pixels, and the capture was simply empty.
  // So: require real content to exist BEFORE calling it settled, and throw
  // rather than quietly shoot an empty page.
  await page.evaluate(async () => {
    const size = () => document.body.innerText.trim().length +
                       document.getElementsByTagName('*').length;
    let last = -1, stable = 0, spins = 0;
    while (spins++ < 100) {
      await new Promise(r => setTimeout(r, 50));
      const n = size();
      // a rendered page on this site is never this small
      // TEN consecutive readings (500ms), not three. Measured on /book/: the
      // content size sits at ~518 for ~360ms while React mounts, then jumps to
      // ~864. Three readings is 150ms — comfortably inside that plateau, so
      // the guard certified a half-mounted page and the capture came out
      // blank. The wait has to outlast the plateau, not merely observe one.
      if (n > 400) { stable = (n === last) ? stable + 1 : 0; if (stable >= 10) return; }
      last = n;
    }
    throw new Error('page never rendered content: size=' + size());
  });

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
