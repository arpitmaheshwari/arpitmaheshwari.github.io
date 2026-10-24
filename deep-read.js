/* deep-read.js — the long case story sits behind <details class="deep-read">.
   Native disclosure does the work; this only makes sure an in-page link whose
   target is INSIDE the fold (slip rows, jump nav, rail, a shared #hash) opens
   it first, so the browser's own scroll lands on a rendered element. */
(function () {
  var d = document.getElementById('full-case');
  if (!d) return;
  function inside(hash) {
    if (!hash || hash.length < 2) return null;
    var t = document.getElementById(decodeURIComponent(hash.slice(1)));
    return t && d.contains(t) ? t : null;
  }
  function openFor(hash, scroll) {
    var t = inside(hash);
    if (!t) return;
    if (!d.open) d.open = true;
    if (scroll) requestAnimationFrame(function () { t.scrollIntoView(); });
  }
  // a link clicked: open BEFORE the browser follows the hash
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (a) openFor(a.getAttribute('href'), false);
  }, true);
  window.addEventListener('hashchange', function () { openFor(location.hash, true); });
  openFor(location.hash, true);
})();
