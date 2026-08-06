"""Switch and variable allocation.

RPG Maker addresses state by bare number, which turns into an unreadable mess
very fast.  Everything the game remembers is named here once and referred to
by name everywhere else.
"""

from __future__ import annotations

from .art.menu import EFFECTS

# --- switches ----------------------------------------------------------------
# 1..12   one per effect: you have found it
# 20..39  systems
# 40..79  per-world secrets and permanent world memory

SW_HAS_EFFECT = {key: index for index, (key, _, _) in enumerate(EFFECTS, start=1)}

SW_MENU_OPEN = 20
SW_MENU_BUSY = 21
SW_EYE_ACTIVE = 22          # the eye is equipped: hidden things become visible
SW_QUIET_ACTIVE = 23        # nothing notices you
SW_LANTERN_ACTIVE = 24      # dark worlds lift
SW_STATIC_ACTIVE = 25
SW_TALL_ACTIVE = 26
SW_STONE_ACTIVE = 27
SW_POLE_ACTIVE = 28
SW_BELL_ACTIVE = 29
SW_KEY_ACTIVE = 30
SW_EARS_ACTIVE = 31
SW_COAT_ACTIVE = 32
SW_HAT_ACTIVE = 33

SW_EFFECT_ACTIVE = {
    "lantern": SW_LANTERN_ACTIVE, "quiet": SW_QUIET_ACTIVE, "tall": SW_TALL_ACTIVE,
    "hat": SW_HAT_ACTIVE, "ears": SW_EARS_ACTIVE, "coat": SW_COAT_ACTIVE,
    "pole": SW_POLE_ACTIVE, "eye": SW_EYE_ACTIVE, "bell": SW_BELL_ACTIVE,
    "key": SW_KEY_ACTIVE, "stone": SW_STONE_ACTIVE, "static": SW_STATIC_ACTIVE,
}

SW_WOKE_ONCE = 34           # you have slept in the bed at least once
SW_SEEN_NEXUS = 35
SW_OVERLAY_ON = 36
SW_FOLLOWER = 37            # something is following you between worlds
SW_TITLE_CHANGED = 38       # the title screen is quietly different now
SW_DEEP_UNLOCKED = 39

# Per-world memory: things that stay changed once changed.
SW_WORLD_MEMORY_BASE = 40   # 40 + world index
SW_WORLD_SECRET_BASE = 60   # 60 + world index

# Every interactive object in the game owns one switch, so its state persists
# for the whole playthrough: a brick pulled out of a wall stays out, a wound
# toy stays wound, a raised tide stays raised.  Two hundred is generous now
# and was not: the redesign that made these load-bearing pushed the count
# past two hundred on its first build.
# A world that has been permanently changed by its own mechanic.  Separate
# from "world memory", which records that something happened; this records
# that the place is *different now* and stays different.
SW_WORLD_STATE_BASE = 80    # 80 + world index

SW_INTERACT_BASE = 100
SW_INTERACT_COUNT = 320

# --- variables ---------------------------------------------------------------
VR_EQUIPPED = 1             # 0 none, else the effect's number
VR_DREAM_DISTANCE = 2       # total tiles walked across every loop, ever
VR_LOOPS = 3                # times the current world has been circled
VR_LAST_X = 4
VR_LAST_Y = 5
VR_WORLD = 6                # which world you are in
VR_SCRATCH = 7
VR_MENU_CURSOR = 8
VR_ROLL = 9                 # a dice roll, for rare events
VR_STEPS = 10
VR_EFFECTS_FOUND = 11
VR_MENU_SLOT = 12
VR_PREV_WORLD = 13
VR_TEMP_X = 14
VR_TEMP_Y = 15
# The diary watcher needs a variable nothing else touches.  It shares the frame
# with the loop watch, which rewrites VR_SCRATCH every single frame, and a key
# read that lands in a variable somebody else is using is a keypress that never
# happened.
VR_KEY = 16
# The number the counters in the number world are currently set to.
VR_SET_NUMBER = 17
# Frames since the player last changed tile.  Standing still is the only
# input this game has that is not walking, so several worlds read it.
VR_STILL = 17
VR_VISITS_BASE = 20         # 20 + world index: times you have entered it

# The number world's registers.  Six independent numbers, each set separately
# on its own plinths, each editing a different property of the map.  The state
# of that world is the whole tuple, not any one of them.
# The stairwell remembers the order you fell through it.  Not how many falls
# — the *sequence*, folded into one number, so the same four edges taken in a
# different order are a different answer.
VR_FALL = 18
VR_FALLS = 19

# The grove is one town received on four channels, and the receiver is chased
# rather than switched: VR_CHASE counts how many junctions of the drift you
# have followed correctly, and resets to nothing the moment you pick a wrong
# one.  VR_CHANNEL is only what the town currently is; it is never set
# directly by anything the player can reach.
VR_CHASE = 50
VR_CHANNEL = 51
VR_CHASE_FROM = 52          # which junction the current step was started at
VR_RING_DIR = 53            # which way the ring came from: 0 up 1 right 2 down 3 left
VR_RING_X = 54              # where you were standing when it started
VR_RING_Y = 55
VR_RING_WAIT = 56           # seconds left before the next ring

# Where you were standing in the scrawl world when you stepped into a
# painting, so that coming back out puts you on the mural rather than at an
# arrival tile.  Consecutive, because the engine reads a teleport destination
# from three variables in a row.
VR_MURAL_MAP = 57
VR_MURAL_X = 58
VR_MURAL_Y = 59
# How far round the star's tips you have got, and in which order.
VR_AMBIENCE = 62          # counts down to the grove's next ambient sound

VR_STAR_ORDER = 60
VR_STAR_STEP = 61

# The four things the grove has that can be carried, one found on each
# channel and every one of them used on a different channel from the one that
# had it.  They are switches rather than inventory because none of them are
# items in the menu sense — the game has no menu they would appear in.
SW_FACE_BASE = SW_INTERACT_BASE + SW_INTERACT_COUNT      # past the pool
SW_FACE_COIN = SW_FACE_BASE + 0
SW_FACE_TAPE = SW_FACE_BASE + 1
SW_FACE_SEED = SW_FACE_BASE + 2
SW_FACE_BULB = SW_FACE_BASE + 3
SW_FACE_MAST = SW_FACE_BASE + 4         # the compound gate is open
SW_FACE_ENDED = SW_FACE_BASE + 5        # you have stood under the mast
SW_FACE_HEARD = SW_FACE_BASE + 6        # the receiver is in your hands

# The four paintings on the floor of the scrawl world, and the four things
# each of them keeps.  Unlike the grove's loop these are not a chain — a
# painting is a closed object and you can visit them in any order — but all
# four together are the only thing the plaza will answer to.
SW_MURAL_BASE = SW_FACE_BASE + 8
SW_MURAL_LENS = SW_MURAL_BASE + 0       # the eye
SW_MURAL_THREAD = SW_MURAL_BASE + 1     # the spiral
SW_MURAL_TOOTH = SW_MURAL_BASE + 2      # the mouth
SW_MURAL_POINT = SW_MURAL_BASE + 3      # the star
SW_MURAL_PLAZA = SW_MURAL_BASE + 4      # the plaza has been given all four
SW_MURAL_ITEM = {"neon2": SW_MURAL_LENS, "neon3": SW_MURAL_THREAD,
                 "neon4": SW_MURAL_TOOTH, "neon5": SW_MURAL_POINT}
# One per painting, for the secret in it that has been found.
SW_MURAL_SECRET = SW_MURAL_BASE + 8     # + painting index
SW_FACE_ITEM = {"coin": SW_FACE_COIN, "tape": SW_FACE_TAPE,
                "seed": SW_FACE_SEED, "bulb": SW_FACE_BULB}

VR_REG_BASE = 40
REG_US, REG_FAR, REG_LIGHT, REG_WAYS, REG_AGO, REG_YOU = range(6)
REG_NAMES = ("how many of us", "how far", "how bright",
             "how many ways", "how long ago", "how many of you")
REG_MAX = (20, 9, 9, 9, 9, 4)

# --- names, for the database editor lists ------------------------------------

def _dense(names: dict[int, str]) -> dict[int, str]:
    """Fill every gap between 1 and the highest id in use.

    The allocation above is deliberately spaced out — leaving room beside each
    group is what stops a new switch from being wedged into somebody else's
    range — but the database is a list, not a map, and a list with holes in it
    is a list whose length is not its highest index.  Anything allocated past
    that length is then addressing storage the engine has no reason to have
    made.  Nothing is saved by shipping the holes, so they are filled.
    """
    if not names:
        return names
    return {index: names.get(index, "-") for index in range(1, max(names) + 1)}



def switch_names(world_names: list[str]) -> dict[int, str]:
    names: dict[int, str] = {}
    for key, index in SW_HAS_EFFECT.items():
        names[index] = f"has {key}"
    names.update({
        SW_MENU_OPEN: "menu open", SW_MENU_BUSY: "menu busy",
        SW_WOKE_ONCE: "woke once", SW_SEEN_NEXUS: "seen nexus",
        SW_OVERLAY_ON: "overlay on", SW_FOLLOWER: "followed",
        SW_TITLE_CHANGED: "title changed", SW_DEEP_UNLOCKED: "deep unlocked",
    })
    for key, index in SW_EFFECT_ACTIVE.items():
        names[index] = f"{key} active"
    for index in range(SW_INTERACT_COUNT):
        names[SW_INTERACT_BASE + index] = f"used {index:03d}"
    for index, world in enumerate(world_names):
        names[SW_WORLD_STATE_BASE + index] = f"{world} altered"
    for index, world in enumerate(world_names):
        names[SW_WORLD_MEMORY_BASE + index] = f"{world} changed"
        names[SW_WORLD_SECRET_BASE + index] = f"{world} secret"
    names.update({SW_FACE_COIN: "the coin", SW_FACE_TAPE: "the tape",
                  SW_FACE_SEED: "the seed", SW_FACE_BULB: "the bulb",
                  SW_FACE_MAST: "the compound", SW_FACE_ENDED: "under the mast",
                  SW_FACE_HEARD: "the receiver",
                  SW_MURAL_LENS: "the lens", SW_MURAL_THREAD: "the thread",
                  SW_MURAL_TOOTH: "the loose tooth",
                  SW_MURAL_POINT: "the long point",
                  SW_MURAL_PLAZA: "the plaza answered"})
    for index in range(4):
        names[SW_MURAL_SECRET + index] = f"painting {index} secret"
    return _dense(names)


def variable_names(world_names: list[str]) -> dict[int, str]:
    names = {
        VR_EQUIPPED: "equipped", VR_DREAM_DISTANCE: "dream distance",
        VR_LOOPS: "loops", VR_LAST_X: "last x", VR_LAST_Y: "last y",
        VR_WORLD: "world", VR_SCRATCH: "scratch", VR_MENU_CURSOR: "menu cursor",
        VR_ROLL: "roll", VR_STEPS: "steps", VR_EFFECTS_FOUND: "effects found",
        VR_MENU_SLOT: "menu slot", VR_PREV_WORLD: "previous world",
        VR_TEMP_X: "temp x", VR_TEMP_Y: "temp y", VR_KEY: "key",
        VR_SET_NUMBER: "the number", VR_STILL: "still",
        VR_FALL: "the way down", VR_FALLS: "falls",
    }
    for index, world in enumerate(world_names):
        names[VR_VISITS_BASE + index] = f"visits {world}"
    for index, label in enumerate(REG_NAMES):
        names[VR_REG_BASE + index] = label
    names.update({VR_CHASE: "the chase", VR_CHANNEL: "the channel",
                  VR_CHASE_FROM: "chased from", VR_RING_DIR: "the ring",
                  VR_RING_X: "ring x", VR_RING_Y: "ring y",
                  VR_RING_WAIT: "until the ring",
                  VR_AMBIENCE: "until the next sound",
                  VR_MURAL_MAP: "the way back", VR_MURAL_X: "back x",
                  VR_MURAL_Y: "back y", VR_STAR_ORDER: "the order",
                  VR_STAR_STEP: "how many points"})
    return _dense(names)
