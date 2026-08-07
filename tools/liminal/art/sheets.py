"""Per-world chipset assembly.

One world, one idea, committed to completely.  Nothing here tries to be a
building; the pink world is *only* pink brick, the number world is *only*
digits, and neither of them acknowledges that this is strange.

Every world exposes a small shared vocabulary so the map generators can be
reused — ``ground``, ``ground_b``, ``path``, ``glow``, ``void``, the
``shadow_*`` overlays and an animated ``special`` — and then fills the rest of
its sheet with props that exist nowhere else in the game.
"""

from __future__ import annotations

from typing import Callable

from . import chipsets as ct
from . import grove as gv
from . import material as mt
from . import landmarks as lm
from .canvas import Canvas, TRANSPARENT, blend, cooler, outline_in, warmer
from .chipsets import ChipsetBuild, ChipsetBuilder
from .palette import PALETTES, Palette

TILE = ct.TILE


def _reflection(name: str) -> str:
    """Which silhouette stands in this world's mirrors.

    Layers reflect whatever their base world reflects — a channel of the grove
    is still the grove, and a floor of the stairwell is still the stairwell —
    so the portal art stays consistent across a world's own maps.
    """
    base = name.rstrip("012345") or name
    return ct.REFLECTION.get(base, "door")


def _shadows(cb: ChipsetBuilder, pal: Palette) -> None:
    for side in ("top", "left", "right", "bottom"):
        cb.add_upper(f"shadow_{side[0]}", ct.soft_shadow(pal, side))


# The motif each world's boundary walls are built from.  This is the surface
# the player looks at whenever they cannot go somewhere, so it carries more of
# a world's identity than anything they can walk on.
WALL_MOTIF: dict[str, str] = {
    "room": "paper", "nexus": "doors", "pink": "brick", "numbers": "digits",
    "blocks": "blocks", "stairs": "steps", "sand": "strata", "faces": "trunks",
    "hands": "fingers", "checker": "checker", "toys": "toybox", "neon": "neon",
    "umbrellas": "scallops", "stars": "starfield",
    # The grove's boundary is the same canopy on all four channels, received
    # differently: grown shut, stripped bare, or gone altogether.
    "faces2": "thicket", "faces3": "bare", "faces4": "bars",
}


# Where a world's boundary is made of something other than its prop material.
# The forest is the case that matters: its props are brown trunks, but the wall
# containing the player is a solid mass of canopy.
WALL_COLORS: dict[str, dict] = {
    "faces": {"base": (74, 118, 76), "light": (104, 152, 100),
              "dark": (38, 66, 46), "accent": (146, 186, 132)},
    # deeper, wetter, and with the light no longer reaching the ground
    "faces2": {"base": (52, 104, 58), "light": (82, 140, 76),
               "dark": (20, 46, 30), "accent": (172, 206, 122)},
    # no leaves left: branch structure in front of an overcast sky
    "faces3": {"base": (120, 122, 118), "light": (188, 192, 192),
               "dark": (68, 70, 72), "accent": (216, 220, 222)},
    # not made of anything — where the picture stops carrying the town
    "faces4": {"base": (188, 52, 50), "light": (240, 236, 226),
               "dark": (28, 18, 22), "accent": (240, 236, 226)},
}


def _basics(cb: ChipsetBuilder, pal: Palette, ground: Canvas,
            ground_b: Canvas | None = None, *, world: str = "") -> None:
    cb.add("ground", ground)
    cb.add("ground_b", ground_b if ground_b is not None
           else ct.soft_ground(pal.ground_b, pal.ground, 0.3))
    cb.add("path", ct.path_ground(pal))
    cb.add("glow", ct.glow_pool(pal))
    cb.add("void", ct.void_tile(pal), passable=False)
    motif = WALL_MOTIF.get(world or cb.name, "brick")
    colors = WALL_COLORS.get(world or cb.name, {})
    cb.add("wall_core", ct.wall_band(pal, motif, **colors), passable=False)
    cb.add("wall_face", ct.wall_band(pal, motif, face=True, **colors),
           passable=False)


# Three ground marks per world.  Nothing shared: the litter of one dream must
# never be mistakable for the litter of another, and on a looping map these
# double as the small landmarks that let it lie about its size.
DECALS: dict[str, list[tuple[str, str]]] = {
    "room":      [("crack", "form_dark"), ("pebble", "accent"), ("dropped", "form")],
    "nexus":     [("ring", "accent"), ("spark", "accent"), ("prints", "form")],
    "pink":      [("loose_brick", "form_light"), ("crack", "form_dark"),
                  ("drainhole", "form_dark")],
    "numbers":   [("point", "form"), ("tally", "form_dark"), ("equals", "accent")],
    "blocks":    [("peg", "form_dark"), ("scribble", "accent"), ("marble", "form")],
    "stairs":    [("step_shard", "form"), ("rope", "form_dark"),
                  ("fallen_star", "accent")],
    "sand":      [("bone", "form"), ("prints", "form_dark"), ("halfring", "accent")],
    "faces":     [("leaves", "accent_soft"), ("sigil", "form_dark"),
                  ("ringcaps", "accent")],
    "hands":     [("fingerprint", "form_dark"), ("pebble", "form"),
                  ("ring", "accent")],
    "checker":   [("offsquare", "accent"), ("crack", "form_dark"),
                  ("pebble", "form")],
    "toys":      [("marble", "accent"), ("jackmark", "form_dark"),
                  ("shaving", "form")],
    "neon":      [("glyph", "form"), ("spark", "accent"), ("scanline", "form_dark")],
    "umbrellas": [("puddle", "accent_soft"), ("dropped", "form"),
                  ("waterring", "accent")],
    "stars":     [("constellation", "accent"), ("ripple", "accent_soft"),
                  ("fallen_star", "accent")],
    # What is lying on the ground is the fastest way to tell one channel from
    # another before the player has consciously noticed the colour changed.
    "faces2":    [("creeper", "accent_soft"), ("seedhead", "accent"),
                  ("windfall", "form_light")],
    "faces3":    [("ashfall", "accent"), ("chalkline", "form_dark"),
                  ("tapeloop", "form")],
    "faces4":    [("colourbar", "accent"), ("cornerpip", "form_light"),
                  ("tone", "accent_soft")],
}


# The floor patterns each world is carpeted in, and the murals painted on it.
# Density is what makes a dream floor worth looking at; composition is what
# keeps it from being noise.  Both lists are per-world and share nothing.
PATTERNS: dict[str, list[str]] = {
    "room":      ["weave", "grid", "dots"],
    "nexus":     ["concentric", "dots", "grid"],
    "pink":      ["square_frame", "weave", "diamond", "grid"],
    "numbers":   ["grid", "tick", "square_frame", "cross"],
    "blocks":    ["square_frame", "dots", "cross", "weave"],
    "stairs":    ["chevron", "stripes", "grid"],
    "sand":      ["stripes", "dots", "weave"],
    "faces":     ["bloom", "dots", "concentric"],
    "hands":     ["concentric", "diamond", "dots"],
    "checker":   ["grid", "square_frame", "cross", "diamond"],
    "toys":      ["dots", "bloom", "square_frame", "chevron"],
    "neon":      ["square_frame", "concentric", "stripes", "cross", "diamond",
                  "grid"],
    "umbrellas": ["chevron", "concentric", "weave"],
    "stars":     ["dots", "diamond", "concentric"],
    "faces2":    ["bloom", "weave", "dots"],
    "faces3":    ["grid", "tick", "stripes"],
    "faces4":    ["stripes", "grid", "cross", "square_frame"],
}

MURALS: dict[str, list[str]] = {
    "room": ["rings"], "nexus": ["rings", "eye"],
    "pink": ["rings", "lattice"], "numbers": ["grid", "rings"],
    "blocks": ["sun", "grid"], "stairs": ["spiral", "lattice"],
    "sand": ["rings", "sun"], "faces": ["eye", "sun"],
    "hands": ["hand", "rings"], "checker": ["grid", "star"],
    "toys": ["sun", "star"], "neon": ["eye", "spiral", "star"],
    "umbrellas": ["waves", "rings"], "stars": ["star", "waves"],
    "faces2": ["sun", "rings"], "faces3": ["grid", "rings"],
    "faces4": ["eye", "star", "grid"],
}


# What moves, per world.  Four animated tiles each: three block C strips and
# one adjustable-speed autotile.  A dream that holds perfectly still reads as
# a screenshot.
ANIMATION: dict[str, tuple[tuple[str, str, str], tuple[str, int]]] = {
    "room":      (("pulse", "scan", "pulse"), ("pulse", 14)),
    "nexus":     (("pulse", "pulse", "scan"), ("pulse", 12)),
    "pink":      (("pulse", "crawl", "checkerflip"), ("pulse", 12)),
    "numbers":   (("scan", "pulse", "crawl"), ("scan", 8)),
    "blocks":    (("pulse", "checkerflip", "crawl"), ("checkerflip", 10)),
    "stairs":    (("crawl", "pulse", "scan"), ("crawl", 7)),
    "sand":      (("pulse", "scan", "pulse"), ("pulse", 16)),
    "faces":     (("pulse", "crawl", "pulse"), ("pulse", 13)),
    "hands":     (("pulse", "pulse", "scan"), ("pulse", 15)),
    "checker":   (("checkerflip", "pulse", "scan"), ("checkerflip", 9)),
    "toys":      (("pulse", "checkerflip", "crawl"), ("pulse", 10)),
    # the neon world moves fastest and hardest, because that is its whole point
    "neon":      (("pulse", "crawl", "scan"), ("crawl", 5)),
    "umbrellas": (("crawl", "pulse", "scan"), ("crawl", 11)),
    "stars":     (("pulse", "crawl", "pulse"), ("pulse", 9)),
    # A channel's animation is its reception.  Growth crawls; a failing signal
    # scans slowly and unevenly; a dead one scans as fast as the hardware can.
    "faces2":    (("crawl", "pulse", "crawl"), ("crawl", 15)),
    "faces3":    (("scan", "pulse", "scan"), ("scan", 10)),
    "faces4":    (("scan", "checkerflip", "scan"), ("scan", 4)),
}


def _animate(cb: ChipsetBuilder, pal: Palette, world: str) -> None:
    strips, (flow_kind, speed) = ANIMATION[world]
    for index, kind in enumerate(strips):
        cb.add_animated(f"anim_{index}", ct.glow_frames(pal, kind))
    cb.add_flow(ct.glow_frames(pal, flow_kind), speed=speed)


def _decals(cb: ChipsetBuilder, pal: Palette, world: str, ground: Canvas) -> None:
    for index, (motif, color_field) in enumerate(DECALS[world]):
        cb.add(f"decal_{index}", ct.decal(ground, motif, getattr(pal, color_field)))
    # dense carpet patterns
    for index, kind in enumerate(PATTERNS[world]):
        ink = pal.accent if index % 2 == 0 else pal.accent_soft
        back = pal.ground if index % 3 else pal.ground_b
        cb.add(f"pattern_{index}", ct.pattern_tile(pal, kind, ink, back))
    # the big paintings on the floor
    for index, kind in enumerate(MURALS[world]):
        cb.add_object(f"mural_{index}",
                      ct.floor_mural(pal, kind, 4, 4),
                      solid="none")
    # a second and third wall pattern, so boundaries are not one note
    motif = WALL_MOTIF.get(world, "brick")
    alt = {"brick": "strata", "digits": "grid", "blocks": "checker",
           "steps": "brick", "strata": "brick", "trunks": "strata",
           "fingers": "strata", "checker": "brick", "toybox": "checker",
           "neon": "checker", "scallops": "strata", "starfield": "checker",
           "paper": "strata", "doors": "brick", "thicket": "trunks",
           "bare": "strata", "bars": "checker", "rings": "checker",
           "coil": "strata", "teeth": "checker", "rays": "starfield",
           "cumulus": "scallops", "cornice": "strata", "lockers": "checker",
           "cards": "grid"}.get(motif, "brick")
    # The grove's second boundary was a brown strata band -- the generic
    # fallback, because the alt table had no opinion about a world whose
    # motif is "trunks".  Two thousand six hundred tiles of masonry in a map
    # called the grove.  All four channels get massed hedge instead, in their
    # own reception's colours.
    if world in gv.LOOKS:
        look = gv.LOOKS[world]
        # Built from the same base the primary wall uses, so a channel's
        # boundary is one colour whatever tile of it you are looking at.
        tint = WALL_COLORS.get(world, {}).get("base")
        cb.add("wall_alt", gv.hedge(look, 0, tint), passable=False)
        cb.add("wall_alt_face", gv.hedge(look, 1, tint), passable=False)
    else:
        cb.add("wall_alt", ct.wall_band(pal, alt, accent=pal.accent_soft),
               passable=False)
        cb.add("wall_alt_face", ct.wall_band(pal, alt, face=True,
                                             accent=pal.accent_soft),
               passable=False)


# The unique structures each world is remembered for.  They go on the upper
# tile layer, which sits almost empty at ten of a hundred and forty-four slots
# while the lower layer is nearly full — and upper tiles draw over the floor
# with the player in front of them, which is what a tall thing you walk past
# needs.  Nothing here is repeated between worlds.
LANDMARKS: dict[str, list[tuple[str, object, dict]]] = {}


def _landmarks(cb: ChipsetBuilder, pal: Palette, world: str) -> None:
    for name, maker, kwargs in LANDMARKS.get(world, []):
        art = maker(pal, **kwargs)
        cb.add_object(f"mark_{name}", art, solid="bottom2", upper=True)


def _finish(cb: ChipsetBuilder, ground: Canvas) -> ChipsetBuild:
    cb.fill_autotile_area(ground)
    return cb.finish()


# --- the two places that are not dreams --------------------------------------

def _room_materials() -> dict[str, "mt.Material"]:
    """One palette shared by the room and the balcony it opens onto.

    Two places that are the same flat need the same substances, or stepping
    outside reads as loading a different game.  The concrete, the sky and the
    city are the only things the balcony adds.
    """
    return {
        # the building itself, in three substances so a cut through a wall
        # shows layers rather than a border
        "plaster": mt.Material("plaster", (98, 94, 116), grain="v"),
        "core": mt.Material("core", (74, 76, 92)),
        "skin": mt.Material("skin", (48, 48, 64)),
        # the room
        "floor": mt.Material("floor", (80, 58, 50)),
        "wood": mt.Material("wood", (94, 68, 54)),
        "linen": mt.Material("linen", (188, 188, 196)),
        "cloth": mt.Material("cloth", (56, 86, 98)),
        "lamp": mt.Material("lamp", (204, 164, 106)),
        "metal": mt.Material("metal", (96, 100, 112)),
        "screen": mt.Material("screen", (60, 76, 80)),
        "leaf": mt.Material("leaf", (70, 98, 68)),
        # outside
        "sky": mt.Material("sky", (98, 100, 130)),
        "far": mt.Material("far", (64, 64, 92)),
        "near": mt.Material("near", (46, 44, 66)),
        "concrete": mt.Material("concrete", (92, 90, 100)),
    }


def _wall_cut(mats: dict, side: str) -> Canvas:
    """One tile of a wall seen in section: skin, then core.

    The room is a hole cut in a building, and this is the cut.  Yume Nikki's
    interiors do the same thing and it is the single cheapest way to make a
    top-down room read as having thickness — the border is not a texture, it
    is the *inside* of the wall, and the layers are what say so.
    """
    core, skin = mats["core"], mats["skin"]
    art = Canvas(TILE, TILE, core.mid)
    mt.bricks(art, 0, 0, TILE, TILE, core, course=4, stagger=True)
    if side == "n":                     # the far wall: skin above, core below
        mt.plane(art, 0, 0, TILE, 6, skin.shade)
        art.hline(6, 0, TILE - 1, skin.deep)
        art.hline(7, 0, TILE - 1, core.lit)
    elif side == "s":                   # the near wall: core above, skin below
        mt.plane(art, 0, 10, TILE, 6, skin.shade)
        art.hline(9, 0, TILE - 1, skin.deep)
        art.hline(8, 0, TILE - 1, core.lit)
    elif side == "w":
        mt.plane(art, 0, 0, 6, TILE, skin.shade)
        art.vline(6, 0, TILE - 1, skin.deep)
        art.vline(7, 0, TILE - 1, core.lit)
    elif side == "e":
        mt.plane(art, 10, 0, 6, TILE, skin.shade)
        art.vline(9, 0, TILE - 1, skin.deep)
        art.vline(8, 0, TILE - 1, core.lit)
    return art


def _wall_face(mats: dict, side: str, low: bool = False) -> Canvas:
    """The plaster face of a wall, turned toward the room.

    Light comes from the upper left for the whole game, so the far wall is
    brightest at the top and the west-facing plaster is the one in shadow.
    Everything here is two flat values with a dithered seam between them —
    there is no gradient anywhere on a wall.
    """
    pl = mats["plaster"]
    art = Canvas(TILE, TILE, pl.mid)
    if side == "n":
        if low:
            mt.plane(art, 0, 0, TILE, 10, pl.mid)
            mt.seam(art, 0, 10, TILE, 3, pl.mid, pl.shade)
            mt.plane(art, 0, 13, TILE, 3, pl.shade)
        else:
            mt.plane(art, 0, 0, TILE, 2, pl.hot)
            mt.seam(art, 0, 2, TILE, 3, pl.hot, pl.lit)
            mt.plane(art, 0, 5, TILE, 11, pl.lit)
    elif side == "s":
        if low:
            mt.plane(art, 0, 0, TILE, 11, pl.mid)
            mt.seam(art, 0, 11, TILE, 3, pl.mid, pl.lit)
            mt.plane(art, 0, 14, TILE, 2, pl.lit)
        else:
            mt.plane(art, 0, 0, TILE, 4, pl.shade)  # the floor join, in shadow
            mt.seam(art, 0, 4, TILE, 3, pl.shade, pl.mid)
            mt.plane(art, 0, 7, TILE, 9, pl.mid)
    elif side == "w":                              # faces east: lit
        mt.plane(art, 0, 0, 4, TILE, pl.shade)
        mt.seam(art, 4, 0, 3, TILE, pl.shade, pl.mid, vertical=True)
        mt.plane(art, 7, 0, 9, TILE, pl.mid)
    elif side == "e":                              # faces west: in shadow
        mt.plane(art, 0, 0, 9, TILE, pl.mid)
        mt.seam(art, 9, 0, 3, TILE, pl.mid, pl.shade, vertical=True)
        mt.plane(art, 12, 0, 4, TILE, pl.shade)
    for x in range(0, TILE, 8):                    # faint vertical panelling
        art.vline(x, 0, TILE - 1, pl.shade)
    return art


def _planks(mats: dict, offset: int) -> Canvas:
    """Floorboards: four to a tile, with the butt joints staggered.

    Two planks per tile is a scaled-up texture and looks like it; four with
    the ends broken in different places reads as a floor.  Every board has its
    lit lip on the side the light comes from and its groove on the other.
    """
    fl = mats["floor"]
    art = Canvas(TILE, TILE, fl.mid)
    mt.plane(art, 0, 0, TILE, TILE, fl.mid)
    for top in range(0, TILE, 8):               # two wide boards to a tile
        art.hline(top, 0, TILE - 1, fl.shade)   # the groove between them
        art.hline(top + 1, 0, TILE - 1, fl.lit)  # and the lit lip of the next
        art.hline(top + 5, 0, TILE - 1, fl.shade)   # the grain within a board
    if offset:                                  # a butt joint, but rarely:
        art.vline(offset % TILE, 0, TILE - 1, fl.shade)   # one tile in six
    return art


def build_room() -> ChipsetBuild:
    """The room you wake up in, built on the shared material system.

    The least dreamlike place in the game, and the one that sets the style for
    everything remastered after it.  Every surface here is a Material — five
    values from one base, shadows keeping their hue and pushed cool, highlights
    warm and desaturating — laid down as flat planes with a two-pixel dithered
    seam where they meet.  No gradients, no noise, no black outlines.

    The walls are the load-bearing idea.  They are not a border pattern: they
    are a section through a building, drawn as skin, core and plaster face, so
    that standing in the middle of the floor you can see how thick the walls
    are on every side.  Furniture is drawn with a visible front, lit from the
    same upper-left as the walls, so the whole room agrees about where it is.
    """
    pal = PALETTES["room"]
    cb = ChipsetBuilder("room", pal)
    mats = _room_materials()
    PLASTER, CORE = mats["plaster"], mats["core"]
    FLOOR, WOOD = mats["floor"], mats["wood"]
    LINEN, CLOTH = mats["linen"], mats["cloth"]
    LAMP, METAL = mats["lamp"], mats["metal"]
    SCREEN, LEAF = mats["screen"], mats["leaf"]
    SKY, FAR = mats["sky"], mats["far"]

    # --- the floor
    floor = _planks(mats, 0)
    cb.add("ground", floor)
    cb.add("ground_b", _planks(mats, 9))
    cb.add("path", _planks(mats, 5))

    RUG = mt.Material("rug", (88, 54, 58))
    rug = Canvas(TILE, TILE, RUG.mid)
    mt.weave(rug, 0, 0, TILE, TILE, RUG, pitch=4)
    cb.add("rug", rug)
    rug_edge = rug.copy()
    mt.plane(rug_edge, 0, 0, TILE, 2, RUG.lit)
    cb.add("rug_edge", rug_edge)

    glow = _planks(mats, 0)
    mt.seam(glow, 0, 0, TILE, TILE, blend(FLOOR.mid, LAMP.mid, 0.34), FLOOR.mid)
    cb.add("glow", glow)
    cb.add("void", ct.flat(mats["skin"].deep), passable=False)
    # Outside the room there is nothing, and nothing is black.  The map is
    # exactly one screen, so this is what fills the corners rather than the
    # engine's backdrop showing through.
    cb.add("black", ct.flat((0, 0, 0)), passable=False)

    # --- the walls, in section
    for side in ("n", "s", "w", "e"):
        cb.add(f"cut_{side}", _wall_cut(mats, side), passable=False)
        cb.add(f"face_{side}", _wall_face(mats, side), passable=False)
    cb.add("face_n_low", _wall_face(mats, "n", low=True), passable=False)

    # --- the bed.  White pillow: it is the one thing in a dark room that has
    # to be legible from across it.
    bed = ct._canvas(2, 3)
    mt.plane(bed, 2, 4, 28, 42, WOOD.mid)
    mt.plane(bed, 2, 4, 28, 2, WOOD.lit)
    mt.plane(bed, 2, 43, 28, 3, WOOD.deep)
    mt.plane(bed, 3, 1, 26, 7, WOOD.shade)              # headboard
    mt.sheen(bed, 4, 2, 24, 4, WOOD)
    mt.plane(bed, 4, 9, 24, 12, LINEN.lit)              # pillow
    mt.plane(bed, 4, 9, 24, 3, LINEN.hot)
    mt.seam(bed, 4, 18, 24, 3, LINEN.lit, LINEN.mid)
    bed.hline(20, 4, 27, LINEN.shade)
    mt.plane(bed, 4, 21, 24, 21, CLOTH.mid)             # blanket
    mt.plane(bed, 4, 21, 24, 3, CLOTH.lit)
    mt.seam(bed, 4, 34, 24, 4, CLOTH.mid, CLOTH.shade)
    mt.plane(bed, 4, 38, 24, 4, CLOTH.shade)
    for fold in (10, 16, 22):                           # folds, not noise
        bed.vline(4 + fold, 24, 37, CLOTH.shade)
        bed.vline(5 + fold, 24, 37, CLOTH.lit)
    cb.add_object("bed", bed, solid="all")

    # --- the desk
    # Everything that stands against a wall is drawn flush to the top of its
    # own canvas.  Half a tile of transparent padding is invisible in the
    # sheet and reads, in the room, as furniture hovering an inch off the
    # skirting — which is what the first pass at this room did on every piece.
    desk = ct._canvas(2, 2)
    mt.plane(desk, 1, 0, 30, 8, WOOD.shade)             # the back panel
    mt.plane(desk, 1, 6, 30, 7, WOOD.mid)               # the top
    mt.plane(desk, 1, 6, 30, 2, WOOD.lit)
    mt.plane(desk, 1, 12, 30, 2, WOOD.deep)
    mt.plane(desk, 2, 14, 28, 9, WOOD.shade)            # the drawer front
    mt.plane(desk, 3, 15, 26, 7, WOOD.mid)
    desk.hline(19, 12, 20, WOOD.lit)                    # its handle
    for lx in (3, 26):
        mt.plane(desk, lx, 23, 3, 8, WOOD.shade)
        desk.vline(lx, 23, 30, WOOD.mid)
    cb.add_object("desk", desk, solid="bottom")

    # The nightstand the lamp stands beside.
    stand = ct._canvas(1, 2)
    mt.plane(stand, 1, 0, 14, 6, WOOD.shade)
    mt.plane(stand, 0, 4, 16, 5, WOOD.mid)              # the top
    mt.plane(stand, 0, 4, 16, 2, WOOD.lit)
    mt.plane(stand, 1, 9, 14, 11, WOOD.shade)           # the drawer
    mt.plane(stand, 2, 10, 12, 4, WOOD.mid)
    stand.hline(12, 5, 10, WOOD.lit)
    mt.plane(stand, 2, 15, 12, 5, WOOD.deep)
    for lx in (2, 12):
        mt.plane(stand, lx, 20, 2, 6, WOOD.shade)
    cb.add_object("nightstand", stand, solid="all")

    # --- the shelf
    shelf = ct._canvas(2, 3)
    mt.plane(shelf, 2, 2, 28, 44, WOOD.shade)
    mt.plane(shelf, 2, 2, 28, 2, WOOD.lit)
    mt.plane(shelf, 3, 4, 26, 41, WOOD.deep)
    for sy in (5, 19, 33):
        for index, bx in enumerate(range(5, 27, 4)):
            book = mt.Material("book", ((124, 66, 64), (74, 90, 118),
                                        (96, 100, 68), (108, 88, 60))[index % 4])
            tall = 11 - (index % 3)
            mt.plane(shelf, bx, sy + (11 - tall), 3, tall, book.mid)
            shelf.vline(bx, sy + (11 - tall), sy + 10, book.lit)
            shelf.vline(bx + 2, sy + (11 - tall), sy + 10, book.shade)
        mt.plane(shelf, 3, sy + 11, 26, 3, WOOD.mid)    # the shelf board
        mt.plane(shelf, 3, sy + 11, 26, 1, WOOD.lit)
    cb.add_object("shelf", shelf, solid="all")

    # --- the wardrobe
    wardrobe = ct._canvas(2, 3)
    mt.plane(wardrobe, 1, 1, 30, 46, WOOD.shade)
    mt.plane(wardrobe, 1, 1, 30, 3, WOOD.lit)
    mt.plane(wardrobe, 1, 44, 30, 3, WOOD.deep)
    for ox in (3, 17):
        mt.plane(wardrobe, ox, 5, 12, 38, WOOD.mid)
        mt.sheen(wardrobe, ox, 5, 12, 9, WOOD)
        mt.seam(wardrobe, ox, 36, 12, 4, WOOD.mid, WOOD.shade)
    wardrobe.vline(15, 3, 44, WOOD.deep)
    wardrobe.vline(16, 3, 44, WOOD.lit)
    for hy in range(22, 28):
        wardrobe.dot(13, hy, METAL.lit)
        wardrobe.dot(18, hy, METAL.mid)
    cb.add_object("wardrobe", wardrobe, solid="all")

    # --- the television, in the new style: a box with a front, not a decal
    tv = ct._canvas(2, 2)
    CASE = mt.Material("case", (76, 68, 64))
    mt.plane(tv, 1, 4, 30, 24, CASE.mid)
    mt.plane(tv, 1, 4, 30, 3, CASE.lit)                 # the lit top edge
    mt.plane(tv, 1, 26, 30, 2, CASE.deep)
    mt.plane(tv, 3, 8, 19, 16, SCREEN.deep)             # the tube's bezel
    mt.plane(tv, 4, 9, 17, 14, SCREEN.mid)
    mt.plane(tv, 4, 9, 17, 4, SCREEN.lit)               # the reflection in it
    mt.seam(tv, 4, 13, 17, 3, SCREEN.lit, SCREEN.mid)
    for gy in range(10, 23, 3):                         # scanlines, structured
        tv.hline(gy, 5, 20, SCREEN.shade)
    mt.plane(tv, 24, 9, 5, 14, CASE.shade)              # the dials
    tv.blob(26, 13, 1.8, METAL.lit)
    tv.blob(26, 19, 1.8, METAL.mid)
    for fx in (4, 25):                                  # feet
        mt.plane(tv, fx, 28, 3, 3, CASE.deep)
    cb.add_object("television", tv, solid="all")

    # --- the small things
    plant = ct._canvas(1, 2)
    POT = mt.Material("pot", (120, 76, 58))
    mt.plane(plant, 3, 20, 10, 11, POT.mid)
    mt.plane(plant, 3, 20, 10, 2, POT.lit)
    mt.plane(plant, 4, 29, 8, 2, POT.deep)
    for dx, dy, ln in ((-4, 6, 8), (0, 2, 11), (4, 5, 9), (-2, 9, 6),
                       (3, 10, 6)):
        plant.line(8, 20, 8 + dx, 20 - dy - ln + 4, LEAF.mid)
        plant.blob(8 + dx, 20 - dy - ln + 5, 2.4, LEAF.lit)
    cb.add_object("plant", plant, solid="all")

    # A standing lamp, flush to the wall.  It does not light the floor: a pool
    # of paint under a lamp is a lie the tile grid cannot keep, and it looked
    # like a stain rather than like light.  The shade is lit and everything
    # else in the room is lit from the upper left, and that is the whole of it.
    #
    # The shade sits a few pixels down and the column under it is wide enough
    # to be read at this size.  Drawn hard against the top of the canvas with
    # a two-pixel stem it looked like it was hanging from nothing.
    lamp = ct._canvas(1, 2)
    mt.plane(lamp, 1, 3, 14, 11, LAMP.mid)              # the shade
    mt.plane(lamp, 1, 3, 14, 3, LAMP.hot)
    mt.seam(lamp, 1, 11, 14, 3, LAMP.mid, LAMP.shade)
    lamp.vline(1, 3, 13, LAMP.lit)
    lamp.vline(14, 3, 13, LAMP.shade)
    lamp.hline(2, 2, 13, LAMP.shade)                    # the top rim
    mt.plane(lamp, 6, 14, 4, 13, METAL.mid)             # the column
    lamp.vline(6, 14, 26, METAL.lit)
    lamp.vline(9, 14, 26, METAL.deep)
    mt.plane(lamp, 3, 27, 10, 4, METAL.shade)           # the foot
    mt.plane(lamp, 3, 27, 10, 1, METAL.lit)
    mt.plane(lamp, 4, 30, 8, 1, METAL.deep)
    cb.add_object("lamp_lit", lamp, solid="all", upper=True)

    clock = ct._canvas(1, 2)
    mt.plane(clock, 2, 10, 12, 16, WOOD.shade)
    mt.plane(clock, 2, 10, 12, 2, WOOD.lit)
    mt.plane(clock, 3, 12, 10, 12, WOOD.deep)
    clock.blob(8, 18, 4.4, LINEN.lit)
    clock.blob(8, 18, 3.2, LINEN.hot)
    clock.vline(8, 15, 18, WOOD.deep)
    clock.hline(18, 8, 11, WOOD.deep)
    cb.add_object("clock", clock, solid="none", upper=True, above=True)

    bin_ = ct._canvas(1, 1)
    mt.plane(bin_, 4, 5, 8, 11, METAL.mid)
    mt.plane(bin_, 4, 5, 8, 2, METAL.lit)
    mt.plane(bin_, 5, 14, 6, 2, METAL.deep)
    cb.add_object("bin", bin_, solid="all")

    slippers = ct._canvas(1, 1)
    for sx in (2, 9):
        mt.plane(slippers, sx, 9, 5, 5, CLOTH.mid)
        mt.plane(slippers, sx, 9, 5, 2, CLOTH.lit)
    cb.add_object("slippers", slippers, solid="none", upper=True)

    # the mirror in the room is the same object as every portal in the game
    cb.add_object("mirror", ct.door_frame(pal, 2, 3, reflect="bed"),
                  solid="all")

    # --- what is set into the far wall.  All three of these are two tiles
    # tall so they sit exactly on the plaster and never over the wall's cut,
    # which is what makes them read as being *in* the wall.
    door = ct._canvas(2, 2)
    mt.plane(door, 0, 0, 32, 32, WOOD.shade)            # the architrave
    mt.plane(door, 0, 0, 32, 2, WOOD.lit)
    mt.plane(door, 3, 2, 26, 30, WOOD.deep)             # the reveal
    mt.plane(door, 5, 3, 22, 29, WOOD.mid)              # the leaf
    mt.plane(door, 5, 3, 22, 2, WOOD.lit)
    for py, ph in ((7, 9), (19, 9)):                    # two recessed panels
        mt.plane(door, 8, py, 16, ph, WOOD.shade)
        mt.plane(door, 9, py + 1, 14, ph - 2, WOOD.mid)
        door.hline(py, 8, 23, WOOD.deep)
        door.hline(py + ph - 1, 8, 23, WOOD.lit)
    door.blob(24, 17, 1.9, METAL.lit)                   # the handle
    cb.add_object("door", door, solid="all")

    window = ct._canvas(2, 2)
    mt.plane(window, 0, 0, 32, 32, WOOD.shade)
    mt.plane(window, 0, 0, 32, 2, WOOD.lit)
    mt.plane(window, 3, 3, 26, 24, SKY.shade)
    mt.plane(window, 3, 3, 26, 9, SKY.mid)              # sky in the top half
    mt.seam(window, 3, 12, 26, 3, SKY.mid, SKY.shade)
    mt.plane(window, 3, 19, 26, 8, FAR.mid)             # the city in the low
    for bx, bh in ((4, 6), (9, 8), (15, 5), (21, 7), (26, 4)):
        mt.plane(window, bx, 27 - bh, 3, bh, FAR.shade)
        window.dot(bx + 1, 27 - bh + 2, LAMP.shade)
    window.vline(15, 3, 26, WOOD.mid)                   # glazing bars
    window.hline(14, 3, 28, WOOD.mid)
    mt.plane(window, 1, 27, 30, 4, WOOD.mid)            # the sill
    mt.plane(window, 1, 27, 30, 1, WOOD.hot)
    cb.add_object("window", window, solid="all")

    slider = ct._canvas(3, 2)
    mt.plane(slider, 0, 0, 48, 32, METAL.shade)         # aluminium frame
    mt.plane(slider, 0, 0, 48, 2, METAL.lit)
    mt.plane(slider, 2, 2, 44, 28, METAL.deep)
    for ox in (3, 24):                                  # two panes
        mt.plane(slider, ox, 3, 21, 26, SKY.shade)
        mt.plane(slider, ox, 3, 21, 10, SKY.mid)
        mt.seam(slider, ox, 13, 21, 3, SKY.mid, SKY.shade)
        mt.plane(slider, ox, 22, 21, 7, FAR.mid)
        for bx in range(ox + 2, ox + 20, 5):
            mt.plane(slider, bx, 22, 3, 7, FAR.shade)
            slider.dot(bx + 1, 25, LAMP.shade)
        slider.vline(ox, 3, 28, METAL.mid)              # the leading edge
    mt.plane(slider, 23, 2, 2, 28, METAL.mid)           # where they overlap
    slider.vline(22, 2, 29, METAL.deep)
    mt.plane(slider, 1, 29, 46, 3, METAL.mid)           # the track
    slider.hline(29, 1, 46, METAL.lit)
    cb.add_object("slider", slider, solid="all")

    _shadows(cb, pal)
    _landmarks(cb, pal, "room")
    _animate(cb, pal, "room")
    _decals(cb, pal, "room", floor)
    return _finish(cb, floor)


def build_hall() -> ChipsetBuild:
    """The corridor outside the room, and every floor of the building.

    One chipset for the whole block.  A building whose floors are each drawn
    from their own art is a set of unrelated rooms with a number written on
    them; a building whose floors are the same corridor in different light is
    a building.  What changes between floors is the grading, the fittings that
    have survived, and how much of the light still works.

    The materials are the room's own — the same plaster, the same section
    through a wall — because you are meant to walk out of your own door and
    recognise the substance of the place.  What is different is the floor:
    the flat has boards and the corridor has contract tile, which is the
    cheapest possible way to say that one of them is yours.
    """
    pal = PALETTES["room"]
    cb = ChipsetBuilder("hall", pal)
    mats = _room_materials()
    PLASTER, CORE = mats["plaster"], mats["core"]
    WOOD, METAL = mats["wood"], mats["metal"]
    LAMP, LEAF = mats["lamp"], mats["leaf"]
    SKY = mats["sky"]

    TILEFLOOR = mt.Material("tilefloor", (84, 80, 88))
    CARPET = mt.Material("carpet", (86, 58, 62))

    # --- the floor: contract tile, laid in a grid, with the grout a value
    # down.  Institutional on purpose.
    def _lino(shift: int) -> Canvas:
        art = Canvas(TILE, TILE, TILEFLOOR.mid)
        mt.tiles(art, 0, 0, TILE, TILE, TILEFLOOR, size=8)
        if shift:
            mt.seam(art, 0, shift, TILE, 3, TILEFLOOR.mid, TILEFLOOR.shade)
        return art

    lino = _lino(0)
    cb.add("ground", lino)
    cb.add("ground_b", _lino(6))
    cb.add("path", _lino(11))
    cb.add("void", ct.flat(mats["skin"].deep), passable=False)
    cb.add("black", ct.flat((0, 0, 0)), passable=False)

    # the runner down the middle of it, which is the only soft thing here
    runner = Canvas(TILE, TILE, CARPET.mid)
    mt.weave(runner, 0, 0, TILE, TILE, CARPET, pitch=4)
    cb.add("runner", runner)
    runner_w = runner.copy()
    mt.plane(runner_w, 0, 0, 2, TILE, CARPET.shade)
    cb.add("runner_w", runner_w)
    runner_e = runner.copy()
    mt.plane(runner_e, TILE - 2, 0, 2, TILE, CARPET.shade)
    cb.add("runner_e", runner_e)

    # --- the walls, in section, exactly as the room's are
    for side in ("n", "s", "w", "e"):
        cb.add(f"cut_{side}", _wall_cut(mats, side), passable=False)
        cb.add(f"face_{side}", _wall_face(mats, side), passable=False)
    cb.add("face_n_low", _wall_face(mats, "n", low=True), passable=False)
    cb.add("face_s_low", _wall_face(mats, "s", low=True), passable=False)

    # --- a flat's front door.  Everything about it says somebody lives here
    # and nothing about it opens: five panels, a spyhole, a number plate and
    # a mat that has not been shaken out.
    def _flat_door(number: bool) -> Canvas:
        art = ct._canvas(2, 2)
        mt.plane(art, 0, 0, 32, 32, WOOD.deep)              # the architrave
        mt.plane(art, 0, 0, 32, 2, WOOD.shade)
        mt.plane(art, 2, 2, 28, 30, WOOD.shade)             # the reveal
        mt.plane(art, 4, 3, 24, 29, WOOD.mid)               # the leaf
        mt.plane(art, 4, 3, 24, 2, WOOD.lit)
        for py, ph in ((6, 8), (16, 6), (24, 6)):
            mt.plane(art, 7, py, 18, ph, WOOD.shade)
            mt.plane(art, 8, py + 1, 16, ph - 2, WOOD.mid)
            art.hline(py, 7, 24, WOOD.deep)
            art.hline(py + ph - 1, 7, 24, WOOD.lit)
        art.blob(16, 5, 1.4, METAL.deep)                    # the spyhole
        art.blob(24, 15, 1.8, METAL.lit)                    # the handle
        if number:
            mt.plane(art, 12, 1, 8, 4, METAL.shade)         # the number plate
            mt.plane(art, 12, 1, 8, 1, METAL.lit)
        return art

    cb.add_object("flat_door", _flat_door(True), solid="all")
    cb.add_object("flat_door_plain", _flat_door(False), solid="all")

    # --- the lift.  It has a call button and an indicator and it is not
    # coming; the indicator is the joke and it is only told once.
    lift = ct._canvas(2, 2)
    mt.plane(lift, 0, 0, 32, 32, METAL.deep)
    mt.plane(lift, 1, 1, 30, 30, METAL.shade)
    mt.plane(lift, 3, 4, 26, 27, METAL.mid)                 # the two leaves
    mt.plane(lift, 3, 4, 26, 2, METAL.lit)
    lift.vline(15, 4, 30, METAL.deep)
    lift.vline(16, 4, 30, METAL.lit)
    for gy in range(8, 30, 4):                              # brushed steel
        lift.hline(gy, 4, 28, METAL.shade)
    mt.plane(lift, 11, 0, 10, 4, METAL.deep)                # the indicator
    mt.plane(lift, 12, 1, 8, 2, LAMP.shade)
    lift.blob(29, 17, 1.6, LAMP.mid)                        # the call button
    cb.add_object("lift", lift, solid="all")

    # --- the stairs.  Two attempts at this were unreadable and both failed
    # the same way: a flight seventeen pixels wide with a tread every six is,
    # from directly above, a ladder — and two of them side by side with a
    # well between is two ladders.  A staircase reads at this size only when
    # the treads run the *full* width of the object, so there is one flight
    # per end of the corridor: up at the west, down at the east.
    def _flight(rising: bool) -> Canvas:
        art = ct._canvas(3, 4)
        w, h = 48, 64
        mt.plane(art, 0, 0, w, h, CORE.deep)
        mt.plane(art, 0, 0, 4, h, CORE.shade)           # the shaft walls
        mt.plane(art, w - 4, 0, 4, h, CORE.deep)
        treads = list(range(6, h - 8, 6))
        for index, ty in enumerate(treads):
            # the far end of a rising flight is in light and of a falling one
            # in shadow: that is the only thing telling you which it is
            t_ = 1 - index / max(1, len(treads) - 1)
            level = t_ if rising else 1 - t_
            tread = (PLASTER.lit if level > 0.66 else
                     PLASTER.mid if level > 0.33 else PLASTER.shade)
            nose = (PLASTER.hot if level > 0.66 else
                    PLASTER.lit if level > 0.33 else PLASTER.mid)
            mt.plane(art, 4, ty, w - 8, 6, tread)
            art.hline(ty, 4, w - 5, nose)               # the nosing
            art.hline(ty + 5, 4, w - 5, PLASTER.deep)   # the riser under it
        # where the flight goes: out of sight either way, but light one way
        mt.plane(art, 4, 0, w - 8, 6, PLASTER.hot if rising else (12, 12, 18))
        if rising:
            mt.seam(art, 4, 4, w - 8, 3, PLASTER.hot, PLASTER.lit)
        # the landing at the corridor end, which is what you step onto
        mt.plane(art, 0, h - 8, w, 8, PLASTER.mid)
        mt.plane(art, 0, h - 8, w, 2, PLASTER.lit)
        mt.seam(art, 0, h - 4, w, 4, PLASTER.mid, PLASTER.shade)
        # handrails down both sides, over everything
        for hx in (5, w - 7):
            art.vline(hx, 2, h - 9, METAL.mid)
            art.vline(hx + 1, 2, h - 9, METAL.shade)
        for hy in range(4, h - 10, 7):
            art.rect(6, hy, 1, 4, METAL.deep)
            art.rect(w - 8, hy, 1, 4, METAL.deep)
        return art

    cb.add_object("stair_up", _flight(True), solid="all")
    cb.add_object("stair_down", _flight(False), solid="all")

    # --- the fittings that survive in a corridor
    radiator = ct._canvas(1, 1)
    mt.plane(radiator, 1, 4, 14, 11, METAL.shade)
    mt.plane(radiator, 1, 4, 14, 2, METAL.lit)
    for rx in range(2, 15, 2):
        radiator.vline(rx, 6, 13, METAL.mid)
    cb.add_object("radiator", radiator, solid="all")

    # A bracket and a shade.  Small and square it read as a notice screwed to
    # the wall; it needs the bracket above it and a wider shade below to be a
    # light at all at this size.
    sconce = ct._canvas(1, 2)
    mt.plane(sconce, 6, 2, 4, 5, METAL.shade)               # the bracket
    mt.plane(sconce, 6, 2, 2, 5, METAL.mid)
    mt.plane(sconce, 2, 7, 12, 8, LAMP.mid)                 # the shade
    mt.plane(sconce, 3, 7, 10, 3, LAMP.hot)
    mt.seam(sconce, 2, 13, 12, 2, LAMP.mid, LAMP.shade)
    sconce.vline(2, 7, 14, LAMP.lit)
    sconce.vline(13, 7, 14, LAMP.shade)
    mt.plane(sconce, 4, 15, 8, 2, LAMP.shade)
    cb.add_object("sconce", sconce, solid="none", upper=True, above=True)

    sconce_dead = ct._canvas(1, 2)
    mt.plane(sconce_dead, 6, 2, 4, 5, METAL.shade)
    mt.plane(sconce_dead, 2, 7, 12, 8, METAL.shade)
    mt.plane(sconce_dead, 3, 7, 10, 3, METAL.mid)
    mt.plane(sconce_dead, 4, 15, 8, 2, METAL.deep)
    cb.add_object("sconce_dead", sconce_dead, solid="none", upper=True,
                  above=True)

    dead = ct._canvas(1, 2)
    POT = mt.Material("pot", (96, 88, 82))
    DEAD = mt.Material("dead", (98, 90, 64))
    mt.plane(dead, 3, 19, 10, 12, POT.mid)
    mt.plane(dead, 3, 19, 10, 2, POT.lit)
    mt.plane(dead, 4, 29, 8, 2, POT.deep)
    for dx, dy in ((-4, 8), (-1, 12), (3, 9), (5, 5)):
        dead.line(8, 19, 8 + dx, 19 - dy, DEAD.shade)
        dead.dot(8 + dx, 19 - dy, DEAD.mid)
    cb.add_object("dead_plant", dead, solid="all")

    notice = ct._canvas(2, 2)
    mt.plane(notice, 1, 2, 30, 26, WOOD.deep)
    mt.plane(notice, 3, 4, 26, 22, mt.Material("cork", (108, 84, 62)).mid)
    for nx, ny, nw, nh in ((5, 6, 9, 7), (17, 7, 9, 6), (7, 16, 11, 7),
                           (20, 15, 6, 8)):
        mt.plane(notice, nx, ny, nw, nh, PLASTER.lit)
        mt.plane(notice, nx, ny, nw, 1, PLASTER.hot)
        for ly in range(ny + 2, ny + nh - 1, 2):
            notice.hline(ly, nx + 1, nx + nw - 2, PLASTER.shade)
    cb.add_object("notice", notice, solid="all")

    boxes = ct._canvas(3, 2)
    mt.plane(boxes, 1, 2, 46, 26, METAL.shade)
    mt.plane(boxes, 1, 2, 46, 2, METAL.lit)
    for by in (5, 16):
        for bx in range(3, 45, 8):
            mt.plane(boxes, bx, by, 7, 10, METAL.mid)
            mt.plane(boxes, bx, by, 7, 1, METAL.lit)
            boxes.hline(by + 3, bx + 1, bx + 5, METAL.deep)   # the slot
            boxes.dot(bx + 5, by + 7, LAMP.shade)             # the lock
    cb.add_object("mailboxes", boxes, solid="all")

    # --- the way out, which is not one.  Wired glass with nothing behind it:
    # the street is not modelled, not dark, not anything.  There is no outside.
    entrance = ct._canvas(3, 2)
    mt.plane(entrance, 0, 0, 48, 32, METAL.deep)
    mt.plane(entrance, 1, 1, 46, 30, METAL.shade)
    for ox in (3, 25):
        mt.plane(entrance, ox, 3, 20, 27, (6, 6, 10))
        for gx in range(ox + 2, ox + 20, 4):                # the wire in it
            entrance.vline(gx, 4, 28, (18, 18, 26))
        for gy in range(6, 29, 4):
            entrance.hline(gy, ox + 1, ox + 18, (18, 18, 26))
        entrance.vline(ox, 3, 29, METAL.mid)
        entrance.vline(ox + 19, 3, 29, METAL.deep)
    mt.plane(entrance, 23, 1, 2, 30, METAL.mid)
    for hy in range(13, 20):                                # the push bars
        entrance.dot(19, hy, METAL.lit)
        entrance.dot(28, hy, METAL.lit)
    cb.add_object("entrance", entrance, solid="all")

    _shadows(cb, pal)
    _animate(cb, pal, "room")
    return _finish(cb, lino)


def build_balcony() -> ChipsetBuild:
    """Outside the room, three paces deep, with the city in front of it.

    A separate screen on purpose.  The room is somewhere you are kept and the
    balcony is the one place in the waking half of the game with a horizon in
    it, and putting both on one map would have made the horizon a decoration
    at the top of a bedroom.  Same materials, same light, different substance:
    everything out here is concrete, render and weather.
    """
    pal = PALETTES["room"]
    cb = ChipsetBuilder("balcony", pal)
    mats = _room_materials()
    CONC, METAL = mats["concrete"], mats["metal"]
    SKY, FAR, NEAR = mats["sky"], mats["far"], mats["near"]
    LAMP, PLASTER = mats["lamp"], mats["plaster"]
    CORE, SKIN = mats["core"], mats["skin"]

    # --- the deck: poured concrete in slabs, with the joints where they fall
    def _slab(offset: int) -> Canvas:
        art = Canvas(TILE, TILE, CONC.mid)
        mt.plane(art, 0, 0, TILE, TILE, CONC.mid)
        art.hline((offset + 3) % TILE, 0, TILE - 1, CONC.shade)
        art.hline((offset + 4) % TILE, 0, TILE - 1, CONC.lit)
        art.vline((offset * 3 + 5) % TILE, 0, TILE - 1, CONC.shade)
        return art

    deck = _slab(0)
    cb.add("ground", deck)
    cb.add("ground_b", _slab(6))
    cb.add("path", _slab(11))
    stain = _slab(2)
    mt.seam(stain, 0, 0, TILE, TILE, CONC.shade, CONC.mid)
    cb.add("glow", stain)
    cb.add("rug", stain)
    cb.add("void", ct.flat(SKIN.deep), passable=False)

    # --- the view: sky, then a far shore of towers, then water, then the
    # near bank, and snow lying on all of it.
    #
    # Distance is done as bands and the towers are *objects*, not tiles: a
    # skyline assembled out of sixteen-pixel cells can only ever be a fence,
    # and the one thing this view has to do is be much larger than the flat
    # it is seen from.
    SNOW = mt.Material("snow", (188, 194, 210))
    WATER = mt.Material("water", (46, 52, 82))
    TOWER = mt.Material("tower", (54, 54, 80), grain="v")

    sky = Canvas(TILE, TILE, SKY.mid)
    mt.seam(sky, 0, 0, TILE, TILE, SKY.lit, SKY.mid)
    cb.add("sky", sky, passable=False)
    sky_low = Canvas(TILE, TILE, SKY.mid)
    mt.plane(sky_low, 0, 0, TILE, TILE, SKY.mid)
    mt.seam(sky_low, 0, 8, TILE, 8, SKY.mid, SKY.shade)
    cb.add("sky_low", sky_low, passable=False)

    # the far bank the towers stand on: snow, and the shoreline under it
    bank = Canvas(TILE, TILE, SNOW.shade)
    mt.plane(bank, 0, 0, TILE, 7, SNOW.mid)
    mt.plane(bank, 0, 0, TILE, 2, SNOW.lit)
    mt.seam(bank, 0, 7, TILE, 3, SNOW.mid, SNOW.shade)
    mt.plane(bank, 0, 10, TILE, 4, SNOW.shade)
    mt.plane(bank, 0, 14, TILE, 2, WATER.lit)      # the waterline itself
    cb.add("bank_far", bank, passable=False)

    # open water: nearly flat.  It was a full grid of highlight runs and read
    # as another course of brickwork sitting between the city and the flat,
    # which is the last thing a body of water should do.  Two long broken
    # runs a tile, and the value under them barely moving.
    water = Canvas(TILE, TILE, WATER.mid)
    mt.plane(water, 0, 0, TILE, TILE, WATER.mid)
    mt.seam(water, 0, 0, TILE, 5, WATER.shade, WATER.mid)
    water.hline(6, 1, 9, WATER.lit)
    water.hline(12, 7, TILE - 2, WATER.lit)
    cb.add("water", water, passable=False)
    # the same water directly under the towers, carrying their lights down in
    # broken vertical smears — the only place the surface is busy
    glint = water.copy()
    for gx in range(3, TILE, 6):
        for gy in (2, 6, 11):
            glint.dot(gx, gy, LAMP.deep)
            glint.dot(gx, gy + 2, WATER.lit)
    cb.add("water_lit", glint, passable=False)

    # the near bank, below the water: snow again, and the top of it lit
    near_bank = Canvas(TILE, TILE, SNOW.shade)
    mt.plane(near_bank, 0, 0, TILE, 2, WATER.deep)
    mt.plane(near_bank, 0, 2, TILE, 5, SNOW.shade)
    mt.seam(near_bank, 0, 7, TILE, 3, SNOW.shade, SNOW.mid)
    mt.plane(near_bank, 0, 10, TILE, 6, SNOW.mid)
    cb.add("bank_near", near_bank, passable=False)

    # --- the towers.  Drawn as single unbroken shafts: the first pass put a
    # snow-capped setback every four courses, which chopped each one into a
    # stack of crates and lost the only thing they are for, which is being
    # much taller than the flat they are seen from.
    def _tower(cols: int, rows: int, crown: int, pitch: int) -> Canvas:
        art = ct._canvas(cols, rows)
        w, h = cols * TILE, rows * TILE
        lit = max(4, w // 3)                    # the face turned to the light
        mt.plane(art, 0, crown, w, h - crown, TOWER.shade)
        mt.plane(art, 0, crown, lit, h - crown, TOWER.mid)
        mt.seam(art, lit, crown, 3, h - crown, TOWER.mid, TOWER.shade,
                vertical=True)
        art.vline(0, crown, h - 1, TOWER.lit)   # the lit corner
        art.vline(w - 1, crown, h - 1, TOWER.deep)
        # the crown: a plant room, and snow lying on top of it
        mt.plane(art, 3, crown - 5, w - 6, 6, TOWER.shade)
        mt.plane(art, 3, crown - 5, w - 6, 2, SNOW.shade)
        mt.plane(art, 0, crown, w, 2, SNOW.shade)
        mt.plane(art, 0, crown, w, 1, SNOW.mid)
        art.vline(w // 2, max(0, crown - 11), crown - 5, TOWER.deep)  # a mast
        # windows: sparse and unevenly lit, so the tower reads as occupied at
        # night rather than as a grid
        for course, row in enumerate(range(crown + 5, h - 3, pitch)):
            for index, col in enumerate(range(2, w - 3, 4)):
                state = (course * 5 + index * 3) % 7
                art.rect(col, row, 2, 2,
                         LAMP.shade if state == 0 else
                         LAMP.deep if state == 1 else TOWER.deep)
        return art

    cb.add_object("tower_a", _tower(2, 6, 14, 6), solid="all", upper=True)
    cb.add_object("tower_b", _tower(3, 5, 22, 7), solid="all", upper=True)
    cb.add_object("tower_c", _tower(2, 4, 30, 6), solid="all", upper=True)
    cb.add_object("tower_d", _tower(3, 6, 8, 8), solid="all", upper=True)

    # --- the building at your back, in the same section as the room's walls
    for side in ("s", "w", "e"):
        cb.add(f"cut_{side}", _wall_cut(mats, side), passable=False)
    render = Canvas(TILE, TILE, PLASTER.shade)
    mt.plane(render, 0, 0, TILE, TILE, PLASTER.shade)
    mt.plane(render, 0, 0, TILE, 3, PLASTER.mid)
    for x in range(0, TILE, 8):
        render.vline(x, 3, TILE - 1, PLASTER.deep)
    cb.add("render", render, passable=False)

    # --- the parapet, seen in section the same way: a top surface you look
    # down on and a face turned back toward you
    SNOW_C = mt.Material("snow", (188, 194, 210))
    parapet = Canvas(TILE, TILE, CONC.mid)
    mt.plane(parapet, 0, 0, TILE, 4, CONC.shade)        # the outside face
    mt.plane(parapet, 0, 4, TILE, 4, SNOW_C.lit)        # snow lying on it
    mt.seam(parapet, 0, 8, TILE, 2, SNOW_C.lit, SNOW_C.shade)
    mt.plane(parapet, 0, 10, TILE, 3, CONC.mid)         # the coping under it
    mt.plane(parapet, 0, 13, TILE, 3, CONC.deep)        # the shadow it throws
    cb.add("parapet", parapet, passable=False)

    # --- the railing that stands on it
    rail = ct._canvas(1, 1)
    mt.plane(rail, 0, 1, TILE, 3, METAL.mid)            # the handrail
    mt.plane(rail, 0, 1, TILE, 1, METAL.lit)
    for x in range(1, TILE, 4):                         # the balusters
        mt.plane(rail, x, 4, 2, 11, METAL.shade)
        rail.vline(x, 4, 14, METAL.mid)
    cb.add_object("rail", rail, solid="all", upper=True)

    # --- the way back in: the same door, from the other side
    slider = ct._canvas(3, 2)
    mt.plane(slider, 0, 0, 48, 32, METAL.shade)
    mt.plane(slider, 0, 0, 48, 2, METAL.lit)
    mt.plane(slider, 2, 2, 44, 28, METAL.deep)
    ROOMGLOW = mt.Material("roomglow", (86, 70, 74))
    for ox in (3, 24):
        mt.plane(slider, ox, 3, 21, 26, ROOMGLOW.shade)
        mt.plane(slider, ox, 3, 21, 9, ROOMGLOW.mid)
        mt.seam(slider, ox, 12, 21, 3, ROOMGLOW.mid, ROOMGLOW.shade)
        slider.vline(ox, 3, 28, METAL.mid)
    mt.plane(slider, 8, 14, 6, 8, LAMP.shade)           # the lamp, through it
    mt.plane(slider, 23, 2, 2, 28, METAL.mid)
    slider.vline(22, 2, 29, METAL.deep)
    mt.plane(slider, 1, 29, 46, 3, METAL.mid)
    slider.hline(29, 1, 46, METAL.lit)
    cb.add_object("slider", slider, solid="all")

    # --- what accumulates on a balcony nobody sits on
    aircon = ct._canvas(2, 2)
    mt.plane(aircon, 2, 6, 28, 24, METAL.mid)
    mt.plane(aircon, 2, 6, 28, 3, METAL.lit)
    mt.plane(aircon, 2, 28, 28, 2, METAL.deep)
    mt.plane(aircon, 5, 11, 22, 15, METAL.shade)        # the grille
    for gy in range(12, 26, 3):
        aircon.hline(gy, 6, 25, METAL.deep)
        aircon.hline(gy + 1, 6, 25, METAL.mid)
    cb.add_object("aircon", aircon, solid="all")

    chair = ct._canvas(1, 2)
    PLASTIC = mt.Material("plastic", (118, 116, 108))
    mt.plane(chair, 3, 6, 10, 13, PLASTIC.shade)        # the back
    mt.plane(chair, 3, 6, 10, 2, PLASTIC.lit)
    mt.plane(chair, 2, 19, 12, 5, PLASTIC.mid)          # the seat
    mt.plane(chair, 2, 19, 12, 2, PLASTIC.lit)
    for lx in (3, 11):
        mt.plane(chair, lx, 24, 2, 6, PLASTIC.shade)
    cb.add_object("chair", chair, solid="all")

    pot = ct._canvas(1, 1)
    POT = mt.Material("pot", (118, 74, 56))
    DEAD = mt.Material("dead", (96, 88, 62))
    mt.plane(pot, 3, 7, 10, 9, POT.mid)
    mt.plane(pot, 3, 7, 10, 2, POT.lit)
    for dx, dy in ((-3, 5), (0, 7), (3, 4)):
        pot.line(8, 7, 8 + dx, 7 - dy, DEAD.mid)
    cb.add_object("pot", pot, solid="all")

    bucket = ct._canvas(1, 1)
    mt.plane(bucket, 4, 6, 8, 10, METAL.shade)
    mt.plane(bucket, 4, 6, 8, 2, METAL.mid)
    mt.plane(bucket, 5, 8, 6, 5, mats["sky"].shade)     # rain, still in it
    cb.add_object("bucket", bucket, solid="all")

    _shadows(cb, pal)
    _animate(cb, pal, "room")
    return _finish(cb, deck)


def build_nexus() -> ChipsetBuild:
    """Between the dreams: soft dark, and doors that are not in any wall."""
    pal = PALETTES["nexus"]
    cb = ChipsetBuilder("nexus", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.35)
    _basics(cb, pal, ground)

    # Twelve portals, and every one of them is a different mirror.
    #
    # These used to be one object, so all twelve looked identical and the
    # per-world mirror only ever appeared *inside* its own world — which put
    # the distinguishing detail on the side of the trip where the player
    # already knows where they are.  A mirror is only useful as a portal if it
    # tells you where it goes while you are still standing in front of it.
    #
    # Each takes the destination world's own frame colour and glass, and the
    # silhouette standing in it is a thing from that world.  The nexus is the
    # only place in the game that borrows other worlds' palettes, and it is
    # allowed to because looking through is the entire point of the room.
    from ..worlds.worlds import DREAM_ORDER

    for key in DREAM_ORDER:
        other = PALETTES[key]
        cb.add_object(f"door_{key}", ct.door_frame(other, 2, 3,
                                                   reflect=ct.REFLECTION[key]))
    cb.add_object("door", ct.door_frame(pal, 2, 3, reflect="door"))
    cb.add_object("door_shut", ct.door_frame(pal, 2, 3))
    cb.add_object("lamp", ct.lamp_post(pal, 1, 3), solid="bottom")
    cb.add_object("bench", ct.bench_seat(pal, 3, 2), solid="bottom")
    cb.add_object("mirror", ct.standing_mirror(pal, 2, 3), solid="all")

    arch = ct._canvas(3, 1)
    arch.rect(0, 8, 48, 8, pal.form_dark)
    arch.rect(0, 8, 48, 2, pal.form)
    cb.add_object("arch", arch, solid="none", upper=True, above=True)

    _shadows(cb, pal)
    _landmarks(cb, pal, "nexus")
    _animate(cb, pal, "nexus")
    _decals(cb, pal, "nexus", ground)
    return _finish(cb, ground)


# --- the dreams --------------------------------------------------------------

def build_pink() -> ChipsetBuild:
    """Endless pink brick.  Every hallway nearly identical, almost no landmarks."""
    pal = PALETTES["pink"]
    cb = ChipsetBuilder("pink", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.3)
    _basics(cb, pal, ground, ct.brick_ground(pal, course=8))

    cb.add_object("wall", ct.wall_run(pal, height=3, brick=True))
    cb.add_object("wall_short", ct.wall_run(pal, height=2, brick=True))
    # The impossible door: same brick, same pink, no reason for it.
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    cb.add_object("arch", ct.brick_arch(pal, 4, 4), solid="bottom2")
    cb.add_object("niche", ct.wall_niche(pal, 2, 3))

    col = ct._canvas(1, 3)
    col.rect(2, 0, 12, 48, pal.form)
    col.rect(2, 0, 3, 48, pal.form_light)
    col.rect(11, 0, 3, 48, pal.form_dark)
    col.round_rect(0, 0, 16, 6, 2, pal.form_light)
    outline_in(col, cooler(pal.form_dark, 0.3))
    cb.add_object("column", col, solid="bottom")

    _shadows(cb, pal)
    _landmarks(cb, pal, "pink")
    _animate(cb, pal, "pink")
    _decals(cb, pal, "pink", ground)
    return _finish(cb, ground)


def build_numbers() -> ChipsetBuild:
    """A landscape built out of oversized digits.  Nothing acknowledges this."""
    pal = PALETTES["numbers"]
    cb = ChipsetBuilder("numbers", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.3)
    _basics(cb, pal, ground)

    for digit in (0, 1, 3, 5, 7, 9):
        cb.add_object(f"digit_{digit}", ct.big_digit(pal, digit, 3, 4),
                      solid="bottom")
    for kind in ("plus", "minus", "equals"):
        cb.add_object(f"sign_{kind}", ct.operator_sign(pal, kind, 2, 2),
                      solid="bottom")
    cb.add_object("plinth", ct.number_plinth(pal, 3, 2), solid="all")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "numbers")
    _animate(cb, pal, "numbers")
    _decals(cb, pal, "numbers", ground)
    return _finish(cb, ground)


def build_blocks() -> ChipsetBuild:
    """Children's building blocks, at the size of buildings."""
    pal = PALETTES["blocks"]
    cb = ChipsetBuilder("blocks", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.3)
    _basics(cb, pal, ground)

    colors = ((228, 128, 124), (120, 176, 226), (238, 206, 126), (140, 200, 152))
    for index, (color, mark) in enumerate(zip(colors,
                                              ("dot", "ring", "square", "cross"))):
        cb.add_object(f"block_{index}", ct.toy_block(pal, color, 3, 3, mark=mark))
    # Scale is not consistent here, and never explains itself.
    cb.add_object("block_tiny", ct.toy_block(pal, colors[1], 1, 1, mark="dot"))
    cb.add_object("block_huge", ct.toy_block(pal, colors[0], 4, 4, mark="ring"))
    cb.add_object("ball", ct.ball_toy(pal, colors[2], 2, 2), solid="all")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "blocks")
    _animate(cb, pal, "blocks")
    _decals(cb, pal, "blocks", ground)
    return _finish(cb, ground)


def build_stairs() -> ChipsetBuild:
    """Floating staircases.  No walls.  Some of them lead nowhere."""
    pal = PALETTES["stairs"]
    cb = ChipsetBuilder("stairs", pal)

    # The drop is the void outside the carved layout, not the floor itself:
    # anything the architecture carves out is stone you can stand on.
    ground = ct.star_ground(pal, density=2)
    cb.add("ground", ground)
    cb.add("ground_b", ct.soft_ground(pal.ground_b, pal.void, 0.4))
    landing = Canvas(TILE, TILE, pal.form)
    landing.rect(0, 0, TILE, 3, pal.form_light)
    landing.rect(0, TILE - 3, TILE, 3, pal.form_dark)
    cb.add("path", landing)
    cb.add("glow", ct.glow_pool(pal))
    cb.add("void", ct.void_tile(pal), passable=False)
    cb.add("wall_core", ct.wall_band(pal, "steps"), passable=False)
    cb.add("wall_face", ct.wall_band(pal, "steps", face=True),
           passable=False)

    cb.add_object("stair_up", ct.floating_stair(pal, 4, 3, rising=True),
                  solid="none")
    cb.add_object("stair_down", ct.floating_stair(pal, 4, 3, rising=False),
                  solid="none")
    cb.add_object("landing", ct.stair_landing(pal, 3, 2), solid="none")
    cb.add_object("spiral", ct.spiral_stair(pal, 3, 5), solid="none")
    cb.add_object("stair_broken", ct.broken_stair(pal, 3, 2), solid="none")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    cb.add_object("lamp", ct.lamp_post(pal, 1, 3), solid="bottom")
    _shadows(cb, pal)
    _landmarks(cb, pal, "stairs")
    _animate(cb, pal, "stairs")
    _decals(cb, pal, "stairs", ground)
    return _finish(cb, ground)


def build_sand() -> ChipsetBuild:
    """A nearly empty pale desert.  The emptiness is the content."""
    pal = PALETTES["sand"]
    cb = ChipsetBuilder("sand", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.22)
    dune = Canvas(TILE, TILE, pal.ground_b)
    dune.dither(pal.ground, 0.5, ct.BAYER8)
    dune.hline(6, 0, TILE - 1, warmer(pal.ground, 0.2))
    _basics(cb, pal, ground, dune)

    cb.add_object("structure", ct.tiny_structure(pal, 2, 3), solid="bottom")
    cb.add_object("obelisk", ct.obelisk(pal, 2, 5), solid="bottom")
    cb.add_object("dead_tree", ct.dead_tree(pal, 3, 4), solid="bottom")
    post = ct._canvas(1, 3)
    post.rect(6, 4, 4, 44, pal.form_dark)
    post.round_rect(3, 0, 10, 8, 3, pal.accent)
    outline_in(post, cooler(pal.form_dark, 0.3))
    cb.add_object("post", post, solid="bottom")
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent_soft))
    _shadows(cb, pal)
    _landmarks(cb, pal, "sand")
    _animate(cb, pal, "sand")
    _decals(cb, pal, "sand", ground)
    return _finish(cb, ground)


# What colour each channel's locked door is painted.  Read straight off
# hidden.OPENS: the door on a channel is painted for the channel its key comes
# from, not for the one it stands on, so the four of them make a closed loop
# and none is a hint about where it is standing.
LOCK_COLOUR = {
    "faces":  (122, 214, 138),      # green   -- the key is on overgrown
    "faces2": (168, 170, 186),      # grey    -- the key is on off-colour
    "faces3": (214, 76, 62),        # red     -- the key is on no signal
    "faces4": (232, 186, 92),       # amber   -- the key is on the grove
}


def _grove_common(cb: ChipsetBuilder, pal: Palette, look, world: str,
                  *, tree_rows: int = 4, bare: bool = False,
                  cap: tuple[int, int, int] = (216, 128, 118)) -> Canvas:
    """Everything all four channels of the grove have, in the same order.

    The street plan is generated once and shared, so the four channels have to
    agree tile for tile about what exists — the difference between them is the
    ``Look``, which is a set of materials, and nothing else.  Writing it out
    four times is how the channels drifted apart in the first place: one of
    them ended up with a kerb the others did not have, and the illusion that
    they are one town received four ways only survives if the geometry is
    identical.
    """
    ground = gv.turf(look, 0)
    _basics(cb, pal, ground, gv.turf(look, 1), world=world)
    cb.add("road", gv.road(look))
    cb.add("road_line", gv.lane(look))
    cb.add("road_line_h", gv.lane_across(look))
    # four kerbs, because a kerb has to know which side of the road it is on
    for side in ("n", "s", "w", "e"):
        cb.add(f"kerb_{side}", gv.kerb(look, side))
    cb.add("kerb", gv.kerb(look, "n"))
    cb.add("paving", gv.paving(look))

    cb.add_object("tree", gv.tree(look, 3, tree_rows, face=True, bare=bare),
                  solid="bottom")
    cb.add_object("tree_plain", gv.tree(look, 3, tree_rows, bare=bare),
                  solid="bottom")
    cb.add_object("stump", gv.stump(look, 2, 2), solid="all")
    cb.add_object("mushroom", gv.mushroom(look, cap, 2, 2), solid="bottom")
    cb.add_object("bush", gv.bush(look, 2, 2), solid="bottom")

    # Street furniture, on the upper layer with no ground baked in: every one
    # of these stands on asphalt, kerb and grass alike and must show whichever
    # is really underneath.
    cb.add_object("traffic_light", gv.traffic_light(look, 1, 4),
                  solid="bottom", upper=True)
    cb.add_object("shelter", gv.bus_shelter(look, 4, 3), solid="bottom",
                  upper=True)
    cb.add_object("phone_box", gv.phone_box(look, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("car", gv.dead_car(look, 3, 2), solid="all", upper=True)
    cb.add_object("vending", gv.vending_machine(look, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("road_sign", gv.road_sign(look, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                        reflect=_reflection(cb.name)))

    # The four ways into the hidden half.  Every channel carries all four,
    # because the street plan is shared tile for tile and a channel missing an
    # object is a channel whose geometry has drifted -- and because the same
    # entrance standing in the same place on all four receptions is the whole
    # trick the hidden half is built on.
    cb.add_object("crack", gv.rock_split(look, 2, 3), solid="all")
    cb.add_object("cover", gv.manhole(look, 2, 2), solid="all")
    cb.add_object("hatch", gv.hatch_shed(look, 2, 3), solid="all")
    # Painted the colour of the channel whose key opens it, which is the only
    # instruction the game gives about the locks.
    cb.add_object("lock", gv.locked_door(look, LOCK_COLOUR[world], 2, 3),
                  solid="all")
    return ground


# The four ways further down.  Each is a mirror standing in a hidden room,
# and each shows the place on the other side of it rather than the player.
# The glass takes that place's own colour, which is the only thing telling the
# player these four are not the twelve other mirrors in the game.
DESCENTS = {
    "caustic":   (2, 3, (108, 236, 132), (44, 96, 62)),   # glowing, wet
    "hell":      (2, 3, (196, 44, 38), (28, 12, 14)),     # dark, and lit red
    "purgatory": (2, 3, (156, 158, 172), (72, 74, 88)),   # no colour at all
    "lobotomy":  (2, 3, (250, 232, 178), (216, 176, 120)),  # far too warm
}


def _descent(cb: ChipsetBuilder, pal: Palette, key: str) -> None:
    cols, rows, glow, leaf = DESCENTS[key]
    cb.add_object(f"gate_{key}",
                  ct.door_frame(pal, cols, rows, glow=glow, leaf=leaf,
                                reflect=ct.REFLECTION[key]),
                  solid="all")


def build_under() -> ChipsetBuild:
    """Under the grove: rock where nobody built, brick where somebody did.

    One chipset for all eight rooms beneath the town, and the whole of the
    difference between a cave and a sewer lives in it.  A cave is irregular
    rock, broken stone underfoot and water lying in a shape nothing cut.  A
    sewer is engineering brick in courses with a channel down the middle of
    it, because a sewer is a thing that was *made*.

    Nothing down here is furnished.  The first pass gave the caves crates,
    racking and a rectangle of water, which read as a cellar with a rug in it.
    """
    pal = PALETTES["faces"]
    cb = ChipsetBuilder("under", pal)
    look = gv.CAVE

    floor = gv.rubble(look, 0)
    cb.add("ground", floor)
    cb.add("ground_b", gv.rubble(look, 3))
    cb.add("path", gv.rubble(look, 5))
    for n in range(3):
        cb.add(f"pool_{n}", gv.pool(look, n), passable=False)
    cb.add("water", gv.pool(look, 1), passable=False)
    cb.add("glow", gv.rubble(look, 2))
    cb.add("rug", gv.rubble(look, 4))
    cb.add("void", ct.flat((0, 0, 0)), passable=False)
    cb.add("black", ct.flat((0, 0, 0)), passable=False)
    for n in range(3):
        cb.add(f"rock_{n}", gv.rock_face(look, seed=n), passable=False)
    cb.add("rock", gv.rock_face(look), passable=False)
    cb.add("rock_crack", gv.rock_face(look, cracked=True), passable=False)
    cb.add("brick", gv.sewer_wall(look), passable=False)
    cb.add("channel", gv.sewer_channel(look), passable=False)
    for side in ("n", "s", "w", "e"):
        cb.add(f"cut_{side}", gv.rock_face(look, seed=1), passable=False)
        cb.add(f"face_{side}", gv.rock_face(look, seed=2), passable=False)
    cb.add("face_n_low", gv.rock_face(look), passable=False)
    cb.add("face_s_low", gv.rock_face(look, seed=1), passable=False)

    cb.add_object("boulder", gv.boulder(look, 2, 2), solid="all")
    cb.add_object("boulder_small", gv.boulder(look, 1, 1), solid="all")
    cb.add_object("column", gv.column(look, 1, 4), solid="bottom", upper=True)
    cb.add_object("mouth", gv.cave_mouth(look, 2, 3), solid="none",
                  upper=True, above=True)
    cb.add_object("ladder", gv.ladder(look, 2, 3), solid="none", upper=True,
                  above=True)
    cb.add_object("lamp", gv.traffic_light(look, 1, 4), solid="bottom",
                  upper=True)
    # what makes four caves and four runs into eight places
    cb.add("wedge", gv.wedge_wall(look), passable=False)
    cb.add("smooth", gv.flat_floor(look, mt.Material("floor", (72, 68, 82))))
    cb.add("deep", gv.deep_water(look), passable=False)
    cb.add("dry", gv.dry_channel(look))
    cb.add_object("cable", gv.cable_tray(look, 3, 2), solid="all", upper=True)
    # two of the four ways further down stand in rooms made of rock
    for key in ("caustic", "hell", "purgatory"):
        _descent(cb, pal, key)
    _shadows(cb, pal)
    _animate(cb, pal, "faces")
    return _finish(cb, floor)


def build_premises() -> ChipsetBuild:
    """Inside the grove's buildings, and the small rooms above them.

    Board, paint and equipment.  Every one of these is somewhere the town used
    to do something from, and the giveaway is that none of them have been
    cleared out — the racks are still racked, the desks are still stacked, and
    the only thing missing is anybody to be doing it.
    """
    pal = PALETTES["faces"]
    cb = ChipsetBuilder("premises", pal)
    look = gv.PREM

    floor = gv.boards(look, 0)
    cb.add("ground", floor)
    cb.add("ground_b", gv.boards(look, 7))
    cb.add("path", gv.boards(look, 11))
    cb.add("rug", gv.paving(look))
    cb.add("glow", gv.boards(look, 3))
    cb.add("void", ct.flat((0, 0, 0)), passable=False)
    cb.add("black", ct.flat((0, 0, 0)), passable=False)
    PLASTER = mt.Material("plaster", (104, 98, 112), grain="v")
    CORE = mt.Material("core", (74, 76, 92))
    mats = {"plaster": PLASTER, "core": CORE,
            "skin": mt.Material("skin", (48, 48, 64))}
    for side in ("n", "s", "w", "e"):
        cb.add(f"cut_{side}", _wall_cut(mats, side), passable=False)
        cb.add(f"face_{side}", _wall_face(mats, side), passable=False)
    cb.add("face_n_low", _wall_face(mats, "n", low=True), passable=False)
    cb.add("face_s_low", _wall_face(mats, "s", low=True), passable=False)

    cb.add_object("rack", gv.rack(look, 2, 3), solid="all")
    cb.add_object("crate", gv.crate(look, 2, 2), solid="all")
    cb.add_object("counter", gv.dead_car(look, 3, 2), solid="all", upper=True)
    cb.add_object("machine", gv.vending_machine(look, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("board", gv.road_sign(look, 2, 3), solid="bottom",
                  upper=True)
    # The way out is a door, and it is a door.  Every hidden room used the
    # nexus portal frame, which is a full-length mirror, so a cave read as
    # somewhere with a mirror in it and an office read as a changing room.
    door = ct._canvas(2, 3)
    WOOD = mt.Material("wood", (96, 70, 54))
    METAL = mt.Material("metal", (104, 108, 118))
    mt.plane(door, 0, 8, 32, 40, WOOD.deep)
    mt.plane(door, 3, 10, 26, 38, WOOD.shade)
    mt.plane(door, 5, 11, 22, 37, WOOD.mid)
    mt.plane(door, 5, 11, 22, 2, WOOD.lit)
    for py, ph in ((15, 12), (30, 14)):
        mt.plane(door, 8, py, 16, ph, WOOD.shade)
        mt.plane(door, 9, py + 1, 14, ph - 2, WOOD.mid)
    door.blob(24, 30, 1.9, METAL.lit)
    cb.add_object("way_out", door, solid="none", upper=True, above=True)
    # and what makes eight rooms above ground into eight places
    cb.add("glass", gv.glass_wall(look), passable=False)
    cb.add("bed", gv.planting_bed(look), passable=False)
    cb.add("stone", gv.flat_floor(look, mt.Material("stone", (96, 94, 100))))
    cb.add_object("levers", gv.lever_bank(look, 3, 2), solid="all")
    cb.add_object("desk", gv.desk(look, 2, 2), solid="all")
    cb.add_object("frame", gv.jack_frame(look, 2, 3), solid="all")
    cb.add_object("transformer", gv.transformer(look, 3, 3), solid="all")
    cb.add_object("fence", gv.mesh_fence(look, 2, 2), solid="all", upper=True)
    cb.add_object("transmitter", gv.transmitter(look, 3, 3), solid="all")
    _descent(cb, pal, "lobotomy")
    _shadows(cb, pal)
    _animate(cb, pal, "faces")
    return _finish(cb, floor)


def build_faces() -> ChipsetBuild:
    """A CITY THE FOREST GREW THROUGH.

    Not a forest.  A forest is a place; this is a place that used to be a
    different place.  The roads still have their lane markings, the traffic
    lights are still cycling, the windows are still lit, and none of it has
    been switched off or moved — the trees simply arrived afterwards and grew
    through everything.

    Remastered into the room's material system.  Same five values, same cool
    shadows and warm highlights, same rule that a surface is flat regions and
    the boundaries between them carry the form — but with the chroma let off
    its lead, because this is a dream and the room is not.
    """
    pal = PALETTES["faces"]
    cb = ChipsetBuilder("faces", pal)
    ground = _grove_common(cb, pal, gv.GROVE, "faces")
    _shadows(cb, pal)
    _landmarks(cb, pal, "faces")
    _animate(cb, pal, "faces")
    _decals(cb, pal, "faces", ground)
    return _finish(cb, ground)


def _street(cb: ChipsetBuilder, *, surface: RGB, grit: RGB, marking: RGB,
            kerb_top: RGB, kerb_lip: RGB, marking_wear: float = 0.0,
            seed: int = 0) -> None:
    """The road surface, which every channel of the grove has to provide.

    The street plan is identical on all four channels — it has to be, or they
    are four maps and not four receptions of one — so the *tiles* carry the
    difference.  ``marking_wear`` eats into the lane markings, which is the
    single detail that tells the player how far from the original signal they
    have tuned before they have consciously read anything else.
    """
    road = Canvas(TILE, TILE, surface)
    road.dither(grit, 0.3, ct.BAYER8)
    cb.add("road", road)

    lane = road.copy()
    if marking_wear <= 0:
        lane.rect(7, 0, 3, 10, marking)
    else:
        # the same line, with bites taken out of it
        for y in range(10):
            if ((y * 7 + seed * 5) % 10) / 10.0 >= marking_wear:
                lane.rect(7, y, 3, 1, marking)
            elif ((y * 3 + seed) % 4) == 0:
                lane.rect(8, y, 1, 1, blend(marking, surface, 0.5))
    cb.add("road_line", lane)

    kerb = Canvas(TILE, TILE, surface)
    kerb.dither(grit, 0.2, ct.BAYER8)
    kerb.rect(0, 0, TILE, 5, kerb_top)
    kerb.rect(0, 5, TILE, 2, kerb_lip)
    cb.add("kerb", kerb)


def build_faces2() -> ChipsetBuild:
    """OVERGROWN.  The grove, received on the channel where it never stopped.

    Everything in the grove is here, and everything in the grove has had
    another forty years put on it.  The road is under moss rather than beside
    it, the traffic lights are inside the hedges rather than in front of them,
    and the boundary is not a treeline any more but a wall of thicket.  Nothing
    has been removed.  That is the horror of this one: the town is still all
    present, it is simply no longer reachable.
    """
    pal = PALETTES["faces2"]
    cb = ChipsetBuilder("faces2", pal)
    ground = _grove_common(cb, pal, gv.OVERGROWN, "faces2", tree_rows=5,
                           cap=(236, 208, 120))
    cb.add("moss", gv.moss(gv.OVERGROWN))
    # the two things that only exist here, and both of them are in the way
    cb.add_object("bramble", ct.bramble(pal, 2, 2), solid="all", upper=True)
    cb.add_object("hive", ct.hive(pal, 2, 3), solid="bottom", upper=True)
    _shadows(cb, pal)
    _landmarks(cb, pal, "faces2")
    _animate(cb, pal, "faces2")
    _decals(cb, pal, "faces2", ground)
    return _finish(cb, ground)


def build_faces3() -> ChipsetBuild:
    """OFF-COLOUR.  The grove with the colour going out of it.

    The greens fail first, because they were carrying the most, and what is
    left is the part of the town that was always grey: kerbs, concrete, steel.
    The trees are still standing in exactly the same places and are still the
    same size — they have simply stopped being rendered as anything but their
    branches, which is why this is the channel where you can see through the
    wood, and therefore the channel where things that were hidden by leaves
    are not hidden any more.
    """
    pal = PALETTES["faces3"]
    cb = ChipsetBuilder("faces3", pal)
    ground = _grove_common(cb, pal, gv.OFF_COLOUR, "faces3", bare=True,
                           cap=(196, 200, 198))
    # a thin ash lying over everything, which is what "failing" looks like
    ash = mt.Material("ash", (166, 168, 166))
    dust = Canvas(TILE, TILE, ash.mid)
    mt.plane(dust, 0, 0, TILE, TILE, ash.mid)
    mt.seam(dust, 0, 5, TILE, 4, ash.lit, ash.mid)
    mt.seam(dust, 0, 12, TILE, 3, ash.mid, ash.shade)
    cb.add("ash", dust)
    cb.add_object("aerial", ct.aerial(pal, 2, 4), solid="bottom", upper=True)
    cb.add_object("meter", ct.meter_box(pal, 1, 2), solid="bottom", upper=True)
    _shadows(cb, pal)
    _landmarks(cb, pal, "faces3")
    _animate(cb, pal, "faces3")
    _decals(cb, pal, "faces3", ground)
    return _finish(cb, ground)


def build_faces4() -> ChipsetBuild:
    """NO SIGNAL.  The pattern a transmitter sends when it has nothing to send.

    Everything is still exactly where it was, and nothing is drawn as itself.
    A tree is the symbol for a tree.  Grass is crosshatch.  The road is a run
    of colour bars laid in the direction of travel.  It is the most legible the
    town ever gets — you can read the whole street plan at a glance, because
    the picture has given up on depth entirely — and it is the least like a
    place, which is exactly the trade the channel is making.
    """
    pal = PALETTES["faces4"]
    cb = ChipsetBuilder("faces4", pal)

    # crosshatch where the grass should be: the mark that means "vegetation"
    # Kept dark and low-contrast on purpose: the roads on this channel are
    # full-brightness colour bars, and if the ground is loud too the street
    # plan stops being readable at exactly the moment the picture claims to
    # have become nothing but a diagram.
    ground = Canvas(TILE, TILE, pal.ground)
    for offset in range(-TILE, TILE * 2, 7):
        ground.line(offset, 0, offset + TILE, TILE - 1, pal.ground_b)
    ground_b = Canvas(TILE, TILE, pal.ground_b)
    ground_b.checker(pal.ground, pal.ground_b, 8)
    _basics(cb, pal, ground, ground_b, world="faces4")

    # the road, as bars running along it
    bars = Canvas(TILE, TILE, (24, 22, 26))
    for index, tone in enumerate(((240, 236, 226), (226, 214, 96),
                                  (96, 200, 208), (96, 196, 108),
                                  (208, 92, 178), (206, 58, 54),
                                  (74, 84, 176), (24, 22, 26))):
        bars.rect(0, index * 2, TILE, 2, tone)
    cb.add("road", bars)
    line = bars.copy()
    line.rect(6, 0, 4, TILE, (240, 236, 226))
    cb.add("road_line", line)
    across = Canvas(TILE, TILE, (24, 22, 26))
    for index, tone in enumerate(((240, 236, 226), (226, 214, 96),
                                  (96, 200, 208), (96, 196, 108),
                                  (208, 92, 178), (206, 58, 54),
                                  (74, 84, 176), (24, 22, 26))):
        across.rect(index * 2, 0, 2, TILE, tone)
    across.rect(0, 6, TILE, 4, (240, 236, 226))
    cb.add("road_line_h", across)
    # Four kerbs here too.  This channel is a diagram of the town rather than
    # the town, and a diagram whose pavements run the wrong way is a diagram
    # of somewhere else.
    for side in ("n", "s", "w", "e"):
        stone = Canvas(TILE, TILE, (24, 22, 26))
        near = side in ("n", "w")
        for start, depth, tone in ((0, 5, (240, 236, 226)),
                                   (5, 2, (206, 58, 54))):
            at = start if near else TILE - start - depth
            if side in ("n", "s"):
                stone.rect(0, at, TILE, depth, tone)
            else:
                stone.rect(at, 0, depth, TILE, tone)
        cb.add(f"kerb_{side}", stone)
    plain = Canvas(TILE, TILE, (24, 22, 26))
    plain.rect(0, 0, TILE, 5, (240, 236, 226))
    plain.rect(0, 5, TILE, 2, (206, 58, 54))
    cb.add("kerb", plain)
    cb.add("paving", ct.pattern_tile(pal, "grid", (240, 236, 226),
                                     (36, 24, 28)))
    # the black square: where the picture is not carrying anything at all
    black = Canvas(TILE, TILE, (18, 14, 18))
    black.outline(0, 0, TILE, TILE, (36, 28, 34))
    cb.add("dead", black)

    cb.add_object("tree", ct.tree_glyph(pal, 3, 4), solid="bottom")
    cb.add_object("tree_plain", ct.tree_glyph(pal, 3, 5), solid="bottom")
    cb.add_object("stump", gv.stump(gv.NO_SIGNAL, 2, 2), solid="all")
    cb.add_object("mushroom", gv.mushroom(gv.NO_SIGNAL, (240, 236, 226), 2, 2),
                  solid="bottom")
    marker = ct._canvas(2, 2)
    marker.outline(2, 2, 28, 28, pal.accent)
    marker.line(2, 2, 30, 30, pal.form)
    marker.line(30, 2, 2, 30, pal.form)
    cb.add_object("bush", marker, solid="none", upper=True)
    # the two things that only exist once the picture has stopped
    cb.add_object("tone_pillar", ct.tone_pillar(pal, 1, 4), solid="bottom",
                  upper=True)
    caption = ct._canvas(4, 1)
    caption.rect(0, 3, 64, 10, (18, 14, 18))
    for index in range(11):
        caption.rect(3 + index * 5, 6, 3, 4, (240, 236, 226))
    cb.add_object("caption", caption, solid="none", upper=True)

    # The furniture keeps the shape it has on every other channel and
    # loses its colour: the claim this channel is making is that the town
    # is still there and only the picture has failed, and it stops being
    # true the moment a bus shelter is a different bus shelter.
    cb.add_object("traffic_light", gv.traffic_light(gv.NO_SIGNAL, 1, 4),
                  solid="bottom", upper=True)
    cb.add_object("shelter", gv.bus_shelter(gv.NO_SIGNAL, 4, 3),
                  solid="bottom", upper=True)
    cb.add_object("phone_box", gv.phone_box(gv.NO_SIGNAL, 2, 3),
                  solid="bottom", upper=True)
    cb.add_object("car", gv.dead_car(gv.NO_SIGNAL, 3, 2), solid="all",
                  upper=True)
    cb.add_object("vending", gv.vending_machine(gv.NO_SIGNAL, 2, 3),
                  solid="bottom", upper=True)
    cb.add_object("road_sign", gv.road_sign(gv.NO_SIGNAL, 2, 3),
                  solid="bottom", upper=True)

    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))

    # The four ways in, which this channel carries like the other three: the
    # street plan is shared tile for tile, so an entrance missing here is an
    # entrance that exists on three receptions of one town and not the fourth.
    cb.add_object("crack", gv.rock_split(gv.NO_SIGNAL, 2, 3), solid="all")
    cb.add_object("cover", gv.manhole(gv.NO_SIGNAL, 2, 2), solid="all")
    cb.add_object("hatch", gv.hatch_shed(gv.NO_SIGNAL, 2, 3), solid="all")
    cb.add_object("lock", gv.locked_door(gv.NO_SIGNAL, LOCK_COLOUR["faces4"],
                                         2, 3), solid="all")
    _shadows(cb, pal)
    _landmarks(cb, pal, "faces4")
    _animate(cb, pal, "faces4")
    _decals(cb, pal, "faces4", ground)
    return _finish(cb, ground)


def build_hands() -> ChipsetBuild:
    """A grassy plain with enormous stone hands coming out of it."""
    pal = PALETTES["hands"]
    cb = ChipsetBuilder("hands", pal)

    ground = ct.grass_ground(pal, 0)
    _basics(cb, pal, ground, ct.grass_ground(pal, 2))

    cb.add_object("hand_up", ct.stone_hand(pal, 3, 4, pose="up"), solid="bottom")
    cb.add_object("hand_reach", ct.stone_hand(pal, 3, 4, pose="reach"),
                  solid="bottom")
    cb.add_object("hand_broken", ct.stone_hand(pal, 3, 3, pose="broken"),
                  solid="all")
    cb.add_object("plinth", ct.number_plinth(pal, 3, 2), solid="all")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "hands")
    _animate(cb, pal, "hands")
    _decals(cb, pal, "hands", ground)
    return _finish(cb, ground)


def build_checker() -> ChipsetBuild:
    """Checkerboard country, with the occasional house standing in it."""
    pal = PALETTES["checker"]
    cb = ChipsetBuilder("checker", pal)

    ground = ct.checker_ground(pal.ground, pal.ground_b, 8)
    cb.add("ground", ground)
    cb.add("ground_b", ct.checker_ground(pal.ground_b, pal.ground, 8))
    cb.add("path", ct.checker_ground(pal.ground, pal.form, 4))
    cb.add("glow", ct.glow_pool(pal))
    cb.add("void", ct.void_tile(pal), passable=False)
    cb.add("wall_core", ct.wall_band(pal, "checker"), passable=False)
    cb.add("wall_face", ct.wall_band(pal, "checker", face=True),
           passable=False)

    cb.add_object("house", ct.little_house(pal, pal.accent, 4, 4), solid="bottom2")
    cb.add_object("house_pale", ct.little_house(pal, pal.accent_soft, 4, 4),
                  solid="bottom2")
    cb.add_object("pillar", ct.checker_pillar(pal, 1, 4), solid="bottom")
    cb.add_object("fence", ct.picket_fence(pal, 3, 1), solid="all")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "checker")
    _animate(cb, pal, "checker")
    _decals(cb, pal, "checker", ground)
    return _finish(cb, ground)


def build_toys() -> ChipsetBuild:
    """You are three inches tall and the crayons are pillars."""
    pal = PALETTES["toys"]
    cb = ChipsetBuilder("toys", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.28)
    _basics(cb, pal, ground)

    for index, color in enumerate(((232, 130, 132), (122, 190, 200),
                                   (248, 214, 118))):
        cb.add_object(f"crayon_{index}", ct.crayon(pal, color, 2, 5),
                      solid="bottom")
    cb.add_object("die", ct.die_block(pal, 3, 3, pips=5))
    cb.add_object("die_small", ct.die_block(pal, 2, 2, pips=3))
    cb.add_object("ball", ct.ball_toy(pal, (232, 130, 132), 2, 2), solid="all")
    cb.add_object("rings", ct.ring_stack(pal, 2, 3), solid="bottom")
    cb.add_object("jack", ct.jack_toy(pal, 2, 2), solid="all")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "toys")
    _animate(cb, pal, "toys")
    _decals(cb, pal, "toys", ground)
    return _finish(cb, ground)


def build_neon() -> ChipsetBuild:
    """A black void covered in enormous glowing scrawl.  No sky, no ground."""
    pal = PALETTES["neon"]
    cb = ChipsetBuilder("neon", pal)

    ground = Canvas(TILE, TILE, pal.ground)
    ground.dither(pal.ground_b, 0.18, ct.BAYER8)
    grid = Canvas(TILE, TILE, pal.ground)
    grid.hline(0, 0, TILE - 1, cooler(pal.form_dark, 0.4))
    grid.vline(0, 0, TILE - 1, cooler(pal.form_dark, 0.4))
    _basics(cb, pal, ground, grid)

    for kind in ("eye", "spiral", "mouth", "arrow", "star"):
        cb.add_object(f"scrawl_{kind}", ct.scrawl(pal, kind, 4, 4), solid="none")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "neon")
    _animate(cb, pal, "neon")
    _decals(cb, pal, "neon", ground)
    return _finish(cb, ground)


# The four paintings, from the inside.  Each one is the same construction —
# glowing line on near-black, with the painting's own motif as the floor, the
# wall and the props — and the whole difference between them is which two
# colours they are allowed and which shape everything is made of.  That is a
# deliberately narrow brief: a mural interior that has as many materials as an
# ordinary world is not a mural any more, it is another room.
MURAL_INSIDES: dict[str, dict] = {
    "neon2": dict(motif="eye", wall="rings", floor="concentric",
                  glow=("pulse", 11),
                  decals=(("ring", "form"), ("fingerprint", "accent_soft"),
                          ("spark", "accent")),
                  patterns=("concentric", "dots", "square_frame")),
    "neon3": dict(motif="spiral", wall="coil", floor="spiral",
                  glow=("crawl", 6),
                  decals=(("ripple", "form"), ("glyph", "accent_soft"),
                          ("spark", "accent")),
                  patterns=("concentric", "diamond", "weave")),
    "neon4": dict(motif="mouth", wall="teeth", floor="stripes",
                  glow=("pulse", 8),
                  decals=(("offsquare", "form"), ("crack", "accent_soft"),
                          ("point", "accent")),
                  patterns=("stripes", "chevron", "grid")),
    "neon5": dict(motif="star", wall="rays", floor="cross",
                  glow=("scan", 5),
                  decals=(("fallen_star", "form"), ("spark", "accent"),
                          ("constellation", "accent_soft")),
                  patterns=("cross", "diamond", "dots")),
}


def _mural_inside(key: str):
    """One painting, from inside it."""
    spec = MURAL_INSIDES[key]

    def build() -> ChipsetBuild:
        pal = PALETTES[key]
        cb = ChipsetBuilder(key, pal)

        # The floor is the painting's own line work, drawn *dim*.  The first
        # pass had it at nearly full brightness and the result was a screen
        # with one value on it: floor, wall and prop all shouting the same
        # colour, so nothing had a shape.  A painting's interior is lit by the
        # paint, and paint on the floor is the part furthest from the light.
        ground = ct.pattern_tile(pal, spec["floor"],
                                 blend(pal.form_dark, pal.ground, 0.74),
                                 pal.ground)
        ground_b = ct.pattern_tile(pal, spec["floor"],
                                   blend(pal.form_dark, pal.ground_b, 0.58),
                                   pal.ground_b)
        _basics(cb, pal, ground, ground_b, world=key)

        # The lit line: what the painting is actually made of, and the only
        # thing in here that is allowed to be at full brightness.
        line = Canvas(TILE, TILE, pal.ground)
        line.rect(0, 6, TILE, 4, pal.form)
        line.rect(0, 7, TILE, 2, pal.form_light)
        cb.add("line", line)
        cross = Canvas(TILE, TILE, pal.ground)
        cross.rect(0, 6, TILE, 4, pal.form)
        cross.rect(6, 0, 4, TILE, pal.form)
        cross.rect(7, 7, 2, 2, pal.form_light)
        cb.add("line_cross", cross)
        # and the part of the painting that is not painted
        cb.add("unpainted", ct.void_tile(pal), passable=False)

        for kind in ("eye", "spiral", "mouth", "arrow", "star"):
            cb.add_object(f"scrawl_{kind}", ct.scrawl(pal, kind, 4, 4),
                          solid="none")
        # the motif at landmark scale, standing up off the floor
        cb.add_object("motif", ct.scrawl(pal, spec["motif"], 6, 6),
                      solid="none", upper=True)
        cb.add_object("post", ct.checker_pillar(pal, 1, 4), solid="all",
                      upper=True)
        cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
        _shadows(cb, pal)
        _animate(cb, pal, key)
        _decals(cb, pal, key, ground)
        return _finish(cb, ground)
    return build


for _key, _spec in MURAL_INSIDES.items():
    WALL_MOTIF[_key] = _spec["wall"]
    DECALS[_key] = [tuple(pair) for pair in _spec["decals"]]
    PATTERNS[_key] = list(_spec["patterns"])
    MURALS[_key] = [_spec["motif"] if _spec["motif"] in
                    ("eye", "spiral", "star") else "rings"]
    ANIMATION[_key] = ((_spec["glow"][0], "pulse", "scan"), _spec["glow"])


def build_umbrellas() -> ChipsetBuild:
    """A forest where the trees are umbrellas.  It is not raining."""
    pal = PALETTES["umbrellas"]
    cb = ChipsetBuilder("umbrellas", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.3)
    _basics(cb, pal, ground)

    for index, color in enumerate(((198, 96, 96), (104, 132, 176),
                                   (242, 208, 130))):
        cb.add_object(f"umbrella_{index}", ct.umbrella(pal, color, 3, 4),
                      solid="bottom")
    closed = ct._canvas(1, 3)
    closed.round_rect(6, 4, 5, 40, 2, (198, 96, 96))
    closed.rect(7, 40, 3, 8, pal.form_dark)
    outline_in(closed, cooler((198, 96, 96), 0.4))
    cb.add_object("umbrella_shut", closed, solid="bottom")
    cb.add_object("mushroom", ct.mushroom(pal, (104, 132, 176), 2, 2),
                  solid="bottom")
    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    _shadows(cb, pal)
    _landmarks(cb, pal, "umbrellas")
    _animate(cb, pal, "umbrellas")
    _decals(cb, pal, "umbrellas", ground)
    return _finish(cb, ground)


# The four planes above the umbrella forest.  Each is the same construction —
# a floor, a boundary, and the props that plane happens to be furnished with —
# and the argument the ascent makes is carried entirely by what happens to
# those three as you go up: the floor loses its softness, the boundary gets
# more regular, and the props stop being things and start being fittings.
ASCENT: dict[str, dict] = {
    "umbrellas2": dict(wall="cumulus", floor="bloom", edge=6,
                       props=("umbrella_0", "umbrella_1", "bench", "mushroom"),
                       decals=(("waterring", "accent"), ("puddle", "accent_soft"),
                               ("ripple", "form_dark")),
                       patterns=("bloom", "concentric", "dots"),
                       glow=("flow", 12)),
    "umbrellas3": dict(wall="cornice", floor="square_frame", edge=4,
                       props=("umbrella_0", "column", "bench", "planter"),
                       decals=(("ring", "form_dark"), ("chalkline", "accent_soft"),
                               ("puddle", "accent")),
                       patterns=("square_frame", "grid", "concentric"),
                       glow=("flow", 9)),
    "umbrellas4": dict(wall="lockers", floor="grid", edge=2,
                       props=("column", "cabinet", "bench", "planter"),
                       decals=(("offsquare", "form_dark"), ("tally", "accent_soft"),
                               ("chalkline", "accent")),
                       patterns=("grid", "square_frame", "tick"),
                       glow=("pulse", 7)),
    "umbrellas5": dict(wall="cards", floor="tick", edge=1,
                       props=("cabinet", "counter", "column", "cabinet"),
                       decals=(("tally", "form_dark"), ("cornerpip", "accent_soft"),
                               ("offsquare", "accent")),
                       patterns=("tick", "grid", "stripes"),
                       glow=("scan", 4)),
}


def _plane(key: str):
    """One plane of the ascent."""
    spec = ASCENT[key]

    def build() -> ChipsetBuild:
        pal = PALETTES[key]
        cb = ChipsetBuilder(key, pal)

        ground = ct.pattern_tile(pal, spec["floor"],
                                 blend(pal.form_dark, pal.ground, 0.62),
                                 pal.ground)
        ground_b = ct.soft_ground(pal.ground_b, pal.ground, 0.3)
        _basics(cb, pal, ground, ground_b, world=key)

        # The edge.  On the first plane it is a soft lip you could fall off;
        # by the last it is a painted line, and there is nothing beyond it.
        edge = Canvas(TILE, TILE, pal.ground)
        edge.rect(0, TILE - spec["edge"], TILE, spec["edge"], pal.form_dark)
        edge.rect(0, TILE - spec["edge"] - 1, TILE, 1, pal.form_light)
        cb.add("edge", edge)
        # Water pouring off that edge: the only way down, on every plane.
        fall = Canvas(TILE, TILE, pal.accent_soft)
        fall.dither(pal.form_light, 0.45, ct.BAYER8)
        for column in range(0, TILE, 3):
            fall.vline(column, 0, TILE - 1, pal.form_light)
        cb.add("waterfall", fall)

        cb.add_object("umbrella_0", ct.umbrella(pal, pal.accent, 3, 4),
                      solid="bottom")
        cb.add_object("umbrella_1", ct.umbrella(pal, pal.accent_soft, 3, 4),
                      solid="bottom")
        cb.add_object("mushroom", ct.mushroom(pal, pal.accent_soft, 2, 2),
                      solid="bottom")
        cb.add_object("bench", ct.bench_seat(pal, 3, 2), solid="all",
                      upper=True)
        cb.add_object("column", ct.checker_pillar(pal, 1, 4), solid="all",
                      upper=True)
        cb.add_object("planter", ct.number_plinth(pal, 3, 2), solid="all",
                      upper=True)
        cb.add_object("cabinet", ct.wardrobe(pal, 2, 3), solid="all",
                      upper=True)
        counter = ct._canvas(4, 2)
        counter.rect(0, 8, 64, 20, pal.form)
        counter.rect(0, 8, 64, 3, pal.form_light)
        counter.rect(0, 25, 64, 3, pal.form_dark)
        for x in range(4, 62, 12):
            counter.rect(x, 13, 8, 8, pal.ground_b)
        outline_in(counter, pal.form_dark)
        cb.add_object("counter", counter, solid="all", upper=True)
        cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
        _shadows(cb, pal)
        _animate(cb, pal, key)
        _decals(cb, pal, key, ground)
        return _finish(cb, ground)
    return build


for _key, _spec in ASCENT.items():
    WALL_MOTIF[_key] = _spec["wall"]
    DECALS[_key] = [tuple(pair) for pair in _spec["decals"]]
    PATTERNS[_key] = list(_spec["patterns"])
    MURALS[_key] = ["rings"]
    ANIMATION[_key] = ((_spec["glow"][0], "pulse", "scan"), _spec["glow"])


def build_stars() -> ChipsetBuild:
    """An ocean made of stars.  You can walk on some of it."""
    pal = PALETTES["stars"]
    cb = ChipsetBuilder("stars", pal)

    ground = ct.star_ground(pal, density=3)
    cb.add("ground", ground)
    cb.add("ground_b", ct.star_ground(pal, density=5))
    walkway = Canvas(TILE, TILE, pal.form)
    walkway.rect(0, 0, TILE, 3, pal.form_light)
    walkway.rect(0, TILE - 3, TILE, 3, pal.form_dark)
    cb.add("path", walkway)
    cb.add("glow", ct.glow_pool(pal))
    cb.add("void", ct.void_tile(pal), passable=False)
    cb.add("wall_core", ct.wall_band(pal, "starfield"), passable=False)
    cb.add("wall_face", ct.wall_band(pal, "starfield", face=True),
           passable=False)

    deep = ct.star_ground(pal, density=5)
    deep.mix(pal.void, 0.35)
    cb.add("deep", deep, passable=False, terrain=2)

    cb.add_object("door", ct.door_frame(pal, 2, 3,
                                    reflect=_reflection(cb.name)))
    cb.add_object("lamp", ct.lamp_post(pal, 1, 3), solid="bottom")
    cb.add_object("pole", ct.telephone_pole(pal, 3, 5), solid="bottom")
    cb.add_object("pier", ct.pier(pal, 4, 2), solid="none")
    cb.add_object("island", ct.floating_island(pal, 4, 3), solid="none")
    cb.add_object("buoy", ct.buoy(pal, 1, 2), solid="all")
    _shadows(cb, pal)
    _landmarks(cb, pal, "stars")
    _animate(cb, pal, "stars")
    _decals(cb, pal, "stars", ground)
    return _finish(cb, ground)


BUILDERS: dict[str, Callable[[], ChipsetBuild]] = {
    "room": build_room,
    "balcony": build_balcony,
    "hall5": build_hall,
    "cave1": build_under,
    "box1": build_premises,
    "nexus": build_nexus,
    "pink": build_pink,
    "numbers": build_numbers,
    "blocks": build_blocks,
    "stairs": build_stairs,
    "sand": build_sand,
    "faces": build_faces,
    "hands": build_hands,
    "checker": build_checker,
    "toys": build_toys,
    "neon": build_neon,
    "umbrellas": build_umbrellas,
    "stars": build_stars,
    "faces2": build_faces2,
    "faces3": build_faces3,
    "faces4": build_faces4,
    **{key: _mural_inside(key) for key in MURAL_INSIDES},
    **{key: _plane(key) for key in ASCENT},
}


# Two or three landmarks per world, each unique to it.
LANDMARKS.update({
    "pink": [("knot", lm.knot_of_halls, {"cols": 8, "rows": 8}),
             ("sealed", lm.sealed_room, {"cols": 6, "rows": 5})],
    "numbers": [("calculator", lm.calculator_terrace, {"cols": 7, "rows": 5}),
                ("pierced", lm.pierced_terrace, {"cols": 7, "rows": 6})],
    "blocks": [("monolith", lm.monolith_block,
                {"color": (228, 128, 124), "cols": 7, "rows": 7}),
               ("fractal", lm.fractal_block,
                {"color": (120, 176, 226), "cols": 5, "rows": 5}),
               ("doors", lm.door_slab, {"cols": 5, "rows": 4}),
               ("furniture", lm.furniture_slab, {"cols": 4, "rows": 5})],
    "stairs": [("knot", lm.stair_knot, {"cols": 7, "rows": 7}),
               ("arena", lm.stair_arena, {"cols": 8, "rows": 6})],
    "sand": [("ladders", lm.ladder_forest, {"cols": 6, "rows": 8}),
             ("cathedral", lm.upside_down_cathedral, {"cols": 8, "rows": 7}),
             ("ceramic", lm.ceramic_sea, {"cols": 5, "rows": 3})],
    # The forest world's landmarks are all municipal.  None of them belong.
    # The mast is on every channel and is the only thing in the world drawn
    # identically on all four — it is doing the transmitting, so it is not
    # subject to it.
    "faces": [("facade", lm.apartment_facade, {"cols": 5, "rows": 7}),
              ("escalator", lm.escalator, {"cols": 3, "rows": 5}),
              ("mast", lm.broadcast_mast, {"cols": 3, "rows": 7})],
    "faces2": [("house", lm.swallowed_house, {"cols": 5, "rows": 5}),
               ("mast", lm.broadcast_mast, {"cols": 3, "rows": 7})],
    "faces3": [("dishes", lm.dish_array, {"cols": 5, "rows": 4}),
               ("mast", lm.broadcast_mast, {"cols": 3, "rows": 7})],
    "faces4": [("card", lm.test_card, {"cols": 6, "rows": 5}),
               ("mast", lm.broadcast_mast, {"cols": 3, "rows": 7})],
    "checker": [("circle", lm.circular_room_marker, {"cols": 5, "rows": 5})],
    # Toys is the densest sheet in the game, so its landmarks are sized to
    # fit rather than sized to impress: the brick tower still runs taller than
    # the screen, which is the part that matters.
    "toys": [("tower", lm.brick_tower,
              {"color": (232, 130, 132), "cols": 4, "rows": 9}),
             ("plaza", lm.board_game_plaza, {"cols": 7, "rows": 7}),
             ("junction", lm.track_junction, {"cols": 5, "rows": 5})],
    "neon": [("billboard", lm.billboard_room, {"cols": 7, "rows": 6}),
             ("hanging", lm.hanging_neighbourhood, {"cols": 8, "rows": 7})],
    "umbrellas": [("tower", lm.umbrella_tower,
                   {"color": (198, 96, 96), "cols": 3, "rows": 9}),
                  ("pool", lm.upturned_pool,
                   {"color": (242, 208, 130), "cols": 5, "rows": 4}),
                  ("handles", lm.handle_grove, {"cols": 5, "rows": 4}),
                  ("bridge", lm.rib_bridge, {"cols": 6, "rows": 3})],
    "stars": [("eye", lm.eye_island, {"cols": 6, "rows": 4}),
              ("spiral", lm.spiral_island, {"cols": 6, "rows": 5}),
              ("inverted", lm.inverted_island, {"cols": 5, "rows": 5}),
              ("chair", lm.chair_island, {"cols": 4, "rows": 4})],
    # The procession's monuments.  The colossal hand is twelve tiles tall so
    # it runs off the top of the screen and cannot be seen all at once.
    "hands": [("colossus", lm.colossal_hand, {"cols": 6, "rows": 10}),
              ("ring", lm.hand_ring, {"cols": 7, "rows": 6}),
              ("holding", lm.hand_holding_door, {"cols": 5, "rows": 7})],
})
