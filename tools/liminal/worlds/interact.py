"""One core interactive system per world, and it is how you explore that world.

Two rules govern this file, both in ``docs/GOLDEN_RULE.md``: the interaction
rule (a world gets one verb, it works everywhere in that world, and it is the
intended route through it) and the sequencing rule (the verb has to be worth
something — order, hidden instruction, permanent consequence, and a reward for
the player who pays attention that the casual player never sees).

Reference points, per the sequencing rule: *Please, Don't Touch Anything*,
*Blue Prince*, *House.wad*, and the deep Zombies easter eggs. What those share
is not difficulty. It is that the world holds information the player has to
assemble themselves, across the whole space, with nothing acknowledging it.

Nothing here is explained in game. Ever.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class System:
    """A world's verb, what it is done to, and what it is *for*."""
    verb: str
    thing: str
    before: tuple[str, ...]
    after: tuple[str, ...]
    payoff: tuple[str, ...]
    # The design this is an implementation of.  Written out because half of
    # these are larger than what is currently wired up, and the gap between
    # the two should be legible rather than lost.
    design: str = ""
    sound: str = "Rustle"
    done: str = "Appear"
    count: int = 16
    live: int = 5
    # The chipset object this verb is *done to*.  Without one the world spawns
    # sixteen events that describe an object which was never drawn — the grove
    # had sixteen telephones in it and not one telephone.
    art: str = ""
    # extra maps this world needs beyond its own: floors, states, planes
    layers: int = 0


SYSTEMS: dict[str, System] = {

    # ------------------------------------------------------------------ pink
    "pink": System(
        verb="pull a brick", thing="loose brick", count=20, live=4,
        before=("one brick is not flush with the others.",),
        after=("the gap is still there.", "", "it is your gap."),
        payoff=("the wall gives more than a brick.", "",
                "there is a room behind it that has no door."),
        sound="StepStone", done="LowThud",
        design="""
        Kept. Pulling a wall apart in a world made of wall is already
        exploration: the gap stays, it is yours, and the rooms behind the
        walls have no other way in.
        """),

    # --------------------------------------------------------------- numbers
    "numbers": System(
        verb="set the number", thing="numeral", count=20, live=4,
        before=("it is showing a number.", "", "the number can be changed."),
        after=("it is showing what you left it on.",),
        payoff=("the number matches how many of them are here.",),
        sound="Cursor", done="ChimeFar",
        design="""
        Numbers are a lock whose key is a body count.

        Every numeral in the world can be set. Passages are numbered, and a
        passage opens when the number you have set matches something true
        about the world right now — how many residents are standing in it,
        how many doors you have opened, how many times you have been here.
        Different numbers open different parts of the world, so the world is
        entered differently depending on what you have made true.

        And one of those numbers is zero.

        Setting the counter to zero opens the last passage, and it opens it by
        making the statement true: it kills everything in the world. Every
        resident, at once, permanently, across every visit for the rest of the
        save. There is no warning, no confirmation and no way back.

        What comes with it: the music cuts to something gritty and much worse,
        the overlay changes, the grade drops. The passage that opens leads
        somewhere that could only ever have been reached this way, and the
        world is empty forever afterwards. Nothing acknowledges that you did
        it. The counters still work. They all read zero.
        """),

    # ---------------------------------------------------------------- blocks
    "blocks": System(
        verb="stack it", thing="loose block", count=18, live=4,
        before=("it is the right size to be put on another one.",),
        after=("it is on top of the other one.", "", "you can stand on it."),
        payoff=("it is high enough now.", "",
                "you can see over the wall, and then you are over it."),
        sound="LowThud", done="LowThud",
        design="""
        Kept. Stacking is height, height is over the wall, and what is over
        the wall was never reachable on foot.
        """),

    # ---------------------------------------------------------------- stairs
    "stairs": System(
        verb="step off", thing="edge", count=14, live=3, layers=5,
        before=("there is nothing under this side.",),
        after=("you have already looked over it once.",),
        payoff=("you go down for much longer than you went up.",),
        sound="StepStone", done="GlassRing",
        design="""
        The stairwell is not one map. It is five floors, and which floor you
        land on depends on the order you fell through the others.

        Stepping off an edge drops you to another floor — but *which* edge, on
        *which* floor, in *which* order, decides where you come out. The same
        four falls in a different sequence reach a different place entirely.
        This is the quicksand-pit structure: the entrances all look alike, the
        order is the whole puzzle, and nothing in the world tells you what the
        order is. Some floors can only be reached by a sequence nobody would
        stumble into.

        The floors are not equal. Each one down is more corrupted than the
        last: the palette sours, the overlay thickens, the music degrades, and
        the residents are the same residents — twisting, contorting, wrong in
        the joints, still saying their lines. By the deepest floor the world
        has stopped pretending to be a stairwell.
        """),

    # ------------------------------------------------------------------ sand
    "sand": System(
        verb="dig", thing="shallow place", count=18, live=4,
        before=("the sand is thinner here.",),
        after=("there is something under it after all.",),
        payoff=("it is a door, lying flat.", "", "it opens downward."),
        sound="StepSoft", done="Rustle",
        design="""
        Kept. A world that covers things, and a verb that uncovers them, and
        what you uncover stays uncovered.
        """),

    # ----------------------------------------------------------------- faces
    "faces": System(
        verb="chase the signal", thing="telephone", count=16, live=4,
        art="phone_box",
        layers=4,
        before=("there is a dial tone.", "", "it should not have one."),
        after=("the tone is the same as it was.",),
        payoff=("something starts ringing.", "",
                "it is a long way off, and it will not ring forever."),
        sound="Cursor", done="ChimeFar",
        design="""
        The grove is a broadcast, and you are tuning it.

        Lift a receiver and something starts ringing somewhere else in the
        world. The direction you move when you hear it is the input: go left
        towards the ring and the world shifts into its green state; go right
        and it shifts into another. Four states, four palettes, and the map
        underneath is the same map.

        Each state has residents the other three do not, and things you can
        pick up that the other three do not have. Some of what you find in one
        state is only *usable* in another — so progress is carrying something
        out of green and into the state where it means anything. You are not
        solving the grove. You are chasing a signal across it and taking
        whatever each channel happens to be showing.

        Nothing announces a state change. The colour of the light is the only
        notification, which is the same way this game has always told you
        where you are.
        """),

    # ----------------------------------------------------------------- hands
    "hands": System(
        verb="take its hand", thing="open hand", count=16, live=4,
        before=("it is open, and at about your height.",),
        after=("it is still pointing the way it pointed.",),
        payoff=("it closes around yours, and then it points.",),
        sound="StepStone", done="Watch",
        design="""
        The hands are not the mechanic. They are the *index* to it.

        Take a hand and it closes around yours and points. Follow the point
        exactly — not roughly, exactly — and at the end of it is an anomaly.
        The field is full of them and none are visible:

          * invisible platforms running out over the void to somewhere
          * a stretch of wall that is not wall, that you walk straight through
          * a resident who does not belong to this world at all, standing
            where nothing should be standing, who either says something that
            matters or does not wait to be spoken to
          * something buried, in a world with nothing to bury it in

        When you reach one, the world makes a sound — a single haunting note
        that plays nowhere else and means *you found it*. That note is the
        only confirmation this world ever gives.

        A hand followed carelessly leads nowhere. The pointing is precise and
        so is the following.
        """),

    # --------------------------------------------------------------- checker
    "checker": System(
        verb="flip it", thing="loose square", count=20, live=4,
        before=("this one is not fixed down.",),
        after=("it is the other colour now.",),
        payoff=("it turns over, and so does everything on it.", "",
                "this is a different part of the board."),
        sound="LowThud", done="GlassRing",
        design="""
        The board is a machine and the squares are its input.

        Stepping on a square does something. Which something depends on the
        square: some flip and stay flipped, some throw you to their opposite
        on the far side of the board, some change the world around them,
        some do nothing at all and are still part of the answer.

        Scattered through the world are *hints* — scratched into walls,
        spelled out by where objects have been left standing, arrangements of
        residents that mean something if you are looking down at them. Each
        one names squares, or an order, or a state. Follow one and nothing
        obvious happens. Follow several, in the right order, with the board in
        the right configuration, and the world does something it has no
        business doing: lore surfaces, something arrives, a part of the board
        that was never on the board opens.

        This is the *Please, Don't Touch Anything* world. Most players will
        flip squares, enjoy the teleports and leave. The sequences are for the
        player who wrote things down.

        Getting a sequence wrong is not punished and not signposted. It simply
        does not work, and the board does not care.
        """),

    # ------------------------------------------------------------------ toys
    "toys": System(
        verb="wind it", thing="key", count=22, live=4,
        before=("there is a key in its back.",),
        after=("it is going, and it is not coming back.",),
        payoff=("it does what it does.",),
        sound="Cursor", done="Appear",
        design="""
        Every toy winds, and no two do the same thing.

        One walks off through a wall. One rises and becomes a lift. One folds
        out into a bridge. One breaks and is broken forever. One opens. One
        sets off three others in a chain. One does something so small nobody
        notices. Nothing is ever announced — the joy is winding an unfamiliar
        toy and finding out, which is what a toy is for.

        Some are very well hidden. Behind, under, inside. The best ones are
        not on the route.

        And one of them is wrong.

        The wrong toy does something useful the first time — a way opens, and
        the toy is still standing there, still wound, still available. Winding
        it again does it again, and takes something. The childlike quality of
        the world thins each time: the palette drains, the music loses its
        tune, the other toys stop moving, the residents stop being toys.
        Nothing stops you. It never stops working. By the last time it is not
        a nursery any more and the way it opened is not somewhere you wanted
        to go.
        """),

    # ------------------------------------------------------------------ neon
    "neon": System(
        verb="step into the mural", thing="mural", count=20, live=4,
        layers=4,
        before=("the tube is here but nothing is in it.",),
        after=("it is lit, and it holds.",),
        payoff=("the light runs all the way out over the dark.",),
        sound="StaticBurst", done="Appear",
        design="""
        The best-looking world in the game, so the mechanic gets out of the
        way and lets it look like that.

        The floor murals are alive. Standing on one sets it going — it
        pulses, it drags its colour across the room, the residents nearby
        change into something else while it runs, the whole chamber's scheme
        swaps to the mural's own palette. Different murals, different light.
        The reward for walking over one is that it is beautiful.

        And some of them are doors. Stand on the right mural and you go *into*
        it, Mario-64 style: a whole layer of the world built out of that
        painting's palette and shapes, with its own music, its own residents,
        its own rules about what is floor. Coming back out puts you where the
        mural was.

        This is the world to over-invest in. Music, palette, overlay,
        animation, residents, the lot. It is allowed to be the simplest
        mechanically because it is doing the most work visually, and it is the
        closest thing here to the reason any of this exists.
        """),

    # ------------------------------------------------------------- umbrellas
    "umbrellas": System(
        verb="open it over you", thing="furled umbrella", count=18, live=4,
        layers=5,
        before=("it is furled.", "", "it has never once been needed."),
        after=("it is open.", "", "still nothing falls on it."),
        payoff=("it opens, and it pulls.", "",
                "you come up somewhere with more sky in it."),
        sound="Rustle", done="Appear",
        design="""
        Upward, through five planes, and it gets worse the higher you get.

        Opening an umbrella under yourself lifts you to the next plane. The
        first is cloud: soft, bright, pale, high — everything about it says
        you have arrived somewhere good, and it is laying that on slightly too
        thick.

        Each plane up, the imagery comes apart. The architecture gets more
        ordered and less kind. The light gets flatter. The residents get more
        uniform, and then more identical, and then they stop being residents
        and start being furniture. What looked ceremonial starts looking
        administrative. By the top it is a bureaucracy with very good
        lighting, and the way down is the only mercy in it.

        Nothing is ever named. There is no scripture, no iconography anybody
        could point at, nothing that says the word out loud. It is a dream
        about the *shape* of an ascent, and it should be readable three
        different ways depending on who is playing.

        Coming down is the waterfalls. The clouds pour off their own edges,
        and stepping into one drops you the whole way to the bottom in one
        go — no stages, no gentle descent. You arrive back in the soft bright
        place you started, which now reads completely differently.
        """),

    # ----------------------------------------------------------------- stars
    "stars": System(
        verb="move the tide", thing="marker", count=16, live=4,
        before=("the water is at a line on it.",),
        after=("the water is at a different line on it.",),
        payoff=("the water goes out a long way.", "",
                "what it leaves behind was always there."),
        sound="WaterDrop", done="WaterStep",
        design="""
        Kept. Changing the water level changes what is island and what is
        floor, and the shallows are wide enough that a low tide is a different
        map.
        """),
}


def of(key: str) -> System | None:
    return SYSTEMS.get(key)


def layers_needed() -> dict[str, int]:
    """Worlds that need more maps than they have, and how many.

    These are *not* subworlds — they are additional states or floors of the
    same world, reached by that world's own verb and sharing its identity.
    """
    return {key: s.layers for key, s in SYSTEMS.items() if s.layers}
