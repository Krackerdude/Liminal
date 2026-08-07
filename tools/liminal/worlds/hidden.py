"""The grove's hidden half: twelve secret rooms and four locked buildings.

The town has always had a mechanic — four receptions of one place — and until
now the only thing it did with it was change the light.  This is the part that
makes tuning *worth* something.

**The shape of it**

Every channel has three secret rooms and one locked building.  The rooms are
found; the building is opened.  Nothing is signposted, nothing is listed in a
menu, and no NPC ever says the word "key".

The twelve rooms are three *sets* of four rather than twelve one-offs, and
that is deliberate architecture rather than tidiness:

    the crack      a split in a rock face, one per channel
    the cover      a manhole in the road, one per channel
    the hatch      a way up into something small, one per channel

The same entrance in the same place on all four channels, opening onto four
different rooms.  Which means that later, when the television remote lets you
change channel wherever you happen to be standing, going into the cave on one
reception and switching inside it puts you in a different cave with a
different way out — and the way out is on a channel you could not otherwise
have reached from there.  A warp whistle made out of a thing the world was
already doing.

**The locks**

Four buildings, four keys, and the keys are deliberately in the wrong places:

    the exchange        on the grove          opens with the GREEN key
    the nursery office  on overgrown          opens with the GREY key
    the depot           on off-colour         opens with the RED key
    the transmitter     on no signal          opens with the AMBER key

A closed loop across all four receptions with none of them spare.  Each lock
is painted the colour of the channel its key comes from, which is the only
instruction the game ever gives, and it gives it without a word.

**The manhole**

One of the twelve cannot be found by looking.  The meter reader asks you —
on any channel — to come and find them somewhere else, and means it literally:
speak to them, tune away, speak to them again.  The cover comes off the moment
you do.  Nothing tells you that is what happened.
"""

from __future__ import annotations

import random

from ..cmds import MSG_MIDDLE, MV_FACE_HERO, Script
from ..maps import (ANIM_CONTINUOUS, LAYER_BELOW, LAYER_SAME, MOVE_RANDOM,
                    MOVE_STATIONARY, TRIGGER_ACTION, Page)
from ..state import (SW_HIDE_ASKED, SW_HIDE_DOOR, SW_HIDE_FOUND, SW_HIDE_KEY,
                     SW_HIDE_MANHOLE, SW_REMOTE, VR_DREAM_DISTANCE)
from . import atmosphere
from . import reach
from . import systems as sys
from .cast_lookup import charset_slot

CHANNELS = ("faces", "faces2", "faces3", "faces4")

# What each channel is called when a lock has to name it without words.
CHANNEL_COLOUR = ("amber", "green", "grey", "red")


class Area:
    """One hidden room: where it is, what is in it, and who is in it."""

    def __init__(self, key: str, title: str, family: str, channel: int,
                 npc: str, lines: tuple[str, ...],
                 prize: tuple[str, ...], *, gives: str = ""):
        self.key = key
        self.title = title
        self.family = family        # crack, cover, hatch, or lock
        self.channel = channel
        self.npc = npc
        self.lines = lines
        self.prize = prize          # what you find, said once
        self.gives = gives          # "key", "remote", or nothing
        # What it is made of follows from how you get in, rather than being
        # stated twice: you go down through rock and water, and up into board
        # and paint.  Setting it by hand is how four rooms ended up asking a
        # cave chipset for a filing rack.
        self.rock = family in ("crack", "cover")


# --- the sixteen --------------------------------------------------------------
# Three sets of four, then the four buildings.  Read down a set and it is the
# same room received four ways, which is the same trick the town itself plays.

AREAS: tuple[Area, ...] = (
    # ---- the crack in the rock face ------------------------------------------
    Area("cave1", "the culvert", "crack", 0, "gardener",
         ("i put the seed drill down here in '71.", "",
          "it's still down here. i can hear it when it rains."),
         ("a storm drain nobody has opened in years.", "",
          "the water is going somewhere and it is not going out.")),
    Area("cave2", "the root hollow", "crack", 1, "grafter",
         ("they came down through the roof and kept going.", "",
          "i didn't graft these. these joined by themselves."),
         ("the roots have made a room.", "",
          "something small is wedged in the wall of it."),
         gives="key"),
    Area("cave3", "the dry cave", "crack", 2, "ash_walker",
         ("it doesn't fall in here.", "", "that's why i come in here."),
         ("it is completely dry.", "",
          "there is a clean patch on the floor",
          "in the shape of somebody sitting.")),
    Area("cave4", "the anechoic", "crack", 3, "test_tone",
         ("...", "", "( it has stopped )", "",
          "( it has never stopped before )"),
         ("the walls are wedges, floor to ceiling.", "",
          "your own footsteps do not arrive.", "",
          "something is under the far wall."),
         gives="key"),

    # ---- under the cover -----------------------------------------------------
    Area("under1", "the sewers", "cover", 0, "meter_reader",
         ("supply comes in down here.", "",
          "so does everything else. it all comes in down here."),
         ("a brick run under the whole street plan.", "",
          "there is a bunch of keys on a nail",
          "and one of them is warm."),
         gives="key"),
    Area("under2", "the flooded run", "cover", 1, "swarm",
         ("we came down for the winter.", "", "we did not go back up."),
         ("water to the knee, and warm.", "",
          "something has been living well down here.")),
    Area("under3", "the dry main", "cover", 2, "staffholder",
         ("the levels are right down here.", "",
          "everything is right down here. that's the trouble."),
         ("the run is bone dry and swept.", "",
          "somebody has been keeping it,",
          "and they have not been up top in a long time.")),
    Area("under4", "the cable duct", "cover", 3, "continuity",
         ("FOUR CABLES LEFT THE MAST.", "", "FIVE ARRIVED HERE."),
         ("cable, in bundles, going one way.", "",
          "one of the bundles is not carrying anything",
          "and it is the warmest of them.")),

    # ---- up the hatch --------------------------------------------------------
    Area("box1", "the signal box", "hatch", 0, "commuter",
         ("i come up here to see it arriving.", "",
          "it's a better view of nothing than the stop is."),
         ("levers, all of them pulled.", "",
          "the diagram on the wall has five lines on it",
          "and the town has four.")),
    Area("box2", "the sunken greenhouse", "hatch", 1, "seedling",
         ("this is where i'm from!", "", "i think. it's warm like this."),
         ("glass, green with the inside of itself.", "",
          "everything in here grew without anybody",
          "and everything in here grew correctly.")),
    Area("box3", "the substation", "hatch", 2, "last_engineer",
         ("i'm not supposed to have a key to this.", "",
          "nobody's supposed to have a key to anything."),
         ("the substation is live and humming.", "",
          "there is a spare key on the panel,",
          "labelled with a colour rather than a name."),
         gives="key"),
    Area("box4", "the continuity suite", "hatch", 3, "presenter",
         ("I READ FROM HERE.", "", "I HAVE NEVER BEEN GIVEN ANYTHING TO READ."),
         ("a desk, a microphone, a light that is on.", "",
          "the running order is a single line",
          "and the line is your name.")),

    # ---- the four locked buildings -------------------------------------------
    Area("prem1", "the exchange", "lock", 0, "caption",
         ("[ CONNECTING ]", "", "[ STILL CONNECTING ]"),
         ("a wall of jacks, every one of them patched.", "",
          "the log says four carriers and then, later,",
          "in a different hand: FIVE.")),
    Area("prem2", "the nursery office", "lock", 1, "ranger",
         ("plan's on the wall.", "", "we planted all of it. every one."),
         ("the planting plan covers the whole town.", "",
          "every tree is on it.", "",
          "the ones over the cracks are circled.")),
    Area("prem3", "the depot", "lock", 2, "bough_sleeper",
         ("...they kept a fifth set of everything...", "",
          "...for the fifth one..."),
         ("racking, floor to roof, and all of it labelled.", "",
          "there are four of everything.", "",
          "there are five of some things.")),
    Area("prem4", "the transmitter hut", "lock", 3, "leaf_head",
         ("i sat in here until it grew.", "",
          "you can hear all four at once in here.", "",
          "you get used to it. that's the part i'd warn you about."),
         ("the transmitter is running on all four carriers.", "",
          "on the shelf, next to a cold cup:", "",
          "a television remote."),
         gives="remote"),
)

BY_KEY = {area.key: area for area in AREAS}

# Which channel's key opens which channel's building.  Deliberately offset by
# one so the four of them make a ring and nobody is left out: the grove's key
# opens the last building, and the last channel's key opens the first.
OPENS = {0: 3, 1: 0, 2: 1, 3: 2}    # key from channel -> building on channel
NEEDS = {building: key for key, building in OPENS.items()}

# Where each family's entrance stands, as an offset from a junction.  The same
# offset on all four channels, because the entrance has to be in the same place
# or the sets are four unrelated rooms rather than one room received four ways.
DOORWAYS = {"crack": (-8, -7), "cover": (4, 2), "hatch": (7, -6),
            "lock": (-7, 5)}


def _index(area: Area) -> int:
    return AREAS.index(area)


# --- the maps -----------------------------------------------------------------

def build(key: str):
    """A hidden room, as its own one-screen map.

    Four kinds of place and four different builds.  A cave is not a room with
    rock wallpaper: it has no straight walls, nothing was carried into it, and
    the water in it lies in a shape nothing cut.  A sewer *was* built, so it
    gets courses of brick and a channel running the length of it.  The rooms
    above ground are rooms, and those are the only two that get furniture.
    """
    from . import worlds as W
    from . import gen

    area = BY_KEY[key]

    def make(map_id: int):
        art = "cave1" if area.rock else "box1"
        world, cs, rng = W._new(key, map_id, 20, 15, loop=False, art=art)
        m, t = world.map, cs.tiles
        rng = random.Random(hash(key) & 0xffff)
        m.fill_rect(0, 0, m.width, m.height, t["black"])
        LAYOUTS[key](m, t, cs, rng, gen)
        # The tile you arrive on, kept clear in every room.  Two of them
        # buried it -- one under a crossing channel and one behind a wall --
        # and a hidden room you cannot stand up in is not a hidden room.
        # Only the row the player actually lands on.  Clearing two rows also
        # cleared the bottom of the way out, so the exit object lost its foot
        # and the tile in front of it stopped being part of the object.
        from ..maps import EMPTY_UPPER
        for ax in (8, 9, 10):
            m.set_lower(ax, m.height - 4, t["ground"])
            # and nothing standing on it either: the cable duct had a tray
            # over its own arrival square
            m.set_upper(ax, m.height - 4, EMPTY_UPPER)
        world.landmarks = {"out": [(9, m.height - 7)], "prize": [(15, 5)],
                           "npc": [(5, 6)]}
        world.spawn = (9, m.height - 4)
        world.npcs = []
        return world

    return make


# --- sixteen rooms, sixteen layouts -------------------------------------------
# Four family templates with a per-room tint gave sixteen rooms that were four
# rooms.  A room is its own place when its *walls* and its *contents* are its
# own, not when the same six things have been shuffled round it.  So each of
# these is written out.  They share two chipsets and nothing else.


def _shell(m, t, walls: str, floor: str, *, inset: int = 2,
           ragged: bool = False) -> None:
    """The box a room sits in.  Ragged for anything nobody built."""
    for y in range(m.height):
        give = (0, 1, 0, 2, 1, 0, 1, 2, 0, 1)[y % 10] if ragged else 0
        left, right = inset + give, m.width - inset - give
        for x in range(m.width):
            solid = x < left or x >= right or y < inset or y >= m.height - inset
            m.set_lower(x, y, t[walls if solid else floor])


def _cave1(m, t, cs, rng, gen) -> None:
    """THE CULVERT.  Where the storm drain gives out into the rock.

    Half built and half not: brick for as far as somebody bothered, and then
    the tunnel simply stops being a tunnel.
    """
    _shell(m, t, "rock_0", "ground", ragged=True)
    for y in range(3, m.height - 3):                # the brick half, west
        for x in range(2, 9):
            m.set_lower(x, y, t["brick"] if y < 5 or y > m.height - 6
                        else t["ground_b"])
    for x in range(2, 12):                          # the drain, still running
        m.set_lower(x, 7, t["channel"])
        m.set_lower(x, 8, t["channel"])
    for x in range(12, m.width - 3):                # and where it soaks away
        m.set_lower(x, 7, t["pool_1"])
        m.set_lower(x, 8, t["pool_2"])
    gen.stamp(m, cs.obj("boulder"), 14, 4)
    gen.stamp(m, cs.obj("column"), 16, 2, overlap=True)
    gen.stamp(m, cs.obj("mouth"), 9, m.height - 7, overlap=True)


def _cave2(m, t, cs, rng, gen) -> None:
    """THE ROOT HOLLOW.  A shaft the roots came down and kept going."""
    _shell(m, t, "rock_1", "ground_b", ragged=True)
    for cx in (4, 6, 9, 11, 14, 16):                # a forest of them
        gen.stamp(m, cs.obj("column"), cx, 1 + (cx % 3), overlap=True)
    for x in range(6, 14):                          # soft ground under it all
        for y in range(9, 12):
            m.set_lower(x, y, t["path"])
    gen.stamp(m, cs.obj("boulder_small"), 3, 10)
    gen.stamp(m, cs.obj("mouth"), 9, m.height - 7, overlap=True)


def _cave3(m, t, cs, rng, gen) -> None:
    """THE DRY CAVE.  A wide flat nothing, and one clean patch on it.

    The emptiest room in the game.  Everything has been pushed to the walls
    and the middle is bare, which is what somebody does to a room they sit in.
    """
    _shell(m, t, "rock_2", "ground", inset=2, ragged=True)
    for n, (bx, by) in enumerate(((3, 3), (16, 3), (3, 11), (16, 10),
                                  (5, 2), (13, 12))):
        gen.stamp(m, cs.obj("boulder" if n % 3 else "boulder_small"), bx, by)
    for y in range(6, 10):                          # the clean patch
        for x in range(8, 12):
            m.set_lower(x, y, t["smooth"])
    # Standing at the head of the clean patch, facing it.  Whoever sat here
    # sat looking at this.
    gen.stamp(m, cs.obj("gate_purgatory"), 9, 3)
    gen.stamp(m, cs.obj("mouth"), 9, m.height - 7, overlap=True)


def _cave4(m, t, cs, rng, gen) -> None:
    """THE ANECHOIC.  The only room down here with no fault in it.

    Perfectly rectangular, wedges floor to ceiling, a poured floor and not one
    loose stone.  Everywhere else underground is irregular on purpose; this
    one repeats exactly, and that is the whole of what is wrong with it.
    """
    _shell(m, t, "wedge", "smooth", inset=2)
    for y in range(2, m.height - 2):                # wedges on the inside too
        m.set_lower(2, y, t["wedge"])
        m.set_lower(m.width - 3, y, t["wedge"])
    for x in range(2, m.width - 2):
        m.set_lower(x, 2, t["wedge"])
        m.set_lower(x, m.height - 3, t["wedge"])
    # A room with no fault in it, and one thing in it that is not foam.  It is
    # dead centre, because in a space this regular the middle is the only
    # place anything can be.
    gen.stamp(m, cs.obj("gate_hell"), 9, 5)
    gen.stamp(m, cs.obj("mouth"), 9, m.height - 7, overlap=True)


def _under1(m, t, cs, rng, gen) -> None:
    """THE SEWERS.  Four runs meeting under the crossroads."""
    _shell(m, t, "brick", "ground", inset=2)
    for x in range(2, m.width - 2):                 # the east-west main
        m.set_lower(x, 7, t["channel"])
        m.set_lower(x, 8, t["channel"])
    for y in range(2, m.height - 2):                # and the one crossing it
        m.set_lower(9, y, t["channel"])
        m.set_lower(10, y, t["channel"])
    for x in range(8, 12):                          # a slab over the junction
        for y in range(7, 9):
            m.set_lower(x, y, t["ground_b"])
    # The way further down.  It stands at the head of the north run, so the
    # first thing you see coming down the ladder is the length of the sewer
    # with something standing at the end of it.
    for x in range(8, 12):
        for y in range(3, 6):
            m.set_lower(x, y, t["ground"])
    gen.stamp(m, cs.obj("gate_caustic"), 9, 3)
    gen.stamp(m, cs.obj("ladder"), 9, m.height - 7, overlap=True)


def _under2(m, t, cs, rng, gen) -> None:
    """THE FLOODED RUN.  Water bank to bank, and a ledge along one wall."""
    _shell(m, t, "brick", "deep", inset=2)
    for x in range(2, m.width - 2):                 # the ledge, and only it
        m.set_lower(x, m.height - 4, t["ground"])
        m.set_lower(x, m.height - 3, t["ground_b"])
    for x in range(3, 8):
        m.set_lower(x, 3, t["ground"])              # a step down at the far end
    gen.stamp(m, cs.obj("ladder"), 9, m.height - 7, overlap=True)


def _under3(m, t, cs, rng, gen) -> None:
    """THE DRY MAIN.  Swept, and kept, by somebody who has not been up."""
    _shell(m, t, "brick", "ground", inset=3)
    for x in range(3, m.width - 3):                 # the invert, with nothing
        m.set_lower(x, 7, t["dry"])
        m.set_lower(x, 8, t["dry"])
    for n, bx in enumerate((4, 6, 14, 16)):         # stacked against the wall
        gen.stamp(m, cs.obj("boulder_small"), bx, 4 if n % 2 else 10)
    gen.stamp(m, cs.obj("ladder"), 9, m.height - 7, overlap=True)


def _under4(m, t, cs, rng, gen) -> None:
    """THE CABLE DUCT.  Low, narrow, and going one way only."""
    _shell(m, t, "brick", "ground", inset=4)
    for y in (4, m.height - 5):                     # trays on both walls
        for x in range(4, m.width - 6, 3):
            gen.stamp(m, cs.obj("cable"), x, y, overlap=True)
    gen.stamp(m, cs.obj("ladder"), 9, m.height - 7, overlap=True)


def _room_shell(m, t) -> None:
    """The four walls every room above ground has."""
    for x in range(1, m.width - 1):
        m.set_lower(x, 0, t["cut_n"])
        m.set_lower(x, 1, t["face_n"])
        m.set_lower(x, 2, t["face_n_low"])
        m.set_lower(x, m.height - 3, t["face_s"])
        m.set_lower(x, m.height - 2, t["face_s_low"])
        m.set_lower(x, m.height - 1, t["cut_s"])
    for y in range(3, m.height - 3):
        m.set_lower(1, y, t["cut_w"])
        m.set_lower(2, y, t["face_w"])
        m.set_lower(m.width - 3, y, t["face_e"])
        m.set_lower(m.width - 2, y, t["cut_e"])
        for x in range(3, m.width - 3):
            m.set_lower(x, y, t["ground_b" if (x * 3 + y * 5) % 7 == 0
                                else "ground"])


def _box1(m, t, cs, rng, gen) -> None:
    """THE SIGNAL BOX.  One long bank of levers and a view of nothing."""
    _room_shell(m, t)
    for x in range(3, m.width - 3):                 # the operating floor
        m.set_lower(x, 9, t["stone"])
        m.set_lower(x, 10, t["stone"])
    for lx in (4, 7, 10, 13):
        gen.stamp(m, cs.obj("levers"), lx, 6)
    gen.stamp(m, cs.obj("board"), 15, 3, overlap=True)
    gen.stamp(m, cs.obj("desk"), 3, 3)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _box2(m, t, cs, rng, gen) -> None:
    """THE SUNKEN GREENHOUSE.  Glass on every side and beds down both."""
    _room_shell(m, t)
    for x in range(1, m.width - 1):                 # glass, not plaster
        m.set_lower(x, 1, t["glass"])
        m.set_lower(x, 2, t["glass"])
    for y in range(3, m.height - 3):
        m.set_lower(2, y, t["glass"])
        m.set_lower(m.width - 3, y, t["glass"])
    for y in range(4, m.height - 4):                # the beds
        for x in list(range(3, 7)) + list(range(13, 17)):
            m.set_lower(x, y, t["bed"])
    for x in range(7, 13):                          # the path between them
        for y in range(3, m.height - 3):
            m.set_lower(x, y, t["stone"])
    gen.stamp(m, cs.obj("crate"), 9, 4)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _box3(m, t, cs, rng, gen) -> None:
    """THE SUBSTATION.  Live, fenced, and you are not going to touch it."""
    _room_shell(m, t)
    for y in range(4, 11):                          # a poured slab
        for x in range(5, 15):
            m.set_lower(x, y, t["stone"])
    gen.stamp(m, cs.obj("transformer"), 8, 4)
    for fx in (6, 8, 10, 12):                       # the fence round it
        gen.stamp(m, cs.obj("fence"), fx, 8, overlap=True)
    gen.stamp(m, cs.obj("rack"), 3, 3)
    gen.stamp(m, cs.obj("machine"), 15, 3)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _box4(m, t, cs, rng, gen) -> None:
    """THE CONTINUITY SUITE.  A desk, a light, and a window into the dark."""
    _room_shell(m, t)
    for x in range(6, 14):                          # the booth beyond the glass
        for y in range(3, 6):
            m.set_lower(x, y, t["glass"])
    for y in range(7, 11):                          # the studio floor
        for x in range(4, 16):
            m.set_lower(x, y, t["rug"])
    gen.stamp(m, cs.obj("desk"), 8, 7)
    gen.stamp(m, cs.obj("board"), 3, 3, overlap=True)
    gen.stamp(m, cs.obj("rack"), 15, 6)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _prem1(m, t, cs, rng, gen) -> None:
    """THE EXCHANGE.  Frames in rows, and one aisle down the middle."""
    _room_shell(m, t)
    for fx in (3, 6, 12, 15):
        gen.stamp(m, cs.obj("frame"), fx, 3)
        gen.stamp(m, cs.obj("frame"), fx, 8)
    for y in range(3, m.height - 3):                # the aisle
        for x in range(9, 12):
            m.set_lower(x, y, t["stone"])
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _prem2(m, t, cs, rng, gen) -> None:
    """THE NURSERY OFFICE.  One plan on the wall and stock along the sides."""
    _room_shell(m, t)
    for x in range(3, m.width - 3):                 # the plan, floor to eye
        m.set_lower(x, 3, t["rug"])
    for y in range(5, m.height - 4):                # stock, both walls
        for x in (3, 4, 15, 16):
            m.set_lower(x, y, t["bed"])
    gen.stamp(m, cs.obj("board"), 6, 1, overlap=True)
    gen.stamp(m, cs.obj("desk"), 5, 9)
    gen.stamp(m, cs.obj("crate"), 6, 5)
    # There is a door in the back of this office that is not on the plan.
    for y in range(4, 8):
        for x in range(10, 14):
            m.set_lower(x, y, t["stone"])
    gen.stamp(m, cs.obj("gate_lobotomy"), 11, 4)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _prem3(m, t, cs, rng, gen) -> None:
    """THE DEPOT.  Deep racking in aisles, and four of everything."""
    _room_shell(m, t)
    for ry in (3, 8):
        for rx in (3, 6, 9, 12, 15):
            gen.stamp(m, cs.obj("rack"), rx, ry)
    for x in range(3, m.width - 3):                 # the picking aisle
        m.set_lower(x, 7, t["stone"])
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


def _prem4(m, t, cs, rng, gen) -> None:
    """THE TRANSMITTER HUT.  Too small for what is in it."""
    _room_shell(m, t)
    for y in range(3, m.height - 3):                # the hut is narrower
        for x in list(range(3, 6)) + list(range(14, 17)):
            m.set_lower(x, y, t["cut_w" if x < 6 else "cut_e"])
    for y in range(6, 11):
        for x in range(6, 14):
            m.set_lower(x, y, t["stone"])
    gen.stamp(m, cs.obj("transmitter"), 6, 3)
    gen.stamp(m, cs.obj("rack"), 12, 3)
    gen.stamp(m, cs.obj("desk"), 11, 9)
    gen.stamp(m, cs.obj("way_out"), 9, m.height - 7, overlap=True)


LAYOUTS = {
    "cave1": _cave1, "cave2": _cave2, "cave3": _cave3, "cave4": _cave4,
    "under1": _under1, "under2": _under2, "under3": _under3,
    "under4": _under4,
    "box1": _box1, "box2": _box2, "box3": _box3, "box4": _box4,
    "prem1": _prem1, "prem2": _prem2, "prem3": _prem3, "prem4": _prem4,
}


# --- what happens in them -----------------------------------------------------

def _gleam(**kwargs) -> Page:
    """The interactable page, imported late.

    ``events`` imports ``worlds`` and ``worlds`` builds these rooms, so this
    module cannot import ``events`` at the top of itself without closing the
    circle.  Everything it needs from there is fetched at call time instead.
    """
    from .events import gleam
    return gleam(**kwargs)


def _prize(area: Area) -> Script:
    """The one thing in the room, said once and then remembered."""
    index = _index(area)
    s = Script()
    s.se("ChimeFar", volume=40)
    s.msg(*area.prize)
    if area.gives == "key":
        s.se("ItemGet", volume=64)
        s.msg("", "a key.", "",
              f"the tag on it is {CHANNEL_COLOUR[area.channel]}.")
        s.switch(SW_HIDE_KEY + area.channel, True)
    elif area.gives == "remote":
        s.se("ItemGet", volume=70)
        s.flash(240, 236, 226, 26, 4, False)
        s.msg("", "you take the remote.", "",
              "it is warm, and it has four buttons,",
              "and one of them is worn down to the plastic.")
        s.switch(SW_REMOTE, True)
    s.switch(SW_HIDE_FOUND + index, True)
    return s


def _reachable_spot(world, x: int, y: int, open_tiles) -> tuple[int, int]:
    """A tile near (x, y) the player can actually walk up to and face.

    Falls back to the requested tile when the room offers nothing better,
    which cannot happen in a room with any floor in it but is not worth
    crashing the build over.
    """
    found = reach.spot_for(world, x, y, stand_on=False,
                           open_tiles=open_tiles, radius=10)
    return found if found is not None else (x, y)


def events(world, worlds: dict) -> None:
    """One hidden room: the way out, the resident, and the thing in it."""
    from .events import _door, _place

    area = BY_KEY[world.key]
    m = world.map
    from .events import _arrival_event
    m.add_event("arrive", 0, 0, [_arrival_event(world)])

    # Where the resident stands and where the prize sits are chosen against
    # the *finished* room rather than trusted from the layout.  Sixteen rooms
    # were each drawn by hand and each of them was then handed the same three
    # coordinates; where a room's own furniture happened to be standing there,
    # the resident and the prize went behind it.  That is how the television
    # remote ended up in a wall.  So the room is walked first, and everything
    # that is not part of the scenery is put somewhere the player can get to.
    open_tiles = reach.walkable(world)

    home = worlds[CHANNELS[area.channel]]
    # On the *bottom row of the exit object itself*, which is the tile the
    # player is facing when they stand on the arrival square.  It used to go
    # three rows below the object's top, which in a fifteen-row map is inside
    # the wall -- so every hidden room in the game was a room you could not
    # leave.
    ox, oy = world.landmarks["out"][0]
    _place(world, "the way out", *_reachable_spot(world, ox, oy + 2, open_tiles),
           [_door(home.map_id, *home.spawn, sound="StepStone",
                  leaving=world.key, entering=home.key)])

    sheet, slot = charset_slot(_channel_design(area))
    said = Script()
    said.move_route(0, [MV_FACE_HERO], frequency=8)
    said.msg(*area.lines)
    nx, ny = _reachable_spot(world, *world.landmarks["npc"][0], open_tiles)
    m.add_event(area.npc, nx, ny, [
        Page(script=said, charset=sheet, charset_index=slot,
             move_type=MOVE_STATIONARY, move_speed=2, move_frequency=3,
             trigger=TRIGGER_ACTION, animation_type=ANIM_CONTINUOUS)])

    if world.key in DESCENTS:
        _descent(world, area, open_tiles)

    px, py = _reachable_spot(world, *world.landmarks["prize"][0], open_tiles)
    taken = Script()
    taken.msg("you have already been through this.")
    _place(world, "what is here", px, py, [
        _gleam(script=_prize(area), trigger=TRIGGER_ACTION),
        _gleam(script=taken, trigger=TRIGGER_ACTION,
              switch_a=SW_HIDE_FOUND + _index(area), translucent=True),
    ])


# --- the four ways further down -----------------------------------------------
# Not built yet: four mirrors standing in four of the sixteen rooms, each one
# showing the place on the other side of it.  They are placed now rather than
# later because where a door *stands* is most of what it means — the one in
# the sewers is at the head of a long run so you see it before you reach it,
# the one in the anechoic is dead centre because in a room that regular the
# middle is the only place anything can be, the one in the dry cave faces the
# clean patch somebody used to sit on, and the one in the nursery office is
# behind a door that is not on the plan.
DESCENTS = {
    "under1": ("caustic", "the sewers", (
        "the run keeps going, and it should not.", "",
        "the brick stops and something else carries on,",
        "and it is lit from inside itself.")),
    "cave4": ("hell", "the anechoic", (
        "there is a door in the wedge wall.", "",
        "it does not have a frame, a hinge or a handle.", "",
        "you can hear through it. only through it.")),
    "cave3": ("purgatory", "the dry cave", (
        "it is standing at the head of the clean patch,", "facing it.", "",
        "whoever sat here sat looking at this.")),
    "prem2": ("lobotomy", "the nursery office", (
        "there is a door in the back wall.", "",
        "it is not on the plan, and the plan has everything on it.", "",
        "there is light coming under it, and it is very warm light.")),
}

# What each of them says when you try it, which is the same in all four cases
# and is the point: they are not shut, they are not ready.
NOT_YET = ("", "not yet.")


def _descent(world, area, open_tiles=None) -> None:
    """The mirror that goes further down, and what it shows."""
    from .events import _place

    key, _, lines = DESCENTS[world.key]
    look = Script()
    look.se("Watch", volume=44)
    look.msg(*lines)
    look.wait(8)
    look.se("ChimeFar", volume=30)
    look.msg(*NOT_YET)
    _place(world, f"the way to {key}",
           *_reachable_spot(world, 10, 6, open_tiles),
           [_gleam(script=look, trigger=TRIGGER_ACTION)])


def _channel_design(area: Area) -> str:
    """The resident, drawn as their own channel receives them."""
    from .grove import SUFFIX
    return f"{area.npc}{SUFFIX[CHANNELS[area.channel]]}"


# --- how you get in -----------------------------------------------------------

def _stamp(world, obj: str, x: int, y: int) -> None:
    """Put the entrance on the map, so there is something to walk up to."""
    from . import gen
    gen.stamp(world.map, world.chipset.obj(obj), x, y, overlap=True)


# What each entrance is bedded on, and therefore what it has to stand on.
# These four are lower-layer objects -- Block F had no room left -- so each one
# carries its own ground, and standing a turf-bedded crack in the carriageway
# puts a green rectangle in the middle of the road.  The first version did
# exactly that.
BEDDING = {"crack": ("ground", "ground_b", "path"),
           "hatch": ("ground", "ground_b", "path"),
           "cover": ("road", "road_line", "road_line_h"),
           "lock":  ("paving", "ground", "ground_b", "path")}


def _approachable(world, obj: str, x: int, y: int, open_tiles,
                  radius: int = 8) -> tuple[int, int]:
    """Move an entrance until the player can actually walk up to it.

    An entrance is a solid two-by-three object dropped at an offset from a
    clearing, and a clearing in this town is ringed with trees.  Twice the
    offset put the crack in the middle of the ring, where it was perfectly
    visible from nowhere and reachable from nowhere.

    So the footprint is tried against the town as it stands: it is a good spot
    when at least one tile *outside* the footprint but touching it is ground
    the player can already reach.  The requested position wins when it
    qualifies, and the nearest one that does wins when it does not.
    """
    m = world.map
    grid = world.chipset.obj(obj)
    bed = {world.chipset.tiles[name] for name in BEDDING[obj]
           if name in world.chipset.tiles}

    def on_its_own_ground(px: int, py: int) -> bool:
        return all(m.get_lower((px + c) % m.width, (py + r) % m.height) in bed
                   for r in range(grid.rows) for c in range(grid.cols))

    def touches_floor(px: int, py: int) -> bool:
        feet = {((px + c) % m.width, (py + r) % m.height)
                for r in range(grid.rows) for c in range(grid.cols)}
        for fx, fy in feet:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                side = ((fx + dx) % m.width, (fy + dy) % m.height)
                if side not in feet and side in open_tiles:
                    return True
        return False

    if touches_floor(x, y) and on_its_own_ground(x, y):
        return x, y
    # Rank on the ground first and the distance second: an entrance five tiles
    # further along a verge is still in the place it belongs, and one tile into
    # the carriageway is not.
    best = None
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            px, py = (x + dx) % m.width, (y + dy) % m.height
            if not touches_floor(px, py):
                continue
            rank = (0 if on_its_own_ground(px, py) else 1, dx * dx + dy * dy)
            if best is None or rank < best[0]:
                best = (rank, (px, py))
    return best[1] if best else (x, y)


def entrances(world, worlds: dict, rng: random.Random) -> None:
    """The crack, the cover, the hatch and the locked door, on one channel."""
    from .events import _door, _place_object
    from . import gen

    channel = CHANNELS.index(world.key)
    # The town as it stands, before any entrance is cut into it.
    open_tiles = reach.walkable(world)
    spots = list(world.landmarks.get("junctions", [])) or [world.spawn]
    glades = list(world.landmarks.get("glades", [])) or [world.spawn]

    for area in AREAS:
        if area.channel != channel:
            continue
        base = glades if area.family in ("crack", "hatch") else spots
        anchor = base[_index(area) % len(base)]
        dx, dy = DOORWAYS[area.family]
        x, y = (anchor[0] + dx) % world.map.width, \
               (anchor[1] + dy) % world.map.height
        target = worlds[area.key]
        opening = _door(target.map_id, *target.spawn, sound="StepStone",
                        leaving=world.key, entering=area.key)
        kind = {"crack": "crack", "cover": "cover",
                "hatch": "hatch"}.get(area.family, "lock")
        x, y = _approachable(world, kind, x, y, open_tiles)

        # Stamp the thing before hanging the interaction on it.  Every one of
        # these was an invisible gleam on open grass until a playthrough went
        # looking for them and correctly reported that the entrance to the
        # hidden half did not exist.  An interaction with nothing under it is
        # the same bug as the phantom phone box, and it is worse here, because
        # this is not a piece of scenery -- it is the way in.
        if area.family == "crack":
            look = Script()
            look.se("StepStone", volume=34)
            look.msg("a split in the rock, shoulder wide.", "",
                     "it does not close up again behind it.")
            _stamp(world, "crack", x, y)
            _place_object(world, "crack", [
                _gleam(script=look, trigger=TRIGGER_ACTION), opening],
                at=(x, y), name="the crack")

        elif area.family == "cover":
            shut = Script()
            shut.se("LowThud", volume=30)
            shut.msg("a cover, seated in the road.", "",
                     "there is no lifting it from up here.")
            _stamp(world, "cover", x, y)
            _place_object(world, "cover", [
                _gleam(script=shut, trigger=TRIGGER_ACTION),
                _gleam(script=_lift(target), trigger=TRIGGER_ACTION,
                      switch_a=SW_HIDE_MANHOLE),
            ], at=(x, y), name="the cover")

        elif area.family == "hatch":
            _stamp(world, "hatch", x, y)
            _place_object(world, "hatch", [
                _gleam(script=_hatch(target), trigger=TRIGGER_ACTION)],
                at=(x, y), name="the hatch")

        else:
            _stamp(world, "lock", x, y)
            _place_object(world, "lock", [
                _gleam(script=_locked(area), trigger=TRIGGER_ACTION),
                _gleam(script=_unlock(area, target), trigger=TRIGGER_ACTION,
                      switch_a=SW_HIDE_KEY + NEEDS[area.channel]),
            ], at=(x, y), name="the door")

    _the_ask(world, channel)


def _lift(target) -> Script:
    s = Script()
    s.se("LowThud", volume=54)
    s.msg("the cover is off.", "", "somebody took it off from underneath.")
    s.bgm_fadeout(6)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("faces").leave)
    s.teleport(target.map_id, *target.spawn)
    s.fade_in(atmosphere.of(target.key).enter)
    return s


def _hatch(target) -> Script:
    s = Script()
    s.se("Latch", volume=44)
    s.msg("a hatch, and a ladder under it.")
    s.bgm_fadeout(6)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("faces").leave)
    s.teleport(target.map_id, *target.spawn)
    s.fade_in(atmosphere.of(target.key).enter)
    return s


def _locked(area: Area) -> Script:
    """The door, shut.  The lock is the only instruction in the puzzle."""
    colour = CHANNEL_COLOUR[NEEDS[area.channel]]
    s = Script()
    s.se("Latch", volume=40)
    s.msg(f"{area.title}.", "", "locked.")
    s.wait(6)
    s.msg(f"the lock is painted {colour}.", "",
          "it has been painted that colour deliberately.")
    return s


def _unlock(area: Area, target) -> Script:
    s = Script()
    s.se("Latch", volume=52)
    s.msg("the key turns.")
    s.se("DoorOpen", volume=62)
    s.switch(SW_HIDE_DOOR + area.channel, True)
    s.bgm_fadeout(6)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("faces").leave)
    s.teleport(target.map_id, *target.spawn)
    s.fade_in(atmosphere.of(target.key).enter)
    return s


# --- the one you cannot find by looking ---------------------------------------

ASK = {
    0: ("do me a favour.", "",
        "go and find me somewhere else.", "",
        "i'll know."),
    1: ("find me on another one!", "", "i'll be so pleased."),
    2: ("come and find me somewhere else.", "",
        "i want to know if i'm the same."),
    3: ("FIND ME AGAIN.", "", "SOMEWHERE I AM WORSE."),
}

ANSWER = ("you found me.", "", "i said i'd know.", "",
          "the cover in the road's off.", "",
          "it's been off since you came in. i just didn't say.")


def _the_ask(world, channel: int) -> None:
    """The meter reader, who wants to be met twice.

    Two pages and one switch.  The first time you speak to them anywhere they
    ask; the second time you speak to them *on a different channel* they
    answer, and the manhole is already open — it has been open since you
    walked in, which is the only joke this puzzle tells.
    """
    from .events import _place

    from .grove import SUFFIX
    design = f"meter_reader{SUFFIX[CHANNELS[channel]]}"
    sheet, slot = charset_slot(design)

    ask = Script()
    ask.move_route(0, [MV_FACE_HERO], frequency=8)
    ask.msg(*ASK[channel])
    ask.switch(SW_HIDE_ASKED, True)

    answer = Script()
    answer.move_route(0, [MV_FACE_HERO], frequency=8)
    answer.se("LowThud", volume=34)
    answer.msg(*ANSWER)
    answer.switch(SW_HIDE_MANHOLE, True)

    spots = list(world.landmarks.get("junctions", [])) or [world.spawn]
    ax, ay = spots[(channel + 1) % len(spots)]
    _place(world, "the one who asks", ax + 3, ay + 4, [
        Page(script=ask, charset=sheet, charset_index=slot,
             move_type=MOVE_STATIONARY, trigger=TRIGGER_ACTION,
             animation_type=ANIM_CONTINUOUS),
        Page(script=answer, charset=sheet, charset_index=slot,
             move_type=MOVE_STATIONARY, trigger=TRIGGER_ACTION,
             animation_type=ANIM_CONTINUOUS, switch_a=SW_HIDE_ASKED),
    ])
