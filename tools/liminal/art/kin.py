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
