// The page list, derived from the repo rather than hand-maintained, so a new
// page is covered the day it exists instead of the day someone remembers.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

// Forwarding stubs are DETECTED, not listed. Hardcoding their filenames put a
// retired term in this file (canon §1) and, worse, meant a new stub would be
// silently uncovered. A stub declares itself with a meta refresh; that is the
// property to test for.
// A stub forwards two ways: a meta refresh, or a script calling
// location.replace on load. /folio/ is the second kind — it shows "Opening
// the portfolio…" for a moment and leaves. Baselining that is racing the
// redirect, and it started failing the instant the redirect got faster.
// Nothing about how it LOOKS is worth a screenshot; where it GOES is covered
// by redirects.spec.js.
const isStub = p => {
  const html = fs.readFileSync(p, 'utf8');
  if (/<meta[^>]+http-equiv=["']refresh["']/i.test(html)) return true;
  // A script redirect alone is not enough: the homepage calls
  // location.replace inside a handler to switch to the book edition, and a
  // bare regex marked it a stub and broke its own redirect test. A stub is a
  // page with essentially nothing ON it — that is the property to test.
  if (!/location\.replace\(/.test(html)) return false;
  const visible = html
    .replace(/<(script|style|noscript|svg)\b[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return visible.length < 200;
};

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    const rel = path.relative(ROOT, full).split(path.sep).join('/');
    if (e.isDirectory()) {
      // partials/ holds the SOURCE fragments for the shared nav and footer.
      // They are not pages and have no baseline; counting them made the
      // dyslexia-toggle census report 38/41 when the real figure was 38/39.
      if (/^(\.|node_modules|prototypes|portfolio-sources|tests|partials)/.test(rel.split('/')[0])) continue;
      if (rel.includes('og-images')) continue;
      walk(full, out);
    } else if (e.name.endsWith('.html') && !e.name.startsWith('__')) {
      out.push(rel);
    }
  }
  return out;
}

const ALL = walk(ROOT).sort();
const STUBS = ALL.filter(r => isStub(path.join(ROOT, r)));
const PAGES = ALL.filter(r => !STUBS.includes(r));

// Where each stub says it goes — read from the page, not from a map I maintain.
function stubTarget(rel) {
  const html = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  const m = html.match(/<meta[^>]+http-equiv=["']refresh["'][^>]+content=["'][^;]*;\s*url=([^"']+)["']/i);
  if (m) return m[1].trim();
  const j = html.match(/location\.replace\(\s*['"]([^'"]+)['"]/);
  return j ? j[1].trim() : null;
}

module.exports = { PAGES, STUBS, ROOT, stubTarget };
