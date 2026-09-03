/* A "there is more below" hint for the mobile book page.
 *
 * .bk-m-page is overflow-y:auto, so on a phone a long page scrolls INSIDE the page box.
 * Measured 2026-09-03 at 390px: 10 of the book's 46 pages carry more content than the box,
 * spilling between 37px and 286px. Nothing said so. A reader sees what looks like the end of
 * the page and taps "next", and the rest is simply never read — content that is present,
 * reachable, and invisible, which is the failure mode no property gate can see.
 *
 * React replaces the page element on every flip, so this watches the stable .bk-m-stage
 * ancestor rather than binding to a page that is about to be thrown away.
 */
(function () {
  'use strict';
  var THRESHOLD = 8;               // ignore sub-pixel and rounding noise

  function update(page) {
    if (!page) return;
    var more = page.scrollHeight - page.scrollTop - page.clientHeight > THRESHOLD;
    // The flag goes on the STAGE, not the page: the fade is painted by the stage, which is a
    // stable ancestor that survives the flip and is not itself the scrolling box.
    var stage = page.closest('.bk-m-stage');
    if (!stage) return;
    if (more) stage.setAttribute('data-more', '1');
    else stage.removeAttribute('data-more');
  }

  function current() { return document.querySelector('.bk-m-page'); }

  function start() {
    var stage = document.querySelector('.bk-m-stage');
    if (!stage || stage.dataset.hintBound) return;
    stage.dataset.hintBound = '1';

    // scroll happens on the page element, which changes — delegate from the stage
    stage.addEventListener('scroll', function (e) {
      if (e.target && e.target.classList && e.target.classList.contains('bk-m-page')) update(e.target);
    }, true);

    var mo = new MutationObserver(function () { update(current()); });
    mo.observe(stage, { childList: true, subtree: true });

    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function () { update(current()); });
      ro.observe(stage);
    }
    window.addEventListener('resize', function () { update(current()); });
    update(current());
  }

  // The stage is rendered by React, so it may not exist yet at DOMContentLoaded.
  function waitFor() {
    if (document.querySelector('.bk-m-stage')) { start(); return; }
    var tries = 0;
    var iv = setInterval(function () {
      if (document.querySelector('.bk-m-stage') || ++tries > 60) { clearInterval(iv); start(); }
    }, 100);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', waitFor);
  else waitFor();
})();
