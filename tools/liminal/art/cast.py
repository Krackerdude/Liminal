"""The cast.

Who lives in each dream, and what the one thing you will remember about them
is.  Nobody explains themselves and nobody is hostile; they are simply busy
with something that made sense before you arrived.

Charsets are packed eight characters to a sheet.  ``CAST`` maps a sheet name
to its eight slots, and ``WORLD_CAST`` says which of those belong to which
world, so a world's inhabitants never wander into somebody else's dream unless
that is the point.
"""

from __future__ import annotations

from . import kin
from .canvas import Canvas
from .charsets import (Body, creature_block, draw_block_cat, draw_cloud_ladder,
                       draw_cone, draw_floating_eye, draw_long_bird,
                       draw_mailbox, draw_pawn, draw_seedling, draw_shade,
                       draw_television, draw_umbrella_watcher,
                       draw_walking_hand, draw_wind_up, draw_zero,
                       figure_block, sheet)

# The player.  Plain on purpose: everything memorable about them is borrowed
# from whatever they happen to be carrying.
DREAMER = Body(skin=(240, 214, 190), hair=(84, 66, 74), shirt=(132, 152, 196),
               trousers=(78, 74, 96), shoe=(60, 56, 70))


def _variant(**changes) -> Body:
    fields = {f: getattr(DREAMER, f) for f in DREAMER.__annotations__}
    fields.update(changes)
    return Body(**fields)


# Slot 0 of Dreamer is the walking-around self; the rest are what the effects
# turn you into.
DREAMER_SLOTS = [
    ("plain", DREAMER),
    ("lantern", _variant(carry="lantern", glow=(250, 226, 168),
                         feature_color=(214, 178, 110))),
    ("quiet", _variant(translucent=True, faceless=True)),
    ("tall", _variant(tall=9, faceless=True, shirt=(108, 122, 168))),
    ("hat", _variant(feature="cone_hat", feature_color=(226, 156, 118))),
    ("ears", _variant(feature="ears", feature_color=(238, 206, 126))),
    ("coat", _variant(feature="coat", shirt=(92, 84, 118),
                      feature_color=(92, 84, 118))),
    ("pole", _variant(carry="pole", feature_color=(160, 132, 96))),
]

# A charset holds eight, and there are thirteen selves: the plain one and one
# per effect.  The remainder live on a second sheet, and ``equip`` picks the
# sheet from the slot.
DREAMER_SLOTS_B = [
    ("eye", _variant(feature="antenna", feature_color=(226, 246, 244),
                     glow=(180, 232, 228))),
    ("bell", _variant(carry="ring", feature_color=(238, 214, 140))),
    ("key", _variant(carry="can", feature_color=(212, 186, 120))),
    ("stone", _variant(feature="wide_hat", feature_color=(150, 146, 140),
                       shirt=(120, 118, 116), trousers=(84, 82, 80))),
    ("static", _variant(translucent=True, feature="scarf",
                        feature_color=(226, 226, 232), faceless=True)),
]


CAST: dict[str, list[tuple[str, object]]] = {
    # pink / numbers / blocks / stairs
    "KinA": [
        # measures the same wall over and over; the tape has gone much too far
        ("measurer", Body(skin=(238, 208, 200), hair=(196, 132, 156),
                          shirt=(226, 166, 182), trousers=(170, 108, 134),
                          tall=5, carry="tape", feature_color=(250, 240, 236))),
        # a child whose head is one of the bricks
        ("brick_child", Body(skin=(226, 158, 176), hair=(206, 140, 164),
                             shirt=(244, 194, 204), trousers=(178, 114, 138),
                             head_w=14, head_h=13, faceless=True)),
        # keeps count of something
        ("counter", Body(skin=(246, 240, 220), hair=(150, 160, 152),
                         shirt=(168, 210, 198), trousers=(120, 172, 168),
                         feature="antenna", feature_color=(240, 154, 96))),
        ("zero", draw_zero),
        # carrying a block considerably larger than itself
        ("stacker", Body(skin=(240, 214, 190), hair=(96, 82, 74),
                         shirt=(120, 176, 226), trousers=(88, 96, 140),
                         carry="block", feature_color=(228, 128, 124))),
        ("block_cat", draw_block_cat),
        # permanently mid-step, going up nothing
        ("climber", Body(skin=(232, 216, 204), hair=(88, 92, 116),
                         shirt=(208, 206, 216), trousers=(132, 132, 152),
                         feature="scarf", feature_color=(250, 224, 156))),
        ("long_bird", draw_long_bird),
    ],
    # sand / faces / hands / checker
    "KinB": [
        # has been waiting long enough that the hat is the only news
        ("waiting_one", Body(skin=(236, 224, 208), hair=(178, 164, 144),
                             shirt=(214, 202, 180), trousers=(178, 164, 144),
                             feature="wide_hat", feature_color=(120, 128, 148))),
        # too tall, and barely there
        ("sand_walker", Body(skin=(244, 238, 226), hair=(214, 204, 188),
                             shirt=(238, 230, 210), trousers=(206, 196, 178),
                             tall=10, faceless=True, translucent=True)),
        # waters things that are already fine
        ("gardener", Body(skin=(232, 200, 170), hair=(102, 74, 58),
                          shirt=(126, 166, 118), trousers=(92, 132, 96),
                          carry="can", feature_color=(184, 146, 112))),
        ("seedling", draw_seedling),
        ("walking_hand", draw_walking_hand),
        # carries a ring bigger than its head and does not put it down
        ("ring_keeper", Body(skin=(226, 196, 156), hair=(120, 140, 108),
                             shirt=(206, 198, 196), trousers=(150, 140, 144),
                             carry="ring", feature_color=(232, 226, 224))),
        ("pawn", draw_pawn),
        # wears a house
        ("housekeeper", Body(skin=(236, 232, 224), hair=(122, 118, 118),
                             shirt=(202, 198, 192), trousers=(122, 118, 118),
                             feature="tall_hat", feature_color=(198, 84, 78))),
    ],
    # toys / neon / umbrellas / stars
    "KinC": [
        ("wind_up", draw_wind_up),
        ("cone", draw_cone),
        ("floating_eye", draw_floating_eye),
        # drawn in one continuous glowing line
        ("scrawler", Body(skin=(190, 252, 246), hair=(96, 240, 226),
                          shirt=(40, 120, 130), trousers=(28, 90, 100),
                          faceless=True, glow=(96, 240, 226))),
        ("umbrella_watcher", draw_umbrella_watcher),
        # has an umbrella for a head and is perfectly happy
        ("drenched", Body(skin=(198, 96, 96), hair=(140, 66, 74),
                          shirt=(104, 132, 176), trousers=(76, 98, 136),
                          feature="wide_hat", feature_color=(198, 96, 96))),
        # poles a boat that is not there across an ocean that is not water
        ("ferryman", Body(skin=(216, 224, 240), hair=(40, 44, 92),
                          shirt=(70, 78, 140), trousers=(36, 40, 88),
                          tall=7, carry="pole", feature_color=(160, 200, 240))),
        # the only light for a very long way
        ("lantern_bearer", Body(skin=(240, 226, 206), hair=(52, 56, 96),
                                shirt=(120, 130, 196), trousers=(58, 62, 116),
                                carry="lantern", glow=(252, 248, 226),
                                feature_color=(238, 206, 126))),
    ],
    # room / nexus / the ones that follow you
    "KinD": [
        ("mailbox", draw_mailbox),
        ("television", draw_television),
        ("cloud_ladder", draw_cloud_ladder),
        ("shade", draw_shade),
        # sits by the doors and has never once looked up
        ("keeper", Body(skin=(228, 214, 226), hair=(52, 46, 78),
                        shirt=(84, 76, 116), trousers=(48, 44, 72),
                        feature="coat", feature_color=(84, 76, 116))),
        # asleep, standing
        ("sleeper", Body(skin=(238, 216, 200), hair=(96, 78, 88),
                         shirt=(196, 172, 220), trousers=(118, 108, 156),
                         faceless=True)),
        # wears your colours, but taller
        ("twin", Body(skin=(240, 214, 190), hair=(84, 66, 74),
                      shirt=(132, 152, 196), trousers=(78, 74, 96),
                      tall=6, faceless=True)),
        # goes past, every time, in the same direction
        ("wanderer", Body(skin=(232, 210, 196), hair=(70, 62, 74),
                          shirt=(150, 142, 160), trousers=(92, 88, 104),
                          feature="scarf", feature_color=(206, 112, 108))),
    ],
}


# Which sheet slot each named character lives in, once packed.
def slot_of(name: str) -> tuple[str, int]:
    for sheet_name, entries in _sheets().items():
        for index, (entry_name, _) in enumerate(entries):
            if entry_name == name:
                return sheet_name, index
    for index, (entry_name, _) in enumerate(DREAMER_SLOTS):
        if entry_name == name:
            return "Dreamer", index
    raise KeyError(name)



# --- two more residents per populated world ----------------------------------
# Four designs per world is the unit: enough that a crowd is not one sprite
# repeated, few enough that each is recognisably *of* its world.  Worlds with
# no residents get no designs — an empty place does not need a cast.

EXTRA: dict[str, list[tuple[str, object]]] = {
    # pink's four are bespoke drawings; see art/kin.py
    "pink": [],
    "numbers": [
        ("divider", Body(skin=(226, 224, 216), hair=(120, 130, 128),
                         shirt=(186, 198, 194), trousers=(96, 108, 106),
                         tall=4, feature="tall_hat",
                         feature_color=(220, 228, 224))),
        ("remainder", Body(skin=(220, 220, 212), hair=(150, 158, 154),
                           shirt=(168, 180, 176), trousers=(110, 120, 118),
                           feature="scarf", feature_color=(232, 214, 150))),
    ],
    "blocks": [
        ("toppler", Body(skin=(250, 226, 206), hair=(214, 150, 90),
                         shirt=(120, 176, 226), trousers=(196, 108, 104),
                         carry="block", feature_color=(238, 206, 96))),
        ("corner_piece", Body(skin=(246, 220, 200), hair=(96, 132, 190),
                              shirt=(238, 200, 96), trousers=(120, 176, 226),
                              feature="hat", feature_color=(196, 108, 104))),
    ],
    "sand": [
        ("surveyor", Body(skin=(232, 210, 182), hair=(168, 146, 118),
                          shirt=(214, 200, 174), trousers=(150, 134, 108),
                          carry="pole", feature_color=(186, 168, 138))),
        ("half_buried", Body(skin=(226, 204, 176), hair=(150, 130, 104),
                             shirt=(200, 186, 160), trousers=(140, 124, 100),
                             faceless=True, feature="wide_hat",
                             feature_color=(222, 208, 176))),
    ],
    "faces": [
        # waits at a stop that no longer has anything to stop at
        ("commuter", Body(skin=(236, 214, 190), hair=(84, 74, 66),
                          shirt=(96, 118, 96), trousers=(62, 70, 60),
                          feature="coat", feature_color=(96, 118, 96))),
        ("leaf_head", Body(skin=(214, 220, 190), hair=(96, 140, 92),
                           shirt=(140, 176, 118), trousers=(74, 108, 74),
                           feature="antenna", feature_color=(168, 206, 132))),
    ],
    "checker": [
        ("black_square", Body(skin=(228, 228, 232), hair=(38, 38, 44),
                              shirt=(46, 46, 54), trousers=(30, 30, 36),
                              feature="hat", feature_color=(28, 28, 34))),
        ("white_square", Body(skin=(60, 58, 66), hair=(238, 238, 242),
                              shirt=(236, 236, 240), trousers=(210, 210, 216),
                              feature="hat", feature_color=(248, 248, 250))),
    ],
    "toys": [
        ("tin_soldier", Body(skin=(248, 214, 190), hair=(196, 96, 92),
                             shirt=(226, 116, 112), trousers=(84, 96, 152),
                             feature="tall_hat", feature_color=(60, 70, 120))),
        ("spinning_top", Body(skin=(250, 224, 196), hair=(232, 168, 92),
                              shirt=(120, 190, 176), trousers=(230, 150, 96),
                              feature="cone_hat", feature_color=(238, 118, 130))),
    ],
    "neon": [
        ("flicker", Body(skin=(216, 206, 240), hair=(96, 240, 226),
                         shirt=(180, 70, 220), trousers=(56, 40, 96),
                         translucent=True, glow=(120, 250, 236),
                         feature_color=(96, 240, 226))),
        ("sign_holder", Body(skin=(226, 210, 244), hair=(240, 96, 200),
                             shirt=(70, 60, 130), trousers=(40, 34, 78),
                             carry="ring", feature_color=(250, 120, 210))),
    ],
    "umbrellas": [
        ("rain_listener", Body(skin=(226, 220, 214), hair=(96, 110, 124),
                               shirt=(150, 172, 178), trousers=(88, 104, 116),
                               feature="ears", feature_color=(206, 216, 214))),
        ("spoke_keeper", Body(skin=(220, 214, 208), hair=(120, 100, 96),
                              shirt=(178, 148, 140), trousers=(104, 88, 84),
                              carry="pole", feature_color=(196, 96, 96))),
    ],
    "stars": [
        ("wader", Body(skin=(214, 220, 240), hair=(80, 96, 156),
                       shirt=(110, 132, 200), trousers=(58, 70, 128),
                       feature="scarf", feature_color=(200, 216, 250))),
        ("net_caster", Body(skin=(206, 214, 238), hair=(60, 76, 132),
                            shirt=(88, 108, 172), trousers=(44, 56, 108),
                            carry="ring", feature_color=(226, 236, 255))),
    ],
}


# Who belongs to which dream.  A world's residents stay in their world, which
# is what makes it mean something when one of them turns up somewhere else.
WORLD_CAST: dict[str, list[str]] = {
    "room": ["television", "mailbox"],
    "nexus": ["keeper", "sleeper", "cloud_ladder"],
    "pink": ["measurer", "brick_child"],
    "numbers": ["counter", "zero"],
    "blocks": ["stacker", "block_cat"],
    "stairs": ["climber", "long_bird"],
    "sand": ["waiting_one", "sand_walker"],
    "faces": ["gardener", "seedling"],
    "hands": ["walking_hand", "ring_keeper"],
    "checker": ["pawn", "housekeeper"],
    "toys": ["wind_up", "cone"],
    "neon": ["floating_eye", "scrawler"],
    "umbrellas": ["umbrella_watcher", "drenched"],
    "stars": ["ferryman", "lantern_bearer"],
}


# Worlds whose whole cast has been redrawn as bespoke per-facing functions.
BESPOKE: dict[str, dict] = {"pink": kin.PINK, "numbers": kin.NUMBERS,
                            "blocks": kin.BLOCKS,
                            "toys": kin.TOYS,
                            "neon": kin.NEON,
                            "checker": kin.CHECKER,
                            "sand": kin.SAND,
                            "faces": kin.FACES,
                            "umbrellas": kin.UMBRELLAS,
                            "stars": kin.STARS,
                            "room": kin.ROOM,
                            "nexus": kin.NEXUS,
                            "stairs": kin.STAIRS,
                            "hands": kin.HANDS,
                            # the grove's other three channels
                            "faces2": kin.FACES2,
                            "faces3": kin.FACES3,
                            "faces4": kin.FACES4}


def _sheets() -> dict[str, list[tuple[str, object]]]:
    """Every charset, with the extra residents folded in beside the originals.

    The extras live on their own sheets rather than being squeezed into the
    existing four: a sheet holds eight, the originals already fill them, and a
    world needs its four designs reachable by name whatever order they were
    written in.
    """
    out = dict(CAST)
    for world, entries in EXTRA.items():
        out[f"Kin{world.title()}"] = list(entries)
    for world, designs in BESPOKE.items():
        out[f"Kin{world.title()}"] = list(designs.items())
    return out


for _world, _entries in EXTRA.items():
    WORLD_CAST[_world] = WORLD_CAST[_world] + [n for n, _ in _entries]
for _world, _designs in BESPOKE.items():
    WORLD_CAST[_world] = list(_designs)


def build_sheets() -> dict[str, Canvas]:
    """Render every charset file the game needs."""
    out: dict[str, Canvas] = {}
    # An event with no charset does not draw nothing — the engine falls back to
    # a *chipset tile*, and tile zero is the void, so every invisible trigger
    # in the game showed up as a black square sitting next to the thing it was
    # attached to.  An explicitly empty sheet is the only way to mean "no
    # graphic" and be believed.
    out["Blank"] = sheet([])
    out["Dreamer"] = sheet([figure_block(body) for _, body in DREAMER_SLOTS])
    out["DreamerB"] = sheet([figure_block(body) for _, body in DREAMER_SLOTS_B])
    for sheet_name, entries in _sheets().items():
        blocks = []
        for _, spec in entries:
            blocks.append(figure_block(spec) if isinstance(spec, Body)
                          else creature_block(spec))
        out[sheet_name] = sheet(blocks)
    return out
