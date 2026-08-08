"""Events for the world behind the television.

Only the plumbing so far: a way in, a way out of every region, and the routes
between the four.  What actually lives here comes next.
"""

from __future__ import annotations

from ..cmds import Script
from ..maps import LAYER_SAME, TRIGGER_ACTION, Page
from . import atmosphere
from . import systems as sys
from .worlds import HILLS_ORDER


def _leave(target) -> Script:
    """Back through the set, into the room you were sitting in."""
    s = Script()
    s.se("Corrupt", volume=54)
    s.msg("the picture is on the wrong side of the glass.")
    s.wait(8)
    s.se("Static2", volume=70)
    s.bgm_fadeout(3)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(19)
    s.teleport(target.map_id, *target.spawn)
    s.call_event(sys.CE_ARRIVE)
    s.fade_in(atmosphere.of("room").enter)
    return s


def _cross(target, key: str) -> Script:
    """From one region of the hills into the next.  No fade to black.

    The regions are the same ground, so the crossing is a *cut* rather than a
    journey: the picture changes and the player does not move, which is the
    broadcast world's trick and the only honest way to say these are four
    versions of one place.
    """
    s = Script()
    s.se("Corrupt", volume=60)
    s.flash(240, 236, 226, 20, 2, False)
    s.bgm_fadeout(3)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(19)
    s.teleport(target.map_id, *target.spawn)
    s.call_event(sys.CE_ARRIVE)
    s.fade_in(19)
    return s


def hills_events(world, worlds: dict, rng) -> None:
    """One region's plumbing: the way out, and the way onward."""
    from .events import _place_object

    index = HILLS_ORDER.index(world.key)

    # The way out is a door standing in the open, which the door pass has
    # already placed and told the layout about.
    if "door" in world.chipset.objects and "door" in world.landmarks:
        _place_object(world, "door", [
            Page(script=_leave(worlds["room"]), trigger=TRIGGER_ACTION,
                 layer=LAYER_SAME)],
            at=world.landmarks["door"][0], name="the way back")

    # And the way onward is the gate, which does nothing in the region it
    # stands in and everything in the next one.
    onward = HILLS_ORDER[(index + 1) % len(HILLS_ORDER)]
    if "gate" in world.chipset.objects:
        spots = world.landmarks.get("meadows") or []
        if spots:
            far = spots[len(spots) // 2]
            _place_object(world, "gate", [
                Page(script=_cross(worlds[onward], onward),
                     trigger=TRIGGER_ACTION, layer=LAYER_SAME)],
                at=((far[0] + 8) % world.map.width,
                    (far[1] - 6) % world.map.height), name="the gate")
