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
from ..state import (SW_DEEP_UNLOCKED, SW_EARS_ACTIVE, SW_EYE_ACTIVE,
                     SW_FOLLOWER, SW_HAS_EFFECT, SW_KEY_ACTIVE,
                     SW_LANTERN_ACTIVE, SW_MENU_OPEN, SW_POLE_ACTIVE,
                     SW_QUIET_ACTIVE, SW_STATIC_ACTIVE, SW_STONE_ACTIVE,
                     SW_TALL_ACTIVE, SW_WOKE_ONCE, SW_WORLD_MEMORY_BASE,
                     SW_WORLD_SECRET_BASE, VR_DREAM_DISTANCE, VR_EQUIPPED,
                     VR_LOOPS, VR_ROLL, VR_SCRATCH, VR_VISITS_BASE, VR_WORLD)
from . import systems as sys
from .cast_lookup import charset_slot
from .worlds import DREAM_ORDER, WORLD_ORDER, World

EFFECT_INDEX = {key: index for index, (key, _, _) in enumerate(EFFECTS, start=1)}

# Which effect is hidden in which dream.  Twelve dreams, twelve effects.
EFFECT_HOME = dict(zip(DREAM_ORDER, [key for key, _, _ in EFFECTS]))


def _arrival_event(world: World) -> Page:
    """Auto-start on entry: set the world number, grade, then erase itself."""
    index = WORLD_ORDER.index(world.key) + 1
    s = Script()
    s.var(VR_WORLD, index)
    s.call_event(sys.CE_ARRIVE)
    s.erase_event()
    return Page(script=s, trigger=TRIGGER_AUTO)


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
          transition: int = 2) -> Page:
    s = Script()
    s.se(sound, volume=70)
    s.bgm_fadeout(8)
    s.fade_out(transition)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.teleport(target_map, x, y)
    s.fade_in(transition)
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
            sleep.fade_out(9)          # mosaic: the room comes apart
            sleep.wait(8)
            sleep.switch(SW_WOKE_ONCE, True)
            sleep.teleport(worlds["nexus"].map_id, *worlds["nexus"].spawn)
            sleep.tint(100, 100, 100, 100, 0, False)
            sleep.fade_in(11)          # wave: the doors assemble
        with branch(1):
            sleep.msg_options(MSG_BOTTOM)
    m.add_event("bed", 4, 5, [Page(script=sleep, trigger=TRIGGER_ACTION)])

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
    m.add_event("television", 9, 5, [Page(script=tv, trigger=TRIGGER_ACTION)])

    # The mirror: after you have been away long enough, it is late.
    mirror = Script()
    with mirror.if_var(VR_DREAM_DISTANCE, 4, 1):
        mirror.se("Watch", volume=45)
        mirror.msg("you are still there.", "", "you look tired.")
    with mirror.if_var(VR_DREAM_DISTANCE, 3, 2):
        mirror.msg("you are still there.")
    m.add_event("mirror", 12, 5, [Page(script=mirror, trigger=TRIGGER_ACTION)])

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
    m.add_event("wardrobe", 18, 5, [Page(script=wardrobe, trigger=TRIGGER_ACTION)])

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
    m.add_event("window", 7, 2, [Page(script=window, trigger=TRIGGER_ACTION)])

    desk = Script()
    desk.msg("there is nothing written on it.")
    m.add_event("desk", 14, 6, [Page(script=desk, trigger=TRIGGER_ACTION)])


# --- the nexus ---------------------------------------------------------------

def nexus_events(world: World, worlds: dict[str, World]) -> None:
    m = world.map
    m.add_event("arrive", 1, 1, [_arrival_event(world)])

    for index, (x, y) in enumerate(world.landmarks["doors"]):
        key = DREAM_ORDER[index]
        target = worlds[key]
        m.add_event(f"door_{key}", x + 1, y + 3,
                    [_door(target.map_id, *target.spawn)])

    # The mirror here shows the room, which is not behind you.
    mirror = Script()
    mirror.se("Watch", volume=40)
    mirror.msg("the room is in it.", "", "you are not.")
    mx, my = world.landmarks["mirror"][0]
    m.add_event("mirror", mx + 1, my + 3, [Page(script=mirror,
                                                trigger=TRIGGER_ACTION)])

    # The keeper sits by the doors and has never looked up.
    kx, ky = world.landmarks["bench"][0]
    m.add_event("keeper", kx + 1, ky + 2, _npc_pages(
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
    m.add_event("sleeper", sx, sy, [
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
    m.add_event("thirteenth", m.width // 2, 3, [
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

    # -- the way back.  Every dream has one, and it is never signposted.
    back = Script()
    back.se("DoorShut", volume=60)
    back.bgm_fadeout(10)
    back.fade_out(6)
    back.call_event(sys.CE_OVERLAY_OFF)
    back.teleport(worlds["nexus"].map_id, *worlds["nexus"].spawn)
    back.fade_in(6)
    bx, by = world.spot(rng, pad=3)
    m.add_event("way back", bx, by, [Page(script=back, trigger=TRIGGER_ACTION)])

    # -- the effect that lives here
    effect_key = EFFECT_HOME[key]
    ex, ey = world.spot(rng, pad=4)
    got = Script()
    got.var(VR_SCRATCH, EFFECT_INDEX[effect_key])
    got.call_event(sys.CE_GIVE_EFFECT)
    got.switch(SW_WORLD_SECRET_BASE + index, True)
    m.add_event(f"effect {effect_key}", ex, ey, [
        Page(script=got, trigger=TRIGGER_ACTION, charset="KinD",
             charset_index=3, animation_type=ANIM_CONTINUOUS,
             move_type=MOVE_STATIONARY),
        # once taken, the spot is empty and stays empty
        Page(script=Script(), trigger=TRIGGER_ACTION,
             switch_a=SW_HAS_EFFECT[effect_key]),
    ])

    # -- residents
    for name in world.npcs:
        nx, ny = world.spot(rng, pad=2)
        m.add_event(name, nx, ny, _npc_pages(name, *[NPC_LINES[name]],
                                             quiet_line=NPC_QUIET.get(name)))

    # -- hidden layer: things that need a condition
    for maker in HIDDEN.get(key, []):
        maker(world, worlds, rng)

    # -- world memory: the loop changes what is here
    corrupt = Script()
    corrupt.se("Wrong", volume=40)
    corrupt.msg("this was not here before.")
    corrupt.switch(SW_WORLD_MEMORY_BASE + index, True)
    cx, cy = world.spot(rng, pad=3)
    m.add_event("after the fifth", cx, cy, [
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
