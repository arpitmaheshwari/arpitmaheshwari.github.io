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

  function start() {
    var btn = document.getElementById('dyslexiaToggle');
    if (!btn || btn.dataset.dyslexiaBound) return;   // never bind twice
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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
