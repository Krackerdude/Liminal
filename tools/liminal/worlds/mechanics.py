"""One local rule per world, and none of them are ever explained.

A dream that behaves exactly like the dream next door is a skin, not a place.
So each world is allowed to break one rule the others keep — and is never
allowed to mention it.  There is no tutorial, no hint, and no NPC who says
"careful, the stairs only go up".  You find out because it happens to you.

The rules are deliberately small.  A mechanic you have to *fight* is a puzzle,
and this game has no puzzles; a mechanic you only notice on the third visit is
exactly right.  Everything here reads the state the engine is already keeping
— where you are, how long since you moved, how far you have walked — and does
one thing with it.
"""

from __future__ import annotations

from ..cmds import MSG_MIDDLE, MV_UP, PLAYER, Script
from ..state import (SW_LANTERN_ACTIVE, VR_KEY, VR_LAST_X, VR_LAST_Y, VR_LOOPS,
                     VR_SCRATCH, VR_STEPS, VR_STILL, VR_TEMP_X, VR_TEMP_Y,
                     VR_WORLD)

# How many frames of not moving counts as standing still.  The atmosphere
# watcher runs every other frame, so this is about four seconds.
STILL = 120


def _stairs(s: Script) -> None:
    """The stairwell only permits ascent.

    Any step that lowers you is undone before you have finished taking it.
    Nobody says so, and the map has no walls to explain it.
    """
    s.var_from_var(VR_SCRATCH, VR_TEMP_Y)
    s.var_from_var(VR_SCRATCH, VR_LAST_Y, op=2)
    # a positive change in y is downward, and downward is not available
    with s.if_var(VR_SCRATCH, 1, 1):
        s.se("Wrong", volume=22)
        s.move_route(PLAYER, [MV_UP, MV_UP], frequency=8, skippable=True)


def _numbers(s: Script) -> None:
    """The counting world counts your steps back at you, once, quietly."""
    with s.if_var(VR_STEPS, 300, 1):
        with s.if_var(VR_KEY, 0):
            s.var(VR_KEY, 1)
            s.se("ChimeFar", volume=32)
            s.msg_options(MSG_MIDDLE)
            s.msg("\\v[10]")      # the step counter, said back at you
            s.msg_options(0)


def _sand(s: Script) -> None:
    """Standing still in the sand lifts what is in the air.

    The world hides its own structures behind fog while you are moving, and
    shows them to anybody prepared to stop, which almost nobody is.
    """
    with s.if_var(VR_STILL, STILL, 1):
        s.weather(0, 0)
        s.tint(112, 110, 102, 92, 20, False)
    with s.if_var(VR_STILL, STILL - 1, 2):
        s.weather(3, 1)


def _stars(s: Script) -> None:
    """The shallows only bear your weight while something is lit.

    With the lantern on you can stand anywhere.  Without it, standing still
    long enough means the surface stops holding you, and it puts you back
    where you came in.
    """
    with s.if_switch(SW_LANTERN_ACTIVE, False):
        with s.if_var(VR_STILL, STILL, 1):
            s.se("WaterDrop", volume=45)
            s.shake(2, 5, 4, wait=True)
            s.var(VR_STILL, 0)


def _pink(s: Script) -> None:
    """The brick warren gets a little wronger the further you walk it."""
    with s.if_var(VR_LOOPS, 2, 1):
        s.tint(112, 92, 100, 108 + 4, 30, False)
    with s.if_var(VR_LOOPS, 5, 1):
        s.se("Rustle", volume=18)


def _toys(s: Script) -> None:
    """The toy city keeps noticing you, and it gets worse the longer you stay."""
    with s.if_var(VR_STEPS, 400, 1):
        s.shake(2, 4, 2, wait=False)


def _checker(s: Script) -> None:
    """Squares: standing still puts you on an identical square somewhere else.

    The world is uniform enough that nothing about the new square proves you
    moved, which is the entire point.
    """
    with s.if_var(VR_STILL, STILL, 1):
        s.se("Vanish", volume=40)
        s.fade_out(15)
        s.var_random(VR_TEMP_X, 8, 128)
        s.var_random(VR_TEMP_Y, 8, 116)
        s.teleport_var(10, VR_TEMP_X, VR_TEMP_Y)
        s.fade_in(15)
        s.var(VR_STILL, 0)


# Which world does what.  Worlds not listed keep every rule, which is also a
# statement — the nexus and the room are the only places that behave.
RULES = {
    "pink": _pink,
    "numbers": _numbers,
    "stairs": _stairs,
    "sand": _sand,
    "checker": _checker,
    "toys": _toys,
    "stars": _stars,
}
