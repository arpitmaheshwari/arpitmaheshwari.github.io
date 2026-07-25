/* Pattern demos — the same live demos as the book's Field Guide, in the classic theme.
   Each pattern page mounts one via <div class="pd" data-demo="key"></div>.
   Self-contained: injects its own styles, no dependencies, no data leaves the page. */
(function () {
  "use strict";

  var CSS = "" +
    ".pd{border:1px solid var(--border);border-radius:8px;padding:22px 24px;background:var(--bg-card)}" +
    ".pd__lead{font-family:var(--ff-mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-dim);margin:0 0 14px}" +
    ".pd__row{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:14px}" +
    ".pd__chip{font-family:var(--ff-display);font-weight:300;font-size:34px;line-height:1;color:var(--ink);font-variant-numeric:tabular-nums lining-nums}" +
    ".pd__seg{display:flex;gap:6px;flex:1 1 auto;min-width:200px}" +
    ".pd__btn{flex:1;padding:9px 6px;font-family:var(--ff-mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-muted);background:transparent;border:1px solid var(--border);border-radius:5px;cursor:pointer;transition:border-color .15s,color .15s,background .15s}" +
    ".pd__btn:hover{border-color:var(--gold);color:var(--ink)}" +
    ".pd__btn.on{background:var(--gold);color:var(--bg);border-color:var(--gold)}" +
    ".pd__btn:focus-visible{outline:2px solid var(--gold);outline-offset:2px}" +
    ".pd__go{padding:9px 16px;font-family:var(--ff-mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--gold);background:transparent;border:1px solid var(--gold-dark);border-radius:5px;cursor:pointer;transition:background .15s,color .15s}" +
    ".pd__go:hover{background:var(--gold);color:var(--bg)}" +
    ".pd__verdict{padding-top:14px;border-top:1px solid var(--border)}" +
    ".pd__verb{font-family:var(--ff-display);font-style:italic;font-size:21px;line-height:1.2;color:var(--gold);display:block;margin-bottom:5px}" +
    ".pd__verb--ok{color:#7ea88f}" +
    ".pd__sub{font-size:13px;line-height:1.55;color:var(--ink-muted)}" +
    ".pd__panel{margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--border);list-style:none}" +
    ".pd__panel li{font-size:13px;color:var(--ink-muted);padding:3px 0}" +
    ".pd__panel--src li{font-family:var(--ff-mono);font-size:11.5px;color:var(--gold)}" +
    ".pd__bar{height:6px;background:var(--border);border-radius:3px;margin-top:10px;overflow:hidden}" +
    ".pd__bar i{display:block;height:100%;background:var(--gold)}";

  function h(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  }
  function seg(labels, onPick, startIdx) {
    var wrap = h("div", "pd__seg");
    var btns = labels.map(function (l, i) {
      var b = h("button", "pd__btn" + (i === startIdx ? " on" : ""), l);
      b.type = "button";
      b.setAttribute("aria-pressed", i === startIdx ? "true" : "false");
      b.addEventListener("click", function () {
        btns.forEach(function (x, j) { x.className = "pd__btn" + (j === i ? " on" : ""); x.setAttribute("aria-pressed", j === i ? "true" : "false"); });
        onPick(i);
      });
      wrap.appendChild(b);
      return b;
    });
    return wrap;
  }
  function verdict() {
    var v = h("div", "pd__verdict");
    var verb = h("span", "pd__verb");
    var sub = h("div", "pd__sub");
    v.appendChild(verb); v.appendChild(sub);
    return { root: v, set: function (t, s, ok) { verb.textContent = t; verb.className = "pd__verb" + (ok ? " pd__verb--ok" : ""); sub.textContent = s; } };
  }

  var DEMOS = {

    /* act-review-ignore: a score never ships naked — it resolves to a verb */
    verbs: function (el) {
      el.appendChild(h("div", "pd__lead", "Three scores from the same model — each resolves to a verb, never a naked number"));
      var row = h("div", "pd__row");
      var chip = h("span", "pd__chip", "92");
      var v = verdict();
      var MAP = [
        { s: "92", verb: "→ Act on it", sub: "High confidence, signals named — the user can check the model's work and move. An override stays one click away." , ok: true },
        { s: "61", verb: "→ Review first", sub: "Mixed signals — surfaced for a human to weigh, with the reasons on the card. Never auto-run." },
        { s: "23", verb: "→ Ignore", sub: "Low confidence — the model declines to bluff. An honest no is what makes the act believable." }
      ];
      row.appendChild(chip);
      row.appendChild(seg(["Score 92", "Score 61", "Score 23"], function (i) { chip.textContent = MAP[i].s; v.set(MAP[i].verb, MAP[i].sub, !!MAP[i].ok); }, 0));
      el.appendChild(row); el.appendChild(v.root);
      v.set(MAP[0].verb, MAP[0].sub, true);
    },

    /* confidence-scores: same score, three stakes */
    gauge: function (el) {
      el.appendChild(h("div", "pd__lead", "The same 87% — three stakes, three different verbs"));
      var row = h("div", "pd__row");
      row.appendChild(h("span", "pd__chip", "87%"));
      var v = verdict();
      var MAP = [
        { verb: "→ Act on it", sub: "Low stakes: 87% clears the bar — let it run.", ok: true },
        { verb: "→ Review first", sub: "Medium stakes: 87% is close — a human glances before it ships." },
        { verb: "→ Hand to a human", sub: "High stakes: 87% isn't enough when the downside is real." }
      ];
      row.appendChild(seg(["Low stakes", "Medium", "High stakes"], function (i) { v.set(MAP[i].verb, MAP[i].sub, !!MAP[i].ok); }, 1));
      el.appendChild(row); el.appendChild(v.root);
      v.set(MAP[1].verb, MAP[1].sub);
    },

    /* ai-failure-states: deliver — or admit you can't */
    alert: function (el) {
      el.appendChild(h("div", "pd__lead", "Tap to see it deliver — or admit it can't"));
      var v = verdict();
      var MAP = [
        { verb: "Risk 7.2 / 10", sub: "Confident read — here's the breakdown, sources attached.", ok: true },
        { verb: "“I can't price this one.”", sub: "Out of its depth — says so plainly, and hands you to a human with context. No confident tone past the point it knows anything." }
      ];
      el.appendChild(seg(["Confident", "Unsure"], function (i) { v.set(MAP[i].verb, MAP[i].sub, i === 0); }, 1));
      el.appendChild(v.root);
      v.set(MAP[1].verb, MAP[1].sub);
    },

    /* ml-explainability: a number you can audit */
    branch: function (el) {
      el.appendChild(h("div", "pd__lead", "A number you can audit"));
      var row = h("div", "pd__row");
      row.appendChild(h("span", "pd__chip", "Risk 7.2"));
      var open = false;
      var panel = h("ul", "pd__panel");
      ["One client is 60% of revenue", "Founder is the sole code owner", "Churn up three quarters running"].forEach(function (t) { panel.appendChild(h("li", null, "— " + t)); });
      panel.style.display = "none";
      var btn = h("button", "pd__go", "Why this score? ▸");
      btn.type = "button"; btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", function () {
        open = !open;
        panel.style.display = open ? "" : "none";
        btn.textContent = open ? "Hide the reasons ▾" : "Why this score? ▸";
        btn.setAttribute("aria-expanded", String(open));
      });
      row.appendChild(btn);
      el.appendChild(row); el.appendChild(panel);
    },

    /* human-in-loop: correcting the model should feel like teaching */
    loop: function (el) {
      el.appendChild(h("div", "pd__lead", "Correcting it should feel like teaching, not cleanup"));
      var v = verdict();
      var done = false;
      var btn = h("button", "pd__go", "I disagree");
      btn.type = "button";
      function paint() {
        if (done) { v.set("Noted — you're teaching it", "Your correction is logged and feeds next week's model. Not an exception — a training signal.", true); btn.textContent = "↺ Start over"; }
        else { v.set("Recommend: raise bid 12%", "Not sure the model's right? Say so — and watch what happens to the correction."); btn.textContent = "I disagree"; }
      }
      btn.addEventListener("click", function () { done = !done; paint(); });
      el.appendChild(v.root); el.appendChild(h("div", "pd__row")).appendChild(btn);
      paint();
    },

    /* provenance-citations: the claim and its sources travel together */
    trace: function (el) {
      el.appendChild(h("div", "pd__lead", "The claim and its sources travel together"));
      var row = h("div", "pd__row");
      var claim = h("span", "pd__verb", "“Valuation looks stretched”");
      claim.style.fontSize = "19px";
      row.appendChild(claim);
      var open = false;
      var panel = h("ul", "pd__panel pd__panel--src");
      ["Cap table · row 14 ↗", "Board deck Q3 · p. 8 ↗", "Auditor's note · §2.1 ↗"].forEach(function (t) { panel.appendChild(h("li", null, t)); });
      panel.style.display = "none";
      var btn = h("button", "pd__go", "▸ 3 sources");
      btn.type = "button"; btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", function () {
        open = !open;
        panel.style.display = open ? "" : "none";
        btn.textContent = open ? "▾ 3 sources" : "▸ 3 sources";
        btn.setAttribute("aria-expanded", String(open));
      });
      row.appendChild(btn);
      el.appendChild(row); el.appendChild(panel);
      el.appendChild(h("div", "pd__sub", "A citation you can't open is decoration — each of these drills to the document itself."));
    },

    /* capability-contract: an honest no, drawn up front */
    bounds: function (el) {
      el.appendChild(h("div", "pd__lead", "An honest “no”, stated in the interface"));
      var v = verdict();
      var MAP = [
        { verb: "✓ Price liquid public equities", sub: "Confident here — this is the job it was built for.", ok: true },
        { verb: "✗ Illiquid, pre-revenue assets", sub: "Out of scope — handed to a human, not guessed. The boundary is specific, and it's on the screen, not in the docs." }
      ];
      el.appendChild(seg(["In scope", "Out of scope"], function (i) { v.set(MAP[i].verb, MAP[i].sub, i === 0); }, 0));
      el.appendChild(v.root);
      v.set(MAP[0].verb, MAP[0].sub, true);
    },

    /* calibration-track-record: confidence with a memory */
    calib: function (el) {
      el.appendChild(h("div", "pd__lead", "Confidence with a memory"));
      var row = h("div", "pd__row");
      row.appendChild(h("span", "pd__chip", "80% sure"));
      var open = false;
      var panel = h("div");
      panel.style.display = "none";
      var stat = h("div", "pd__sub");
      stat.innerHTML = "<strong style='color:var(--gold);font-family:var(--ff-display);font-style:italic;font-size:18px'>Right 82% of the time</strong> &nbsp;·&nbsp; across its last 200 calls at this confidence";
      var bar = h("div", "pd__bar");
      var fill = h("i"); fill.style.width = "82%";
      bar.appendChild(fill);
      panel.appendChild(stat); panel.appendChild(bar);
      var btn = h("button", "pd__go", "Show its track record ▸");
      btn.type = "button"; btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", function () {
        open = !open;
        panel.style.display = open ? "" : "none";
        btn.textContent = open ? "Hide the record ▾" : "Show its track record ▸";
        btn.setAttribute("aria-expanded", String(open));
      });
      row.appendChild(btn);
      el.appendChild(row); el.appendChild(panel);
      el.appendChild(h("div", "pd__sub", "Does 80% mean 80%? The history answers — and it doesn't reset when the model retrains."));
    },

    /* reversibility: a way back buys the first action */
    undo: function (el) {
      el.appendChild(h("div", "pd__lead", "Reversibility buys the first action"));
      var v = verdict();
      var MAP = [
        { verb: "Act now — undo anytime", sub: "Cheap to walk back, so people try it. The way back is shown before they commit.", ok: true },
        { verb: "Act now — permanent", sub: "Feels risky — so most won't act at all, however accurate the call." }
      ];
      el.appendChild(seg(["1-click undo", "No way back"], function (i) { v.set(MAP[i].verb, MAP[i].sub, i === 0); }, 0));
      el.appendChild(v.root);
      v.set(MAP[0].verb, MAP[0].sub, true);
    }
  };

  function init() {
    var mounts = document.querySelectorAll("[data-demo]");
    if (!mounts.length) return;
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    mounts.forEach(function (el) {
      var key = el.getAttribute("data-demo");
      if (DEMOS[key]) { el.classList.add("pd"); DEMOS[key](el); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
