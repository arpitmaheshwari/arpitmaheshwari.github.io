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
    f.addEventListener('pointermove', function (e) {
      var r = f.getBoundingClientRect();
      var rx = ((e.clientY - r.top) / r.height - 0.5) * -7;
      var ry = ((e.clientX - r.left) / r.width - 0.5) * 9;
      f.style.transform = 'perspective(900px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateY(-6px)';
    });
    f.addEventListener('pointerleave', function () { f.style.transform = ''; });
  });
})();

/* ---- the moving light (L20 item 3) --------------------------------------
   Sets --tx/--ty in [-1,1] on the hovered card so its shadow and lit edge can
   follow the cursor. Deliberately narrow:
     · only when the modern touch is on, so the attribute stays the single switch;
     · only for a FINE pointer with real hover — on a touch screen the values
       would be set once on tap and then stick, which reads as a stuck card;
     · never under prefers-reduced-motion.
   With none of that true the custom properties stay 0 and the CSS degrades to a
   plain centred lift, which is why the selectors do not depend on this file. */
(function () {
  var d = document.documentElement;
  if (d.getAttribute('data-touch') !== 'modern') return;
  if (!window.matchMedia) return;
  if (!matchMedia('(hover:hover) and (pointer:fine)').matches) return;
  if (matchMedia('(prefers-reduced-motion:reduce)').matches) return;
  var SEL = '.rcell,.lane,.idx a,.thought-card';
  document.addEventListener('pointermove', function (e) {
    var card = e.target.closest && e.target.closest(SEL);
    if (!card) return;
    var r = card.getBoundingClientRect();
    if (!r.width || !r.height) return;
    card.style.setProperty('--tx', ((e.clientX - r.left) / r.width * 2 - 1).toFixed(3));
    card.style.setProperty('--ty', ((e.clientY - r.top) / r.height * 2 - 1).toFixed(3));
  }, { passive: true });
  document.addEventListener('pointerout', function (e) {
    var card = e.target.closest && e.target.closest(SEL);
    if (!card) return;
    card.style.setProperty('--tx', 0);
    card.style.setProperty('--ty', 0);
  }, { passive: true });
})();

/* ---- L21 · the essay contents rail -------------------------------------
   Why this exists. Measured on /writing/confidence-scoring at 1440: a 609px
   prose column with 368px of empty margin on the left and 463px on the right,
   for the whole length of the essay. The layout rule calls that a defect —
   capped text in a wide container is a decision about the remaining space, and
   "empty because the column ended" is not a decision.

   The case pages already solved this with a margin rail (cream.css L17), but
   that grid keys off .measure-c/.measure-t and the four essays have NEITHER:
   their layout comes from xi-* extracted classes carrying their own max-width
   and auto margins. So rather than fight those for the column, this gives the
   LEFT margin a job and leaves the column exactly where it is.

   Contents are generated from the page's own h2s — nothing is authored here, so
   no fact can be invented. Built in script because the essays carry no heading
   ids to anchor to; with no JS the essay reads exactly as it does today. */
(function () {
  var d = document.documentElement;
  if (!/\bp-writing-/.test(document.body.className)) return;   // essays only, not the index
  var main = document.querySelector('main');
  if (!main) return;
  var heads = [].slice.call(main.querySelectorAll('h2'));
  if (heads.length < 3) return;            // too few sections to be worth a rail

  // the essay's own column wrapper: the closest common ancestor of the headings
  var host = heads[0].parentElement;
  while (host && host !== main && !heads.every(function (h) { return host.contains(h); })) {
    host = host.parentElement;
  }
  if (!host || host === document.body) return;

  function slug(s) {
    return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48);
  }
  var wrap = document.createElement('div');
  wrap.className = 'esy-rail';
  var nav = document.createElement('nav');
  nav.className = 'esy-toc';
  nav.setAttribute('aria-label', 'Contents');
  var head = document.createElement('p');
  head.className = 'esy-toc-h';
  head.textContent = 'Contents';
  nav.appendChild(head);
  var list = document.createElement('ol');
  heads.forEach(function (h, i) {
    var text = (h.textContent || '').trim();
    if (!h.id) h.id = slug(text) || ('section-' + (i + 1));
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = text;
    li.appendChild(a);
    list.appendChild(li);
  });
  nav.appendChild(list);
  wrap.appendChild(nav);
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
  host.insertBefore(wrap, host.firstChild);

  /* mark the section being read: the LAST heading scrolled past, not one that
     happens to sit inside a band. The first version used an IntersectionObserver
     with rootMargin '-88px 0px -70% 0px' and marked nothing for most of the
     page, because between two headings no heading is inside the band at all —
     verified by scrolling to 1400px and reading back "none marked". */
  var links = heads.map(function (h) { return nav.querySelector('a[href="#' + h.id + '"]'); });
  var raf = 0;
  function mark() {
    raf = 0;
    var line = 96, active = -1;               // just under the 64px bar
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].getBoundingClientRect().top <= line) active = i;
    }
    for (var k = 0; k < links.length; k++) {
      if (!links[k]) continue;
      if (k === active) links[k].setAttribute('aria-current', 'true');
      else links[k].removeAttribute('aria-current');
    }
  }
  function onScroll() { if (!raf) raf = requestAnimationFrame(mark); }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll, { passive: true });
  mark();
})();
