/* While the mobile menu is open, the page behind it is inert.
 *
 * Found 2026-09-03 by tabbing with the menu open at 390px: focus walked straight out of the
 * menu into "Book the 30-min call", "Send me the role" and "See selected work" — content the
 * open overlay was covering. A keyboard or screen-reader user was being offered controls they
 * could not see, in an order that made no sense.
 *
 * The menu-open class is toggled by an inline handler duplicated across 37 pages, so this
 * watches for the class rather than editing 37 copies of the same script. It owns exactly one
 * concern: everything that is not the navigation stops being reachable while the menu is up.
 */
(function () {
  'use strict';
  var OPEN = 'nav-open';

  function outside(menu) {
    // Siblings of the nav's own banner: main, footer, and any stray top-level content.
    var banner = menu.closest('[role="banner"]') || menu.closest('nav') || menu;
    return [].slice.call(document.body.children).filter(function (el) {
      return el !== banner && !el.contains(banner) && el.tagName !== 'SCRIPT';
    });
  }

  function apply(menu) {
    var open = menu.classList.contains(OPEN);
    outside(menu).forEach(function (el) {
      if (open) el.setAttribute('inert', '');
      else el.removeAttribute('inert');
    });
  }

  function start() {
    var menu = document.querySelector('.nav-links');
    if (!menu || menu.dataset.inertBound) return;
    menu.dataset.inertBound = '1';
    new MutationObserver(function () { apply(menu); })
      .observe(menu, { attributes: true, attributeFilter: ['class'] });
    apply(menu);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
