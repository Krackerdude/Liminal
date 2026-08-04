"""One core interactive system per world, and it is how you explore that world.

The rule is in ``docs/GOLDEN_RULE.md``.  A world gets a single verb that
belongs to it and to nothing else, that verb works on the world's own furniture
wherever it is found, and — the part that matters — **the verb is the intended
route through the world.**

An earlier version of this file had twelve verbs that all did the same thing:
print a different line the second time you touched something.  That is "press
button, world does thing", and it is not a system.  What makes a mechanic worth
having is that the world is *shaped around it*: places you cannot reach without
it, residents who are not there until you use it, and the world's own effect
sitting behind it.

So every system below declares what it opens:

``reveals``   a resident who is not on the map until this is used
``opens``     a way into somewhere the layout otherwise seals off
``holds``     the world's effect, behind the mechanic rather than beside it

and the ratio matters.  Most uses do nothing but answer you — a world where
every brick hides a room is a world with no bricks in it, only doors.  Roughly
one in five carries something.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class System:
    """A world's verb, what it is done to, and what it is *for*."""
    verb: str
    thing: str
    before: tuple[str, ...]
    after: tuple[str, ...]
    # what a live one does, told in the world's own terms
    payoff: tuple[str, ...]
    sound: str = "Rustle"
    done: str = "Appear"
    count: int = 16
    live: int = 5              # every Nth one carries something


SYSTEMS: dict[str, System] = {
    # ---- kept, because pulling a wall apart is already exploration --------
    "pink": System(
        verb="pull a brick", thing="loose brick", count=20, live=4,
        before=("one brick is not flush with the others.",),
        after=("the gap is still there.", "", "it is your gap."),
        payoff=("the wall gives more than a brick.", "",
                "there is a room behind it that has no door."),
        sound="StepStone", done="LowThud"),

    # ---- kept ------------------------------------------------------------
    "blocks": System(
        verb="stack it", thing="loose block", count=18, live=4,
        before=("it is the right size to be put on another one.",),
        after=("it is on top of the other one.", "", "you can stand on it."),
        payoff=("it is high enough now.", "",
                "you can see over the wall, and then you are over it."),
        sound="LowThud", done="LowThud"),

    # ---- kept ------------------------------------------------------------
    "sand": System(
        verb="dig", thing="shallow place", count=18, live=4,
        before=("the sand is thinner here.",),
        after=("there is something under it after all.",),
        payoff=("it is a door, lying flat.", "", "it opens downward."),
        sound="StepSoft", done="Rustle"),

    # ---- kept ------------------------------------------------------------
    "stars": System(
        verb="move the tide", thing="marker", count=16, live=4,
        before=("the water is at a line on it.",),
        after=("the water is at a different line on it.",),
        payoff=("the water goes out a long way.", "",
                "what it leaves behind was always there."),
        sound="WaterDrop", done="WaterStep"),

    # ---- redrawn: the verb erases the world ------------------------------
    # A world built out of numerals, and you can count them down. A numeral
    # at zero is gone, and things stand behind numerals.
    "numbers": System(
        verb="count it down", thing="numeral", count=20, live=4,
        before=("it is showing a number.", "", "the number can go down."),
        after=("it is showing one less than it was.",),
        payoff=("it reaches zero and stops being there.", "",
                "somebody was standing behind it."),
        sound="Cursor", done="ChimeFar"),

    # ---- redrawn: falling is the only way down ---------------------------
    # The stairwell only permits ascent, so the verb is the exception to its
    # own rule: you can step off a landing on purpose. It is the only route
    # to anything below you, and there is a great deal below you.
    "stairs": System(
        verb="step off", thing="edge", count=14, live=3,
        before=("there is nothing under this side.",),
        after=("you have already looked over it once.",),
        payoff=("you go down for much longer than you went up.",),
        sound="StepStone", done="GlassRing"),

    # ---- redrawn: sound is the map ---------------------------------------
    # The grove is full of municipal fittings that should not be there and
    # still work. Lift a receiver and something rings, somewhere else, for a
    # while. Getting to it before it stops is the whole world.
    "faces": System(
        verb="lift the receiver", thing="telephone", count=16, live=4,
        before=("there is a dial tone.", "", "it should not have one."),
        after=("the tone is the same as it was.",),
        payoff=("something starts ringing.", "",
                "it is a long way off, and it will not ring forever."),
        sound="Cursor", done="ChimeFar"),

    # ---- redrawn: you are led, not told ----------------------------------
    # Take a stone hand and it closes and points. Follow the point and there
    # is another hand, pointing further. The chain goes somewhere.
    "hands": System(
        verb="take its hand", thing="open hand", count=16, live=4,
        before=("it is open, and at about your height.",),
        after=("it is still pointing the way it pointed.",),
        payoff=("it closes around yours, and then it points.", "",
                "there is another one where it is pointing."),
        sound="StepStone", done="Watch"),

    # ---- redrawn: flipping moves you -------------------------------------
    # Every square has an opposite somewhere in the world. Flipping one
    # swaps it with its opposite, and you are standing on it when it goes.
    "checker": System(
        verb="flip it", thing="loose square", count=20, live=4,
        before=("this one is not fixed down.",),
        after=("it is the other colour now.",),
        payoff=("it turns over, and so does everything on it.", "",
                "this is a different part of the board."),
        sound="LowThud", done="GlassRing"),

    # ---- redrawn: wound things go somewhere ------------------------------
    # A wound toy walks off in a straight line and does not stop. Some of
    # them walk into places you cannot, and what they do when they get there
    # is the reason to wind them.
    "toys": System(
        verb="wind it", thing="key", count=22, live=4,
        before=("there is a key in its back.",),
        after=("it is going, and it is not coming back.",),
        payoff=("it walks off, and it walks through the wall.", "",
                "something on the other side falls over."),
        sound="Cursor", done="Appear"),

    # ---- redrawn: you draw the floor -------------------------------------
    # The chambers are separated by void. Empty tubes run across the void,
    # and light put into a tube is something you can stand on.
    "neon": System(
        verb="fill the tube", thing="unlit run", count=20, live=4,
        before=("the tube is here but nothing is in it.",),
        after=("it is lit, and it holds.",),
        payoff=("the light runs all the way out over the dark.", "",
                "it reaches the other side."),
        sound="StaticBurst", done="Appear"),

    # ---- redrawn: umbrellas carry you ------------------------------------
    # In a world where nothing has ever fallen, an opened umbrella has
    # nothing to do but lift. Opening one under yourself is transport.
    "umbrellas": System(
        verb="open it over you", thing="furled umbrella", count=18, live=4,
        before=("it is furled.", "", "it has never once been needed."),
        after=("it is open.", "", "still nothing falls on it."),
        payoff=("it opens, and it pulls.", "",
                "you come down a long way from where you went up."),
        sound="Rustle", done="Appear"),
}


def of(key: str) -> System | None:
    return SYSTEMS.get(key)
