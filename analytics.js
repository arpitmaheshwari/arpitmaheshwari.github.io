/* analytics.js — Google Analytics 4 loader, live domain only.

   WHY THIS FILE EXISTS: the GA snippet was pasted into 39 pages, so it fired
   from anywhere those pages were opened — including a local server. The gates
   in tools/ open every page many times; one full sweep is ~844 page loads, and
   a working day was thousands of fabricated visits in the numbers this site's
   owner reads to judge whether his outreach is landing. Blocking trackers in
   the test browsers fixed the gates. This fixes the site, so nothing running
   anywhere but the live domain can register — including a real person opening
   localhost in their own browser.

   THE ONE SUBTLETY: window.gtag is ALWAYS defined, on every host. Page code
   calls it from click and scroll handlers, and a good deal of that code does
   not check that it exists first. Off the live domain it becomes a no-op that
   still honours event_callback, because /folio/ fires an event and redirects
   in the callback — drop the callback and that page would hang for its 500ms
   fallback on every local open.

   TURNING IT OFF: blank MEASUREMENT_ID. Nothing else to unwind.
   ADDING A DOMAIN (a staging host, say): add it to LIVE_HOSTS.
*/
(function () {
  'use strict';
  var MEASUREMENT_ID = 'G-PFY6ME99K8';
  var LIVE_HOSTS = ['arpitmaheshwari.com', 'www.arpitmaheshwari.com'];

  // Keep the interface on every host; only the transmission is conditional.
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  var dnt = navigator.doNotTrack === '1' || window.doNotTrack === '1' ||
            navigator.msDoNotTrack === '1';
  var live = LIVE_HOSTS.indexOf(location.hostname) !== -1;

  if (!MEASUREMENT_ID || !live || dnt) {
    window.gtag = function () {
      var opts = arguments[2];
      if (opts && typeof opts.event_callback === 'function') {
        setTimeout(opts.event_callback, 0);   // /folio/ redirects from here
      }
    };
    return;
  }

  window.gtag = gtag;
  var s = document.createElement('script');
  s.async = 1;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + MEASUREMENT_ID;
  document.head.appendChild(s);

  gtag('js', new Date());
  // beacon transport survives the page unload, which is what the click-through
  // and scroll-depth events need. Two pages set it inline; now every page has it.
  gtag('config', MEASUREMENT_ID, { transport_type: 'beacon' });
})();
