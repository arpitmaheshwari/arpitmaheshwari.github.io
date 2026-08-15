/* clarity.js — Microsoft Clarity loader (heatmaps + session replay).
   INACTIVE until a project ID is set below. Prepared 2026-08-15.

   HOW TO TURN IT ON (one edit, no other file changes):
     1. Sign in at https://clarity.microsoft.com  →  new project  →  copy the ID
     2. Replace the empty string on the PROJECT_ID line
     3. Update lab/teardown.html: the third-party-domains row goes from 1 to 2.
        (That row is a receipt. Leaving it stale is the exact failure this site
        argues against — and it was already stale once, counting Google Fonts
        months after they were removed.)
     4. Push. Every page picks it up — the loader is already linked site-wide.

   WHY A LOADER FILE INSTEAD OF A PASTED SNIPPET: the vendor's copy-paste
   snippet would have to live in 55 pages, and the inline-style/duplication
   gate exists precisely because this site has been bitten by the same thing
   pasted 16 different ways. One file, one ID, one place to turn it off.

   WHAT IT COSTS, HONESTLY:
     · a SECOND third-party domain gating nothing on first paint (loaded async)
       — lab/teardown.html's measured receipt has been updated to say two.
     · session replay records interactions on the page. It masks text input by
       default; this site has one email field, and DNT is honoured below.

   TURNING IT OFF: blank the ID. Nothing else to unwind.
*/
(function () {
  'use strict';
  var PROJECT_ID = 'y2u3gbd89h';   // live since 2026-08-15

  if (!PROJECT_ID) return;                        // inactive by default
  // respect an explicit do-not-track signal rather than arguing with it
  var dnt = navigator.doNotTrack === '1' || window.doNotTrack === '1' ||
            navigator.msDoNotTrack === '1';
  if (dnt) return;

  (function (c, l, a, r, i, t, y) {
    c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
    t = l.createElement(r); t.async = 1;
    t.src = 'https://www.clarity.ms/tag/' + i;
    y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
  })(window, document, 'clarity', 'script', PROJECT_ID);
})();
