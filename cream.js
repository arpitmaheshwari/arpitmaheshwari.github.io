/* cream.js — the gallery's motion (branch: cream, 2026-09-05).
 * Source: Cream Design System v1.0 (Arpit's package), Concept 9 ground truth.
 * Three behaviours, nothing else: the cursor gold glow, gallery-ease reveals,
 * and the 3D frame tilt (max 7deg/9deg). All three die under reduced motion.
 * Replaces attention.js's doubt ring + the chant band — retired by Arpit's
 * decision when the cream skin landed. */
(function () {
  'use strict';
  if (document.documentElement.getAttribute('data-skin') !== 'cream') return;
  var reduce = matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* reveals — IntersectionObserver adds .visible; CSS carries the ease */
  var io = ('IntersectionObserver' in window) && new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(function (el) {
    if (reduce || !io) el.classList.add('visible'); else io.observe(el);
  });
  if (reduce) return;

  /* the glow follows the cursor, eased [spec] */
  var glow = document.createElement('div');
  glow.id = 'cream-glow'; glow.setAttribute('aria-hidden', 'true');
  document.body.appendChild(glow);
  var mx = innerWidth / 2, my = innerHeight * 0.4, sx = mx, sy = my, live = false;
  addEventListener('pointermove', function (e) { mx = e.clientX; my = e.clientY; live = true; }, { passive: true });
  (function tick() {
    if (live) {
      sx += (mx - sx) * 0.045; sy += (my - sy) * 0.045;
      glow.style.background = 'radial-gradient(560px circle at ' + sx + 'px ' + sy +
        'px, rgba(214,178,120,.18), transparent 70%)';
    }
    requestAnimationFrame(tick);
  })();

  /* frame tilt on hover — max 7/9 degrees [spec]; pointer-fine only */
  if (!matchMedia('(hover:hover) and (pointer:fine)').matches) return;
  document.querySelectorAll('.frame, .fig-shot-live, figure.framed').forEach(function (f) {
    f.style.transition = 'transform .7s cubic-bezier(.16,1,.3,1), box-shadow .7s';
    f.addEventListener('pointermove', function (e) {
      var r = f.getBoundingClientRect();
      var rx = ((e.clientY - r.top) / r.height - 0.5) * -7;
      var ry = ((e.clientX - r.left) / r.width - 0.5) * 9;
      f.style.transform = 'perspective(900px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateY(-6px)';
    });
    f.addEventListener('pointerleave', function () { f.style.transform = ''; });
  });
})();
