// The page list, derived from the repo rather than hand-maintained, so a new
// page is covered the day it exists instead of the day someone remembers.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

// Forwarding stubs are DETECTED, not listed. Hardcoding their filenames put a
// retired term in this file (canon §1) and, worse, meant a new stub would be
// silently uncovered. A stub declares itself with a meta refresh; that is the
// property to test for.
const isStub = p => /<meta[^>]+http-equiv=["']refresh["']/i.test(fs.readFileSync(p, 'utf8'));

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    const rel = path.relative(ROOT, full).split(path.sep).join('/');
    if (e.isDirectory()) {
      if (/^(\.|node_modules|prototypes|portfolio-sources|tests)/.test(rel.split('/')[0])) continue;
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
  return m ? m[1].trim() : null;
}

module.exports = { PAGES, STUBS, ROOT, stubTarget };
