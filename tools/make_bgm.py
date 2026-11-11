"""Make the game's background music: a light, cheerful kitchen loop (marimba tune, plucked chords, bass, shaker).

    python tools/make_bgm.py          # writes src/assets/audio/bgm.mp3 (needs numpy and ffmpeg)

It is a seamless 16-bar loop at 112 bpm in C major (C - Am - F - G), quiet enough to sit under the voices.
"""
import os
import subprocess
import wave

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "src", "assets", "audio")
SR = 44100
BPM = 112
BEAT = 60 / BPM
BARS = 16
N = int(round(BARS * 4 * BEAT * SR))
mix = np.zeros((N, 2))
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, t, pan=0.0, gain=1.0):
    i = int(round(t * SR)) % N
    n = len(sig)
    l, r = gain * (1 - pan) / 2 * 2 ** .5, gain * (1 + pan) / 2 * 2 ** .5
    end = i + n
    if end <= N:
        mix[i:end, 0] += sig * l; mix[i:end, 1] += sig * r
    else:                                   # wrap round: the loop is seamless
        k = N - i
        mix[i:, 0] += sig[:k] * l; mix[i:, 1] += sig[:k] * r
        mix[:n - k, 0] += sig[k:] * l; mix[:n - k, 1] += sig[k:] * r


def marimba(m, dur=0.9):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22) + 0.15 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 60)
    return s * np.minimum(1, t * 400)


def pluck(m, dur=0.6):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * t) for k in range(5)) * np.exp(-t * 6)
    return s * np.minimum(1, t * 300)


def bass(m, dur):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.exp(-t * 2.2) * np.minimum(1, t * 200) * np.minimum(1, (dur - t) * 40)


def shaker(dur=0.07):
    n = int(dur * SR); s = rng.standard_normal(n)
    s = np.diff(np.concatenate([[0], s]))          # brighter
    return s * np.exp(-np.arange(n) / SR * 60)


def bell(m, dur=1.4):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 3) * np.minimum(1, t * 500)


CHORDS = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67])]   # C Am F G (bass root, triad)
# two 4-bar phrases of the tune (8th notes; None = rest), played twice: A A' B A
A = [72, None, 76, 79, 76, None, 74, 72, 69, None, 72, 76, 74, None, 72, 69, 69, None, 72, 77, 76, None, 74, 72, 71, None, 74, 79, 77, 76, 74, None]
A2 = [72, None, 76, 79, 81, None, 79, 76, 72, None, 76, 79, 77, None, 76, 74, 72, None, 69, 72, 74, None, 76, 77, 79, None, 77, 74, 72, None, None, None]
B = [79, 81, 79, 76, 74, 76, 72, None, 76, 77, 76, 72, 69, 72, 76, None, 77, 79, 77, 74, 72, 74, 77, None, 79, None, 74, None, 71, None, 74, None]
TUNE = A + A2 + B + A2

for bar in range(BARS):
    root, triad = CHORDS[bar % 4]
    t0 = bar * 4 * BEAT
    add(bass(root, BEAT * 1.6), t0, -0.1, 0.42); add(bass(root + 7, BEAT * 1.2), t0 + 2 * BEAT, -0.1, 0.3)
    for b in (1, 3):                                            # off-beat chord plucks
        for j, m in enumerate(triad):
            add(pluck(m), t0 + b * BEAT + j * 0.012, 0.25, 0.11)
    for e in range(8):                                          # shaker on every 8th, accented off-beats
        add(shaker(), t0 + e * BEAT / 2, 0.4, 0.05 if e % 2 else 0.025)
    for e in range(8):
        m = TUNE[(bar * 8 + e) % len(TUNE)]
        if m:
            add(marimba(m), t0 + e * BEAT / 2, -0.2, 0.32)
    if bar % 4 == 3:                                            # a little sparkle at the end of each phrase
        add(bell(84), t0 + 3.5 * BEAT, 0.5, 0.09)

mix /= np.max(np.abs(mix)) / 0.8
os.makedirs(OUT, exist_ok=True)
wav = os.path.join(OUT, "bgm.wav")
with wave.open(wav, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "96k", os.path.join(OUT, "bgm.mp3")], check=True)
os.remove(wav)
print("bgm.mp3", round(N / SR, 1), "s")
