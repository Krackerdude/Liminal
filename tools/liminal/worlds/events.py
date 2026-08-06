"""Per-world events: who is there, what is hidden, and what changes.

Three layers of secret, per the rule that no world should ever feel used up:

**visible**  the effect lying somewhere in the open, and the residents
**hidden**   things that need a condition — an effect equipped, standing still,
             walking a loop, coming back a second time
**deep**     things almost nobody will see: a whole map behind a wall, an
             anomaly with a one-in-a-thousand chance, a place that only exists
             once you have walked far enough

Nothing here explains itself.  There are no journals, no achievement lines and
no NPC who tells you what just happened.  The reward for finding something is
that you saw it.
"""

from __future__ import annotations

import random

from ..art.menu import EFFECTS
from ..cmds import (MSG_BOTTOM, MSG_MIDDLE, MSG_TOP, MV_FACE_DOWN, MV_FACE_HERO,
                    MV_FACE_LEFT, MV_FACE_RANDOM, MV_FACE_RIGHT, MV_FACE_UP,
                    MV_DECREASE_TRANSP, MV_INCREASE_TRANSP, MV_LEFT,
                    MV_RANDOM, MV_RIGHT, MV_UP, MV_DOWN, MV_WAIT, PLAYER,
                    Script)
from ..maps import (ANIM_CONTINUOUS, ANIM_FIXED_GRAPHIC, DIR_DOWN, DIR_LEFT,
                    DIR_RIGHT, DIR_UP, LAYER_BELOW, LAYER_SAME, MOVE_CUSTOM,
                    MOVE_RANDOM, MOVE_STATIONARY, TRIGGER_ACTION,
                    TRIGGER_AUTO, TRIGGER_PARALLEL, TRIGGER_TOUCH, Page)
from ..state import (SW_INTERACT_BASE, SW_WORLD_STATE_BASE, VR_SET_NUMBER,
                     VR_FALL, VR_FALLS, VR_REG_BASE, REG_NAMES, REG_MAX, REG_US, REG_FAR,
                     REG_LIGHT, REG_WAYS, REG_AGO, REG_YOU,
                     SW_DEEP_UNLOCKED, SW_EARS_ACTIVE, SW_EYE_ACTIVE,
                     SW_FOLLOWER, SW_HAS_EFFECT, SW_KEY_ACTIVE,
                     SW_LANTERN_ACTIVE, SW_MENU_OPEN, SW_POLE_ACTIVE,
                     SW_QUIET_ACTIVE, SW_STATIC_ACTIVE, SW_STONE_ACTIVE,
                     SW_TALL_ACTIVE, SW_WOKE_ONCE, SW_WORLD_MEMORY_BASE,
                     SW_WORLD_SECRET_BASE, VR_DREAM_DISTANCE, VR_EQUIPPED,
                     VR_LOOPS, VR_ROLL, VR_SCRATCH, VR_VISITS_BASE, VR_WORLD)
from . import atmosphere, interact
from . import systems as sys
from .cast_lookup import charset_slot
from ..art.cast import WORLD_CAST
from .layout import solid_ids
from .worlds import (BLOCK_ORDER, DREAM_ORDER, HOME_DOOR, HOME_FLOOR,
                     NEXUS_ORDER, POPULATION, WORLD_ORDER, World)

# Interactables draw as the world's own door graphic at a small size, which
# reads as "part of the architecture" rather than as an item lying about.
# Interactables wear a faint pulsing gleam rather than nothing at all.  They
# were on the Blank charset, which made every one of them literally invisible.
_ICON_SHEET, _ICON_SLOT = "Gleam", 0


def gleam(**kwargs) -> Page:
    """A page for something the player can interact with, wearing the gleam.

    Every interactable in the game goes through here.  Two separate mistakes
    made the gleam invisible in the shipped build and both were "somebody
    forgot a keyword": the pages that had the charset did not set
    ``animation_type``, so the sprite never cycled and RPG Maker showed its
    middle frame forever, and the hand-authored items in the grove, the
    paintings and the ascent never got the charset at all and stayed on
    ``Blank``.  Neither is possible now without going out of your way.
    """
    kwargs.setdefault("charset", _ICON_SHEET)
    kwargs.setdefault("charset_index", _ICON_SLOT)
    kwargs.setdefault("animation_type", ANIM_CONTINUOUS)
    kwargs.setdefault("move_type", MOVE_STATIONARY)
    kwargs.setdefault("layer", LAYER_SAME)
    return Page(**kwargs)

# Each interactable owns a switch for the whole playthrough; this hands them
# out in order across every world.
_interact_next = [0]

EFFECT_INDEX = {key: index for index, (key, _, _) in enumerate(EFFECTS, start=1)}

# Which effect is hidden in which dream.  Twelve dreams, twelve effects.
EFFECT_HOME = dict(zip(DREAM_ORDER, [key for key, _, _ in EFFECTS]))


def _free_tile(world: World, x: int, y: int, *, radius: int = 6) -> tuple[int, int]:
    """Nudge a placement off any tile another event is already standing on.

    Two events sharing a tile is legal, and the engine will happily run one of
    them forever while the other can never be talked to.  Landmark-relative
    placements (the keeper beside the bench, a door beside its frame) are the
    ones that collide, because two landmarks can end up next to each other.
    """
    m = world.map
    taken = {(e.x, e.y) for e in m.events}
    x, y = x % m.width, y % m.height
    if (x, y) not in taken:
        return x, y
    for step in range(1, radius + 1):
        for dy in range(-step, step + 1):
            for dx in range(-step, step + 1):
                if max(abs(dx), abs(dy)) != step:
                    continue
                spot = ((x + dx) % m.width, (y + dy) % m.height)
                if spot not in taken:
                    return spot
    return x, y


def _far_from(world: World, origin: tuple[int, int],
              rng: random.Random) -> tuple[int, int]:
    """A standable tile in whichever room is furthest from ``origin``.

    Distance is measured the short way round both axes, because every world
    wraps: a tile near the left edge is next to the right edge, and a naive
    subtraction would call it the other side of the world.
    """
    m = world.map
    zones = list(getattr(world.plan, "zones", []) or [])
    if not zones:
        return world.spot(rng, pad=4)

    def far(zone) -> int:
        dx = abs(((zone.cx - origin[0] + m.width // 2) % m.width) - m.width // 2)
        dy = abs(((zone.cy - origin[1] + m.height // 2) % m.height) - m.height // 2)
        return dx * dx + dy * dy

    return _near(world, max(zones, key=far), rng)


def _near(world: World, zone, rng: random.Random) -> tuple[int, int]:
    """A standable tile inside a zone, biased toward its middle.

    Falls back to the world's own scatter if the room turns out to be full or
    solid, so a crowded zone never silently drops the rest of its residents.
    """
    m = world.map
    solid = solid_ids(world.chipset)
    for _ in range(24):
        x = zone.cx + rng.randint(-zone.w // 3, zone.w // 3)
        y = zone.cy + rng.randint(-zone.h // 3, zone.h // 3)
        if (m.get_lower(x, y) not in solid and m.get_upper(x, y) not in solid):
            return x % m.width, y % m.height
    return world.spot(rng, pad=2)




def _wrapped(m, a: tuple[int, int], b: tuple[int, int]) -> int:
    """Manhattan distance the short way round both axes."""
    dx = abs(((a[0] - b[0] + m.width // 2) % m.width) - m.width // 2)
    dy = abs(((a[1] - b[1] + m.height // 2) % m.height) - m.height // 2)
    return dx + dy


def _at_edge(world: World, zone, rng: random.Random) -> tuple[int, int]:
    """A standable tile against the inside of a room's wall, not its middle.

    Things placed at zone centres read as furniture and get walked past.
    Things placed against the far wall, round a corner from the way in, have
    to be looked for — which is the whole difference between a control panel
    and a discovery.
    """
    m = world.map
    solid = solid_ids(world.chipset)
    half_w, half_h = max(1, zone.w // 2 - 1), max(1, zone.h // 2 - 1)
    for _ in range(40):
        if rng.random() < 0.5:
            x = zone.cx + rng.choice((-half_w, half_w))
            y = zone.cy + rng.randint(-half_h, half_h)
        else:
            x = zone.cx + rng.randint(-half_w, half_w)
            y = zone.cy + rng.choice((-half_h, half_h))
        if (m.get_lower(x, y) not in solid and m.get_upper(x, y) not in solid):
            return x % m.width, y % m.height
    return _near(world, zone, rng)


def _place(world: World, name: str, x: int, y: int, pages) -> None:
    """Add an event at the first tile near ``(x, y)`` that is not taken."""
    world.map.add_event(name, *_free_tile(world, x, y), pages)


def _place_wide(world: World, name: str, x: int, y: int, pages, *,
                reach: int = 1) -> None:
    """The same, plus relays on the tiles around it that do the same thing.

    A shelter is four tiles by three and used to answer on exactly one of
    them, so finding an object and finding its one live pixel were two
    different problems and only the second one was interesting.  This puts the
    same pages on every free tile within ``reach``, so walking up to the thing
    anywhere along its face and pressing the action key works.

    The relays are the identical page list, which means they share the switch
    the real one sets: using any of them marks the object used, and every
    other relay flips to the used page with it.
    """
    m = world.map
    ox, oy = _free_tile(world, x, y)
    m.add_event(name, ox, oy, pages)
    taken = {(e.x, e.y) for e in m.events}
    solid = solid_ids(world.chipset)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dx == 0 and dy == 0:
                continue
            px, py = (ox + dx) % m.width, (oy + dy) % m.height
            if (px, py) in taken:
                continue
            if (m.get_lower(px, py) in solid or m.get_upper(px, py) in solid):
                continue
            m.add_event(f"{name} reach {dx},{dy}", px, py, pages)
            taken.add((px, py))


def _arrival_event(world: World) -> Page:
    """Auto-start on entry: set the world number, grade, then erase itself."""
    index = WORLD_ORDER.index(world.key) + 1
    s = Script()
    # A new game has never set VR_WORLD, and no map is world zero, so this is
    # the only moment in a playthrough when it can still be zero.  Boot is a
    # call-triggered common event, and until this existed nothing called it:
    # every new game started with its state uninitialised.
    with s.if_var(VR_WORLD, 0):
        s.call_event(sys.CE_BOOT)
    s.var(VR_WORLD, index)
    s.call_event(sys.CE_ARRIVE)
    s.erase_event()
    # below the player: nothing talks to this, and it must not stand in a
    # doorway blocking the tile it happens to have been placed on
    return Page(script=s, trigger=TRIGGER_AUTO, layer=LAYER_BELOW)


def _npc_pages(name: str, lines: list[str], *, move=MOVE_RANDOM,
              speed: int = 2, condition_switch: int | None = None,
              quiet_line: str | None = None) -> list[Page]:
    """A resident: wanders, and says one thing that is not an explanation."""
    sheet, slot = charset_slot(name)
    s = Script()
    s.move_route(0, [MV_FACE_HERO], frequency=8)
    s.msg(*lines)
    pages = [Page(script=s, charset=sheet, charset_index=slot, move_type=move,
                  move_speed=speed, move_frequency=3, trigger=TRIGGER_ACTION,
                  animation_type=ANIM_CONTINUOUS)]
    if quiet_line is not None:
        # With QUIET equipped nothing notices you, so they say something else,
        # or nothing at all.
        q = Script()
        q.msg(quiet_line)
        pages.append(Page(script=q, charset=sheet, charset_index=slot,
                          move_type=move, move_speed=speed, move_frequency=2,
                          trigger=TRIGGER_ACTION, switch_a=SW_QUIET_ACTIVE,
                          animation_type=ANIM_CONTINUOUS))
    return pages


def _pickup(effect_key: str) -> Page:
    """The effect, lying where it was left.  Vanishes once taken."""
    s = Script()
    s.var(VR_SCRATCH, EFFECT_INDEX[effect_key])
    s.call_event(sys.CE_GIVE_EFFECT)
    return Page(script=s, charset="Objects", charset_index=0,
                trigger=TRIGGER_ACTION, animation_type=ANIM_CONTINUOUS)


def _door(target_map: int, x: int, y: int, *, sound: str = "DoorOpen",
          leaving: str = "nexus", entering: str = "nexus") -> Page:
    """A door, which comes apart the way one world does and assembles the way
    the other does.  Twenty transitions exist; one fade everywhere wastes
    nineteen of them and makes fourteen places feel like one place."""
    s = Script()
    s.se(sound, volume=70)
    s.bgm_fadeout(8)
    s.weather(0, 0)
    s.pan_reset(speed=6, wait=False)
    s.fade_out(atmosphere.of(leaving).leave)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.teleport(target_map, x, y)
    s.fade_in(atmosphere.of(entering).enter)
    return Page(script=s, trigger=TRIGGER_ACTION)


# --- the room ----------------------------------------------------------------

def room_events(world: World, worlds: dict[str, World]) -> None:
    m = world.map
    m.add_event("arrive", 1, 1, [_arrival_event(world)])

    # The bed: the only way in.
    sleep = Script()
    sleep.msg_options(MSG_MIDDLE)
    sleep.msg("the bed is exactly as you left it.", "", "sleep?")
    with sleep.choice(["yes", "not yet"], cancel=2) as branch:
        with branch(0):
            sleep.msg_options(MSG_BOTTOM)
            sleep.se("Breath", volume=55)
            sleep.bgm_fadeout(18)
            sleep.tint(60, 60, 80, 40, 20, True)
            sleep.fade_out(atmosphere.of("room").leave)
            sleep.wait(8)
            sleep.switch(SW_WOKE_ONCE, True)
            sleep.teleport(worlds["nexus"].map_id, *worlds["nexus"].spawn)
            sleep.tint(100, 100, 100, 100, 0, False)
            sleep.fade_in(atmosphere.of("nexus").enter)
        with branch(1):
            sleep.msg_options(MSG_BOTTOM)
    # the head of the bed, against the back wall: the tile you reach if you
    # walk into the corner, which is how anyone actually crosses a room
    _place(world, "bed", 7, 6, [Page(script=sleep, trigger=TRIGGER_ACTION)])

    # The television: shows the world you were last in.
    tv = Script()
    tv.se("StaticBurst", volume=45)
    tv.show_picture(sys.PIC_FLASH, "Static", 160, 120, transparency=55)
    tv.wait(4)
    tv.erase_picture(sys.PIC_FLASH)
    with tv.if_var(VR_DREAM_DISTANCE, 1, 1):
        tv.msg("something moves on it, a long way off.",
               "it stops when you look directly at it.")
    with tv.if_var(VR_DREAM_DISTANCE, 0):
        tv.msg("it is not plugged in.")
    _place(world, "television", 11, 5, [Page(script=tv, trigger=TRIGGER_ACTION)])

    # The mirror: after you have been away long enough, it is late.
    mirror = Script()
    with mirror.if_var(VR_DREAM_DISTANCE, 4, 1):
        mirror.se("Watch", volume=45)
        mirror.msg("you are still there.", "", "you look tired.")
    with mirror.if_var(VR_DREAM_DISTANCE, 3, 2):
        mirror.msg("you are still there.")
    _place(world, "mirror", 5, 9, [Page(script=mirror, trigger=TRIGGER_ACTION)])

    # The wardrobe: a deep layer, and the only thing in the game with a lock.
    wardrobe = Script()
    with wardrobe.if_else_switch(SW_KEY_ACTIVE) as arm:
        with arm(False):
            wardrobe.se("DoorOpen", volume=60)
            wardrobe.msg("it opens.")
            wardrobe.fade_out(30)      # zoom in
            wardrobe.teleport(worlds["room"].map_id, *worlds["room"].spawn)
            wardrobe.switch(SW_WORLD_MEMORY_BASE, True)
            wardrobe.fade_in(30)
        with arm(True):
            wardrobe.msg("it does not open.",
                         "it has never opened.")
    _place(world, "wardrobe", 14, 6, [Page(script=wardrobe, trigger=TRIGGER_ACTION)])

    # The window: nothing outside, unless you are wearing the eye.
    window = Script()
    with window.if_else_switch(SW_EYE_ACTIVE) as arm:
        with arm(False):
            window.se("Watch", volume=50)
            window.msg("there is a street out there.",
                       "there are streetlights, and a road,",
                       "and it goes on for a very long way.")
            window.wait(10)
            window.msg("none of it is lit from anywhere.")
        with arm(True):
            window.msg("it is too dark to see out.")
    _place(world, "window", 5, 3, [Page(script=window, trigger=TRIGGER_ACTION)])

    desk = Script()
    desk.msg("there is nothing written on it.")
    _place(world, "desk", 3, 7, [Page(script=desk, trigger=TRIGGER_ACTION)])

    # The flat's front door.  It used to be the one door in the game that
    # went nowhere; there is a building on the other side of it now.
    _place(world, "door", 3, 3,
           [_door(worlds["hall4"].map_id, *worlds["hall4"].spawn,
                  sound="Latch", leaving="room", entering="hall4")])

    stand = Script()
    stand.msg("a glass of water you do not remember pouring.")
    _place(world, "nightstand", 10, 5,
           [Page(script=stand, trigger=TRIGGER_ACTION)])

    # The way out to the balcony.  The only door in the room that opens.
    _place(world, "slider", 14, 3,
           [_door(worlds["balcony"].map_id, *worlds["balcony"].spawn,
                  sound="DoorOpen", leaving="room", entering="balcony")])


def balcony_events(world: World, worlds: dict[str, World]) -> None:
    """Outside: a horizon, and four things nobody has moved in a while."""
    m = world.map
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    _place(world, "slider", 10, 12,
           [_door(worlds["room"].map_id, 14, 3, sound="DoorOpen",
                  leaving="balcony", entering="room")])

    rail = Script()
    rail.se("Watch", volume=40)
    rail.msg("the city is on.", "", "not all of it. enough of it.")
    with rail.if_var(VR_DREAM_DISTANCE, 3, 1):
        rail.wait(8)
        rail.msg("some of those windows are the wrong colour",
                 "and you know which ones.")
    for spot in (5, 10, 15):
        _place(world, f"the rail {spot}", spot, 11,
               [Page(script=rail, trigger=TRIGGER_ACTION)])

    chair = Script()
    chair.msg("a plastic chair, facing out.", "",
              "it has been rained on since anybody sat in it.")
    _place(world, "chair", 5, 12, [Page(script=chair, trigger=TRIGGER_ACTION)])

    unit = Script()
    unit.se("Carrier", volume=30)
    unit.msg("it is running.", "", "nothing in the flat is cold.")
    _place(world, "aircon", 14, 11, [Page(script=unit, trigger=TRIGGER_ACTION)])

    bucket = Script()
    bucket.msg("there is water in it.", "", "it has not rained.")
    _place(world, "bucket", 7, 11, [Page(script=bucket, trigger=TRIGGER_ACTION)])


# --- the building -------------------------------------------------------------

# What is written on the doors that do not open.  One line each, none of them
# about the player, and the same door says the same thing on every floor —
# which is how you find out there are only so many kinds of neighbour.
BEHIND = (
    ("a television, turned down.",),
    ("nothing at all.",),
    ("something being moved, slowly, across a floor.",),
    ("two people who stop when you stop.",),
    ("a tap running.",),
    ("nothing. it has been nothing every time.",),
    ("a chain on the inside.",),
)

# Going down, the corridor says less and means more by it.
FLOOR_NOTE = {
    0: ("the top floor.", "", "the ceiling is very close up here."),
    1: (),
    2: ("the third floor.", "", "one of these was yours once."),
    3: ("the second floor.", "", "the carpet stops halfway along."),
    4: ("the ground floor.", "", "it is much colder down here."),
}


def _locked(index: int) -> Script:
    s = Script()
    s.se("Latch", volume=38)
    with s.if_else_switch(SW_EARS_ACTIVE) as arm:
        with arm(True):
            s.msg("it does not open.")
        with arm(False):
            s.msg("it does not open.")
            s.wait(6)
            s.msg("through it:", "", *BEHIND[index % len(BEHIND)])
    return s


def block_events(world: World, worlds: dict[str, World]) -> None:
    """One floor of the apartment block.

    Every door but two is locked, and the two are the stairs.  Nothing here
    is a puzzle: the building is a real place that happens to have exactly
    one thing you can do in it, and the point of the locked doors is that
    somebody is behind each one.
    """
    m = world.map
    depth = BLOCK_ORDER.index(world.key)
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    # the stairs.  Up is nearer the far wall, down nearer the near one, on
    # every floor without exception.
    if depth > 0:
        above = worlds[BLOCK_ORDER[depth - 1]]
        _place(world, "stair up", 4, 8,
               [_door(above.map_id, 4, 9, sound="StepStone",
                      leaving=world.key, entering=above.key)])
    if world.key != "lobby":
        below = worlds[BLOCK_ORDER[depth + 1]]
        _place(world, "stair down", 15, 8,
               [_door(below.map_id, 15, 9, sound="StepStone",
                      leaving=world.key, entering=below.key)])

    # the flats
    index = 0
    for side, row, front in (("north", 2, 4), ("south", 10, 9)):
        for x, _ in world.landmarks.get(side, []):
            if world.key == HOME_FLOOR and side == "north" and x == HOME_DOOR:
                _place(world, "your door", x, front,
                       [_door(worlds["room"].map_id, *worlds["room"].spawn,
                              sound="Latch", leaving=world.key,
                              entering="room")])
            else:
                _place(world, f"{side} {x}", x, front,
                       [Page(script=_locked(index + depth),
                             trigger=TRIGGER_ACTION)])
            index += 1

    lift = Script()
    lift.se("Buzzer", volume=34)
    lift.msg("the button lights.")
    lift.wait(20)
    lift.msg("the indicator does not change.")
    with lift.if_var(VR_DREAM_DISTANCE, 2, 1):
        lift.wait(10)
        lift.msg("it has read the same floor since you moved in",
                 "and you have never once wondered which one.")
    _place(world, "the lift", 15, 9, [Page(script=lift, trigger=TRIGGER_ACTION)])

    if world.key != "lobby":
        board = Script()
        board.msg("a board of notices behind glass.", "",
                  "none of them are new",
                  "and none of them are about anybody you know.")
        _place(world, "the board", 3, 9,
               [gleam(script=board, trigger=TRIGGER_ACTION)])

    note = FLOOR_NOTE.get(depth)
    if note:
        landing = Script()
        landing.msg(*note)
        _place(world, "the landing", 4, 9,
               [gleam(script=landing, trigger=TRIGGER_ACTION)])

    if world.key == "lobby":
        _lobby(world)


def _lobby(world: World) -> None:
    """The ground floor.  Same corridor, none of the light, and the only
    door in the building that is meant to lead outside."""
    out = Script()
    out.se("Latch", volume=44)
    out.msg("locked.")
    out.wait(8)
    out.msg("there is glass in it and nothing behind the glass.")
    with out.if_var(VR_DREAM_DISTANCE, 4, 1):
        out.wait(10)
        out.se("Watch", volume=40)
        out.msg("you have never been outside this building.", "",
                "you have never once thought about that until now.")
    _place(world, "the way out", 10, 9,
           [Page(script=out, trigger=TRIGGER_ACTION)])

    boxes = Script()
    boxes.msg("a wall of little brass doors.", "",
              "one of them has your number on it",
              "and it has never had anything in it.")
    _place(world, "the boxes", 8, 4,
           [Page(script=boxes, trigger=TRIGGER_ACTION)])

    notice = Script()
    notice.msg("four notices, all of them curled.", "",
               "the newest one is about the lift.")
    with notice.if_var(VR_DREAM_DISTANCE, 3, 1):
        notice.wait(8)
        notice.msg("it is dated, and the date is wrong",
                   "in a way you cannot put a number on.")
    _place(world, "the notices", 13, 4,
           [gleam(script=notice, trigger=TRIGGER_ACTION)])

    dark = Script()
    dark.se("Heartbeat", volume=30)
    dark.msg("the last light down here is at the far end", "",
             "and it is behind you.")
    _place(world, "the dark", 16, 8,
           [Page(script=dark, trigger=TRIGGER_ACTION)])


# --- the nexus ---------------------------------------------------------------

def nexus_events(world: World, worlds: dict[str, World]) -> None:
    m = world.map
    m.add_event("arrive", 1, 1, [_arrival_event(world)])

    for index, (x, y) in enumerate(world.landmarks["doors"]):
        key = NEXUS_ORDER[index]
        target = worlds[key]
        # on the door's own bottom tile, so you use it by facing it rather
        # than by standing on top of it
        _place(world, f"door_{key}", x + 1, y + 2,
               [_door(target.map_id, *target.spawn,
                      leaving="nexus", entering=key)])

    # The mirror here shows the room, which is not behind you — and it is the
    # only way back to it.  Twelve doors lead out of the nexus and none of
    # them lead home; without this the room is somewhere you can only ever
    # leave.  Nothing labels it as an exit.  It shows you the room, and if you
    # keep looking, you are in it.
    mirror = Script()
    mirror.se("Watch", volume=40)
    mirror.msg("the room is in it.", "", "you are not.")
    mirror.msg_options(MSG_MIDDLE)
    mirror.msg("keep looking?")
    with mirror.choice(["yes", "no"], cancel=2) as branch:
        with branch(0):
            mirror.msg_options(MSG_BOTTOM)
            mirror.call_event(sys.CE_WAKE)
        with branch(1):
            mirror.msg_options(MSG_BOTTOM)
    mx, my = world.landmarks["mirror"][0]
    _place(world, "mirror", mx + 1, my + 2,
           [Page(script=mirror, trigger=TRIGGER_ACTION)])

    # The keeper sits by the doors and has never looked up.
    kx, ky = world.landmarks["bench"][0]
    _place(world, "keeper", kx + 1, ky + 2, _npc_pages(
        "keeper",
        ["they do not look up.", "", "\"you found the one that was open.\""],
        move=MOVE_STATIONARY,
        quiet_line="they do not look up. they were never going to."))

    # Someone asleep, standing. On a later visit they are gone.
    sx, sy = (m.width // 2 + 6, m.height // 2 - 6)
    gone = Script()
    gone.se("Vanish", volume=40)
    gone.msg("there is a warm patch of floor here.")
    sheet, slot = charset_slot("sleeper")
    _place(world, "sleeper", sx, sy, [
        Page(script=Script().msg("asleep, standing up.", "",
                                 "you decide not to."),
             charset=sheet, charset_index=slot, move_type=MOVE_STATIONARY,
             trigger=TRIGGER_ACTION, animation_type=ANIM_FIXED_GRAPHIC),
        # once you have walked far enough, they are not here any more
        Page(script=gone, trigger=TRIGGER_ACTION,
             variable=(VR_DREAM_DISTANCE, 8)),
    ])

    # A thirteenth door, which is only there when the eye is on.
    hidden = Script()
    hidden.se("DoorOpen", volume=70)
    hidden.bgm_fadeout(10)
    hidden.fade_out(16)
    hidden.call_event(sys.CE_OVERLAY_OFF)
    hidden.teleport(worlds["stars"].map_id, *worlds["stars"].spawn)
    hidden.bgm("Deep", fadein=30, volume=70)
    hidden.fade_in(16)
    _place(world, "thirteenth", m.width // 2, 3, [
        Page(script=hidden, trigger=TRIGGER_ACTION, switch_a=SW_EYE_ACTIVE),
    ])


# --- the dreams --------------------------------------------------------------

def _standing_still(world: World, seconds: int, script: Script) -> Page:
    """A page that fires when the player has not moved for a while.

    Standing still is the only input this game has that is not walking, so it
    is worth rewarding.
    """
    s = Script()
    s.var_from_event(VR_SCRATCH, PLAYER, 1)
    with s.if_var_var(VR_SCRATCH, 14):
        s.wait(seconds * 10)
        s.extend(script)
    s.wait(2)
    return Page(script=s, trigger=TRIGGER_PARALLEL)


def dream_events(world: World, worlds: dict[str, World],
                 rng: random.Random) -> None:
    """Everything a dream gets: residents, its effect, and its secrets."""
    m = world.map
    key = world.key
    index = WORLD_ORDER.index(key)
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    # -- the door.  One per world, standing where you arrived, and the only way
    # out.  Walking away from it is the whole game; walking back to it is the
    # only thing this world will ever ask of you.
    # You come back out of the door you went in, standing in front of it, so
    # the hub keeps its shape: each world has a fixed place in the ring and
    # returning tells you where you have been without anything saying so.
    nexus = worlds["nexus"]
    nx, ny = nexus.landmarks["doors"][NEXUS_ORDER.index(key)]
    back = Script()
    back.se("DoorShut", volume=60)
    back.bgm_fadeout(10)
    back.weather(0, 0)
    back.pan_reset(speed=6, wait=False)
    back.fade_out(atmosphere.of(key).leave)
    back.call_event(sys.CE_OVERLAY_OFF)
    back.teleport(nexus.map_id, nx + 1, ny + 3)
    back.fade_in(atmosphere.of("nexus").enter)
    bx, by = world.landmarks["door_face"][0]
    _place(world, "door", bx, by, [Page(script=back, trigger=TRIGGER_ACTION)])

    # -- the effect that lives here
    effect_key = EFFECT_HOME[key]
    # As far from the door as the world allows.  An effect dropped at a random
    # spot lands next to the arrival tile about as often as anywhere else, and
    # a thing you trip over on the way in is not a thing you found.  On a torus
    # the far side is a real place: the zone whose wrapped distance from the
    # door is greatest.
    ex, ey = _far_from(world, world.spawn, rng)
    got = Script()
    got.var(VR_SCRATCH, EFFECT_INDEX[effect_key])
    got.call_event(sys.CE_GIVE_EFFECT)
    got.switch(SW_WORLD_SECRET_BASE + index, True)
    _place(world, f"effect {effect_key}", ex, ey, [
        Page(script=got, trigger=TRIGGER_ACTION, charset="KinD",
             charset_index=3, animation_type=ANIM_CONTINUOUS,
             move_type=MOVE_STATIONARY),
        # once taken, the spot is empty and stays empty
        Page(script=Script(), trigger=TRIGGER_ACTION,
             switch_a=SW_HAS_EFFECT[effect_key]),
    ])

    # -- residents.  A world's four designs, instanced as many times as its
    # population says, scattered rather than grouped.  Cycling the designs
    # keeps every one of them present in roughly equal numbers; varying the
    # gait per instance is what stops a crowd from reading as one sprite
    # copied twenty times.
    designs = WORLD_CAST.get(key, [])
    if designs:
        # `resident`, not `index` — this loop used to shadow the world index
        # computed above, so every world's memory switch was silently set to
        # 40 + its own population instead of 40 + its own number.
        # Residents belong to *rooms*, not to the map.  Scattering them
        # uniformly over a hundred-and-fifty-tile world puts one every
        # thousand tiles — a screen holds three hundred, so you can walk for
        # minutes and meet nobody, and the ones you do meet are standing in
        # corridors and dead space.  Clustering into a third of the zones
        # means some rooms are busy, most are empty, and the emptiness reads
        # as deliberate because the crowd next door proves it is.
        zones = list(getattr(world.plan, "zones", []) or [])
        rng.shuffle(zones)
        occupied = zones[:max(1, len(zones) // 3)] if zones else []
        for resident in range(POPULATION.get(key, 0)):
            name = designs[resident % len(designs)]
            if occupied:
                zone = occupied[resident % len(occupied)]
                nx, ny = _near(world, zone, rng)
            else:
                nx, ny = world.spot(rng, pad=2)
            # roughly one in five stands still; the rest wander at their own
            # pace, which reads as a place people live rather than a patrol
            still = resident % 5 == 0
            pages = _npc_pages(
                name, NPC_LINES[name],
                move=MOVE_STATIONARY if still else MOVE_RANDOM,
                speed=2 + (resident % 3 == 0),
                quiet_line=NPC_QUIET.get(name))
            # The last page wins, and it is empty: once a world has been
            # altered by its own mechanic, its residents are simply not there
            # any more.  No body, no line, no acknowledgement.
            if key == "numbers":
                # In the number world a resident is present only while the
                # register says there are at least this many.  Turn the
                # number down and they go out one at a time, in front of you,
                # with no ceremony — RPG Maker page conditions are "at least",
                # which is exactly the behaviour this wants.
                first = pages[0]
                pages = [Page(script=Script(), trigger=TRIGGER_ACTION)] + [
                    Page(script=p.script, charset=p.charset,
                         charset_index=p.charset_index, move_type=p.move_type,
                         move_speed=p.move_speed, move_frequency=p.move_frequency,
                         trigger=p.trigger, animation_type=p.animation_type,
                         switch_a=p.switch_a,
                         variable=(VR_REG_BASE + REG_US, resident + 1))
                    for p in pages]
            # The last page wins, and it is empty: once a world has been
            # altered by its own mechanic, its residents are simply not there
            # any more.  No body, no line, no acknowledgement.
            gone = Script()
            gone.se("Vanish", volume=22)
            gone.msg("there is a warm patch of floor here.")
            pages.append(Page(script=gone, trigger=TRIGGER_ACTION,
                              switch_a=SW_WORLD_STATE_BASE + index))
            _place(world, f"{name} {resident}", nx, ny, pages)

    # -- this world's own verb, everywhere in it, and load-bearing.
    #
    # Most of these answer you and nothing more.  Roughly one in four is
    # *live*: it reveals a resident who was not on the map, or opens a way
    # into somewhere the layout seals off.  A world where every brick hides a
    # room has no bricks in it, only doors — the ratio is the mechanic.
    if key == "numbers":
        _numbers_system(world, worlds, rng, index)
    if key.startswith("stairs"):
        _stairs_system(world, worlds, rng, index)
    system = interact.of(key)
    # Three worlds own their verb outright and build it themselves, because in
    # all three the verb *does* something to the world rather than answering
    # you: the counters set a register, the edges fold into a fall order, and
    # the umbrellas lift you a plane.  Leaving the generic version in place
    # alongside meant most of the umbrellas in the forest promised a lift and
    # then did not give one, which is the one thing this game must not do.
    if system is not None and key != "numbers" \
            and key != "umbrellas" \
            and not key.startswith("stairs"):
        zones = list(getattr(world.plan, "zones", []) or [])
        base = SW_INTERACT_BASE + _interact_next[0]
        designs = WORLD_CAST.get(key, [])
        for n in range(system.count):
            # across *all* zones, not the occupied third: the verb has to be
            # in the empty rooms too, or the empty rooms hold nothing
            if zones:
                ix, iy = _near(world, zones[n % len(zones)], rng)
            else:
                ix, iy = world.spot(rng, pad=2)
            switch = base + n
            live = system.live and n % system.live == 0

            touch = Script()
            touch.se(system.sound, volume=40)
            touch.msg(*(system.payoff if live else system.before))
            touch.se(system.done, volume=55 if live else 40)
            if live:
                touch.flash(255, 250, 236, 18, 3, False)
            touch.switch(switch, True)

            after = Script()
            after.se(system.sound, volume=28)
            after.msg(*system.after)

            _place_wide(world, f"{system.thing} {n}", ix, iy, [
                gleam(script=touch, trigger=TRIGGER_ACTION),
                gleam(script=after, trigger=TRIGGER_ACTION, switch_a=switch,
                      translucent=True),
            ])

            if not live:
                continue

            # What a live one leaves behind, alternating so a world gets both
            # kinds: somebody who was not there, and a way that was not there.
            if designs and (n // max(1, system.live)) % 2 == 0:
                hidden = designs[(n // max(1, system.live)) % len(designs)]
                sheet, slot = charset_slot(hidden)
                hx, hy = _near(world, zones[(n + 3) % len(zones)], rng) \
                    if zones else world.spot(rng, pad=2)
                said = Script()
                said.move_route(0, [MV_FACE_HERO], frequency=8)
                said.msg(*NPC_LINES[hidden])
                # no first page at all: until the switch is on, nothing here
                _place(world, f"{hidden} behind {n}", hx, hy, [
                    Page(script=Script(), trigger=TRIGGER_ACTION),
                    Page(script=said, trigger=TRIGGER_ACTION, switch_a=switch,
                         charset=sheet, charset_index=slot,
                         move_type=MOVE_STATIONARY,
                         animation_type=ANIM_CONTINUOUS),
                ])
            else:
                # a way through, at the far end of the world from the door
                wx, wy = _far_from(world, (ix, iy), rng)
                through = Script()
                through.se("DoorOpen", volume=55)
                through.msg("there is a way through here now.")
                through.fade_out(atmosphere.of(key).leave)
                through.teleport(world.map_id, *world.spawn)
                through.fade_in(atmosphere.of(key).enter)
                _place(world, f"way through {n}", wx, wy, [
                    Page(script=Script(), trigger=TRIGGER_ACTION),
                    Page(script=through, trigger=TRIGGER_ACTION,
                         switch_a=switch),
                ])
        _interact_next[0] += system.count

    # -- hidden layer: things that need a condition.  Phase 6 fills this in;
    # until then a world simply has no conditional secrets rather than
    # crashing the build on a name that was never written.
    for maker in HIDDEN.get(key, ()):
        maker(world, worlds, rng)

    # -- world memory: the loop changes what is here
    corrupt = Script()
    corrupt.se("Wrong", volume=40)
    corrupt.msg("this was not here before.")
    corrupt.switch(SW_WORLD_MEMORY_BASE + index, True)
    cx, cy = world.spot(rng, pad=3)
    _place(world, "after the fifth", cx, cy, [
        # invisible until the world has been circled five times
        Page(script=Script(), trigger=TRIGGER_ACTION),
        Page(script=corrupt, trigger=TRIGGER_ACTION, charset="KinD",
             charset_index=2, variable=(VR_LOOPS, 5),
             animation_type=ANIM_CONTINUOUS),
    ])



# --- the number world --------------------------------------------------------

def _numbers_system(world: World, worlds: dict[str, World],
                    rng: random.Random, index: int) -> None:
    """Six numbers, set separately, and the map is whatever they add up to.

    This is not a counter and a door.  The number world keeps six independent
    registers — how many of us, how far, how bright, how many ways, how long
    ago, how many of you — each set on its own plinths, scattered, in no
    order, with no menu.  Each one edits a different property of the map on
    its own, and they read each other: passages want a *combination*, and some
    registers clamp others, so the world you are standing in is the whole
    tuple rather than any one number.

    What each register does, none of which is ever stated:

    ``how many of us``   residents are present up to this number and simply
                         are not, past it.  Turn it down and the world
                         empties in front of you.  Turn it to zero and they
                         are gone permanently, for the rest of the save.
    ``how far``          how much of the world exists.  Distant passages are
                         shut below their own distance.
    ``how bright``       the light.  Low reveals things that are only there
                         in the dark, and hides the ones that need looking at.
    ``how many ways``    how many passages there are at all, and it cannot
                         exceed ``how far``.
    ``how long ago``     the condition of the place.  High is decayed.
    ``how many of you``  above one, you are not the only one walking here.

    A plinth does one thing to one register.  Half of them add and half
    subtract, and which is which is written on them in a language the game
    does not translate.
    """
    from .worlds import POPULATION

    system = interact.of("numbers")
    m = world.map
    altered = SW_WORLD_STATE_BASE + index
    zones = list(getattr(world.plan, "zones", []) or [])
    population = POPULATION.get("numbers", 0)

    placed: dict[int, list[tuple[int, int]]] = {}

    def spot(n: int) -> tuple[int, int]:
        """Where a plinth stands: apart from its own kind, and out of the way.

        Two things matter and neither is "somewhere in this room".  A register
        whose plinths are all in one place is a dial, not a search — so the
        plinths for one register stride across the zone list rather than
        taking the next zone along, which puts the same number's controls on
        opposite sides of the world.

        And they sit at the *edges* of their rooms rather than the middles.
        A plinth in the centre of a chamber is furniture you walk past; a
        plinth against the far wall behind something is a thing you find.
        """
        if not zones:
            return world.spot(rng, pad=2)
        reg = n % len(REG_NAMES)
        run = n // len(REG_NAMES)
        # The stride alone is not enough — zone lists are short and two
        # strides can still land in neighbouring rooms — so the result is
        # checked and rejected.  A register whose plinths turned out to be six
        # tiles apart is a dial with two knobs.
        best_at, best_score = None, -1
        for attempt in range(len(zones)):
            zone = zones[(reg + run * 7 + attempt * 5) % len(zones)]
            at = _at_edge(world, zone, rng)
            kin = min((_wrapped(m, at, other)
                       for other in placed.get(reg, [])), default=999)
            door = _wrapped(m, at, world.spawn)
            if kin >= 40 and door >= 28:
                best_at = at
                break
            score = min(kin, door)
            if score > best_score:
                best_at, best_score = at, score
        at = best_at
        placed.setdefault(reg, []).append(at)
        return at


    def readable(n: int) -> tuple[int, int]:
        return (_near(world, zones[n % len(zones)], rng) if zones
                else world.spot(rng, pad=2))

    # -- the plinths.  Every register gets several, spread apart, so setting
    # one number is itself a walk across the world.
    for n in range(system.count):
        reg = n % len(REG_NAMES)
        var = VR_REG_BASE + reg
        rises = (n // len(REG_NAMES)) % 2 == 0
        step = Script()
        step.se(system.sound, volume=40)
        if rises:
            step.var(var, 1, op=1)
            with step.if_var(var, REG_MAX[reg], 1):
                step.var(var, REG_MAX[reg])
        else:
            step.var(var, 1, op=2)
            with step.if_var(var, 0, 2):
                step.var(var, 0)
        # a register cannot mean more than the world it is in
        if reg == REG_WAYS:
            step.var_from_var(VR_SCRATCH, VR_REG_BASE + REG_FAR)
            step.var_from_var(VR_SCRATCH, var, op=2)
            with step.if_var(VR_SCRATCH, 0, 2):
                step.se("Wrong", volume=30)
                step.var_from_var(var, VR_REG_BASE + REG_FAR)
        step.se(system.done, volume=42)
        step.msg(f"{REG_NAMES[reg]}.", "",
                 "it is showing something different now.")
        _place(world, f"plinth {REG_NAMES[reg]} {n}", *spot(n),
               [Page(script=step, trigger=TRIGGER_ACTION,
                     charset=_ICON_SHEET, charset_index=_ICON_SLOT,
                     animation_type=ANIM_CONTINUOUS)])

    # -- the readout.  One monument in the world states all six at once, and
    # it is the only place the whole state is legible.
    read = Script()
    read.msg_options(MSG_MIDDLE)
    read.msg("six numbers are cut into it.")
    for reg, label in enumerate(REG_NAMES):
        read.msg_value(f"{label}:", VR_REG_BASE + reg)
    read.msg_options(MSG_BOTTOM)
    _place(world, "the readout", *readable(3),
           [Page(script=read, trigger=TRIGGER_ACTION)])

    # -- passages, each wanting a different register at a different value.
    # RPG Maker gives a page one variable condition, so anything wanting two
    # numbers at once is gated by the agreement watcher below.
    for slot, (reg, wanted) in enumerate(
            ((REG_FAR, 7), (REG_LIGHT, 2), (REG_WAYS, 5), (REG_AGO, 8))):
        shut = Script()
        shut.se("Wrong", volume=36)
        shut.msg(f"a number is cut into it: {wanted}.", "",
                 f"({REG_NAMES[reg]}.)")
        open_ = Script()
        open_.se("DoorOpen", volume=58)
        open_.msg("it agrees now.")
        open_.flash(255, 250, 236, 18, 4, False)
        open_.switch(SW_WORLD_SECRET_BASE + index, True)
        _place(world, f"passage {slot}", *_far_from(world, world.spawn, rng), [
            Page(script=shut, trigger=TRIGGER_ACTION),
            Page(script=open_, trigger=TRIGGER_ACTION,
                 variable=(VR_REG_BASE + reg, wanted)),
        ])

    # -- the one that wants everything at once.  Nothing states the
    # combination; the readout states the numbers and the rest is yours.
    deep = Script()
    deep.se("ChimeFar", volume=60)
    deep.msg("all six agree.")
    deep.flash(255, 250, 236, 26, 6, True)
    deep.switch(SW_DEEP_UNLOCKED, True)
    _place(world, "the agreement", *_at_edge(world, zones[-1], rng) if zones else world.spot(rng, pad=3), [
        Page(script=Script().msg("six numbers are cut into it.", "",
                                 "none of them agree."),
             trigger=TRIGGER_ACTION),
        Page(script=deep, trigger=TRIGGER_ACTION,
             switch_a=SW_INTERACT_BASE + 319),
    ])

    # -- zero.  Turning "how many of us" down to nothing does not open a door
    # so much as make the sentence on it true.
    kill = Script()
    kill.se("Wrong", volume=70)
    kill.msg("a number is cut into it.", "", "there is nothing in the cut.")
    kill.wait(12)
    kill.msg("the plinths agree.")
    kill.wait(8)
    kill.bgm_fadeout(6)
    kill.flash(255, 255, 255, 31, 2, True)
    kill.tint(58, 62, 60, 24, 14, True)
    kill.se("LowThud", volume=90)
    kill.switch(altered, True)
    kill.switch(SW_WORLD_MEMORY_BASE + index, True)
    kill.call_event(sys.CE_OVERLAY_OFF)
    kill.show_picture(sys.PIC_OVERLAY, "StaticB", 160, 120, transparency=58,
                      use_transparent_color=True, effect=2, power=9)
    kill.bgm("Wrong", fadein=4, volume=88)
    kill.wait(20)
    kill.msg("it is open.")
    _place(world, "passage zero", *_far_from(
        world, (world.spawn[0] + m.width // 3, world.spawn[1]), rng), [
        Page(script=Script().msg("a number is cut into it.", "",
                                 "there is nothing in the cut."),
             trigger=TRIGGER_ACTION),
        Page(script=kill, trigger=TRIGGER_ACTION,
             variable=(VR_REG_BASE + REG_US, 0)),
        Page(script=Script().msg("it is open."), trigger=TRIGGER_ACTION,
             switch_a=altered),
    ])




def floor_events(world: World, worlds: dict[str, World],
                 rng: random.Random) -> None:
    """A deeper floor of a world: arrival, its edges, and one way home.

    A floor is not a dream — it has no door in the nexus and no effect of its
    own, because it is not somewhere you choose to go.  It gets the world's
    own verb and a single way out, which on the stairwell is the only thing
    down here that goes up.
    """
    from .worlds import WORLD_ORDER

    index = WORLD_ORDER.index(world.key)
    world.map.add_event("arrive", 0, 0, [_arrival_event(world)])
    if world.key.startswith("stairs"):
        _stairs_system(world, worlds, rng, index)

    nexus = worlds["nexus"]
    nx, ny = nexus.landmarks["doors"][NEXUS_ORDER.index("stairs")]
    back = Script()
    back.se("DoorShut", volume=60)
    back.bgm_fadeout(10)
    back.weather(0, 0)
    back.pan_reset(speed=6, wait=False)
    back.fade_out(atmosphere.of("stairs").leave)
    back.call_event(sys.CE_OVERLAY_OFF)
    back.teleport(nexus.map_id, nx + 1, ny + 3)
    back.fade_in(atmosphere.of("nexus").enter)
    _place(world, "door", *_far_from(world, world.spawn, rng),
           [Page(script=back, trigger=TRIGGER_ACTION)])


# --- the stairwell -----------------------------------------------------------

def _stairs_system(world: World, worlds: dict[str, World],
                   rng: random.Random, index: int) -> None:
    """Edges you can step off, and the order you take them is the answer.

    A fall does not simply drop you one floor.  Each edge has a number, and
    stepping off folds that number into a running total — so four falls taken
    in a different sequence produce a different total, and the total decides
    which floor you land on.  The same edges, in a different order, are a
    different route.

    This is the quicksand-pit structure: every entrance looks like every other
    entrance, nothing is labelled, and the deepest floors can only be reached
    by an order nobody stumbles into.  The world never mentions that order is
    what matters.
    """
    from .worlds import DEPTH, STAIR_FLOORS

    system = interact.of("stairs")
    depth = DEPTH.get(world.key, 0)
    floors = ["stairs", *STAIR_FLOORS]
    zones = list(getattr(world.plan, "zones", []) or [])

    for n in range(system.count):
        at = (_at_edge(world, zones[n % len(zones)], rng) if zones
              else world.spot(rng, pad=2))
        # each edge is worth a different amount, and the amounts are chosen so
        # that order changes the sum: multiply by three, then add
        weight = 1 + (n * 5 + depth * 3) % 7

        fall = Script()
        fall.se(system.sound, volume=45)
        fall.msg(*system.before)
        fall.wait(6)
        fall.se("Wrong", volume=30)
        fall.msg("you step off it.")
        # fold this edge into the running order
        fall.var(VR_FALL, 3, op=3)               # multiply the history by three
        fall.var(VR_FALL, weight, op=1)          # then add this edge
        fall.var(VR_FALL, 97, op=5)              # keep it inside one number
        fall.var(VR_FALLS, 1, op=1)
        fall.bgm_fadeout(4)
        fall.fade_out(atmosphere.of("stairs").leave)
        fall.wait(10)
        fall.call_event(sys.CE_OVERLAY_OFF)

        # where the total lands you.  Every branch is a real floor; none of
        # them is "back where you started" unless the order says so.
        for slot, target in enumerate(floors):
            other = worlds.get(target)
            if other is None:
                continue
            with fall.if_var(VR_FALL, slot * 19, 0):
                fall.teleport(other.map_id, *other.spawn)
        # anything the branches did not catch falls to the floor below, or
        # back to the top if there is nothing below
        below = floors[min(depth + 1, len(floors) - 1)]
        with fall.if_var(VR_FALL, 0, 3):        # always true; the default
            pass
        fall.teleport(worlds[below].map_id, *worlds[below].spawn)
        fall.fade_in(atmosphere.of("stairs").enter)

        _place(world, f"edge {n}", *at,
               [Page(script=fall, trigger=TRIGGER_ACTION,
                     charset=_ICON_SHEET, charset_index=_ICON_SLOT,
                     animation_type=ANIM_CONTINUOUS)])


# --- what the residents say --------------------------------------------------
# One line each, and none of it is information.

NPC_LINES: dict[str, list[str]] = {
    "measurer": ["\"it is the same as yesterday.\"", "",
                 "they write nothing down."],
    "brick_child": ["they are the same colour as the wall.", "",
                    "they do not seem to mind."],
    "counter": ["\"four hundred and six.\"", "", "\"...four hundred and seven.\""],
    "zero": ["it rolls a little to face you.", "", "it is empty in the middle."],
    "stacker": ["\"i am nearly finished.\"", "",
                "the tower behind them is two blocks tall."],
    "block_cat": ["it looks at you with its whole body.", "",
                  "the ears do not move."],
    "climber": ["\"nearly there.\"", "", "they have not moved."],
    "long_bird": ["it turns its head all the way round to see you", "",
                  "and then all the way back."],
    "waiting_one": ["\"not yet.\"", "", "the hat does not move at all."],
    "sand_walker": ["they are very far away.", "",
                    "they were very far away when you started walking."],
    "gardener": ["\"they are all doing fine.\"", "",
                 "they water something that is already wet."],
    "seedling": ["it follows you for three steps and then forgets."],
    "walking_hand": ["it walks around you, not away from you."],
    "ring_keeper": ["\"it is not mine.\"", "", "they do not put it down."],
    "pawn": ["it can only move forwards.", "", "it is not in a hurry."],
    "housekeeper": ["\"there is nobody in.\"", "",
                    "the house on their head is dark."],
    "wind_up": ["the key turns whether or not they are walking."],
    "cone": ["it moves aside for you.", "", "there is nothing behind it."],
    "floating_eye": ["it blinks after you do."],
    "scrawler": ["they are drawn in one line.", "",
                 "you can see where it started."],
    "umbrella_watcher": ["it turns to face you.", "", "it is not raining."],
    "drenched": ["\"it will, eventually.\""],
    "ferryman": ["\"there is nowhere to go.\"", "", "they keep poling anyway."],
    "lantern_bearer": ["they are the only light for a very long way.", "",
                       "they do not seem to know."],
    "keeper": ["they do not look up."],
    "sleeper": ["asleep, standing up."],
    "cloud_ladder": ["it is carrying a ladder.", "", "there is nothing to lean it on."],
    "television": ["it is pleased to see you."],
    "mailbox": ["there is nothing in it.", "", "the flag is up anyway."],
}

NPC_LINES.update({
    "wall_ear": ["they have their ear against the wall.", "",
                 "they hold up a hand so you will be quiet."],
    "brick_carrier": ["\"i am putting it back.\"", "",
                      "they have been going the other way."],
    "divider": ["\"it goes in twice.\"", "", "\"and then once more.\""],
    "remainder": ["\"there is always a bit left over.\""],
    "toppler": ["they are holding it very carefully.", "",
                "it was never going to stay up."],
    "corner_piece": ["\"i only fit in one place.\"", "",
                     "they are not in it."],
    "surveyor": ["they are measuring something a long way off.", "",
                 "there is nothing a long way off."],
    "half_buried": ["only the hat is above the sand.", "", "it turns to follow you."],
    "commuter": ["they are waiting at a stop.", "",
                 "nothing has come past for a long time."],
    "leaf_head": ["something is growing out of the top of their head.", "",
                  "they seem pleased about it."],
    "black_square": ["\"i can only go diagonally.\"", "",
                     "they demonstrate. it is not diagonal."],
    "white_square": ["they stand on white and will not step off it."],
    "tin_soldier": ["they salute something behind you.", "",
                    "there is nothing behind you."],
    "spinning_top": ["they have been turning for a while.", "",
                     "they do not seem dizzy."],
    "flicker": ["they are only there some of the time."],
    "sign_holder": ["they hold up a ring and look through it at you."],
    "rain_listener": ["\"listen.\"", "", "it is not raining. it has never rained."],
    "spoke_keeper": ["they are carrying the handle without the umbrella."],
    "wader": ["they are standing in it up to the knee.", "",
              "there is nothing to stand in."],
    "net_caster": ["they cast the ring out over the water and pull it back.", "",
                   "it is always empty. they do it again."],
})

NPC_LINES.update({
    "coat_stand": ["it is wearing everything you own.", "",
                   "none of it is yours any more."],
    "clock": ["it is right twice a day.", "", "neither time is now."],
    "doorframe": ["a door with nothing behind it.", "",
                  "it is looking for a wall."],
    "handrail": ["it would like to be held on to.", "", "you keep walking."],
    "descender": ["they are going down.", "", "there is no down here."],
    "thumb": ["it has an opinion.", "", "it will not give it."],
    "clasp": ["two hands, holding each other.", "",
              "neither of them is anybody's."],
})

# Per-world conditional secrets, keyed by world.  Empty until Phase 6.
HIDDEN: dict[str, list] = {}


NPC_QUIET: dict[str, str] = {
    "measurer": "they measure straight through where you are standing.",
    "counter": "\"four hundred and six.\" the number does not change.",
    "gardener": "they water the ground where you are standing.",
    "umbrella_watcher": "it does not turn.",
    "floating_eye": "it looks past you.",
    "cone": "it does not move aside. you walk around it.",
    "housekeeper": "the house on their head has a light on now.",
    "climber": "they are further up than they were.",
}
