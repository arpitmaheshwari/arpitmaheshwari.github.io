# partials/pages/ — the source of every classic page

Since 2026-09-13 the 35 classic pages are **rendered**, not edited: `tools/build-pages.py` puts each
source here into `partials/pages/_layout.html` (the one frame: doctype, head wrapper, body class, skip link,
nav, footer, closing tags) and writes the page to its public path. Nav and footer come from
`partials/` through the same code `build-partials.py` uses; cache stamps are applied on the way.

**To change a page:** edit `partials/pages/<its path>`, run `python3 tools/build-pages.py`, commit both.
**To change the frame for every page:** edit `partials/pages/_layout.html`, run the build.
**Never edit the public page directly** — the `pages-built-check` gate blocks the push until the
edit is in its source.

A source page is a one-line header and four verbatim regions:

    <!--page body_class="p-home" footer_note="No copyright · Design is for all"-->
    <!--head--> … <!--/head-->          everything inside <head> (still per page tonight)
    <!--pre-nav--> … <!--/pre-nav-->    what sits between the skip link and the nav
    <!--content--> … <!--/content-->    from after </nav> to before <footer
    <!--tail--> … <!--/tail-->          scripts after </footer>

The first build reproduced all 35 pages byte for byte (`build-pages.py --check` → 0 differ).
Next step, separately proven: fold the head lines every page shares into the layout.
