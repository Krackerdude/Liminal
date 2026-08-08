"""What lives on the island.

Original animals, not borrowed ones.  The world they are in is a homage and
they are drawn to fit it — small, round, two-tone, built out of masses rather
than lines — but nothing here is a traced sprite, and none of them is anybody
else's character.  The lineage they belong to is the game's own: the same
``_mass`` and ``_round`` that light every resident of the grove, the same rule
that a mass takes the light and a detail stays flat.

Four facings each, drawn separately, because a back view that is a front view
with the eyes moved does not turn around.

They come in three kinds:

**the small ones**   birds and beach animals.  Nothing is wrong with them and
                     nothing ever happens to them, which is the point: they
                     are what the island is supposed to be full of.
**the wrong ones**   the same animals with something taken out or added.  They
                     only appear in the regions that have gone.
**him**              one design, and everything about it is a lie about scale:
                     it is drawn to the same twenty-four pixels as a bird.
"""

from __future__ import annotations

from . import material as _mt
from .canvas import Canvas, RGB, blend, cooler, warmer
from .charsets import DOWN, GROUND, LEFT, RIGHT, UP, _small_legs
from .kin import CX, _bob, _mass, _round


# --- the small ones -----------------------------------------------------------

def _wing(cell: Canvas, x: int, y: int, colour: RGB, lead: int,
          frame: int) -> None:
    """A folded wing, opening a little on the middle frame."""
    spread = 1 if frame == 1 else 0
    _mass(cell, x, y, 4 + spread, 6 + spread, colour, top=2)


def draw_bluebird(cell: Canvas, facing: int, frame: int) -> None:
    """A round blue bird that never stops hopping.

    The friendliest thing in the world and the only one drawn entirely in
    primary colour.  Everything else on the island is a variation on it.
    """
    b = _bob(frame)
    body, wing = (78, 140, 226), (52, 104, 190)
    beak, ink = (246, 190, 72), (28, 26, 38)
    top = 10 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 6, 7, 6.5, body)
    if side:
        _wing(cell, CX - 2, top + 3, wing, lead, frame)
        _round(cell, CX + lead * 4, top - 1, 4.5, 4.5, body)
        cell.rect(CX + lead * 8, top - 1, 3, 2, beak)
        cell.rect(CX + lead * 5, top - 2, 2, 2, ink)
        cell.rect(CX - lead * 7, top + 5, 4, 3, wing)      # tail
    elif facing == DOWN:
        _round(cell, CX, top - 1, 5, 4.5, body)
        cell.rect(CX - 3, top - 2, 2, 2, ink)
        cell.rect(CX + 2, top - 2, 2, 2, ink)
        cell.rect(CX - 1, top + 1, 3, 2, beak)
        _wing(cell, CX - 8, top + 3, wing, -1, frame)
        _wing(cell, CX + 4, top + 3, wing, 1, frame)
    else:
        _round(cell, CX, top - 1, 5, 4.5, wing)
        cell.rect(CX - 2, top + 4, 5, 5, wing)             # tail, straight up
        _wing(cell, CX - 8, top + 3, wing, -1, frame)
        _wing(cell, CX + 4, top + 3, wing, 1, frame)
    _small_legs(cell, frame, CX, GROUND - 3, beak, spread=3)


def draw_finch(cell: Canvas, facing: int, frame: int) -> None:
    """Smaller, pink, and always facing slightly the wrong way."""
    b = _bob(frame)
    body, wing = (238, 156, 186), (206, 112, 150)
    beak, ink = (250, 214, 120), (34, 28, 34)
    top = 12 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 5, 5.5, 5, body)
    if side:
        _round(cell, CX + lead * 3, top, 3.5, 3.5, body)
        cell.rect(CX + lead * 6, top, 3, 2, beak)
        cell.rect(CX + lead * 4, top - 1, 2, 2, ink)
        cell.rect(CX - lead * 6, top + 4, 4, 2, wing)
    elif facing == DOWN:
        _round(cell, CX, top, 4, 3.5, body)
        cell.rect(CX - 3, top - 1, 2, 2, ink)
        cell.rect(CX + 2, top - 1, 2, 2, ink)
        cell.rect(CX - 1, top + 2, 2, 2, beak)
    else:
        _round(cell, CX, top, 4, 3.5, wing)
        cell.rect(CX - 1, top + 4, 3, 4, wing)
    _wing(cell, CX - 7, top + 2, wing, -1, frame)
    _wing(cell, CX + 3, top + 2, wing, 1, frame)
    _small_legs(cell, frame, CX, GROUND - 3, beak, spread=2)


def draw_hoglet(cell: Canvas, facing: int, frame: int) -> None:
    """A small spined animal.  Nothing to do with anybody: it is a hedgehog.

    Which is the joke, and it is never said out loud: the island is full of
    ordinary animals and one of them happens to be this.
    """
    b = _bob(frame)
    coat, spine = (150, 126, 108), (92, 74, 66)
    snout, ink = (206, 178, 158), (30, 26, 30)
    top = 12 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 5, 8, 5.5, coat)
    for index in range(6):                              # the spines
        sx = CX - 7 + index * 3
        cell.vline(sx, top - 1, top + 3, spine)
        cell.dot(sx, top - 2, blend(spine, (255, 255, 255), 0.3))
    if side:
        _round(cell, CX + lead * 6, top + 6, 3.5, 3, snout)
        cell.rect(CX + lead * 8, top + 5, 2, 2, ink)
        cell.rect(CX + lead * 5, top + 5, 2, 2, ink)
    elif facing == DOWN:
        _round(cell, CX, top + 8, 4, 3, snout)
        cell.rect(CX - 3, top + 7, 2, 2, ink)
        cell.rect(CX + 2, top + 7, 2, 2, ink)
        cell.rect(CX - 1, top + 10, 2, 1, ink)
    else:
        _round(cell, CX, top + 4, 7, 4, spine)
    _small_legs(cell, frame, CX, GROUND - 3, spine, spread=4)


def draw_shellback(cell: Canvas, facing: int, frame: int) -> None:
    """A beach animal carrying something that is not its own shell."""
    b = _bob(frame)
    shell, body = (198, 152, 96), (222, 190, 160)
    ink = (36, 30, 32)
    top = 12 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 4, 8, 6, shell)
    cell.ellipse(CX, top + 4, 5, 3.5, warmer(shell, 0.2))
    cell.ellipse(CX, top + 4, 2.5, 1.6, cooler(shell, 0.25))
    if side:
        _round(cell, CX + lead * 7, top + 7, 3, 2.5, body)
        cell.rect(CX + lead * 8, top + 6, 2, 2, ink)
    elif facing == DOWN:
        _round(cell, CX, top + 9, 3.5, 2.5, body)
        cell.rect(CX - 3, top + 8, 2, 2, ink)
        cell.rect(CX + 2, top + 8, 2, 2, ink)
    for cx in (CX - 9, CX + 7):                          # claws
        cell.rect(cx, top + 6 + (1 if frame == 1 else 0), 3, 3, body)
    _small_legs(cell, frame, CX, GROUND - 3, shell, spread=5)


# --- the wrong ones -----------------------------------------------------------

def draw_smiler(cell: Canvas, facing: int, frame: int) -> None:
    """A bluebird with a mouth it should not have.

    Same body, same colour, same hop.  The only difference is on the face,
    and only when it is looking at you -- from behind it is a bluebird.
    """
    b = _bob(frame)
    body, wing = (78, 140, 226), (52, 104, 190)
    beak, ink = (246, 190, 72), (18, 16, 24)
    teeth = (240, 236, 226)
    top = 10 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 6, 7, 6.5, body)
    _wing(cell, CX - 8, top + 3, wing, -1, frame)
    _wing(cell, CX + 4, top + 3, wing, 1, frame)
    if side:
        _round(cell, CX + lead * 4, top - 1, 4.5, 4.5, body)
        cell.rect(CX + lead * 5, top - 2, 2, 2, ink)
        for step in range(4):                            # the grin, in profile
            cell.dot(CX + lead * (5 + step), top + 2, teeth)
    elif facing == DOWN:
        _round(cell, CX, top - 1, 5, 4.5, body)
        cell.rect(CX - 3, top - 2, 2, 2, ink)
        cell.rect(CX + 2, top - 2, 2, 2, ink)
        cell.dot(CX - 3, top - 2, (198, 40, 36))
        cell.dot(CX + 3, top - 2, (198, 40, 36))
        cell.rect(CX - 4, top + 1, 9, 3, ink)            # far too wide
        for tx in range(CX - 3, CX + 4, 2):
            cell.vline(tx, top + 1, top + 3, teeth)
    else:
        _round(cell, CX, top - 1, 5, 4.5, wing)
        cell.rect(CX - 2, top + 4, 5, 5, wing)
    _small_legs(cell, frame, CX, GROUND - 3, beak, spread=3)


def draw_hollow(cell: Canvas, facing: int, frame: int) -> None:
    """An animal-shaped absence: the silhouette of a bird and nothing in it."""
    b = _bob(frame)
    void = (10, 8, 12)
    edge = (58, 20, 22)
    top = 10 + b
    cell.ellipse(CX, top + 6, 7, 6.5, edge)
    cell.ellipse(CX, top + 6, 6.2, 5.7, void)
    cell.ellipse(CX, top - 1, 5, 4.5, edge)
    cell.ellipse(CX, top - 1, 4.3, 3.8, void)
    if facing == DOWN:
        cell.rect(CX - 3, top - 2, 2, 2, (198, 40, 36))
        cell.rect(CX + 2, top - 2, 2, 2, (198, 40, 36))
    for wx in (CX - 8, CX + 5):
        cell.rect(wx, top + 3, 3, 6, void)
    _small_legs(cell, frame, CX, GROUND - 3, edge, spread=3)


def draw_watcher(cell: Canvas, facing: int, frame: int) -> None:
    """A finch that has stopped doing anything except look.

    It does not hop.  ``_bob`` is not called, which at this size is the most
    unsettling thing a sprite can do in a world where everything else does.
    """
    body, wing = (188, 128, 148), (140, 90, 112)
    ink, iris = (12, 10, 14), (206, 44, 40)
    top = 12
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    _round(cell, CX, top + 5, 5.5, 5, body)
    _wing(cell, CX - 7, top + 2, wing, -1, 0)
    _wing(cell, CX + 3, top + 2, wing, 1, 0)
    _round(cell, CX, top, 4, 3.5, body)
    if side:
        cell.rect(CX + lead * 3, top - 1, 3, 3, ink)
        cell.dot(CX + lead * 4, top, iris)
    elif facing == DOWN:
        cell.rect(CX - 4, top - 1, 3, 3, ink)
        cell.rect(CX + 2, top - 1, 3, 3, ink)
        cell.dot(CX - 3, top, iris)
        cell.dot(CX + 3, top, iris)
    else:
        cell.rect(CX - 1, top + 3, 3, 4, wing)
    _small_legs(cell, frame, CX, GROUND - 3, wing, spread=2)


# --- him ----------------------------------------------------------------------

def draw_him(cell: Canvas, facing: int, frame: int) -> None:
    """The thing the world is about.

    Drawn to exactly the same twenty-four pixels as a bird, which is the only
    honest way to do it: the horror is not that it is large, it is that it is
    standing in a field at the same scale as everything else and none of the
    animals will go near it.

    Black body, no highlight anywhere on it -- it is the one figure in the
    game that the light does not touch -- and two red points.  From behind it
    is a silhouette with nothing to read, so a player who sees it turn away
    loses it against the trees.
    """
    dark, darker = (24, 22, 42), (10, 8, 18)
    red, white = (216, 32, 28), (236, 232, 226)
    top = 4
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    # spines off the back of the head, which is the whole silhouette
    for index, (sx, sy, sw, sh) in enumerate(((-11, 4, 7, 4), (-12, 8, 8, 4),
                                              (-10, 12, 7, 4))):
        cell.rect(CX + (sx if lead > 0 else -sx - sw), top + sy, sw, sh,
                  darker if index % 2 else dark)

    cell.ellipse(CX, top + 8, 8.5, 8, dark)
    cell.ellipse(CX - 2, top + 6, 5, 4, darker)
    cell.rect(CX - 6, top + 17, 12, 9, dark)             # body
    cell.rect(CX - 7, top + 24, 14, 3, darker)

    if facing == UP:
        return                                            # nothing to read

    if side:
        cell.rect(CX + lead * 3, top + 7, 3, 3, red)
        cell.dot(CX + lead * 4, top + 8, white)
        for step in range(5):                             # the grin
            cell.dot(CX + lead * (2 + step), top + 13,
                     white if step % 2 else darker)
    else:
        cell.rect(CX - 5, top + 6, 4, 4, red)
        cell.rect(CX + 2, top + 6, 4, 4, red)
        cell.dot(CX - 4, top + 7, white)
        cell.dot(CX + 3, top + 7, white)
        cell.rect(CX - 6, top + 12, 13, 4, darker)
        for tx in range(CX - 5, CX + 6, 2):
            cell.vline(tx, top + 12, top + 15, white)
    cell.rect(CX - 8, top + 20, 3, 4, white)              # the gloves
    cell.rect(CX + 6, top + 20, 3, 4, white)
