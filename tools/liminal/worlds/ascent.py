"""Upward, through four planes, and it gets worse the higher you get.

Opening an umbrella under yourself lifts you one plane. That is the whole
verb. There is no ladder, no lift, no stair and nothing that looks like a way
up — only a furled umbrella lying about, and the ordinary act of opening one.

The first plane is cloud: soft, bright, pale, high. Everything about it says
you have arrived somewhere good, and it is laying that on slightly too thick.
Each plane up, the imagery comes apart. The architecture gets more ordered and
less kind. The light gets flatter. The residents get more uniform, then more
identical, then they stop being residents and start being fittings. By the top
it is a bureaucracy with very good lighting.

Nothing is ever named. There is no scripture, no iconography anybody could
point at, nothing that says the word out loud. It is a dream about the *shape*
of an ascent, and it is meant to be readable three different ways depending on
who is playing it.

Coming down is the waterfalls. Every plane pours off its own edge, and
stepping into one drops you the whole way to the bottom in a single go — no
stages, no gentle descent. You arrive back in the soft bright place you
started, which now reads completely differently.
"""

from __future__ import annotations

import random

from ..cmds import MV_FACE_HERO, Script
from ..maps import (ANIM_CONTINUOUS, LAYER_BELOW, LAYER_SAME, MOVE_RANDOM,
                    MOVE_STATIONARY, TRIGGER_ACTION, TRIGGER_TOUCH, Page)
from ..state import (SW_WORLD_SECRET_BASE, SW_WORLD_STATE_BASE, VR_SCRATCH)
from ..art.cast import WORLD_CAST
from . import atmosphere
from . import systems as sys
from .cast_lookup import charset_slot
from .events import gleam

# The forest at the bottom, then four planes.
PLANES = ("umbrellas", "umbrellas2", "umbrellas3", "umbrellas4", "umbrellas5")

_MAP_IDS: dict[str, int] = {}


def height_of(key: str) -> int:
    return PLANES.index(key)


# What opening one says, per plane.  The first is delighted with itself; by
# the last it is a procedure, and the umbrella does not go anywhere because
# there is nothing above the top.
LIFT = {
    0: ("it opens, and it pulls.", "",
        "you come up somewhere with more sky in it."),
    1: ("it opens, and it pulls.", "",
        "the light up here is very even."),
    2: ("it opens.", "", "you are lifted without any sense of rising."),
    3: ("it opens.", "", "you are moved up one."),
    4: ("it opens.", "", "nothing happens.", "",
        "there is nothing above this."),
}

# The waterfall, per plane.  It says less each time, which is the same joke
# the residents are telling.
FALL = {
    1: ("the cloud pours off its own edge here.", "",
        "you step into it."),
    2: ("water goes over the side and does not come back.", "",
        "you step into it."),
    3: ("an overflow, tiled, with a grating.", "", "you step into it."),
    4: ("OVERFLOW", "", "you step into it."),
}

# Who is on each plane, and how much of them there is.  The list gets shorter
# and the lines get fewer, which is the argument made in staffing.
PEOPLE = {
    1: (("umbrella_watcher", ("it is better up here.", "", "it is.")),
        ("drenched", ("i came up wet and i have stayed wet.",)),
        ("rain_listener", ("i can still hear it from up here.", "",
                           "that is the part i did not expect."))),
    2: (("umbrella_watcher", ("it is better up here.",)),
        ("spoke_keeper", ("everything is accounted for.",))),
    3: (("spoke_keeper", ("everything is accounted for.",)),),
    4: (("clerk", ("YES.",)),),
}

CROWD = {1: 3, 2: 4, 3: 6, 4: 8}
WANDER = {1: True, 2: True, 3: False, 4: False}

WHERE = {1: "banks", 2: "courts", 3: "cells", 4: "windows"}

# One thing written on each plane.  Together they are one sentence, and it is
# only readable by somebody who went all the way up.
WRITTEN = {
    1: ("cut into the edge of the cloud, in a good hand:", "",
        "IT IS BETTER HERE"),
    2: ("carved into the third column, in the same hand:", "",
        "IT IS BETTER HERE AND"),
    3: ("stamped into a cabinet, in no hand at all:", "",
        "IT IS BETTER HERE AND THERE IS"),
    4: ("printed, and pinned behind the counter:", "",
        "IT IS BETTER HERE AND THERE IS MORE OF IT"),
}

# What you find at the top for having gone all the way.  Not a reward — the
# only mercy in the place is that the way down exists.
TOP = (
    ("every window is open and every one of them is staffed.",),
    ("you are given a form.", "",
     "it asks how far you have come",
     "and there is no room to write it in."),
    ("you look back down through the floor.", "",
     "the cloud is a long way under you now",
     "and it is the only thing here with a shape."),
)


# --- the verb -----------------------------------------------------------------

def _open_it(height: int) -> Script:
    """Open an umbrella under yourself and be one plane higher."""
    s = Script()
    s.se("Rustle", volume=52)
    s.msg(*LIFT[height])
    if height >= len(PLANES) - 1:
        return s
    s.se("Appear", volume=58)
    s.bgm_fadeout(8)
    s.pan(0, 3, 4, wait=False)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("umbrellas").leave)
    up = PLANES[height + 1]
    s.teleport(_MAP_IDS[up], *_ARRIVE[up])
    s.pan_reset(speed=6, wait=False)
    s.fade_in(atmosphere.of("umbrellas").enter)
    return s


def _step_into(height: int) -> Script:
    """The whole way down, in one go.  No stages."""
    s = Script()
    s.msg(*FALL[height])
    s.se("WaterStep", volume=70)
    s.bgm_fadeout(4)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("umbrellas").leave)
    # every plane drops to the bottom, not to the plane below it: the ascent
    # is a climb and the descent is a fall, and they are not the same shape
    s.teleport(_MAP_IDS["umbrellas"], *_ARRIVE["umbrellas"])
    s.fade_in(atmosphere.of("umbrellas").enter)
    s.se("WaterDrop", volume=40)
    return s


_ARRIVE: dict[str, tuple[int, int]] = {}


# --- assembly -----------------------------------------------------------------

def _free(world, x: int, y: int) -> tuple[int, int]:
    from .layout import solid_ids

    m = world.map
    solid = solid_ids(world.chipset)
    taken = {(e.x, e.y) for e in m.events}
    for step in range(6):
        for dy in range(-step, step + 1):
            for dx in range(-step, step + 1):
                if max(abs(dx), abs(dy)) != step:
                    continue
                px, py = (x + dx) % m.width, (y + dy) % m.height
                if (m.get_lower(px, py) not in solid
                        and m.get_upper(px, py) not in solid
                        and (px, py) not in taken):
                    return px, py
    return x % m.width, y % m.height


def register(worlds: dict) -> None:
    """Every plane needs to know every other plane's number and arrival tile."""
    _MAP_IDS.update({key: worlds[key].map_id for key in PLANES})
    _ARRIVE.update({key: worlds[key].spawn for key in PLANES})


def lifts(world, worlds: dict, rng: random.Random) -> None:
    """The furled umbrellas that go up, on whichever plane this is.

    Placed against the edges of rooms rather than in the middle of them, for
    the same reason everything load-bearing in this game is: a thing you walk
    past on your way in is scenery, and a thing you have to go round a corner
    to find is a discovery.
    """
    from .events import _at_edge

    register(worlds)
    height = height_of(world.key)
    m = world.map
    zones = list(getattr(world.plan, "zones", []) or [])
    # The forest at the bottom is the widest and the one the player meets
    # first, so it carries the most: eighteen umbrellas of which a quarter go
    # anywhere.  A world where every umbrella lifts has no umbrellas in it,
    # only lifts — the ratio is the mechanic.
    count = (18, 8, 7, 6, 4)[height]
    for n in range(count):
        if zones:
            ux, uy = _at_edge(world, zones[(n * 3 + 1) % len(zones)], rng)
        else:
            ux, uy = world.spot(rng, pad=3)
        ux, uy = _free(world, ux, uy)
        shut = Script()
        shut.se("Rustle", volume=34)
        shut.msg("it is furled.", "", "it has never once been needed.")
        m.add_event(f"furled {n}", ux, uy, [
            gleam(script=shut, trigger=TRIGGER_ACTION),
        ] if n % 4 else [
            Page(script=_open_it(height), trigger=TRIGGER_ACTION,
                 layer=LAYER_SAME),
        ])


def plane_events(world, worlds: dict, rng: random.Random) -> None:
    """One plane of the ascent: arrival, the way down, who is on it, and
    the one line of the sentence that is written here."""
    from .events import _arrival_event

    register(worlds)
    height = height_of(world.key)
    m = world.map
    index = _index(world.key)
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    where = WHERE[height]
    spots = list(world.landmarks.get(where, [])) or [world.spawn]

    # The waterfalls.  Three per plane, spread as far apart as the plane
    # allows, because the way down must never be the thing you happen to be
    # standing next to.
    for n in range(3):
        wx, wy = spots[(n * max(1, len(spots) // 3)) % len(spots)]
        wx, wy = _free(world, wx + 5, wy - 4)
        m.add_event(f"the overflow {n}", wx, wy,
                    [Page(script=_step_into(height), trigger=TRIGGER_ACTION,
                          layer=LAYER_SAME)])

    lifts(world, worlds, rng)

    # Who is here.  Wandering and talkative at the bottom; stationary,
    # identical and monosyllabic at the top.
    for design, lines in PEOPLE[height]:
        sheet, slot = charset_slot(design)
        for n in range(CROWD[height]):
            sx, sy = spots[(n * 2 + 1) % len(spots)]
            sx, sy = _free(world, sx + rng.randint(-4, 4),
                           sy + rng.randint(-3, 3))
            said = Script()
            said.move_route(0, [MV_FACE_HERO], frequency=8)
            said.msg(*lines)
            m.add_event(f"{design} {n}", sx, sy, [
                Page(script=said, charset=sheet, charset_index=slot,
                     move_type=MOVE_RANDOM if WANDER[height]
                     else MOVE_STATIONARY,
                     move_speed=2, move_frequency=3, trigger=TRIGGER_ACTION,
                     animation_type=ANIM_CONTINUOUS)])

    # The sentence, one word-group per plane.
    lx, ly = _free(world, spots[len(spots) // 2][0] - 3,
                   spots[len(spots) // 2][1] + 3)
    written = Script()
    written.msg(*WRITTEN[height])
    written.switch(SW_WORLD_SECRET_BASE + index, True)
    m.add_event("written here", lx, ly,
                [gleam(script=written, trigger=TRIGGER_ACTION)])

    if height == len(PLANES) - 1:
        _the_top(world, index)


def _the_top(world, index: int) -> None:
    """The last plane says three things and then stops."""
    m = world.map
    spots = list(world.landmarks.get("windows", [])) or [world.spawn]
    for n, lines in enumerate(TOP):
        tx, ty = spots[(n * 5 + 2) % len(spots)]
        tx, ty = _free(world, tx, ty + 3)
        s = Script()
        s.msg(*lines)
        if n == len(TOP) - 1:
            s.se("ChimeFar", volume=44)
            s.switch(SW_WORLD_STATE_BASE + index, True)
        m.add_event(f"the top {n}", tx, ty,
                    [gleam(script=s, trigger=TRIGGER_ACTION)])


def _index(key: str) -> int:
    from .worlds import WORLD_ORDER

    return WORLD_ORDER.index(key)
