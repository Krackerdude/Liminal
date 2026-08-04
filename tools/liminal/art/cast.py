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
    for sheet_name, entries in CAST.items():
        for index, (entry_name, _) in enumerate(entries):
            if entry_name == name:
                return sheet_name, index
    for index, (entry_name, _) in enumerate(DREAMER_SLOTS):
        if entry_name == name:
            return "Dreamer", index
    raise KeyError(name)


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
    for sheet_name, entries in CAST.items():
        blocks = []
        for _, spec in entries:
            blocks.append(figure_block(spec) if isinstance(spec, Body)
                          else creature_block(spec))
        out[sheet_name] = sheet(blocks)
    return out
