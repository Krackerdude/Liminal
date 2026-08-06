"""Inside the four paintings on the floor of the scrawl world.

Four murals in the neon world are also ways into it. Step on one and you are
inside it — a whole map built out of that painting's shape and its two
colours, Mario-64 style, with its own residents, its own thing to carry away
and its own secret. Step on the way out and you are back on the mural, on the
tile you left from.

A painting is a closed object, so unlike the grove these are not a chain: they
can be walked in any order and none of them needs anything from another. What
they *are* is a set. The plaza in the middle of the scrawl world will not
answer to any of the four things on their own, and answers to all four.

The four secrets are all found by doing something the room's own shape invites
and nothing tells you to do:

    the eye      stand in the pupil and stop moving
    the spiral   walk it outward, from the middle, all the way
    the mouth    go all the way down the throat rather than into the pockets
    the star     touch the five tips in the order the points are longest

None of that is written down anywhere in the game.
"""

from __future__ import annotations

import random

from ..cmds import MV_FACE_HERO, Script
from ..maps import (ANIM_CONTINUOUS, LAYER_BELOW, LAYER_SAME, MOVE_RANDOM,
                    MOVE_STATIONARY, TRIGGER_ACTION, TRIGGER_AUTO,
                    TRIGGER_PARALLEL, TRIGGER_TOUCH, Page)
from ..state import (SW_MURAL_ITEM, SW_MURAL_PLAZA, SW_MURAL_SECRET,
                     SW_MURAL_LENS, SW_MURAL_POINT, SW_MURAL_THREAD,
                     SW_MURAL_TOOTH, SW_WORLD_STATE_BASE, VR_MURAL_MAP,
                     VR_MURAL_X, VR_MURAL_Y, VR_STAR_ORDER, VR_STAR_STEP,
                     VR_STILL)
from ..art.cast import WORLD_CAST
from . import atmosphere
from . import systems as sys
from .cast_lookup import charset_slot
from .events import gleam

INSIDES = ("neon2", "neon3", "neon4", "neon5")
PAINTING = {"neon2": "eye", "neon3": "spiral", "neon4": "mouth",
            "neon5": "star"}

_MAP_IDS: dict[str, int] = {}


# --- what each painting keeps -------------------------------------------------

ITEM = {
    "neon2": ("the lens",
              ("something the size of a coin, ground perfectly flat.", "",
               "held up, it does not magnify.",
               "it only makes things further away.")),
    "neon3": ("the thread",
              ("one length of line, wound onto nothing.", "",
               "both ends are loose.",
               "there is no middle you can find.")),
    "neon4": ("the loose tooth",
              ("it came away without any trouble at all.", "",
               "it is still warm.")),
    "neon5": ("the long point",
              ("the point that was longer than the others.", "",
               "it is not attached to anything now",
               "and it is still longer than the others.")),
}

# Where the item is, expressed as a landmark of that interior rather than a
# coordinate: each one is at the far end of whatever the room asks you to do.
ITEM_AT = {"neon2": ("rings", -1), "neon3": ("centre", 0),
           "neon4": ("gums", 11), "neon5": ("tips", 2)}

SECRET = {
    "neon2": (("you stand in the pupil and stop.", "",
               "after a while the rings begin to move",
               "and you understand that they always were,",
               "and that you were going round with them."),
              "the eye"),
    "neon3": (("you have walked it outward.", "",
               "from the inside, a spiral is not a maze.",
               "it is one instruction, repeated,",
               "and you have finished carrying it out."),
              "the spiral"),
    "neon4": (("the throat opens out at the end", "into a room the shape of a room.", "",
               "there is a chair in it, and a lamp,",
               "and the lamp is on."),
              "the mouth"),
    "neon5": (("all five, in the order they are long.", "",
               "the star turns over.", "",
               "on the other side it is the same star,",
               "and one of the points is longer than the others."),
              "the star"),
}

LORE = {
    "neon2": ("someone has written on the inside of the third ring:", "",
              "I PAINTED THIS FROM MEMORY AND THE MEMORY",
              "WAS OF PAINTING IT"),
    "neon3": ("written along the corridor, one word per turn:", "",
              "OUT   IS   THE   SAME   WALK   AS   IN"),
    "neon4": ("scratched into a tooth at eye height:", "",
              "IT IS NOT EATING. IT IS SAYING SOMETHING",
              "VERY SLOWLY."),
    "neon5": ("on the underside of the hub, upside down:", "",
              "FIVE IS AS MANY AS I COULD FIT.",
              "THERE WERE MORE."),
}

# Two residents per painting, and both of them are made of it.
LINES = {
    "lash": ("i grew out of the edge of this.",),
    "iris": ("i am the part that changes.", "", "not much, and not fast."),
    "winding": ("i have been going round since it was drawn.",),
    "unplaced": ("i keep arriving in the middle.", "",
                 "i keep setting off again."),
    "tooth": ("i came out on my own.", "", "nothing pulled."),
    "swallowed": ("it is not as bad as it looks.", "",
                  "it is exactly as slow as it looks."),
    "point": ("there were five of us.",),
    "long_point": ("i am the one that is longer.", "",
                   "i did not ask to be."),
}

# How many of each design stand about, and which landmark they gather on. A
# painting is not a town: two or three of each is a population.
CROWD = {"neon2": ("rings", 3), "neon3": ("turns", 3),
         "neon4": ("gums", 4), "neon5": ("tips", 2)}


# --- the way in and the way out -----------------------------------------------

def _enter(target_key: str, spawn: tuple[int, int]) -> Script:
    """Step onto the painting and be inside it.

    Where you were standing is written down first, so that coming out puts you
    back on the mural instead of at an arrival tile — which is the difference
    between a painting you stepped into and a door you went through.
    """
    s = Script()
    s.var_from_event(VR_MURAL_MAP, 10001, 0)
    s.var_from_event(VR_MURAL_X, 10001, 1)
    s.var_from_event(VR_MURAL_Y, 10001, 2)
    s.se("Appear", volume=64)
    s.flash(255, 255, 255, 26, 3, False)
    s.bgm_fadeout(6)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("neon").leave)
    s.teleport(_MAP_IDS[target_key], *spawn)
    s.fade_in(atmosphere.of("neon").enter)
    return s


def _leave(neon_map_id: int) -> Script:
    """Back out onto the mural, on the tile you stepped in from.

    The map is a literal — there is only one scrawl world to come back to —
    but the coordinates are the ones written down on the way in, which is what
    makes this a painting you climbed out of rather than a second door.
    """
    s = Script()
    s.se("Vanish", volume=60)
    s.bgm_fadeout(6)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("neon").leave)
    s.teleport_var(neon_map_id, VR_MURAL_X, VR_MURAL_Y)
    s.fade_in(atmosphere.of("neon").enter)
    return s


def entrances(neon, worlds: dict, rng: random.Random) -> None:
    """Turn four of the scrawl world's floor paintings into ways in.

    Touch-triggered, not action-triggered: the brief is that you step onto a
    painting and go into it, and having to face a picture on the floor and
    press a button would make it a door.
    """
    _MAP_IDS.update({key: worlds[key].map_id for key in INSIDES})
    m = neon.map
    chambers = list(neon.landmarks.get("chambers", []))
    if not chambers:
        return
    # Spread across the world rather than clustered: four paintings on four
    # sides, so finding the second one is a walk and not a glance.
    spacing = max(1, len(chambers) // 4)
    for index, key in enumerate(INSIDES):
        cx, cy = chambers[(index * spacing + 1) % len(chambers)]
        inside = worlds[key]
        page = Page(script=_enter(key, inside.spawn), trigger=TRIGGER_TOUCH,
                    layer=LAYER_SAME)
        m.add_event(f"into the {PAINTING[key]}", cx % m.width, cy % m.height,
                    [page])
        # a resident of that painting, standing beside its own picture, who
        # has come out and does not say so
        design = WORLD_CAST[key][0]
        sheet, slot = charset_slot(design)
        said = Script()
        said.move_route(0, [MV_FACE_HERO], frequency=8)
        said.msg(*LINES[design])
        m.add_event(f"out of the {PAINTING[key]}", (cx + 4) % m.width,
                    (cy + 2) % m.height,
                    [Page(script=said, charset=sheet, charset_index=slot,
                          trigger=TRIGGER_ACTION, move_type=MOVE_STATIONARY,
                          animation_type=ANIM_CONTINUOUS)])

    # The plaza, which will not answer to any one of the four things and does
    # answer to all four.
    px, py = neon.landmarks["plaza"][0]
    shut = Script()
    shut.se("Wrong", volume=30)
    shut.msg("the painting in the middle is of four things.", "",
             "you are carrying fewer than four things.")

    # A page can hold two switch conditions and the plaza wants four, so the
    # page carries the first two and the script carries the other two.  The
    # short arm has to say the same thing the bare page says, or a player
    # holding two of the four would get silence and read it as a bug.
    from .worlds import WORLD_ORDER

    given = Script()
    with given.if_else_switch(SW_MURAL_TOOTH) as arm:
        with arm(False):
            with given.if_else_switch(SW_MURAL_POINT) as inner:
                with inner(False):
                    given.se("Appear", volume=76)
                    given.msg("you put the lens, the thread, the tooth",
                              "and the long point down on the painting",
                              "in the middle.")
                    given.flash(255, 255, 255, 30, 4, True)
                    given.msg("the floor is a picture of the room you are in.",
                              "",
                              "in the picture, the floor is a picture",
                              "of the room you are in.")
                    given.switch(SW_MURAL_PLAZA, True)
                    given.switch(SW_WORLD_STATE_BASE
                                 + WORLD_ORDER.index("neon"), True)
                    given.se("ChimeFar", volume=60)
                with inner(True):
                    given.se("Wrong", volume=30)
                    given.msg("the painting in the middle is of four things.",
                              "",
                              "you are carrying fewer than four things.")
        with arm(True):
            given.se("Wrong", volume=30)
            given.msg("the painting in the middle is of four things.", "",
                      "you are carrying fewer than four things.")

    after = Script()
    after.msg("the four of them are still lying on it.")

    m.add_event("the middle painting", px % m.width, (py - 6) % m.height, [
        gleam(script=shut, trigger=TRIGGER_ACTION),
        Page(script=given, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             switch_a=SW_MURAL_LENS, switch_b=SW_MURAL_THREAD),
        Page(script=after, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             switch_a=SW_MURAL_PLAZA),
    ])


# --- the secret in each one ---------------------------------------------------

def _eye_secret(world, index: int) -> None:
    """Stand in the pupil and stop.

    The only thing the eye asks of you is the one thing a game normally never
    rewards, which is doing nothing in a specific place.
    """
    x, y = world.landmarks["pupil"][0]
    m = world.map
    watch = Script()
    watch.se("Watch", volume=48)
    watch.msg(*SECRET["neon2"][0])
    watch.flash(214, 254, 250, 24, 6, True)
    watch.switch(SW_MURAL_SECRET + index, True)
    m.add_event("the pupil", x % m.width, y % m.height, [
        # the variable page: the still-counter has to be up before this exists
        Page(script=Script(), trigger=TRIGGER_ACTION),
        Page(script=watch, trigger=TRIGGER_TOUCH, layer=LAYER_SAME,
             variable=(VR_STILL, 40)),
        Page(script=Script(), trigger=TRIGGER_ACTION,
             switch_a=SW_MURAL_SECRET + index),
    ])


def _spiral_secret(world, index: int) -> None:
    """Walk it outward.  There is one marker per turn and they only count up
    if you meet them in the order that runs from the middle out."""
    m = world.map
    turns = list(world.landmarks.get("turns", []))
    for step, (x, y) in enumerate(reversed(turns)):
        mark = Script()
        mark.var(VR_STAR_STEP, step + 1)
        mark.se("Cursor", volume=30)
        wrong = Script()
        wrong.var(VR_STAR_STEP, 0)
        pages = [Page(script=wrong, trigger=TRIGGER_TOUCH, layer=LAYER_SAME)]
        if step:
            pages.append(Page(script=mark, trigger=TRIGGER_TOUCH,
                              layer=LAYER_SAME,
                              variable=(VR_STAR_STEP, step)))
        else:
            pages = [Page(script=mark, trigger=TRIGGER_TOUCH,
                          layer=LAYER_SAME)]
        m.add_event(f"turn {step}", x % m.width, y % m.height, pages)

    x, y = world.landmarks["outer"][0]
    done = Script()
    done.se("ChimeFar", volume=58)
    done.msg(*SECRET["neon3"][0])
    done.flash(254, 200, 234, 26, 6, True)
    done.switch(SW_MURAL_SECRET + index, True)
    m.add_event("all the way out", (x - 2) % m.width, y % m.height, [
        Page(script=Script(), trigger=TRIGGER_ACTION),
        Page(script=done, trigger=TRIGGER_TOUCH, layer=LAYER_SAME,
             variable=(VR_STAR_STEP, max(1, len(turns)))),
        Page(script=Script(), trigger=TRIGGER_ACTION,
             switch_a=SW_MURAL_SECRET + index),
    ])


def _mouth_secret(world, index: int) -> None:
    """Go all the way down rather than into any of the pockets."""
    x, y = world.landmarks["throat"][0]
    m = world.map
    room = Script()
    room.se("Appear", volume=56)
    room.msg(*SECRET["neon4"][0])
    room.flash(255, 190, 176, 22, 5, True)
    room.switch(SW_MURAL_SECRET + index, True)
    seen = Script()
    seen.msg("the lamp is still on.")
    m.add_event("the far end", (x + 3) % m.width, y % m.height, [
        gleam(script=room, trigger=TRIGGER_ACTION),
        Page(script=seen, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             switch_a=SW_MURAL_SECRET + index),
    ])


def _star_secret(world, index: int) -> None:
    """The five tips, in the order the points are longest.

    Each tip folds its own number into a running total the way the stairwell's
    falls do, so the same five tips in a different order come to a different
    answer and only one order comes to the right one.
    """
    m = world.map
    tips = list(world.landmarks.get("tips", []))
    # the order is 2, 4, 1, 3, 0 — nothing in the room says so, and the only
    # clue is which point is drawn longest, which is visible from the hub
    weights = (1, 3, 9, 27, 81)
    for slot, (x, y) in enumerate(tips):
        touch = Script()
        touch.se("Cursor", volume=34)
        touch.var(VR_STAR_ORDER, weights[slot], 1)
        m.add_event(f"tip {slot}", x % m.width, y % m.height,
                    [Page(script=touch, trigger=TRIGGER_TOUCH,
                          layer=LAYER_SAME)])

    hx, hy = world.landmarks["hub"][0]
    total = sum(weights)
    turned = Script()
    turned.se("LowThud", volume=62)
    turned.msg(*SECRET["neon5"][0])
    turned.flash(255, 252, 236, 30, 8, True)
    turned.switch(SW_MURAL_SECRET + index, True)
    m.add_event("the hub", hx % m.width, (hy + 3) % m.height, [
        Page(script=Script(), trigger=TRIGGER_ACTION),
        Page(script=turned, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             variable=(VR_STAR_ORDER, total)),
        Page(script=Script(), trigger=TRIGGER_ACTION,
             switch_a=SW_MURAL_SECRET + index),
    ])


SECRET_OF = {"neon2": _eye_secret, "neon3": _spiral_secret,
             "neon4": _mouth_secret, "neon5": _star_secret}


# --- assembly -----------------------------------------------------------------

def _beside(world, x: int, y: int) -> tuple[int, int]:
    """A standable tile next to ``(x, y)``, preferring the one below it."""
    from .layout import solid_ids

    m = world.map
    solid = solid_ids(world.chipset)
    taken = {(e.x, e.y) for e in m.events}
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1),
                   (0, 2), (2, 0), (0, -2), (-2, 0)):
        px, py = (x + dx) % m.width, (y + dy) % m.height
        if (m.get_lower(px, py) not in solid
                and m.get_upper(px, py) not in solid
                and (px, py) not in taken):
            return px, py
    return (x + 1) % m.width, y % m.height


def _spot(world, where: str, offset: int) -> tuple[int, int]:
    points = list(world.landmarks.get(where, [])) or [world.spawn]
    x, y = points[offset % len(points)]
    return x % world.map.width, y % world.map.height


def inside_events(world, worlds: dict, rng: random.Random) -> None:
    """Everything in one painting: the way out, who is in it, what it keeps."""
    from .events import _arrival_event

    _MAP_IDS.update({key: worlds[key].map_id for key in INSIDES})
    key = world.key
    index = INSIDES.index(key)
    m = world.map
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    # The way out stands *next to* where you came in, not on it.  An event on
    # the arrival tile is one the player is standing inside, and the engine
    # only offers an action to the tile in front of you — so an exit placed
    # where you land is an exit that cannot be used at all.
    ox, oy = _beside(world, *world.spawn)
    out = Page(script=_leave(worlds["neon"].map_id), trigger=TRIGGER_ACTION,
               layer=LAYER_SAME)
    m.add_event("back out", ox, oy, [out])

    # what it keeps
    name, lines = ITEM[key]
    where, offset = ITEM_AT[key]
    ix, iy = _spot(world, where, offset)
    switch = SW_MURAL_ITEM[key]
    got = Script()
    got.se("ItemGet", volume=66)
    got.msg(*lines)
    got.switch(switch, True)
    m.add_event(name, ix, iy, [
        gleam(script=got, trigger=TRIGGER_ACTION),
        Page(script=Script(), trigger=TRIGGER_ACTION, switch_a=switch),
    ])

    # what is written in it
    lore = Script()
    lore.msg(*LORE[key])
    lx, ly = _spot(world, where, offset + 1)
    m.add_event("written here", (lx + 2) % m.width, (ly - 1) % m.height,
                [gleam(script=lore, trigger=TRIGGER_ACTION)])

    # who is in it
    place, copies = CROWD[key]
    spots = list(world.landmarks.get(place, [])) or [world.spawn]
    for design_index, design in enumerate(WORLD_CAST[key]):
        sheet, slot = charset_slot(design)
        for n in range(copies):
            sx, sy = spots[(n * 2 + design_index) % len(spots)]
            sx = (sx + rng.randint(-4, 4)) % m.width
            sy = (sy + rng.randint(-3, 3)) % m.height
            said = Script()
            said.move_route(0, [MV_FACE_HERO], frequency=8)
            said.msg(*LINES[design])
            m.add_event(f"{design} {n}", sx, sy, [
                Page(script=said, charset=sheet, charset_index=slot,
                     move_type=MOVE_STATIONARY if n % 2 else MOVE_RANDOM,
                     move_speed=2, move_frequency=3, trigger=TRIGGER_ACTION,
                     animation_type=ANIM_CONTINUOUS)])

    SECRET_OF[key](world, index)
