/* The email address, assembled at run time — on every page, not just one.
 *
 * Arpit, 2026-09-09: "The first thing I want is to connect with me either on
 * LinkedIn or email and initiate the conversation." Measured against that, the
 * site asked for the wrong thing: "Book the 30-min call" appeared 81 times
 * across 38 pages and sat in the sticky nav, while email existed as a single
 * link at 94% of the way down ONE page and LinkedIn at 79%. Canon already knew
 * the shape of this — "Email IS public (changed 2026-07-21 after recruiter
 * feedback — recruiters don't fill forms)" — and also calls the calendar "the
 * quiet secondary", which it had stopped being.
 *
 * Why this file exists at all: canon keeps the address OUT of the served HTML
 * so bots cannot scrape it, which is why it was assembled by an inline script.
 * That script lived on index.html alone, so a nav CTA on 38 pages could not use
 * it. Copying it inline 38 times is the exact pattern this repo already
 * abandoned once ("lived as an inline block on 20 pages and was simply ABSENT
 * from the other 17"). So the behaviour travels with the nav instead, in one
 * file, owning one concern.
 *
 * Destinations are set ON LOAD, not on click: with it only on click the link is
 * href="#contact" for keyboard activation, "copy link address", middle-click and
 * assistive tech — a lesson the inline version had already learned and written
 * down. Every [data-email] element is wired independently, so a page that is
 * missing one does not silently kill the rest.
 */
(function () {
  'use strict';
  var user = 'maheshwari.arpit' + '88';
  var host = 'gmail.com';
  var to = 'mailto:' + user + '@' + host;

  function wire() {
    var els = document.querySelectorAll('[data-email]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.dataset.emailBound) continue;      // never wire twice
      el.dataset.emailBound = '1';
      var subject = el.getAttribute('data-email-subject');
      el.setAttribute('href', subject ? to + '?subject=' + encodeURIComponent(subject) : to);
      // an element left empty on purpose gets the address as its label
      if (!el.textContent.trim()) el.textContent = user + '@' + host;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
