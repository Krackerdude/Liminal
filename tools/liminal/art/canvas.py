"""A small pixel-pushing toolkit.

Everything LIMINAL looks like is drawn here from scratch: 16x16 tiles, 24x32
sprites, window frames, title cards.  The house style is flat colour plus
ordered dithering — the palette does the emotional work, the dither keeps it
from looking like clean vector art, and nothing is ever antialiased.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

RGB = tuple[int, int, int]

# The colour reserved for palette index 0.  RPG Maker treats the first palette
# entry of an indexed PNG as transparent, and this magenta is the traditional
# choice — it never appears by accident in real artwork.
TRANSPARENT: RGB = (255, 0, 255)

# Ordered dither matrices, normalised to 0..1 thresholds.
BAYER4 = np.array([
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
], dtype=np.float64) / 16.0

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=np.float64) / 64.0


class Canvas:
    """An RGB image with integer coordinates and wrap-around drawing."""

    def __init__(self, width: int, height: int, fill: RGB = TRANSPARENT):
        self.w = width
        self.h = height
        self.px = np.zeros((height, width, 3), dtype=np.uint8)
        self.px[:, :] = fill

    # -- construction --------------------------------------------------------
    @classmethod
    def from_array(cls, array: np.ndarray) -> "Canvas":
        canvas = cls(array.shape[1], array.shape[0])
        canvas.px = array.astype(np.uint8).copy()
        return canvas

    def copy(self) -> "Canvas":
        return Canvas.from_array(self.px)

    def sub(self, x: int, y: int, w: int, h: int) -> "Canvas":
        return Canvas.from_array(self.px[y:y + h, x:x + w])

    def paste(self, other: "Canvas", x: int, y: int,
              mask: RGB | None = None) -> "Canvas":
        """Blit ``other`` at (x, y), optionally treating ``mask`` as see-through."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + other.w), min(self.h, y + other.h)
        if x0 >= x1 or y0 >= y1:
            return self
        src = other.px[y0 - y:y1 - y, x0 - x:x1 - x]
        if mask is None:
            self.px[y0:y1, x0:x1] = src
        else:
            keep = np.any(src != np.array(mask, dtype=np.uint8), axis=-1)
            region = self.px[y0:y1, x0:x1]
            region[keep] = src[keep]
        return self

    # -- primitives ----------------------------------------------------------
    def fill(self, color: RGB) -> "Canvas":
        self.px[:, :] = color
        return self

    def rect(self, x: int, y: int, w: int, h: int, color: RGB) -> "Canvas":
        """Fill a rectangle, clipped to the canvas.

        Clipping rather than wrapping: a shape that runs off the bottom of a
        sprite cell should be cut off, not reappear on its head.  Use
        :meth:`dot`, :meth:`hline` and :meth:`vline` when you do want the
        wrap-around behaviour that makes a tile seamless.
        """
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x0 < x1 and y0 < y1:
            self.px[y0:y1, x0:x1] = color
        return self

    def outline(self, x: int, y: int, w: int, h: int, color: RGB) -> "Canvas":
        self.rect(x, y, w, 1, color)
        self.rect(x, y + h - 1, w, 1, color)
        self.rect(x, y, 1, h, color)
        self.rect(x + w - 1, y, 1, h, color)
        return self

    def dot(self, x: int, y: int, color: RGB) -> "Canvas":
        self.px[y % self.h, x % self.w] = color
        return self

    def get(self, x: int, y: int) -> RGB:
        return tuple(int(v) for v in self.px[y % self.h, x % self.w])  # type: ignore

    def hline(self, y: int, x0: int, x1: int, color: RGB) -> "Canvas":
        return self.rect(min(x0, x1), y, abs(x1 - x0) + 1, 1, color)

    def vline(self, x: int, y0: int, y1: int, color: RGB) -> "Canvas":
        return self.rect(x, min(y0, y1), 1, abs(y1 - y0) + 1, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: RGB) -> "Canvas":
        steps = max(abs(x1 - x0), abs(y1 - y0))
        if steps == 0:
            return self.dot(x0, y0, color)
        for i in range(steps + 1):
            t = i / steps
            self.dot(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), color)
        return self

    def round_rect(self, x: int, y: int, w: int, h: int, radius: int,
                   color: RGB) -> "Canvas":
        """A rectangle with its corners knocked off.

        Rounded forms are the backbone of the whole look — almost nothing in
        this game has a true 90-degree corner.
        """
        radius = max(0, min(radius, min(w, h) // 2))
        self.rect(x + radius, y, w - 2 * radius, h, color)
        self.rect(x, y + radius, w, h - 2 * radius, color)
        for cx, cy, sx, sy in ((x + radius, y + radius, -1, -1),
                               (x + w - 1 - radius, y + radius, 1, -1),
                               (x + radius, y + h - 1 - radius, -1, 1),
                               (x + w - 1 - radius, y + h - 1 - radius, 1, 1)):
            for dy in range(radius + 1):
                for dx in range(radius + 1):
                    if dx * dx + dy * dy <= radius * radius + radius:
                        self.dot(cx + sx * dx, cy + sy * dy, color)
        return self

    def blob(self, cx: float, cy: float, r: float, color: RGB,
             squash: float = 1.0) -> "Canvas":
        """A soft round mass — clouds, bushes, canopies, heads."""
        return self.ellipse(cx, cy, r, r * squash, color)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float,
                color: RGB, filled: bool = True) -> "Canvas":
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        d = ((xs - cx) / max(rx, 0.001)) ** 2 + ((ys - cy) / max(ry, 0.001)) ** 2
        mask = d <= 1.0 if filled else (d <= 1.0) & (d >= 0.55)
        self.px[mask] = color
        return self

    # -- texture -------------------------------------------------------------
    def dither(self, color: RGB, amount: float, matrix: np.ndarray = BAYER4,
               offset: tuple[int, int] = (0, 0), region: np.ndarray | None = None
               ) -> "Canvas":
        """Sprinkle ``color`` over the canvas at ``amount`` density (0..1)."""
        n = matrix.shape[0]
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        threshold = matrix[(ys + offset[1]) % n, (xs + offset[0]) % n]
        mask = threshold < amount
        if region is not None:
            mask &= region
        self.px[mask] = color
        return self

    def noise(self, colors: Sequence[RGB], density: float, seed: int,
              region: np.ndarray | None = None) -> "Canvas":
        rng = np.random.default_rng(seed)
        mask = rng.random((self.h, self.w)) < density
        if region is not None:
            mask &= region
        pick = rng.integers(0, len(colors), size=(self.h, self.w))
        for index, color in enumerate(colors):
            self.px[mask & (pick == index)] = color
        return self

    def value_noise(self, seed: int, scale: int = 4, octaves: int = 3) -> np.ndarray:
        """Smooth 0..1 noise field, used for grime and lighting falloff."""
        rng = np.random.default_rng(seed)
        field = np.zeros((self.h, self.w), dtype=np.float64)
        total = 0.0
        for octave in range(octaves):
            step = max(1, scale // (2 ** octave))
            gh, gw = self.h // step + 2, self.w // step + 2
            grid = rng.random((gh, gw))
            ys = np.clip(np.arange(self.h) / step, 0, gh - 1.001)
            xs = np.clip(np.arange(self.w) / step, 0, gw - 1.001)
            y0, x0 = ys.astype(int), xs.astype(int)
            fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
            fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
            a = grid[np.ix_(y0, x0)]
            b = grid[np.ix_(y0, x0 + 1)]
            c = grid[np.ix_(y0 + 1, x0)]
            d = grid[np.ix_(y0 + 1, x0 + 1)]
            weight = 0.5 ** octave
            field += weight * ((a * (1 - fx) + b * fx) * (1 - fy) +
                               (c * (1 - fx) + d * fx) * fy)
            total += weight
        return field / total

    def stripes(self, color: RGB, period: int, width: int = 1,
                vertical: bool = False, offset: int = 0) -> "Canvas":
        if vertical:
            for x in range(offset, self.w, period):
                self.rect(x, 0, width, self.h, color)
        else:
            for y in range(offset, self.h, period):
                self.rect(0, y, self.w, width, color)
        return self

    def checker(self, a: RGB, b: RGB, size: int) -> "Canvas":
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        mask = ((xs // size) + (ys // size)) % 2 == 0
        self.px[mask] = a
        self.px[~mask] = b
        return self

    def scanlines(self, darkness: float = 0.85, period: int = 2) -> "Canvas":
        for y in range(0, self.h, period):
            row = self.px[y].astype(np.float64) * darkness
            self.px[y] = np.clip(row, 0, 255).astype(np.uint8)
        return self

    # -- colour --------------------------------------------------------------
    def shade(self, factor: float, region: np.ndarray | None = None) -> "Canvas":
        """Multiply brightness.  <1 darkens, >1 lightens."""
        target = self.px.astype(np.float64) * factor
        target = np.clip(target, 0, 255).astype(np.uint8)
        if region is None:
            self.px = target
        else:
            self.px[region] = target[region]
        return self

    def mix(self, color: RGB, amount: float,
            region: np.ndarray | None = None) -> "Canvas":
        """Blend towards a flat colour — the cheapest way to unify a palette."""
        tint = np.array(color, dtype=np.float64)
        target = self.px.astype(np.float64) * (1 - amount) + tint * amount
        target = np.clip(target, 0, 255).astype(np.uint8)
        if region is None:
            self.px = target
        else:
            self.px[region] = target[region]
        return self

    def modulate(self, field: np.ndarray, low: float = 0.8,
                 high: float = 1.15) -> "Canvas":
        """Scale brightness by a 0..1 field mapped onto ``low``..``high``."""
        factor = (low + field * (high - low))[:, :, None]
        self.px = np.clip(self.px.astype(np.float64) * factor, 0, 255).astype(np.uint8)
        return self

    def vignette(self, strength: float = 0.5, power: float = 2.0) -> "Canvas":
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        cx, cy = (self.w - 1) / 2, (self.h - 1) / 2
        d = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2) / math.sqrt(2)
        factor = (1 - strength * np.clip(d, 0, 1) ** power)[:, :, None]
        self.px = np.clip(self.px.astype(np.float64) * factor, 0, 255).astype(np.uint8)
        return self

    def replace(self, old: RGB, new: RGB) -> "Canvas":
        mask = np.all(self.px == np.array(old, dtype=np.uint8), axis=-1)
        self.px[mask] = new
        return self

    # -- transforms ----------------------------------------------------------
    def flip_h(self) -> "Canvas":
        return Canvas.from_array(self.px[:, ::-1])

    def roll(self, dx: int, dy: int) -> "Canvas":
        return Canvas.from_array(np.roll(np.roll(self.px, dy, axis=0), dx, axis=1))

    def scale(self, factor: int) -> "Canvas":
        return Canvas.from_array(np.repeat(np.repeat(self.px, factor, axis=0),
                                           factor, axis=1))


def shade_of(color: RGB, factor: float) -> RGB:
    return tuple(int(max(0, min(255, c * factor))) for c in color)  # type: ignore


def cooler(color: RGB, amount: float = 0.22) -> RGB:
    """A shadow tone: darker, and pushed towards blue.

    Shifting the hue instead of only dropping the value is what keeps a
    three-colour sprite from looking like a three-colour sprite.
    """
    r, g, b = color
    return (int(max(0, r * (1 - amount * 1.35))),
            int(max(0, g * (1 - amount * 1.1))),
            int(max(0, min(255, b * (1 - amount * 0.55) + 14 * amount))))


def warmer(color: RGB, amount: float = 0.18) -> RGB:
    """A highlight tone: lighter, and pushed towards yellow."""
    r, g, b = color
    return (int(min(255, r + (255 - r) * amount * 1.25)),
            int(min(255, g + (255 - g) * amount * 1.05)),
            int(min(255, b + (255 - b) * amount * 0.55)))


def outline_in(canvas: "Canvas", color: RGB | None = None,
               darken: float = 0.62) -> "Canvas":
    """Trace a border around the sprite using a darker *local* colour.

    Passing ``color`` forces a single outline tone; leaving it ``None`` samples
    the nearest solid pixel and darkens that, so a green tree is outlined in
    dark green rather than in black.
    """
    solid = np.any(canvas.px != np.array(TRANSPARENT, dtype=np.uint8), axis=-1)
    grown = np.zeros_like(solid)
    neighbour = np.zeros(canvas.px.shape, dtype=np.uint8)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        shifted = np.roll(np.roll(solid, dy, axis=0), dx, axis=1)
        fresh = shifted & ~grown
        grown |= shifted
        rolled = np.roll(np.roll(canvas.px, dy, axis=0), dx, axis=1)
        neighbour[fresh] = rolled[fresh]
    edge = grown & ~solid
    if color is not None:
        canvas.px[edge] = color
    else:
        tinted = np.clip(neighbour.astype(np.float64) * darken, 0, 255).astype(np.uint8)
        canvas.px[edge] = tinted[edge]
    return canvas


def blend(a: RGB, b: RGB, t: float) -> RGB:
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))  # type: ignore


def ramp(base: RGB, steps: int, low: float = 0.55,
         high: float = 1.35) -> list[RGB]:
    """A shading ramp for one hue — the backbone of every tile in the game."""
    if steps == 1:
        return [base]
    return [shade_of(base, low + (high - low) * i / (steps - 1))
            for i in range(steps)]


def save_indexed(canvas: Canvas, path: str, *,
                 transparent: bool = True, max_colors: int = 256) -> None:
    """Write an 8-bit PNG with ``TRANSPARENT`` pinned to palette index 0.

    RPG Maker (and EasyRPG Player) key transparency off palette index 0, so
    every charset, chipset and picture in the game has to come out this way.
    """
    from PIL import Image

    image = Image.fromarray(canvas.px, mode="RGB")
    reserved = 1 if transparent else 0
    quantized = image.quantize(colors=max(2, max_colors - reserved),
                               method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)

    palette = quantized.getpalette() or []
    indices = np.array(quantized, dtype=np.uint8)

    if transparent:
        # Shift every index up by one and drop TRANSPARENT into slot 0.
        indices = indices + 1
        palette = list(TRANSPARENT) + palette
        mask = np.all(canvas.px == np.array(TRANSPARENT, dtype=np.uint8), axis=-1)
        indices[mask] = 0

    palette = (palette + [0] * 768)[:768]
    out = Image.fromarray(indices, mode="P")
    out.putpalette(palette)
    out.save(path, optimize=True)


def tile_grid(canvas: Canvas, size: int = 16) -> Iterable[tuple[int, int, Canvas]]:
    for row in range(canvas.h // size):
        for col in range(canvas.w // size):
            yield col, row, canvas.sub(col * size, row * size, size, size)
