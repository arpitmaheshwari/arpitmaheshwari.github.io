/* ============================================================================
   fit.js — the /fit/ matcher.

   WHAT IT IS: a lexicon and a static index, matched with string search. There is no
   model, no network call, no scoring heuristic dressed up as intelligence. The page
   says so, and this file has to stay true to that sentence.

   TWO THINGS THAT ARE EASY TO GET WRONG AND ARE HANDLED HERE
   1. Overlapping terms. "design system" contains "design"; "user research" contains
      "research". Matching every term independently double-counts and makes a JD look
      like a broader hit than it is. Terms are applied longest-first over an occupancy
      map, so the longest phrase claims the characters and the shorter one cannot.
   2. Short tokens. "ai", "ml", "vc", "3d" are real JD words and also live inside other
      words. Every term is matched on word boundaries, and a term made only of word
      characters gets \b on both ends.

   The honest failure mode is stated in the UI rather than hidden: a lexicon of a few
   hundred phrases will miss wording it has never seen, and it says so when it finds
   nothing.
   ============================================================================ */
(function () {
  'use strict';

  var IDX = null;
  var form = document.getElementById('fit-form');
  if (!form) return;

  var SAMPLE = [
    'Senior Product Designer, AI',
    '',
    'You will design AI-native experiences for a B2B SaaS platform used by revenue teams.',
    'You will work day to day with ML engineers and data scientists to turn model output',
    'into interfaces people trust — confidence, explainability, and human-in-the-loop review',
    'of agent actions.',
    '',
    'What you will do',
    '- Own end-to-end design for data-dense dashboards and workflow tools',
    '- Build and evolve our design system, with design tokens and a component library',
    '- Prototype in code (React/TypeScript) and partner closely with front-end engineers',
    '- Run usability testing and discovery interviews with enterprise customers',
    '',
    'Requirements',
    '- 8+ years in product design, including 0 to 1 work',
    '- Experience with enterprise SaaS and complex data',
    '- Strong accessibility practice (WCAG)',
    '- Comfortable with ambiguity in an early stage startup',
    '',
    'Nice to have',
    '- Experience in fintech or private equity',
    '- Native iOS and Android app design',
    '- Motion design'
  ].join('\n');

  /* ── matching ────────────────────────────────────────────────────────────── */

  function normalise(s) {
    return s.toLowerCase()
      .replace(/[‘’]/g, "'")
      .replace(/[“”]/g, '"')
      .replace(/[–—]/g, '-')
      .replace(/\s+/g, ' ');
  }

  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function boundedRe(term) {
    var t = esc(term);
    // \b only means anything next to a word character; "0 to 1" ends in one, "c++" would not
    var lead = /^\w/.test(term) ? '\\b' : '';
    var tail = /\w$/.test(term) ? '\\b' : '';
    return new RegExp(lead + t + tail, 'g');
  }

  function match(text) {
    var hay = normalise(text);
    var taken = new Uint8Array(hay.length);
    var hits = {};              // evidence id (or '!blocker' / '!none') -> [terms]
    // IDX.terms arrives sorted longest-first; the longest phrase claims the characters
    IDX.terms.forEach(function (pair) {
      var term = pair[0], id = pair[1] === null ? '!none' : pair[1];
      var re = boundedRe(normalise(term)), m, found = false;
      while ((m = re.exec(hay)) !== null) {
        var a = m.index, b = a + m[0].length, clash = false, i;
        for (i = a; i < b; i++) { if (taken[i]) { clash = true; break; } }
        if (!clash) {
          for (i = a; i < b; i++) taken[i] = 1;
          found = true;
        }
        if (re.lastIndex === m.index) re.lastIndex++;   // zero-length guard
      }
      if (found) { (hits[id] = hits[id] || []).push(term); }
    });
    return hits;
  }

  /* ── rendering ───────────────────────────────────────────────────────────── */

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function termChips(terms) {
    var p = el('p', 'fit-terms');
    p.appendChild(el('span', 'fit-terms-k', 'matched on'));
    terms.slice(0, 8).forEach(function (t) { p.appendChild(el('code', 'fit-chip', t)); });
    if (terms.length > 8) p.appendChild(el('span', 'fit-more', '+' + (terms.length - 8) + ' more'));
    return p;
  }

  function citeList(cites) {
    var p = el('p', 'fit-cites');
    p.appendChild(el('span', 'fit-cites-k', 'check it'));
    cites.forEach(function (u) {
      var a = el('a', 'fit-cite', u);
      a.href = u.charAt(0) === '/' ? '..' + u : u;
      a.setAttribute('data-cta', 'fit-cite');
      a.setAttribute('data-location', 'fit-results');
      p.appendChild(a);
    });
    return p;
  }

  function group(key, title, blurb, items, render, count) {
    var sec = el('section', 'fit-group fit-group--' + key);
    var h = el('h3', 'fit-group-h');
    h.appendChild(el('span', 'fit-group-t', title));
    h.appendChild(el('span', 'fit-group-n', String(count == null ? items.length : count)));
    sec.appendChild(h);
    sec.appendChild(el('p', 'fit-group-b', blurb));
    var ul = el('ul', 'fit-list');
    items.forEach(function (it) { ul.appendChild(render(it)); });
    sec.appendChild(ul);
    return sec;
  }

  function evidenceItem(entry) {
    var li = el('li', 'fit-item');
    li.appendChild(el('p', 'fit-item-h', entry.label));
    li.appendChild(el('p', 'fit-item-c', entry.claim));
    li.appendChild(citeList(entry.cites));
    li.appendChild(termChips(entry.terms));
    return li;
  }

  /* Terms are a list, not findings. One card per term produced a stack of boxes each
     holding a 60px chip against 590px of nothing — leftover space, not designed space.
     They share one card and wrap. */
  function chipsItem(terms) {
    var li = el('li', 'fit-item fit-item--chips');
    terms.forEach(function (t) { li.appendChild(el('code', 'fit-chip', t)); });
    return li;
  }

  function render(hits) {
    var out = document.getElementById('fit-out');
    out.textContent = '';

    var documented = [], thin = [];
    Object.keys(hits).forEach(function (id) {
      if (id.charAt(0) === '!') return;
      var e = IDX.evidence[id];
      if (!e) return;
      var withTerms = Object.assign({}, e, { terms: hits[id] });
      (e.strength === 'thin' ? thin : documented).push(withTerms);
    });
    // most specific first: the entry the JD said the most about leads
    documented.sort(function (a, b) { return b.terms.length - a.terms.length; });
    thin.sort(function (a, b) { return b.terms.length - a.terms.length; });

    var blockers = (hits['!blocker'] || []);
    var unpublished = (hits['!none'] || []);
    var total = documented.length + thin.length + blockers.length + unpublished.length;

    var count = document.getElementById('fit-count');
    if (total === 0) {
      count.textContent = 'Nothing in this description matched the index.';
      out.appendChild(el('p', 'fit-empty',
        'That is a real answer, not an error — but it has two possible causes, and this tool ' +
        'cannot tell you which. Either the role is outside the work published here, or it is ' +
        'written in words the lexicon has never seen. It knows ' + IDX.terms.length +
        ' phrases; it is not a language model. Read the work and judge it yourself.'));
      return;
    }
    count.textContent = documented.length + ' documented · ' + thin.length + ' thin · ' +
      unpublished.length + ' with nothing published' +
      (blockers.length ? ' · ' + blockers.length + ' blocking' : '');

    if (blockers.length) {
      out.appendChild(group('block', 'Where the fit plainly isn’t there',
        'These are facts about the arrangement, not gaps in the work. If the role needs them, ' +
        'the rest of this page does not matter.',
        [blockers], chipsItem, blockers.length));
      // a div, not a p: <p> inside <p> is auto-closed by the parser, so the lines silently
      // became siblings of a stray empty paragraph rather than children of this one
      var note = el('div', 'fit-blocker-note');
      IDX.constraints.forEach(function (c) {
        var b = el('b', null, c[0] + ': ');
        var s = el('span', null, c[1]);
        var line = el('p', 'fit-blocker-line');
        line.appendChild(b); line.appendChild(s);
        note.appendChild(line);
      });
      out.appendChild(note);
    }

    if (documented.length) {
      out.appendChild(group('doc', 'Documented, with the page behind it',
        'A case study or a runnable artifact stands behind each of these. The links go to the ' +
        'page — read it and disagree if it does not hold up.',
        documented, evidenceItem));
    }
    if (thin.length) {
      out.appendChild(group('thin', 'Mentioned, but thin',
        'The site says this, but no case study carries its weight. Treat it as a claim to ' +
        'pressure-test in conversation, not as evidence.',
        thin, evidenceItem));
    }
    if (unpublished.length) {
      out.appendChild(group('none', 'Nothing published on this',
        'The role asks for these and this site does not answer them. That is not a claim he ' +
        'cannot do them — it is the tool declining to guess past its evidence.',
        [unpublished], chipsItem, unpublished.length));
    }
  }

  /* ── wiring ──────────────────────────────────────────────────────────────── */

  function paintContract() {
    var can = document.getElementById('fit-can');
    var cannot = document.getElementById('fit-cannot');
    IDX.contract.can.forEach(function (t) { can.appendChild(el('li', null, t)); });
    IDX.contract.cannot.forEach(function (t) { cannot.appendChild(el('li', null, t)); });
    var dl = document.getElementById('fit-constraints');
    IDX.constraints.forEach(function (c) {
      dl.appendChild(el('dt', null, c[0]));
      dl.appendChild(el('dd', null, c[1]));
    });
  }

  function run() {
    var jd = document.getElementById('fit-jd').value;
    if (!jd.trim()) { document.getElementById('fit-jd').focus(); return; }
    var res = document.getElementById('fit-results');
    res.hidden = false;           // unhide BEFORE rendering: content injected into a hidden
    render(match(jd));            // live region is not reliably announced by screen readers
    res.scrollIntoView({ behavior: 'smooth', block: 'start' });
    // and move focus to the answer, so a keyboard user is not left at the button with the
    // result somewhere below them
    var h = document.getElementById('h-results');
    if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    if (typeof gtag === 'function') gtag('event', 'fit_check_run', { length: jd.length });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  document.getElementById('fit-sample').addEventListener('click', function () {
    document.getElementById('fit-jd').value = SAMPLE;
    run();
  });
  document.getElementById('fit-clear').addEventListener('click', function () {
    document.getElementById('fit-jd').value = '';
    document.getElementById('fit-results').hidden = true;
    document.getElementById('fit-jd').focus();
  });

  fetch('../data/fit-index.json')
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (j) { IDX = j; paintContract(); })
    .catch(function () {
      // the page promised a contract before you type; if it cannot keep that promise it
      // says so rather than quietly accepting input it has nothing to match against
      var f = document.getElementById('fit-form');
      f.innerHTML = '<p class="fit-empty">The index did not load, so this tool cannot run. ' +
        'It will not guess without it. The work itself is at ' +
        '<a href="../index.html#featured-case-studies">the case studies</a>.</p>';
    });
})();
