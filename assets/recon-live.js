/* recon-live.js — the self-demonstrating widget (2026-08-06).
 *
 * Why this exists: a static embedded demo reads as an IMAGE in a sea of text — visitors
 * scroll past it exactly like a screenshot (Arpit's correction, and the industry agrees:
 * the ghost-cursor / auto-demo pattern is a whole product category). So each .recon widget
 * demonstrates ITSELF once when it first enters the viewport: a ghost cursor glides to a
 * real control, presses it (a real .click(), so the widget genuinely changes state), and
 * fades. The visitor sees the instrument being used — the strongest possible affordance.
 *
 * Gestalt principles carried by this file:
 *   - Continuity + common fate: the ghost's path connects control to consequence; the
 *     MutationObserver flashes every element that changes on a press, so cause and effect
 *     visibly move together.
 * The rest (figure/ground, proximity, similarity, closure, symmetry, common region) live
 * in styles.css under "Interactive moments".
 *
 * Honesty rails: the ghost presses a real button — never fakes a result; it runs ONCE per
 * widget per page-load; it is aria-hidden decoration (the state change it triggers is
 * announced by the widgets' own aria-live regions); reduced-motion visitors skip the ghost
 * entirely (no motion, no synthetic click — their widget stays untouched until they act).
 */
(function () {
  'use strict';
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var widgets = document.querySelectorAll('.recon');
  if (!widgets.length || !('IntersectionObserver' in window)) return;

  /* Common fate: anything that changes inside a widget flashes, so a press visibly
     propagates to its consequences. */
  widgets.forEach(function (w) {
    var mo = new MutationObserver(function (muts) {
      muts.forEach(function (m) {
        var el = m.target.nodeType === 3 ? m.target.parentElement : m.target;
        if (!el || !el.classList || el.classList.contains('rl-ghost')) return;
        if (el.closest && el.closest('button')) return; /* buttons have their own physics */
        el.classList.remove('rl-flash');
        void el.offsetWidth;
        el.classList.add('rl-flash');
      });
    });
    mo.observe(w, { subtree: true, childList: true, characterData: true });
  });

  function ghostDemo(w) {
    if (w.dataset.rlDone) return;
    w.dataset.rlDone = '1';
    var target = null;
    var btns = w.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      if (btns[i].getAttribute('aria-pressed') === 'false') { target = btns[i]; break; }
    }
    if (!target) target = btns[0];
    if (!target) return;

    var g = document.createElement('div');
    g.className = 'rl-ghost';
    g.setAttribute('aria-hidden', 'true');
    w.appendChild(g);

    var wr = w.getBoundingClientRect();
    var tr = target.getBoundingClientRect();
    /* start at the widget's centre, land on the control's centre */
    var x0 = wr.width / 2, y0 = wr.height * 0.6;
    var x1 = tr.left - wr.left + tr.width / 2, y1 = tr.top - wr.top + tr.height / 2;
    g.style.transform = 'translate(' + x0 + 'px,' + y0 + 'px)';

    requestAnimationFrame(function () {
      g.classList.add('rl-ghost--on');
      requestAnimationFrame(function () {
        g.style.transform = 'translate(' + x1 + 'px,' + y1 + 'px)';
      });
    });
    setTimeout(function () {
      g.classList.add('rl-ghost--press');
      target.click();
    }, 950);
    setTimeout(function () { g.classList.remove('rl-ghost--press'); }, 1250);
    setTimeout(function () {
      g.classList.remove('rl-ghost--on');
      setTimeout(function () { g.remove(); }, 450);
    }, 1900);
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting && e.intersectionRatio >= 0.6) {
        io.unobserve(e.target);
        setTimeout(function () { ghostDemo(e.target); }, 350);
      }
    });
  }, { threshold: 0.6 });
  widgets.forEach(function (w) { io.observe(w); });
})();
