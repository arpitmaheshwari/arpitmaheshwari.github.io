/**
 * trustlint.js — a deterministic linter for the trust properties of an AI answer.
 *
 * What it does: reads an answer as text and flags the patterns that make a
 * fluent answer untrustworthy — numbers with no source, absolutes, superlatives
 * nobody can check, hedging used as decoration, and the big one: asserting
 * confidently when there was nothing to assert from.
 *
 * What it explicitly does NOT do, and cannot: judge whether a claim is TRUE.
 * It has no model, no retrieval, no network. It is a linter, not a benchmark —
 * the same relationship ESLint has to correctness. A clean lint pass means the
 * answer is shaped honestly, not that it is right. Anything that claimed
 * otherwise from regexes alone would be committing the exact sin it audits.
 *
 * @author  Arpit Maheshwari
 * @license MIT
 */

export const VERSION = '1.0.0';

/* -------------------------------------------------------------------------- */
/* patterns                                                                    */
/* -------------------------------------------------------------------------- */

/** A citation: [1], [cap table], (source: X), or a bare URL. */
const CITATION = /\[[^\]]+\]|\((?:source|ref|per|via)\b[^)]*\)|https?:\/\/\S+/i;

/** A number that asserts something: money, percentages, multiples, magnitudes,
 *  or any figure of 2+ digits — but not a bare year, which is usually context. */
const NUMERIC_CLAIM = /[$£€]\s?\d[\d,.]*|\d[\d,.]*\s?%|\b\d[\d,.]*\s?(?:x|×|bps|bn|million|billion|trillion|k)\b|\b(?!19\d{2}\b|20\d{2}\b)\d{2,}[\d,.]*\b/i;

const ABSOLUTE = /\b(always|never|guaranteed?|certainly|definitely|undoubtedly|impossible|100\s?%|zero\s+risk|no\s+risk|every\s+time)\b/i;
const HEDGE = /\b(might|may|possibly|perhaps|probably|likely|unlikely|appears?\s+to|seems?\s+to|roughly|approximately|arguably|I\s+think|I\s+believe)\b/i;
const SUPERLATIVE = /\b(best|worst|fastest|slowest|largest|smallest|cheapest|optimal|unmatched|industry[-\s]leading|state[-\s]of[-\s]the[-\s]art)\b/i;
// Apostrophes: BOTH forms. The straight-only version returned "no abstention found" for
// "I don’t know" — the curly form any word processor, any CMS and this site itself
// produce. A linter whose job is to notice honest abstention was blind to it in exactly
// the text a careful writer pastes in. Found 2026-08-30 while curling the JS surfaces.
const ABSTENTION = /\b(I\s+(?:don['\u2019]t|do not|cannot|can['\u2019]t)\s+(?:know|say|determine|verify)|insufficient\s+(?:data|evidence|sources?)|not\s+enough\s+(?:data|evidence|sources?)|unable\s+to\s+verify|no\s+(?:source|evidence)\s+(?:for|to)|cannot\s+be\s+determined)\b/i;

/** Every rule this linter can report, so a UI can document itself. */
export const RULES = Object.freeze([
  { id: 'uncited-number', severity: 'high', describe: 'A figure is asserted with no source in the same sentence.' },
  { id: 'no-sources-no-abstention', severity: 'high', describe: 'The answer makes claims with no citation anywhere, and never says it is unsure.' },
  { id: 'absolute-claim', severity: 'high', describe: 'Absolute language (“always”, “guaranteed”) that no evidence can support.' },
  { id: 'uncited-superlative', severity: 'medium', describe: 'A superlative (“fastest”, “best”) with nothing behind it.' },
  { id: 'decorative-hedge', severity: 'medium', describe: 'Hedging in a sentence that cites nothing — softened language standing in for evidence.' },
  { id: 'over-hedged', severity: 'low', describe: 'Most sentences hedge, which reads as evasion rather than care.' },
  { id: 'honest-abstention', severity: 'info', describe: 'The answer states plainly where it cannot go. This is the behaviour to keep.' },
]);

const severityOf = (id) => (RULES.find((r) => r.id === id) || {}).severity || 'low';

const clip = (s, n = 120) => {
  const t = s.trim().replace(/\s+/g, ' ');
  return t.length > n ? `${t.slice(0, n - 1)}…` : t;
};

/* -------------------------------------------------------------------------- */
/* lint()                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Lint an AI answer for trust properties.
 *
 * @param {string} answer  The model's answer, as plain text.
 * @param {object} [options]
 * @param {number} [options.sources] Distinct sources the system actually had.
 *        Omit to infer from citation markers found in the text.
 * @param {number} [options.hedgeRatioLimit=0.5] Fraction of hedging sentences
 *        above which the answer is flagged as evasive.
 * @returns {{
 *   sentences: number, claimSentences: number, citedClaims: number,
 *   coverage: number, sources: number, findings: Array<{rule: string,
 *   severity: string, excerpt: string, why: string}>,
 *   counts: {high: number, medium: number, low: number, info: number},
 *   verdict: 'do-not-ship'|'needs-review'|'shaped-honestly'|'empty',
 *   limitations: string
 * }}
 */
export function lint(answer, options = {}) {
  if (typeof answer !== 'string') {
    throw new TypeError(`answer must be a string, received ${typeof answer}`);
  }
  const hedgeRatioLimit = options.hedgeRatioLimit ?? 0.5;

  const text = answer.trim();
  const limitations = 'Deterministic text analysis only: this checks the SHAPE of an answer, never whether it is true. A clean pass is not a correctness claim.';

  if (!text) {
    return {
      sentences: 0, claimSentences: 0, citedClaims: 0, coverage: 1, sources: 0,
      findings: [], counts: { high: 0, medium: 0, low: 0, info: 0 },
      verdict: 'empty', limitations,
    };
  }

  const sentences = text.split(/(?<=[.!?])\s+/).filter((s) => s.trim());
  const citationMatches = text.match(new RegExp(CITATION.source, 'gi')) || [];
  const inferredSources = new Set(citationMatches.map((c) => c.toLowerCase())).size;
  const sources = Number.isInteger(options.sources) ? options.sources : inferredSources;

  const findings = [];
  const add = (rule, excerpt, why) => findings.push({ rule, severity: severityOf(rule), excerpt, why });

  let claimSentences = 0;
  let citedClaims = 0;
  let hedgeSentences = 0;

  sentences.forEach((sentence) => {
    const hasCitation = CITATION.test(sentence);
    const hasNumber = NUMERIC_CLAIM.test(sentence);
    const hedged = HEDGE.test(sentence);
    if (hedged) hedgeSentences += 1;

    if (hasNumber) {
      claimSentences += 1;
      if (hasCitation) citedClaims += 1;
      else add('uncited-number', clip(sentence), 'A reader cannot check this figure, so they must either trust it blindly or discard the whole answer.');
    }

    if (ABSOLUTE.test(sentence)) {
      add('absolute-claim', clip(sentence), 'Absolutes cannot be evidenced. One counter-example destroys the credibility of everything around it.');
    }

    if (SUPERLATIVE.test(sentence) && !hasCitation) {
      add('uncited-superlative', clip(sentence), 'A ranking claim with no source is marketing language in an answer that is meant to be auditable.');
    }

    if (hedged && !hasCitation && hasNumber) {
      add('decorative-hedge', clip(sentence), 'Hedging is honest when evidence is thin and evasive when it replaces evidence. Cite it or abstain.');
    }
  });

  const hasAbstention = ABSTENTION.test(text);
  if (hasAbstention) {
    const sentence = sentences.find((s) => ABSTENTION.test(s)) || '';
    add('honest-abstention', clip(sentence), 'Naming the limit is what earns the trust the rest of the answer spends.');
  }

  if (sources === 0 && claimSentences > 0 && !hasAbstention) {
    add('no-sources-no-abstention', clip(sentences[0]), 'The system had nothing to stand on and said nothing about that. This is the failure that costs the most trust per incident.');
  }

  const hedgeRatio = sentences.length ? hedgeSentences / sentences.length : 0;
  if (hedgeRatio > hedgeRatioLimit && sentences.length >= 3) {
    add('over-hedged', `${hedgeSentences} of ${sentences.length} sentences hedge`, 'Uniform hedging carries no information: if everything is uncertain, the user cannot tell what actually is.');
  }

  const counts = { high: 0, medium: 0, low: 0, info: 0 };
  findings.forEach((f) => { counts[f.severity] += 1; });

  const verdict = counts.high > 0 ? 'do-not-ship' : counts.medium > 0 ? 'needs-review' : 'shaped-honestly';

  return {
    sentences: sentences.length,
    claimSentences,
    citedClaims,
    coverage: claimSentences === 0 ? 1 : Number((citedClaims / claimSentences).toFixed(4)),
    sources,
    findings,
    counts,
    verdict,
    limitations,
  };
}

export default { VERSION, RULES, lint };
