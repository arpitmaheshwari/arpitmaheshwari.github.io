/**
 * loop.js — the decision logic behind eight trust patterns, as code.
 *
 * These are the rules I argue for in design reviews, written as functions so
 * they can be tested instead of debated. Pure, synchronous, zero-dependency:
 * no DOM, no network, no state, no framework. Works in a browser or in Node.
 *
 * The patterns these implement are documented at arpitmaheshwari.com/patterns
 * and shipped in production products (under NDA). This file is the logic only —
 * the visual layer is deliberately left to you.
 *
 * @author  Arpit Maheshwari — arpitmaheshwari.com
 * @license MIT
 */

export const VERSION = '1.0.0';

/* -------------------------------------------------------------------------- */
/* internal helpers                                                            */
/* -------------------------------------------------------------------------- */

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);

function assertUnit(value, name) {
  if (!isNum(value)) {
    throw new TypeError(`${name} must be a finite number, received ${typeof value}`);
  }
  if (value < 0 || value > 1) {
    // The most common mistake is passing a percentage. Say so, rather than
    // failing silently and producing a confident, wrong verb.
    const hint = value > 1 && value <= 100 ? ` — did you mean ${value / 100}? (pass 0–1, not 0–100)` : '';
    throw new RangeError(`${name} must be between 0 and 1, received ${value}${hint}`);
  }
}

const round = (n, dp = 4) => (isNum(n) ? Number(n.toFixed(dp)) : n);

/* -------------------------------------------------------------------------- */
/* 1. decide() — Act / Review / Ignore                                         */
/* -------------------------------------------------------------------------- */

/** Default thresholds. Deliberately conservative: the gap between `review` and
 *  `act` is where a human stays in the loop. Tune per domain, not per demo. */
export const DEFAULT_THRESHOLDS = Object.freeze({ act: 0.85, review: 0.55 });

/**
 * Resolve a confidence score into exactly one verb, before it reaches a screen.
 *
 * The rule this encodes: a naked number ends in a shrug, so a score is never
 * rendered alone. It becomes `act`, `review`, or `ignore` — and each verb
 * carries an obligation. An `act` must be overridable. A `review` must show its
 * reasons. An `ignore` must be honest that it is below the line, not hidden.
 *
 * Reversibility outranks confidence: if an action cannot be undone, the model
 * does not get to auto-act no matter how sure it is. That downgrade is the
 * whole Reversibility / Safe-to-Act pattern in one branch.
 *
 * @param {number} score  Model confidence, 0–1.
 * @param {object} [options]
 * @param {number} [options.act=0.85]        At or above this, act.
 * @param {number} [options.review=0.55]     At or above this, review.
 * @param {boolean} [options.reversible=true] Can the act be undone cheaply?
 * @param {Array<{name: string, value?: number|string}>} [options.signals]
 *        The named signals that drove the score. Required for a `review`:
 *        a review with nothing to review is a dead end.
 * @returns {{
 *   verb: 'act'|'review'|'ignore', score: number, reasons: string[],
 *   requires: {override: boolean, reasons: boolean, disclosure: boolean},
 *   downgraded: boolean, violations: string[], explain: string
 * }}
 */
export function decide(score, options = {}) {
  assertUnit(score, 'score');

  const act = options.act ?? DEFAULT_THRESHOLDS.act;
  const review = options.review ?? DEFAULT_THRESHOLDS.review;
  assertUnit(act, 'options.act');
  assertUnit(review, 'options.review');
  if (review > act) {
    throw new RangeError(`options.review (${review}) cannot exceed options.act (${act})`);
  }

  const reversible = options.reversible !== false; // default true
  const signals = Array.isArray(options.signals) ? options.signals : [];
  const reasons = signals
    .filter((s) => s && typeof s.name === 'string')
    .map((s) => (s.value === undefined ? s.name : `${s.name}: ${s.value}`));

  let verb = score >= act ? 'act' : score >= review ? 'review' : 'ignore';
  let downgraded = false;

  // Reversibility outranks confidence.
  if (verb === 'act' && !reversible) {
    verb = 'review';
    downgraded = true;
  }

  const violations = [];
  if (verb === 'review' && reasons.length === 0) {
    // Surfaced, not thrown: this is a design defect in the caller's config,
    // and it should show up in a test or a lint pass rather than at runtime.
    violations.push('review-without-reasons');
  }

  const requires = {
    override: verb === 'act',    // never an act the user cannot take back
    reasons: verb === 'review',  // never a review without something to read
    disclosure: verb === 'ignore', // never a silent drop
  };

  const explain = downgraded
    ? `Confidence ${round(score, 2)} clears the act threshold (${act}), but the action is irreversible — routed to review.`
    : verb === 'act'
      ? `Confidence ${round(score, 2)} at or above ${act}: safe to act, with an override.`
      : verb === 'review'
        ? `Confidence ${round(score, 2)} sits between ${review} and ${act}: a human decides, with reasons on the card.`
        : `Confidence ${round(score, 2)} below ${review}: below the line — say so rather than guess.`;

  return { verb, score, reasons, requires, downgraded, violations, explain };
}

/* -------------------------------------------------------------------------- */
/* 2. calibrate() — Calibration & Track Record                                 */
/* -------------------------------------------------------------------------- */

/** Below this many observations, a calibration claim is noise. */
export const MIN_CALIBRATION_SAMPLE = 30;
/** Gap (mean confidence − accuracy) beyond which we name the bias. */
export const CALIBRATION_TOLERANCE = 0.05;

/**
 * Score how honest a model's confidence has actually been.
 *
 * "80% sure" is only meaningful if, across the times it said 80%, it was right
 * about 80% of the time. This computes the standard measures of that:
 *
 *   Brier score = mean((confidence − outcome)²). Lower is better; 0 is perfect.
 *   ECE (expected calibration error) = Σ (nᵦ/N) · |accuracyᵦ − confidenceᵦ|,
 *       the sample-weighted average gap across confidence bins.
 *   MCE (maximum calibration error) = the worst single bin's gap.
 *
 * Empty bins are excluded from ECE, as is conventional. With fewer than
 * MIN_CALIBRATION_SAMPLE observations the verdict is `insufficient-data`,
 * because a track record you cannot support is just another confident claim.
 *
 * @param {Array<{confidence: number, correct: boolean}>} history
 * @param {object} [options]
 * @param {number} [options.bins=10] Number of equal-width confidence bins.
 * @returns {{
 *   n: number, brier: number|null, ece: number|null, mce: number|null,
 *   meanConfidence: number|null, accuracy: number|null,
 *   bins: Array<{lo: number, hi: number, n: number, meanConfidence: number|null,
 *                accuracy: number|null, gap: number|null}>,
 *   verdict: 'well-calibrated'|'overconfident'|'underconfident'|'insufficient-data'
 * }}
 */
export function calibrate(history, options = {}) {
  if (!Array.isArray(history)) {
    throw new TypeError(`history must be an array, received ${typeof history}`);
  }
  const binCount = options.bins ?? 10;
  if (!Number.isInteger(binCount) || binCount < 1) {
    throw new RangeError(`options.bins must be a positive integer, received ${binCount}`);
  }

  const bins = Array.from({ length: binCount }, (_, i) => ({
    lo: round(i / binCount), hi: round((i + 1) / binCount),
    n: 0, sumConfidence: 0, hits: 0,
  }));

  let sumConfidence = 0, hits = 0, sumSquaredError = 0;

  history.forEach((row, i) => {
    if (!row || typeof row !== 'object') {
      throw new TypeError(`history[${i}] must be an object`);
    }
    assertUnit(row.confidence, `history[${i}].confidence`);
    if (typeof row.correct !== 'boolean') {
      throw new TypeError(`history[${i}].correct must be a boolean, received ${typeof row.correct}`);
    }
    const outcome = row.correct ? 1 : 0;
    sumConfidence += row.confidence;
    hits += outcome;
    sumSquaredError += (row.confidence - outcome) ** 2;

    // A confidence of exactly 1 belongs in the top bin, not a phantom one.
    const idx = Math.min(Math.floor(row.confidence * binCount), binCount - 1);
    bins[idx].n += 1;
    bins[idx].sumConfidence += row.confidence;
    bins[idx].hits += outcome;
  });

  const n = history.length;
  if (n === 0) {
    return {
      n: 0, brier: null, ece: null, mce: null, meanConfidence: null, accuracy: null,
      bins: bins.map((b) => ({ lo: b.lo, hi: b.hi, n: 0, meanConfidence: null, accuracy: null, gap: null })),
      verdict: 'insufficient-data',
    };
  }

  let ece = 0, mce = 0;
  const shaped = bins.map((b) => {
    if (b.n === 0) return { lo: b.lo, hi: b.hi, n: 0, meanConfidence: null, accuracy: null, gap: null };
    const meanConfidence = b.sumConfidence / b.n;
    const accuracy = b.hits / b.n;
    const gap = Math.abs(accuracy - meanConfidence);
    ece += (b.n / n) * gap;
    mce = Math.max(mce, gap);
    return {
      lo: b.lo, hi: b.hi, n: b.n,
      meanConfidence: round(meanConfidence), accuracy: round(accuracy), gap: round(gap),
    };
  });

  const meanConfidence = sumConfidence / n;
  const accuracy = hits / n;
  const drift = meanConfidence - accuracy;

  const verdict = n < MIN_CALIBRATION_SAMPLE
    ? 'insufficient-data'
    : drift > CALIBRATION_TOLERANCE
      ? 'overconfident'
      : drift < -CALIBRATION_TOLERANCE
        ? 'underconfident'
        : 'well-calibrated';

  return {
    n,
    brier: round(sumSquaredError / n),
    ece: round(ece),
    mce: round(mce),
    meanConfidence: round(meanConfidence),
    accuracy: round(accuracy),
    bins: shaped,
    verdict,
  };
}

/* -------------------------------------------------------------------------- */
/* 3. abstain() — Provenance, Citations & the honest "I don't know"            */
/* -------------------------------------------------------------------------- */

/** Defaults chosen to fail toward humility: every claim cited, two sources,
 *  and a clear majority agreeing before the system speaks at all. */
export const DEFAULT_ABSTENTION_POLICY = Object.freeze({
  minSources: 2,
  minCoverage: 1,     // every claim carries a source, or we don't ship the answer
  minAgreement: 0.6,
});

/**
 * Decide whether the honest move is to say nothing.
 *
 * A fluent, wrong answer costs more than a refusal — once in a
 * capital-allocation workflow, a single confident hallucination undoes the
 * trust the tool spent months earning. So the threshold is set to fail toward
 * humility, and the reasons for refusing are returned so the interface can tell
 * the user *what is missing* instead of shrugging.
 *
 * @param {object} evidence
 * @param {number} evidence.claims     How many assertions the answer makes.
 * @param {number} evidence.cited      How many of those carry a source.
 * @param {number} evidence.sources    Count of distinct sources.
 * @param {number} [evidence.agreement=1] Fraction of sources that agree, 0–1.
 * @param {object} [policy]            Overrides for DEFAULT_ABSTENTION_POLICY.
 * @returns {{
 *   abstain: boolean, coverage: number, reasons: string[],
 *   missing: {sources: number, citations: number}, explain: string
 * }}
 */
export function abstain(evidence, policy = {}) {
  if (!evidence || typeof evidence !== 'object') {
    throw new TypeError(`evidence must be an object, received ${typeof evidence}`);
  }
  const { claims, cited, sources } = evidence;
  const agreement = evidence.agreement ?? 1;

  [['claims', claims], ['cited', cited], ['sources', sources]].forEach(([name, v]) => {
    if (!Number.isInteger(v) || v < 0) {
      throw new TypeError(`evidence.${name} must be a non-negative integer, received ${v}`);
    }
  });
  assertUnit(agreement, 'evidence.agreement');
  if (cited > claims) {
    throw new RangeError(`evidence.cited (${cited}) cannot exceed evidence.claims (${claims})`);
  }

  const p = { ...DEFAULT_ABSTENTION_POLICY, ...policy };
  // No claims means nothing was asserted — there is nothing to abstain from.
  const coverage = claims === 0 ? 1 : cited / claims;

  const reasons = [];
  if (sources < p.minSources) reasons.push(`only ${sources} source${sources === 1 ? '' : 's'} (needs ${p.minSources})`);
  if (coverage < p.minCoverage) reasons.push(`${claims - cited} of ${claims} claims uncited`);
  if (agreement < p.minAgreement) reasons.push(`sources disagree (${round(agreement, 2)} agreement, needs ${p.minAgreement})`);

  const shouldAbstain = reasons.length > 0;

  return {
    abstain: shouldAbstain,
    coverage: round(coverage),
    reasons,
    missing: {
      sources: Math.max(0, p.minSources - sources),
      citations: Math.max(0, claims - cited),
    },
    explain: shouldAbstain
      ? `Not enough to stand behind: ${reasons.join('; ')}. Say so, and name what is missing.`
      : `${cited}/${claims} claims cited across ${sources} sources at ${round(agreement, 2)} agreement — answerable.`,
  };
}

/* -------------------------------------------------------------------------- */
/* 4. disclose() — latency as a trust surface                                  */
/* -------------------------------------------------------------------------- */

/** A spinner shown for under ~200ms reads as a flicker, not as progress. */
export const SPINNER_FLOOR_MS = 200;

/**
 * Decide what to show while a model is still thinking.
 *
 * Latency is not only a performance problem; past a budget it becomes a trust
 * problem, because silence is indistinguishable from failure. This maps elapsed
 * time onto a disclosure stage and says plainly when the user is owed an
 * explanation rather than another rotation of a spinner.
 *
 * @param {number} elapsedMs
 * @param {object} [options]
 * @param {number} [options.budgetMs=1000] The promise you are making.
 * @param {boolean} [options.partialAvailable=false] Any usable partial result?
 * @returns {{stage: 'instant'|'skeleton'|'partial'|'over-budget', tellUser: boolean,
 *            offerPartial: boolean, elapsedMs: number, budgetMs: number, message: string}}
 */
export function disclose(elapsedMs, options = {}) {
  if (!isNum(elapsedMs) || elapsedMs < 0) {
    throw new RangeError(`elapsedMs must be a non-negative number, received ${elapsedMs}`);
  }
  const budgetMs = options.budgetMs ?? 1000;
  if (!isNum(budgetMs) || budgetMs <= 0) {
    throw new RangeError(`options.budgetMs must be a positive number, received ${budgetMs}`);
  }
  const partialAvailable = options.partialAvailable === true;

  let stage;
  if (elapsedMs < SPINNER_FLOOR_MS) stage = 'instant';
  else if (elapsedMs <= budgetMs) stage = partialAvailable ? 'partial' : 'skeleton';
  else stage = 'over-budget';

  const tellUser = stage === 'over-budget';

  const message = stage === 'instant'
    ? 'Show nothing yet — a spinner under 200ms reads as a flicker.'
    : stage === 'skeleton'
      ? 'Show the shape of the answer, so the wait has a subject.'
      : stage === 'partial'
        ? 'Show what is already known, and mark the rest as still arriving.'
        : `Past the ${budgetMs}ms budget: say so, and ${partialAvailable ? 'offer the partial answer' : 'offer a way out'} — silence reads as failure.`;

  return {
    stage,
    tellUser,
    offerPartial: stage === 'over-budget' && partialAvailable,
    elapsedMs,
    budgetMs,
    message,
  };
}

export default { VERSION, decide, calibrate, abstain, disclose };
