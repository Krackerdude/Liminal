"""Materials: five values, hue-shifted, lit from one direction.

This is the foundation for the remastered art, and it exists because the first
pass at this game had no shared idea of what a surface *is*.  Every chipset
invented its own shading, so nothing matched anything, and where shading was
computed at all it came out as a smooth gradient or a field of Bayer noise.

A material here is five values derived from one base colour, and the derivation
is the whole point:

* **Shadows shift cool and slightly toward blue.**  Light that has bounced
  around a room before reaching a surface is bluer than light that arrived
  straight, so a shadow that is only "darker" reads as dirty rather than dim.
* **Highlights shift warm and desaturate.**  A lit face of a painted object
  loses colour as it approaches the light.
* **The step between values is uneven.**  Even steps read as a gradient; a
  larger jump into the darkest value and a small one at the top is what makes
  five colours describe a *plane* rather than a ramp.

Rules this module enforces so no chipset has to remember them:

**Planes, not gradients.**  ``plane`` fills a rectangle with one value and
``lit``/``shade`` name which value.  A surface is a small number of flat
regions, and the boundaries between them are where the form is.

**Dithering only at a boundary, and only two values wide.**  ``seam`` lays a
two-pixel dithered join between neighbouring values.  There is no function
here that will texture an area with a dither pattern, because that is the
thing that made the old sprites look like static.

**Edges are one value darker, not black.**  ``edge`` traces a shape in its own
ramp's next step down.  Nothing in the remastered art is outlined in black.

**Textures are structured, never random.**  ``boards``, ``bricks``, ``tiles``
and ``weave`` are all deterministic patterns with a stated grain direction.
There is no noise function in this module on purpose: "add some noise" is how
the first pass turned every surface into grit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .canvas import Canvas, RGB

# The light.  One direction for the whole game: from the upper left and
# slightly in front, which is why every top face is the lit one and every
# right-hand face is the shaded one.
LIGHT = (-1, -1)

# Where each value sits, darkest to lightest.  Deliberately uneven — see the
# module docstring.
STOPS = (0.0, 0.30, 0.55, 0.78, 1.0)


def _shift(base: RGB, amount: float) -> RGB:
    """Move a colour along the ramp, shifting hue as it goes.

    ``amount`` is -1 (deepest shadow) to +1 (highlight).  Shadows are pulled
    toward a cool blue-violet and gain saturation; highlights are pulled toward
    a warm off-white and lose it.  That single asymmetry is most of what makes
    these read as painted rather than as tinted.
    """
    r, g, b = (float(c) for c in base)
    if amount < 0:
        t = -amount
        # Toward a cool shadow.  Luminance comes off every channel by the same
        # factor, which preserves the hue, and *then* a small push toward blue
        # is added on top.  Scaling the channels by different amounts — which
        # is what this did first — desaturates as it darkens, so the shadow of
        # a warm lamp came out neutral grey and the object stopped being made
        # of anything.
        factor = 1 - 0.70 * t
        r, g, b = r * factor, g * factor, b * factor
        r -= 6 * t
        b += 16 * t
    else:
        t = amount
        # toward a warm light: gain luminance, gain red, desaturate
        grey = (r + g + b) / 3.0
        r = r + (255 - r) * 0.62 * t
        g = g + (250 - g) * 0.54 * t
        b = b + (232 - b) * 0.42 * t
        r = r * (1 - 0.18 * t) + grey * 0.18 * t
    return (int(max(0, min(255, r))), int(max(0, min(255, g))),
            int(max(0, min(255, b))))


@dataclass(frozen=True)
class Material:
    """One surface, as five values from dark to light.

    ``name`` is only for readability in the chipsets.  ``grain`` is the
    direction any structured texture runs, which the texture helpers read so a
    floorboard and a wall panel do not accidentally run the same way.
    """
    name: str
    base: RGB
    grain: str = "h"        # "h", "v" or "none"

    @property
    def ramp(self) -> tuple[RGB, RGB, RGB, RGB, RGB]:
        return (_shift(self.base, -0.85), _shift(self.base, -0.45),
                self.base, _shift(self.base, 0.34), _shift(self.base, 0.70))

    def value(self, index: int) -> RGB:
        return self.ramp[max(0, min(4, index))]

    # the four names every chipset uses instead of remembering indices
    @property
    def deep(self) -> RGB:
        return self.value(0)

    @property
    def shade(self) -> RGB:
        return self.value(1)

    @property
    def mid(self) -> RGB:
        return self.value(2)

    @property
    def lit(self) -> RGB:
        return self.value(3)

    @property
    def hot(self) -> RGB:
        return self.value(4)


_BAYER = np.array([[0, 2], [3, 1]], dtype=np.float64) / 4.0


def plane(art: Canvas, x: int, y: int, w: int, h: int, colour: RGB) -> None:
    """One flat region.  A surface is a handful of these and nothing else."""
    art.rect(x, y, w, h, colour)


def seam(art: Canvas, x: int, y: int, w: int, h: int, a: RGB, b: RGB, *,
         vertical: bool = False) -> None:
    """A two-pixel dithered join between two neighbouring values.

    This is the only place dithering happens.  It softens the boundary where
    two planes meet, which is what gives the surface its airbrushed quality
    without any of it becoming texture.
    """
    for row in range(h):
        for col in range(w):
            px, py = x + col, y + row
            if not (0 <= px < art.w and 0 <= py < art.h):
                continue
            t = (col / max(1, w - 1)) if vertical else (row / max(1, h - 1))
            art.px[py, px] = b if t > _BAYER[py % 2, px % 2] else a


def edge(art: Canvas, mat: Material, region: RGB, *, step: int = 1) -> None:
    """Trace a colour's border in its own ramp, one value down.

    Never black.  The old art outlined everything in a hard dark line and the
    result was a sheet of stickers rather than a room.
    """
    target = np.all(art.px == np.array(region, np.uint8), axis=-1)
    empty = ~target
    grown = np.zeros_like(target)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        grown |= np.roll(np.roll(target, dy, axis=0), dx, axis=1)
    ramp = mat.ramp
    try:
        index = ramp.index(tuple(region))
    except ValueError:
        index = 2
    art.px[grown & empty] = ramp[max(0, index - step)]


# --- structured textures ------------------------------------------------------
# Every one of these is deterministic and has a direction.  There is no noise
# function in this module, and adding one would undo the point of it.

def boards(art: Canvas, x: int, y: int, w: int, h: int, mat: Material, *,
           width: int = 6, vertical: bool = False) -> None:
    """Floorboards or panelling: long runs with a seam between each.

    The lit edge of every board is on the side the light comes from and the
    shadowed edge on the other, which is what makes a floor read as boards
    rather than as stripes.
    """
    plane(art, x, y, w, h, mat.mid)
    span = h if not vertical else w
    for offset in range(0, span, width):
        if vertical:
            art.rect(x + offset, y, 1, h, mat.lit)
            art.rect(x + offset + width - 1, y, 1, h, mat.shade)
        else:
            art.rect(x, y + offset, w, 1, mat.lit)
            art.rect(x, y + offset + width - 1, w, 1, mat.shade)


def bricks(art: Canvas, x: int, y: int, w: int, h: int, mat: Material, *,
           course: int = 5, stagger: bool = True) -> None:
    """Courses of brick, each with a lit top edge and a shaded underside."""
    plane(art, x, y, w, h, mat.mid)
    for row, cy in enumerate(range(y, y + h, course)):
        art.rect(x, cy, w, 1, mat.shade)
        if cy + 1 < y + h:
            art.rect(x, cy + 1, w, 1, mat.lit)
        offset = (row % 2) * (course + 1) if stagger else 0
        for bx in range(x + offset, x + w, course * 2 + 2):
            art.rect(bx, cy + 1, 1, min(course - 1, y + h - cy - 1), mat.shade)


def tiles(art: Canvas, x: int, y: int, w: int, h: int, mat: Material, *,
          size: int = 8) -> None:
    """A grid of tiles, grouted in the shadow value and lit along one corner."""
    plane(art, x, y, w, h, mat.mid)
    for gy in range(y, y + h, size):
        art.rect(x, gy, w, 1, mat.shade)
    for gx in range(x, x + w, size):
        art.rect(gx, y, 1, h, mat.shade)
    for gy in range(y, y + h, size):
        for gx in range(x, x + w, size):
            art.rect(gx + 1, gy + 1, min(2, w), 1, mat.lit)


def weave(art: Canvas, x: int, y: int, w: int, h: int, mat: Material, *,
          pitch: int = 4) -> None:
    """Cloth: a two-value basket weave, which reads as fabric at this size."""
    plane(art, x, y, w, h, mat.mid)
    for row in range(h):
        for col in range(w):
            px, py = x + col, y + row
            if not (0 <= px < art.w and 0 <= py < art.h):
                continue
            if ((col // (pitch // 2)) + (row // (pitch // 2))) % 2:
                art.px[py, px] = mat.shade


def sheen(art: Canvas, x: int, y: int, w: int, h: int, mat: Material) -> None:
    """A soft lit band across the top of a surface, dithered into the mid.

    The airbrushed part.  One band, two pixels of seam, and nothing else — a
    surface with two of these on it stops reading as a surface.
    """
    plane(art, x, y, w, max(1, h - 2), mat.lit)
    seam(art, x, y + max(1, h - 2), w, 2, mat.lit, mat.mid)
