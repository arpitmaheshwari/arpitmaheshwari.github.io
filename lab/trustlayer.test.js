/**
 * trustlayer.test.js — the tests for trustlayer.js, and a ~40-line runner.
 *
 * No test framework, because adding one to a zero-dependency library would be
 * the joke telling itself. Runs two ways, same assertions both times:
 *
 *   node lab/trustlayer.test.js          → prints results, exits non-zero on failure
 *   import { run } from './trustlayer.test.js'  → returns results for the browser
 *
 * @license MIT
 */

import {
  decide, calibrate, abstain, disclose,
  VERSION, DEFAULT_THRESHOLDS, MIN_CALIBRATION_SAMPLE,
} from './trustlayer.js';

/* ------------------------------- the runner ------------------------------- */

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

function assert(condition, message) {
  if (!condition) throw new Error(message || 'expected truthy value');
}
function equal(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message || 'values differ'} — expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}
function close(actual, expected, tolerance, message) {
  if (typeof actual !== 'number' || Math.abs(actual - expected) > tolerance) {
    throw new Error(`${message || 'not close enough'} — expected ${expected} ±${tolerance}, got ${actual}`);
  }
}
function throws(fn, message) {
  try { fn(); } catch { return; }
  throw new Error(message || 'expected a throw, got none');
}

/** Runs every test. Returns a plain object so any UI can render it. */
export function run() {
  const results = tests.map(({ name, fn }) => {
    try { fn(); return { name, passed: true, error: null }; }
    catch (error) { return { name, passed: false, error: error.message }; }
  });
  const failed = results.filter((r) => !r.passed).length;
  return { total: results.length, passed: results.length - failed, failed, results };
}

/* ------------------------------- fixtures -------------------------------- */

/**
 * A deterministic, perfectly calibrated history: at confidence c, exactly c of
 * every 10 predictions are correct. ECE on this should be ~0 by construction.
 */
function perfectlyCalibrated() {
  const history = [];
  for (let step = 1; step <= 9; step += 1) {
    const confidence = step / 10;
    for (let i = 0; i < 10; i += 1) history.push({ confidence, correct: i < step });
  }
  return history; // 90 rows
}

/** Always claims 0.9, right only half the time — textbook overconfidence. */
function overconfident() {
  return Array.from({ length: 100 }, (_, i) => ({ confidence: 0.9, correct: i % 2 === 0 }));
}

/* --------------------------------- decide -------------------------------- */

test('decide: high score resolves to act', () => {
  const d = decide(0.92);
  equal(d.verb, 'act', 'verb');
  assert(d.requires.override, 'an act must always carry an override');
});

test('decide: mid score resolves to review', () => {
  equal(decide(0.7, { signals: [{ name: 'recency conflict' }] }).verb, 'review');
});

test('decide: low score resolves to ignore, and says so', () => {
  const d = decide(0.2);
  equal(d.verb, 'ignore');
  assert(d.requires.disclosure, 'an ignore must be disclosed, never silently dropped');
});

test('decide: thresholds are inclusive at the boundary', () => {
  equal(decide(DEFAULT_THRESHOLDS.act).verb, 'act', 'exactly at act threshold');
  equal(decide(DEFAULT_THRESHOLDS.review, { signals: [{ name: 's' }] }).verb, 'review', 'exactly at review threshold');
});

test('decide: irreversible actions never auto-act, however confident', () => {
  const d = decide(0.99, { reversible: false, signals: [{ name: 'irreversible transfer' }] });
  equal(d.verb, 'review', 'verb downgraded');
  assert(d.downgraded, 'downgrade is reported, not hidden');
  assert(!d.requires.override, 'a review needs reasons, not an override');
});

test('decide: reversibility outranks even a perfect score', () => {
  equal(decide(1, { reversible: false, signals: [{ name: 'x' }] }).verb, 'review');
});

test('decide: a review without reasons is flagged as a defect', () => {
  const d = decide(0.7);
  assert(d.violations.includes('review-without-reasons'), 'violation surfaced');
});

test('decide: named signals become human-readable reasons', () => {
  const d = decide(0.7, { signals: [{ name: 'margin', value: '12%' }, { name: 'stale data' }] });
  equal(d.reasons.length, 2);
  equal(d.reasons[0], 'margin: 12%');
  equal(d.reasons[1], 'stale data');
});

test('decide: custom thresholds are honoured', () => {
  equal(decide(0.5, { act: 0.4, review: 0.2 }).verb, 'act');
});

test('decide: percentages are rejected with a useful hint', () => {
  try {
    decide(87);
    throw new Error('expected a throw for a 0–100 input');
  } catch (error) {
    assert(/0.87/.test(error.message), 'error should suggest the 0–1 equivalent');
  }
});

test('decide: invalid inputs throw rather than guess', () => {
  throws(() => decide('0.9'), 'string score');
  throws(() => decide(NaN), 'NaN score');
  throws(() => decide(-0.1), 'negative score');
  throws(() => decide(0.9, { act: 0.5, review: 0.8 }), 'review above act');
});

test('decide: explanation names the rule that fired', () => {
  assert(/irreversible/.test(decide(0.95, { reversible: false, signals: [{ name: 's' }] }).explain));
});

/* -------------------------------- calibrate ------------------------------- */

test('calibrate: empty history is insufficient, not zero', () => {
  const c = calibrate([]);
  equal(c.n, 0);
  equal(c.brier, null, 'no fabricated score');
  equal(c.verdict, 'insufficient-data');
});

test('calibrate: small samples refuse to render a verdict', () => {
  const c = calibrate(Array.from({ length: MIN_CALIBRATION_SAMPLE - 1 }, () => ({ confidence: 0.8, correct: true })));
  equal(c.verdict, 'insufficient-data', 'a track record you cannot support is just another claim');
});

test('calibrate: a perfectly calibrated history scores ~0 ECE', () => {
  const c = calibrate(perfectlyCalibrated());
  equal(c.n, 90);
  close(c.ece, 0, 0.001, 'ECE');
  equal(c.verdict, 'well-calibrated');
});

test('calibrate: overconfidence is named', () => {
  const c = calibrate(overconfident());
  equal(c.verdict, 'overconfident');
  close(c.meanConfidence - c.accuracy, 0.4, 0.001, 'confidence exceeds accuracy by 0.4');
  close(c.ece, 0.4, 0.001, 'ECE equals the gap when all mass is in one bin');
});

test('calibrate: underconfidence is named too', () => {
  const c = calibrate(Array.from({ length: 100 }, () => ({ confidence: 0.3, correct: true })));
  equal(c.verdict, 'underconfident');
});

test('calibrate: Brier score is 0 for perfect certainty that is correct', () => {
  close(calibrate(Array.from({ length: 40 }, () => ({ confidence: 1, correct: true }))).brier, 0, 1e-9);
});

test('calibrate: Brier score is 1 for perfect certainty that is wrong', () => {
  close(calibrate(Array.from({ length: 40 }, () => ({ confidence: 1, correct: false }))).brier, 1, 1e-9);
});

test('calibrate: Brier score is 0.25 for a coin flip claimed at 0.5', () => {
  close(calibrate(Array.from({ length: 40 }, (_, i) => ({ confidence: 0.5, correct: i % 2 === 0 }))).brier, 0.25, 1e-9);
});

test('calibrate: confidence of exactly 1 lands in the top bin', () => {
  const c = calibrate([{ confidence: 1, correct: true }], { bins: 10 });
  equal(c.bins[9].n, 1, 'top bin');
  equal(c.bins.length, 10, 'no phantom eleventh bin');
});

test('calibrate: empty bins are excluded from ECE, not counted as perfect', () => {
  const c = calibrate(overconfident(), { bins: 10 });
  const populated = c.bins.filter((b) => b.n > 0);
  equal(populated.length, 1, 'all mass in one bin');
  close(c.ece, populated[0].gap, 1e-9, 'ECE reduces to that bin');
});

test('calibrate: MCE reports the worst bin, ECE the weighted average', () => {
  const history = [
    // A big, mildly-off bin plus a small, badly-off one: ECE should sit below MCE.
    ...Array.from({ length: 90 }, (_, i) => ({ confidence: 0.5, correct: i % 2 === 0 })),
    ...Array.from({ length: 10 }, () => ({ confidence: 0.95, correct: false })),
  ];
  const c = calibrate(history);
  assert(c.mce >= c.ece, 'the worst bin is at least as bad as the average');
});

test('calibrate: bin count is configurable', () => {
  equal(calibrate(perfectlyCalibrated(), { bins: 5 }).bins.length, 5);
});

test('calibrate: malformed rows throw rather than skew the score', () => {
  throws(() => calibrate([{ confidence: 0.8 }]), 'missing correct');
  throws(() => calibrate([{ confidence: 0.8, correct: 'yes' }]), 'non-boolean outcome');
  throws(() => calibrate([{ confidence: 80, correct: true }]), 'percentage confidence');
  throws(() => calibrate('nope'), 'non-array history');
  throws(() => calibrate([], { bins: 0 }), 'zero bins');
});

/* --------------------------------- abstain -------------------------------- */

test('abstain: fully cited, multi-source, agreeing evidence answers', () => {
  const a = abstain({ claims: 4, cited: 4, sources: 3, agreement: 0.9 });
  equal(a.abstain, false);
  equal(a.coverage, 1);
});

test('abstain: a single uncited claim is enough to hold the answer', () => {
  const a = abstain({ claims: 4, cited: 3, sources: 3, agreement: 1 });
  equal(a.abstain, true);
  assert(a.reasons.some((r) => /uncited/.test(r)), 'names what is missing');
  equal(a.missing.citations, 1);
});

test('abstain: one source is not corroboration', () => {
  const a = abstain({ claims: 2, cited: 2, sources: 1, agreement: 1 });
  equal(a.abstain, true);
  equal(a.missing.sources, 1);
});

test('abstain: disagreeing sources trigger a refusal', () => {
  equal(abstain({ claims: 2, cited: 2, sources: 4, agreement: 0.4 }).abstain, true);
});

test('abstain: several failures are all reported, not just the first', () => {
  const a = abstain({ claims: 3, cited: 1, sources: 1, agreement: 0.2 });
  equal(a.reasons.length, 3, 'tell the user everything that is missing');
});

test('abstain: zero claims asserts nothing, so there is nothing to abstain from', () => {
  const a = abstain({ claims: 0, cited: 0, sources: 2 });
  equal(a.coverage, 1);
  equal(a.abstain, false);
});

test('abstain: policy is overridable for lower-stakes domains', () => {
  const evidence = { claims: 4, cited: 2, sources: 1, agreement: 1 };
  equal(abstain(evidence).abstain, true, 'strict by default');
  equal(abstain(evidence, { minSources: 1, minCoverage: 0.5 }).abstain, false, 'relaxed on request');
});

test('abstain: agreement defaults to full when unspecified', () => {
  equal(abstain({ claims: 1, cited: 1, sources: 2 }).abstain, false);
});

test('abstain: impossible evidence throws', () => {
  throws(() => abstain({ claims: 1, cited: 2, sources: 2 }), 'more citations than claims');
  throws(() => abstain({ claims: 1.5, cited: 1, sources: 2 }), 'fractional claims');
  throws(() => abstain(null), 'null evidence');
});

/* -------------------------------- disclose -------------------------------- */

test('disclose: under 200ms, show nothing', () => {
  const d = disclose(120);
  equal(d.stage, 'instant');
  assert(/flicker/.test(d.message));
});

test('disclose: inside budget with no partial, show a skeleton', () => {
  equal(disclose(600, { budgetMs: 1000 }).stage, 'skeleton');
});

test('disclose: inside budget with a partial, show the partial', () => {
  equal(disclose(600, { budgetMs: 1000, partialAvailable: true }).stage, 'partial');
});

test('disclose: past budget, the user is owed an explanation', () => {
  const d = disclose(4000, { budgetMs: 1000 });
  equal(d.stage, 'over-budget');
  assert(d.tellUser, 'silence reads as failure');
  assert(/silence/.test(d.message));
});

test('disclose: past budget with a partial, offer the partial', () => {
  assert(disclose(4000, { budgetMs: 1000, partialAvailable: true }).offerPartial);
});

test('disclose: exactly at budget is still inside it', () => {
  equal(disclose(1000, { budgetMs: 1000 }).stage, 'skeleton');
});

test('disclose: invalid timings throw', () => {
  throws(() => disclose(-1), 'negative elapsed');
  throws(() => disclose(100, { budgetMs: 0 }), 'zero budget');
});

/* ------------------------------ module surface ---------------------------- */

test('module: exports a semver version', () => {
  assert(/^\d+\.\d+\.\d+$/.test(VERSION), `VERSION should be semver, got ${VERSION}`);
});

/* ------------------------------- node runner ------------------------------ */

const isNode = typeof process !== 'undefined' && process.versions && process.versions.node;
if (isNode && process.argv[1] && process.argv[1].endsWith('trustlayer.test.js')) {
  const { total, passed, failed, results } = run();
  results.filter((r) => !r.passed).forEach((r) => console.error(`FAIL  ${r.name}\n      ${r.error}`));
  console.log(`\ntrustlayer.js v${VERSION} — ${passed}/${total} passed${failed ? `, ${failed} failed` : ''}`);
  process.exit(failed ? 1 : 0);
}
