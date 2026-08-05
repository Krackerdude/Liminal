"""The player.

The drawing lives in :mod:`dreamer_art`, one glyph per value, hand-pixelled.
This module does two things and nothing else: it maps those glyphs to colours,
and it builds the twelve-cell charset block.

There is no shading code here.  Four earlier attempts computed the shading —
gradients, radial dome terms, Bayer dither across whole surfaces — and every
one of them pillow-shaded the sprite into a balloon.  Values are chosen by
hand in the art file, where they can be seen.

The palette is restrained on purpose: muted, low saturation, one accent.  The
shadows shift cooler and the highlights warmer within each material, and that
is the only rendering trick used anywhere on the figure.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import dreamer_art
from .canvas import Canvas, RGB, TRANSPARENT, blend

CELL_W, CELL_H = 24, 32
GROUND = 30
CX = 12

UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
FACING_NAME = {UP: "up", RIGHT: "right", DOWN: "down"}


# --- the palette -------------------------------------------------------------
# Four values for the hair, two for the skin, three for the sweater, two each
# for the shorts and the shoes.  Nothing is saturated: the sweater is the only
# thing on the sprite carrying colour at all, and it is a faded plum rather
# than a red, because a bright sweater on a quiet character is the character
# shouting.

HAIR = {
    "1": (34, 28, 36),      # the mass, in shadow
    "2": (54, 45, 56),      # the mass, lit
    "3": (76, 65, 76),      # the top plane — the part you see from up here
    "4": (104, 92, 100),
}
SKIN = {"5": (216, 186, 168), "6": (176, 142, 130)}
EYE = {"0": (38, 32, 40)}
SWEATER = {"7": (74, 56, 76), "8": (104, 84, 104), "9": (132, 112, 128)}
SHORTS = {"a": (48, 44, 56), "b": (66, 62, 74)}
SHOES = {"c": (62, 52, 44), "d": (88, 76, 62)}

INK: dict[str, RGB] = {**HAIR, **SKIN, **EYE, **SWEATER, **SHORTS, **SHOES}


@dataclass
class Dreamer:
    """One of the thirteen selves: plain, plus one per effect.

    An effect never redraws the figure.  It recolours one material, or adds a
    single shape to the silhouette, because the character has to read as the
    same dream object whatever they happen to be carrying.
    """
    name: str = "plain"
    sweater: tuple[RGB, RGB, RGB] | None = None
    hair: tuple[RGB, RGB, RGB, RGB] | None = None
    faceless: bool = False
    translucent: bool = False
    glow: RGB | None = None
    tall: int = 0
    feature: str = ""
    feature_color: RGB = (168, 158, 146)
    carry: str = ""

    def ink(self) -> dict[str, RGB]:
        table = dict(INK)
        if self.sweater:
            table.update(dict(zip("789", self.sweater)))
        if self.hair:
            table.update(dict(zip("1234", self.hair)))
        return table


# --- assembly ----------------------------------------------------------------

def _stamp(cell: Canvas, rows: list[str], table: dict[str, RGB], *,
           drop: int = 0) -> None:
    for y, row in enumerate(rows):
        if not 0 <= y + drop < cell.h:
            continue
        for x, glyph in enumerate(row):
            if glyph == "." or x >= cell.w:
                continue
            colour = table.get(glyph)
            if colour is not None:
                cell.px[y + drop, x] = colour


def _draw(spec: Dreamer, facing: int, frame: int) -> Canvas:
    cell = Canvas(CELL_W, CELL_H, TRANSPARENT)

    if spec.glow is not None:
        for radius, amount in ((9.0, 0.10), (6.0, 0.20), (4.0, 0.32)):
            halo = Canvas(CELL_W, CELL_H, TRANSPARENT)
            halo.blob(CX, 14, radius, blend(spec.glow, (255, 255, 255), amount))
            cell.paste(halo, 0, 0, mask=TRANSPARENT)

    rows = dreamer_art.grid(FACING_NAME[facing], frame)
    table = spec.ink()
    if spec.faceless:
        table = {k: v for k, v in table.items() if k != "0"}
    _stamp(cell, rows, table, drop=-(spec.tall // 3) if spec.tall else 0)

    _feature(cell, spec, facing)
    if spec.carry:
        _carried(cell, spec, facing, frame)

    if spec.translucent:
        solid = np.any(cell.px != np.array(TRANSPARENT, np.uint8), axis=-1)
        cell.mix((255, 255, 255), 0.42, region=solid)
    return cell


# --- what an effect changes --------------------------------------------------
# One shape each, and each one has to survive being read as a silhouette.

def _put(cell: Canvas, x: int, y: int, w: int, h: int, colour: RGB) -> None:
    for row in range(h):
        for col in range(w):
            px, py = x + col, y + row
            if 0 <= px < cell.w and 0 <= py < cell.h:
                cell.px[py, px] = colour


def _feature(cell: Canvas, spec: Dreamer, facing: int) -> None:
    if not spec.feature:
        return
    tone = spec.feature_color
    dark = blend(tone, (20, 18, 26), 0.45)
    lit = blend(tone, (255, 250, 240), 0.22)

    if spec.feature == "hat":
        _put(cell, 4, 1, 16, 2, dark)
        _put(cell, 6, 0, 12, 2, tone)
        _put(cell, 6, 0, 12, 1, lit)
    elif spec.feature == "wide_hat":
        _put(cell, 1, 2, 22, 2, dark)
        _put(cell, 6, 0, 12, 2, tone)
        _put(cell, 6, 0, 12, 1, lit)
    elif spec.feature == "cone_hat":
        for row in range(6):
            width = 2 + row * 2
            _put(cell, CX - width // 2, row, width, 1,
                 lit if row < 2 else tone)
        _put(cell, 5, 5, 14, 1, dark)
    elif spec.feature == "ears":
        for x in (3, 18):
            _put(cell, x, 0, 3, 4, tone)
            _put(cell, x, 0, 3, 1, lit)
    elif spec.feature == "antenna":
        _put(cell, CX, 0, 1, 3, dark)
        _put(cell, CX - 1, 0, 3, 1, lit)
    elif spec.feature == "scarf":
        _put(cell, 6, 15, 12, 2, tone)
        _put(cell, 6, 16, 12, 1, dark)
        if facing != UP:
            _put(cell, 14, 17, 3, 5, tone)
    elif spec.feature == "coat":
        _put(cell, 4, 18, 16, 9, tone)
        _put(cell, 4, 26, 16, 1, dark)
        if facing != UP:
            _put(cell, CX, 19, 1, 7, dark)


def _carried(cell: Canvas, spec: Dreamer, facing: int, frame: int) -> None:
    if facing == UP:
        return
    y = 21 + (1 if frame == 2 else 0)
    x = 18 if facing == RIGHT else 17

    if spec.carry == "lantern":
        _put(cell, x, y - 5, 1, 4, (120, 106, 88))
        _put(cell, x - 2, y - 1, 5, 5, (198, 178, 132))
        _put(cell, x - 1, y, 3, 3, (238, 226, 186))
    elif spec.carry == "pole":
        _put(cell, x, y - 12, 2, 18, (132, 112, 82))
        _put(cell, x, y - 12, 1, 18, (166, 146, 114))
    elif spec.carry == "ring":
        cell.ellipse(x, y, 3, 3, (186, 168, 116), filled=False)
    elif spec.carry == "can":
        _put(cell, x - 2, y - 2, 5, 6, (156, 142, 102))
        _put(cell, x - 2, y - 2, 2, 6, (118, 106, 76))
    elif spec.carry == "block":
        _put(cell, x - 3, y - 3, 7, 7, (150, 96, 96))
        _put(cell, x - 3, y - 3, 7, 1, (182, 128, 122))
    elif spec.carry == "tape":
        _put(cell, x - 3, y - 1, 6, 4, (162, 160, 166))
        cell.ellipse(x - 1, y, 1.4, 1.4, (66, 62, 70))


# --- sheets ------------------------------------------------------------------

def dreamer_cell(spec: Dreamer, facing: int, frame: int) -> Canvas:
    if facing == LEFT:
        return _draw(spec, RIGHT, frame).flip_h()
    return _draw(spec, facing, frame)


def dreamer_block(spec: Dreamer) -> Canvas:
    block = Canvas(CELL_W * 3, CELL_H * 4, TRANSPARENT)
    for facing in range(4):
        for frame in range(3):
            block.paste(dreamer_cell(spec, facing, frame),
                        frame * CELL_W, facing * CELL_H)
    return block
