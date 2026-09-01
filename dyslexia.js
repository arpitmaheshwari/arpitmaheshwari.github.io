/* The dyslexia-friendly reading toggle.
 *
 * This lived as an inline block on 20 pages and was simply ABSENT from the other 17, which
 * still rendered the button, still gave it aria-pressed, and did nothing when it was
 * pressed. A control that claims to help a low-vision reader and quietly does nothing is
 * worse than not shipping one, so the behaviour now travels with the button in
 * partials/footer.html instead of being copied per page.
 *
 * Restores the reader's last choice, and degrades quietly where storage is unavailable
 * (private windows and some embedded views throw on access, not just return null).
 */
(function () {
  'use strict';
  var KEY = 'dyslexia-mode';
  function read() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function write(v) { try { localStorage.setItem(KEY, v); } catch (e) { /* no-op */ } }

  // Stale inline copies of this handler still ship on ~18 pages; two toggles
  // cancel each other and the control goes dead (caught by the 2026-09-02
  // exploratory sweep). Cloning the button strips every earlier listener, so
  // this file is the ONLY binder no matter what a page pasted inline. This
  // script loads deferred, i.e. after every inline block that could bind.
  function claim(btn) {
    var clone = btn.cloneNode(true);
    btn.replaceWith(clone);
    return clone;
  }

  function start() {
    var btn = document.getElementById('dyslexiaToggle');
    if (!btn || btn.dataset.dyslexiaBound) return;   // never bind twice
    btn = claim(btn);
    btn.dataset.dyslexiaBound = '1';

    function apply(on) {
      document.body.classList.toggle('dyslexia-mode', on);
      btn.classList.toggle('active', on);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    apply(read() === 'on');

    btn.addEventListener('click', function () {
      var on = !document.body.classList.contains('dyslexia-mode');
      apply(on);
      write(on ? 'on' : 'off');
      if (typeof gtag === 'function') gtag('event', 'dyslexia_toggle', { state: on ? 'on' : 'off' });
    });
  }

  // The mobile menu, same story one register up: the binder used to live as an
  // inline block per page, and 7 pattern pages shipped WITHOUT it — a rendered
  // hamburger that did nothing, so phone readers could not navigate at all
  // (2026-09-02 sweep, BLOCKER). The behaviour now travels with the nav in the
  // shared script every page loads; claim() strips any page's stale inline copy.
  function startMenu() {
    var btn = document.getElementById('menuToggle');
    var links = document.querySelector('.nav-links');
    if (!btn || !links || btn.dataset.menuBound) return;
    btn = claim(btn);
    btn.dataset.menuBound = '1';
    function close() {
      links.classList.remove('nav-open');
      btn.setAttribute('aria-expanded', 'false');
    }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = links.classList.toggle('nav-open');
      btn.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', function (e) {
      if (links.classList.contains('nav-open') && !links.contains(e.target) && !btn.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('nav-open')) { close(); btn.focus(); }
    });
    // stray duplicate scroll-shading binders are idempotent (toggle with a condition)
    var nav = document.getElementById('nav');
    if (nav) window.addEventListener('scroll', function () {
      nav.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  function boot() { start(); startMenu(); }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
