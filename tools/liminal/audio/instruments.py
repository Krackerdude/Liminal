"""Voices.

A small, deliberately limited instrument set.  Everything is soft-edged and a
little out of tune, because a perfectly tuned sound reads as a *game* and a
slightly wrong one reads as a memory of a game.
"""

from __future__ import annotations

import numpy as np

from .dsp import (SR, detuned, env_adsr, env_fade, env_pluck, lowpass_fast,
                  noise, saturate, saw, sine, square, triangle, wobble)


def music_box(freq: float, seconds: float = 1.6, gain: float = 1.0) -> np.ndarray:
    """A struck tine: one bright partial, one inharmonic ghost above it."""
    body = sine(freq, seconds) * env_pluck(seconds, curve=3.2)
    shimmer = sine(freq * 2.76, seconds) * env_pluck(seconds, curve=7.0) * 0.28
    air = sine(freq * 4.1, seconds) * env_pluck(seconds, curve=12.0) * 0.10
    return (body + shimmer + air) * 0.5 * gain


def toy_piano(freq: float, seconds: float = 1.0, gain: float = 1.0) -> np.ndarray:
    """Slightly broken, slightly loud, entirely sincere."""
    body = triangle(freq, seconds, harmonics=5) * env_pluck(seconds, curve=5.0)
    knock = noise(min(seconds, 0.03), int(freq)) * env_pluck(min(seconds, 0.03),
                                                             curve=40.0)
    out = body
    out[:len(knock)] += knock * 0.35
    return saturate(out, 1.8) * 0.42 * gain


def bell(freq: float, seconds: float = 3.0, gain: float = 1.0) -> np.ndarray:
    """A distant bell.  Inharmonic, so it never quite resolves."""
    out = np.zeros(int(seconds * SR))
    for ratio, level, curve in ((1.0, 1.0, 1.6), (2.01, 0.5, 2.4),
                                (2.98, 0.28, 3.4), (4.21, 0.14, 5.0),
                                (5.43, 0.08, 7.0)):
        out += sine(freq * ratio, seconds) * env_pluck(seconds, curve=curve) * level
    return out * 0.30 * gain


def pad(freq: float, seconds: float = 6.0, gain: float = 1.0,
        cutoff: float = 1400.0) -> np.ndarray:
    """A slow chord voice: three detuned saws, filtered until they stop biting."""
    raw = detuned(lambda f, s: saw(f, s, harmonics=8), freq, seconds,
                  cents=9.0, voices=3)
    raw = lowpass_fast(raw, cutoff, passes=2)
    shape = env_adsr(seconds, attack=seconds * 0.32, decay=seconds * 0.1,
                     sustain=0.82, release=seconds * 0.4)
    return raw * shape * 0.24 * gain


def glass(freq: float, seconds: float = 4.0, gain: float = 1.0) -> np.ndarray:
    """A high sine that arrives late and leaves slowly."""
    body = sine(freq, seconds) + sine(freq * 2.002, seconds) * 0.3
    shape = env_adsr(seconds, attack=seconds * 0.45, decay=0.1, sustain=0.8,
                     release=seconds * 0.45)
    return body * shape * 0.18 * gain


def sub(freq: float, seconds: float = 4.0, gain: float = 1.0) -> np.ndarray:
    """The floor of the mix.  Felt more than heard."""
    body = sine(freq, seconds) + sine(freq * 1.004, seconds) * 0.5
    shape = env_adsr(seconds, attack=seconds * 0.25, decay=0.2, sustain=0.85,
                     release=seconds * 0.35)
    return body * shape * 0.30 * gain


def blip(freq: float, seconds: float = 0.18, gain: float = 1.0) -> np.ndarray:
    """Chiptune square, for the worlds that know they are made of data."""
    body = square(freq, seconds, harmonics=6)
    return body * env_pluck(seconds, attack=0.002, curve=6.0) * 0.20 * gain


def pluck(freq: float, seconds: float = 1.2, gain: float = 1.0,
          damping: float = 0.5) -> np.ndarray:
    """Karplus-Strong: a plucked string, cheap and slightly unreal."""
    n = int(seconds * SR)
    period = max(2, int(SR / freq))
    rng = np.random.default_rng(int(freq * 100) % 9973)
    buffer = rng.uniform(-1, 1, period)
    out = np.empty(n)
    index = 0
    previous = 0.0
    for sample in range(n):
        value = buffer[index]
        averaged = (value + previous) * 0.5 * (1.0 - damping * 0.02)
        buffer[index] = averaged
        previous = value
        out[sample] = value
        index = (index + 1) % period
    return out * env_pluck(seconds, curve=2.2) * 0.26 * gain


def breath(seconds: float = 4.0, seed: int = 0, gain: float = 1.0,
           cutoff: float = 700.0) -> np.ndarray:
    """Wind, or a room's own hiss.  Never quite silent."""
    raw = noise(seconds, seed)
    raw = lowpass_fast(raw, cutoff, passes=3)
    swell = 0.6 + 0.4 * np.sin(np.linspace(0, 2 * np.pi * 2, len(raw)))
    return raw * swell * 0.5 * gain


def drop(seconds: float = 0.5, freq: float = 900.0,
         gain: float = 1.0) -> np.ndarray:
    """A single drip: a sine sliding up, which is what makes it read as water."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    sweep = freq * (1 + 1.6 * t / seconds)
    phase = 2 * np.pi * np.cumsum(sweep) / SR
    return np.sin(phase) * env_pluck(seconds, curve=9.0) * 0.30 * gain


def tick(seconds: float = 0.08, gain: float = 1.0, seed: int = 1) -> np.ndarray:
    """A clock, a footstep, a switch."""
    raw = noise(seconds, seed)
    raw = lowpass_fast(raw, 2600, passes=1)
    return raw * env_pluck(seconds, attack=0.001, curve=30.0) * 0.5 * gain


def hum(freq: float, seconds: float = 8.0, gain: float = 1.0) -> np.ndarray:
    """Electrical hum: a fundamental with its odd harmonics, barely moving."""
    out = sine(freq, seconds)
    out += sine(freq * 2, seconds) * 0.4
    out += sine(freq * 3, seconds) * 0.18
    lfo = 1.0 + 0.06 * np.sin(np.linspace(0, 2 * np.pi * 3, len(out)))
    return out * lfo * 0.12 * gain


def choir(freq: float, seconds: float = 6.0, gain: float = 1.0) -> np.ndarray:
    """Almost voices.  Formant-ish peaks over a detuned pair."""
    base = detuned(lambda f, s: triangle(f, s, harmonics=9), freq, seconds,
                   cents=12.0, voices=4)
    formant = sine(freq * 3.1, seconds) * 0.16 + sine(freq * 5.2, seconds) * 0.08
    body = lowpass_fast(base + formant, 1800, passes=2)
    shape = env_adsr(seconds, attack=seconds * 0.35, decay=0.2, sustain=0.8,
                     release=seconds * 0.4)
    return body * shape * 0.20 * gain


def shepard(seconds: float, base: float = 55.0, octaves: int = 7,
            cycles: int = 1, gain: float = 1.0) -> np.ndarray:
    """An endlessly rising tone.

    Each voice climbs an octave over the loop while fading in from silence at
    the bottom and out at the top, so the pitch appears to rise forever and
    the buffer still joins to itself perfectly.
    """
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    ramp = (t / seconds * cycles) % 1.0
    for index in range(octaves):
        position = (ramp + index / octaves) % 1.0
        freq = base * (2.0 ** (position * octaves))
        phase = 2 * np.pi * np.cumsum(freq) / SR
        # a raised cosine window in log-frequency: silent at both ends
        window = 0.5 - 0.5 * np.cos(2 * np.pi * position)
        out += np.sin(phase) * window
    return out / octaves * 0.5 * gain
