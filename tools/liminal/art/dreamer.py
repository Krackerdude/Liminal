"""The player.

This sprite is not generated.  It is the author's own artwork, transcribed
pixel for pixel out of ``Sprite References/Screenshot 2026-08-04 214834.png``
and re-laid into the charset layout RPG Maker wants.  Nothing in this module
draws a figure: every colour on it is a colour lifted from that file.

The reference sheet is four columns of directions by three rows of frames, at
eight times scale on an Aseprite transparency checker:

    column 0  back      column 1  front      column 2  right      column 3  left
    rows      the three walk frames, in order

RPG Maker wants the transpose — three frames across, four directions down, in
the order up, right, down, left — so the transcription reorders the cells and
centres each one in a 24x32 cell with its feet on the floor.

The thirteen selves are the same artwork with one non-destructive change each:
a halo behind it, a translucency pass over it, or one small object beside it.
None of them repaint the figure, because the figure is not mine to repaint.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from .canvas import Canvas, RGB, TRANSPARENT, blend

CELL_W, CELL_H = 24, 32
GROUND = 30
CX = 12

UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3

_HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.normpath(os.path.join(
    _HERE, "..", "..", "..", "Sprite References",
    "Screenshot 2026-08-04 214834.png"))

# Measured off the file: eight times scale, an Aseprite checker behind it, and
# the sprite bands at these native coordinates.  Which column is which facing
# was settled by counting skin pixels and where their centroid sits — the back
# view has almost none, the front has them centred, and the two profiles have
# them offset to their own side.
SCALE = 8
CHECKER = ((192, 192, 192), (128, 128, 128))
COLUMNS = {UP: (9, 24), RIGHT: (44, 58), DOWN: (26, 41), LEFT: (61, 75)}
ROWS = ((5, 33), (36, 63), (66, 93))


def _sheet() -> tuple[np.ndarray, np.ndarray]:
    """The reference at native resolution, with the checker knocked out."""
    from PIL import Image

    a = np.array(Image.open(REFERENCE).convert("RGBA"))[::SCALE, ::SCALE]
    solid = a[:, :, 3] > 128
    for colour in CHECKER:
        solid &= ~np.all(a[:, :, :3] == np.array(colour, np.uint8), axis=-1)
    return a[:, :, :3], solid


_CACHE: dict[tuple[int, int], Canvas] = {}


def _source(facing: int, frame: int) -> Canvas:
    """One cell of the reference, centred in 24x32 with its feet on the floor."""
    key = (facing, frame)
    if key in _CACHE:
        return _CACHE[key]
    rgb, solid = _sheet()
    x0, x1 = COLUMNS[facing]
    y0, y1 = ROWS[frame]
    sub, mask = rgb[y0:y1 + 1, x0:x1 + 1], solid[y0:y1 + 1, x0:x1 + 1]

    # Trim to what is actually drawn, so the figure is placed by its own
    # extents rather than by whatever band the screenshot happened to have.
    ys, xs = np.nonzero(mask)
    sub = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    mask = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
    left = CX - sub.shape[1] // 2
    top = GROUND - sub.shape[0]
    for row in range(sub.shape[0]):
        for col in range(sub.shape[1]):
            if not mask[row, col]:
                continue
            px, py = left + col, top + row
            if 0 <= px < CELL_W and 0 <= py < CELL_H:
                cell.px[py, px] = sub[row, col]
    _CACHE[key] = cell
    return cell


@dataclass
class Dreamer:
    """One of the thirteen selves.

    An effect never repaints the artwork.  It adds a halo, makes the figure
    translucent, or puts one small object beside it, and that is all.
    """
    name: str = "plain"
    translucent: bool = False
    glow: RGB | None = None
    carry: str = ""
    feature: str = ""
    feature_color: RGB = (198, 190, 176)


# --- what an effect adds -----------------------------------------------------

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
    dark = blend(tone, (18, 16, 24), 0.45)
    lit = blend(tone, (255, 250, 242), 0.22)
    top = 1

    if spec.feature == "cone_hat":
        for row in range(6):
            width = 2 + row * 2
            _put(cell, CX - width // 2, top + row, width, 1,
                 lit if row < 2 else tone)
        _put(cell, CX - 7, top + 6, 15, 1, dark)
    elif spec.feature == "wide_hat":
        _put(cell, CX - 10, top + 4, 21, 2, dark)
        _put(cell, CX - 5, top + 1, 11, 3, tone)
        _put(cell, CX - 5, top + 1, 11, 1, lit)
    elif spec.feature == "ears":
        for x in (CX - 9, CX + 6):
            _put(cell, x, top, 3, 4, tone)
            _put(cell, x, top, 3, 1, lit)
    elif spec.feature == "antenna":
        _put(cell, CX, top, 1, 4, dark)
        _put(cell, CX - 1, top, 3, 1, lit)
    elif spec.feature == "scarf":
        _put(cell, CX - 6, 15, 12, 2, tone)
        _put(cell, CX - 6, 16, 12, 1, dark)
        if facing != UP:
            _put(cell, CX + 3, 17, 3, 5, tone)


def _carried(cell: Canvas, spec: Dreamer, facing: int, frame: int) -> None:
    if facing == UP or not spec.carry:
        return
    y = 20 + (1 if frame == 2 else 0)
    x = CX + 6 if facing != LEFT else CX - 8

    if spec.carry == "lantern":
        _put(cell, x, y - 5, 1, 4, (120, 106, 88))
        _put(cell, x - 2, y - 1, 5, 5, (198, 178, 132))
        _put(cell, x - 1, y, 3, 3, (240, 228, 188))
    elif spec.carry == "pole":
        _put(cell, x, y - 12, 2, 18, (132, 112, 82))
        _put(cell, x, y - 12, 1, 18, (168, 148, 116))
    elif spec.carry == "ring":
        cell.ellipse(x, y, 3, 3, (188, 170, 118), filled=False)
    elif spec.carry == "can":
        _put(cell, x - 2, y - 2, 5, 6, (156, 142, 102))
        _put(cell, x - 2, y - 2, 2, 6, (118, 106, 76))
    elif spec.carry == "block":
        _put(cell, x - 3, y - 3, 7, 7, (150, 96, 96))
        _put(cell, x - 3, y - 3, 7, 1, (184, 130, 124))
    elif spec.carry == "tape":
        _put(cell, x - 3, y - 1, 6, 4, (162, 160, 166))
        cell.ellipse(x - 1, y, 1.4, 1.4, (66, 62, 70))


# --- sheets ------------------------------------------------------------------

def dreamer_cell(spec: Dreamer, facing: int, frame: int) -> Canvas:
    cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
    if spec.glow is not None:
        for radius, amount in ((9.0, 0.10), (6.0, 0.20), (4.0, 0.32)):
            halo = Canvas(CELL_W, CELL_H, TRANSPARENT)
            halo.blob(CX, 16, radius, blend(spec.glow, (255, 255, 255), amount))
            cell.paste(halo, 0, 0, mask=TRANSPARENT)
    cell.paste(_source(facing, frame), 0, 0, mask=TRANSPARENT)

    _feature(cell, spec, facing)
    _carried(cell, spec, facing, frame)
    if spec.translucent:
        solid = np.any(cell.px != np.array(TRANSPARENT, np.uint8), axis=-1)
        cell.mix((255, 255, 255), 0.42, region=solid)
    return cell


def dreamer_block(spec: Dreamer) -> Canvas:
    block = Canvas(CELL_W * 3, CELL_H * 4, TRANSPARENT)
    for facing in range(4):
        for frame in range(3):
            block.paste(dreamer_cell(spec, facing, frame),
                        frame * CELL_W, facing * CELL_H)
    return block
