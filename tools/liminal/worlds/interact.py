"""One core interactive system per world, and it is everywhere in that world.

The rule this implements is in ``docs/GOLDEN_RULE.md``: a world gets a single
verb that belongs to it and to nothing else, and that verb works on the world's
own furniture wherever the player finds it.  Not one puzzle room — the whole
place.

The test it has to pass: **if you removed the mechanic and the world still
played identically apart from a few locked doors, it was a puzzle, not a
system.**

Each verb is diegetic.  Nobody hands you a "brick tool"; there are simply loose
bricks in a world made of brick, and pulling one is the obvious thing to try.
Nothing is explained anywhere, and the first thing a player should do on
arriving somewhere new is discover a way of touching it that works nowhere
else.

State is permanent.  Every interactable owns a switch for the whole
playthrough, so a brick pulled out stays out, a wound toy stays wound, and a
tide raised on your first visit is still high on your fourth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class System:
    """A world's verb, and what its furniture does when you use it."""
    verb: str                # what the player is doing, for our own reading
    thing: str               # what they are doing it to
    before: tuple[str, ...]  # what the object says untouched
    after: tuple[str, ...]   # what it says once used
    sound: str = "Rustle"
    done: str = "Appear"     # heard once, when it changes
    # how many of them are scattered through the world
    count: int = 14


SYSTEMS: dict[str, System] = {
    # A world made of brick, so the brick is the mechanic.  Pull one and the
    # wall has a gap in it; the gap stays.
    "pink": System(
        verb="pull a brick", thing="loose brick", count=18,
        before=("one brick is not flush with the others.",),
        after=("the gap is still there.", "", "it is your gap."),
        sound="StepStone", done="LowThud"),

    # Counting: every numeral can be advanced, and the world is watching what
    # they add up to.
    "numbers": System(
        verb="advance it", thing="counter", count=16,
        before=("it is showing a number.", "", "the number can be changed."),
        after=("it is showing a different number now.",),
        sound="Cursor", done="ChimeFar"),

    # A nursery: the blocks are for stacking, and stacked blocks are stairs.
    "blocks": System(
        verb="stack it", thing="loose block", count=16,
        before=("it is the right size to be put on another one.",),
        after=("it is on top of the other one.", "", "you can stand on it."),
        sound="LowThud", done="LowThud"),

    # Stairs that can be turned to face somewhere else, which is the only way
    # a stairwell that only goes up can ever take you anywhere new.
    "stairs": System(
        verb="turn the flight", thing="flight of stairs", count=12,
        before=("it goes up, and it goes that way.",),
        after=("it goes up, and it goes a different way now.",),
        sound="StepStone", done="GlassRing"),

    # Sand covers things.  Digging uncovers them, and they stay uncovered.
    "sand": System(
        verb="dig", thing="shallow place", count=16,
        before=("the sand is thinner here.",),
        after=("there is something under it after all.",),
        sound="StepSoft", done="Rustle"),

    # A grove full of municipal fittings that do not belong in it, all of
    # which still work.
    "faces": System(
        verb="operate it", thing="fitting", count=16,
        before=("it still has power.",),
        after=("it is doing what it was for.", "", "nothing needed it to."),
        sound="Cursor", done="Appear"),

    # A field of stone hands.  You can take one, and a held hand points.
    "hands": System(
        verb="take its hand", thing="open hand", count=14,
        before=("it is open, and at about your height.",),
        after=("it closes around yours.", "", "then it points."),
        sound="StepStone", done="Watch"),

    # Squares flip.  A flipped square is a different square, and the world is
    # made of nothing but squares.
    "checker": System(
        verb="flip it", thing="loose square", count=18,
        before=("this one is not fixed down.",),
        after=("it is the other colour now.",),
        sound="LowThud", done="GlassRing"),

    # Everything in a toy world winds up.  This is the one Yume Nikki would
    # have done, and it is right.
    "toys": System(
        verb="wind it", thing="key", count=20,
        before=("there is a key in its back.",),
        after=("it is going.", "", "it will not stop now."),
        sound="Cursor", done="Appear"),

    # Light you can draw with, on a world made of drawn light.  A drawn line
    # is a line you can stand on.
    "neon": System(
        verb="draw", thing="unlit run", count=18,
        before=("the tube is here but nothing is in it.",),
        after=("it is lit.", "", "it goes somewhere."),
        sound="StaticBurst", done="Appear"),

    # Every umbrella opens or shuts.  Open, it shelters; shut, it is a pole.
    "umbrellas": System(
        verb="open it", thing="closed umbrella", count=16,
        before=("it is furled.", "", "it has never once been needed."),
        after=("it is open.", "", "still nothing falls on it."),
        sound="Rustle", done="Appear"),

    # A shallow ocean whose depth you can change, which changes what is
    # island and what is not.
    "stars": System(
        verb="raise the tide", thing="marker", count=14,
        before=("the water is at a line on it.",),
        after=("the water is at a different line on it.",),
        sound="WaterDrop", done="WaterStep"),
}


def of(key: str) -> System | None:
    return SYSTEMS.get(key)
