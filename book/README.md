# The Monograph — book-theme portfolio

An interactive "bound book" portfolio that lives at `/book/`, parallel to the
main static site at `/`. Self-contained: cover → contents → chapters, with a
3D page-flip on desktop and a single-page reader on mobile.

## Files
- `index.html` — boots the app (React production UMD + `portfolio.js`, no in-browser Babel)
- `portfolio.js` — pre-compiled app + content (see "Rebuilding" below)
- `book.css` — all visual styling (namespace `--bk-*` / `.bk-*`)
- `image-slot.js` — graceful image-placeholder custom element for figures/plates

## Locked theme
Accent **claret `#8E3942`**, type pairing **Playfair Display · Spectral**,
paper warmth 70%, comfy margins. The authoring "tweaks" panel was removed for
the shipped build. Only 4 font families load: Playfair Display, Spectral,
Caveat (margin notes), Spline Sans Mono (labels).

## Rebuilding `portfolio.js`
`portfolio.js` is the JSX (book content + app shell) transpiled once with Babel
so visitors never download an in-browser compiler. To regenerate after editing
content/app source:

1. Keep JSX source (`book-content.jsx` + the app component) somewhere out of the repo.
2. `npx @babel/cli --presets @babel/preset-react src.jsx -o portfolio.js`
3. Confirm with `node --check portfolio.js`, then preview `/book/`.

No build tooling is committed to the repo — the shipped artifact is plain JS + CSS + HTML.
