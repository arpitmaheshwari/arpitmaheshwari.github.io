#!/usr/bin/env python3
"""Fail when the narration is monotone — the property nobody was measuring.

Why this exists: narrate.mjs has carried the comment "Measured by tools/prosody-check.py"
since the per-segment prosody arc was written. That file did not exist. So "does the voice
sound robotic" was opinion against opinion, with no instrument, on a six-minute artifact
that is expensive to re-render.

WHAT IT MEASURES, per segment, from the rendered audio itself — not from the rate/pitch
numbers the script ASKED for, because a setting is an intention and this grades the result:

    median f0      the segment's pitch centre, by autocorrelation on voiced frames
    f0 spread      interquartile range within the segment — flat delivery collapses this
    arc spread     how far the segment medians sit apart ACROSS the film

A film can fail two different ways and they need separate names. Flat-within means every
sentence in a segment lands on the same note. Flat-across means the segments are each
lively but all centred identically, so the film has no shape. v1's arc was rate +3/-6% and
pitch +12/-14Hz; v2 widened it to +4/-8% and +16/-18Hz precisely to move the second number.

CALIBRATION
    --selftest synthesises a monotone tone and a varied one and requires the gate to tell
    them apart. A checker that cannot fail is not evidence.

CANNOT SEE: whether the writing is any good, whether the voice suits the material, accent,
mispronunciation, or anything about the PICTURE. A segment can be perfectly varied and
still be dull.
"""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, '..', 'portfolio-sources', 'video')
BUILD = os.path.join(VID, 'build')
FF = os.path.join(VID, 'node_modules', '@ffmpeg-installer', 'darwin-arm64', 'ffmpeg')

# A neural voice reading English sits roughly here; anything outside is almost certainly
# the autocorrelation locking onto a harmonic rather than the fundamental.
F0_MIN, F0_MAX = 60.0, 400.0
MIN_SPREAD_HZ = 12.0    # within a segment: below this the delivery is flat
MIN_ARC_HZ = 10.0       # across segments: below this the film has one note


def f0_track(path):
    """Median-per-frame fundamental, voiced frames only, by autocorrelation."""
    wav = path + '.probe.wav'
    subprocess.run([FF, '-y', '-i', path, '-ac', '1', '-ar', '16000', wav],
                   capture_output=True)
    if not os.path.exists(wav):
        return None
    with wave.open(wav) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
        sr = w.getframerate()
    os.remove(wav)
    win, hop = int(sr * 0.04), int(sr * 0.02)
    lo, hi = int(sr / F0_MAX), int(sr / F0_MIN)
    out = []
    for i in range(0, max(0, len(a) - win), hop):
        f = a[i:i + win]
        if np.sqrt(np.mean(f * f)) < 300:          # silence / unvoiced
            continue
        f = f - f.mean()
        c = np.correlate(f, f, 'full')[len(f) - 1:]
        if c[0] <= 0:
            continue
        seg = c[lo:hi]
        if not len(seg):
            continue
        k = int(np.argmax(seg)) + lo
        if c[k] / c[0] < 0.3:                      # too weak to be a real period
            continue
        out.append(sr / k)
    return np.array(out) if out else None


def grade(tracks):
    findings, rows = [], []
    for sid, f0 in tracks:
        if f0 is None or len(f0) < 20:
            rows.append((sid, None, None))
            findings.append(('UNMEASURED', sid, 'too few voiced frames to judge'))
            continue
        med = float(np.median(f0))
        spread = float(np.percentile(f0, 75) - np.percentile(f0, 25))
        rows.append((sid, med, spread))
        if spread < MIN_SPREAD_HZ:
            findings.append(('FLAT-WITHIN', sid,
                             f'{spread:.1f}Hz of variation inside the segment '
                             f'(floor {MIN_SPREAD_HZ:.0f}Hz) — every sentence lands on one note'))
    meds = [m for _, m, _ in rows if m]
    arc = (max(meds) - min(meds)) if len(meds) > 1 else 0.0
    if meds and arc < MIN_ARC_HZ:
        findings.append(('FLAT-ACROSS', 'film',
                         f'{arc:.1f}Hz between the highest and lowest segment '
                         f'(floor {MIN_ARC_HZ:.0f}Hz) — the film has no shape'))
    return rows, arc, findings


def selftest():
    sr, t = 16000, np.linspace(0, 2, 32000)
    flat = (8000 * np.sin(2 * np.pi * 150 * t)).astype(np.int16)
    varied = (8000 * np.sin(2 * np.pi * (120 + 70 * np.sin(2 * np.pi * 0.9 * t)) * t)).astype(np.int16)
    got = []
    for name, sig in (('flat', flat), ('varied', varied)):
        p = os.path.join(BUILD, f'_prosody_selftest_{name}.wav')
        with wave.open(p, 'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(sig.tobytes())
        f0 = f0_track(p)
        os.remove(p)
        got.append(0.0 if f0 is None else float(np.percentile(f0, 75) - np.percentile(f0, 25)))
    ok = got[0] < MIN_SPREAD_HZ <= got[1]
    print(f"[calibration] {'PASS' if ok else 'FAIL'} — monotone tone reads {got[0]:.1f}Hz spread, "
          f"varied tone reads {got[1]:.1f}Hz; the gate can {'tell them apart' if ok else 'NOT tell them apart'}")
    return ok


def main():
    if not os.path.exists(FF):
        print('UNMEASURED — no bundled ffmpeg to decode the audio with.')
        return 3
    if not selftest():
        print('\nRefusing to report. A checker that cannot fail is not evidence.')
        return 2
    if '--selftest' in sys.argv:
        return 0
    dpath = os.path.join(BUILD, 'durations.json')
    if not os.path.exists(dpath):
        print('UNMEASURED — no durations.json; the narration has not been rendered.')
        return 3
    d = json.load(open(dpath))
    # durations.json names each segment's own audio file; never guess at seg-NN ordering.
    tracks = []
    for s in d['segments']:
        a = s.get('aiff') or ''
        if a and not os.path.isabs(a):
            a = os.path.join(BUILD, os.path.basename(a))
        tracks.append((s['id'], f0_track(a) if a and os.path.exists(a) else None))
    rows, arc, findings = grade(tracks)
    print(f"\nvoice {d.get('voice')} — {len(rows)} segment(s)")
    for sid, med, spread in rows:
        if med is None:
            print(f"  {sid:12s}  unmeasured")
        else:
            print(f"  {sid:12s}  centre {med:5.1f}Hz   spread {spread:5.1f}Hz")
    print(f"  {'ARC':12s}  {arc:5.1f}Hz between the highest and lowest segment")
    for kind, where, why in findings:
        print(f"  {kind}  {where}: {why}")
    print(f"\n{len([f for f in findings if f[0] != 'UNMEASURED'])} prosody finding(s)")
    print("CANNOT SEE: whether the writing is good, the accent, mispronunciation, or the picture.")
    return 1 if any(f[0] != 'UNMEASURED' for f in findings) else 0


if __name__ == '__main__':
    sys.exit(main())
