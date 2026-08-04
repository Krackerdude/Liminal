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
from . import landmarks as lm
from .canvas import Canvas, TRANSPARENT, blend, cooler, outline_in, warmer
from .chipsets import ChipsetBuild, ChipsetBuilder
from .palette import PALETTES, Palette

TILE = ct.TILE


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
}


# Where a world's boundary is made of something other than its prop material.
# The forest is the case that matters: its props are brown trunks, but the wall
# containing the player is a solid mass of canopy.
WALL_COLORS: dict[str, dict] = {
    "faces": {"base": (74, 118, 76), "light": (104, 152, 100),
              "dark": (38, 66, 46), "accent": (146, 186, 132)},
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
}

MURALS: dict[str, list[str]] = {
    "room": ["rings"], "nexus": ["rings", "eye"],
    "pink": ["rings", "lattice"], "numbers": ["grid", "rings"],
    "blocks": ["sun", "grid"], "stairs": ["spiral", "lattice"],
    "sand": ["rings", "sun"], "faces": ["eye", "sun"],
    "hands": ["hand", "rings"], "checker": ["grid", "star"],
    "toys": ["sun", "star"], "neon": ["eye", "spiral", "star"],
    "umbrellas": ["waves", "rings"], "stars": ["star", "waves"],
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
           "paper": "strata", "doors": "brick"}.get(motif, "brick")
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

def build_room() -> ChipsetBuild:
    """The room you wake up in.  Ordinary on purpose, so leaving it counts."""
    pal = PALETTES["room"]
    cb = ChipsetBuilder("room", pal)

    boards = Canvas(TILE, TILE, pal.ground)
    boards.rect(0, 0, TILE, 1, warmer(pal.ground, 0.25))
    boards.vline(0, 0, TILE - 1, cooler(pal.ground, 0.14))
    boards.vline(8, 0, TILE - 1, cooler(pal.ground, 0.10))
    _basics(cb, pal, boards)
    rug = Canvas(TILE, TILE, pal.accent_soft)
    rug.dither(pal.accent, 0.35)
    cb.add("rug", rug)

    cb.add_object("wall", ct.wall_run(pal, height=3, brick=False))
    cb.add_object("door", ct.door_frame(pal, leaf=pal.form_dark))
    # The near and side walls, one tile deep, so the room is a room and not a
    # slab of floor with a headboard.  Without these there is only one wall to
    # put anything against, and everything ends up in a row along it.
    cb.add("skirt", ct.wall_run(pal, height=1, brick=False), passable=False)

    bed = ct._canvas(2, 3)
    bed.round_rect(1, 4, 30, 42, 5, pal.form)
    bed.round_rect(3, 6, 26, 16, 4, pal.form_light)
    bed.round_rect(3, 24, 26, 20, 4, pal.accent_soft)
    bed.round_rect(1, 0, 30, 8, 4, pal.form_dark)
    outline_in(bed, cooler(pal.form_dark, 0.3))
    cb.add_object("bed", bed, solid="all")

    desk = ct._canvas(2, 2)
    desk.round_rect(1, 8, 30, 12, 3, pal.form_dark)
    desk.rect(4, 20, 4, 11, cooler(pal.form_dark, 0.2))
    desk.rect(24, 20, 4, 11, cooler(pal.form_dark, 0.2))
    outline_in(desk, cooler(pal.form_dark, 0.45))
    cb.add_object("desk", desk, solid="bottom")

    cb.add_object("wardrobe", ct.wardrobe(pal, 2, 3), solid="all")
    cb.add_object("television", ct.old_television(pal, 2, 2), solid="all")
    cb.add_object("mirror", ct.standing_mirror(pal, 2, 3), solid="all")

    window = ct._canvas(2, 2)
    window.round_rect(2, 2, 28, 26, 3, pal.form_dark)
    window.rect(5, 5, 22, 20, pal.void)
    window.vline(15, 5, 24, pal.form_dark)
    window.hline(14, 5, 26, pal.form_dark)
    cb.add_object("window", window, solid="none", upper=True)

    cb.add_upper("lamp", ct.lamp_post(pal, 1, 1).sub(0, 0, TILE, TILE), above=True)
    _shadows(cb, pal)
    _landmarks(cb, pal, "room")
    _animate(cb, pal, "room")
    _decals(cb, pal, "room", boards)
    return _finish(cb, boards)


def build_nexus() -> ChipsetBuild:
    """Between the dreams: soft dark, and doors that are not in any wall."""
    pal = PALETTES["nexus"]
    cb = ChipsetBuilder("nexus", pal)

    ground = ct.soft_ground(pal.ground, pal.ground_b, 0.35)
    _basics(cb, pal, ground)

    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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


def build_faces() -> ChipsetBuild:
    """A CITY THE FOREST GREW THROUGH.

    Not a forest.  A forest is a place; this is a place that used to be a
    different place.  The roads still have their lane markings, the traffic
    lights are still cycling, the windows are still lit, and none of it has
    been switched off or moved — the trees simply arrived afterwards and grew
    through everything.
    """
    pal = PALETTES["faces"]
    cb = ChipsetBuilder("faces", pal)

    ground = ct.grass_ground(pal, 0)
    _basics(cb, pal, ground, ct.grass_ground(pal, 1))

    # asphalt, still marked out in lanes nobody is driving in
    road = Canvas(TILE, TILE, (62, 62, 68))
    road.dither((54, 54, 60), 0.3, ct.BAYER8)
    cb.add("road", road)
    lane = Canvas(TILE, TILE, (62, 62, 68))
    lane.dither((54, 54, 60), 0.3, ct.BAYER8)
    lane.rect(7, 0, 3, 10, (226, 222, 200))
    cb.add("road_line", lane)
    kerb = Canvas(TILE, TILE, (62, 62, 68))
    kerb.rect(0, 0, TILE, 5, (168, 166, 162))
    kerb.rect(0, 5, TILE, 2, (120, 118, 116))
    cb.add("kerb", kerb)
    paving = ct.pattern_tile(pal, "grid", (150, 148, 146), (176, 174, 170))
    cb.add("paving", paving)

    cb.add_object("tree", ct.round_tree(pal, 3, 4, face=True), solid="bottom")
    cb.add_object("tree_plain", ct.round_tree(pal, 3, 4, face=False),
                  solid="bottom")
    cb.add_object("stump", ct.stump_face(pal, 2, 2), solid="all")
    cb.add_object("mushroom", ct.mushroom(pal, (216, 128, 118), 2, 2),
                  solid="bottom")
    bush = ct._canvas(2, 2)
    bush.blob(16, 20, 13, pal.accent_soft)
    bush.blob(9, 22, 8, pal.accent_soft)
    bush.blob(23, 22, 8, pal.accent_soft)
    bush.blob(13, 15, 6, warmer(pal.accent_soft, 0.22))
    outline_in(bush, cooler(pal.accent_soft, 0.4))
    cb.add_object("bush", bush, solid="bottom")

    # Street furniture, scattered through the trees as though the town was
    # never cleared — only grown over.
    # Upper layer, no ground baked in: every one of these stands on asphalt,
    # kerb and grass alike, and must show whichever is really underneath.
    cb.add_object("traffic_light", lm.traffic_light(pal, 1, 4), solid="bottom",
                  upper=True)
    cb.add_object("shelter", lm.bus_shelter(pal, 4, 3), solid="bottom",
                  upper=True)
    cb.add_object("phone_box", lm.phone_box(pal, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("car", lm.dead_car(pal, 3, 2), solid="all", upper=True)
    cb.add_object("vending", lm.vending_machine(pal, 2, 3), solid="bottom",
                  upper=True)
    cb.add_object("road_sign", lm.road_sign(pal, 2, 3), solid="bottom",
                  upper=True)

    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
    _shadows(cb, pal)
    _landmarks(cb, pal, "faces")
    _animate(cb, pal, "faces")
    _decals(cb, pal, "faces", ground)
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
    _shadows(cb, pal)
    _landmarks(cb, pal, "neon")
    _animate(cb, pal, "neon")
    _decals(cb, pal, "neon", ground)
    return _finish(cb, ground)


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
    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
    _shadows(cb, pal)
    _landmarks(cb, pal, "umbrellas")
    _animate(cb, pal, "umbrellas")
    _decals(cb, pal, "umbrellas", ground)
    return _finish(cb, ground)


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

    cb.add_object("door", ct.door_frame(pal, 2, 3, glow=pal.accent))
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
    "faces": [("facade", lm.apartment_facade, {"cols": 5, "rows": 7}),
              ("escalator", lm.escalator, {"cols": 3, "rows": 5})],
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
