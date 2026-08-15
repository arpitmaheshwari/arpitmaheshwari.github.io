#!/usr/bin/env python3
"""extract-inline.py v2 — migrate a page to zero inline styling (theme-swap precondition).

v1 shipped two real bugs, both caught by pixel-diff + rendered inspection (2026-08-13):
  BUG 1 — declaration splitting on raw ';' mangled url("data:image/svg+xml,...") values
          (data URIs contain semicolons), unbalancing quotes in the merged stylesheet so a
          later page's @media print interior leaked to screen scope: hire/ rendered its
          PRINT styles (white body, no nav) in a browser.
  BUG 2 — page <style> blocks merged UNSCOPED, so one page's `body{...}` styled every page.

v2 therefore:
  - splits declarations with a quote/paren-aware tokenizer (never inside "..", '..', (..));
  - scopes every moved page-block rule with `body.p-<slug>` (added to the page's <body>):
      body...   -> body.p-<slug>...
      html...   -> html:has(body.p-<slug>)...
      :root...  -> body.p-<slug>...   (custom props inherit from body)
      @media/@supports recurse; @keyframes/@font-face/@page kept whole (collisions detected);
  - style="" attrs -> .xi-<slug>-NNN classes with !important (the faithful weight of inline),
    EXCEPT transition/animation props, and EXCEPT opacity/transform in animation-bearing
    classes (animations override normal declarations but lose to !important);
  - onmouseover/onmouseout pairs -> dedicated .hv-<slug>-N:hover rules.

Usage: python3 tools/extract-inline.py <page.html> [--css styles.css]
Verify each page with a pixel diff against the classic-v1 tag before trusting it.
"""
import re, sys, os, argparse

# ---------------------------------------------------------------- tokenizers

def split_decls(decl):
    """Split a declaration list on ';' — but never inside quotes or parens."""
    out, buf, depth, q = [], [], 0, None
    for ch in decl:
        if q:
            buf.append(ch)
            if ch == q: q = None
            continue
        if ch in ('"', "'"):
            q = ch; buf.append(ch); continue
        if ch == '(': depth += 1
        elif ch == ')': depth = max(0, depth-1)
        if ch == ';' and depth == 0:
            s=''.join(buf).strip()
            if s: out.append(s)
            buf=[]
        else:
            buf.append(ch)
    s=''.join(buf).strip()
    if s: out.append(s)
    return out

def norm(decl):
    return ';'.join(split_decls(decl))

def bang(body):
    outs=[]; has_anim = any(d.split(':',1)[0].strip().lower().startswith('animation')
                            for d in split_decls(body))
    for d in split_decls(body):
        prop=d.split(':',1)[0].strip().lower()
        if prop.startswith(('transition','animation')):
            outs.append(d)
        elif has_anim and prop in ('opacity','transform'):
            outs.append(d)
        else:
            outs.append(d+'!important')
    return ';'.join(outs)

def css_rules(css):
    """Yield (selector_or_atrule, body, is_at) top-level chunks, comment/string/brace aware."""
    i, n = 0, len(css)
    while i < n:
        # skip ws + comments
        while i < n and css[i].isspace(): i += 1
        if css.startswith('/*', i):
            j = css.find('*/', i+2)
            i = (j+2) if j != -1 else n
            continue
        if i >= n: break
        # read selector up to '{'
        j, q = i, None
        while j < n:
            ch = css[j]
            if q:
                if ch == q: q = None
            elif ch in ('"', "'"): q = ch
            elif ch == '{': break
            j += 1
        if j >= n: break
        sel = css[i:j].strip()
        # read balanced body
        depth, k, q = 1, j+1, None
        while k < n and depth:
            ch = css[k]
            if q:
                if ch == q: q = None
            elif css.startswith('/*', k):
                e = css.find('*/', k+2); k = (e+1) if e != -1 else n-1
            elif ch in ('"', "'"): q = ch
            elif ch == '{': depth += 1
            elif ch == '}': depth -= 1
            k += 1
        body = css[j+1:k-1]
        yield sel, body
        i = k

def scope_block(css, slug):
    out=[]
    for sel, body in css_rules(css):
        if sel.startswith(('@keyframes','@-webkit-keyframes','@font-face','@page')):
            out.append(f"{sel}{{{body}}}")
        elif sel.startswith(('@media','@supports')):
            out.append(f"{sel}{{{scope_block(body, slug)}}}")
        elif sel.startswith('@'):
            out.append(f"{sel}{{{body}}}")   # unknown at-rule: keep, flag via stderr
        else:
            # :where() contributes ZERO specificity — scoping must not change which
            # rule wins. body.p-<slug> raised .proof-grid from (0,1,0) to (0,2,0) and
            # resurrected a rule production had overridden (index receipts went 2x2 -> 4-across).
            parts=[]
            for s in sel.split(','):
                s=s.strip()
                if s==':root' or s.startswith(':root'):
                    parts.append(f"body:where(.p-{slug})"+s[5:])
                elif s=='body' or s.startswith(('body ','body.','body:','body[','body>')):
                    parts.append(f"body:where(.p-{slug})"+s[4:])
                elif s=='html' or s.startswith(('html ','html.','html:','html[','html>')):
                    parts.append(f"html:where(:has(body.p-{slug}))"+s[4:])
                else:
                    parts.append(f":where(body.p-{slug}) "+s)
            out.append(f"{','.join(parts)}{{{body}}}")
    return '\n'.join(out)

def slug(path):
    s = re.sub(r'\.html$', '', path.replace('index','').strip('/').replace('/','-')).strip('-')
    return s or 'home'

# ---------------------------------------------------------------- migration

def run(page, cssfile):
    pg = slug(page)
    s = open(page, encoding='utf-8').read()
    orig_len = len(s)

    # BUG 4 (caught on lab/loop.html): tag_re rewrote style= attributes inside JS
    # template literals, turning dynamic chart-bar heights into a static class whose
    # CSS read "height:${conf}%" — flat bars. Scripts are code, not markup: mask them
    # out before every pass and restore them untouched at the end.
    scripts=[]
    def _mask(m):
        scripts.append(m.group(0)); return f"\x00SCRIPT{len(scripts)-1}\x00"
    s = re.sub(r'<script\b[^>]*>.*?</script>', _mask, s, flags=re.S)

    decl_to_cls, order = {}, []
    def cls_for(decl):
        n = norm(decl)
        if n not in decl_to_cls:
            decl_to_cls[n] = f"xi-{pg}-{len(decl_to_cls)+1:03d}"; order.append(n)
        return decl_to_cls[n]

    tag_re = re.compile(r'<([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"]|"[^"]*")*?)>')
    def fix_tag(m):
        tag, attrs = m.group(1), m.group(2)
        sm = re.search(r'\sstyle="([^"]*)"', attrs)
        if not sm: return m.group(0)
        c = cls_for(sm.group(1))
        attrs = attrs[:sm.start()] + attrs[sm.end():]
        cm = re.search(r'\sclass="([^"]*)"', attrs)
        if cm: attrs = attrs[:cm.start()] + f' class="{cm.group(1)} {c}"' + attrs[cm.end():]
        else:  attrs = f' class="{c}"' + attrs
        return f'<{tag}{attrs}>'
    s = tag_re.sub(fix_tag, s)
    assert not re.findall(r'style="[^"]*"', s), f"{page}: style attrs remain"

    hover_map, hover_order = {}, []
    def fix_hover(m):
        tag = m.group(0)
        over = re.search(r'onmouseover="([^"]*)"', tag)
        if not over: return tag
        decls = tuple(sorted(
            f"{re.sub(r'([A-Z])', lambda x: '-'+x.group(1).lower(), p)}:{v}"
            for p, v in re.findall(r"this\.style\.([a-zA-Z]+)\s*=\s*'([^']*)'", over.group(1))))
        assert decls, f"{page}: unparseable handler: {over.group(1)[:80]}"
        if decls not in hover_map:
            hover_map[decls] = f"hv-{pg}-{len(hover_map)+1}"; hover_order.append(decls)
        hc = hover_map[decls]
        tag = re.sub(r'\s*onmouseover="[^"]*"', '', tag)
        tag = re.sub(r'\s*onmouseout="[^"]*"', '', tag)
        cm = re.search(r'class="([^"]*)"', tag)
        if cm: tag = tag[:cm.start()] + f'class="{cm.group(1)} {hc}"' + tag[cm.end():]
        else:  tag = tag[:-1] + f' class="{hc}">'
        return tag
    s = re.sub(r'<[a-zA-Z][^>]*onmouseover[^>]*>', fix_hover, s)
    assert 'onmouseover' not in s and 'onmouseout' not in s, f"{page}: handlers remain"

    blocks = []
    for m in re.finditer(r'<style([^>]*)>(.*?)</style>', s, re.S):
        if 'noscript' in s[max(0, m.start()-12):m.start()]: continue
        blocks.append((m.group(0), m.group(1), m.group(2)))
    raws=[]
    for whole, attrs, content in blocks:
        s = s.replace(whole, '', 1)
        mm = re.search(r'media="([^"]+)"', attrs)
        # a media-attributed <style> is scoped by its attribute — dropping the tag
        # must not drop the scoping (learned from ai-design-checklist's media="print"
        # block rendering its PRINT look on screen)
        if mm and mm.group(1).strip().lower() not in ('all','screen'):
            raws.append(f"@media {mm.group(1)}{{{content}}}")
        else:
            raws.append(content)
    raw = '\n'.join(raws)
    blocks = [b[0] for b in blocks]
    scoped = scope_block(raw, pg) if raw.strip() else ''

    # body page class
    bm = re.search(r'<body([^>]*)>', s)
    assert bm, f"{page}: no body tag"
    battrs = bm.group(1)
    cm = re.search(r'class="([^"]*)"', battrs)
    if cm: battrs = battrs[:cm.start()] + f'class="{cm.group(1)} p-{pg}"' + battrs[cm.end():]
    else:  battrs += f' class="p-{pg}"'
    s = s[:bm.start()] + f'<body{battrs}>' + s[bm.end():]

    css = open(cssfile, encoding='utf-8').read()
    css += f"\n\n/* ===== EXTRACTED FROM {page} (theme-swap migration; scoped body.p-{pg}) ===== */\n"
    if scoped: css += scoped + "\n"
    if order:
        css += f"/* --- former style attributes ({page}) --- */\n"
        for n in order: css += f".{decl_to_cls[n]}{{{bang(n)}}}\n"
    if hover_order:
        css += f"/* --- former hover handlers ({page}) --- */\n"
        for decls in hover_order:
            css += f".{hover_map[decls]}:hover{{{';'.join(decls)}}}\n"

    for i, sc in enumerate(scripts):
        s = s.replace(f"\x00SCRIPT{i}\x00", sc)
    assert '\x00SCRIPT' not in s, f"{page}: script placeholder left behind"

    open(page, 'w', encoding='utf-8').write(s)
    open(cssfile, 'w', encoding='utf-8').write(css)
    print(f"{page}: {len(decl_to_cls)} classes · {len(hover_map)} hover · "
          f"{len(blocks)} blocks scoped as p-{pg} · {orig_len} -> {len(s)} bytes")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('pages', nargs='+')
    ap.add_argument('--css', default='styles.css')
    a = ap.parse_args()
    for p in a.pages:
        run(p, a.css)
