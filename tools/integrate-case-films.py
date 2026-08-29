#!/usr/bin/env python3
"""Insert the narrated case-summary film above each case's verdict slip.

Placement is Arpit's explicit call (2026-08-30): the film sits ABOVE the vband,
as its own band, reusing the walkthrough's .vid-frame grammar so attention.js's
whole-frame click-to-play binds automatically. Idempotent: skips a page that
already has .vband-film. Duration comes from the pipeline's durations.json —
never hand-typed.
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VID = ROOT / 'portfolio-sources' / 'video'
FF = VID / 'node_modules' / '@ffmpeg-installer' / 'darwin-arm64' / 'ffmpeg'
ASSETS = ROOT / 'assets' / 'video'

CASES = ['adtech','fintech','vc-diligence','ptc','o2','orgos','planit']

def mmss(sec):
    return f"{int(sec//60)}:{int(round(sec%60)):02d}"

changed = 0
for c in CASES:
    build = VID / f'build-{c}'
    web = build / f'case-{c}-web.mp4'
    durf = build / 'durations.json'
    if not web.exists() or not durf.exists():
        print(f"SKIP {c}: pipeline outputs missing"); continue
    page = ROOT / 'case-studies' / f'{c}.html'
    s = page.read_text()
    if 'vband-film' in s:
        print(f"ok   {c}: already integrated"); continue
    total = json.load(open(durf))['total']
    dur = mmss(total)
    # ship assets
    ASSETS.mkdir(parents=True, exist_ok=True)
    dst = ASSETS / f'case-{c}.mp4'
    dst.write_bytes(web.read_bytes())
    poster = ASSETS / f'case-{c}-poster.jpg'
    subprocess.run([str(FF), '-y', '-ss', '1', '-i', str(web), '-frames:v', '1', '-q:v', '4', str(poster)],
                   check=True, capture_output=True)
    size_mb = dst.stat().st_size / 1e6
    block = f'''<!-- the case, narrated — summary film above the slip (Arpit's placement, 2026-08-30) -->
<section class="vband-film" aria-label="The case, narrated — {dur} video summary">
  <figure class="vid-main vid-case">
    <div class="vid-frame">
      <video controls playsinline preload="none" width="1920" height="1080"
             poster="./../assets/video/case-{c}-poster.jpg"
             data-cta="case-film" data-location="case-{c}">
        <source src="./../assets/video/case-{c}.mp4" type="video/mp4">
        <p class="vid-fallback">Your browser can&rsquo;t play this video.
          <a href="./../assets/video/case-{c}.mp4">Download the file ({size_mb:.0f}&nbsp;MB)</a>.</p>
      </video>
    </div>
    <figcaption class="vid-cap-row">
      <span class="vid-meta">{dur} &middot; the case, narrated &middot; rather read? &mdash; the 60-second slip is next</span>
      <span class="vid-meta">synthetic voice for now</span>
    </figcaption>
  </figure>
</section>

'''
    anchor = '<section class="vband"'
    assert anchor in s, f"{c}: vband anchor missing"
    s = s.replace(anchor, block + anchor, 1)
    page.write_text(s)
    changed += 1
    print(f"DONE {c}: {dur}, {size_mb:.1f} MB")
print(f"\n{changed} page(s) updated")
