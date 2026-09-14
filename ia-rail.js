/* ia-rail.js — the reading rail and the hero field card, built from the page's own headings.
   WHY (2026-09-14, Arpit: "fix the architectural gap across all the pages"): seventeen article pages and
   five Lab tool pages set their text in a 45% centred column and left the rest of the band empty. The
   chosen direction (A, from rendered options) gives that space a role: a sticky "on this page" list beside
   the article, and a field card in the hero that carries the page's own facts plus the section count.
   Nothing here is invented: the list is the page's h2s; the card's lines are moved from the hero itself.
   Below 1024px the rail is not rendered at all — a phone reads the page in source order. */
(function () {
  if (!window.matchMedia || !window.matchMedia('(min-width: 1024px)').matches) return;
  var main = document.querySelector('main');
  if (!main) return;
  var heads = [].slice.call(main.querySelectorAll('h2')).filter(function (h) {
    return h.textContent.trim() && !h.closest('.lab-tests') && !h.closest('[hidden]');
  });
  if (heads.length < 2) return;
  heads.forEach(function (h, i) { if (!h.id) h.id = 's-' + (i + 1); });   // ids are set in the source at build time; this is only a fallback
  function list() {
    var ol = document.createElement('ol');
    ol.className = 'ia-toc';
    heads.forEach(function (h) {
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = '#' + h.id; a.textContent = h.textContent.trim().replace(/^\d+\.\s*/, '');
      li.appendChild(a); ol.appendChild(li);
    });
    return ol;
  }
  // 1 · the hero card gets the section count and the list
  // the card states the count; it lists the sections only when it has nothing else to say (writing, resources),
  // because the article rail below already carries the list
  var card = document.querySelector('.page-head .ph-card, .lab-hero .lh-side');
  if (card) {
    var k = document.createElement('p'); k.className = 'ia-k'; k.textContent = 'On this page · ' + heads.length + ' sections';
    card.appendChild(k);
    if (!card.querySelector('.lbl-cap') || card.classList.contains('lh-side')) card.appendChild(list());
  }
  // 2 · the article rail (article family only; the Lab's body uses its own sticky headings)
  var col = main.querySelector(':scope > .xi-process-004');
  if (col) {
    var rail = document.createElement('aside');
    rail.className = 'ia-rail'; rail.setAttribute('aria-label', 'On this page');
    var rk = document.createElement('p'); rk.className = 'ia-k'; rk.textContent = 'On this page';
    rail.appendChild(rk); rail.appendChild(list());
    var meta = document.querySelector('.page-head .ph-card');
    if (meta) {
      var back = document.createElement('p'); back.className = 'ia-m';
      var first = meta.querySelector('.lbl-cap a');
      if (first) { var a2 = first.cloneNode(true); a2.className = ''; back.appendChild(document.createTextNode('Part of ')); back.appendChild(a2); rail.appendChild(back); }
    }
    main.classList.add('has-rail');
    main.insertBefore(rail, col);
    // the current section lights up as the reader scrolls
    if ('IntersectionObserver' in window) {
      var links = rail.querySelectorAll('a');
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (l) { l.classList.toggle('is-here', l.getAttribute('href') === '#' + e.target.id); }); } });
      }, { rootMargin: '-40% 0px -55% 0px' });
      heads.forEach(function (h) { io.observe(h); });
    }
  }
})();
