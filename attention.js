/* attention.js — what a reader actually did, measured on this page.
   No third party: every signal below is sent to the analytics already installed.

   Why this exists (2026-08-15): the site could tell me a page was OPENED and a
   CTA was CLICKED, and nothing in between — so "does anyone reach the AdTech
   thesis?" was unanswerable. A visual heatmap needs volume this site does not
   have yet; scroll depth and section dwell are readable at n=20.

   Sends five things, once each per page view:
     scroll_depth      25 / 50 / 75 / 100  — how far down the reader got
     section_dwell     seconds a named section was actually on screen (>=2s)
     artifact_view     a diagram entered the viewport (did the evidence land?)
     read_complete     reached the last section AND spent > 45s (a real read)
     rage_click        3+ clicks in one spot inside 1s (something looked clickable)

   HOW TO VERIFY IT YOURSELF (30 seconds, real browser — headless cannot do
   this faithfully: it dispatches scroll events unreliably, which cost a long
   diagnosis here). Open any page, scroll to the bottom, then in the console:
       window.__attention.sent
   You should see scroll_depth entries and, after leaving the tab,
   section_dwell. Google Analytics → Admin → DebugView shows the same events
   arriving live.

   Deliberately NOT collected: no mouse paths, no keystrokes, no text entered,
   no per-visitor identifier of any kind. Everything here is page-scoped and
   aggregate-shaped, which is the same honesty the patterns pages argue for.
*/
(function () {
  'use strict';
  if (!window.matchMedia) return;
  var send = function (name, params) {
    if (window.__attention) window.__attention.sent.push(name);
    if (typeof window.gtag === 'function') window.gtag('event', name, params || {});
  };
  var page = location.pathname.replace(/index\.html$/, '') || '/';
  window.__attention = { loaded: true, sent: [] };   // verification affordance:
  // a tracker that silently does nothing is worse than none. This lets a probe
  // (and the pre-push gate) prove the script RAN and what it emitted.
  var started = Date.now();

  /* ---------- 1 · scroll depth ----------
     NOTE (measured, not assumed): this site scrolls the BODY element, not the
     window — body carries overflow-y:auto, so window.scrollY stays 0 forever.
     A window-only listener records nothing for every real visitor. Caught in
     testing because the probe scrolled and the counter never moved. */
  var marks = [25, 50, 75, 100], hit = {};
  /* Use the STANDARD scrolling element rather than sniffing overflow. First
     attempt guessed the scroller by checking overflow-y, and picked <body>
     because body carries overflow-y:auto here — but the document is what
     actually scrolls, so scrollTop was read off the wrong element and every
     reader would have registered 0%. document.scrollingElement is the browser
     telling us the answer instead of us inferring it. */
  function onScroll() {
    var el = document.scrollingElement || document.documentElement;
    var top = el.scrollTop || window.scrollY || 0;
    var max = el.scrollHeight - el.clientHeight;
    if (max < 200) return;                      // too short to have a "depth"
    var pct = Math.min(100, Math.round((top / max) * 100));
    for (var i = 0; i < marks.length; i++) {
      var m = marks[i];
      if (pct >= m && !hit[m]) {
        hit[m] = true;
        send('scroll_depth', { percent: m, page_path: page });
      }
    }
  }
  /* Throttle on a timestamp, not requestAnimationFrame. rAF-gated throttling
     leaves a latch (`ticking`) that never clears if the browser drops the
     frame — background tabs and reduced-motion contexts do exactly that, and
     every later scroll is then ignored. Measured: four depth marks crossed,
     one event emitted. A clock cannot get stuck. */
  var lastRun = 0;
  function handler() {
    var now = Date.now();
    if (now - lastRun < 120) return;
    lastRun = now;
    onScroll();
  }
  window.addEventListener('scroll', handler, { passive: true });
  document.addEventListener('scroll', handler, { passive: true, capture: true });

  /* ---------- 2 · section dwell + 3 · artifact views ---------- */
  if ('IntersectionObserver' in window) {
    var enter = new WeakMap(), total = new WeakMap();
    var named = [].slice.call(document.querySelectorAll('main section[id], section[id]'));
    var dwell = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          enter.set(e.target, Date.now());
        } else if (enter.has(e.target)) {
          var secs = (Date.now() - enter.get(e.target)) / 1000;
          enter.delete(e.target);
          total.set(e.target, (total.get(e.target) || 0) + secs);
        }
      });
    }, { threshold: 0.4 });
    named.forEach(function (s) { dwell.observe(s); });

    var artifacts = [].slice.call(document.querySelectorAll('figure svg, figure img, [data-demo]'));
    var seen = new WeakSet();
    var artObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting || seen.has(e.target)) return;
        seen.add(e.target);
        var fig = e.target.closest('figure, section');
        var label = (e.target.getAttribute('data-demo') ||
                     (fig && fig.id) ||
                     (e.target.getAttribute('aria-label') || '').slice(0, 40) ||
                     'artifact');
        send('artifact_view', { artifact: label, page_path: page });
      });
    }, { threshold: 0.5 });
    artifacts.forEach(function (a) { artObs.observe(a); });

    /* flush dwell on the way out — one event per section that held attention */
    var flushed = false;
    var flush = function () {
      if (flushed) return; flushed = true;
      named.forEach(function (s) {
        if (enter.has(s)) {
          total.set(s, (total.get(s) || 0) + (Date.now() - enter.get(s)) / 1000);
        }
        var secs = Math.round(total.get(s) || 0);
        if (secs >= 2) {
          send('section_dwell', { section: s.id, seconds: secs, page_path: page });
        }
      });
      var elapsed = (Date.now() - started) / 1000;
      var last = named[named.length - 1];
      if (last && (total.get(last) || 0) > 0 && elapsed > 45) {
        send('read_complete', { page_path: page, seconds: Math.round(elapsed) });
      }
    };
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') flush();
    });
    window.addEventListener('pagehide', flush);
  }

  /* ---------- 4 · rage clicks: something looked clickable and wasn't ---------- */
  var recent = [];
  document.addEventListener('click', function (ev) {
    var now = Date.now();
    recent = recent.filter(function (c) { return now - c.t < 1000; });
    recent.push({ x: ev.clientX, y: ev.clientY, t: now });
    var near = recent.filter(function (c) {
      return Math.abs(c.x - ev.clientX) < 30 && Math.abs(c.y - ev.clientY) < 30;
    });
    if (near.length >= 3) {
      var el = ev.target.closest('a,button') ? 'interactive' : 'dead';
      send('rage_click', {
        page_path: page,
        target: el,
        label: (ev.target.textContent || '').trim().slice(0, 30)
      });
      recent = [];
    }
  }, { passive: true });
})();

/* Walkthrough video: a controls-video ignores body clicks in poster state, so the
   whole frame becomes click-to-toggle. The guard skips the bottom 52px — clicks on
   the native control bar already toggle, and handling them here would double-toggle
   into a no-op (verified by CDP hit-test before this was written). */
document.addEventListener('click', function (e) {
  var v = e.target.closest && e.target.closest('.vid-frame video');
  if (!v) return;
  var r = v.getBoundingClientRect();
  if (e.clientY > r.bottom - 52) return;            // native control bar
  // Chrome ignores body clicks in poster state but toggles them itself once
  // playing — acting unconditionally made pause impossible (both toggles
  // cancelled). So: act only if, a beat later, the native handler did nothing.
  var was = v.paused;
  setTimeout(function () {
    if (v.paused !== was) return;                   // native already toggled
    if (was) { v.play(); } else { v.pause(); }
  }, 60);
});
