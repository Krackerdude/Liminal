"""Bespoke residents, drawn per world and per facing.

Everything here is a drawing function rather than a body configuration.  A
palette swap with a different hat is a variant, not a character, and a sprite
whose back view is its front view with the eyes moved two pixels does not turn
around — it just stands there while the engine claims it turned.

So every design in this module draws its four facings *separately*:

**down**   the face: whatever this thing looks at you with
**up**     the back: no features at all, and a different silhouette
**side**   a profile: narrower, and built out of different parts

``tools/facings.py`` measures the result and fails anything under 12% change
on either axis.

Each function takes ``(cell, facing, frame)`` and paints into a 24x32 canvas
whose floor is at :data:`GROUND`.
"""

from __future__ import annotations

import math

from .canvas import Canvas, RGB, blend, cooler, warmer
from .charsets import (CELL_W as CELL_W_FULL, DOWN, GROUND, LEFT,
                        RIGHT, UP, _small_legs)

CX = 12


def _bob(frame: int) -> int:
    return (0, -1, 0)[frame]


def _mortar(cell: Canvas, x: int, y: int, w: int, h: int, brick: RGB,
            line: RGB, course: int = 5, offset: int = 0) -> None:
    """Brick coursing, drawn into a rectangle.  The pink world is made of it."""
    cell.rect(x, y, w, h, brick)
    for row, ry in enumerate(range(y + course - 1, y + h, course)):
        cell.hline(ry, x, x + w - 1, line)
        stagger = (row + offset) % 2 * (w // 2)
        for rx in range(x + stagger, x + w, max(3, w // 2)):
            cell.vline(rx, ry - course + 1, ry - 1, line)


# --- pink: a world made of brick, and so is everyone in it -------------------

def draw_measurer(cell: Canvas, facing: int, frame: int) -> None:
    """A column of bricks with a tape that has gone much too far.

    Front: two recessed eyes set into the coursing.  Back: unbroken coursing
    and the tape spool sunk into it.  Side: one brick deep, and the tape runs
    off the front of the cell.
    """
    b = _bob(frame)
    brick, line = (232, 168, 186), (196, 118, 146)
    dark, pale = (188, 112, 140), (248, 214, 224)
    side = facing in (LEFT, RIGHT)
    top = 5 + b

    if side:
        # One brick deep, and leaning the way it is going: the column itself is
        # offset, the lit edge is the leading edge, and the spool sits on the
        # front face rather than in the middle.
        reach = -1 if facing == LEFT else 1
        cx = CX + reach
        _mortar(cell, cx - 4, top, 8, GROUND - top - 4, dark, cooler(dark, 0.25))
        cell.vline(cx + (3 if reach > 0 else -4), top, GROUND - 5, pale)
        cell.vline(cx + (-4 if reach > 0 else 3), top, GROUND - 5,
                   cooler(dark, 0.45))
        _small_legs(cell, frame, cx, GROUND - 5, dark, spread=2)
        ty = top + 9
        cell.rect(cx + (1 if reach > 0 else -5), ty - 2, 5, 5, pale)
        cell.rect(cx + (5 * reach if reach > 0 else -11), ty, 7, 2,
                  warmer(pale, 0.3))
        cell.dot(cx + (11 * reach), ty, dark)
    else:
        _mortar(cell, CX - 6, top, 12, GROUND - top - 4, brick, line)
        _small_legs(cell, frame, CX, GROUND - 5, dark, spread=4)
        if facing == DOWN:
            # eyes are gaps in the wall, not features on a face
            for ex in (CX - 4, CX + 2):
                cell.rect(ex, top + 8, 3, 3, (44, 30, 44))
                cell.rect(ex, top + 8, 3, 1, cooler(line, 0.3))
            cell.rect(CX - 3, top + 15, 7, 1, line)
            # the spool, held out in front
            cell.rect(CX - 3, top + 18, 7, 6, pale)
            cell.rect(CX - 1, top + 20, 3, 2, dark)
        else:
            # from behind: no gaps at all, and the tape sunk into the back
            cell.rect(CX - 3, top + 12, 7, 6, cooler(brick, 0.18))
            cell.rect(CX - 2, top + 14, 5, 2, dark)


def draw_brick_child(cell: Canvas, facing: int, frame: int) -> None:
    """A small one whose head is a single brick, and knows it.

    The head is a cuboid, so it presents a face, a back and a short end — three
    genuinely different rectangles.
    """
    b = _bob(frame)
    brick, line = (240, 186, 200), (206, 130, 158)
    dark = (176, 106, 134)
    body = (250, 214, 224)
    side = facing in (LEFT, RIGHT)

    lead = -1 if facing == LEFT else 1
    hw = 7 if side else 13
    hx = CX - hw // 2 + (lead * 2 if side else 0)
    hy = 7 + b
    cell.rect(CX - (4 if side else 6) + (lead if side else 0), hy + 10,
              (8 if side else 12), GROUND - hy - 14, body)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    cell.rect(hx, hy, hw, 11, brick)
    cell.rect(hx, hy, hw, 1, warmer(brick, 0.3))
    cell.rect(hx, hy + 10, hw, 1, dark)
    if facing == DOWN:
        cell.hline(hy + 5, hx, hx + hw - 1, line)
        for ex in (hx + 2, hx + hw - 4):
            cell.rect(ex, hy + 2, 2, 2, (48, 32, 46))
        cell.rect(CX - 2, hy + 7, 4, 1, line)
    elif facing == UP:
        # From behind the head is a single unbroken face with one deep crack,
        # and the collar of the body shows above the shoulders — no coursing,
        # no gaps, nothing to look back at.
        cell.rect(hx + 1, hy + 1, hw - 2, 9, cooler(brick, 0.16))
        for cy in range(hy + 2, hy + 10):
            cell.dot(hx + 4 + (cy - hy) % 3, cy, dark)
        cell.rect(CX - 6, hy + 11, 12, 3, cooler(body, 0.22))
    else:
        # The short end of a brick: two courses deep, chipped on the leading
        # corner, and the whole head pushed forward off centre.
        cell.rect(hx + 1, hy + 1, hw - 2, 9, cooler(brick, 0.10))
        cell.hline(hy + 5, hx + 1, hx + hw - 2, line)
        chip = hx + hw - 2 if lead > 0 else hx + 1
        cell.rect(chip, hy + 1, 1, 3, dark)
        cell.vline(hx + hw - 1 if lead > 0 else hx, hy, hy + 10,
                   warmer(brick, 0.35))


def draw_wall_ear(cell: Canvas, facing: int, frame: int) -> None:
    """Mostly one enormous ear, pressed to a wall that is always there.

    An ear is the ideal thing to have to draw from four sides: flat and open
    from the front, a closed curve from behind, a thin blade in profile.
    """
    b = _bob(frame)
    skin, inner = (246, 206, 214), (214, 140, 166)
    dark, cloth = (188, 116, 144), (226, 156, 178)
    side = facing in (LEFT, RIGHT)
    top = 4 + b

    cell.rect(CX - (3 if side else 5), 20 + b, (6 if side else 10),
              GROUND - 24 - b, cloth)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top + 8, 8, 9, skin)
        cell.ellipse(CX, top + 9, 5, 6, inner)
        cell.ellipse(CX, top + 10, 2.5, 3.5, dark)
        cell.ellipse(CX - 5, top + 12, 2, 3, skin)
    elif facing == UP:
        # the back of an ear: a smooth closed shell with a ridge
        cell.ellipse(CX, top + 8, 8, 9, cooler(skin, 0.12))
        cell.ellipse(CX + 1, top + 7, 5, 6, cooler(skin, 0.22))
        cell.vline(CX + 3, top + 3, top + 13, dark)
    else:
        # in profile it is a blade, and it leads with its edge
        lead = -1 if facing == LEFT else 1
        cell.ellipse(CX + lead, top + 8, 3.5, 9.5, skin)
        cell.ellipse(CX + lead * 2, top + 8, 1.5, 7, inner)
        cell.rect(CX - lead * 3, top + 4, 3, 10, cooler(skin, 0.18))


def draw_brick_carrier(cell: Canvas, facing: int, frame: int) -> None:
    """Carrying one loose brick back to wherever it came from.

    The brick is held in front, so from behind it is hidden entirely and the
    silhouette is a plain back — which is most of the difference.
    """
    b = _bob(frame)
    coat, dark = (214, 140, 168), (170, 98, 128)
    skin = (244, 200, 210)
    loose, edge = (228, 150, 150), (188, 106, 112)
    side = facing in (LEFT, RIGHT)
    top = 8 + b
    bw = 8 if side else 13

    cell.rect(CX - bw // 2, top, bw, GROUND - top - 4, coat)
    cell.rect(CX - bw // 2, top, bw, 3, warmer(coat, 0.22))
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        cell.ellipse(CX, top - 3, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (52, 34, 48))
        cell.rect(CX - 6, top + 8, 12, 8, loose)
        cell.rect(CX - 6, top + 8, 12, 1, warmer(loose, 0.3))
        cell.hline(top + 12, CX - 6, CX + 5, edge)
    elif facing == UP:
        cell.ellipse(CX, top - 3, 5, 5, cooler(skin, 0.20))
        cell.ellipse(CX, top - 4, 4, 3, dark)
        # only the far edge of the brick shows past the shoulders
        cell.rect(CX - 4, top + 9, 8, 2, edge)
    else:
        lead = -1 if facing == LEFT else 1
        cell.ellipse(CX + lead, top - 3, 4, 5, skin)
        # one eye, on the face rather than floating off the side of the cell
        cell.rect(CX + (2 if lead > 0 else -3), top - 4, 2, 2, (52, 34, 48))
        cell.rect(CX + (2 * lead if lead > 0 else -9), top + 8, 7, 8, loose)
        cell.hline(top + 12, CX + (2 * lead if lead > 0 else -9),
                   CX + (2 * lead if lead > 0 else -9) + 6, edge)


PINK = {
    "measurer": draw_measurer,
    "brick_child": draw_brick_child,
    "wall_ear": draw_wall_ear,
    "brick_carrier": draw_brick_carrier,
}


# --- numbers: a clinical place, and its residents are notation ---------------

def draw_counter(cell: Canvas, facing: int, frame: int) -> None:
    """A head that is a flip counter, still going up.

    Front: the digits.  Back: the mechanism that turns them.  Side: the
    display is a thin card, so it nearly disappears.
    """
    b = _bob(frame)
    case, shell = (206, 218, 214), (150, 166, 164)
    dark, lit = (86, 100, 100), (250, 246, 226)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b
    hw = 5 if side else 16

    cell.rect(CX - (3 if side else 5), top + 13, (6 if side else 10),
              GROUND - top - 17, shell)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    hx = CX - hw // 2 + (lead * 2 if side else 0)
    cell.rect(hx, top, hw, 13, case)
    if facing == DOWN:
        cell.rect(hx + 1, top + 2, hw - 2, 9, dark)
        for i, dx in enumerate((2, 6, 10)):
            cell.rect(hx + dx, top + 3 + (frame + i) % 2, 3, 7, lit)
            cell.hline(top + 6, hx + dx, hx + dx + 2, dark)
        cell.hline(top + 12, hx, hx + hw - 1, shell)
    elif facing == UP:
        # the works: a drum, a spindle and the strap that holds it on
        cell.rect(hx + 1, top + 1, hw - 2, 11, cooler(case, 0.22))
        cell.ellipse(CX, top + 6, 5, 4.5, shell)
        cell.ellipse(CX, top + 6, 2, 2, dark)
        cell.rect(hx, top + 5, hw, 2, cooler(shell, 0.3))
    else:
        cell.rect(hx, top + 1, hw, 11, cooler(case, 0.12))
        cell.vline(hx + (hw - 1 if lead > 0 else 0), top, top + 12, lit)
        cell.rect(CX - lead * 3, top + 4, 3, 5, shell)


def draw_zero(cell: Canvas, facing: int, frame: int) -> None:
    """A nought, walking.  Empty in the middle, and the middle is the point."""
    b = _bob(frame)
    ring, inner = (244, 242, 232), (176, 190, 190)
    dark = (96, 110, 112)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 13 + b

    if side:
        # edge-on a ring is a bar: almost nothing, which is most of the change
        cell.rect(CX - 2 + lead, cy - 10, 4, 20, ring)
        cell.rect(CX - 2 + lead, cy - 10, 4, 2, warmer(ring, 0.3))
        cell.vline(CX + (1 if lead > 0 else -3) + lead, cy - 9, cy + 8, inner)
        _small_legs(cell, frame, CX + lead, GROUND - 5, dark, spread=2)
    else:
        cell.ellipse(CX, cy, 9, 11, ring)
        cell.ellipse(CX, cy, 5, 7, (255, 0, 255))
        _small_legs(cell, frame, CX, GROUND - 5, dark, spread=4)
        if facing == DOWN:
            for ex in (CX - 6, CX + 4):
                cell.rect(ex, cy - 3, 2, 3, dark)
            cell.ellipse(CX, cy - 10, 6, 2, warmer(ring, 0.35))
        else:
            # from behind: the seam where it was closed, and no eyes
            cell.vline(CX, cy - 11, cy - 7, inner)
            cell.vline(CX, cy + 7, cy + 11, inner)
            cell.ellipse(CX, cy, 8, 10, inner, filled=False)


def draw_divider(cell: Canvas, facing: int, frame: int) -> None:
    """A division sign: a bar, a dot above, a dot below.  It is very tall."""
    b = _bob(frame)
    bar, dot = (232, 236, 232), (120, 138, 138)
    dark = (78, 92, 94)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 2 + b

    if side:
        # edge-on the bar is a stub and the dots line up behind each other
        cell.rect(CX - 1 + lead, top, 3, GROUND - top - 5, bar)
        cell.rect(CX - 1 + lead, top + 8, 3, 3, dot)
        cell.rect(CX + (2 * lead), top + 9, 4, 2, bar)
        cell.rect(CX - 1 + lead, top + 17, 3, 3, dot)
        _small_legs(cell, frame, CX + lead, GROUND - 5, dark, spread=2)
    else:
        cell.rect(CX - 2, top, 5, GROUND - top - 5, bar)
        cell.rect(CX - 8, top + 9, 17, 3, bar)
        _small_legs(cell, frame, CX, GROUND - 5, dark, spread=4)
        if facing == DOWN:
            cell.rect(CX - 3, top + 3, 3, 3, dot)
            cell.rect(CX + 1, top + 3, 3, 3, dot)
            cell.rect(CX - 2, top + 15, 5, 4, dot)
        else:
            # From behind the dots are gone entirely and the bar is braced —
            # a division sign only reads as one from the side it is written on.
            cell.rect(CX - 2, top, 5, GROUND - top - 5, cooler(bar, 0.20))
            cell.rect(CX - 8, top + 8, 17, 5, cooler(bar, 0.32))
            cell.rect(CX - 6, top + 9, 13, 1, dot)
            cell.rect(CX - 4, top + 14, 9, 4, cooler(bar, 0.12))
            cell.vline(CX - 4, top + 1, top + 7, dot)
            cell.vline(CX + 4, top + 1, top + 7, dot)


def draw_remainder(cell: Canvas, facing: int, frame: int) -> None:
    """What was left over.  A piece of it is simply missing, and it shows."""
    b = _bob(frame)
    body, cut = (214, 224, 220), (158, 174, 174)
    dark = (88, 102, 104)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b
    bw = 7 if side else 15

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, body)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        # the bite, taken out of the front, with a raw edge
        for i in range(6):
            cell.rect(CX + 1 + i // 2, top + 4 + i, 7 - i, 1, (255, 0, 255))
        cell.rect(CX - 6, top + 3, 3, 3, dark)
        cell.rect(CX - 6, top + 12, 8, 1, cut)
    elif facing == UP:
        # from behind it is whole, and that is the joke
        cell.rect(CX - bw // 2 + 1, top + 1, bw - 2, GROUND - top - 7,
                  cooler(body, 0.14))
        cell.rect(CX - 5, top + 2, 10, 2, cut)
    else:
        for i in range(5):
            x = CX + (1 + i // 2) * lead if lead > 0 else CX - 4 - i // 2
            cell.rect(x, top + 5 + i, 4 - i // 2, 1, (255, 0, 255))
        cell.vline(CX + (bw // 2 + lead - 1 if lead > 0 else -bw // 2 + lead),
                   top, GROUND - 6, cut)


NUMBERS = {
    "counter": draw_counter,
    "zero": draw_zero,
    "divider": draw_divider,
    "remainder": draw_remainder,
}


# --- blocks: a nursery built out of stacking toys ----------------------------

def draw_stacker(cell: Canvas, facing: int, frame: int) -> None:
    """Nearly finished.  The tower behind them is two blocks tall."""
    b = _bob(frame)
    skin, coat = (246, 216, 194), (118, 174, 224)
    dark, block, edge = (72, 84, 130), (230, 128, 124), (176, 88, 92)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    bw = 8 if side else 13

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5.5, 5, skin)
        for ex in (CX - 4, CX + 2):
            cell.rect(ex, top - 5, 2, 2, (56, 40, 52))
        cell.rect(CX - 5, top + 4, 11, 9, block)
        cell.rect(CX - 5, top + 4, 11, 2, warmer(block, 0.3))
        cell.rect(CX - 1, top + 7, 3, 3, warmer(block, 0.5))
    elif facing == UP:
        # a hood, and the block only visible as a sliver past the shoulder
        cell.ellipse(CX, top - 4, 5.5, 5, cooler(skin, 0.25))
        cell.ellipse(CX, top - 5, 5, 3.5, dark)
        cell.rect(CX - 6, top + 1, 12, 3, cooler(coat, 0.25))
        cell.rect(CX + 4 * lead, top + 5, 3, 6, edge)
    else:
        cell.ellipse(CX + lead, top - 4, 4.5, 5, skin)
        cell.rect(CX + (2 if lead > 0 else -3), top - 5, 2, 2, (56, 40, 52))
        bx = CX + 2 if lead > 0 else CX - 9
        cell.rect(bx, top + 3, 7, 9, block)
        cell.rect(bx, top + 3, 7, 2, warmer(block, 0.3))


def draw_block_cat(cell: Canvas, facing: int, frame: int) -> None:
    """A cat assembled from cubes.  It looks at you with its whole body."""
    b = _bob(frame)
    fur, dark = (238, 206, 118), (176, 138, 66)
    ink = (60, 48, 40)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 8 + b

    if side:
        cell.rect(CX - 5 + lead, top + 3, 11, 12, fur)
        cell.rect(CX - 5 + lead, top + 3, 11, 2, warmer(fur, 0.25))
        # head forward, tail up behind
        cell.rect(CX + (2 if lead > 0 else -6) + lead, top - 2, 5, 7, fur)
        cell.rect(CX + (3 if lead > 0 else -5) + lead, top - 5, 1, 3, fur)
        cell.rect(CX + (4 * -lead), top - 4, 2, 8, dark)
        cell.rect(CX + (4 if lead > 0 else -5) + lead, top, 2, 2, ink)
        _small_legs(cell, frame, CX + lead, GROUND - 5, dark, spread=3)
    else:
        cell.rect(CX - 7, top + 2, 15, 13, fur)
        cell.rect(CX - 7, top + 2, 15, 2, warmer(fur, 0.25))
        _small_legs(cell, frame, CX, GROUND - 5, dark, spread=5)
        for ear in (CX - 6, CX + 3):
            cell.rect(ear, top - 3, 4, 4, fur if facing == DOWN else dark)
        if facing == DOWN:
            for ex in (CX - 5, CX + 2):
                cell.rect(ex, top + 5, 3, 3, ink)
            cell.rect(CX - 1, top + 10, 3, 1, ink)
        else:
            # from behind: a tail straight up the middle, and no face at all
            cell.rect(CX - 1, top - 6, 3, 10, dark)
            cell.rect(CX - 7, top + 8, 15, 1, dark)


def draw_toppler(cell: Canvas, facing: int, frame: int) -> None:
    """A stack of four blocks that has never once fallen over."""
    b = _bob(frame)
    hues = ((228, 120, 118), (238, 200, 96), (120, 176, 226), (150, 206, 150))
    dark = (78, 88, 118)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 3 + b
    w = 7 if side else 14

    for i, hue in enumerate(hues):
        # each block sits a pixel off the one below it, leaning the way it goes
        drift = (i - 1) * (lead if side else 1)
        x = CX - w // 2 + drift
        cell.rect(x, top + i * 5, w, 5, hue)
        cell.rect(x, top + i * 5, w, 1, warmer(hue, 0.35))
        cell.hline(top + i * 5 + 4, x, x + w - 1, cooler(hue, 0.3))
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        for ex in (CX - 4, CX + 2):
            cell.rect(ex, top + 6, 2, 3, (48, 36, 44))
        cell.rect(CX - 3, top + 16, 7, 2, (48, 36, 44))
    elif facing == UP:
        for i in range(4):
            cell.rect(CX - w // 2 + 1, top + i * 5 + 1, w - 2, 3,
                      cooler(hues[i], 0.24))
    else:
        cell.vline(CX + (w // 2 - 1) * lead, top, top + 19, (255, 250, 236))


def draw_corner_piece(cell: Canvas, facing: int, frame: int) -> None:
    """Only fits in one place, and is not in it.  Shaped like the gap."""
    b = _bob(frame)
    body, edge = (238, 200, 96), (186, 148, 60)
    dark = (80, 92, 120)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b

    if side:
        cell.rect(CX - 4 + lead, top, 8, 18, body)
        cell.rect(CX - 4 + lead, top, 8, 2, warmer(body, 0.3))
        # the notch, cut into whichever side is leading
        nx = CX + (1 if lead > 0 else -4) + lead
        cell.rect(nx, top + 5, 4, 7, (255, 0, 255))
        cell.vline(CX + (-4 if lead > 0 else 3) + lead, top, top + 17, edge)
        cell.rect(CX - 2 + lead, top + 3, 2, 2, (52, 42, 40))
        _small_legs(cell, frame, CX + lead, GROUND - 5, dark, spread=2)
    else:
        cell.rect(CX - 8, top, 17, 18, body)
        cell.rect(CX - 8, top, 17, 2, warmer(body, 0.3))
        _small_legs(cell, frame, CX, GROUND - 5, dark, spread=5)
        if facing == DOWN:
            # an L-shaped bite out of the bottom corner
            cell.rect(CX + 1, top + 8, 8, 10, (255, 0, 255))
            cell.rect(CX - 6, top + 4, 3, 3, (52, 42, 40))
            cell.rect(CX - 1, top + 4, 3, 3, (52, 42, 40))
        else:
            cell.rect(CX - 8, top + 8, 8, 10, (255, 0, 255))
            cell.rect(CX - 1, top + 2, 9, 3, edge)
            cell.rect(CX + 2, top + 9, 5, 8, cooler(body, 0.2))


BLOCKS = {
    "stacker": draw_stacker,
    "block_cat": draw_block_cat,
    "toppler": draw_toppler,
    "corner_piece": draw_corner_piece,
}


# --- toys: everything here is smaller than it ought to be --------------------

def draw_wind_up(cell: Canvas, facing: int, frame: int) -> None:
    """The key turns whether or not they are walking.  It is on their back."""
    b = _bob(frame)
    tin, dark = (232, 148, 140), (170, 92, 96)
    brass, face = (238, 200, 118), (250, 224, 206)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 7 + b
    bw = 8 if side else 14

    cell.round_rect(CX - bw // 2 + (lead if side else 0), top, bw,
                    GROUND - top - 5, 4, tin)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == UP:
        # the key, full on, turning
        spin = (0, 1, 2)[frame]
        cell.ellipse(CX, top + 7, 5.5, 5.5, brass)
        cell.ellipse(CX, top + 7, 2, 2, dark)
        for arm in ((0, -5), (5, 0), (0, 5), (-5, 0))[spin:] + \
                   ((0, -5), (5, 0))[:spin]:
            cell.rect(CX + arm[0] - 1, top + 7 + arm[1] - 1, 3, 3, brass)
        cell.round_rect(CX - 5, top - 2, 11, 5, 2, cooler(tin, 0.22))
    elif facing == DOWN:
        cell.round_rect(CX - 5, top - 2, 11, 9, 3, face)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top + 1, 2, 3, (60, 44, 48))
        cell.rect(CX - 2, top + 5, 5, 1, dark)
        cell.rect(CX - 4, top + 11, 9, 2, brass)
    else:
        cell.round_rect(CX - 4 + lead, top - 2, 9, 9, 3, face)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top + 1, 2, 3,
                  (60, 44, 48))
        # the key edge-on behind them: a stub and a disc
        kx = CX - 5 * lead
        cell.rect(kx - 1, top + 6, 3, 3, brass)
        cell.ellipse(kx - lead * 2, top + 7, 1.5, 4, brass)


def draw_cone(cell: Canvas, facing: int, frame: int) -> None:
    """A road cone that moves aside for you.  There is nothing behind it."""
    b = _bob(frame)
    orange, band = (236, 130, 72), (250, 244, 232)
    dark, base = (176, 88, 52), (198, 100, 60)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    apex = 6 + b

    # A cone has no back, so the difference has to be in the shape: it leans
    # forward in profile and its seam faces away from you from behind.
    tilt = lead if side else 0
    for row in range(GROUND - 4 - apex):
        span = 1 + row * 6 // (GROUND - 4 - apex)
        drift = tilt * (GROUND - 4 - apex - row) // 6
        hue = band if 5 <= row <= 8 else orange
        cell.hline(apex + row, CX - span + drift, CX + span + drift, hue)
    cell.rect(CX - 8 + tilt, GROUND - 5, 17 - abs(tilt), 3, base)
    cell.rect(CX - 8 + tilt, GROUND - 5, 17 - abs(tilt), 1, warmer(base, 0.3))
    _small_legs(cell, frame, CX + tilt, GROUND - 2, dark, spread=4)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, apex + 11, 2, 3, (52, 34, 30))
    elif facing == UP:
        # A cone has no back, so it has to be given one: the seam it was rolled
        # from runs the full height, the reflective band is dulled, and the
        # base ring shows its underside.
        cell.vline(CX, apex + 1, GROUND - 6, dark)
        cell.vline(CX - 1, apex + 3, GROUND - 6, cooler(orange, 0.28))
        for row in range(5, 9):
            span = 1 + row * 6 // (GROUND - 4 - apex)
            cell.hline(apex + row, CX - span, CX + span, cooler(band, 0.34))
        cell.rect(CX - 8, GROUND - 4, 17, 2, cooler(base, 0.35))
        cell.rect(CX - 5, GROUND - 6, 11, 2, dark)
    else:
        cell.vline(CX + 5 * lead + tilt, apex + 9, GROUND - 6, dark)


def draw_tin_soldier(cell: Canvas, facing: int, frame: int) -> None:
    """Salutes something behind you.  There is nothing behind you."""
    b = _bob(frame)
    coat, trim = (226, 92, 96), (240, 214, 138)
    skin, dark = (248, 214, 196), (68, 78, 128)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    cell.rect(CX - bw // 2 + (lead if side else 0), top + 4, bw, 2, trim)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    # a shako, far too tall
    hx = CX - (3 if side else 5) + (lead if side else 0)
    cell.rect(hx, top - 15, (6 if side else 10), 11, dark)
    cell.rect(hx, top - 6, (6 if side else 10), 2, trim)
    if facing == DOWN:
        cell.ellipse(CX, top - 3, 5, 4, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (54, 38, 44))
        cell.rect(CX + 4, top + 2, 3, 7, skin)      # the saluting arm
        cell.rect(CX + 3, top + 1, 5, 2, coat)
    elif facing == UP:
        # From behind: the plume that only exists on the back of the shako, a
        # cross-belt, and no face or arm at all.
        cell.ellipse(CX, top - 3, 5, 4, cooler(skin, 0.3))
        cell.rect(CX - 5, top - 18, 11, 4, trim)
        cell.rect(CX - 2, top - 25, 5, 8, coat)
        cell.rect(CX - 2, top - 27, 5, 3, warmer(coat, 0.4))
        for i in range(7):
            cell.rect(CX - 5 + i, top + i, 3, 2, trim)
    else:
        cell.ellipse(CX + lead, top - 3, 4, 4, skin)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 4, 2, 2,
                  (54, 38, 44))
        cell.rect(CX + 2 * lead, top + 1, 3, 8, skin)
        cell.rect(CX + (2 if lead > 0 else -4) * lead, top - 20, 2, 5, coat)


def draw_spinning_top(cell: Canvas, facing: int, frame: int) -> None:
    """Has been turning for a while.  Does not seem dizzy."""
    b = _bob(frame)
    hull, stripe = (120, 190, 176), (238, 118, 130)
    knob, dark = (238, 200, 118), (74, 96, 96)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 14 + b
    lean = lead * 2 if side else 0

    # a fat lens on a point, leaning as it goes
    for row in range(-9, 10):
        span = int((1 - abs(row) / 10.5) * 10)
        drift = lean * (10 - abs(row)) // 10
        hue = stripe if (row + frame * 3) % 6 < 2 else hull
        cell.hline(cy + row, CX - span + drift, CX + span + drift, hue)
    cell.rect(CX - 1 + lean, cy + 9, 3, GROUND - cy - 11, dark)
    cell.rect(CX - 2 + lean, GROUND - 3, 5, 2, cooler(dark, 0.2))

    if facing == DOWN:
        cell.ellipse(CX, cy - 11, 3.5, 2.5, knob)
        for ex in (CX - 5, CX + 3):
            cell.rect(ex, cy - 2, 2, 3, (44, 52, 56))
        cell.rect(CX - 2, cy + 3, 5, 1, (44, 52, 56))
    elif facing == UP:
        cell.ellipse(CX, cy - 11, 3.5, 2.5, cooler(knob, 0.3))
        cell.ellipse(CX, cy, 6, 6, cooler(hull, 0.25))
        cell.ellipse(CX, cy, 2, 2, dark)
    else:
        cell.ellipse(CX + lean, cy - 11, 2.5, 2.5, knob)
        cell.rect(CX + 7 * lead + lean, cy - 3, 2, 5, cooler(hull, 0.35))


TOYS = {
    "wind_up": draw_wind_up,
    "cone": draw_cone,
    "tin_soldier": draw_tin_soldier,
    "spinning_top": draw_spinning_top,
}


# --- neon: drawn in light, and light does not have a back --------------------

def draw_floating_eye(cell: Canvas, facing: int, frame: int) -> None:
    """It blinks after you do.  From behind it is only the nerve."""
    b = _bob(frame)
    white, iris = (226, 250, 248), (64, 226, 218)
    pupil, nerve = (18, 26, 40), (200, 96, 200)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 14 + b

    if facing == UP:
        # the back of an eye: no white at all, just the stalk and the vessels
        cell.ellipse(CX, cy, 8, 7, cooler(white, 0.45))
        cell.ellipse(CX, cy, 6, 5, nerve)
        cell.rect(CX - 2, cy - 12, 5, 8, cooler(nerve, 0.2))
        for i, sx in enumerate((-6, -2, 2, 6)):
            cell.vline(CX + sx, cy - 4 + i % 2, cy + 5, cooler(nerve, 0.35))
    elif facing == DOWN:
        cell.ellipse(CX, cy, 10, 8, white)
        cell.ellipse(CX, cy, 5, 5, iris)
        cell.ellipse(CX, cy, 2.5, 2.5, pupil)
        if frame == 1:
            cell.rect(CX - 10, cy - 2, 21, 5, white)   # mid-blink
        cell.ellipse(CX - 3, cy - 3, 2, 1.5, (255, 255, 255))
    else:
        # in profile an eye is a dome on a stalk, and it leads with the cornea
        cell.ellipse(CX, cy, 5, 7.5, white)
        cell.ellipse(CX + 4 * lead, cy, 3, 5, cooler(white, 0.12))
        cell.ellipse(CX + 5 * lead, cy, 1.5, 3, iris)
        cell.rect(CX - 7 * lead, cy - 2, 4, 4, nerve)


def draw_scrawler(cell: Canvas, facing: int, frame: int) -> None:
    """Drawn in one continuous line.  You can see where it started."""
    b = _bob(frame)
    line, glow = (96, 240, 226), (30, 110, 120)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 5 + b

    def stroke(points, colour):
        for i in range(len(points) - 1):
            cell.line(points[i][0], points[i][1],
                      points[i + 1][0], points[i + 1][1], colour)

    if facing == DOWN:
        pts = [(CX - 6, GROUND - 4), (CX - 4, top + 12), (CX - 6, top + 4),
               (CX, top), (CX + 6, top + 4), (CX + 4, top + 12),
               (CX + 6, GROUND - 4)]
        stroke(pts, glow)
        stroke([(x, y - 1) for x, y in pts], line)
        cell.rect(CX - 4, top + 5, 2, 3, line)
        cell.rect(CX + 2, top + 5, 2, 3, line)
        cell.dot(CX - 6, GROUND - 4, (255, 255, 255))
    elif facing == UP:
        # the same line, but closed: no eyes, and the loose end tucked away
        pts = [(CX, GROUND - 4), (CX - 5, top + 10), (CX, top),
               (CX + 5, top + 10), (CX, GROUND - 4)]
        stroke(pts, glow)
        stroke([(x, y - 1) for x, y in pts], line)
        cell.vline(CX, top + 3, GROUND - 6, cooler(line, 0.4))
    else:
        pts = [(CX - 3 * lead, GROUND - 4), (CX + 2 * lead, top + 14),
               (CX - 2 * lead, top + 6), (CX + 4 * lead, top),
               (CX + 5 * lead, top + 9), (CX + 2 * lead, GROUND - 4)]
        stroke(pts, glow)
        stroke([(x, y - 1) for x, y in pts], line)
        cell.rect(CX + 2 * lead, top + 5, 2, 3, line)


def draw_flicker(cell: Canvas, facing: int, frame: int) -> None:
    """Only there some of the time.  Which parts, depends where you stand."""
    b = _bob(frame)
    body, hot = (240, 96, 200), (250, 214, 246)
    dim, dark = (120, 44, 110), (54, 34, 78)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b
    bw = 8 if side else 14

    # bands of the figure simply are not drawn, and the gaps move per frame
    for row in range(GROUND - 5 - top):
        if (row + frame * 2) % 7 == 3:
            continue
        drift = lead if side and row < 8 else 0
        cell.hline(top + row, CX - bw // 2 + drift, CX + bw // 2 - 1 + drift,
                   body if row % 4 else hot)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        for ex in (CX - 4, CX + 2):
            cell.rect(ex, top + 5, 3, 4, dark)
        cell.rect(CX - 3, top + 12, 7, 1, dim)
    elif facing == UP:
        cell.rect(CX - bw // 2, top, bw, 5, dim)
        cell.vline(CX, top + 5, GROUND - 7, dim)
    else:
        # In profile the gaps run the other way — vertical, and leading — so
        # the two sides never resolve into the same figure.
        for col in range(bw):
            if (col + frame) % 4 == 1:
                cell.vline(CX - bw // 2 + col + lead, top, GROUND - 7,
                           (255, 0, 255))
        cell.rect(CX + (1 if lead > 0 else -3) + lead, top + 5, 3, 4, dark)
        cell.vline(CX + (bw // 2 - 1) * lead + lead, top, GROUND - 7, hot)


def draw_sign_holder(cell: Canvas, facing: int, frame: int) -> None:
    """Holds up a ring and looks through it at you."""
    b = _bob(frame)
    coat, dark = (72, 60, 132), (40, 34, 78)
    ring, hot = (250, 120, 210), (255, 226, 250)
    skin = (226, 210, 244)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    bw = 7 if side else 13

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        cell.ellipse(CX, top - 4, 8, 8, ring, filled=False)
        cell.ellipse(CX, top - 4, 7, 7, hot, filled=False)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, dark)
    elif facing == UP:
        # the ring is held out in front, so from behind only its top edge shows
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.3))
        cell.ellipse(CX, top - 4, 4, 3, dark)
        cell.rect(CX - 6, top - 12, 13, 2, ring)
        cell.rect(CX - 5, top + 1, 11, 3, cooler(coat, 0.3))
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.ellipse(CX + 5 * lead, top - 4, 2.5, 8, ring, filled=False)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 5, 2, 2, dark)


NEON = {
    "floating_eye": draw_floating_eye,
    "scrawler": draw_scrawler,
    "flicker": draw_flicker,
    "sign_holder": draw_sign_holder,
}


# --- checker: two colours, and nothing is allowed to be a third --------------

def draw_pawn(cell: Canvas, facing: int, frame: int) -> None:
    """It can only move forwards.  It is not in a hurry."""
    b = _bob(frame)
    pale, shade = (238, 238, 242), (170, 172, 180)
    dark = (52, 52, 60)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 5 + b

    # turned from one piece: a ball, a collar, a flaring skirt
    lean = lead * 2 if side else 0
    cell.ellipse(CX + lean, top + 4, 5.5, 5.5, pale)
    cell.rect(CX - 4 + lean, top + 9, 9, 2, shade)
    for row in range(GROUND - 6 - top - 10):
        span = 3 + row * 6 // max(1, GROUND - 16 - top)
        cell.hline(top + 11 + row, CX - span + lean, CX + span + lean, pale)
    cell.rect(CX - 8 + lean, GROUND - 5, 17, 3, shade)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top + 3, 2, 2, dark)
    elif facing == UP:
        # from behind, the lathe rings and the felt on its base
        cell.ellipse(CX, top + 4, 5.5, 5.5, shade)
        cell.ellipse(CX, top + 3, 3.5, 3, pale)
        for row in (14, 18, 22):
            cell.hline(top + row, CX - 5, CX + 5, shade)
        cell.rect(CX - 6, GROUND - 3, 13, 2, dark)
    else:
        cell.ellipse(CX + lean + lead, top + 3, 4, 5, pale)
        cell.vline(CX + lean - 6 * lead, top + 12, GROUND - 6, shade)


def draw_housekeeper(cell: Canvas, facing: int, frame: int) -> None:
    """Wears a house.  There is nobody in."""
    b = _bob(frame)
    wall, roof = (232, 228, 220), (198, 84, 78)
    dark, glass = (96, 92, 92), (48, 44, 56)
    lit = (250, 226, 150)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 3 + b
    hw = 8 if side else 15
    # in profile the whole house is carried forward, not just its details
    hx = CX - hw // 2 + (lead * 3 if side else 0)

    cell.rect(CX - (4 if side else 6), top + 16, (8 if side else 12),
              GROUND - top - 20, cooler(wall, 0.25))
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    cell.rect(hx, top + 5, hw, 11, wall)
    for i in range(6):
        cell.hline(top + 4 - i, hx + i, hx + hw - 1 - i, roof)
    cell.rect(hx, top + 5, hw, 1, cooler(roof, 0.3))

    if facing == DOWN:
        for wx in (hx + 2, hx + hw - 5):
            cell.rect(wx, top + 8, 3, 4, glass)
            cell.hline(top + 10, wx, wx + 2, wall)
        cell.rect(CX - 1, top + 12, 3, 4, dark)
    elif facing == UP:
        # the back of a house: a chimney, no door, one lit window
        cell.rect(hx + 2, top - 5, 3, 6, cooler(roof, 0.4))
        cell.rect(CX + 1, top + 8, 4, 4, lit)
        cell.rect(hx + 1, top + 6, hw - 2, 9, cooler(wall, 0.18))
        cell.rect(CX + 1, top + 8, 4, 4, lit)
    else:
        # the gable end: the roof comes to a point instead of a ridge, and
        # there is one small window high up under it
        for i in range(7):
            cell.hline(top + 4 - i, hx + 3 - i // 2, hx + hw - 4 + i // 2, roof)
        cell.rect(hx, top + 5, hw, 11, wall)
        cell.rect(hx + (2 if lead > 0 else hw - 5), top + 9, 3, 3, glass)
        cell.rect(hx + (hw - 1 if lead > 0 else 0), top + 5, 1, 11,
                  warmer(wall, 0.3))
        cell.rect(hx + (hw - 4 if lead > 0 else 1), top - 6, 3, 6,
                  cooler(roof, 0.4))
        cell.rect(CX - 4 * lead, top + 14, 3, 6, cooler(wall, 0.3))


def draw_black_square(cell: Canvas, facing: int, frame: int) -> None:
    """Only goes diagonally.  Demonstrates.  It is not diagonal."""
    b = _bob(frame)
    ink, sheen = (40, 40, 48), (96, 96, 110)
    pale = (236, 236, 242)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 7 + b
    w = 8 if side else 17

    cell.rect(CX - w // 2 + (lead * 2 if side else 0), top, w, 17, ink)
    _small_legs(cell, frame, CX, GROUND - 5, sheen, spread=3 if side else 6)

    if facing == DOWN:
        for ex in (CX - 5, CX + 2):
            cell.rect(ex, top + 5, 3, 3, pale)
        # a diagonal drawn across the face, going the wrong way
        for i in range(10):
            cell.dot(CX - 5 + i, top + 14 - i, sheen)
    elif facing == UP:
        cell.rect(CX - w // 2 + 1, top + 1, w - 2, 15, sheen)
        cell.rect(CX - w // 2 + 3, top + 3, w - 6, 11, ink)
        cell.rect(CX - 2, top - 3, 5, 4, ink)
    else:
        cell.rect(CX + (w // 2 - 2) * lead + lead * 2, top, 2, 17, pale)
        cell.rect(CX - lead + lead * 2, top + 5, 2, 3, pale)


def draw_white_square(cell: Canvas, facing: int, frame: int) -> None:
    """Stands on white and will not step off it."""
    b = _bob(frame)
    pale, edge = (244, 244, 248), (186, 186, 196)
    ink = (56, 54, 64)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 7 + b
    w = 8 if side else 17

    cell.rect(CX - w // 2 + (lead * 2 if side else 0), top, w, 17, pale)
    cell.rect(CX - w // 2 + (lead * 2 if side else 0), top, w, 2,
              warmer(pale, 0.3))
    _small_legs(cell, frame, CX, GROUND - 5, edge, spread=3 if side else 6)
    # it carries its own square of floor and never leaves it
    cell.rect(CX - 8, GROUND - 3, 17, 3, pale)
    cell.rect(CX - 8, GROUND - 3, 8, 3, ink)

    if facing == DOWN:
        for ex in (CX - 5, CX + 2):
            cell.rect(ex, top + 5, 3, 3, ink)
        cell.rect(CX - 3, top + 12, 7, 1, edge)
    elif facing == UP:
        cell.rect(CX - w // 2 + 2, top + 2, w - 4, 13, edge)
        cell.rect(CX - 3, top - 3, 7, 4, pale)
        cell.rect(CX - 1, top + 4, 3, 9, pale)
    else:
        cell.rect(CX + (w // 2 - 2) * lead + lead * 2, top, 2, 17, ink)
        cell.rect(CX - lead + lead * 2, top + 5, 2, 3, ink)


CHECKER = {
    "pawn": draw_pawn,
    "housekeeper": draw_housekeeper,
    "black_square": draw_black_square,
    "white_square": draw_white_square,
}


# --- sand: bleached, and half of everything is buried ------------------------

def draw_waiting_one(cell: Canvas, facing: int, frame: int) -> None:
    """Has been waiting long enough that the hat is the only news."""
    b = _bob(frame)
    cloth, shade = (222, 210, 188), (176, 164, 142)
    hat, dark = (120, 128, 148), (92, 84, 70)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 12 + b

    # a robe that widens to the ground, no legs at all
    for row in range(GROUND - 2 - top):
        span = (3 if side else 4) + row * (3 if side else 6) // (GROUND - 2 - top)
        cell.hline(top + row, CX - span + (lead if side else 0),
                   CX + span + (lead if side else 0), cloth)
    cell.hline(GROUND - 2, CX - (6 if side else 10), CX + (6 if side else 10),
               shade)

    hw = 9 if side else 21
    cell.ellipse(CX + (lead if side else 0), top - 3, hw / 2, 2.5, hat)
    cell.ellipse(CX + (lead if side else 0), top - 6, 4, 3.5, cooler(hat, 0.2))

    if facing == DOWN:
        cell.rect(CX - 5, top + 1, 11, 5, dark)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top + 2, 2, 2, (232, 226, 210))
    elif facing == UP:
        # from behind, the brim hides everything and the robe has a seam
        cell.ellipse(CX, top - 3, hw / 2, 3, cooler(hat, 0.3))
        cell.vline(CX, top + 2, GROUND - 3, shade)
        cell.hline(top + 8, CX - 7, CX + 7, shade)
    else:
        cell.rect(CX + (1 if lead > 0 else -4) + lead, top + 1, 4, 4, dark)
        cell.vline(CX - 4 * lead + lead, top + 2, GROUND - 3, shade)


def draw_sand_walker(cell: Canvas, facing: int, frame: int) -> None:
    """Very far away.  Was very far away when you started walking."""
    b = _bob(frame)
    pale, faint = (246, 240, 228), (214, 204, 186)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 1 + b

    # far too tall and far too thin, and it thins further as it rises
    for row in range(GROUND - 3 - top):
        span = 1 + row * (2 if side else 4) // (GROUND - 3 - top)
        drift = lead * (GROUND - 3 - top - row) // 9 if side else 0
        cell.hline(top + row, CX - span + drift, CX + span + drift,
                   pale if row % 3 else faint)

    if facing == DOWN:
        cell.rect(CX - 2, top + 5, 2, 3, faint)
        cell.rect(CX + 1, top + 5, 2, 3, faint)
    elif facing == UP:
        # From behind it is barely there at all: the column thins to a thread
        # and most of it is simply erased.  A thing this far away should not
        # survive being turned around.
        for row in range(GROUND - 3 - top):
            if row % 3 != 2:
                span = 1 + row * 4 // (GROUND - 3 - top)
                cell.hline(top + row, CX - span, CX + span, (255, 0, 255))
        cell.vline(CX, top, GROUND - 4, faint)
    else:
        cell.vline(CX + lead * 2, top + 3, GROUND - 6, faint)


def draw_surveyor(cell: Canvas, facing: int, frame: int) -> None:
    """Measuring something a long way off.  There is nothing a long way off."""
    b = _bob(frame)
    coat, dark = (214, 200, 174), (150, 134, 108)
    skin, rod = (232, 210, 182), (186, 168, 138)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (72, 62, 50))
        # the rod, held across the body and foreshortened to a stub
        cell.rect(CX - 7, top + 5, 15, 2, rod)
        cell.rect(CX - 8, top + 3, 2, 6, dark)
    elif facing == UP:
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.25))
        cell.ellipse(CX, top - 5, 4.5, 3, dark)
        # the rod carried upright over the shoulder
        cell.rect(CX + 3, top - 14, 2, 20, rod)
        cell.rect(CX + 2, top - 15, 4, 2, dark)
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 5, 2, 2,
                  (72, 62, 50))
        # sighting along it: the rod runs out of the cell entirely
        rx = CX + 2 * lead if lead > 0 else CX - 12
        cell.rect(rx, top + 2, 12, 2, rod)
        cell.rect(CX + 9 * lead, top, 2, 6, dark)


def draw_half_buried(cell: Canvas, facing: int, frame: int) -> None:
    """Only the hat is above the sand.  It turns to follow you."""
    b = _bob(frame) // 2
    hat, band = (222, 208, 176), (168, 152, 122)
    sand, dark = (232, 220, 198), (196, 182, 154)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 20 + b

    # the sand it is in, mounded up
    for row in range(6):
        span = 11 - row
        cell.hline(GROUND - 2 - row, CX - span, CX + span,
                   sand if row % 2 else dark)

    hw = 7 if side else 11
    cell.ellipse(CX + (lead * 2 if side else 0), cy, hw, 3, hat)
    cell.ellipse(CX + (lead * 2 if side else 0), cy - 4, hw / 2, 4, hat)
    cell.ellipse(CX + (lead * 2 if side else 0), cy - 2, hw / 2, 1.5, band)

    if facing == DOWN:
        # two points of shadow under the brim, watching
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, cy + 1, 2, 2, (86, 76, 62))
    elif facing == UP:
        cell.ellipse(CX, cy, hw, 3, cooler(hat, 0.22))
        cell.ellipse(CX, cy - 4, hw / 2, 4, cooler(hat, 0.3))
        cell.rect(CX - 2, cy + 2, 5, 2, band)
    else:
        cell.rect(CX + (hw - 2) * lead + lead * 2, cy - 1, 2, 2, band)
        cell.rect(CX + lead * 2 + (1 if lead > 0 else -2), cy + 1, 2, 2,
                  (86, 76, 62))


SAND = {
    "waiting_one": draw_waiting_one,
    "sand_walker": draw_sand_walker,
    "surveyor": draw_surveyor,
    "half_buried": draw_half_buried,
}


# --- faces: a grove with municipal fittings that do not belong ---------------

def draw_gardener(cell: Canvas, facing: int, frame: int) -> None:
    """Waters something that is already wet."""
    b = _bob(frame)
    coat, dark = (126, 166, 118), (74, 108, 82)
    skin, can = (232, 200, 170), (184, 146, 112)
    water = (168, 208, 214)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        cell.ellipse(CX, top - 7, 6.5, 2.5, dark)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (62, 48, 40))
        cell.rect(CX + 2, top + 5, 7, 6, can)
        cell.rect(CX + 8, top + 3, 2, 3, can)
        for i in range(3):
            cell.dot(CX + 9, top + 8 + i * 2 + frame, water)
    elif facing == UP:
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.28))
        cell.ellipse(CX, top - 7, 6.5, 2.5, cooler(dark, 0.2))
        # the can is on the far side; only its handle clears the shoulder
        cell.rect(CX + 5, top + 3, 2, 4, can)
        cell.rect(CX - 5, top + 1, 11, 3, cooler(coat, 0.25))
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.ellipse(CX + lead, top - 7, 5.5, 2.5, dark)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 4, 2, 2,
                  (62, 48, 40))
        cx = CX + 2 * lead if lead > 0 else CX - 9
        cell.rect(cx, top + 5, 7, 6, can)
        cell.rect(CX + 8 * lead, top + 7, 2, 2, can)


def draw_seedling(cell: Canvas, facing: int, frame: int) -> None:
    """Follows you for three steps and then forgets."""
    b = _bob(frame)
    leaf, stem = (150, 206, 132), (108, 152, 96)
    pot, soil = (198, 132, 96), (92, 74, 60)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b

    pw = 7 if side else 11
    cell.rect(CX - pw // 2 + (lead if side else 0), GROUND - 12, pw, 9, pot)
    cell.rect(CX - pw // 2 - 1 + (lead if side else 0), GROUND - 13, pw + 2, 3,
              warmer(pot, 0.25))
    cell.rect(CX - pw // 2 + 1 + (lead if side else 0), GROUND - 11, pw - 2, 2,
              soil)
    _small_legs(cell, frame, CX, GROUND - 3, soil, spread=3 if side else 4)

    cell.vline(CX + (lead if side else 0), top + 3, GROUND - 12, stem)
    if facing == DOWN:
        cell.ellipse(CX - 4, top + 4, 4, 2.5, leaf)
        cell.ellipse(CX + 4, top + 6, 4, 2.5, leaf)
        cell.ellipse(CX, top + 1, 3, 3, leaf)
        for ex in (CX - 2, CX + 1):
            cell.dot(ex, top + 1, soil)
    elif facing == UP:
        # from behind, the leaves fold together and the pot shows its base ring
        cell.ellipse(CX, top + 3, 3, 5, cooler(leaf, 0.25))
        cell.vline(CX, top - 1, top + 8, stem)
        cell.rect(CX - 4, GROUND - 5, 9, 2, cooler(pot, 0.35))
    else:
        cell.ellipse(CX + 4 * lead + lead, top + 4, 5, 2, leaf)
        cell.ellipse(CX - 2 * lead + lead, top + 7, 3, 1.5, cooler(leaf, 0.2))
        cell.dot(CX + lead + (1 if lead > 0 else -1), top + 2, soil)


def draw_commuter(cell: Canvas, facing: int, frame: int) -> None:
    """Waiting at a stop.  Nothing has come past for a long time."""
    b = _bob(frame)
    coat, dark = (86, 106, 88), (54, 64, 54)
    skin, case = (236, 214, 190), (108, 84, 66)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    bw = 7 if side else 13

    # a long coat that reaches the ground
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 2, coat)
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw, 3,
              warmer(coat, 0.18))

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (48, 40, 38))
        cell.vline(CX, top + 4, GROUND - 4, dark)       # the coat's opening
        cell.rect(CX + 5, top + 8, 5, 6, case)
    elif facing == UP:
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.3))
        cell.ellipse(CX, top - 5, 4.5, 3, dark)
        # a vent up the back of the coat, and the case hidden entirely
        cell.vline(CX, GROUND - 12, GROUND - 3, dark)
        cell.rect(CX - 6, top + 2, 13, 2, cooler(coat, 0.3))
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 5, 2, 2,
                  (48, 40, 38))
        cx = CX + 3 * lead if lead > 0 else CX - 8
        cell.rect(cx, top + 9, 5, 6, case)
        cell.vline(CX - bw // 2 * lead + lead, top, GROUND - 4, dark)


def draw_leaf_head(cell: Canvas, facing: int, frame: int) -> None:
    """Something is growing out of the top of their head.  They are pleased."""
    b = _bob(frame)
    skin, coat = (214, 220, 190), (140, 176, 118)
    dark, leaf = (74, 108, 74), (168, 206, 132)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 11 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 4, 5 if side else 6, 5, skin)
    sway = (-1, 0, 1)[frame]
    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (56, 66, 50))
        cell.rect(CX - 2, top - 1, 5, 1, dark)
        cell.vline(CX + sway, top - 16, top - 8, dark)
        cell.ellipse(CX - 3 + sway, top - 14, 3.5, 2, leaf)
        cell.ellipse(CX + 3 + sway, top - 12, 3.5, 2, leaf)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 6, 5, cooler(skin, 0.3))
        # the stem seen from behind: one furled leaf, no face
        cell.vline(CX + sway, top - 15, top - 8, dark)
        cell.ellipse(CX + sway, top - 13, 2, 4, cooler(leaf, 0.25))
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (56, 66, 50))
        cell.vline(hx + sway, top - 15, top - 8, dark)
        cell.ellipse(hx + 4 * lead + sway, top - 13, 4.5, 1.8, leaf)


FACES = {
    "gardener": draw_gardener,
    "seedling": draw_seedling,
    "commuter": draw_commuter,
    "leaf_head": draw_leaf_head,
}


# --- umbrellas: it is not raining, and it never has ---------------------------

def draw_umbrella_watcher(cell: Canvas, facing: int, frame: int) -> None:
    """It turns to face you.  It is not raining."""
    b = _bob(frame)
    canopy, rib = (198, 96, 96), (150, 62, 70)
    shaft, pale = (140, 110, 96), (238, 200, 196)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 5 + b

    cell.rect(CX - 1 + (lead if side else 0), top + 8, 2, GROUND - top - 12,
              shaft)
    _small_legs(cell, frame, CX + (lead if side else 0), GROUND - 4, shaft,
                spread=3)

    if facing == DOWN:
        # open, facing you: a scalloped dome with the ribs showing
        for row in range(9):
            span = int((1 - (row / 9) ** 2) ** 0.5 * 11)
            cell.hline(top + row, CX - span, CX + span, canopy)
        for sx in (-9, -4, 0, 4, 9):
            cell.vline(CX + sx, top + 2, top + 8, rib)
        cell.rect(CX - 3, top + 3, 2, 3, pale)
        cell.rect(CX + 2, top + 3, 2, 3, pale)
        for sx in (-11, -6, 0, 6, 11):
            cell.dot(CX + sx, top + 9, rib)
    elif facing == UP:
        # from behind: a smooth shell, a finial, and no eyes anywhere
        for row in range(9):
            span = int((1 - (row / 9) ** 2) ** 0.5 * 11)
            cell.hline(top + row, CX - span, CX + span, cooler(canopy, 0.22))
        cell.rect(CX - 1, top - 4, 3, 5, shaft)
        cell.ellipse(CX, top - 5, 2, 2, pale)
        cell.ellipse(CX, top + 4, 5, 3, cooler(canopy, 0.35))
    else:
        # in profile the canopy is a narrow arc tipped the way it walks
        for row in range(9):
            span = int((1 - (row / 9) ** 2) ** 0.5 * 5)
            cell.hline(top + row, CX - span + lead * 2, CX + span + lead * 2,
                       canopy)
        cell.rect(CX + 2 * lead + (1 if lead > 0 else -2), top + 3, 2, 3, pale)
        cell.rect(CX + 6 * lead, top + 7, 3, 2, rib)


def draw_drenched(cell: Canvas, facing: int, frame: int) -> None:
    """An umbrella for a head, and perfectly happy about it."""
    b = _bob(frame)
    canopy, rib = (198, 96, 96), (150, 62, 70)
    coat, dark = (104, 132, 176), (66, 88, 128)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 12 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    hx = CX + (lead * 2 if side else 0)
    if facing == DOWN:
        for row in range(8):
            span = int((1 - (row / 8) ** 2) ** 0.5 * (10 if not side else 5))
            cell.hline(top - 9 + row, hx - span, hx + span, canopy)
        for sx in (-8, -3, 2, 7):
            cell.vline(hx + sx, top - 7, top - 2, rib)
        cell.rect(hx - 3, top - 5, 2, 2, (250, 240, 236))
        cell.rect(hx + 2, top - 5, 2, 2, (250, 240, 236))
    elif facing == UP:
        for row in range(8):
            span = int((1 - (row / 8) ** 2) ** 0.5 * 10)
            cell.hline(top - 9 + row, hx - span, hx + span,
                       cooler(canopy, 0.25))
        cell.rect(hx - 1, top - 14, 3, 6, dark)
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        for row in range(8):
            span = int((1 - (row / 8) ** 2) ** 0.5 * 5)
            cell.hline(top - 9 + row, hx - span, hx + span, canopy)
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (250, 240, 236))
        cell.rect(hx + 5 * lead, top - 3, 3, 2, rib)


def draw_rain_listener(cell: Canvas, facing: int, frame: int) -> None:
    """"Listen."  It is not raining.  It has never rained."""
    b = _bob(frame)
    skin, cloth = (226, 220, 214), (150, 172, 178)
    dark, inner = (88, 104, 116), (196, 176, 172)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 12 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, cloth)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 4, 4.5 if side else 5.5, 5, skin)

    if facing == DOWN:
        # both ears, cupped forward, enormous
        for sx in (-8, 8):
            cell.ellipse(CX + sx, top - 5, 4, 6, skin)
            cell.ellipse(CX + sx, top - 5, 2, 4, inner)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (70, 76, 84))
        cell.rect(CX - 2, top - 1, 5, 1, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5.5, 5, cooler(skin, 0.28))
        for sx in (-8, 8):
            cell.ellipse(CX + sx, top - 5, 3, 6, cooler(skin, 0.18))
        cell.rect(CX - 5, top + 1, 11, 2, cooler(cloth, 0.3))
    else:
        # one ear, edge-on and turned toward whatever it is listening for
        cell.ellipse(hx + 5 * lead, top - 5, 2, 6, skin)
        cell.ellipse(hx + 5 * lead, top - 5, 1, 4, inner)
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (70, 76, 84))


def draw_spoke_keeper(cell: Canvas, facing: int, frame: int) -> None:
    """Carrying the handle without the umbrella."""
    b = _bob(frame)
    coat, dark = (178, 148, 140), (104, 88, 84)
    skin, rod = (220, 214, 208), (196, 96, 96)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (66, 58, 56))
        # the naked spokes, spread across the front
        cell.rect(CX + 4, top - 2, 2, 14, rod)
        for i, sx in enumerate((-3, 0, 3, 6)):
            cell.line(CX + 5, top + 1, CX + 5 + sx, top - 6 + abs(sx) // 2, rod)
    elif facing == UP:
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.28))
        cell.ellipse(CX, top - 5, 4.5, 3, dark)
        # only the shaft clears the shoulder; the spokes are all in front
        cell.rect(CX + 4, top - 8, 2, 8, cooler(rod, 0.3))
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 5, 2, 2,
                  (66, 58, 56))
        rx = CX + 4 * lead
        cell.rect(rx, top - 6, 2, 18, rod)
        for dy in (-6, -3, 0):
            cell.line(rx, top + dy, rx + 5 * lead, top + dy - 4, rod)


UMBRELLAS = {
    "umbrella_watcher": draw_umbrella_watcher,
    "drenched": draw_drenched,
    "rain_listener": draw_rain_listener,
    "spoke_keeper": draw_spoke_keeper,
}


# --- stars: a shallow ocean with nothing under it ----------------------------

def draw_ferryman(cell: Canvas, facing: int, frame: int) -> None:
    """Poles a boat that is not there.  There is nowhere to go."""
    b = _bob(frame)
    robe, dark = (70, 78, 140), (36, 40, 88)
    skin, pole = (216, 224, 240), (160, 200, 240)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b

    # a very tall robe that meets the water without feet
    for row in range(GROUND - 2 - top):
        span = (3 if side else 4) + row * (3 if side else 5) // (GROUND - 2 - top)
        drift = lead if side else 0
        cell.hline(top + row, CX - span + drift, CX + span + drift,
                   robe if row % 5 else cooler(robe, 0.2))
    cell.hline(GROUND - 2, CX - (6 if side else 9), CX + (6 if side else 9),
               dark)

    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 3, 4.5, 5, skin)
    cell.ellipse(hx, top - 5, 5, 3, dark)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 3, 2, 2, (30, 34, 62))
        # the pole held across, foreshortened to a short bar
        cell.rect(CX + 5, top - 8, 2, 26, pole)
        cell.rect(CX + 3, top + 3, 6, 2, cooler(pole, 0.3))
    elif facing == UP:
        cell.ellipse(hx, top - 3, 4.5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 5, 5, 3.5, cooler(dark, 0.2))
        # a hood seam and the pole angled away over the far shoulder
        cell.vline(CX, top - 1, GROUND - 4, cooler(robe, 0.35))
        cell.line(CX - 4, top - 6, CX - 9, top - 14, pole)
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 3, 2, 2, (30, 34, 62))
        # sighting along the pole: it leaves the cell at both ends
        cell.line(CX + 8 * lead, top - 9, CX - 6 * lead, GROUND - 4, pole)


def draw_lantern_bearer(cell: Canvas, facing: int, frame: int) -> None:
    """The only light for a very long way.  Does not seem to know."""
    b = _bob(frame)
    coat, dark = (120, 130, 196), (58, 62, 116)
    skin, brass = (240, 226, 206), (238, 206, 126)
    flame = (255, 250, 226)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    # the light it throws, on the ground around it
    glow = (1, 0, 1)[frame]
    cell.ellipse(CX, GROUND - 2, 11 + glow, 3.5, cooler(flame, 0.62))

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (48, 44, 68))
        cell.rect(CX + 5, top - 1, 1, 4, brass)
        cell.round_rect(CX + 2, top + 3, 7, 8, 2, brass)
        cell.ellipse(CX + 5, top + 7, 2, 2.5, flame)
    elif facing == UP:
        cell.ellipse(CX, top - 4, 5, 5, cooler(skin, 0.3))
        cell.ellipse(CX, top - 5, 4.5, 3, dark)
        # the lantern is in front, so from behind it is only a rim of light
        cell.rect(CX + 4, top + 2, 4, 2, cooler(brass, 0.25))
        cell.rect(CX - 6, top + 1, 13, 2, cooler(coat, 0.3))
        cell.rect(CX + 6, top + 4, 3, 5, cooler(flame, 0.45))
    else:
        cell.ellipse(CX + lead, top - 4, 4, 5, skin)
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top - 5, 2, 2,
                  (48, 44, 68))
        lx = CX + 3 * lead if lead > 0 else CX - 9
        cell.rect(lx + 2, top - 2, 1, 5, brass)
        cell.round_rect(lx, top + 3, 6, 8, 2, brass)
        cell.ellipse(lx + 3, top + 7, 1.5, 2.5, flame)


def draw_wader(cell: Canvas, facing: int, frame: int) -> None:
    """Standing in it up to the knee.  There is nothing to stand in."""
    b = _bob(frame)
    coat, dark = (110, 132, 200), (58, 70, 128)
    skin, ripple = (214, 220, 240), (168, 196, 240)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 8, coat)
    # the water it is in, which is not there
    for i, ry in enumerate((GROUND - 7, GROUND - 4)):
        span = (7 if side else 10) - i * 2
        cell.hline(ry + (frame % 2), CX - span, CX + span, ripple)
        cell.hline(ry + 1 + (frame % 2), CX - span + 2, CX + span - 2,
                   cooler(ripple, 0.3))

    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 4, 4.5 if side else 5, 5, skin)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (40, 46, 84))
        cell.rect(CX - 5, top + 2, 11, 2, dark)     # a scarf, ends forward
        cell.rect(CX + 3, top + 4, 3, 8, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.3))
        cell.ellipse(hx, top - 5, 4.5, 3, dark)
        cell.rect(CX - 5, top + 2, 11, 2, cooler(dark, 0.2))
        cell.vline(CX, top + 4, GROUND - 9, cooler(coat, 0.3))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (40, 46, 84))
        cell.rect(CX - 4 * lead + lead, top + 2, 8, 2, dark)
        cell.rect(CX - 6 * lead + lead, top + 4, 2, 9, dark)


def draw_net_caster(cell: Canvas, facing: int, frame: int) -> None:
    """Casts the ring out over the water and pulls it back.  Always empty."""
    b = _bob(frame)
    coat, dark = (88, 108, 172), (44, 56, 108)
    skin, net = (206, 214, 238), (226, 236, 255)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 4, 4.5 if side else 5, 5, skin)
    reach = (0, 2, 4)[frame]

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (36, 42, 78))
        # the ring open toward you, mesh across it
        cell.ellipse(CX, top + 9 + reach, 8, 4, net, filled=False)
        cell.ellipse(CX, top + 9 + reach, 7, 3, cooler(net, 0.4), filled=False)
        for sx in (-4, 0, 4):
            cell.vline(CX + sx, top + 7 + reach, top + 12 + reach,
                       cooler(net, 0.5))
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.32))
        cell.ellipse(hx, top - 5, 4.5, 3, dark)
        # the ring is cast away from you: only the line over the shoulder
        cell.line(CX + 3, top + 1, CX + 9, top - 9 - reach, net)
        cell.ellipse(CX + 9, top - 11 - reach, 3, 1.5, net, filled=False)
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (36, 42, 78))
        # edge-on the ring is a line, swung out ahead
        rx = CX + (6 + reach) * lead
        cell.ellipse(rx, top + 6, 1.5, 5, net, filled=False)
        cell.line(CX + 2 * lead, top + 2, rx, top + 3, net)


STARS = {
    "ferryman": draw_ferryman,
    "lantern_bearer": draw_lantern_bearer,
    "wader": draw_wader,
    "net_caster": draw_net_caster,
}


# --- the room: ordinary things, which is the point ---------------------------

def draw_television(cell: Canvas, facing: int, frame: int) -> None:
    """Pleased to see you.  From behind it is all vents and cable."""
    b = _bob(frame)
    case, dark = (176, 186, 182), (108, 118, 118)
    glass, lit = (58, 70, 78), (198, 232, 226)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 8 + b
    w = 9 if side else 18

    cell.round_rect(CX - w // 2 + (lead * 2 if side else 0), top, w, 15, 3, case)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 6)

    if facing == DOWN:
        cell.rect(CX - 6, top + 3, 12, 9, glass)
        cell.rect(CX - 6, top + 3, 12, 1, cooler(glass, 0.4))
        for i in range(0, 9, 2):
            cell.hline(top + 4 + i, CX - 5, CX + 5, cooler(lit, 0.55))
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, top + 6, 2, 2, lit)
        cell.rect(CX - 1, top + 9, 3, 1, lit)
        cell.rect(CX + 7, top + 4, 2, 2, dark)
    elif facing == UP:
        # the back of a set: louvres, a dial, and the cable going nowhere
        for i in range(0, 13, 2):
            cell.hline(top + 2 + i, CX - 7, CX + 7, cooler(case, 0.28))
        cell.ellipse(CX + 4, top + 4, 2.5, 2.5, dark)
        cell.line(CX - 5, top + 13, CX - 9, GROUND - 4, dark)
        cell.rect(CX - 2, top - 4, 5, 5, dark)      # the aerial socket
    else:
        cell.rect(CX + (w // 2 - 3) * lead + lead * 2, top + 3, 3, 9, glass)
        for i in range(0, 13, 3):
            cell.hline(top + 2 + i, CX - 4 * lead + lead * 2,
                       CX + lead * 2, cooler(case, 0.28))
        cell.line(CX - 4 * lead, top + 13, CX - 7 * lead, GROUND - 4, dark)


def draw_mailbox(cell: Canvas, facing: int, frame: int) -> None:
    """Nothing in it.  The flag is up anyway."""
    b = _bob(frame)
    body, dark = (150, 166, 178), (94, 106, 118)
    flag, slot = (216, 96, 88), (52, 60, 70)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    w = 8 if side else 14

    # a barrel vault: rounded on top, flat below
    for row in range(6):
        span = int((1 - (1 - row / 6) ** 2) ** 0.5 * (w // 2))
        cell.hline(top + row, CX - span + (lead if side else 0),
                   CX + span + (lead if side else 0), body)
    cell.rect(CX - w // 2 + (lead if side else 0), top + 5, w, 10, body)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 5)

    if facing == DOWN:
        cell.rect(CX - 5, top + 7, 11, 3, slot)
        cell.rect(CX - 5, top + 7, 11, 1, cooler(body, 0.35))
        for ex in (CX - 4, CX + 2):
            cell.rect(ex, top + 2, 2, 2, slot)
        cell.rect(CX + 6, top - 3, 2, 8, dark)
        cell.rect(CX + 7, top - 3, 4, 3, flag)
    elif facing == UP:
        # closed back: a hinge strip and the post it came off
        cell.rect(CX - w // 2, top + 4, w, 2, cooler(body, 0.3))
        cell.vline(CX, top + 1, top + 14, cooler(body, 0.22))
        cell.rect(CX - 2, top + 15, 5, 6, dark)
        cell.rect(CX - 8, top - 3, 2, 8, dark)
        cell.rect(CX - 11, top - 3, 4, 3, cooler(flag, 0.3))
    else:
        cell.rect(CX + (w // 2 - 2) * lead + lead, top + 6, 2, 4, slot)
        cell.rect(CX - w // 2 * lead + lead, top + 4, 2, 11, cooler(body, 0.3))
        cell.rect(CX + 5 * lead, top - 3, 2, 8, dark)
        cell.rect(CX + 5 * lead, top - 3, 3 * lead, 3, flag)


def draw_coat_stand(cell: Canvas, facing: int, frame: int) -> None:
    """Wearing everything you own.  None of it is yours any more."""
    b = _bob(frame)
    wood, dark = (168, 132, 96), (110, 84, 62)
    coat, scarf = (108, 118, 152), (196, 108, 104)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 4 + b

    cell.rect(CX - 1 + (lead if side else 0), top, 3, GROUND - top - 4, wood)
    cell.rect(CX - (3 if side else 5), GROUND - 6, (7 if side else 11), 3, dark)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.rect(CX - 7, top + 2, 15, 2, wood)      # the arms, spread
        cell.rect(CX - 6, top + 4, 13, 14, coat)
        cell.rect(CX - 6, top + 4, 13, 2, warmer(coat, 0.25))
        cell.vline(CX, top + 6, top + 17, cooler(coat, 0.3))
        cell.rect(CX - 4, top + 1, 9, 2, scarf)
    elif facing == UP:
        cell.rect(CX - 7, top + 2, 15, 2, wood)
        cell.rect(CX - 6, top + 4, 13, 14, cooler(coat, 0.22))
        cell.rect(CX + 3, top - 1, 3, 12, scarf)     # a scarf hanging behind
        cell.rect(CX - 2, top - 3, 5, 4, wood)
    else:
        cell.rect(CX - 3 * lead + lead, top + 2, 7, 2, wood)
        cell.rect(CX - 3 * lead + lead, top + 4, 6, 14, coat)
        cell.rect(CX + 4 * lead, top + 1, 2, 10, scarf)


def draw_clock(cell: Canvas, facing: int, frame: int) -> None:
    """Right twice, and neither time is now."""
    b = _bob(frame)
    case, dark = (196, 162, 112), (128, 100, 64)
    face, hand = (242, 236, 216), (60, 50, 44)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 5 + b
    w = 7 if side else 15

    cell.round_rect(CX - w // 2 + (lead if side else 0), top, w,
                    GROUND - top - 5, 3, case)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top + 6, 5.5, 5.5, face)
        cell.vline(CX, top + 2, top + 6, hand)
        cell.hline(top + 6, CX, CX + 4, hand)
        for a in ((0, -4), (4, 0), (0, 4), (-4, 0)):
            cell.dot(CX + a[0], top + 6 + a[1], dark)
        cell.rect(CX - 2, top + 15, 5, 6, dark)      # the pendulum window
        cell.ellipse(CX, top + 19 + (-1, 0, 1)[frame], 2, 2, face)
    elif facing == UP:
        # the back of a case: a door, a keyhole, and the weights on their chain
        cell.rect(CX - w // 2 + 1, top + 1, w - 2, GROUND - top - 7,
                  cooler(case, 0.22))
        cell.ellipse(CX + 3, top + 8, 1.5, 1.5, dark)
        cell.vline(CX - 3, top + 3, top + 16, dark)
        cell.rect(CX - 4, top + 16, 3, 5, cooler(case, 0.4))
    else:
        cell.ellipse(CX + (w // 2 - 1) * lead + lead, top + 6, 1.5, 5, face)
        cell.rect(CX - w // 2 * lead + lead, top + 2, 2, 16, cooler(case, 0.3))
        cell.rect(CX - lead + lead, top + 15, 3, 6, dark)


ROOM = {
    "television": draw_television,
    "mailbox": draw_mailbox,
    "coat_stand": draw_coat_stand,
    "clock": draw_clock,
}


# --- the nexus: whoever waits by the doors ------------------------------------

def draw_keeper(cell: Canvas, facing: int, frame: int) -> None:
    """Sits by the doors and has never once looked up."""
    b = _bob(frame) // 2
    coat, dark = (84, 76, 116), (48, 44, 72)
    skin, pale = (228, 214, 226), (170, 158, 190)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 13 + b

    # seated: wide at the base, and it never rises
    for row in range(GROUND - 3 - top):
        span = (4 if side else 5) + row * (3 if side else 6) // (GROUND - 3 - top)
        cell.hline(top + row, CX - span + (lead if side else 0),
                   CX + span + (lead if side else 0), coat)
    cell.hline(GROUND - 3, CX - (7 if side else 11), CX + (7 if side else 11),
               dark)

    hx = CX + (lead if side else 0)
    # the head is always tipped down, whichever way the body faces
    cell.ellipse(hx, top - 2, 4.5 if side else 5, 4.5, skin)

    if facing == DOWN:
        cell.ellipse(CX, top - 4, 5.5, 3.5, dark)
        cell.rect(CX - 3, top, 7, 1, pale)          # lowered lids, not eyes
        cell.rect(CX - 6, top + 6, 13, 2, cooler(coat, 0.3))
    elif facing == UP:
        # From behind, the hood is up and the head has gone into it entirely —
        # a keeper who never looks up has nothing to show you when you walk
        # round the back.
        cell.ellipse(hx, top - 1, 6.5, 6, coat)
        cell.ellipse(hx, top, 5, 4.5, cooler(coat, 0.35))
        cell.vline(CX, top + 4, GROUND - 4, cooler(coat, 0.4))
        for ry in range(top + 6, GROUND - 4, 4):
            cell.hline(ry, CX - 8, CX + 8, cooler(coat, 0.25))
    else:
        cell.ellipse(hx, top - 4, 4.5, 3, dark)
        cell.rect(hx + (1 if lead > 0 else -2), top, 2, 1, pale)
        cell.vline(CX - 5 * lead + lead, top + 2, GROUND - 4,
                   cooler(coat, 0.3))


def draw_sleeper(cell: Canvas, facing: int, frame: int) -> None:
    """Asleep, standing up.  You decide not to."""
    b = _bob(frame)
    gown, dark = (196, 172, 220), (118, 108, 156)
    skin = (238, 216, 200)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12
    # the whole figure leans a little, and never quite falls
    tilt = (-1, 0, 1)[frame]

    cell.rect(CX - bw // 2 + tilt + (lead if side else 0), top, bw,
              GROUND - top - 4, gown)
    hx = CX + tilt + (lead if side else 0)
    cell.ellipse(hx, top - 4, 4.5 if side else 5, 5, skin)

    if facing == DOWN:
        cell.rect(CX - 4 + tilt, top - 4, 3, 1, dark)   # closed eyes
        cell.rect(CX + 2 + tilt, top - 4, 3, 1, dark)
        cell.rect(CX - 5 + tilt, top + 3, 11, 2, cooler(gown, 0.25))
    elif facing == UP:
        cell.ellipse(hx, top - 5, 5, 4, dark)           # hair, no face
        cell.vline(CX + tilt, top + 1, GROUND - 5, cooler(gown, 0.3))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 4, 2, 1, dark)
        cell.ellipse(hx - 3 * lead, top - 5, 3, 3.5, dark)
        cell.vline(CX + tilt - 3 * lead, top + 1, GROUND - 5,
                   cooler(gown, 0.25))


def draw_cloud_ladder(cell: Canvas, facing: int, frame: int) -> None:
    """Carrying a ladder.  There is nothing to lean it on."""
    b = _bob(frame)
    cloud, shade = (238, 240, 248), (186, 192, 212)
    wood, dark = (188, 152, 104), (128, 100, 66)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 15 + b

    if side:
        cell.ellipse(CX + lead, cy, 6, 6, cloud)
        cell.ellipse(CX + lead - 2, cy + 2, 4, 4, shade)
    else:
        cell.ellipse(CX - 4, cy + 1, 5, 4.5, cloud)
        cell.ellipse(CX + 4, cy + 1, 5, 4.5, cloud)
        cell.ellipse(CX, cy - 2, 6, 5.5, cloud)
    _small_legs(cell, frame, CX + (lead if side else 0), GROUND - 4, shade,
                spread=3 if side else 4)

    if facing == DOWN:
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, cy - 2, 2, 3, (86, 96, 120))
        # the ladder held across, so it reads as rungs and two stiles
        cell.rect(CX - 10, cy + 5, 21, 2, wood)
        cell.rect(CX - 10, cy + 9, 21, 2, wood)
        for rx in range(CX - 8, CX + 9, 5):
            cell.vline(rx, cy + 5, cy + 10, dark)
    elif facing == UP:
        # from behind, the ladder is end-on: two dots and a long shadow
        cell.ellipse(CX, cy - 1, 7, 6, shade)
        cell.rect(CX - 3, cy + 4, 2, 2, wood)
        cell.rect(CX + 2, cy + 4, 2, 2, wood)
        cell.vline(CX - 2, cy + 6, GROUND - 5, cooler(wood, 0.35))
        cell.vline(CX + 3, cy + 6, GROUND - 5, cooler(wood, 0.35))
    else:
        cell.rect(CX + (1 if lead > 0 else -2) + lead, cy - 2, 2, 3,
                  (86, 96, 120))
        # Carried fore and aft, tipped the way it walks, so the two profiles
        # are mirror images rather than the same bar twice.
        for i, sy in enumerate((cy + 3, cy + 7)):
            for x in range(CELL_W_FULL):
                cell.rect(x, sy + (x if lead > 0 else CELL_W_FULL - x) // 8,
                          1, 2, wood)
        for rx in range(2, CELL_W_FULL, 6):
            off = (rx if lead > 0 else CELL_W_FULL - rx) // 8
            cell.vline(rx, cy + 3 + off, cy + 8 + off, dark)


def draw_doorframe(cell: Canvas, facing: int, frame: int) -> None:
    """A door with nothing behind it, and it is looking for a wall."""
    b = _bob(frame)
    frame_c, dark = (150, 138, 176), (86, 78, 112)
    inside = (30, 26, 48)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 4 + b
    w = 6 if side else 16

    cell.rect(CX - w // 2 + (lead * 2 if side else 0), top, w,
              GROUND - top - 4, frame_c)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=2 if side else 6)

    if facing == DOWN:
        # open: you can see the dark that is not a room
        cell.rect(CX - 5, top + 4, 11, GROUND - top - 10, inside)
        cell.rect(CX - 5, top + 4, 11, 1, dark)
        cell.ellipse(CX + 3, top + 13, 1.5, 1.5, (226, 200, 140))
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top + 7, 2, 3, (196, 186, 220))
    elif facing == UP:
        # from behind it is simply solid: a panel, and no opening at all
        cell.rect(CX - w // 2 + 2, top + 2, w - 4, GROUND - top - 8,
                  cooler(frame_c, 0.22))
        cell.rect(CX - 4, top + 5, 9, 7, cooler(frame_c, 0.36))
        cell.rect(CX - 4, top + 14, 9, 7, cooler(frame_c, 0.36))
    else:
        cell.rect(CX - w // 2 + (lead * 2), top + 3, 2, GROUND - top - 9,
                  inside)
        cell.vline(CX + (w // 2 - 1) * lead + lead * 2, top, GROUND - 5,
                   warmer(frame_c, 0.3))


NEXUS = {
    "keeper": draw_keeper,
    "sleeper": draw_sleeper,
    "cloud_ladder": draw_cloud_ladder,
    "doorframe": draw_doorframe,
}


# --- stairs: everything is going up, and nothing arrives ---------------------

def draw_climber(cell: Canvas, facing: int, frame: int) -> None:
    """"Nearly there."  They have not moved."""
    b = _bob(frame)
    coat, dark = (208, 206, 216), (128, 128, 150)
    skin, rope = (232, 216, 204), (238, 208, 148)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12
    # permanently mid-stride: one leg up, always the same one
    rise = (2, 1, 2)[frame]

    cell.rect(CX - bw // 2 + (lead if side else 0), top - rise, bw,
              GROUND - top - 4, coat)
    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 5 - rise, 4.5 if side else 5, 5, skin)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 6 - rise, 2, 2, (64, 60, 76))
        cell.rect(CX - 6, top + 2 - rise, 13, 2, rope)   # coiled across
        cell.rect(CX - 6, GROUND - 8, 5, 5, dark)        # the raised knee
        cell.rect(CX + 2, GROUND - 5, 5, 3, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 6 - rise, 5, 4, dark)
        # the coil hangs down the back, and both boots are flat on the step
        cell.ellipse(CX + 4, top + 4 - rise, 3.5, 5, rope, filled=False)
        cell.rect(CX - 6, GROUND - 5, 5, 3, dark)
        cell.rect(CX + 2, GROUND - 5, 5, 3, dark)
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 6 - rise, 2, 2,
                  (64, 60, 76))
        cell.ellipse(CX + 4 * lead, top + 2 - rise, 2, 4, rope, filled=False)
        cell.rect(CX + 2 * lead, GROUND - 9, 5, 4, dark)
        cell.rect(CX - 4 * lead, GROUND - 5, 5, 3, dark)


def draw_long_bird(cell: Canvas, facing: int, frame: int) -> None:
    """Turns its head all the way round to see you, then all the way back."""
    b = _bob(frame)
    plume, dark = (244, 244, 248), (176, 180, 196)
    beak, leg = (238, 178, 96), (198, 152, 90)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    body_y = 20 + b

    cell.ellipse(CX + (lead if side else 0), body_y, 6 if side else 8, 5.5,
                 plume)
    cell.vline(CX - 2, body_y + 4, GROUND - 3, leg)
    cell.vline(CX + 2, body_y + 4, GROUND - 3, leg)
    cell.hline(GROUND - 3, CX - 4, CX, leg)
    cell.hline(GROUND - 3, CX + 1, CX + 5, leg)

    # the neck: absurdly long, and it goes somewhere different every facing
    if facing == DOWN:
        for i in range(12):
            cell.rect(CX - 1, body_y - 5 - i, 3, 1, plume)
        cell.ellipse(CX, body_y - 17, 3.5, 3, plume)
        for ex in (CX - 2, CX + 1):
            cell.dot(ex, body_y - 18, (52, 48, 60))
        cell.rect(CX - 1, body_y - 15, 3, 3, beak)
    elif facing == UP:
        # gone over the shoulder and back on itself: the head faces away
        for i in range(10):
            cell.rect(CX - 1 + i // 3, body_y - 5 - i, 3, 1, dark)
        cell.ellipse(CX + 3, body_y - 15, 3.5, 3, dark)
        cell.ellipse(CX, body_y - 1, 6, 4, dark)
        cell.rect(CX + 2, body_y - 12, 3, 4, cooler(beak, 0.3))
    else:
        for i in range(12):
            cell.rect(CX - 1 + (i * lead) // 3, body_y - 5 - i, 3, 1, plume)
        hx = CX + (4 * lead)
        cell.ellipse(hx, body_y - 17, 3, 3, plume)
        cell.dot(hx + lead, body_y - 18, (52, 48, 60))
        cell.rect(hx + 2 * lead, body_y - 17, 4, 2, beak)


def draw_handrail(cell: Canvas, facing: int, frame: int) -> None:
    """A banister that got up.  It still wants to be held on to."""
    b = _bob(frame)
    wood, dark = (198, 176, 148), (132, 112, 88)
    brass = (226, 194, 128)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 4 + b

    # turned balusters, and a rail that rises the way stairs do
    if facing == DOWN or facing == UP:
        for i, bx in enumerate((-7, -2, 3)):
            cell.rect(CX + bx, top + 6 - i * 2, 4, GROUND - top - 10, wood)
            cell.ellipse(CX + bx + 2, top + 11 - i * 2, 3, 2.5,
                         wood if facing == DOWN else dark)
        for i in range(17):
            cell.rect(CX - 8 + i, top + 5 - i // 3, 2, 3, brass)
    else:
        cell.rect(CX - 1 + lead, top + 6, 4, GROUND - top - 10, wood)
        cell.ellipse(CX + 1 + lead, top + 11, 3, 2.5, wood)
        for i in range(CELL_W_FULL):
            cell.rect(i, top + 8 - (i if lead > 0 else CELL_W_FULL - i) // 3,
                      1, 3, brass)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=3 if side else 6)

    if facing == DOWN:
        for ex in (CX - 6, CX + 3):
            cell.rect(ex, top + 15, 2, 3, (70, 58, 48))
        cell.rect(CX - 2, top + 20, 5, 1, dark)
    elif facing == UP:
        cell.rect(CX - 8, top + 14, 17, 2, dark)
        cell.rect(CX - 8, top + 20, 17, 2, dark)
    else:
        cell.rect(CX + (1 if lead > 0 else -2) + lead, top + 15, 2, 3,
                  (70, 58, 48))


def draw_descender(cell: Canvas, facing: int, frame: int) -> None:
    """Going down, in a place with no down.  Upside down about it."""
    b = _bob(frame)
    coat, dark = (140, 146, 178), (84, 90, 124)
    skin = (230, 218, 208)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    # inverted: the head is at the bottom and the feet are in the air
    foot = 3 + b
    bw = 7 if side else 12
    head_y = GROUND - 7

    cell.rect(CX - bw // 2 + (lead if side else 0), foot + 5, bw,
              GROUND - foot - 16, coat)
    hx = CX + (lead if side else 0)
    cell.ellipse(hx, head_y, 4.5 if side else 5, 5, skin)
    # boots, waving, at the top
    swing = (-2, 0, 2)[frame]
    cell.rect(CX - 5 + swing, foot, 4, 6, dark)
    cell.rect(CX + 2 - swing, foot, 4, 6, dark)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, head_y - 1, 2, 2, (56, 52, 70))
        cell.rect(CX - 2, head_y + 3, 5, 1, dark)
        cell.rect(CX - 6, GROUND - 14, 13, 2, cooler(coat, 0.3))
    elif facing == UP:
        cell.ellipse(hx, head_y + 1, 5, 4, dark)     # hair falling downward
        cell.vline(CX, foot + 6, GROUND - 10, cooler(coat, 0.35))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), head_y - 1, 2, 2, (56, 52, 70))
        cell.ellipse(hx - 3 * lead, head_y + 1, 3, 3.5, dark)


STAIRS = {
    "climber": draw_climber,
    "long_bird": draw_long_bird,
    "handrail": draw_handrail,
    "descender": draw_descender,
}


# --- hands: a field of them, and the procession has gone ---------------------

def draw_walking_hand(cell: Canvas, facing: int, frame: int) -> None:
    """Walks around you, not away from you.  On its fingers."""
    b = _bob(frame)
    stone, dark = (206, 202, 190), (148, 144, 132)
    deep = (104, 100, 92)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    palm = 15 + b
    step = (0, -2, 0)[frame]

    if facing == DOWN:
        # the back of a hand: knuckles toward you, fingers splayed down
        cell.ellipse(CX, palm, 8, 6.5, stone)
        for i, fx in enumerate((-7, -3, 1, 5)):
            cell.rect(CX + fx, palm + 4, 3, 9 + (step if i % 2 else 0), stone)
            cell.rect(CX + fx, palm + 11 + (step if i % 2 else 0), 3, 2, dark)
            cell.hline(palm + 7, CX + fx, CX + fx + 2, dark)
        cell.rect(CX - 10, palm - 2, 3, 6, stone)          # the thumb, aside
        for kx in (-6, -2, 2, 6):
            cell.rect(CX + kx, palm - 2, 2, 2, dark)
    elif facing == UP:
        # the palm: a bowl with lines in it, and the fingers curl away
        cell.ellipse(CX, palm, 8, 6.5, dark)
        cell.ellipse(CX, palm, 6, 5, stone)
        for ly in (palm - 2, palm + 1, palm + 4):
            cell.hline(ly, CX - 5, CX + 4, deep)
        for fx in (-7, -3, 1, 5):
            cell.rect(CX + fx, palm + 5, 3, 6, dark)
            cell.rect(CX + fx, palm + 9, 3, 3, stone)
        cell.rect(CX + 8, palm - 2, 3, 6, dark)
    else:
        # edge-on: two fingers visible, the rest hidden behind them
        cell.ellipse(CX + lead, palm, 4.5, 6.5, stone)
        for i, fx in enumerate((0, 3)):
            x = CX + (fx * lead) + lead
            cell.rect(x, palm + 4, 3, 9 + (step if i else 0), stone)
            cell.rect(x, palm + 11 + (step if i else 0), 3, 2, dark)
        cell.rect(CX - 5 * lead + lead, palm - 3, 3, 7, dark)
        cell.vline(CX + 4 * lead + lead, palm - 5, palm + 3, dark)


def draw_ring_keeper(cell: Canvas, facing: int, frame: int) -> None:
    """"It is not mine."  They do not put it down."""
    b = _bob(frame)
    coat, dark = (206, 198, 196), (150, 140, 144)
    skin, band = (226, 196, 156), (238, 226, 216)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)
    cell.ellipse(hx, top - 4, 4.5 if side else 5, 5, skin)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (72, 62, 54))
        # held out flat: a full circle, bigger than the head
        cell.ellipse(CX, top + 9, 8, 8, band, filled=False)
        cell.ellipse(CX, top + 9, 7, 7, cooler(band, 0.35), filled=False)
    elif facing == UP:
        cell.ellipse(hx, top - 5, 5, 4, dark)
        # from behind the ring is edge-on above the shoulder: a bright line
        cell.rect(CX - 1, top - 12, 3, 10, band)
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (72, 62, 54))
        cell.ellipse(CX + 5 * lead, top + 8, 2, 8, band, filled=False)
        cell.rect(CX + 2 * lead, top + 4, 3, 2, skin)


def draw_thumb(cell: Canvas, facing: int, frame: int) -> None:
    """A thumb, standing.  It has an opinion and will not give it."""
    b = _bob(frame)
    stone, dark = (198, 194, 182), (140, 136, 126)
    nail = (226, 222, 210)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 6 + b
    w = 6 if side else 10

    for row in range(GROUND - 4 - top):
        t = row / max(1, GROUND - 4 - top)
        span = int(w / 2 * (0.65 + 0.35 * (1 - (1 - t) ** 2)))
        cell.hline(top + row, CX - span + (lead if side else 0),
                   CX + span + (lead if side else 0), stone)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=2 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top + 5, 3.5, 5, nail)      # the nail, facing you
        cell.ellipse(CX, top + 4, 2.5, 3.5, cooler(nail, 0.12))
        cell.hline(top + 11, CX - 3, CX + 3, dark)
        for ex in (CX - 2, CX + 1):
            cell.dot(ex, top + 14, dark)
    elif facing == UP:
        # The knuckle side: no nail at all, a deep crease across the joint, and
        # the whole pad shaded — a thumb from behind is a different object.
        cell.ellipse(CX, top + 6, 5, 7, cooler(stone, 0.26))
        for ky in range(top + 8, GROUND - 6, 3):
            cell.hline(ky, CX - 4, CX + 4, dark)
            cell.hline(ky + 1, CX - 3, CX + 3, cooler(stone, 0.18))
        cell.ellipse(CX, top + 3, 4, 3, cooler(stone, 0.34))
    else:
        cell.ellipse(CX + 2 * lead + lead, top + 5, 1.5, 5, nail)
        cell.hline(top + 11, CX - 3 * lead + lead, CX + lead, dark)
        cell.vline(CX - 3 * lead + lead, top + 2, GROUND - 6,
                   cooler(stone, 0.28))


def draw_clasp(cell: Canvas, facing: int, frame: int) -> None:
    """Two hands holding each other.  Neither of them is anybody's."""
    b = _bob(frame)
    stone, other = (204, 200, 188), (182, 176, 168)
    dark = (128, 124, 116)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 15 + b

    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=3 if side else 5)

    if facing == DOWN:
        # interlaced: fingers of one over the back of the other
        cell.ellipse(CX - 3, cy, 6, 7, stone)
        cell.ellipse(CX + 3, cy, 6, 7, other)
        for i in range(4):
            cell.rect(CX - 6 + i * 4, cy - 5 + (i % 2) * 2, 3, 7,
                      stone if i % 2 else other)
        cell.hline(cy + 5, CX - 8, CX + 8, dark)
    elif facing == UP:
        # from behind it is one closed mass with a single seam
        cell.ellipse(CX, cy, 9, 7.5, cooler(stone, 0.14))
        cell.vline(CX, cy - 7, cy + 7, dark)
        cell.ellipse(CX, cy - 1, 5, 4, cooler(other, 0.2))
        for wy in (cy + 3, cy + 6):
            cell.hline(wy, CX - 7, CX + 7, dark)
    else:
        cell.ellipse(CX + lead, cy, 5, 7.5, stone)
        cell.ellipse(CX + 3 * lead, cy + 1, 3, 5, other)
        for i in range(3):
            cell.rect(CX + (i * 2 - 2) * lead + lead, cy - 6 + i, 3, 5,
                      other if i % 2 else stone)
        cell.hline(cy + 6, CX - 4 * lead + lead, CX + 4 * lead + lead, dark)


HANDS = {
    "walking_hand": draw_walking_hand,
    "ring_keeper": draw_ring_keeper,
    "thumb": draw_thumb,
    "clasp": draw_clasp,
}


# --- overgrown: the same town, forty more years of growth ---------------------
# The grove already has four residents.  These are not those four re-tinted:
# they are the people this channel has instead, and the difference between the
# two casts is the difference between a place that is being lived in and a
# place that is being lived *through*.

def draw_ranger(cell: Canvas, facing: int, frame: int) -> None:
    """Still managing this wood.  The clipboard has a sapling through it."""
    b = _bob(frame)
    coat, dark = (74, 108, 66), (40, 62, 40)
    skin, board = (222, 206, 178), (188, 172, 132)
    shoot = (150, 198, 118)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw, 2,
              warmer(coat, 0.22))
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)

    hx = CX + (lead if side else 0)
    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        # the peaked cap, brim toward you
        cell.ellipse(hx, top - 7, 6, 3, dark)
        cell.rect(hx - 7, top - 6, 15, 2, cooler(dark, 0.2))
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (38, 44, 36))
        # the clipboard, held flat, with the shoot standing out of it
        cell.rect(CX - 5, top + 9, 11, 9, board)
        cell.rect(CX - 3, top + 11, 7, 1, cooler(board, 0.4))
        cell.rect(CX - 3, top + 14, 7, 1, cooler(board, 0.4))
        cell.vline(CX, top + 2, top + 10, shoot)
        cell.ellipse(CX - 3, top + 4, 3, 1.6, shoot)
        cell.ellipse(CX + 3, top + 6, 3, 1.6, shoot)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 6, 6, 4, cooler(dark, 0.15))
        # from behind: no brim, no board — a pack, and the shoot over one
        # shoulder, which is the only part of him you can see is growing
        cell.rect(CX - 5, top + 3, 11, 9, cooler(coat, 0.28))
        cell.rect(CX - 5, top + 3, 11, 2, coat)
        cell.line(CX + 4, top + 2, CX + 8, top - 8, shoot)
        cell.ellipse(CX + 8, top - 9, 2.4, 3, cooler(shoot, 0.2))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.ellipse(hx + lead, top - 7, 5, 3, dark)
        cell.rect(hx + lead, top - 6, 8 * lead, 2, cooler(dark, 0.2))
        cell.rect(hx + (1 if lead > 0 else -2), top - 4, 2, 2, (38, 44, 36))
        # the board seen edge-on: a line, not a rectangle
        bx = CX + 5 * lead
        cell.rect(bx - 1, top + 9, 3, 9, board)
        cell.line(bx, top + 8, bx + 5 * lead, top - 3, shoot)
        cell.ellipse(bx + 5 * lead, top - 4, 3, 1.6, shoot)


def draw_grafter(cell: Canvas, facing: int, frame: int) -> None:
    """One arm was spliced into a branch and the splice took."""
    b = _bob(frame)
    shirt, dark = (128, 132, 84), (56, 66, 44)
    skin, bark = (226, 208, 180), (108, 90, 58)
    leaf = (162, 202, 118)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 11 + b
    bw = 6 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, shirt)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)
    sway = (0, 1, 0)[frame]

    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (46, 40, 34))
        cell.rect(CX - 2, top - 1, 5, 1, cooler(skin, 0.4))
        # left arm ordinary, right arm bark from the elbow out
        cell.rect(CX - 8, top + 2, 3, 9, skin)
        cell.rect(CX + 5, top + 2, 3, 5, skin)
        cell.rect(CX + 5, top + 7, 3, 7, bark)
        cell.line(CX + 6, top + 13, CX + 10 + sway, top + 18, bark)
        cell.ellipse(CX + 10 + sway, top + 18, 3, 1.8, leaf)
        cell.ellipse(CX + 7, top + 16, 2.4, 1.4, leaf)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 6, 5, 3, (62, 52, 44))
        # from behind the splice is hidden and both arms read as one shape
        cell.rect(CX - 8, top + 2, 3, 9, cooler(skin, 0.3))
        cell.rect(CX + 5, top + 2, 3, 9, bark)
        cell.rect(CX - 5, top + 1, 11, 2, cooler(shirt, 0.3))
        cell.vline(CX, top + 3, GROUND - 7, cooler(shirt, 0.25))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (46, 40, 34))
        # in profile only the grafted arm is visible, held straight out
        ax = CX + 3 * lead
        cell.rect(ax - 1, top + 3, 3, 5, skin)
        cell.line(ax, top + 8, ax + 8 * lead, top + 9 + sway, bark)
        cell.line(ax, top + 9, ax + 7 * lead, top + 12 + sway, bark)
        cell.ellipse(ax + 8 * lead, top + 8 + sway, 3, 1.6, leaf)
        cell.ellipse(ax + 6 * lead, top + 13 + sway, 2.4, 1.4, leaf)


def draw_swarm(cell: Canvas, facing: int, frame: int) -> None:
    """A person-shaped cloud of small bodies.  It uses the plural."""
    b = _bob(frame)
    body, dark = (146, 128, 74), (74, 62, 34)
    pale = (216, 200, 132)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 8 + b
    drift = (0, 1, -1)[frame]

    # the silhouette, built from dots rather than filled
    width = 5 if side else 9
    for row in range(top, GROUND - 2):
        span = width - abs(row - (top + 10)) // 5
        for col in range(-span, span + 1):
            if (row * 7 + col * 5 + drift * 3) % 3 == 0:
                continue
            cell.dot(CX + col + (lead if side else 0), row,
                     body if (row + col) % 2 else dark)
    for index in range(6):
        x = CX + ((index * 5 + drift * 2) % 13) - 6
        y = top - 4 + ((index * 7) % 22)
        cell.dot(x, y, pale)

    if facing == DOWN:
        # the face is where the swarm is *not*
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, top + 5, 2, 3, (24, 20, 16))
        cell.hline(top + 12, CX - 3, CX + 3, (24, 20, 16))
        cell.ellipse(CX, top + 2, 6, 5, body)
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, top + 1, 2, 3, (24, 20, 16))
    elif facing == UP:
        # from behind it closes up completely and reads as solid
        cell.ellipse(CX, top + 2, 6, 5, dark)
        cell.ellipse(CX, top + 1, 5, 4, cooler(dark, 0.2))
        cell.rect(CX - 5, top + 8, 11, 2, dark)
    else:
        cell.ellipse(CX + lead, top + 2, 4.5, 5, body)
        cell.rect(CX + lead + (1 if lead > 0 else -2), top + 1, 2, 3,
                  (24, 20, 16))
        # streaming behind: the swarm trails the direction of travel
        for index in range(7):
            cell.dot(CX - lead * (5 + index * 2), top + 4 + (index * 3) % 14,
                     pale if index % 2 else body)


def draw_bough_sleeper(cell: Canvas, facing: int, frame: int) -> None:
    """Asleep along a branch, at head height.  Does not wake."""
    b = _bob(frame)
    bark, dark = (104, 84, 56), (52, 42, 30)
    cloth, skin = (118, 140, 96), (224, 206, 178)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    lie = 14 + b

    if facing == DOWN:
        # seen from below: the soles of two boots and the branch behind
        cell.rect(0, lie + 6, CELL_W_FULL, 4, bark)
        cell.rect(0, lie + 6, CELL_W_FULL, 1, warmer(bark, 0.25))
        cell.rect(CX - 7, lie - 4, 14, 10, cloth)
        for bx in (CX - 6, CX + 1):
            cell.round_rect(bx, lie - 9, 6, 7, 2, dark)
            cell.rect(bx + 1, lie - 8, 4, 3, cooler(dark, 0.3))
        cell.ellipse(CX, lie + 12, 4, 3, skin)      # the top of the head, far
    elif facing == UP:
        # seen from above: the crown of the head, the branch in front
        cell.rect(0, lie - 2, CELL_W_FULL, 4, bark)
        cell.rect(CX - 7, lie + 2, 14, 10, cooler(cloth, 0.25))
        cell.ellipse(CX, lie - 6, 5, 4, cooler(skin, 0.35))
        cell.ellipse(CX, lie - 7, 4.5, 3, (58, 48, 40))
        cell.rect(CX - 4, lie + 12, 9, 3, dark)
    else:
        # in profile the whole length of them is visible along the bough
        cell.rect(0, lie + 4, CELL_W_FULL, 4, bark)
        cell.rect(0, lie + 4, CELL_W_FULL, 1, warmer(bark, 0.25))
        cell.round_rect(CX - 9, lie - 4, 18, 8, 3, cloth)
        cell.ellipse(CX + 9 * lead, lie - 3, 4, 4, skin)
        cell.rect(CX + 9 * lead + (0 if lead > 0 else -1), lie - 4, 3, 1,
                  (58, 48, 40))
        # one arm hanging off the branch, swinging very slightly
        sway = (0, 1, 0)[frame]
        cell.rect(CX - 2 * lead, lie + 4, 2, 7 + sway, skin)
        cell.dot(CX - 2 * lead, lie + 11 + sway, cooler(skin, 0.3))


FACES2 = {
    "ranger": draw_ranger,
    "grafter": draw_grafter,
    "swarm": draw_swarm,
    "bough_sleeper": draw_bough_sleeper,
}


# --- off-colour: the greens fail first, and the grey work carries on ----------

def draw_staffholder(cell: Canvas, facing: int, frame: int) -> None:
    """Holding a levelling staff, sighting along a road that is not there."""
    b = _bob(frame)
    coat, dark = (150, 152, 148), (84, 86, 86)
    skin, staff = (204, 202, 196), (232, 234, 232)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 6 if side else 12

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, coat)
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)

    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (52, 54, 56))
        # the staff held upright and square on: banded its whole length
        cell.rect(CX + 6, top - 12, 4, GROUND - top + 8, staff)
        for band in range(top - 11, GROUND - 2, 4):
            cell.rect(CX + 6, band, 4, 2, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 5, 4.5, 3, (96, 98, 100))
        # from behind: the staff is on the far side and mostly hidden
        cell.rect(CX - 9, top - 6, 3, GROUND - top + 2, cooler(staff, 0.3))
        cell.rect(CX - 5, top + 1, 11, 2, cooler(coat, 0.3))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (52, 54, 56))
        # edge-on the staff is one pixel wide and the bands vanish
        sx = CX + 5 * lead
        cell.rect(sx, top - 12, 2, GROUND - top + 8, staff)
        cell.rect(CX + 2 * lead, top + 4, 4 * lead, 2, skin)


def draw_meter_reader(cell: Canvas, facing: int, frame: int) -> None:
    """Reads the meters.  Writes nothing down."""
    b = _bob(frame)
    coat, dark = (126, 128, 126), (66, 68, 70)
    skin, box = (206, 204, 198), (176, 178, 176)
    dial = (238, 240, 236)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 11 + b
    bw = 7 if side else 13
    spin = (0, 2, 4)[frame]

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 4, coat)
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw, 2,
              warmer(coat, 0.2))
    hx = CX + (lead if side else 0)

    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 5, 2, 2, (46, 48, 50))
        # the meter held out flat, dial turning
        cell.round_rect(CX - 6, top + 8, 13, 10, 2, box)
        cell.ellipse(CX, top + 13, 4, 4, dial)
        cell.line(CX, top + 13, CX + (spin - 2), top + 10, (40, 42, 44))
        cell.rect(CX - 4, top + 16, 9, 1, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 5, 4.5, 3, (80, 82, 84))
        # the meter is against their chest and invisible; a strap crosses instead
        cell.line(CX - 6, top + 1, CX + 6, top + 11, dark)
        cell.rect(CX - 6, top + 2, 13, 1, cooler(coat, 0.35))
        cell.rect(CX - 2, GROUND - 8, 5, 5, cooler(coat, 0.4))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.rect(hx + (1 if lead > 0 else -2), top - 5, 2, 2, (46, 48, 50))
        # in profile the meter is a slab and the dial is a bright edge
        mx = CX + 4 * lead
        cell.round_rect(mx - 1, top + 8, 4, 10, 1, box)
        cell.rect(mx + (2 if lead > 0 else -1), top + 11, 1, 4, dial)
        cell.rect(CX + lead, top + 4, 3 * lead, 2, skin)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=3 if side else 4)


def draw_ash_walker(cell: Canvas, facing: int, frame: int) -> None:
    """Collecting what is falling, in a jar, at the rate it falls."""
    b = _bob(frame)
    coat, dark = (168, 170, 166), (94, 96, 98)
    skin, glass = (208, 206, 200), (226, 232, 234)
    fall = (240, 242, 240)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    bw = 7 if side else 13

    # a coat with ash lying on its shoulders
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 4, coat)
    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw, 3, fall)
    _small_legs(cell, frame, CX, GROUND - 4, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)
    for index in range(5):
        cell.dot(CX - 8 + (index * 5 + frame * 2) % 17,
                 top - 8 + (index * 6 + frame * 3) % 26, fall)

    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        cell.rect(CX - 6, top - 7, 13, 2, fall)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (50, 52, 54))
        # the jar, held up, half filled and open
        cell.round_rect(CX - 4, top + 7, 9, 11, 2, glass)
        cell.rect(CX - 3, top + 13, 7, 4, fall)
        cell.rect(CX - 4, top + 6, 9, 2, cooler(glass, 0.25))
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 5, 5, 3, (86, 88, 90))
        cell.rect(CX - 6, top - 6, 13, 2, fall)
        # from behind the jar is gone and the ash on the shoulders is the shape
        cell.rect(CX - 6, top + 1, 13, 2, fall)
        cell.rect(CX - 2, top + 6, 5, GROUND - top - 12, cooler(coat, 0.3))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.rect(hx + (1 if lead > 0 else -2), top - 4, 2, 2, (50, 52, 54))
        cell.rect(hx - 4, top - 7, 9, 2, fall)
        jx = CX + 4 * lead
        cell.round_rect(jx - 2, top + 8, 5, 11, 2, glass)
        cell.rect(jx - 1, top + 14, 3, 4, fall)


def draw_last_engineer(cell: Canvas, facing: int, frame: int) -> None:
    """Knows the mast is still transmitting.  Has told nobody, because."""
    b = _bob(frame)
    overall, dark = (110, 116, 118), (58, 62, 66)
    skin, hat = (206, 202, 196), (216, 216, 210)
    lamp, cable = (250, 246, 210), (78, 80, 82)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 11 + b
    bw = 7 if side else 13
    glow = (0, 1, 0)[frame]

    cell.rect(CX - bw // 2 + (lead if side else 0), top, bw,
              GROUND - top - 5, overall)
    cell.vline(CX + (lead if side else 0), top + 2, GROUND - 6,
               cooler(overall, 0.25))
    _small_legs(cell, frame, CX, GROUND - 5, dark, spread=3 if side else 4)
    hx = CX + (lead if side else 0)

    if facing == DOWN:
        cell.ellipse(hx, top - 4, 5, 5, skin)
        cell.ellipse(hx, top - 7, 6, 3, hat)
        cell.rect(hx - 7, top - 6, 15, 2, cooler(hat, 0.2))
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, (44, 46, 48))
        # the lamp, lit, held low
        cell.ellipse(CX + 6, top + 13, 3.5 + glow, 3.5 + glow, lamp)
        cell.ellipse(CX + 6, top + 13, 2, 2, (255, 255, 240))
        cell.rect(CX + 5, top + 8, 3, 4, dark)
    elif facing == UP:
        cell.ellipse(hx, top - 4, 5, 5, cooler(skin, 0.35))
        cell.ellipse(hx, top - 6, 6, 4, cooler(hat, 0.18))
        # from behind: the coil of cable over one shoulder, no lamp at all
        for radius in (6, 4.4, 2.8):
            cell.ellipse(CX - 3, top + 8, radius, radius * 0.7, cable,
                         filled=False)
        cell.rect(CX - 5, top + 1, 11, 2, cooler(overall, 0.3))
    else:
        cell.ellipse(hx, top - 4, 4, 5, skin)
        cell.ellipse(hx + lead, top - 7, 5, 3, hat)
        cell.rect(hx + lead, top - 6, 8 * lead, 2, cooler(hat, 0.2))
        cell.rect(hx + (1 if lead > 0 else -2), top - 4, 2, 2, (44, 46, 48))
        # the lamp swings out in front, and the cable trails behind
        cell.ellipse(CX + 6 * lead, top + 13, 3 + glow, 3 + glow, lamp)
        cell.rect(CX + 3 * lead, top + 8, 2, 5, dark)
        cell.line(CX - 3 * lead, top + 6, CX - 8 * lead, top + 14, cable)


FACES3 = {
    "staffholder": draw_staffholder,
    "meter_reader": draw_meter_reader,
    "ash_walker": draw_ash_walker,
    "last_engineer": draw_last_engineer,
}


# --- no signal: nothing is drawn as itself any more ---------------------------
# These are the only residents in the game who are not made of anything.  They
# are made of the pattern that gets sent when there is nothing to send, and the
# giveaway is that they are the only figures whose *silhouette* changes when
# they turn, because a bar seen edge-on is a line.

_BARS = ((240, 236, 226), (226, 214, 96), (96, 200, 208), (96, 196, 108),
         (208, 92, 178), (206, 58, 54), (74, 84, 176))


def draw_presenter(cell: Canvas, facing: int, frame: int) -> None:
    """Introducing something that is not going to happen."""
    b = _bob(frame)
    dark = (24, 22, 26)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 8 + b
    bw = 4 if side else 14

    # the body is the bars, run across whichever width the facing gives
    x0 = CX - bw // 2 + (lead if side else 0)
    for index in range(bw):
        cell.rect(x0 + index, top + 8, 1, GROUND - top - 10,
                  _BARS[index % len(_BARS)] if not side
                  else _BARS[(index + 3) % len(_BARS)])
    cell.rect(x0, GROUND - 3, bw, 2, dark)

    if facing == DOWN:
        # the head is one block of bars with a black square cut in it
        for index in range(11):
            cell.rect(CX - 5 + index, top - 4, 1, 11,
                      _BARS[index % len(_BARS)])
        cell.rect(CX - 3, top, 7, 5, dark)
        cell.rect(CX - 2, top + 1, 2, 2, (240, 236, 226))
        cell.rect(CX + 1, top + 1, 2, 2, (240, 236, 226))
    elif facing == UP:
        # from behind: no cut, and the whole head is the grey step wedge
        for index in range(11):
            value = 32 + index * 20
            cell.rect(CX - 5 + index, top - 4, 1, 11, (value, value, value))
        cell.rect(CX - 5, top + 6, 11, 1, dark)
    else:
        # edge on: the bars collapse to one column and the head is a line
        cell.rect(CX + lead - 1, top - 4, 3, 11, (240, 236, 226))
        cell.rect(CX + lead - 1, top - 4, 3, 3, (206, 58, 54))
        cell.rect(CX + lead + (1 if lead > 0 else -1), top + 1, 1, 2, dark)


def draw_caption(cell: Canvas, facing: int, frame: int) -> None:
    """Speaks only in the words along the bottom of the picture."""
    b = _bob(frame)
    dark, ink = (18, 14, 18), (240, 236, 226)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    words = ((3, 5, 2), (4, 3, 4), (2, 6, 3))[frame]

    if facing == DOWN:
        cell.rect(CX - 9, top, 19, GROUND - top - 3, dark)
        x = CX - 7
        for length in words:
            cell.rect(x, top + 5, length, 3, ink)
            x += length + 2
        x = CX - 6
        for length in reversed(words):
            cell.rect(x, top + 12, length, 3, ink)
            x += length + 2
        cell.rect(CX - 9, top, 19, 1, (206, 58, 54))
    elif facing == UP:
        # from behind, a caption is a blank black bar: the words face outward
        cell.rect(CX - 9, top, 19, GROUND - top - 3, dark)
        cell.rect(CX - 9, top, 19, 2, (52, 44, 52))
        cell.rect(CX - 8, GROUND - 6, 17, 1, (52, 44, 52))
    else:
        # Edge-on it is nearly nothing, which is the joke — but the words are
        # still running, so they spill off the *leading* edge and trail behind
        # it, and that spill is what makes left and right different sprites
        # rather than the same four-pixel bar twice.
        bar = CX + 4 * lead
        cell.rect(bar - 2, top, 4, GROUND - top - 3, dark)
        cell.rect(bar - 2, top, 4, 1, (206, 58, 54))
        cell.rect(bar - 2, top + 5, 4, 3, ink)
        cell.rect(bar - 2, top + 12, 4, 3, ink)
        # the text leaving the bar, in the direction of travel
        run = CX + 8 * lead
        for index, length in enumerate(words):
            cell.rect(min(run, run - length * lead) if lead < 0 else run,
                      top + 5 + index * 5, length, 2, ink)
            run += (length + 2) * lead
        # and the sliver still to arrive, behind
        cell.rect(CX - 7 * lead, top + 9, 3, 2, (96, 92, 96))


def draw_test_tone(cell: Canvas, facing: int, frame: int) -> None:
    """One note, held.  It has been holding it for some time."""
    dark, ink = (24, 22, 26), (240, 236, 226)
    accent = (74, 128, 148)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    phase = frame * 4

    if facing == DOWN:
        # the waveform, seen face on: wide, symmetrical, and loud
        for row in range(6, GROUND - 2):
            width = 2 + abs(8 - ((row + phase) % 16)) // 2
            cell.rect(CX - width, row, width * 2, 1,
                      ink if ((row + phase) % 16) < 8 else accent)
        cell.rect(CX - 1, 6, 3, GROUND - 8, dark)
        cell.rect(CX - 4, 10, 9, 2, dark)
    elif facing == UP:
        # from behind, a waveform is a straight line
        cell.rect(CX - 2, 6, 5, GROUND - 8, ink)
        cell.rect(CX - 1, 6, 3, GROUND - 8, accent)
        cell.rect(CX - 5, GROUND - 5, 11, 2, dark)
    else:
        # edge on: half a waveform, and it leans the way it is going
        for row in range(6, GROUND - 2):
            width = 1 + abs(8 - ((row + phase) % 16)) // 2
            if lead > 0:
                cell.rect(CX + 1, row, width, 1, ink)
            else:
                cell.rect(CX - width, row, width, 1, ink)
        cell.rect(CX, 6, 2, GROUND - 8, accent)


def draw_continuity(cell: Canvas, facing: int, frame: int) -> None:
    """Apologises for the interruption.  Does not say what was interrupted."""
    b = _bob(frame)
    dark = (24, 22, 26)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    bw = 5 if side else 13

    # a grey step wedge for a body, stepping darker toward the ground
    x0 = CX - bw // 2 + (lead if side else 0)
    steps = max(1, bw)
    for index in range(steps):
        value = 216 - index * (168 // steps)
        cell.rect(x0 + index, top + 7, 1, GROUND - top - 9, (value, value, value))

    if facing == DOWN:
        cell.ellipse(CX, top + 1, 6, 6, (206, 58, 54))
        cell.ellipse(CX, top + 1, 4.5, 4.5, (240, 236, 226))
        # the apology: a black bar where a mouth would be, and no eyes
        cell.rect(CX - 4, top + 3, 9, 2, dark)
        cell.rect(CX - 1, top - 5, 3, 3, dark)
    elif facing == UP:
        # from behind the circle is solid and the wedge runs the other way
        cell.ellipse(CX, top + 1, 6, 6, (96, 96, 96))
        cell.ellipse(CX, top, 5, 5, (56, 56, 56))
        for index in range(bw):
            value = 48 + index * (168 // max(1, bw))
            cell.rect(x0 + index, top + 7, 1, GROUND - top - 9,
                      (value, value, value))
    else:
        cell.ellipse(CX + lead, top + 1, 3, 6, (206, 58, 54))
        cell.ellipse(CX + lead, top + 1, 2, 4.5, (240, 236, 226))
        cell.rect(CX + lead + (1 if lead > 0 else -2), top + 3, 2, 2, dark)


FACES4 = {
    "presenter": draw_presenter,
    "caption": draw_caption,
    "test_tone": draw_test_tone,
    "continuity": draw_continuity,
}


# --- inside the murals -------------------------------------------------------
# Two residents per painting.  Everything in a mural's interior is made of the
# mural, these included: there is no skin, no cloth and no wood in any of them,
# only the two colours the painting was drawn in and the one shape it repeats.
# That is the whole reason they read as being *of* the place rather than as
# visitors to it, and it is the only constraint they are under.

def draw_lash(cell: Canvas, facing: int, frame: int) -> None:
    """An eyelash, walking.  It is longer than it needs to be."""
    b = _bob(frame)
    line, glow = (96, 240, 226), (214, 254, 250)
    dark = (20, 96, 108)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 9 + b
    sway = (0, 1, -1)[frame]

    # the shaft: one thick curved stroke from the ground up
    for row in range(top, GROUND - 2):
        offset = (row - top) // 5
        cell.rect(CX - 2 + (offset * lead if side else 0), row, 4, 1,
                  line if row % 3 else glow)
    cell.rect(CX - 2, GROUND - 3, 5, 2, dark)

    if facing == DOWN:
        # facing you, the lash is foreshortened and its root is an open lid
        cell.ellipse(CX, top - 2, 7, 4, dark)
        cell.ellipse(CX, top - 2, 5.4, 2.6, line)
        cell.ellipse(CX, top - 2, 2.4, 2.2, glow)
        cell.dot(CX, top - 2, (10, 26, 34))
        for dx in (-6, -3, 3, 6):
            cell.line(CX + dx, top - 4, CX + dx + dx // 2, top - 9, line)
    elif facing == UP:
        # from behind there is no lid and no eye: only the shaft, and it
        # carries on off the top of the cell
        cell.rect(CX - 2, 0, 4, top, dark)
        cell.rect(CX - 1, 0, 2, top, line)
        cell.ellipse(CX, top - 1, 5, 2.4, dark)
    else:
        # in profile the lash curls hard the way it is going
        for step in range(9):
            cell.dot(CX + lead * (step + 1), top - 2 - step - step * step // 8,
                     glow if step % 2 else line)
        cell.ellipse(CX + lead, top, 3.4, 3, dark)
        cell.ellipse(CX + lead, top, 2, 1.8, line)


def draw_iris(cell: Canvas, facing: int, frame: int) -> None:
    """A ring, standing on its edge.  It turns to keep you in the middle."""
    line, glow = (96, 240, 226), (240, 252, 250)
    dark = (20, 96, 108)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 15
    open_ = (0, 1, 0)[frame]

    if facing == DOWN:
        for radius in (10, 8, 6):
            cell.ellipse(CX, cy, radius, radius, line if radius % 4 else dark,
                         filled=False)
        cell.ellipse(CX, cy, 4 + open_, 4 + open_, dark)
        cell.ellipse(CX, cy, 2, 2, glow)
        for angle in range(0, 360, 30):
            x = CX + int(9.4 * math.cos(math.radians(angle)))
            y = cy + int(9.4 * math.sin(math.radians(angle)))
            cell.dot(x, y, glow)
    elif facing == UP:
        # a ring from behind is a disc: nothing to look through
        cell.ellipse(CX, cy, 10, 10, dark)
        cell.ellipse(CX, cy, 8, 8, line)
        cell.ellipse(CX, cy, 6, 6, dark)
        cell.rect(CX - 2, cy + 9, 5, GROUND - cy - 10, dark)
    else:
        # edge on it is almost a line, and it leans into the walk
        cell.ellipse(CX + lead, cy, 3.2, 10, line, filled=False)
        cell.ellipse(CX + lead, cy, 2.0, 8, dark, filled=False)
        cell.rect(CX + lead - 1, cy - 2, 3, 4, glow)
        cell.rect(CX - 1, cy + 9, 3, GROUND - cy - 10, dark)


def draw_winding(cell: Canvas, facing: int, frame: int) -> None:
    """A figure wound out of one line.  The line has no end you can find."""
    b = _bob(frame)
    line, glow = (244, 118, 196), (254, 200, 234)
    deep = (112, 30, 96)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 8 + b
    spin = frame * 0.7

    turns = 3.0 if not side else 2.0
    steps = 44
    for step in range(steps):
        progress = step / steps
        angle = spin + progress * turns * 2 * math.pi
        radius = 1.5 + progress * (5.5 if side else 8.0)
        x = CX + (lead if side else 0) + int(radius * math.cos(angle))
        y = top + 8 + int(radius * math.sin(angle) * 0.9)
        cell.dot(x, y, glow if step % 5 == 0 else line)
        cell.dot(x, y + 1, deep)
    cell.rect(CX - 2, top + 17, 5, GROUND - top - 18, deep)

    if facing == DOWN:
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, top + 5, 2, 2, (26, 10, 34))
    elif facing == UP:
        # the coil closes up: from behind it is a solid knot
        cell.ellipse(CX, top + 8, 7, 7, deep)
        cell.ellipse(CX, top + 7, 5, 5, line)
    else:
        cell.rect(CX + lead + (1 if lead > 0 else -2), top + 5, 2, 2,
                  (26, 10, 34))
        cell.line(CX + 5 * lead, top + 12, CX + 9 * lead, top + 18, line)


def draw_unplaced(cell: Canvas, facing: int, frame: int) -> None:
    """Keeps arriving at the middle and setting off again."""
    b = _bob(frame)
    line, glow = (244, 118, 196), (180, 138, 246)
    deep = (112, 30, 96)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 10 + b
    step_out = (0, 2, 4)[frame]

    body_w = 6 if side else 11
    cell.round_rect(CX - body_w // 2 + (lead if side else 0), top, body_w,
                    GROUND - top - 4, 3, deep)
    cell.rect(CX - body_w // 2 + (lead if side else 0), top, body_w, 2, line)
    _small_legs(cell, frame, CX, GROUND - 4, deep, spread=3 if side else 4)

    if facing == DOWN:
        cell.ellipse(CX, top - 3, 5, 5, deep)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4, 2, 2, glow)
        # the trail: where they have already been, fading
        for index in range(4):
            cell.dot(CX - 6 + index * 4, GROUND - 1, line if index % 2 else deep)
    elif facing == UP:
        cell.ellipse(CX, top - 3, 5, 5, cooler(deep, 0.3))
        cell.ellipse(CX, top - 4, 4.5, 3, (26, 10, 34))
        # the whole spiral they have walked, drawn on their back
        for index in range(20):
            angle = index * 0.6
            radius = 0.8 + index * 0.28
            cell.dot(CX + int(radius * math.cos(angle)),
                     top + 7 + int(radius * math.sin(angle)), line)
    else:
        cell.ellipse(CX + lead, top - 3, 4, 5, deep)
        cell.rect(CX + lead + (1 if lead > 0 else -2), top - 4, 2, 2, glow)
        # a stride that is always about to be taken back
        cell.line(CX + 3 * lead, GROUND - 2, CX + (3 + step_out) * lead,
                  GROUND - 2, line)


def draw_tooth(cell: Canvas, facing: int, frame: int) -> None:
    """A tooth, upright, walking on its own roots."""
    b = _bob(frame)
    enamel, shade = (255, 236, 220), (168, 40, 62)
    deep = (120, 22, 34)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 7 + b
    crown_w = 9 if side else 15

    cell.round_rect(CX - crown_w // 2 + (lead if side else 0), top, crown_w,
                    15, 4, enamel)
    cell.rect(CX - crown_w // 2 + (lead if side else 0) + 1, top + 1,
              crown_w - 2, 4, (255, 252, 248))
    # the roots, which are also the legs
    root_spread = 3 if side else 5
    swing = (0, 1, 0)[frame]
    for sign in (-1, 1):
        cell.line(CX + sign * 2, top + 14,
                  CX + sign * root_spread + swing * sign, GROUND - 2, shade)
        cell.line(CX + sign * 2 + 1, top + 14,
                  CX + sign * root_spread + 1 + swing * sign, GROUND - 2, deep)

    if facing == DOWN:
        for ex in (CX - 4, CX + 2):
            cell.rect(ex, top + 5, 3, 3, deep)
        cell.hline(top + 11, CX - 4, CX + 4, shade)
        cell.rect(CX - 1, top + 2, 3, 9, (255, 246, 240))
    elif facing == UP:
        # From behind, the crown is in shadow and the roots are the whole
        # story: they splay much wider than the tooth, and there are three of
        # them, which is one more than a tooth seen from the front admits to.
        cell.round_rect(CX - crown_w // 2 + 2, top + 2, crown_w - 4, 13, 4,
                        shade)
        cell.line(CX, top + 2, CX + 1, top + 14, deep)
        cell.line(CX + 1, top + 6, CX + 4, top + 13, deep)
        for sign, spread in ((-1, 7), (0, 0), (1, 7)):
            cell.line(CX + sign * 2, top + 13, CX + sign * spread,
                      GROUND - 2, shade)
            cell.line(CX + sign * 2 + 1, top + 13, CX + sign * spread + 1,
                      GROUND - 2, deep)
        cell.rect(CX - crown_w // 2, top + 12, crown_w, 3, deep)
    else:
        cell.rect(CX + (lead if lead > 0 else -2) + lead, top + 5, 2, 3, deep)
        # in profile a tooth is a wedge, not a block
        for row in range(15):
            cell.rect(CX + lead - 4 + row // 4 * lead, top + row,
                      max(1, 4 - row // 5), 1, shade)


def draw_swallowed(cell: Canvas, facing: int, frame: int) -> None:
    """On their way down.  Facing the wrong way for it."""
    b = _bob(frame)
    line, glow = (250, 90, 96), (255, 190, 176)
    deep = (120, 22, 34)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 13 + b
    pull = (0, 1, 2)[frame]

    # only the top half of them is above the floor
    body_w = 7 if side else 13
    cell.round_rect(CX - body_w // 2 + (lead if side else 0), top + pull,
                    body_w, GROUND - top - pull, 4, deep)
    cell.rect(CX - body_w // 2 + (lead if side else 0), top + pull, body_w, 2,
              line)
    # the floor closing over them, drawn as concentric pull-lines
    for radius in (9, 12):
        cell.ellipse(CX, GROUND - 4, radius, radius * 0.34, line, filled=False)

    if facing == DOWN:
        cell.ellipse(CX, top - 3 + pull, 5, 5, deep)
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, top - 4 + pull, 2, 2, glow)
        # both arms up, which is the only part of this that is not calm
        cell.line(CX - 6, top + 4 + pull, CX - 8, top - 4 + pull, line)
        cell.line(CX + 6, top + 4 + pull, CX + 8, top - 4 + pull, line)
    elif facing == UP:
        cell.ellipse(CX, top - 3 + pull, 5, 5, cooler(deep, 0.3))
        cell.ellipse(CX, top - 4 + pull, 4.5, 3, (30, 8, 12))
        cell.rect(CX - 5, top + 1 + pull, 11, 2, cooler(line, 0.35))
    else:
        cell.ellipse(CX + lead, top - 3 + pull, 4, 5, deep)
        cell.rect(CX + lead + (1 if lead > 0 else -2), top - 4 + pull, 2, 2,
                  glow)
        cell.line(CX + 4 * lead, top + 4 + pull, CX + 7 * lead,
                  top - 3 + pull, line)


def draw_point(cell: Canvas, facing: int, frame: int) -> None:
    """A five-pointed thing with four points.  It does not mention it."""
    b = _bob(frame)
    gold, pale = (252, 210, 84), (255, 252, 236)
    deep = (122, 92, 20)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = 14 + b
    spin = frame * 24

    if facing == UP:
        # From behind, the arms are all pointing away from you: what is left
        # is the back of the hub and the four stubs where the arms leave it,
        # which is a completely different silhouette from the open star.
        cell.blob(CX, cy, 8.0, deep)
        cell.blob(CX, cy - 1, 6.0, gold)
        cell.blob(CX, cy - 2, 3.0, deep)
        for index in (0, 1, 3, 4):
            angle = math.radians(-90 + index * 72 + spin)
            cell.blob(CX + int(7 * math.cos(angle)),
                      cy + int(7 * math.sin(angle)), 2.2, deep)
        cell.rect(CX - 4, GROUND - 4, 9, 3, deep)
        return

    present = (0, 1, 3, 4)
    for index in present:
        angle = math.radians(-90 + index * 72 + spin)
        length = 11 if side else 12
        tx = CX + (lead if side else 0) + int(length * math.cos(angle))
        ty = cy + int(length * math.sin(angle) * (0.7 if side else 1.0))
        cell.line(CX + (lead if side else 0), cy, tx, ty,
                  pale if index == 0 else gold)
        cell.line(CX + (lead if side else 0) + 1, cy, tx + 1, ty, deep)
        cell.blob(tx, ty, 1.8, pale)
    cell.blob(CX + (lead if side else 0), cy, 3.4, gold)

    if facing == DOWN:
        for ex in (CX - 3, CX + 1):
            cell.rect(ex, cy - 1, 2, 2, (28, 24, 8))
        cell.rect(CX - 5, GROUND - 3, 11, 2, deep)
    else:
        cell.rect(CX + lead + (1 if lead > 0 else -2), cy - 1, 2, 2,
                  (28, 24, 8))
        cell.rect(CX - 3, GROUND - 3, 7, 2, deep)


def draw_long_point(cell: Canvas, facing: int, frame: int) -> None:
    """The point that is longer than the others, on its own."""
    b = _bob(frame)
    gold, pale = (252, 210, 84), (255, 252, 236)
    deep = (122, 92, 20)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    top = 4 + b
    lean = (0, 1, 0)[frame]

    if facing == DOWN:
        # a long tapering spike, point toward you, so it is nearly all base
        for row in range(top, GROUND - 2):
            half = max(1, (GROUND - row) // 3)
            cell.rect(CX - half, row, half * 2, 1,
                      pale if row % 4 == 0 else gold)
        cell.rect(CX - 1, top, 3, 6, pale)
        for ex in (CX - 3, CX + 2):
            cell.rect(ex, GROUND - 12, 2, 2, (28, 24, 8))
    elif facing == UP:
        # from behind it is a flat blade with a seam and no face
        cell.rect(CX - 5, top + 4, 11, GROUND - top - 6, deep)
        cell.rect(CX - 3, top + 4, 7, GROUND - top - 6, gold)
        cell.vline(CX, top + 4, GROUND - 3, deep)
        cell.rect(CX - 2, top, 5, 5, deep)
    else:
        # in profile it leans a long way over the direction of travel
        for row in range(top, GROUND - 2):
            progress = (row - top) / (GROUND - top)
            offset = int((1 - progress) * 8) * lead + lean * lead
            half = max(1, int(1 + progress * 3))
            cell.rect(CX + offset - half, row, half * 2, 1,
                      pale if row % 5 == 0 else gold)
        cell.rect(CX + 8 * lead - 1, top, 3, 3, pale)
        cell.rect(CX - 3, GROUND - 3, 7, 2, deep)


NEON_EYE = {"lash": draw_lash, "iris": draw_iris}
NEON_SPIRAL = {"winding": draw_winding, "unplaced": draw_unplaced}
NEON_MOUTH = {"tooth": draw_tooth, "swallowed": draw_swallowed}
NEON_STAR = {"point": draw_point, "long_point": draw_long_point}
