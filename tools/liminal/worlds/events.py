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
from ..state import (SW_INTERACT_BASE, SW_DEEP_UNLOCKED, SW_EARS_ACTIVE, SW_EYE_ACTIVE,
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
from .worlds import DREAM_ORDER, POPULATION, WORLD_ORDER, World

# Interactables draw as the world's own door graphic at a small size, which
# reads as "part of the architecture" rather than as an item lying about.
_ICON_SHEET, _ICON_SLOT = "Blank", 0

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


def _place(world: World, name: str, x: int, y: int, pages) -> None:
    """Add an event at the first tile near ``(x, y)`` that is not taken."""
    world.map.add_event(name, *_free_tile(world, x, y), pages)


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
    _place(world, "bed", 2, 3, [Page(script=sleep, trigger=TRIGGER_ACTION)])

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
    _place(world, "television", 2, 11, [Page(script=tv, trigger=TRIGGER_ACTION)])

    # The mirror: after you have been away long enough, it is late.
    mirror = Script()
    with mirror.if_var(VR_DREAM_DISTANCE, 4, 1):
        mirror.se("Watch", volume=45)
        mirror.msg("you are still there.", "", "you look tired.")
    with mirror.if_var(VR_DREAM_DISTANCE, 3, 2):
        mirror.msg("you are still there.")
    _place(world, "mirror", 18, 13, [Page(script=mirror, trigger=TRIGGER_ACTION)])

    # The wardrobe: a deep layer, and the only thing in the game with a lock.
    wardrobe = Script()
    with wardrobe.if_else_switch(SW_KEY_ACTIVE) as arm:
        with arm(False):
            wardrobe.se("DoorOpen", volume=60)
            wardrobe.msg("it opens.")
            wardrobe.fade_out(30)      # zoom in
            wardrobe.teleport(worlds["room"].map_id, 10, 11)
            wardrobe.switch(SW_WORLD_MEMORY_BASE, True)
            wardrobe.fade_in(30)
        with arm(True):
            wardrobe.msg("it does not open.",
                         "it has never opened.")
    _place(world, "wardrobe", 18, 4, [Page(script=wardrobe, trigger=TRIGGER_ACTION)])

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
    _place(world, "window", 5, 2, [Page(script=window, trigger=TRIGGER_ACTION)])

    desk = Script()
    desk.msg("there is nothing written on it.")
    _place(world, "desk", 18, 8, [Page(script=desk, trigger=TRIGGER_ACTION)])

    # The room's door.  Every world has exactly one, and this is the only one
    # in the game that does not lead anywhere — the way out of here is the bed.
    # Nobody ever says so.
    door = Script()
    door.se("Wrong", volume=40)
    door.msg("it does not open.")
    _place(world, "door", 9, 2, [Page(script=door, trigger=TRIGGER_ACTION)])


# --- the nexus ---------------------------------------------------------------

def nexus_events(world: World, worlds: dict[str, World]) -> None:
    m = world.map
    m.add_event("arrive", 1, 1, [_arrival_event(world)])

    for index, (x, y) in enumerate(world.landmarks["doors"]):
        key = DREAM_ORDER[index]
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
    nx, ny = nexus.landmarks["doors"][DREAM_ORDER.index(key)]
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
            _place(world, f"{name} {resident}", nx, ny, _npc_pages(
                name, NPC_LINES[name],
                move=MOVE_STATIONARY if still else MOVE_RANDOM,
                speed=2 + (resident % 3 == 0),
                quiet_line=NPC_QUIET.get(name)))

    # -- this world's own verb, everywhere in it.
    system = interact.of(key)
    if system is not None:
        zones = list(getattr(world.plan, "zones", []) or [])
        base = SW_INTERACT_BASE + _interact_next[0]
        for n in range(system.count):
            # spread across *all* the zones, not the occupied third: the
            # mechanic has to be in the empty rooms too or the empty rooms
            # have nothing in them to find.
            if zones:
                ix, iy = _near(world, zones[n % len(zones)], rng)
            else:
                ix, iy = world.spot(rng, pad=2)
            switch = base + n
            untouched = Script()
            untouched.se(system.sound, volume=40)
            untouched.msg(*system.before)
            untouched.se(system.done, volume=55)
            untouched.switch(switch, True)
            used = Script()
            used.se(system.sound, volume=28)
            used.msg(*system.after)
            _place(world, f"{system.thing} {n}", ix, iy, [
                Page(script=untouched, trigger=TRIGGER_ACTION,
                     charset=_ICON_SHEET, charset_index=_ICON_SLOT),
                Page(script=used, trigger=TRIGGER_ACTION, switch_a=switch,
                     charset=_ICON_SHEET, charset_index=_ICON_SLOT,
                     translucent=True),
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
