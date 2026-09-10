#!/usr/bin/env python3
"""UNIT TESTS FOR THE INK ALGEBRA — the only part of contrast-audit with no test.

WHY THIS EXISTS. contrast-audit measures pixels, and its correctness rests on four
constants — ALPHA_CORE 0.7, ALPHA_FLOOR 0.5, CORE_BAND 0.10, DIFF_T 24 — each set in
response to a specific incident. Until now the ONLY verification was four end-to-end
canaries on a live page: a browser, a server, a scroll loop and 12MB of screenshots to
check arithmetic that is three lines long.

That mattered on the day the nightly sweep reported the homepage call-to-action at
2.49:1, sampling #B1330C on #F67E99. The authored pair is #1A0D08 on #F67E99 — 7.57:1 —
and #B1330C appears in no stylesheet in the repository. The un-blend
    ink = (painted - (1 - alpha) * ground) / alpha
divides by coverage, so every rounding error is multiplied by 1/alpha; headless Chrome
on Linux renders 11-12.5px text thinner than macOS, coverage fell, and the algebra
returned a colour nobody authored. ALPHA_FLOOR exists to refuse that case. Nothing
tested the floor.

These tests construct frames instead of photographing them. For ink I on ground G at
coverage a:
    B = G                       (ink removed)
    A = a*I + (1-a)*G           (as shipped)
    C = a*MAGENTA + (1-a)*G     (ink keyed)
which is exactly what the browser produces, so _measure cannot tell the difference —
and the expected answer is known in advance, which a live page can never give you.

Runs in milliseconds. No browser, no server, no screenshots.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

# import contrast-audit without running its module-level ensure_server()
import importlib.util, pathlib
_src = pathlib.Path(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'contrast-audit.py')).read_text()
_src = _src.replace('_cdp.ensure_server(8000)', 'pass  # test: no server needed')
_src = _src.replace('\nif __name__ == "__main__":\n    main()', '')
CA = {'__file__': 'contrast-audit.py', '__name__': 'ca_under_test'}
exec(compile(_src, 'contrast-audit.py', 'exec'), CA)

_measure   = CA['_measure']
ratio      = CA['ratio']
MAGENTA    = CA['MAGENTA']
ALPHA_CORE = CA['ALPHA_CORE']
ALPHA_FLOOR = CA['ALPHA_FLOOR']
CORE_BAND  = CA['CORE_BAND']

W = H = 20
RECT = (0, 0, W, H)
BAND = (0, H)


def blend(fg, bg, a):
    return tuple(int(round(fg[ch] * a + bg[ch] * (1 - a))) for ch in range(3))


def frames(ink, ground, alpha, ground_right=None):
    """Three frames for a solid block of `ink` on `ground` at coverage `alpha`.

    ground_right, if given, makes the ground a horizontal gradient so the
    percentile's real job — grading at the WEAKEST position — can be tested."""
    a_im, b_im, c_im = (Image.new("RGB", (W, H)) for _ in range(3))
    pa, pb, pc = a_im.load(), b_im.load(), c_im.load()
    for x in range(W):
        g = ground if ground_right is None else blend(ground_right, ground, x / (W - 1.0))
        for y in range(H):
            pb[x, y] = g
            pa[x, y] = blend(ink, g, alpha)
            pc[x, y] = blend(MAGENTA, g, alpha)
    return a_im, b_im, c_im


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


FAILED = []


def check(name, got, want, tol=0.0):
    ok = (got == want) if tol == 0 else (want is not None and got is not None
                                        and abs(got - want) <= tol)
    print("  %-4s %-58s got %-22s want %s%s"
          % ("ok" if ok else "FAIL", name, repr(got),
             repr(want), "" if tol == 0 else " +/-%g" % tol))
    if not ok:
        FAILED.append(name)


def main():
    print("ink algebra — synthetic frames, known answers\n")

    # 1. FULL COVERAGE recovers the authored colour exactly.
    ink, ground = hexc("#1A0D08"), hexc("#F67E99")
    truth = ratio(ink, ground)
    got, noink, fg, bg, n = _measure(*frames(ink, ground, 1.0), RECT, BAND)
    check("alpha 1.00 recovers the authored ink exactly", fg, "#1A0D08")
    check("alpha 1.00 ratio equals the authored ratio", got, truth, 0.01)

    # 2. AT ALPHA_CORE the recovery is still exact enough to convict on.
    got, _, fg, _, _ = _measure(*frames(ink, ground, ALPHA_CORE), RECT, BAND)
    check("alpha 0.70 (ALPHA_CORE) ratio within 0.25 of truth", got, truth, 0.25)

    # 3. AT THE FLOOR — this is the claim ALPHA_FLOOR rests on and was never tested.
    got, _, fg, _, _ = _measure(*frames(ink, ground, ALPHA_FLOOR), RECT, BAND)
    check("alpha 0.50 (ALPHA_FLOOR) ratio within 0.60 of truth", got, truth, 0.60)

    # 4. BELOW THE FLOOR it must say UNMEASURABLE, never convict.
    #    This is the exact regime that produced ten false Linux failures.
    got, noink, fg, bg, n = _measure(*frames(ink, ground, 0.45), RECT, BAND)
    check("alpha 0.45 (below floor) returns UNMEASURABLE, not a ratio", got, None)
    check("alpha 0.45 is not reported as no-ink either", noink, False)

    # 5. THE ACTUAL INCIDENT. #1A0D08 on #F67E99 is 7.57:1. It was reported as
    #    2.49:1 with a recovered ink of #B1330C. Assert we never see that again.
    for a in (1.0, 0.9, 0.8, ALPHA_CORE):
        got, _, fg, _, _ = _measure(*frames(ink, ground, a), RECT, BAND)
        bad = got is not None and got < 4.5
        print("  %-4s incident regression @alpha %.2f: %.2f:1 (%s) — must stay above 4.5"
              % ("FAIL" if bad else "ok", a, got, fg))
        if bad:
            FAILED.append("incident regression @%.2f" % a)

    # 6. TWO DIFFERENT INVISIBILITIES, which the v3 docstring conflates. It says
    #    "an element whose two frames do not differ paints no legible ink at all
    #    (color == ground, or fully obscured)" — but those are not the same case and
    #    _measure is right to treat them differently. My first version of this test
    #    asserted the docstring and failed; the tool was correct.
    #
    #    (a) INK == GROUND. Frames A and B agree, but frame C still keys the ink to
    #        magenta, so the glyph IS found, its ink recovers to the ground colour,
    #        and the ratio is 1.00 — which fails every requirement there is. Caught
    #        as a FAILURE, correctly, and not flagged no-ink.
    got, noink, fg, bg, _ = _measure(*frames(ground, ground, 1.0), RECT, BAND)
    check("ink == ground grades 1.00:1 (a failure, not a pass)", got, 1.0, 0.02)
    check("ink == ground is a ratio failure, not the no-ink flag", noink, False)

    #    (b) NOTHING PAINTED AT ALL. All three frames identical: the key had nothing
    #        to key, so there is no glyph anywhere. THAT is no-ink — obscured, or
    #        never rendered — and it must be reported, never silently skipped.
    flat = Image.new("RGB", (W, H), ground)
    got, noink, _, _, n = _measure(flat, flat.copy(), flat.copy(), RECT, BAND)
    check("no glyph in any frame is reported as no-ink", noink, True)
    check("no-ink carries ratio 1.0 so it cannot pass a requirement", got, 1.0, 0.001)
    check("no-ink reports zero core pixels", n, 0)

    # 7. GROUND VARIES BY POSITION: grade at the WEAKEST point, not the mean.
    #    White ink over a ramp from black to white: the weak end is the white end.
    light, dark = hexc("#FFFFFF"), hexc("#000000")
    got, _, _, bg, _ = _measure(*frames(light, dark, 1.0, ground_right=light),
                                RECT, BAND)
    worst = ratio(light, light)
    check("gradient ground is graded near its weakest point", got, worst, 1.5)

    # 8. A rect with no area inside the band is not a measurement.
    got = _measure(*frames(ink, ground, 1.0), (0, 0, W, H), (H + 5, H + 10))
    check("a rect outside the band returns None (not a pass)", got, None)

    print()
    if FAILED:
        print("%d assertion(s) FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all assertions passed — the un-blend recovers authored ink at and above the "
          "floor, and refuses below it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
