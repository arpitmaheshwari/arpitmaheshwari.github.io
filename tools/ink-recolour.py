#!/usr/bin/env python3
"""ink-recolour.py — turn black-ink-on-white illustrations into the site's two inks.

    python3 tools/ink-recolour.py            # every PNG in portfolio-sources/illustrations/
    python3 tools/ink-recolour.py home       # one, by name

For each original it writes, with a TRANSPARENT ground:
    assets/visuals/ink/<name>-gold.png    gold #D4A85E ink  — the dark site (--gold)
    assets/visuals/ink/<name>-cream.png   #20180C ink       — cream act bands (--ink on cream)

How: the image's darkness becomes the alpha channel (white paper → 0, black ink → 255), and the
colour is flat. Grey hatching therefore becomes semi-transparent ink, which is what cross-hatching
on a dark ground needs — a hard threshold would turn fine hatching into dust.

Refuses an original that is not ink on white: a coloured image, or one whose border is not
paper-white (a dark or tinted background would become a solid slab). Both are checked on the
pixels, not on the file name.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "portfolio-sources" / "illustrations"
OUT = ROOT / "assets" / "visuals" / "ink"
INKS = {"gold": (0xD4, 0xA8, 0x5E), "cream": (0x20, 0x18, 0x0C)}


def check_is_ink_on_white(rgb, name):
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    spread = np.maximum(np.maximum(abs(r - g), abs(g - b)), abs(r - b))
    coloured = (spread > 40).mean()
    if coloured > 0.01:
        raise SystemExit(f"{name}: {coloured:.1%} of pixels are coloured — regenerate as black ink on white")
    h, w = rgb.shape[:2]
    m = max(4, min(h, w) // 50)
    border = np.concatenate([rgb[:m].reshape(-1, 3), rgb[-m:].reshape(-1, 3),
                             rgb[:, :m].reshape(-1, 3), rgb[:, -m:].reshape(-1, 3)])
    if border.mean() < 235:
        raise SystemExit(f"{name}: the border is not paper-white (mean {border.mean():.0f}) — "
                         "the ground would become a solid slab; crop or regenerate")


def recolour(path):
    im = Image.open(path).convert("RGB")
    rgb = np.asarray(im)
    check_is_ink_on_white(rgb, path.name)
    lum = rgb.mean(axis=2)
    # paper is rarely pure 255; anything above 245 is paper, anything below 30 is full ink
    alpha = np.clip((245 - lum) / (245 - 30), 0, 1)
    alpha = (alpha * 255).round().astype(np.uint8)
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for ink, (r, g, b) in INKS.items():
        out = np.zeros((*alpha.shape, 4), dtype=np.uint8)
        out[..., 0], out[..., 1], out[..., 2], out[..., 3] = r, g, b, alpha
        dst = OUT / f"{path.stem}-{ink}.png"
        Image.fromarray(out).save(dst, optimize=True)
        written.append(dst)
    inked = (alpha > 0).mean()
    print(f"  {path.name}: {im.width}x{im.height}, {inked:.1%} inked → {', '.join(d.name for d in written)}")
    if inked < 0.005:
        raise SystemExit(f"{path.name}: almost nothing inked ({inked:.2%}) — blank or near-white image")


def main(names):
    files = sorted(SRC.glob("*.png")) if not names else [SRC / f"{n}.png" for n in names]
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit("missing: " + ", ".join(f.name for f in missing))
    if not files:
        raise SystemExit(f"no PNGs in {SRC} — see its README for the ten expected names")
    for f in files:
        recolour(f)


if __name__ == "__main__":
    main(sys.argv[1:])
