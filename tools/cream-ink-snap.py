#!/usr/bin/env python3
"""cream-ink-snap — TRIAGE AID ONLY. Reports ink literals that would be illegible
if they were painted on a cream surface.

READ THIS BEFORE TRUSTING IT. This tool cannot know what is actually painted
behind an element: that requires pixels, and tools/contrast-audit.py already
measures them. On its first run this tool flagged `color:#fff` inside the O2 and
AdTech product mockups — white on those products' own brand-blue buttons, which
is correct — because it compared that ink against the PAGE ground. Acting on its
output would have wrecked the reconstructions.

So: fixes are driven by contrast-audit (which knows the real ground). This tool
exists to answer a narrower question quickly — "which literals in the source
could never work on paper?" — as a starting list for triage. It never writes
without --write, and it exempts the product-mockup namespaces, whose palettes
belong to the products being reconstructed, not to this design system.

Why this exists (2026-09-06). The cream skin was migrated by a generator whose
colour map was a hand-written list of ember's known hexes. That map re-found
exactly the defects I already knew about and missed every colour I hadn't
thought of: two demo greens (#5ED48E, #7EA88F) shipped at 1.7-2.6:1 on paper,
and they were sitting in styles.css the whole time. A rule built from the
defects you found can only re-find those.

So this tool does not enumerate. For every colour literal in an INK-carrying
property, across the site's stylesheets AND the page-level <style> blocks, it
MEASURES the literal against cream's three surfaces. If the literal cannot
carry text there, it is snapped to the nearest cream token of the same hue
family. Anything it cannot classify confidently is reported and left alone —
a half-mapped colour is worse than an unmapped one.

Usage:  python3 tools/cream-ink-snap.py            # report only
        python3 tools/cream-ink-snap.py --write    # append the L14 block to cream.css
"""
import re, sys, glob, colorsys

SURFACES = ("#FAF9F6", "#FFFFFF", "#F2F1ED", "#F7F4EE", "#FFFDF8", "#F0ECE2")
INK_PROPS = {"color", "fill", "stroke", "text-decoration-color", "caret-color"}
# product reconstructions carry the real products' palettes — out of scope
EXEMPT = re.compile(r"\.pl[A-Z]-|#recon-|\.rx2-|\.pass\b|\.vslip|\.vplate|\.lug\b")
AA_TEXT, AA_LARGE = 4.5, 3.0

# the cream tokens an illegible literal may be snapped to, by hue family
FAMILY = [
    ("green",  (75, 175),  "var(--cream-positive)"),
    ("cyan",   (175, 200), "var(--cream-info)"),
    ("blue",   (200, 260), "var(--cream-info)"),
    ("violet", (260, 320), "var(--cream-bronze)"),
    ("pink",   (320, 350), "var(--cream-negative)"),
    ("red",    (350, 361), "var(--cream-negative)"),
    ("red2",   (0, 18),    "var(--cream-negative)"),
    ("orange", (18, 45),   "var(--cream-bronze)"),
    ("amber",  (45, 75),   "var(--cream-caution)"),
]


def lum(rgb):
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    la, lb = max(la, lb), min(la, lb)
    return (la + 0.05) / (lb + 0.05)


def parse(col):
    """-> (r,g,b), alpha  or None if not a solid, measurable colour."""
    col = col.strip()
    m = re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", col)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0
    m = re.fullmatch(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)\s*(?:[,/]\s*([\d.]+)\s*)?\)", col)
    if m:
        a = float(m.group(4)) if m.group(4) else 1.0
        return tuple(int(m.group(i)) for i in (1, 2, 3)), a
    return None


def family_of(rgb):
    r, g, b = [x / 255 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.12:
        return "neutral", "var(--text-muted)"
    deg = h * 360
    for name, (lo, hi), token in FAMILY:
        if lo <= deg < hi:
            return name, token
    return None, None


def sources():
    """Every place a colour literal can hide: stylesheets and page <style> blocks."""
    out = []
    for f in ("styles.css", "ember.css"):
        out.append((f, open(f).read()))
    pages = [p for p in glob.glob("*.html") + glob.glob("*/[a-z]*.html")
             if not p.startswith(("prototypes", "partials", "book", "portfolio-sources", "__"))]
    for p in pages:
        for i, block in enumerate(re.findall(r"<style[^>]*>(.*?)</style>", open(p).read(), re.S)):
            out.append((f"{p} <style#{i}>", block))
    return out


def main():
    write = "--write" in sys.argv
    rules, skipped, seen = [], [], set()
    for origin, css in sources():
        css_nc = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
        for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css_nc):
            sel, body = m.group(1).strip(), m.group(2)
            if not sel or sel.startswith(("@", "%")) or "{" in sel:
                continue
            if EXEMPT.search(sel):
                continue
            decls = []
            for d in body.split(";"):
                if ":" not in d:
                    continue
                prop, val = d.split(":", 1)
                prop, val = prop.strip().lower(), val.strip()
                if prop not in INK_PROPS or "var(" in val:
                    continue
                pc = parse(val.replace("!important", "").strip())
                if not pc:
                    continue
                rgb, alpha = pc
                # an alpha ink is composited over the surface before measuring
                worst = min(
                    ratio(tuple(round(rgb[i] * alpha + parse(s)[0][i] * (1 - alpha)) for i in range(3)),
                          parse(s)[0])
                    for s in SURFACES)
                if worst >= AA_TEXT:
                    continue                      # legible on every cream surface: leave it
                fam, token = family_of(rgb)
                if token is None:
                    skipped.append((origin, sel[:48], prop, val, round(worst, 2)))
                    continue
                decls.append((prop, token, val, round(worst, 2), fam))
            if not decls:
                continue
            parts = [p.strip() for p in sel.split(",") if p.strip()]
            scoped = []
            for p in parts:
                if 'data-theme="ember"' in p:
                    scoped.append(p.replace('html[data-theme="ember"]',
                                            'html[data-theme="ember"][data-skin="cream"]'))
                elif p.startswith(("html", ":root")):
                    scoped.append('html[data-theme="ember"][data-skin="cream"]')
                else:
                    scoped.append('html[data-theme="ember"][data-skin="cream"] ' + p)
            nsel = ", ".join(dict.fromkeys(" ".join(s.split()) for s in scoped))
            decl_txt = ";".join(f"{p}:{t}" for p, t, *_ in decls)
            key = (nsel, decl_txt)
            if key in seen:
                continue
            seen.add(key)
            rules.append((nsel, decl_txt, decls, origin))

    print(f"{len(rules)} rule(s) carry ink that cannot be read on a cream surface:\n")
    for nsel, _, decls, origin in rules:
        for prop, token, val, worst, fam in decls:
            print(f"  {worst:5.2f}:1  {prop}:{val:22} -> {token:26} [{fam}]  {origin}")
            print(f"           {nsel[:96]}")
    if skipped:
        print(f"\n{len(skipped)} literal(s) UNCLASSIFIED and left alone (report only):")
        for s in skipped[:10]:
            print("   ", s)

    if write and rules:
        block = ["\n/* ---------- L14 (GENERATED by tools/cream-ink-snap.py — do not hand-edit)",
                 "   Every ink literal that cannot be read on a cream surface, snapped to the",
                 "   cream token of its own hue family. Generated by MEASUREMENT, not by a list",
                 "   of known hexes: the hand-written map this replaces re-found only the",
                 "   defects already known and shipped two demo greens at 1.7-2.6:1. ---------- */"]
        for nsel, decl_txt, decls, origin in rules:
            worst = min(d[3] for d in decls)
            block.append(f"/* {worst}:1 in {origin} */\n{nsel}{{{decl_txt}}}")
        open("cream.css", "a").write("\n".join(block) + "\n")
        print(f"\nappended {len(rules)} rule(s) to cream.css")
    elif write:
        print("\nnothing to write — every ink literal already reads on cream")


if __name__ == "__main__":
    main()
