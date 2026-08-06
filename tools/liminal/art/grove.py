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
