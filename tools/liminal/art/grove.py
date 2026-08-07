"""The grove's own art, in the material system the room established.

A city the forest grew through, and the three other ways of receiving it.
This is the first dream to be remastered, and it is the test of whether the
room's discipline survives contact with somewhere that is allowed to be
beautiful.

What carries over from the room, unchanged:

* **Five values from one base**, hue-shifted — shadows keeping their hue and
  pushed cool, highlights warm and desaturating.
* **Planes, not gradients.**  Every surface is a small number of flat regions
  and the boundaries between them are where the form is.
* **Dithering only at a value boundary**, two pixels wide.
* **Edges one value down their own ramp.**  Nothing here is outlined in black
  except an eye.
* **No noise.**  Every texture is a stated pattern with a direction.

What is allowed to be different, because this is a dream and not a bedroom:

* The chroma is much higher.  The room's whole palette lives inside about
  fifteen points of saturation; the grove's greens are allowed to be green.
* One colour per channel is permitted to be louder than anything in the
  waking half of the game — the lane markings here, the moss on the second
  channel, the colour bars on the fourth.

**The faux-isometric read** is the thing this shares with the room most
deliberately, and it is not a projection — it is a rule about faces.  Anything
standing up in this world shows three of them: a **top** in the lit value, a
**front** in the mid value below it, and a **side** in the shade value down
the right-hand edge, with the ground shadow under the front.  A tile-aligned
box drawn that way reads as a solid at a three-quarter view without a single
diagonal, which is exactly what the room's furniture is doing and why the two
places look like the same game.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import material as mt
from .canvas import Canvas, RGB, TRANSPARENT, blend
from .chipsets import TILE, _canvas

# How far down a standing thing its top face reaches, as a fraction of its
# height.  A third is enough to read as a top without turning every object
# into a plan view of itself.
TOP_FACE = 0.28


@dataclass(frozen=True)
class Look:
    """One channel of the grove, as a set of substances.

    The street plan is identical on all four channels, so everything that
    makes a channel itself has to live in the materials.  Which is the right
    place for it: the difference between the grove and the overgrown grove is
    not that a kerb moved, it is what the kerb is made of now.
    """
    grass: mt.Material
    road: mt.Material
    kerb: mt.Material
    paint: mt.Material          # lane markings, and nothing else
    bark: mt.Material
    leaf: mt.Material
    metal: mt.Material
    glass: mt.Material
    plastic: mt.Material        # the one loud colour a channel is allowed
    wear: float = 0.0           # how far gone the lane markings are
    seed: int = 0


GROVE = Look(
    grass=mt.Material("grass", (86, 132, 78)),
    road=mt.Material("road", (66, 66, 76)),
    kerb=mt.Material("kerb", (146, 146, 148)),
    paint=mt.Material("paint", (222, 220, 196)),
    bark=mt.Material("bark", (104, 78, 58)),
    leaf=mt.Material("leaf", (92, 152, 84)),
    metal=mt.Material("metal", (108, 114, 122)),
    glass=mt.Material("glass", (128, 168, 176)),
    plastic=mt.Material("plastic", (196, 84, 72)),
)

OVERGROWN = Look(
    grass=mt.Material("grass", (78, 138, 70)),
    # Darker than the verge on purpose.  Asphalt going back to soil still
    # has to read as asphalt, or the town is gone rather than overgrown.
    road=mt.Material("road", (44, 58, 42)),
    kerb=mt.Material("kerb", (104, 128, 90)),
    paint=mt.Material("paint", (198, 216, 148)),
    bark=mt.Material("bark", (88, 72, 48)),
    leaf=mt.Material("leaf", (78, 158, 74)),
    metal=mt.Material("metal", (92, 108, 88)),
    glass=mt.Material("glass", (110, 152, 128)),
    plastic=mt.Material("plastic", (156, 108, 60)),
    wear=0.45, seed=1,
)

OFF_COLOUR = Look(
    grass=mt.Material("grass", (128, 132, 126)),
    road=mt.Material("road", (88, 90, 94)),
    kerb=mt.Material("kerb", (168, 170, 168)),
    paint=mt.Material("paint", (226, 228, 226)),
    bark=mt.Material("bark", (110, 108, 104)),
    leaf=mt.Material("leaf", (132, 134, 130)),
    metal=mt.Material("metal", (126, 128, 130)),
    glass=mt.Material("glass", (150, 154, 156)),
    plastic=mt.Material("plastic", (146, 140, 134)),
    seed=2,
)

NO_SIGNAL = Look(
    grass=mt.Material("grass", (96, 96, 104)),
    road=mt.Material("road", (54, 54, 62)),
    kerb=mt.Material("kerb", (150, 150, 158)),
    paint=mt.Material("paint", (236, 232, 220)),
    bark=mt.Material("bark", (86, 80, 88)),
    leaf=mt.Material("leaf", (104, 102, 112)),
    metal=mt.Material("metal", (120, 118, 128)),
    glass=mt.Material("glass", (140, 140, 150)),
    plastic=mt.Material("plastic", (206, 58, 54)),
    wear=0.8, seed=3,
)

LOOKS = {"faces": GROVE, "faces2": OVERGROWN, "faces3": OFF_COLOUR,
         "faces4": NO_SIGNAL}


# --- the rule everything standing up obeys ------------------------------------

def solid(art: Canvas, x: int, y: int, w: int, h: int, mat: mt.Material, *,
          top: int | None = None, cap: mt.Material | None = None,
          rim: bool = True) -> None:
    """A box with a top, a front and a shaded side.

    Three faces and no diagonals.  The top is the lit value and is where the
    light lands; the front is the mid value and is most of what you see; the
    right-hand column is the shade value because the light comes from the
    upper left in every world in this game.  Two pixels of dithered seam sit
    between the top and the front so the corner is soft rather than ruled.

    This one function is the faux-isometric look.  Everything in the grove
    that stands up goes through it, which is why a phone box, a vending
    machine and a bus shelter read as being in the same world.
    """
    face = cap or mat
    top = TOP_FACE and int(h * TOP_FACE) if top is None else top
    top = max(2, top)
    mt.plane(art, x, y, w, top, face.lit)                    # the top face
    mt.seam(art, x, y + top - 2, w, 2, face.lit, mat.mid)
    mt.plane(art, x, y + top, w, h - top, mat.mid)           # the front
    mt.plane(art, x + w - 3, y + top, 3, h - top, mat.shade)  # the side
    mt.seam(art, x + w - 4, y + top, 2, h - top, mat.mid, mat.shade,
            vertical=True)
    mt.plane(art, x, y + h - 2, w, 2, mat.deep)              # where it meets
    if rim:                                                  # the ground
        art.vline(x, y + top, y + h - 1, mat.lit)
        art.hline(y, x + 1, x + w - 2, face.hot)


def post(art: Canvas, x: int, y: int, h: int, mat: mt.Material,
         width: int = 3) -> None:
    """A pole.  Lit down one side, shaded down the other, and never round."""
    mt.plane(art, x, y, width, h, mat.mid)
    art.vline(x, y, y + h - 1, mat.lit)
    art.vline(x + width - 1, y, y + h - 1, mat.shade)
    mt.plane(art, x - 1, y + h - 2, width + 2, 2, mat.deep)


def foot(art: Canvas, x: int, y: int, w: int, mat: mt.Material) -> None:
    """The dark contact under anything standing on the ground.

    Not a cast shadow — a shadow is a separate tile in this engine and would
    move with the light.  This is the two pixels where an object stops being
    an object, and without it everything in the world floats.
    """
    mt.plane(art, x, y, w, 2, mat.deep)


# --- ground -------------------------------------------------------------------

def turf(look: Look, variant: int) -> Canvas:
    """Grass, as blades rather than as noise.

    The old grove ground was a base colour with a dither and a scatter of
    random pixels on it, which at this size is grit.  These are short strokes
    on a grid that is offset per row, which reads as grass because grass has
    a direction and grit does not.
    """
    g = look.grass
    art = Canvas(TILE, TILE, g.mid)
    mt.plane(art, 0, 0, TILE, TILE, g.mid)
    for row in range(0, TILE, 4):
        shift = (row // 4 * 5 + variant * 3) % 8
        for col in range(shift, TILE + 8, 8):
            if col < TILE:
                art.rect(col, row, 1, 3, g.shade)
            if col + 4 < TILE:
                art.rect(col + 4, row + 1, 1, 2, g.lit)
    if variant % 2:
        mt.seam(art, 0, 9, TILE, 3, g.mid, g.shade)
    return art


def road(look: Look) -> Canvas:
    """Asphalt: a plane, with the aggregate in it drawn as a pattern."""
    r = look.road
    art = Canvas(TILE, TILE, r.mid)
    mt.plane(art, 0, 0, TILE, TILE, r.mid)
    for y in range(1, TILE, 5):
        for x in range((y // 5) * 3, TILE, 7):
            art.dot(x, y, r.shade)
            art.dot((x + 4) % TILE, y + 2, r.lit)
    return art


def lane(look: Look) -> Canvas:
    """The same asphalt with a marking on it, worn by however far the signal
    has drifted.  This is the one detail that tells a player how far from the
    original reception they are before they have consciously read anything."""
    art = road(look)
    p = look.paint
    if look.wear <= 0:
        mt.plane(art, 7, 0, 3, 10, p.mid)
        art.vline(7, 0, 9, p.lit)
        art.vline(9, 0, 9, p.shade)
        return art
    for y in range(10):
        if ((y * 7 + look.seed * 5) % 10) / 10.0 >= look.wear:
            mt.plane(art, 7, y, 3, 1, p.mid)
            art.dot(7, y, p.lit)
        elif ((y * 3 + look.seed) % 4) == 0:
            art.dot(8, y, blend(p.shade, look.road.mid, 0.45))
    return art


def lane_across(look: Look) -> Canvas:
    """The centre line of a road running east to west.

    The same marking turned ninety degrees.  One tile served both axes before
    this, so every east-west carriageway in the town had its dashes painted
    across the lane instead of along it.
    """
    art = road(look)
    p = look.paint
    if look.wear <= 0:
        mt.plane(art, 0, 7, 10, 3, p.mid)
        art.hline(7, 0, 9, p.lit)
        art.hline(9, 0, 9, p.shade)
        return art
    for x in range(10):
        if ((x * 7 + look.seed * 5) % 10) / 10.0 >= look.wear:
            mt.plane(art, x, 7, 1, 3, p.mid)
            art.dot(x, 7, p.lit)
        elif ((x * 3 + look.seed) % 4) == 0:
            art.dot(x, 8, blend(p.shade, look.road.mid, 0.45))
    return art


def kerb(look: Look, side: str = "n") -> Canvas:
    """A kerb in section, on whichever side of the carriageway it belongs to.

    The single most useful tile in the world for selling the perspective,
    because it is the one surface the player sees a *vertical face* of on
    every screen, and it is only three pixels tall.

    It has to know which side it is on.  A north-south avenue kerbed with the
    east-west tile is a pavement running at right angles to its own road, and
    once you have seen it you cannot stop seeing it.  ``side`` is which edge
    of the carriageway this stone sits on: ``n`` above an east-west road,
    ``s`` below it, ``w`` left of a north-south road, ``e`` right of it.
    """
    k, r = look.kerb, look.road
    art = road(look)
    horizontal = side in ("n", "s")
    # bands from the pavement side inward: the top of the stone, its face,
    # then the gutter where it meets the tarmac
    bands = ((0, 4, k.lit), (4, 2, None), (5, 3, k.mid), (8, 2, k.shade),
             (10, 2, r.deep))
    for start, depth, colour in bands:
        # the far side of the tile is measured from whichever edge the
        # pavement is on, so the four variants are one description
        if side in ("n", "w"):
            a, b = start, depth
        else:
            a, b = TILE - start - depth, depth
        if colour is None:
            top, low = (k.lit, k.mid) if side in ("n", "w") else (k.mid, k.lit)
            if horizontal:
                mt.seam(art, 0, a, TILE, b, top, low)
            else:
                mt.seam(art, a, 0, b, TILE, top, low, vertical=True)
            continue
        if horizontal:
            mt.plane(art, 0, a, TILE, b, colour)
        else:
            mt.plane(art, a, 0, b, TILE, colour)
    for at in range(0, TILE, 8):                 # the joint between stones
        if horizontal:
            art.vline(at, 0 if side == "n" else 6, 9 if side == "n" else TILE - 1,
                      k.shade)
        else:
            art.hline(at, 0 if side == "w" else 6, 9 if side == "w" else TILE - 1,
                      k.shade)
    return art


def paving(look: Look) -> Canvas:
    """Flags, laid to a grid, each one lit along the corner nearest the light."""
    k = look.kerb
    art = Canvas(TILE, TILE, k.mid)
    mt.tiles(art, 0, 0, TILE, TILE, k, size=8)
    return art


def moss(look: Look) -> Canvas:
    """Growth with a direction to it, for the channel that never stopped."""
    l = look.leaf
    art = Canvas(TILE, TILE, l.mid)
    mt.plane(art, 0, 0, TILE, TILE, l.mid)
    for row in range(0, TILE, 3):
        for col in range((row // 3 * 3) % 6, TILE, 6):
            art.rect(col, row, 3, 1, l.shade)
            art.rect((col + 3) % TILE, row + 1, 2, 1, l.lit)
    mt.seam(art, 0, 6, TILE, 3, l.mid, l.shade)
    return art


# --- what grows ---------------------------------------------------------------

def tree(look: Look, cols: int, rows: int, *, face: bool = False,
         bare: bool = False) -> Canvas:
    """A tree, as a mass of foliage with a lit top and a shaded underside.

    The canopy is built from overlapping lobes rather than from one ellipse.
    One ellipse shaded correctly is a perfectly good sphere and a completely
    charmless tree — the whole character of a tree at this size is in the
    bumps along the top of it, and the first pass at this traded every one of
    them for a clean silhouette.  The lobes are placed, not scattered: five of
    them, biggest in the middle, leaning the way the trunk leans.

    The shading is still the room's.  Three flat values per lobe, seams only
    where the lit crown meets the body, and no outline anywhere.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    b, l = look.bark, look.leaf
    lean = 1 if (cols + rows) % 2 else -1        # which way this one grew
    trunk_w = max(5, w // 5)
    trunk_x = (w - trunk_w) // 2
    trunk_top = int(h * (0.46 if not bare else 0.30))

    # the trunk, with a lit side, a shaded side, and roots that spread
    for row in range(trunk_top, h - 2):
        drift = int((row - trunk_top) / max(1, h - trunk_top) * 2) * -lean
        mt.plane(art, trunk_x + drift, row, trunk_w, 1, b.mid)
        art.dot(trunk_x + drift, row, b.lit)
        art.dot(trunk_x + drift + trunk_w - 1, row, b.shade)
        art.dot(trunk_x + drift + trunk_w - 2, row, b.shade)
    for grain in range(trunk_top + 5, h - 5, 8):          # bark, as courses
        art.hline(grain, trunk_x + 1, trunk_x + trunk_w - 3, b.shade)
    mt.plane(art, trunk_x - 3, h - 4, trunk_w + 6, 2, b.shade)  # the roots
    foot(art, trunk_x - 4, h - 2, trunk_w + 8, b)

    if bare:
        # branches: straight runs at fixed angles, because a bare tree read
        # from above is a diagram and should look like one
        for side, reach, rise in ((-1, 0.8, 0.9), (1, 0.9, 0.8),
                                  (-1, 0.5, 1.2), (1, 0.55, 1.1)):
            for step in range(int(w * 0.24 * reach)):
                bx = trunk_x + trunk_w // 2 + side * step
                by = trunk_top + 4 - int(step * rise)
                if 0 <= bx < w and 0 <= by < h:
                    art.dot(bx, by, b.mid)
                    art.dot(bx, by + 1, b.shade)
        return art

    # Five lobes.  Fractions of the canopy box rather than pixel positions, so
    # the same arrangement works at three tiles wide and at five.
    cy = int(h * 0.28)
    span, deep = w * 0.5, h * 0.26
    lobes = ((0.50, 0.00, 1.00), (0.20, 0.16, 0.62), (0.80, 0.18, 0.58),
             (0.34, -0.22, 0.58), (0.68, -0.16, 0.52))
    for fx, fy, fr in lobes:
        lx = int(w * fx) + lean * 2
        ly = cy + int(deep * fy)
        rx, ry = span * fr * 0.62, deep * fr * 0.82
        art.ellipse(lx, ly + 3, rx, ry, l.shade)          # the underside
        art.ellipse(lx, ly, rx, ry, l.mid)                # the body of it
    for fx, fy, fr in lobes[:3]:                          # and the light on it
        lx = int(w * fx) + lean * 2
        ly = cy + int(deep * fy)
        art.ellipse(lx - int(span * 0.10), ly - 3,
                    span * fr * 0.34, deep * fr * 0.40, l.lit)
    art.ellipse(int(w * 0.40), cy - 6, span * 0.20, deep * 0.22, l.hot)
    # one seam, where the lit crown meets the body, and nowhere else
    mt.seam(art, int(w * 0.18), cy + 1, int(w * 0.52), 2, l.lit, l.mid)
    # two leaves hanging below the mass, which is most of the whimsy
    for lx, ly in ((int(w * 0.14), cy + int(deep * 0.9)),
                   (int(w * 0.86), cy + int(deep * 0.8))):
        art.ellipse(lx, ly, 3.2, 2.0, l.mid)
        art.dot(lx - 1, ly - 1, l.lit)

    if face:
        # Not a face drawn on a tree: a place where the bark has failed and
        # what is behind it is looking out.  Two dark holes and a seam.
        ex, ey = w // 2, trunk_top + 9
        for dx in (-4, 2):
            art.rect(ex + dx, ey, 2, 3, b.deep)
            art.dot(ex + dx, ey, (0, 0, 0))
        art.hline(ey + 6, ex - 3, ex + 2, b.deep)
    return art


def stump(look: Look, cols: int, rows: int) -> Canvas:
    """A cut trunk: the ring of the cut on top, the bark round the side."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    b = look.bark
    solid(art, 2, h // 3, w - 4, h - h // 3 - 2, b, top=6,
          cap=mt.Material("cut", blend(b.base, (214, 190, 152), 0.45)))
    cut = mt.Material("cut", blend(b.base, (214, 190, 152), 0.45))
    for ring in range(2, 8, 2):                  # the rings, concentric
        art.ellipse(w // 2, h // 3 + 3, (w - 6) / 2 - ring, 2.4 - ring * 0.25,
                    cut.shade if ring % 4 else cut.lit)
    foot(art, 1, h - 2, w - 2, b)
    return art


def mushroom(look: Look, cap_colour: RGB, cols: int, rows: int) -> Canvas:
    """A cap and a stem.  The cap is lit on top and dark underneath, which is
    the whole of what makes it a cap rather than a disc."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    cap = mt.Material("cap", cap_colour)
    stem = mt.Material("stem", blend(cap_colour, (236, 228, 208), 0.62))
    sw = max(4, w // 4)
    mt.plane(art, (w - sw) // 2, h // 2, sw, h // 2 - 2, stem.mid)
    art.vline((w - sw) // 2, h // 2, h - 3, stem.lit)
    art.vline((w - sw) // 2 + sw - 1, h // 2, h - 3, stem.shade)
    art.ellipse(w // 2, h // 2 - 1, w * 0.42, h * 0.20, cap.shade)
    art.ellipse(w // 2, h // 2 - 3, w * 0.42, h * 0.18, cap.mid)
    art.ellipse(int(w * 0.42), h // 2 - 5, w * 0.24, h * 0.10, cap.lit)
    for dot in range(3):                          # spots, placed not scattered
        art.dot(int(w * (0.3 + dot * 0.2)), h // 2 - 4 + dot % 2, cap.hot)
    foot(art, (w - sw) // 2 - 1, h - 2, sw + 2, stem)
    return art


def bush(look: Look, cols: int, rows: int) -> Canvas:
    """Three overlapping masses, each with its own lit top.  Not one blob."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    l = look.leaf
    lobes = ((0.50, 0.62, 0.46), (0.24, 0.74, 0.30), (0.76, 0.72, 0.30),
             (0.38, 0.44, 0.26))
    for fx, fy, fr in lobes:
        cx, cy, r = int(w * fx), int(h * fy), w * fr * 0.5
        art.ellipse(cx, cy + 2, r, r * 0.72, l.shade)
        art.ellipse(cx, cy, r - 1, r * 0.68, l.mid)
        art.ellipse(int(cx - r * 0.25), cy - 2, r * 0.5, r * 0.36, l.lit)
    foot(art, int(w * 0.16), h - 2, int(w * 0.68), l)
    return art


# --- what the town left behind ------------------------------------------------

def traffic_light(look: Look, cols: int, rows: int) -> Canvas:
    """A signal head on a post.  Still cycling, for nobody."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.plastic
    post(art, w // 2 - 1, h // 3, h - h // 3 - 1, m, width=3)
    solid(art, 2, 2, w - 4, h // 3, m, top=4)
    lamp = ((196, 64, 56), (222, 186, 84), (104, 190, 110))
    for index, colour in enumerate(lamp):
        c = mt.Material("lamp", colour)
        cy = 6 + index * 5
        art.rect(w // 2 - 2, cy, 4, 4, c.shade)
        art.rect(w // 2 - 2, cy, 4, 2, c.lit if index == 0 else c.shade)
    art.hline(2, 3, w - 4, m.hot)
    return art


def bus_shelter(look: Look, cols: int, rows: int) -> Canvas:
    """A roof, two glass sides and a bench.  The roof is the top face."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, g = look.metal, look.glass
    # the glass back, seen through
    mt.plane(art, 3, 10, w - 6, h - 20, g.shade)
    for gx in range(5, w - 6, 9):                     # the panel joints
        art.vline(gx, 11, h - 12, g.mid)
    mt.plane(art, 3, 10, w - 6, 4, g.lit)             # the light on the glass
    mt.seam(art, 3, 13, w - 6, 3, g.lit, g.shade)
    # the roof, overhanging, which is the whole silhouette
    solid(art, 0, 0, w, 12, m, top=7)
    # the bench inside it, and the uprights
    mt.plane(art, 5, h - 16, w - 10, 5, m.mid)
    mt.plane(art, 5, h - 16, w - 10, 2, m.lit)
    for ux in (3, w - 6):
        mt.plane(art, ux, 10, 3, h - 12, m.mid)
        art.vline(ux, 10, h - 3, m.lit)
        art.vline(ux + 2, 10, h - 3, m.shade)
    foot(art, 2, h - 2, w - 4, m)
    return art


def phone_box(look: Look, cols: int, rows: int) -> Canvas:
    """A box with a lit roof, a glazed front and a door that shuts."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    p, g = look.plastic, look.glass
    solid(art, 1, 4, w - 2, h - 6, p, top=7)
    # the glazing, inset so the frame reads as having thickness
    mt.plane(art, 5, 14, w - 12, h - 26, g.shade)
    mt.plane(art, 5, 14, w - 12, 5, g.mid)
    mt.seam(art, 5, 18, w - 12, 3, g.mid, g.shade)
    for by in range(21, h - 14, 8):                   # the glazing bars
        art.hline(by, 5, w - 8, p.shade)
    art.vline(w // 2, 14, h - 14, p.shade)
    # the sign along the top, the one bright thing on it
    mt.plane(art, 3, 5, w - 6, 4, p.hot)
    art.hline(5, 4, w - 5, blend(p.hot, (255, 255, 255), 0.5))
    foot(art, 0, h - 2, w, p)
    return art


def dead_car(look: Look, cols: int, rows: int) -> Canvas:
    """A car from three quarters on: roof, glasshouse, body, and a shadow.

    The one object in the world with a shape nobody has to be told the name
    of, so it is where the perspective has to be most correct.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    body = mt.Material("body", blend(look.plastic.base, (96, 104, 120), 0.55))
    g, m = look.glass, look.metal
    # the body: a long lit roofline, a front face, and a dark sill
    mt.plane(art, 2, 6, w - 4, h - 12, body.mid)
    mt.plane(art, 2, 6, w - 4, 4, body.lit)
    mt.seam(art, 2, 9, w - 4, 3, body.lit, body.mid)
    mt.plane(art, 2, h - 10, w - 4, 3, body.shade)
    mt.plane(art, 3, h - 7, w - 6, 2, body.deep)
    # the glasshouse, set in from both ends
    mt.plane(art, 8, 8, w - 18, h - 20, g.shade)
    mt.plane(art, 8, 8, w - 18, 3, g.mid)
    art.vline((w - 18) // 2 + 8, 8, h - 14, body.shade)
    # lamps and wheels
    for lx, lit in ((3, True), (w - 6, False)):
        art.rect(lx, h - 16, 3, 4, m.lit if lit else m.shade)
    for wx in (6, w - 12):
        mt.plane(art, wx, h - 8, 6, 4, (24, 24, 28))
        art.hline(h - 8, wx, wx + 5, m.shade)
    foot(art, 2, h - 3, w - 4, body)
    return art


def vending_machine(look: Look, cols: int, rows: int) -> Canvas:
    """Still lit, still stocked, still taking money nobody has."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p, g = look.metal, look.plastic, look.glass
    solid(art, 1, 2, w - 2, h - 4, p, top=6)
    # the window, and what is behind it, in rows rather than at random
    mt.plane(art, 4, 12, w - 12, h - 24, g.shade)
    for shelf in range(12, h - 14, 7):
        art.hline(shelf, 4, w - 9, g.mid)
        for item in range(4, w - 10, 5):
            art.rect(item + 1, shelf + 2, 3, 4,
                     [p.mid, m.lit, p.hot][(shelf + item) % 3])
    # the panel down the side: keypad, slot, tray
    mt.plane(art, w - 8, 12, 5, h - 24, m.shade)
    for ky in range(14, h - 20, 4):
        art.rect(w - 7, ky, 3, 2, m.lit)
    mt.plane(art, 4, h - 10, w - 10, 4, m.deep)
    foot(art, 0, h - 2, w, p)
    return art


def road_sign(look: Look, cols: int, rows: int) -> Canvas:
    """A plate on a post.  It has been turned to face away from the road."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.paint
    post(art, w // 2 - 1, h // 3, h - h // 3 - 1, m, width=3)
    mt.plane(art, 2, 3, w - 4, h // 3 - 2, p.mid)
    mt.plane(art, 2, 3, w - 4, 2, p.hot)              # the lit top edge
    mt.plane(art, 2, h // 3, w - 4, 2, p.shade)
    art.vline(w - 3, 3, h // 3 + 1, p.shade)
    for line in range(6, h // 3 - 2, 4):              # legend, unreadable
        art.hline(line, 5, w - 7, blend(p.deep, p.mid, 0.3))
    return art


# --- the hidden half ----------------------------------------------------------
# Twelve secret rooms and four locked buildings, all of them behind something.
# They share two chipsets because they share two ideas about what a hidden
# place is made of: rock and water under the town, board and paint inside it.

CAVE = Look(
    grass=mt.Material("moss", (62, 96, 68)),
    road=mt.Material("rock", (78, 74, 86)),
    kerb=mt.Material("wet", (96, 100, 118)),
    paint=mt.Material("chalk", (206, 202, 190)),
    bark=mt.Material("clay", (96, 74, 62)),
    leaf=mt.Material("weed", (74, 116, 78)),
    metal=mt.Material("iron", (94, 96, 104)),
    glass=mt.Material("water", (56, 82, 108)),
    plastic=mt.Material("lamp", (206, 168, 106)),
)

PREM = Look(
    grass=mt.Material("board", (98, 74, 58)),
    road=mt.Material("lino", (92, 90, 96)),
    kerb=mt.Material("skirt", (78, 66, 58)),
    paint=mt.Material("paper", (196, 190, 176)),
    bark=mt.Material("desk", (106, 80, 60)),
    leaf=mt.Material("felt", (72, 96, 88)),
    metal=mt.Material("rack", (104, 108, 118)),
    glass=mt.Material("crt", (66, 86, 90)),
    plastic=mt.Material("bake", (176, 122, 74)),
)


def rock_face(look: Look, *, cracked: bool = False, seed: int = 0) -> Canvas:
    """Living rock: irregular blocky mass, and nothing on a grid.

    The first attempt at this laid regular courses with staggered joints,
    which is a *wall* — somebody built that, and the whole point of a cave is
    that nobody did.  Rock breaks along its own faults, so this is a handful
    of unequal chunks at unequal heights, each with light on its upper edge
    and shadow under it, and the gaps between them are the dark.
    """
    r = look.road
    art = Canvas(TILE, TILE, r.shade)
    mt.plane(art, 0, 0, TILE, TILE, r.deep)
    # deterministic, but with no period the eye can pick up at this size
    lump = ((0, 0, 7, 6), (7, 1, 9, 5), (2, 6, 6, 5), (9, 7, 7, 6),
            (0, 11, 5, 5), (5, 12, 5, 4), (12, 3, 4, 4))
    for index, (x, y, w, h) in enumerate(lump):
        x = (x + seed * 3) % TILE
        mt.plane(art, x, y, w, h, r.mid)
        art.hline(y, x, min(TILE - 1, x + w - 1), r.lit)      # the lit top
        art.hline(y + h - 1, x, min(TILE - 1, x + w - 1), r.deep)
        art.vline(min(TILE - 1, x + w - 1), y, y + h - 1, r.shade)
        if index % 3 == 0 and w > 3:
            art.hline(y + 2, x + 1, x + w - 2, r.shade)       # a bedding line
    if cracked:
        # one dark run that ignores every fault line, which is exactly why the
        # eye finds it
        for step in range(TILE):
            x = 6 + (step // 4) - (step % 7 == 0)
            art.vline(max(0, x), step, step, (0, 0, 0))
            art.dot(max(0, x + 1), step, r.deep)
            art.dot(max(0, x - 1), step, r.shade)
    return art


def rubble(look: Look, seed: int = 0) -> Canvas:
    """A cave floor: broken stone, lying where it fell."""
    r, c = look.road, look.bark
    art = Canvas(TILE, TILE, c.mid)
    mt.plane(art, 0, 0, TILE, TILE, c.mid)
    chips = ((1, 2, 4, 2), (7, 1, 3, 2), (11, 4, 4, 2), (3, 7, 5, 2),
             (9, 9, 4, 2), (1, 12, 3, 2), (12, 12, 3, 2))
    for index, (x, y, w, h) in enumerate(chips):
        x, y = (x + seed) % TILE, (y + seed * 2) % TILE
        mt.plane(art, x, y, w, h, r.shade if index % 2 else c.shade)
        art.hline(y, x, min(TILE - 1, x + w - 1), r.lit if index % 2 else c.lit)
    return art


def pool(look: Look, seed: int = 0) -> Canvas:
    """Standing water in a cave: a ragged edge, because nothing cut it.

    A rectangle of water on a cave floor is a rug, and it looked like one.
    """
    w, c = look.glass, look.bark
    art = rubble(look, seed)
    edge = (5, 3, 2, 4, 1, 3, 6, 4, 2, 1, 3, 5, 4, 2, 3, 6)
    for y in range(TILE):
        start = edge[(y + seed * 3) % TILE] // 2
        run = TILE - start - edge[(y * 3 + seed) % TILE] // 3
        if run <= 0:
            continue
        mt.plane(art, start, y, run, 1, w.shade if y % 4 else w.mid)
        art.dot(start, y, c.deep)
    art.hline(4, 3, 9, w.lit)
    art.hline(10, 6, TILE - 3, w.lit)
    return art


def boulder(look: Look, cols: int, rows: int) -> Canvas:
    """A lump of the ceiling that is now a lump of the floor."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    r = look.road
    art.ellipse(w // 2, h - h // 3 + 2, w * 0.44, h * 0.34, r.deep)
    art.ellipse(w // 2, h - h // 3, w * 0.42, h * 0.32, r.mid)
    art.ellipse(int(w * 0.40), h - h // 3 - 3, w * 0.24, h * 0.16, r.lit)
    art.hline(h - h // 3 - 6, int(w * 0.26), int(w * 0.62), r.shade)
    foot(art, int(w * 0.16), h - 3, int(w * 0.68), r)
    return art


def column(look: Look, cols: int, rows: int) -> Canvas:
    """Stalagmite meeting stalactite.  They met a long time ago."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    r = look.road
    for row in range(h):
        t = abs(row / max(1, h - 1) - 0.5) * 2      # fat at both ends
        half = max(2, int(w * (0.10 + 0.22 * t)))
        mt.plane(art, w // 2 - half, row, half * 2, 1, r.mid)
        art.dot(w // 2 - half, row, r.lit)
        art.dot(w // 2 + half - 1, row, r.shade)
    foot(art, w // 2 - 5, h - 2, 10, r)
    return art


def cave_mouth(look: Look, cols: int, rows: int) -> Canvas:
    """The way back out: a hole in the rock with daylight past it.

    Not a mirror.  Every hidden room used the portal frame the nexus uses,
    which made a cave read as somewhere with a full-length mirror in it.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    r, l = look.road, look.plastic
    mt.plane(art, 2, 4, w - 4, h - 4, r.shade)             # the surround
    for step in range(h - 6):                              # a ragged opening
        t = step / max(1, h - 7)
        inset = int(4 + 6 * abs(t - 0.55) + (step % 3))
        mt.plane(art, inset, 6 + step, w - inset * 2, 1, (0, 0, 0))
        art.dot(inset - 1, 6 + step, r.deep)
        art.dot(w - inset, 6 + step, r.deep)
    mt.plane(art, 6, h - 8, w - 12, 4, blend(l.deep, (0, 0, 0), 0.45))
    art.hline(h - 8, 7, w - 8, l.shade)                    # light, a long way
    art.hline(4, 3, w - 4, r.lit)                          # the lintel
    return art


def ladder(look: Look, cols: int, rows: int) -> Canvas:
    """Iron rungs going up, into a circle of the sky."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    art.ellipse(w // 2, 6, w * 0.34, 5, (0, 0, 0))
    art.ellipse(w // 2, 5, w * 0.32, 4.4, blend(m.lit, (0, 0, 0), 0.3))
    for rung in range(12, h - 2, 6):
        mt.plane(art, w // 2 - 6, rung, 12, 2, m.mid)
        art.hline(rung, w // 2 - 6, w // 2 + 5, m.lit)
    for side in (w // 2 - 7, w // 2 + 5):
        mt.plane(art, side, 8, 2, h - 10, m.shade)
        art.vline(side, 8, h - 3, m.mid)
    return art


def sewer_wall(look: Look) -> Canvas:
    """Engineering brick.  Somebody *did* build this one."""
    b = mt.Material("brick", (104, 70, 60))
    art = Canvas(TILE, TILE, b.mid)
    mt.bricks(art, 0, 0, TILE, TILE, b, course=5, stagger=True)
    return art


def sewer_channel(look: Look) -> Canvas:
    """The invert: water in a cut channel, running one way."""
    w = look.glass
    b = mt.Material("brick", (104, 70, 60))
    art = Canvas(TILE, TILE, b.mid)
    mt.plane(art, 0, 0, TILE, TILE, b.shade)
    mt.plane(art, 0, 3, TILE, 11, w.shade)
    mt.seam(art, 0, 3, TILE, 3, b.deep, w.shade)
    art.hline(6, 1, 8, w.lit)
    art.hline(10, 7, TILE - 2, w.mid)
    mt.plane(art, 0, 14, TILE, 2, b.deep)
    return art


def cave_floor(look: Look, wet: bool = False) -> Canvas:
    """Rubble underfoot, and where it is wet it is a plane with a shine."""
    r, w = look.bark, look.glass
    art = Canvas(TILE, TILE, r.mid)
    mt.plane(art, 0, 0, TILE, TILE, r.mid)
    for y in range(1, TILE, 5):
        for x in range((y // 5) * 4, TILE, 6):
            art.rect(x, y, 2, 1, r.shade)
            art.dot(x + 1, y + 1, r.lit)
    if wet:
        mt.plane(art, 0, 0, TILE, TILE, w.shade)
        mt.seam(art, 0, 5, TILE, 4, w.mid, w.shade)
        art.hline(3, 2, 9, w.lit)
        art.hline(11, 6, TILE - 2, w.lit)
    return art


def brick_wall(look: Look) -> Canvas:
    """Engineering brick, for everything under the road that was built."""
    b = mt.Material("brick", (108, 72, 62))
    art = Canvas(TILE, TILE, b.mid)
    mt.bricks(art, 0, 0, TILE, TILE, b, course=5, stagger=True)
    return art


def boards(look: Look, offset: int) -> Canvas:
    """An interior floor: the room's own boards, in this world's timber."""
    f = look.grass
    art = Canvas(TILE, TILE, f.mid)
    mt.plane(art, 0, 0, TILE, TILE, f.mid)
    for top in range(0, TILE, 8):
        art.hline(top, 0, TILE - 1, f.shade)
        art.hline(top + 1, 0, TILE - 1, f.lit)
        art.hline(top + 5, 0, TILE - 1, f.shade)
    if offset:
        art.vline(offset % TILE, 0, TILE - 1, f.shade)
    return art


def rack(look: Look, cols: int, rows: int) -> Canvas:
    """Equipment: a frame of shelves with things blinking in it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, g, l = look.metal, look.glass, look.plastic
    solid(art, 1, 2, w - 2, h - 4, m, top=5)
    for shelf in range(10, h - 8, 9):
        mt.plane(art, 4, shelf, w - 10, 7, g.shade)
        mt.plane(art, 4, shelf, w - 10, 2, g.mid)
        for lamp in range(6, w - 10, 6):
            art.dot(lamp, shelf + 4, l.mid if (lamp + shelf) % 3 else g.lit)
    foot(art, 0, h - 2, w, m)
    return art


def crate(look: Look, cols: int, rows: int) -> Canvas:
    """A box that has been here longer than you have."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    b = look.bark
    solid(art, 1, 3, w - 2, h - 5, b, top=6)
    for band in (h // 2, h - 10):
        mt.plane(art, 1, band, w - 2, 2, b.shade)
    foot(art, 0, h - 2, w, b)
    return art


def water_pool(look: Look) -> Canvas:
    """Standing water.  It has been standing a long time."""
    w = look.glass
    art = Canvas(TILE, TILE, w.mid)
    mt.plane(art, 0, 0, TILE, TILE, w.shade)
    mt.seam(art, 0, 3, TILE, 5, w.mid, w.shade)
    art.hline(2, 1, 8, w.lit)
    art.hline(9, 5, TILE - 2, w.lit)
    return art


# --- what the sixteen are actually made of ------------------------------------
# One template per family and a per-room tint gave sixteen rooms that were four
# rooms.  These are the substances and fittings that let each of them be its
# own place: a room is bespoke when its *walls* and its *contents* are, not
# when its furniture has been shuffled.

def wedge_wall(look: Look) -> Canvas:
    """Anechoic foam: wedges, floor to ceiling, perfectly regular.

    The one wall in the world with no fault in it.  Everywhere else down here
    is irregular on purpose, so a wall that repeats exactly is the most
    unnatural surface the game has.
    """
    m = mt.Material("foam", (58, 54, 68))
    art = Canvas(TILE, TILE, m.mid)
    for row in range(0, TILE, 8):
        for col in range(0, TILE, 4):
            for step in range(4):
                shade = (m.lit, m.mid, m.shade, m.deep)[step]
                art.rect(col + step, row, 1, 8, shade)
        art.hline(row, 0, TILE - 1, m.deep)
    return art


def flat_floor(look: Look, mat: mt.Material) -> Canvas:
    """A poured floor.  No aggregate, no chips, nothing lying on it."""
    art = Canvas(TILE, TILE, mat.mid)
    mt.plane(art, 0, 0, TILE, TILE, mat.mid)
    mt.seam(art, 0, 6, TILE, 4, mat.mid, mat.shade)
    return art


def deep_water(look: Look) -> Canvas:
    """Water bank to bank, and no bottom visible."""
    w = look.glass
    art = Canvas(TILE, TILE, w.deep)
    mt.plane(art, 0, 0, TILE, TILE, w.deep)
    mt.seam(art, 0, 4, TILE, 5, w.shade, w.deep)
    art.hline(2, 2, 10, w.mid)
    art.hline(11, 5, TILE - 2, w.shade)
    return art


def dry_channel(look: Look) -> Canvas:
    """The invert with nothing in it, swept."""
    b = mt.Material("brick", (104, 70, 60))
    art = Canvas(TILE, TILE, b.shade)
    mt.plane(art, 0, 0, TILE, TILE, b.shade)
    mt.plane(art, 0, 3, TILE, 10, b.deep)
    art.hline(3, 0, TILE - 1, b.mid)
    art.hline(12, 0, TILE - 1, b.mid)
    return art


def glass_wall(look: Look) -> Canvas:
    """Greenhouse glazing, green with the inside of itself."""
    g, f = look.glass, look.leaf
    art = Canvas(TILE, TILE, g.shade)
    mt.plane(art, 0, 0, TILE, TILE, g.shade)
    mt.plane(art, 0, 0, TILE, 5, g.mid)
    mt.seam(art, 0, 5, TILE, 3, g.mid, g.shade)
    for x in range(0, TILE, 8):
        art.vline(x, 0, TILE - 1, f.shade)
        art.vline(x + 1, 0, TILE - 1, f.mid)
    art.hline(0, 0, TILE - 1, g.lit)
    return art


def planting_bed(look: Look) -> Canvas:
    """Soil, in a raised bed, with things coming out of it."""
    s = mt.Material("soil", (72, 54, 44))
    f = look.leaf
    art = Canvas(TILE, TILE, s.mid)
    mt.plane(art, 0, 0, TILE, TILE, s.mid)
    mt.plane(art, 0, 0, TILE, 2, s.lit)
    mt.plane(art, 0, TILE - 2, TILE, 2, s.deep)
    for x in range(2, TILE, 5):
        art.vline(x, 4, 12, f.mid)
        art.dot(x - 1, 5, f.lit)
        art.dot(x + 1, 7, f.shade)
    return art


def _panel(look: Look, cols: int, rows: int, mat: mt.Material,
           lamps: int, colour: mt.Material) -> Canvas:
    """A standing unit with something readable on the front of it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    solid(art, 1, 2, w - 2, h - 4, mat, top=5)
    for row in range(9, h - 8, 7):
        mt.plane(art, 4, row, w - 10, 5, mat.shade)
        for index in range(lamps):
            lx = 6 + index * ((w - 14) // max(1, lamps))
            art.rect(lx, row + 1, 2, 2,
                     colour.mid if (row + index) % 3 else colour.hot)
    foot(art, 0, h - 2, w, mat)
    return art


def lever_bank(look: Look, cols: int, rows: int) -> Canvas:
    """A frame of signal levers, every one of them pulled over."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.plastic
    mt.plane(art, 0, h - 12, w, 8, m.shade)
    mt.plane(art, 0, h - 12, w, 2, m.lit)
    for index, lx in enumerate(range(3, w - 3, 5)):
        lean = -2 if index % 2 else 2
        for step in range(14):
            art.dot(lx + (lean * step) // 14, h - 14 - step,
                    m.mid if step > 2 else p.mid)
        art.rect(lx - 1, h - 12, 3, 5, m.deep)
    foot(art, 0, h - 3, w, m)
    return art


def desk(look: Look, cols: int, rows: int) -> Canvas:
    """A working surface with something on it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    d, g = look.bark, look.glass
    mt.plane(art, 0, h - 18, w, 8, d.mid)
    mt.plane(art, 0, h - 18, w, 2, d.lit)
    mt.plane(art, 1, h - 10, w - 2, 3, d.deep)
    for lx in (2, w - 5):
        mt.plane(art, lx, h - 8, 3, 7, d.shade)
    mt.plane(art, 5, h - 28, 12, 10, g.shade)     # a screen on it
    mt.plane(art, 6, h - 27, 10, 4, g.mid)
    foot(art, 0, h - 2, w, d)
    return art


def jack_frame(look: Look, cols: int, rows: int) -> Canvas:
    """A telephone exchange frame: rows of jacks, all of them patched."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.plastic
    solid(art, 0, 1, w, h - 3, m, top=4)
    for row in range(8, h - 6, 5):
        for col in range(3, w - 3, 3):
            art.rect(col, row, 2, 2, m.deep)
            if (row + col) % 4 == 0:
                art.dot(col, row + 2, p.mid)
                art.dot(col, row + 3, p.shade)
    foot(art, 0, h - 2, w, m)
    return art


def transformer(look: Look, cols: int, rows: int) -> Canvas:
    """Something live, behind a fence, that you are not going to touch."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.plastic
    solid(art, 2, 6, w - 4, h - 10, m, top=6)
    for fin in range(4, w - 4, 4):                 # cooling fins
        art.vline(fin, 12, h - 8, m.shade)
        art.vline(fin + 1, 12, h - 8, m.lit)
    for bx in (5, w - 8):                          # bushings on top
        mt.plane(art, bx, 1, 3, 6, p.mid)
        art.dot(bx + 1, 1, p.hot)
    foot(art, 1, h - 3, w - 2, m)
    return art


def mesh_fence(look: Look, cols: int, rows: int) -> Canvas:
    """Chain link.  You can see all of it and reach none of it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m = look.metal
    for x in range(0, w, 3):
        art.vline(x, 4, h - 3, m.shade)
    for y in range(4, h - 2, 3):
        art.hline(y, 0, w - 1, m.mid)
    mt.plane(art, 0, 2, w, 2, m.lit)
    for px in range(0, w, 12):
        mt.plane(art, px, 2, 2, h - 4, m.mid)
    return art


def transmitter(look: Look, cols: int, rows: int) -> Canvas:
    """The thing itself, running, on all four carriers."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p, g = look.metal, look.plastic, look.glass
    solid(art, 1, 3, w - 2, h - 5, m, top=6)
    for row, tone in enumerate((p, g, p, g)):      # four carriers, four lamps
        art.rect(4 + row * 5, 12, 3, 3, tone.hot if row % 2 else tone.mid)
    mt.plane(art, 4, 18, w - 10, h - 26, g.shade)  # the meter window
    for tick in range(6, w - 10, 4):
        art.vline(tick, 20, h - 12, g.mid)
    art.hline(h - 14, 5, w - 8, p.hot)
    foot(art, 0, h - 2, w, m)
    return art


def cable_tray(look: Look, cols: int, rows: int) -> Canvas:
    """Bundles going one way, and one of them carrying nothing."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    m, p = look.metal, look.plastic
    mt.plane(art, 0, 2, w, h - 6, m.shade)
    mt.plane(art, 0, 2, w, 2, m.lit)
    for index, row in enumerate(range(6, h - 8, 5)):
        tone = p if index == 1 else m
        mt.plane(art, 2, row, w - 4, 3, tone.mid)
        art.hline(row, 2, w - 3, tone.lit)
    foot(art, 0, h - 3, w, m)
    return art


# --- the four ways in ---------------------------------------------------------
# A playthrough found the grove's hidden half unfindable, and the reason was
# not that it was well hidden: the crack, the cover, the hatch and the locked
# door had interactions and *no art at all*.  Four invisible gleams on open
# grass, in a town a hundred and forty tiles across.  The player walked past
# the place the entrance was and correctly reported there was nothing there.
#
# Each of these is a thing you can find by looking, which is the only kind of
# hiding this game is allowed to do.


def _bedded(ground: Canvas, cols: int, rows: int) -> Canvas:
    """A drawing surface already covered in the ground it will stand on.

    The four entrances live on the **lower** layer, which is the one rule this
    codebase has about layers turned on its head, and it is not a preference:
    the grove's chipsets have 139 of their 144 upper-layer slots spent, and
    four objects need twenty-two.  Block F is a hard format limit and there is
    no arguing with it.

    The cost of the lower layer is that an object carries its ground with it,
    so each of these bakes in the surface it is actually placed on -- turf for
    the ones in the clearings, road for the one in the carriageway -- and
    ``hidden.entrances`` puts them where that surface is.  It is a bargain
    struck with the format rather than a design.
    """
    art = Canvas(cols * TILE, rows * TILE, (0, 0, 0))
    for row in range(rows):
        for col in range(cols):
            art.paste(ground, col * TILE, row * TILE)
    return art


def rock_split(look: Look, cols: int = 2, rows: int = 3) -> Canvas:
    """An outcrop with a split in it, shoulder wide.

    Rock, in a town made of grass and asphalt, is already the odd thing on the
    screen; the split then reads as the reason the rock is there.  The dark of
    it runs the full height and does not narrow, because a crack that tapers
    looks like damage and a crack that does not looks like a way through.
    """
    art = _bedded(turf(look, 0), cols, rows)
    w, h = cols * TILE, rows * TILE
    r = look.road
    # The mass, in unequal chunks -- the same rule rock_face works by.
    solid(art, 0, TILE, w, h - TILE, r, cap=r)
    for index, (x, y, cw, ch) in enumerate(
            ((0, TILE - 5, 11, 9), (12, TILE - 2, 12, 8),
             (2, TILE + 12, 9, 7), (w - 9, TILE + 9, 9, 8))):
        mt.plane(art, x, y, cw, ch, r.mid)
        art.hline(y, x, min(w - 1, x + cw - 1), r.lit)
        art.hline(y + ch - 1, x, min(w - 1, x + cw - 1), r.deep)
    # The split: straight down the middle, black, with the light catching one
    # lip of it and the other lip in shadow.
    mid = w // 2
    for y in range(TILE - 4, h):
        lean = (y - TILE) // 14
        art.vline(mid + lean, y, y, (0, 0, 0))
        art.vline(mid + lean - 1, y, y, (0, 0, 0))
        art.dot(mid + lean - 2, y, r.shade)
        art.dot(mid + lean + 1, y, r.lit if y % 5 else r.deep)
    # A little of what is inside, at the bottom, so it reads as depth.
    art.rect(mid - 3, h - 6, 6, 6, (0, 0, 0))
    return art


def manhole(look: Look, cols: int = 2, rows: int = 2) -> Canvas:
    """A cover seated in the road, with the rim proud of the asphalt.

    Flat, because it is flat, and legible only because the metal takes the
    light differently from the tarmac around it.  It is the one entrance that
    is *not* hidden by being out of the way -- it is hidden by being the most
    ordinary object in a town.
    """
    art = _bedded(road(look), cols, rows)
    w, h = cols * TILE, rows * TILE
    m, r = look.metal, look.road
    cx, cy = w / 2, h / 2 + 1
    art.ellipse(cx, cy + 1, w * 0.40, h * 0.30, r.deep)      # the seat
    art.ellipse(cx, cy, w * 0.38, h * 0.28, m.shade)         # the rim
    art.ellipse(cx, cy, w * 0.32, h * 0.23, m.mid)           # the plate
    # Cast pattern: concentric, because every cover in the world is.
    art.ellipse(cx, cy, w * 0.22, h * 0.15, m.shade)
    art.ellipse(cx, cy, w * 0.20, h * 0.13, m.mid)
    for step in range(-3, 4):
        art.vline(int(cx + step * 3), int(cy - 4), int(cy + 4), m.deep)
    art.hline(int(cy - h * 0.26), int(cx - w * 0.24), int(cx + w * 0.24), m.lit)
    # The two slots you would put a bar through.
    art.rect(int(cx - w * 0.28), int(cy - 1), 3, 2, (0, 0, 0))
    art.rect(int(cx + w * 0.28) - 2, int(cy - 1), 3, 2, (0, 0, 0))
    return art


def hatch_shed(look: Look, cols: int = 2, rows: int = 3) -> Canvas:
    """Something small with a way up into it, and a hatch left open.

    Board and paint rather than rock, because the three rooms this leads to
    are all built things -- a signal box, a greenhouse, a substation -- and
    the entrance should say which half of the hidden world it belongs to
    before the player is through it.
    """
    art = _bedded(turf(look, 0), cols, rows)
    w, h = cols * TILE, rows * TILE
    b, m = look.bark, look.metal
    solid(art, 1, TILE, w - 2, h - TILE - 1, b, cap=b)
    # Boarding, vertical, with one board darker than its neighbours.
    for x in range(2, w - 2, 4):
        art.vline(x, TILE + 2, h - 3, b.shade if (x // 4) % 3 else b.deep)
    # The hatch itself, up under the eaves and standing open on its hinge.
    hx, hy, hw, hh = w // 2 - 6, TILE + 3, 12, 10
    art.rect(hx, hy, hw, hh, (0, 0, 0))
    art.rect(hx + 1, hy + 1, hw - 2, hh - 2, blend(b.deep, (0, 0, 0), 0.6))
    art.rect(hx - 3, hy - 1, 3, hh + 2, b.lit)               # the flap, open
    art.vline(hx - 3, hy - 1, hy + hh, b.shade)
    # A ladder standing in it, which is the part that says "up".
    for y in range(hy + 2, hy + hh, 3):
        art.hline(y, hx + 2, hx + hw - 3, m.lit)
    art.vline(hx + 2, hy + 1, hy + hh - 1, m.mid)
    art.vline(hx + hw - 3, hy + 1, hy + hh - 1, m.mid)
    return art


def locked_door(look: Look, tag: tuple[int, int, int],
                cols: int = 2, rows: int = 3) -> Canvas:
    """A door that does not open, painted the colour of the key that opens it.

    The paint is the only instruction the game ever gives about the locks, and
    it gives it without a word: four doors, four colours, and the colour of
    each one is the channel its key is on rather than the channel it stands
    on.  So it has to be unmistakably a *colour* and not a shade -- the tag
    band runs the full width of the door and is the brightest thing on it.
    """
    art = _bedded(paving(look), cols, rows)
    w, h = cols * TILE, rows * TILE
    b, m = look.bark, look.metal
    solid(art, 0, 2, w, h - 2, b, cap=b)
    # The opening, recessed, with the door sitting inside it.
    dx, dy, dw, dh = 3, 8, w - 6, h - 10
    art.rect(dx - 1, dy - 1, dw + 2, dh + 2, b.deep)
    art.rect(dx, dy, dw, dh, blend(tag, (0, 0, 0), 0.45))
    art.rect(dx + 1, dy + 1, dw - 2, dh - 3, tag)
    # Two panels, so it reads as a door and not as a painted rectangle.
    for row in range(2):
        py = dy + 4 + row * (dh // 2 - 1)
        art.rect(dx + 3, py, dw - 6, dh // 2 - 6, blend(tag, (0, 0, 0), 0.30))
        art.hline(py, dx + 3, dx + dw - 4, blend(tag, (255, 255, 255), 0.35))
    # Handle, keyhole, and the shine along the hinge side.
    art.rect(dx + dw - 6, dy + dh // 2 - 1, 3, 2, m.lit)
    art.dot(dx + dw - 5, dy + dh // 2 + 2, (0, 0, 0))
    art.vline(dx + 1, dy + 1, dy + dh - 3, blend(tag, (255, 255, 255), 0.25))
    return art


# --- the town going under -----------------------------------------------------
# A grove with a brown brick boundary is not a grove, and a road with no crack
# in it is a road somebody is still maintaining.  These are the tiles that say
# the town lost.


def hedge(look: Look, seed: int = 0, base: tuple[int, int, int] | None = None
          ) -> Canvas:
    """Massed greenery, dark and bushy, as a boundary you cannot see through.

    The grove's secondary boundary was a brown strata band -- the generic
    fallback, inherited because the motif table had no opinion about this
    world -- so a third of the town was walled in masonry.  This is the same
    job done in leaves: overlapping lobes, each lit on the crown and dark
    underneath, with no straight edge anywhere in it.
    """
    # The boundary has to be one material.  Left to its own leaf colour the
    # hedge came out grey-blue on the channel whose wall is near-black red,
    # so the two halves of the same fence read as two different fences.  The
    # caller passes the wall's own base and both are built from it.
    l = mt.Material("hedge", base) if base else look.leaf
    g = look.grass if base is None else l
    art = Canvas(TILE, TILE, blend(l.deep, (0, 0, 0), 0.35))
    mt.plane(art, 0, 0, TILE, TILE, blend(l.deep, (0, 0, 0), 0.30))
    lobes = ((3, 3, 6), (11, 5, 5), (6, 10, 6), (13, 12, 4), (0, 8, 4),
             (8, 1, 4), (1, 14, 5), (14, 0, 4))
    for index, (cx, cy, r) in enumerate(lobes):
        cx = (cx + seed * 5) % TILE
        body = l.shade if index % 3 else blend(l.mid, l.deep, 0.4)
        art.blob(cx, cy, r, body)
        art.blob(cx - 1, cy - 1, max(1, r - 2), blend(body, l.lit, 0.35))
        art.dot(cx - 1, cy - r + 1, l.lit)
    # a few blades catching the light along the top, so it reads as growth
    for x in range(0, TILE, 3):
        art.dot((x + seed) % TILE, (x * 5) % 4, blend(g.lit, l.lit, 0.5))
    return art


# --- what is left in the street -----------------------------------------------

def overtaken_house(look: Look, cols: int = 5, rows: int = 5) -> Canvas:
    """A house the growth has got to, with the house still legible.

    The one this replaces was named a house and drawn as a canopy over two
    tan lobes -- the greenery had eaten it so completely that nothing said
    building.  A ruin has to be readable as the thing it used to be or it is
    just terrain, so the roof line, the windows and the door survive here and
    the ivy goes *over* them.
    """
    art = _bedded(turf(look, 0), cols, rows)
    w, h = cols * TILE, rows * TILE
    b, m, gl = look.bark, look.metal, look.glass
    l, g = look.leaf, look.grass

    wall_top = h // 3
    solid(art, 4, wall_top, w - 8, h - wall_top - 4, b, cap=b)
    # pitched roof: two slopes meeting at a ridge, drawn as steps
    ridge = wall_top - 2
    for step in range(ridge - 8, ridge + 1):
        inset = (ridge - step)
        mt.plane(art, 4 + inset, step, w - 8 - inset * 2, 1,
                 m.shade if step % 2 else m.mid)
    art.hline(ridge - 8, 4 + 8, w - 13, m.lit)
    art.hline(ridge, 4, w - 5, blend(m.deep, (0, 0, 0), 0.3))
    # two windows and a door, all still there
    for wx in (10, w - 24):
        art.rect(wx, wall_top + 6, 12, 11, (0, 0, 0))
        art.rect(wx + 1, wall_top + 7, 10, 9, gl.shade)
        art.vline(wx + 6, wall_top + 7, wall_top + 15, b.deep)
        art.hline(wall_top + 11, wx + 1, wx + 10, b.deep)
    dx = w // 2 - 6
    art.rect(dx, h - 22, 12, 18, (0, 0, 0))
    art.rect(dx + 1, h - 21, 10, 17, blend(b.deep, (0, 0, 0), 0.35))
    art.dot(dx + 9, h - 13, m.lit)
    # the ivy: up one corner, across the eaves, and a swag over one window
    for y in range(ridge, h - 4):
        x = 5 + ((y * 3) % 4)
        art.dot(x, y, l.shade if y % 2 else l.mid)
        art.dot(x + 1, y, l.deep)
        if y % 3 == 0:
            art.dot(x + 2, y, l.lit)
    for x in range(6, w - 6, 3):
        art.dot(x, ridge + 1 + (x % 3), l.mid)
        art.dot(x + 1, ridge + 2 + (x % 2), l.deep)
    for x in range(10, 24):
        art.dot(x, wall_top + 6 + ((x * 5) % 3), l.shade)
    for x in range(0, w, 4):
        art.dot((x + 2) % w, h - 5, g.mid)
        art.dot(x, h - 4, g.shade)
    return art


def telly(look: Look, channel: int, cols: int = 2, rows: int = 2) -> Canvas:
    """A television left in the grass, still showing what it is receiving.

    The grove is one town received four ways, and nothing in it ever says so.
    This does: a set someone dumped on a verge, tipped back on its legs, with
    a picture on it that belongs to the channel the player is standing in.
    The chassis is identical on all four -- same bezel, same knobs, same dead
    plastic -- so the only thing that differs is the signal, which is the
    whole claim the world makes about itself.

    Wrecked cars were the first attempt at a per-channel object and they were
    a recolour of one shape.  This is the opposite: one shape, four pictures.
    """
    art = _bedded(turf(look, 0), cols, rows)
    w, h = cols * TILE, rows * TILE
    case, glass, m = look.plastic, look.glass, look.metal
    shell = blend(case.mid, (52, 48, 46), 0.55)

    art.ellipse(w // 2, h - 4, w * 0.36, 3, (0, 0, 0))
    # the box, with the bezel proud of the screen
    solid(art, 3, 6, w - 6, h - 12, mt.Material("case", shell), cap=None)
    art.rect(4, 7, w - 8, h - 14, blend(shell, (255, 255, 255), 0.10))
    sx, sy, sw, sh = 6, 9, w - 19, h - 19
    art.rect(sx - 1, sy - 1, sw + 2, sh + 2, (0, 0, 0))

    if channel == 0:            # the grove: a picture, and it is this town
        art.rect(sx, sy, sw, sh, blend(glass.mid, (40, 60, 50), 0.45))
        art.hline(sy + sh - 4, sx, sx + sw - 1, blend(look.grass.mid, (0, 0, 0), 0.2))
        art.rect(sx + 2, sy + sh - 8, 3, 5, look.bark.shade)     # a mast
        art.rect(sx + sw - 5, sy + sh - 7, 3, 4, look.road.shade)
        art.hline(sy + 1, sx, sx + sw - 1, blend(glass.lit, (0, 0, 0), 0.3))
    elif channel == 1:          # overgrown: the set has been got into
        art.rect(sx, sy, sw, sh, blend(glass.deep, (0, 0, 0), 0.3))
        for n in range(sh):
            art.dot(sx + (n * 5) % sw, sy + n, look.leaf.shade)
            art.dot(sx + (n * 5 + 1) % sw, sy + n, look.leaf.deep)
        art.dot(sx + 2, sy + 2, look.leaf.lit)
        art.dot(sx + sw - 3, sy + sh - 3, look.leaf.lit)
    elif channel == 2:          # off-colour: the picture with the colour gone
        art.rect(sx, sy, sw, sh, (86, 88, 92))
        for index in range(sw // 2):
            band = 60 + index * 14
            art.vline(sx + index * 2, sy, sy + sh - 1,
                      (min(band, 210), min(band, 210), min(band + 4, 214)))
        art.hline(sy + sh // 2, sx, sx + sw - 1, (34, 34, 38))
    else:                       # no signal: it is not receiving anything
        art.rect(sx, sy, sw, sh, (16, 14, 18))
        for y in range(sy, sy + sh):
            for x in range(sx, sx + sw):
                if (x * 7 + y * 13 + (x ^ y)) % 3 == 0:
                    art.dot(x, y, (208, 206, 202) if (x + y) % 2 else (72, 70, 74))
        art.hline(sy + 2, sx, sx + sw - 1, (240, 238, 234))
        art.hline(sy + sh - 4, sx, sx + sw - 1, (160, 158, 156))

    # the control panel: two knobs and a speaker grille, on the right
    px = sx + sw + 2
    art.rect(px, sy, w - px - 4, sh, blend(shell, (0, 0, 0), 0.25))
    art.blob(px + 2, sy + 3, 2, m.shade)
    art.blob(px + 2, sy + 3, 1, m.lit)
    art.blob(px + 2, sy + 8, 2, m.shade)
    for gy in range(sy + 12, sy + sh - 1, 2):
        art.hline(gy, px + 1, w - 6, blend(shell, (0, 0, 0), 0.45))
    # legs, and the grass coming up round them
    art.rect(5, h - 6, 3, 3, blend(shell, (0, 0, 0), 0.5))
    art.rect(w - 8, h - 6, 3, 3, blend(shell, (0, 0, 0), 0.5))
    for x in range(2, w - 2, 3):
        art.dot(x, h - 4 - (x % 2), look.grass.shade)
    return art
