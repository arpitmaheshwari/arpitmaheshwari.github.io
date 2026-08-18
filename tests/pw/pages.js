// The page list, derived from the repo rather than hand-maintained, so a new
// page is covered the day it exists instead of the day someone remembers.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
// Redirect stubs render nothing of their own — they forward. Covered by
// redirects.spec.js instead, which asserts they land on the right page.
const STUBS = ['case-studies/talon.html', 'lab/hitl.html', 'lab/trustlayer.html'];
function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    const rel = path.relative(ROOT, full).split(path.sep).join('/');
    if (e.isDirectory()) {
      if (/^(\.|node_modules|prototypes|portfolio-sources|tests)/.test(rel.split('/')[0])) continue;
      if (rel.includes('og-images')) continue;
      walk(full, out);
    } else if (e.name.endsWith('.html') && !e.name.startsWith('__')) {
      if (!STUBS.includes(rel)) out.push(rel);
    }
  }
  return out;
}
module.exports = { PAGES: walk(ROOT).sort(), STUBS, ROOT };
