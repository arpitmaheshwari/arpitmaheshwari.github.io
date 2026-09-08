/* ─────────────────────────────────────────────────────────────────────────────
   THE CASE-BOARD INSTRUMENTS — play once, on scroll.

   Each card on the case board carries a working miniature of that product. This
   fires it as the reader arrives at it, once, and then leaves it alone forever.

   Why not a pure-CSS view() timeline: a scroll timeline SCRUBS. Scroll down and
   the plan computes; scroll up and it un-computes. These are one-shot events —
   a plan is calculated, a verdict lands, a bill arrives — so they get to happen
   once, at their own pace, like the real thing.

   Progressive enhancement: the pre-animation states in ember.css live behind
   html.vg-js AND behind prefers-reduced-motion:no-preference. So with this file
   blocked, JavaScript off, or reduced motion on, every instrument renders in
   its resolved state — the information is never carried by the motion.

   The observer unobserves each card as it fires and disconnects itself once the
   last one has, so a settled board costs nothing. Measured at rest on a phone
   viewport: 0ms of task time over six seconds.
   ────────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';
  /* .bcard is a board tile; .vg-hero wraps the single instrument that opens a
     case page. Both fire once, on arrival. */
  var cards = [].slice.call(document.querySelectorAll('.bcard, .vg-hero'));
  if (!cards.length) return;

  /* No IntersectionObserver, or motion is unwelcome: show everything resolved
     and never animate. .live is harmless in both cases — the animations are
     gated on the no-preference media query in the stylesheet. */
  if (!('IntersectionObserver' in window)) {
    cards.forEach(function (c) { c.classList.add('live'); });
    return;
  }

  var left = cards.length;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('live');
      io.unobserve(e.target);
      if (--left === 0) io.disconnect();
    });
  }, { threshold: 0.34, rootMargin: '0px 0px -8% 0px' });

  cards.forEach(function (c) { io.observe(c); });
})();
