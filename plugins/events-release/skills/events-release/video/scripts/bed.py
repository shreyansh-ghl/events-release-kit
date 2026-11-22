"""House music bed + sound effects for a release video, synthesized locally (no licensed audio).

Ported from the Attendee App launch film's temp soundtrack (the one the team liked): 120 BPM pad, kick,
bass, hats and arp in G major, clicks/taps/pops on screen actions, ducked under the narration.

    bed.write_bed(props, out_wav)    # props = resolved release props (see release_video.py)

Pure Python (no numpy). Deterministic: the same props always give the same file.
"""
from __future__ import annotations

import math
import random
import wave
from array import array
from pathlib import Path

SR = 44100
BEAT = 0.5  # 120 BPM
BAR = 4 * BEAT
TWO_PI = 2 * math.pi
MUSIC = 0.29  # bed level (film: lowered 20% after review)
DUCK = 0.64  # how far music dips under the voice
SFX = 0.55
SFX_DUCK = 0.6

CHORDS = [  # G major: I - vi - IV - V  (pad notes, bass root)
    ([55, 59, 62, 66], 43),
    ([52, 55, 59, 62], 40),
    ([48, 52, 55, 59], 36),
    ([50, 54, 57, 62], 38),
]
ARP = [0, 2, 1, 3, 2, 1, 3, 2]


def midi(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def zeros(n: int) -> array:
    return array("d", [0.0]) * n


# ---------- instruments (from the film) ----------

def kick() -> array:
    n = int(0.42 * SR)
    out, ph = zeros(n), 0.0
    for i in range(n):
        t = i / SR
        ph += TWO_PI * (46 + 90 * math.exp(-t / 0.028)) / SR
        out[i] = math.sin(ph) * math.exp(-t / 0.13) + random.uniform(-1, 1) * math.exp(-t / 0.002) * 0.3
    return out


def clap() -> array:
    n = int(0.3 * SR)
    out, prev = zeros(n), 0.0
    for i in range(n):
        t = i / SR
        x = random.uniform(-1, 1)
        bursts = sum(math.exp(-(t - d) / 0.012) for d in (0.0, 0.011, 0.022) if t >= d)
        out[i] = (x - prev) * (0.5 * bursts + math.exp(-t / 0.09)) * 0.45
        prev = x
    return out


def hat(decay: float = 0.018) -> array:
    n = int(decay * 8 * SR)
    out, prev = zeros(n), 0.0
    for i in range(n):
        x = random.uniform(-1, 1)
        out[i] = (x - prev) * math.exp(-(i / SR) / decay) * 0.35
        prev = x
    return out


def bass(m: float, dur: float = 0.45) -> array:
    n, f = int(dur * SR), midi(m)
    out = zeros(n)
    for i in range(n):
        t = i / SR
        x = TWO_PI * f * t
        out[i] = (math.sin(x) + 0.32 * math.sin(2 * x) + 0.12 * math.sin(3 * x)) * min(1.0, t / 0.006) * math.exp(-t / 0.28) * 0.55
    return out


def pad(notes: list[int], dur: float, attack: float = 0.35, release: float = 0.6) -> array:
    n = int(dur * SR)
    out, fs = zeros(n), [midi(m) for m in notes]
    for i in range(n):
        t = i / SR
        a = min(1.0, t / attack) * min(1.0, max(0.0, (dur - t) / release))
        s = sum(math.sin(TWO_PI * f * t) + 0.45 * math.sin(TWO_PI * f * 1.0035 * t) + 0.18 * math.sin(TWO_PI * 2 * f * t) for f in fs)
        out[i] = s * a * (1 + 0.06 * math.sin(TWO_PI * 0.25 * t)) * 0.05
    return out


def pluck(m: float, dur: float = 0.32) -> array:
    n, f = int(dur * SR), midi(m)
    out = zeros(n)
    for i in range(n):
        t = i / SR
        x = TWO_PI * f * t
        out[i] = (math.sin(x) + 0.33 * math.sin(3 * x) + 0.2 * math.sin(5 * x)) * math.exp(-t / 0.09) * 0.22
    return out


def bell(m: float, decay: float = 0.7, gain: float = 0.3) -> array:
    n, f = int(decay * 4 * SR), midi(m)
    out = zeros(n)
    for i in range(n):
        t = i / SR
        out[i] = (math.sin(TWO_PI * f * t) + 0.5 * math.sin(TWO_PI * 2.76 * f * t) * math.exp(-t / 0.2)
                  + 0.25 * math.sin(TWO_PI * 5.4 * f * t) * math.exp(-t / 0.08)) * math.exp(-t / decay) * gain
    return out


def sweep(dur: float, up: bool = True, gain: float = 0.4, tone: bool = False) -> array:
    """Filtered-noise riser (up) or whoosh (rise and fall)."""
    n = max(1, int(dur * SR))
    out, y, ph = zeros(n), 0.0, 0.0
    for i in range(n):
        p = i / n
        cut, a = (0.02 + 0.5 * p * p, p ** 1.6) if up else (0.05 + 0.45 * math.sin(math.pi * p), math.sin(math.pi * p) ** 1.5)
        y += cut * (random.uniform(-1, 1) - y)
        s = y
        if tone:
            ph += TWO_PI * (200 + 1400 * p) / SR
            s += 0.25 * math.sin(ph)
        out[i] = s * a * gain
    return out


def boom(gain: float = 0.9) -> array:
    n = int(2.2 * SR)
    out, ph = zeros(n), 0.0
    for i in range(n):
        t = i / SR
        ph += TWO_PI * (42 + 30 * math.exp(-t / 0.08)) / SR
        out[i] = math.sin(ph) * math.exp(-t / 0.7) * gain
    return out


def crash(gain: float = 0.25) -> array:
    n = int(3.0 * SR)
    out, prev = zeros(n), 0.0
    for i in range(n):
        x = random.uniform(-1, 1)
        out[i] = (x - prev) * math.exp(-(i / SR) / 0.9) * gain
        prev = x
    return out


def tap(gain: float = 0.35) -> array:
    n = int(0.03 * SR)
    out = zeros(n)
    for i in range(n):
        t = i / SR
        out[i] = (math.sin(TWO_PI * 1900 * t) * math.exp(-t / 0.004) + random.uniform(-1, 1) * math.exp(-t / 0.0015) * 0.4) * gain
    return out


def thock(gain: float = 0.6) -> array:
    n = int(0.09 * SR)
    out, ph = zeros(n), 0.0
    for i in range(n):
        t = i / SR
        ph += TWO_PI * (260 - 1300 * t) / SR
        out[i] = (math.sin(ph) * math.exp(-t / 0.018) + random.uniform(-1, 1) * math.exp(-t / 0.002) * 0.5) * gain
    return out


def pop(m: float = 84, gain: float = 0.35) -> array:
    n = int(0.08 * SR)
    out, ph, f0 = zeros(n), 0.0, midi(m)
    for i in range(n):
        t = i / SR
        ph += TWO_PI * f0 * (1 + 0.6 * min(1.0, t / 0.02)) / SR
        out[i] = math.sin(ph) * math.exp(-t / 0.025) * gain
    return out


# ---------- arrangement ----------

class Bus:
    def __init__(self, n: int) -> None:
        self.n = n
        self.d = zeros(n)

    def add(self, t: float, samples: array, gain: float = 1.0) -> None:
        i0 = int(t * SR)
        if i0 < 0 or i0 >= self.n:
            return
        d = self.d
        for k in range(min(len(samples), self.n - i0)):
            d[i0 + k] += samples[k] * gain


def _music(props: dict, n: int) -> array:
    music, send = Bus(n), Bus(n)
    scenes = props["scenes"]
    total = props["total"]
    title = next((s for s in scenes if s["kind"] == "title"), None)
    end = next((s for s in scenes if s["kind"] == "end"), None)
    drop = title["from"] if title else 0.0
    final = end["from"] + 0.3 if end else total
    first_chapter = next((s["from"] for s in scenes if s["kind"] == "chapter"), final)

    cold = next((s for s in scenes if s["kind"] == "cold_open"), None)
    if cold:  # quiet pad under the old pain, a riser into the drop
        send.add(0.0, pad(CHORDS[0][0], max(1.0, drop - 0.05), attack=1.2, release=0.4), 0.5)
        riser = min(2.2, max(0.6, drop - cold["payoff"]["at"]))
        music.add(drop - riser, sweep(riser, up=True, gain=0.45, tone=True))

    k, cl, h = kick(), clap(), hat()
    bar_t, bar_i = drop, 0
    while bar_t < final - 1e-6:
        notes, root = CHORDS[bar_i % 4]
        full = bar_t >= first_chapter
        send.add(bar_t, pad(notes, BAR + 0.05), 0.55)
        for b in range(4):
            t = bar_t + b * BEAT
            if t >= final:
                break
            music.add(t, k, 0.9 if full else 0.75)
            music.add(t, bass(root + (12 if b == 3 and full else 0)), 0.85)
            if full and b in (1, 3):
                music.add(t, cl, 0.8)
            for s in range(4 if full else 2):
                if not full and s == 0:
                    continue
                music.add(t + s * BEAT / (4 if full else 2), h, 0.5 if full else 0.4)
            if full:
                for s in range(2):
                    m = notes[ARP[(b * 2 + s) % 8] % 4] + 12
                    send.add(t + s * BEAT / 2, pluck(m), 0.45)
        bar_t += BAR
        bar_i += 1

    if end:  # final hit, then a long pad tail
        send.add(final, pad([43, 55, 59, 62, 66, 71], min(7.0, total - final + 0.5), attack=0.02, release=4.0), 1.0)
        music.add(final, boom(), 0.9)
        music.add(final, crash(), 0.9)
        music.add(final, k, 1.0)

    # cheap reverb on the send bus (four feedback delay lines)
    out = music.d
    for delay, fb in ((1557, 0.72), (1617, 0.7), (1491, 0.74), (1422, 0.68)):
        line = zeros(n)
        sd = send.d
        for i in range(n):
            line[i] = sd[i] + (line[i - delay] * fb if i >= delay else 0.0)
        for i in range(n):
            out[i] += line[i] * 0.12
    for i in range(n):
        out[i] += send.d[i] * 0.85
    return out


def _sfx(props: dict, n: int) -> array:
    sfx = Bus(n)
    for s in props["scenes"]:
        if s["kind"] == "cold_open" and s.get("prop", {}).get("pile"):
            a = s["beats"][0]["at"] + 0.75
            b = s["beats"][1]["at"] + 1.2 if len(s["beats"]) > 1 else a + 2
            for _ in range(28):
                sfx.add(random.uniform(a + 0.6, b), pop(random.choice([88, 91, 93, 96]), 0.08))
        if s["kind"] == "chapter":
            sfx.add(s["from"], sweep(0.7, up=False, gain=0.22))
            for shot in s["shots"]:
                t0 = shot["from"]
                for c in shot.get("cursor") or []:
                    if len(c) > 3 and c[3] == "click":
                        sfx.add(t0 + c[0], thock(0.55))
                for tp in shot.get("tap") or []:
                    sfx.add(t0 + tp[0], tap())
                if shot.get("phone") and shot["phone"].get("enter") is not None:
                    sfx.add(t0 + shot["phone"]["enter"], sweep(0.6, up=False, gain=0.25))
                for dev in ("laptop", "phone"):
                    for sw in (shot.get(dev) or {}).get("swaps") or []:
                        sfx.add(t0 + sw["t"], pop(84, 0.22))
        if s["kind"] == "end":
            sfx.add(s["from"] + 0.3, bell(86, 0.6, 0.16))
    return sfx.d


def duck(vo: list[dict], t: float) -> float:
    """1.0 when nobody is speaking; dips by DUCK while a VO line plays (soft 150/250 ms edges)."""
    g = 1.0
    for c in vo:
        a, b = c["at"], c["at"] + c["dur"]
        if a - 0.15 <= t <= b + 0.25:
            edge = min(1.0, (t - (a - 0.15)) / 0.15, ((b + 0.25) - t) / 0.25)
            g = min(g, 1.0 - DUCK * edge)
    return g


def write_bed(props: dict, out_wav: Path) -> Path:
    random.seed(7)
    n = int((props["total"] + 0.5) * SR)
    music = _music(props, n)
    sfx = _sfx(props, n)
    mix = zeros(n)
    step = SR // 100
    fade_from = props["total"] - 1.2
    for i0 in range(0, n, step):
        t = i0 / SR
        g = duck(props["vo"], t)
        gs = 1.0 - (1.0 - g) * SFX_DUCK
        tail = 1.0 if t < fade_from else max(0.0, 1.0 - (t - fade_from) / 1.2)
        for i in range(i0, min(n, i0 + step)):
            mix[i] = math.tanh(music[i] * MUSIC * g + sfx[i] * SFX * gs) * tail
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(array("h", (max(-32767, min(32767, int(x * 0.89 * 32767))) for x in mix)).tobytes())
    return out_wav
