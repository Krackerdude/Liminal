"""Events for the world behind the television.

Only the plumbing so far: a way in, a way out of every region, and the routes
between the four.  What actually lives here comes next.
"""

from __future__ import annotations

from ..cmds import Script
from ..maps import (ANIM_CONTINUOUS, LAYER_SAME, MOVE_RANDOM,
                    MOVE_STATIONARY, TRIGGER_ACTION, Page)
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


# What each animal says, per region.  Nothing here explains anything: the
# animals do not know what has happened to their island, which is worse than
# them knowing, and in the red region they have stopped speaking in sentences.
LINES: dict[str, list[str]] = {
    "bluebird": ["it hops twice and looks at you.", "",
                 "it is not going to move off the path."],
    "finch": ["it will not face you.", "",
              "whichever way you go round, it turns first."],
    "hoglet": ["it is asleep, or doing an excellent impression."],
    "shellback": ["the shell is far too big for it.", "",
                  "there is something written on the inside."],
    "watcher_bird": ["it does not hop.", "", "nothing on this island"
                     " has looked at you for this long."],
    "smiler": ["it hops twice and looks at you.", "",
               "it is doing the other thing with its face."],
    "hollow": ["there is a bird-shaped hole here.", "",
               "the grass under it has not been stood on."],
    "him": ["", ""],
}


def _resident(name: str, count: int) -> list:
    """One animal, said once and then remembered.

    Every one of them moves at random except the two that do not, and which
    two those are is the only thing on the island that is ever a warning.
    """
    from .cast_lookup import charset_slot
    still = name in ("watcher_bird", "hollow", "him")
    sheet, slot = charset_slot(name)
    s = Script()
    if name == "him":
        s.se("Laugh", volume=52)
        s.wait(6)
        s.se("ExeAppear", volume=76)
        s.flash(255, 255, 255, 26, 2, True)
        s.erase_event()
    else:
        s.se("Rustle", volume=30)
        s.msg(*LINES[name])
    return [Page(script=s, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
                 charset=sheet, charset_index=slot,
                 move_type=MOVE_STATIONARY if still else MOVE_RANDOM,
                 move_frequency=2 if still else 4,
                 animation_type=ANIM_CONTINUOUS if not still else 1)]


def _populate(world, rng) -> None:
    """Scatter the region's animals along its paths and clearings.

    They live *on the routes*, not in the deep forest: an animal nobody walks
    past is an animal nobody meets, and the island is big.
    """
    from ..art.cast import WORLD_CAST
    from .events import _free_tile

    roster = WORLD_CAST.get(world.key, [])
    if not roster:
        return
    m = world.map
    spine = world.landmarks.get("spine") or []
    clearings = world.landmarks.get("plots") or []
    spots = [spine[int(len(spine) * f)] for f in
             (0.12, 0.26, 0.38, 0.52, 0.64, 0.78, 0.9)] + list(clearings)
    for index, (px, py) in enumerate(spots):
        name = roster[index % len(roster)]
        # Beside the route rather than on it, so nothing blocks the walk.
        for dx, dy in ((3, 2), (-3, 2), (2, -3), (-2, -3), (5, 0), (0, 5)):
            x, y = (px + dx) % m.width, (py + dy) % m.height
            if world.plan.is_floor(x, y) and (x, y) not in world.plan.protected:
                world.map.add_event(f"{name} {index}", x, y,
                                    _resident(name, index))
                break


def hills_events(world, worlds: dict, rng) -> None:
    """One region's plumbing: the way out, the way onward, and who is here."""
    from .events import _place_object

    _populate(world, rng)

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
