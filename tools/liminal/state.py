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
VR_REG_BASE = 40
REG_US, REG_FAR, REG_LIGHT, REG_WAYS, REG_AGO, REG_YOU = range(6)
REG_NAMES = ("how many of us", "how far", "how bright",
             "how many ways", "how long ago", "how many of you")
REG_MAX = (20, 9, 9, 9, 9, 4)

# --- names, for the database editor lists ------------------------------------

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
    return names


def variable_names(world_names: list[str]) -> dict[int, str]:
    names = {
        VR_EQUIPPED: "equipped", VR_DREAM_DISTANCE: "dream distance",
        VR_LOOPS: "loops", VR_LAST_X: "last x", VR_LAST_Y: "last y",
        VR_WORLD: "world", VR_SCRATCH: "scratch", VR_MENU_CURSOR: "menu cursor",
        VR_ROLL: "roll", VR_STEPS: "steps", VR_EFFECTS_FOUND: "effects found",
        VR_MENU_SLOT: "menu slot", VR_PREV_WORLD: "previous world",
        VR_TEMP_X: "temp x", VR_TEMP_Y: "temp y", VR_KEY: "key",
        VR_SET_NUMBER: "the number", VR_STILL: "still",
    }
    for index, world in enumerate(world_names):
        names[VR_VISITS_BASE + index] = f"visits {world}"
    for index, label in enumerate(REG_NAMES):
        names[VR_REG_BASE + index] = label
    return names
