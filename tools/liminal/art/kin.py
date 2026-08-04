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

from .canvas import Canvas, RGB, blend, cooler, warmer
from .charsets import DOWN, GROUND, LEFT, RIGHT, UP, _small_legs

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
