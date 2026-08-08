"""The world behind the television.

A cartoon hillside from a 1991 console platformer, still running long after
whatever was supposed to happen there happened.

Two rules decide every drawing in this file, and both come from the rest of
the game rather than from the source material:

**It is seen from above.**  The thing being referenced is a side-scroller and
this is not one.  Ground is walked on; the checkerboard soil is the *cliff
face* under a grass edge, not a floor; and everything that stands up goes
through ``solid`` — lit top, mid front, shaded right column, two pixels of
dithered seam between them, light from the upper left.  A palm in profile
would be a sticker of a palm.  A palm from a raised three-quarter is a tree
you are walking underneath.

**Five values, structured texture, no noise.**  Every surface is a
``Material``, which is one base colour hue-shifted into deep/shade/mid/lit/hot
— warmer as it brightens, cooler as it darkens, so a red hill and a green hill
are lit by the same sun.  Texture is planes, seams, courses and clumps.  The
only dithering in the game is ``mt.seam``, two pixels wide, where one face
meets another.  Nothing is outlined and nothing is scattered.

The four regions are the same tileset under four ``Look``s, which is the
broadcast world's trick spent again: the geometry never changes, so arriving
in THE RED is arriving somewhere you have already walked.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import material as mt
from .canvas import Canvas, blend
from .chipsets import TILE, _canvas
from .grove import foot, post, solid


@dataclass(frozen=True)
class Look:
    """One region, as a set of substances."""
    grass: mt.Material
    soil: mt.Material           # the lit square of the checker
    soil_alt: mt.Material       # the dark square
    rock: mt.Material
    water: mt.Material
    bark: mt.Material
    leaf: mt.Material
    metal: mt.Material
    bone: mt.Material
    gold: mt.Material
    wrong: float = 0.0          # 0 fine, 1 entirely gone


def _m(name: str, rgb: tuple[int, int, int]) -> mt.Material:
    return mt.Material(name, rgb)


HILLS = Look(
    grass=_m("grass", (92, 184, 76)),
    soil=_m("soil", (198, 142, 78)),
    soil_alt=_m("soil_alt", (162, 102, 52)),
    rock=_m("rock", (132, 136, 144)),
    water=_m("water", (76, 152, 220)),
    bark=_m("bark", (158, 110, 64)),
    leaf=_m("leaf", (56, 146, 64)),
    metal=_m("metal", (152, 158, 170)),
    bone=_m("bone", (228, 216, 200)),
    gold=_m("gold", (248, 200, 56)),
)

DROWN = replace(
    HILLS,
    grass=_m("grass", (44, 130, 116)),
    soil=_m("soil", (112, 112, 132)),
    soil_alt=_m("soil_alt", (82, 82, 104)),
    rock=_m("rock", (98, 104, 124)),
    water=_m("water", (38, 98, 172)),
    bark=_m("bark", (96, 92, 104)),
    leaf=_m("leaf", (34, 110, 106)),
    wrong=0.25,
)

SCRAP = replace(
    HILLS,
    grass=_m("grass", (98, 106, 94)),
    soil=_m("soil", (124, 114, 106)),
    soil_alt=_m("soil_alt", (90, 82, 78)),
    rock=_m("rock", (110, 106, 110)),
    water=_m("water", (132, 150, 92)),      # not water any more
    bark=_m("bark", (112, 98, 84)),
    leaf=_m("leaf", (94, 106, 84)),
    metal=_m("metal", (180, 182, 190)),
    gold=_m("gold", (188, 168, 96)),
    wrong=0.45,
)

RED = replace(
    HILLS,
    grass=_m("grass", (104, 24, 24)),
    soil=_m("soil", (86, 20, 20)),
    soil_alt=_m("soil_alt", (50, 12, 14)),
    rock=_m("rock", (62, 28, 30)),
    water=_m("water", (136, 22, 20)),
    bark=_m("bark", (76, 26, 24)),
    leaf=_m("leaf", (52, 88, 36)),          # the only green left
    metal=_m("metal", (100, 64, 64)),
    bone=_m("bone", (232, 222, 210)),
    gold=_m("gold", (204, 44, 38)),
    wrong=1.0,
)

LOOKS = {"hills": HILLS, "drown": DROWN, "scrap": SCRAP, "red": RED}


# --- ground: seen from above, walked on ---------------------------------------

def turf(look: Look, variant: int = 0) -> Canvas:
    """Grass in clumps on a shifting grid.

    Grass has direction; grit does not.  Each clump is three pixels of shade
    with a lit tip, and the grid offset moves per row so no period shows at
    this size.
    """
    g = look.grass
    art = Canvas(TILE, TILE, g.mid)
    mt.plane(art, 0, 0, TILE, TILE, g.mid)
    for row in range(0, TILE, 4):
        offset = (row // 4 + variant * 2) % 3
        for x in range(offset, TILE, 3):
            top = (row + (x % 2)) % TILE
            art.vline(x, top, min(TILE - 1, top + 2), g.shade)
            art.dot(x, top, g.lit)
            if (x + row + variant) % 7 == 0:
                art.dot(x, min(TILE - 1, top + 3), g.deep)
            if (x * 3 + row) % 13 == 0:
                art.dot(x, top, g.hot)
    return art


def track(look: Look) -> Canvas:
    """Where the grass has been walked off and the soil shows."""
    s, g = look.soil, look.grass
    art = Canvas(TILE, TILE, s.mid)
    mt.plane(art, 0, 0, TILE, TILE, s.mid)
    mt.seam(art, 0, 0, TILE, TILE, s.mid, s.shade)
    for x in range(0, TILE, 5):
        art.dot(x, (x * 3) % TILE, s.lit)
        art.dot((x + 3) % TILE, (x * 5 + 4) % TILE, s.deep)
    for x in range(1, TILE, 7):
        art.vline(x, (x * 2) % TILE, min(TILE - 1, (x * 2) % TILE + 1), g.shade)
    return art


def checker(look: Look, phase: int = 0) -> Canvas:
    """The checkerboard, which is a wall.

    In the source it is exposed dirt under a grass edge, face-on, and it is
    the most recognisable texture the genre has.  Two squares to a tile, each
    lit along top and left, dropped along the bottom, seamed into the next —
    so a run of them reads as a face standing up rather than as a chessboard
    lying flat.
    """
    a, b = look.soil, look.soil_alt
    art = Canvas(TILE, TILE, a.mid)
    half = TILE // 2
    for row in range(2):
        for col in range(2):
            mat = b if (row + col + phase) % 2 else a
            x, y = col * half, row * half
            mt.plane(art, x, y, half, half, mat.mid)
            art.hline(y, x, x + half - 1, mat.lit)
            art.vline(x, y, y + half - 1, blend(mat.lit, mat.mid, 0.45))
            art.vline(x + half - 1, y, y + half - 1, mat.shade)
            mt.seam(art, x, y + half - 3, half, 2, mat.mid, mat.deep)
            art.hline(y + half - 1, x, x + half - 1, mat.deep)
    return art


def brow(look: Look) -> Canvas:
    """The lip of a cliff: grass from above, overhanging the drop.

    The grass sits proud of the dirt with a soft edge, which is the whole
    reason these hills read as rounded instead of as a tilemap.
    """
    art = checker(look)
    g = look.grass
    for x in range(TILE):
        drop = 7 + (1 if (x // 2) % 3 == 0 else 0)
        mt.plane(art, x, 0, 1, drop, g.mid)
        art.dot(x, drop - 1, g.shade)
        art.dot(x, drop, g.deep)
        if x % 3 == 0:
            art.dot(x, max(0, drop - 4), g.lit)
        if x % 5 == 0:
            art.dot(x, max(0, drop - 5), g.hot)
    mt.seam(art, 0, 4, TILE, 2, g.mid, g.shade)
    art.hline(0, 0, TILE - 1, g.lit)
    return art


def stone(look: Look, seed: int = 0) -> Canvas:
    """Bare rock: unequal chunks on no grid, lit along their upper edges."""
    r = look.rock
    art = Canvas(TILE, TILE, r.deep)
    mt.plane(art, 0, 0, TILE, TILE, r.deep)
    lump = ((0, 0, 7, 6), (7, 1, 9, 5), (2, 6, 6, 5), (9, 7, 7, 6),
            (0, 11, 5, 5), (5, 12, 5, 4))
    for index, (x, y, w, h) in enumerate(lump):
        x = (x + seed * 3) % TILE
        mt.plane(art, x, y, w, h, r.mid)
        art.hline(y, x, min(TILE - 1, x + w - 1), r.lit)
        art.vline(min(TILE - 1, x + w - 1), y, y + h - 1, r.shade)
        art.hline(y + h - 1, x, min(TILE - 1, x + w - 1), r.deep)
    return art


def plate(look: Look) -> Canvas:
    """Riveted floor, for the region that stopped being a hillside."""
    m = look.metal
    art = Canvas(TILE, TILE, m.mid)
    mt.plane(art, 0, 0, TILE, TILE, m.mid)
    mt.tiles(art, 0, 0, TILE, TILE, m, size=8)
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        art.dot(x, y, m.lit)
        art.dot(x, y + 1, m.deep)
    return art


# --- water, which moves -------------------------------------------------------

def water(look: Look, frame: int = 0, *, deep: bool = False) -> Canvas:
    """Surface water from above.

    RPG Maker cycles exactly three frames, so the motion must read across
    three drawings and return with no jump.  The bands advance a third of
    their period per frame, which is the only arrangement that loops clean.
    """
    w = look.water
    base = w.deep if deep else w.mid
    art = Canvas(TILE, TILE, base)
    mt.plane(art, 0, 0, TILE, TILE, base)
    period, shift = 6, (frame * 2) % 6
    for y in range(TILE):
        band = (y + shift) % period
        if band == 0:
            art.hline(y, 0, TILE - 1, blend(base, w.lit, 0.34))
            mt.seam(art, 0, y, TILE, 1, blend(base, w.lit, 0.34), base)
        elif band == 3:
            art.hline(y, 0, TILE - 1, blend(base, w.deep, 0.42))
    for index in range(3):
        cx = (index * 6 + frame * 5) % TILE
        cy = (index * 5 + 2) % TILE
        art.dot(cx, cy, w.hot if not deep else w.lit)
        art.dot((cx + 1) % TILE, (cy + 1) % TILE, w.lit)
        art.dot((cx - 1) % TILE, (cy + 1) % TILE, w.lit)
    return art


def shore(look: Look, frame: int = 0) -> Canvas:
    """Where water meets bank: foam that breaks and reforms on the loop."""
    w = look.water
    art = water(look, frame)
    foam = (238, 246, 252) if look.wrong < 0.9 else (234, 208, 208)
    for x in range(TILE):
        lift = 3 + ((x + frame * 3) % 5) // 2
        mt.plane(art, x, 0, 1, lift + 1,
                 foam if (x + frame) % 4 else blend(foam, w.mid, 0.35))
        art.dot(x, lift + 1, blend(foam, w.mid, 0.55))
    mt.seam(art, 0, 4, TILE, 2, foam, w.mid)
    art.hline(0, 0, TILE - 1, foam)
    return art


def spill(look: Look, frame: int = 0) -> Canvas:
    """Water running down a cliff face.  Drawn on the checker, not on grass."""
    w = look.water
    art = checker(look)
    for x in range(2, TILE - 2):
        run = (x * 5 + frame * 5) % 15
        for y in range(TILE):
            phase = (y + run) % 15
            if phase < 5:
                art.dot(x, y, w.lit if x % 3 else w.hot)
            elif phase < 9:
                art.dot(x, y, w.mid)
            elif phase < 11:
                art.dot(x, y, blend(w.deep, look.soil.mid, 0.45))
    art.vline(1, 0, TILE - 1, w.deep)
    art.vline(TILE - 2, 0, TILE - 1, w.deep)
    return art


# --- things that grow ---------------------------------------------------------

def flower(look: Look, frame: int = 0) -> Canvas:
    """A rosette from above.  Three frames, and the turn is in the *light*.

    Removing a petal to suggest rotation reads as a broken flower.  Moving
    where the highlight sits reads as a head turning under the sun, which is
    what it is.
    """
    art = _canvas(1, 1)
    l = look.leaf
    petal = _m("petal", (250, 224, 84) if look.wrong < 0.6 else (196, 188, 174))
    heart = (228, 128, 56) if look.wrong < 0.6 else (98, 16, 16)
    cx = cy = 8
    art.blob(cx, cy + 3, 4.4, blend(l.deep, (0, 0, 0), 0.3))
    ring_pts = ((0, -5), (4, -4), (5, 0), (4, 4), (0, 5), (-4, 4),
                (-5, 0), (-4, -4))
    for index, (dx, dy) in enumerate(ring_pts):
        near = (index - frame * 3) % 8 in (7, 0, 1)
        art.blob(cx + dx * 0.86, cy + dy * 0.86, 2.3,
                 petal.lit if near else petal.mid)
        art.dot(int(cx + dx), int(cy + dy), petal.hot if near else petal.shade)
    art.blob(cx, cy, 2.5, heart)
    art.dot(cx - 1, cy - 1, blend(heart, (255, 255, 255), 0.45))
    return art


def palm(look: Look, cols: int = 3, rows: int = 4) -> Canvas:
    """A palm from a raised three-quarter.

    The crown is a rosette seen slightly from the side, so the near fronds
    hang down over the trunk and the far ones are foreshortened; they are
    drawn far-first so the near ones overlap them.  A frond is a mass — wide
    where it leaves the crown, falling under its own weight, tapering to a
    point — because at sixteen pixels a line is a scratch.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    b, l = look.bark, look.leaf
    crown_y, trunk_w = int(h * 0.30), 7
    trunk_x = (w - trunk_w) // 2

    for y in range(crown_y, h - 3):
        drift = int((y - crown_y) / max(1, h - crown_y) * 2)
        x = trunk_x + drift
        mt.plane(art, x, y, trunk_w, 1, b.mid)
        art.dot(x, y, b.lit)
        art.dot(x + trunk_w - 2, y, b.shade)
        art.dot(x + trunk_w - 1, y, b.deep)
        if (y + drift) % 5 == 0:
            art.hline(y, x + 1, x + trunk_w - 2, b.deep)
            art.hline(y - 1, x + 1, x + trunk_w - 3, b.shade)
    foot(art, trunk_x - 2, h - 3, trunk_w + 5, b)

    cx, cy = trunk_x + trunk_w // 2, crown_y
    fronds = ((0.00, -1.00, 11, False), (-0.85, -0.62, 13, False),
              (0.85, -0.62, 13, False), (-1.00, 0.10, 15, True),
              (1.00, 0.10, 15, True), (-0.62, 0.78, 14, True),
              (0.62, 0.78, 14, True))
    for index, (dx, dy, run, near) in enumerate(fronds):
        px, py = float(cx), float(cy)
        body = l.mid if near else l.shade
        edge = l.shade if near else l.deep
        for step in range(run):
            f = step / run
            px += dx * 1.7
            py += dy * 1.25 + f * f * 2.4
            thick = max(0, int(round(4.6 * (1.0 - f * 0.85))))
            y = int(py)
            if not (0 <= y < h):
                continue
            art.hline(y, int(px) - thick, int(px) + thick, body)
            art.dot(int(px) - thick, y, edge)
            art.dot(int(px) + thick, y, edge)
            if step % 3 == 0 and thick > 1:
                art.dot(int(px), y, l.lit if near else l.mid)
            if 0 < step < run - 2:
                art.dot(int(px) - thick - 1, y + 1, edge)
                art.dot(int(px) + thick + 1, y + 1, edge)
    art.blob(cx, cy, 4.2, l.shade)
    art.blob(cx - 1, cy - 1, 2.6, l.lit)
    art.dot(cx - 1, cy - 2, l.hot)

    nut = blend(b.deep, (0, 0, 0), 0.18)
    for nx, ny in ((-5, 5), (3, 6), (-1, 8)):
        art.blob(cx + nx, cy + ny, 2.4, nut)
        art.dot(cx + nx - 1, cy + ny - 1, b.shade)
    return art


def bush(look: Look, cols: int = 2, rows: int = 2) -> Canvas:
    """Hedging: overlapping lobes, lit crown, dark underside, no outline."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    l = look.leaf
    for cx, cy, r in ((w * 0.32, h * 0.62, 9), (w * 0.68, h * 0.58, 10),
                      (w * 0.50, h * 0.42, 10)):
        art.ellipse(cx, cy + 3, r, r * 0.78, l.deep)
        art.blob(cx, cy, r, l.shade)
        art.blob(cx - 1, cy - 2, r - 2, l.mid)
        art.blob(cx - 2, cy - 3, r - 5, l.lit)
        art.dot(int(cx - 3), int(cy - 5), l.hot)
    foot(art, int(w * 0.16), h - 3, int(w * 0.68), l)
    return art


# --- what the format leaves standing ------------------------------------------

def totem(look: Look, cols: int = 2, rows: int = 4) -> Canvas:
    """A carved post: a standing box with faces cut into its front.

    On ``solid``, so it belongs to the same world as a grove phone box.  The
    arms jutting from the crown are what stop it reading as a cupboard, and
    the middle face is the one that is smiling.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    b = look.bark
    top = TILE - 6

    mt.plane(art, 1, top + 3, w - 2, 5, b.shade)
    art.hline(top + 3, 1, w - 2, b.mid)
    art.hline(top + 7, 1, w - 2, b.deep)
    solid(art, 4, top, w - 8, h - top - 3, b, top=5, cap=b)

    fx, fw = 6, w - 12
    for index, fy in enumerate((top + 9, top + 27, top + 45)):
        if fy + 15 > h - 4:
            break
        mt.plane(art, fx, fy, fw, 15, b.shade)
        art.hline(fy, fx, fx + fw - 1, b.deep)
        mt.seam(art, fx, fy + 13, fw, 2, b.shade, b.mid)
        socket = blend(b.deep, (0, 0, 0), 0.55)
        for ex in (fx + 1, fx + fw - 4):
            mt.plane(art, ex, fy + 3, 3, 4, socket)
            art.dot(ex + 1, fy + 4, (226, 60, 48) if index == 1 else (0, 0, 0))
        if index == 1:
            art.hline(fy + 10, fx + 2, fx + fw - 3, b.deep)
            for tx in range(fx + 2, fx + fw - 2, 2):
                art.dot(tx, fy + 10, (232, 226, 214))
        else:
            art.hline(fy + 10, fx + 3, fx + fw - 4, b.deep)
    foot(art, 3, h - 3, w - 6, b)
    return art


def ring(look: Look, frame: int = 0) -> Canvas:
    """The ring, spinning.  Face, edge, face.

    The one object here whose rules the player already knows, which is
    exactly why it is the one that gets to lie to them.
    """
    art = _canvas(1, 1)
    g = look.gold
    rx = (6.0, 1.8, 5.0)[frame % 3]
    art.ellipse(8, 9, rx + 0.7, 6.4, g.deep)
    art.ellipse(8, 8, rx, 6.0, g.mid)
    art.ellipse(8, 7.4, rx * 0.9, 4.6, g.lit)
    if rx > 2.5:
        art.ellipse(8, 8, rx - 2.2, 3.4, (255, 0, 255))
    art.dot(int(8 - rx + 1), 5, g.hot)
    return art


def monitor(look: Look, cols: int = 2, rows: int = 2,
            frame: int = 0) -> Canvas:
    """The box that holds a power-up, showing the wrong thing."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    solid(art, 2, 2, w - 4, h - 7, m, top=4, cap=m)
    mt.plane(art, 5, 8, w - 10, h - 17, (18, 16, 20))
    if frame == 0:
        art.blob(w / 2, h / 2 - 1, 3.4, look.bone.lit)
        art.dot(int(w / 2), int(h / 2 - 1), (0, 0, 0))
    elif frame == 1:
        for y in range(8, h - 9, 2):
            art.hline(y, 5, w - 6, (88, 86, 92))
    else:
        mt.plane(art, 5, 8, w - 10, h - 17, (152, 16, 16))
        art.hline(int(h / 2 - 1), 5, w - 6, (240, 236, 230))
    post(art, w // 2 - 2, h - 6, 4, m, width=4)
    foot(art, w // 2 - 4, h - 3, 8, m)
    return art


def sign(look: Look, cols: int = 2, rows: int = 3) -> Canvas:
    """The end-of-act post, still turning, nothing left on the plate."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    post(art, w // 2 - 2, 22, h - 25, m, width=4)
    face = blend((236, 232, 226), (0, 0, 0), look.wrong * 0.72)
    solid(art, 2, 4, w - 4, 19, m, top=4, cap=m)
    mt.plane(art, 4, 8, w - 8, 12, face)
    mt.seam(art, 4, 18, w - 8, 2, face, blend(face, (0, 0, 0), 0.3))
    if look.wrong >= 0.75:
        for y in range(9, 20, 2):
            art.hline(y, 4, w - 5, (158, 18, 18))
        art.dot(w // 2 - 3, 12, (0, 0, 0))
        art.dot(w // 2 + 2, 12, (0, 0, 0))
    else:
        art.blob(w / 2, 13, 4, (58, 108, 196))
        art.blob(w / 2 - 1, 12, 2, (240, 240, 244))
    foot(art, w // 2 - 5, h - 3, 10, m)
    return art


def gate(look: Look, cols: int = 4, rows: int = 3) -> Canvas:
    """A ring-shaped arch you can walk under.

    What survives of a loop once the camera is above the world instead of
    beside it: the shape holds, the purpose does not.  Nothing happens when
    you walk through it, and that is the whole line.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    cx, cy = w / 2, h * 0.52
    rx, ry = w * 0.42, h * 0.44
    for band, shade in ((0, m.deep), (2, m.mid), (4, m.lit)):
        art.ellipse(cx, cy, rx - band, ry - band, shade)
    art.ellipse(cx, cy - 1, rx - 5, ry - 5, (255, 0, 255))
    for side in (-1, 1):
        px = int(cx + side * rx) - (3 if side > 0 else 0)
        mt.plane(art, px, int(cy), 3, int(h - cy - 3), m.mid)
        art.vline(px, int(cy), h - 4, m.lit if side < 0 else m.shade)
    foot(art, int(cx - rx), h - 3, int(rx * 2), m)
    return art


def spikes(look: Look, cols: int = 2, rows: int = 2) -> Canvas:
    """A plate with points coming up out of it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    solid(art, 2, h // 2 - 2, w - 4, h // 2, m, top=4, cap=m)
    for cx in range(7, w - 4, 9):
        for step in range(7):
            half = max(0, 4 - step // 2)
            y = h // 2 - 4 - step
            art.hline(y, cx - half, cx + half, m.lit if step % 2 else m.mid)
            art.dot(cx - half, y, m.shade)
        art.dot(cx, h // 2 - 12, m.hot)
    foot(art, 1, h - 3, w - 2, m)
    return art


# --- what is left of the animals ----------------------------------------------

def bones(look: Look, cols: int = 1, rows: int = 1) -> Canvas:
    """Something bird-sized: skull, beak, ribs, one wing still open."""
    art = _canvas(cols, rows)
    f = look.bone
    art.blob(5, 6, 3, f.lit)
    art.blob(5, 6, 2, f.mid)
    art.dot(4, 5, (0, 0, 0))
    art.dot(6, 5, (0, 0, 0))
    art.hline(8, 7, 9, (206, 176, 96))
    art.dot(9, 9, (206, 176, 96))
    for index, y in enumerate(range(9, 14)):
        run = 4 - abs(index - 2)
        art.hline(y, 8 - run, 8 + run, f.mid if index % 2 else f.lit)
    art.vline(8, 9, 13, f.shade)
    art.line(11, 13, 14, 11, f.lit)
    return art


def cairn(look: Look, cols: int = 2, rows: int = 2) -> Canvas:
    """A stack somebody made, with something on top.

    Three circles of decreasing size is a snowman.  Stones are flat and
    unequal and sit on each other badly; the skull is what turns a pile into
    a marker.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    r, f = look.rock, look.bone
    art.ellipse(w / 2, h - 3, w * 0.38, 3, blend(r.deep, (0, 0, 0), 0.45))
    for index, (x, y, sw, sh) in enumerate(((3, h - 10, w - 6, 7),
                                            (5, h - 16, w - 11, 6),
                                            (7, h - 21, w - 15, 5))):
        ox = x + (index % 2)
        mt.plane(art, ox, y, sw, sh, r.mid)
        art.hline(y, ox, ox + sw - 1, r.lit)
        art.vline(ox, y, y + sh - 1, blend(r.lit, r.mid, 0.5))
        art.vline(ox + sw - 1, y, y + sh - 1, r.shade)
        art.hline(y + sh - 1, ox, ox + sw - 1, r.deep)
    top = h - 24
    art.blob(w / 2, top, 3.6, f.lit)
    art.blob(w / 2, top, 2.6, f.mid)
    art.dot(int(w / 2) - 1, top - 1, (0, 0, 0))
    art.dot(int(w / 2) + 1, top - 1, (0, 0, 0))
    art.hline(top + 2, int(w / 2) - 2, int(w / 2) + 2, f.shade)
    return art
