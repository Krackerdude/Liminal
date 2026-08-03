"""A small synthesis toolkit.

Everything the game plays is generated here — there are no samples.  The
constraints that shape it: tracks must loop *seamlessly*, because a joint you
can hear breaks the spell faster than any wrong note; and everything should
sound like it has been through tape at least once.

Loops are kept seamless by making every periodic process complete a whole
number of cycles inside the buffer, and by wrapping delay and reverb tails
around to the start rather than letting them fade into silence at the end.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SR = 32000          # lo-fi on purpose: small files, and the right decade


# --- note names --------------------------------------------------------------

_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name: str) -> float:
    """``"A4"`` / ``"C#3"`` / ``"Eb5"`` to hertz."""
    letter = name[0].upper()
    rest = name[1:]
    semitone = _SEMITONES[letter]
    while rest and rest[0] in "#b":
        semitone += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    midi = 12 * (octave + 1) + semitone
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def scale(root: str, intervals: tuple[int, ...], count: int) -> list[float]:
    """Build a run of frequencies from a root and a set of intervals."""
    base = note(root)
    out = []
    for index in range(count):
        step = intervals[index % len(intervals)]
        octave = index // len(intervals)
        out.append(base * (2.0 ** ((step + 12 * octave) / 12.0)))
    return out


MINOR_PENT = (0, 3, 5, 7, 10)
MAJOR_PENT = (0, 2, 4, 7, 9)
AEOLIAN = (0, 2, 3, 5, 7, 8, 10)
LYDIAN = (0, 2, 4, 6, 7, 9, 11)
WHOLE_TONE = (0, 2, 4, 6, 8, 10)


# --- buffers -----------------------------------------------------------------

def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SR), dtype=np.float64)


def _t(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SR


def add(buffer: np.ndarray, part: np.ndarray, at: float,
        gain: float = 1.0) -> np.ndarray:
    """Mix ``part`` into ``buffer`` at a time offset, wrapping past the end.

    Wrapping is what lets a note that starts near the end of a loop finish at
    the beginning of the next pass without a click.
    """
    start = int(at * SR) % len(buffer)
    n = len(part)
    if n == 0:
        return buffer
    idx = (np.arange(n) + start) % len(buffer)
    np.add.at(buffer, idx, part * gain)
    return buffer


# --- oscillators -------------------------------------------------------------

def sine(freq: float, seconds: float, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * freq * _t(int(seconds * SR)) + phase)


def triangle(freq: float, seconds: float, harmonics: int = 7) -> np.ndarray:
    """Band-limited triangle: soft, hollow, the workhorse for melodies."""
    out = np.zeros(int(seconds * SR))
    t = _t(len(out))
    for k in range(harmonics):
        n = 2 * k + 1
        out += ((-1) ** k) * np.sin(2 * np.pi * freq * n * t) / (n * n)
    return out * (8 / (np.pi ** 2))


def square(freq: float, seconds: float, harmonics: int = 9) -> np.ndarray:
    out = np.zeros(int(seconds * SR))
    t = _t(len(out))
    for k in range(harmonics):
        n = 2 * k + 1
        out += np.sin(2 * np.pi * freq * n * t) / n
    return out * (4 / np.pi)


def saw(freq: float, seconds: float, harmonics: int = 12) -> np.ndarray:
    out = np.zeros(int(seconds * SR))
    t = _t(len(out))
    for n in range(1, harmonics + 1):
        out += ((-1) ** (n + 1)) * np.sin(2 * np.pi * freq * n * t) / n
    return out * (2 / np.pi)


def noise(seconds: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0, 0.32, int(seconds * SR))


def detuned(osc, freq: float, seconds: float, cents: float = 7.0,
            voices: int = 3) -> np.ndarray:
    """Stack slightly mistuned copies.  This is most of the dream in the sound."""
    out = np.zeros(int(seconds * SR))
    for index in range(voices):
        offset = (index - (voices - 1) / 2) * cents
        out += osc(freq * (2 ** (offset / 1200.0)), seconds)
    return out / voices


# --- envelopes ---------------------------------------------------------------

def env_adsr(seconds: float, attack: float = 0.01, decay: float = 0.1,
             sustain: float = 0.7, release: float = 0.3) -> np.ndarray:
    n = int(seconds * SR)
    out = np.zeros(n)
    a = min(int(attack * SR), n)
    d = min(int(decay * SR), max(0, n - a))
    r = min(int(release * SR), max(0, n - a - d))
    s = max(0, n - a - d - r)
    pos = 0
    if a:
        out[pos:pos + a] = np.linspace(0, 1, a)
        pos += a
    if d:
        out[pos:pos + d] = np.linspace(1, sustain, d)
        pos += d
    if s:
        out[pos:pos + s] = sustain
        pos += s
    if r:
        out[pos:pos + r] = np.linspace(sustain, 0, r)
    return out


def env_pluck(seconds: float, attack: float = 0.004,
              curve: float = 4.0) -> np.ndarray:
    """A struck envelope — bells, music box, toy piano."""
    n = int(seconds * SR)
    out = np.exp(-curve * np.linspace(0, 1, n))
    a = max(1, int(attack * SR))
    out[:a] *= np.linspace(0, 1, a)
    return out


def env_swell(seconds: float, peak: float = 0.5) -> np.ndarray:
    """Slow in, slow out.  For pads that arrive rather than start."""
    n = int(seconds * SR)
    x = np.linspace(0, 1, n)
    return np.sin(np.pi * np.clip(x / (2 * peak), 0, 1) *
                  np.where(x < peak, 1, 0) +
                  np.where(x >= peak, np.pi / 2 +
                           (x - peak) / (1 - peak + 1e-9) * np.pi / 2, 0))


def env_fade(buffer: np.ndarray, seconds: float = 0.01) -> np.ndarray:
    n = min(int(seconds * SR), len(buffer) // 2)
    if n <= 0:
        return buffer
    buffer[:n] *= np.linspace(0, 1, n)
    buffer[-n:] *= np.linspace(1, 0, n)
    return buffer


# --- filters and colour ------------------------------------------------------

def lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """One-pole lowpass.  Gentle, and cheap enough to use everywhere."""
    alpha = 1 - math.exp(-2 * math.pi * cutoff / SR)
    out = np.empty_like(x)
    acc = 0.0
    for index in range(len(x)):
        acc += alpha * (x[index] - acc)
        out[index] = acc
    return out


def lowpass_fast(x: np.ndarray, cutoff: float, passes: int = 1) -> np.ndarray:
    """A box-blur approximation of a lowpass — vectorised, so usable on pads."""
    width = max(1, int(SR / max(cutoff, 1.0)))
    out = x
    for _ in range(passes):
        kernel = np.ones(width) / width
        out = np.convolve(np.concatenate([out[-width:], out, out[:width]]),
                          kernel, mode="same")[width:-width]
    return out


def highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return x - lowpass_fast(x, cutoff, passes=2)


def saturate(x: np.ndarray, amount: float = 1.5) -> np.ndarray:
    return np.tanh(x * amount) / np.tanh(amount)


def bitcrush(x: np.ndarray, bits: int = 8) -> np.ndarray:
    levels = 2 ** bits
    return np.round(x * levels) / levels


def wrap_delay(x: np.ndarray, seconds: float, feedback: float = 0.35,
               mix: float = 0.3, taps: int = 6) -> np.ndarray:
    """A delay whose repeats wrap around the loop instead of trailing off."""
    out = x.copy()
    n = len(x)
    step = int(seconds * SR)
    if step <= 0:
        return out
    gain = feedback
    for tap in range(1, taps + 1):
        out += mix * gain * np.roll(x, (step * tap) % n)
        gain *= feedback
    return out


def wrap_reverb(x: np.ndarray, decay: float = 0.55, size: float = 0.09,
                mix: float = 0.35, stages: int = 5) -> np.ndarray:
    """A cheap smeared reverb built from wrapped, mutually prime delays."""
    n = len(x)
    wet = np.zeros(n)
    primes = (1.0, 1.37, 1.81, 2.29, 2.71, 3.19, 3.67)
    gain = 1.0
    for stage in range(stages):
        for prime in primes:
            step = int(size * prime * (stage + 1) * SR) % n
            wet += gain * np.roll(x, step)
        gain *= decay
    wet /= (len(primes) * stages)
    wet = lowpass_fast(wet, 3200, passes=2)
    return x * (1 - mix) + wet * mix * 3.0


def wobble(x: np.ndarray, rate: float = 0.7, depth: float = 0.0022,
           cycles: int | None = None) -> np.ndarray:
    """Tape flutter.

    The LFO is forced to complete a whole number of cycles across the buffer,
    so the pitch drift lines up perfectly when the loop comes round again.
    """
    n = len(x)
    if cycles is None:
        cycles = max(1, round(rate * n / SR))
    phase = np.linspace(0, 2 * np.pi * cycles, n, endpoint=False)
    offset = depth * SR * np.sin(phase)
    positions = (np.arange(n) + offset) % n
    left = np.floor(positions).astype(int)
    frac = positions - left
    right = (left + 1) % n
    return x[left] * (1 - frac) + x[right] * frac


def tape(x: np.ndarray, *, hiss: float = 0.0016, seed: int = 0,
         warmth: float = 1.4, top: float = 6500) -> np.ndarray:
    """Run a finished mix through the tape machine one last time."""
    out = saturate(x, warmth)
    out = lowpass_fast(out, top, passes=1)
    if hiss > 0:
        out = out + noise(len(x) / SR, seed) * hiss
    return out


def normalize(x: np.ndarray, peak: float = 0.86) -> np.ndarray:
    top = float(np.max(np.abs(x)))
    if top < 1e-9:
        return x
    return x * (peak / top)


# --- stereo ------------------------------------------------------------------

def widen(mono: np.ndarray, amount: float = 0.35,
          shift: float = 0.012) -> np.ndarray:
    """Turn a mono buffer into a gently wide stereo pair."""
    delay = int(shift * SR)
    left = mono + amount * np.roll(mono, delay)
    right = mono + amount * np.roll(mono, -delay)
    return np.stack([left, right], axis=-1)


def pan(mono: np.ndarray, position: float = 0.0) -> np.ndarray:
    """position: -1 hard left, 0 centre, +1 hard right."""
    angle = (position + 1) * math.pi / 4
    return np.stack([mono * math.cos(angle), mono * math.sin(angle)], axis=-1)


# --- writing -----------------------------------------------------------------

def to_wav_bytes(data: np.ndarray, sample_rate: int = SR) -> bytes:
    """Encode float audio in [-1, 1] as a 16-bit PCM RIFF file."""
    import struct

    if data.ndim == 1:
        channels = 1
        interleaved = data
    else:
        channels = data.shape[1]
        interleaved = data.reshape(-1)
    clipped = np.clip(interleaved, -1.0, 1.0)
    samples = (clipped * 32767.0).astype("<i2").tobytes()
    byte_rate = sample_rate * channels * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(samples)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate,
                                    byte_rate, channels * 2, 16)
    header += b"data" + struct.pack("<I", len(samples))
    return header + samples


def write_wav(path: str, data: np.ndarray, sample_rate: int = SR) -> None:
    with open(path, "wb") as handle:
        handle.write(to_wav_bytes(data, sample_rate))


@dataclass
class Sequencer:
    """Schedules notes onto a fixed-length looping buffer."""
    bars: int
    beats_per_bar: int = 4
    bpm: float = 72.0

    def __post_init__(self) -> None:
        self.beat = 60.0 / self.bpm
        self.length = self.bars * self.beats_per_bar * self.beat
        self.buffer = silence(self.length)

    def at(self, bar: float, beat: float = 0.0) -> float:
        return (bar * self.beats_per_bar + beat) * self.beat

    def play(self, part: np.ndarray, bar: float, beat: float = 0.0,
             gain: float = 1.0) -> None:
        add(self.buffer, part, self.at(bar, beat), gain)

    def render(self) -> np.ndarray:
        return self.buffer
