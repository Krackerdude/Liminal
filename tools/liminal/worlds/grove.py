"""The grove, and the three other ways of receiving it.

One town.  Four channels.  The street plan is generated once and shared, so
tuning never moves a kerb — what moves is the light on it, what is alive in
it, who is standing in it, and which of the five sealed yards the wood is
currently willing to let you into.

**The receiver**  A payphone in the first junction is ringing when you arrive
and does not stop when you lift it.  From then on the town rings at you
periodically, from a direction.  Walk that way inside the window and the
picture changes around you without you having gone anywhere.  Miss it and
nothing at all happens — no penalty, no message, no second chance on that
ring.  The next one is along in twenty seconds, on the beat.

**The yards**  Five, buried in the green.  Each is reachable on exactly one
channel, because on that channel the seam of wood between it and the street
is not rendered as wood.  Four of them hold one carried thing each, and every
one of those four is *used* on a channel other than the one that had it:

    the grove   →  the coin      used in  no signal
    no signal   →  the tape      used in  overgrown
    overgrown   →  the seed      used in  off-colour
    off-colour  →  the bulb      used back in the grove

which is a closed loop that crosses the whole cast, the whole town and every
reception of it, and cannot be short-circuited: nothing in a yard opens
without the thing found in the yard before it.  The fifth yard is the
compound at the foot of the mast, and it only opens for the bulb.

Nothing in here explains any of that.  The signs are the only signposting and
they are signs, not tutorials.
"""

from __future__ import annotations

import os
import random

from ..cmds import MV_FACE_HERO, Script
from ..maps import (ANIM_CONTINUOUS, LAYER_BELOW, LAYER_SAME, MOVE_RANDOM,
                    MOVE_STATIONARY, TRIGGER_ACTION, TRIGGER_AUTO,
                    TRIGGER_PARALLEL, Page)
from ..state import (SW_FACE_BULB, SW_FACE_COIN, SW_FACE_ENDED, SW_FACE_HEARD,
                     SW_FACE_MAST, SW_FACE_SEED, SW_FACE_TAPE, VR_CHANNEL,
                     VR_AMBIENCE, VR_RING_DIR, VR_RING_WAIT, VR_RING_X,
                     VR_RING_Y)
from ..art.cast import WORLD_CAST
from . import atmosphere
from . import systems as sys
from .cast_lookup import charset_slot
from .events import gleam

# 0 up, 1 right, 2 down, 3 left — the engine's own order, used for the pan.
UP, RIGHT, DOWN, LEFT = range(4)

# How long between rings, in tenths of a second.  Fixed rather than random:
# the window is short and missable on purpose, and a player who cannot feel
# the beat cannot choose to be ready for it.
RING_INTERVAL = 200

# Where the shudder sits for each direction, as the *centre* of the picture on
# a 320x240 screen, and which of the two bands to use.  The band is jittered
# a few pixels while the ring sounds, so the side the sound came from is the
# side that visibly moves.  This is not a camera shake and could not be one:
# a shake moves the whole picture, and the whole picture is not what rang.
SHUDDER = {
    UP:    ("ShudderH", 160, 34),
    RIGHT: ("ShudderV", 286, 120),
    DOWN:  ("ShudderH", 160, 206),
    LEFT:  ("ShudderV", 34, 120),
}
# How far it moves and how long each nudge takes.  Three pixels at a tenth of
# a second reads as a quiver; more than that reads as a fault.
SHUDDER_THROW = 3
SHUDDER_BEATS = 6

# How long the player has, in tenths of a second, from the ring to having
# moved.  Two seconds is about eight tiles at walking pace and about two if
# you have to decide first, which is the difference the window is measuring.
WINDOW = 20
# How far counts as having gone that way.  Two tiles: enough that turning on
# the spot is not enough, small enough that one committed step-and-a-half is.
COMMIT = 2
# Anything past this is the map wrapping under you at the seam, not a walk.
WRAP_GUARD = 24


# --- the four receptions ------------------------------------------------------

CHANNELS = ("faces", "faces2", "faces3", "faces4")


def channel_of(key: str) -> int:
    return CHANNELS.index(key)


# What each yard is, which channel opens it, what it wants and what it gives.
# Read down the ``needs`` column and the loop is visible: every yard after the
# first wants the thing the yard before it handed over, and the last one wants
# the thing that closes the circle back onto the channel you started on.
YARDS = (
    dict(name="exchange", channel=0, needs=None, gives=SW_FACE_COIN,
         thing="coin"),
    dict(name="nursery", channel=1, needs=SW_FACE_TAPE, gives=SW_FACE_SEED,
         thing="seed"),
    dict(name="substation", channel=2, needs=SW_FACE_SEED, gives=SW_FACE_BULB,
         thing="bulb"),
    dict(name="studio", channel=3, needs=SW_FACE_COIN, gives=SW_FACE_TAPE,
         thing="tape"),
    dict(name="compound", channel=0, needs=SW_FACE_BULB, gives=SW_FACE_MAST,
         thing=None),
)


# --- the ring -----------------------------------------------------------------

def _ringer(world) -> Page:
    """The periodic ring, and the window it opens.

    A parallel process, running the whole time the receiver is in your hands.
    It counts down twenty seconds, picks a direction, and rings from it: panned
    in stereo, with the camera drifting a single tile that way, and with that
    edge of the screen visibly quivering for as long as the ring lasts.  Then
    it compares where you were standing against where you are standing two
    seconds later.

    The interval used to be a random five to ten seconds and the direction cue
    was stereo and a one-tile pan.  Neither survives contact with a player: a
    window you cannot anticipate is a window you can only be given, and up and
    down are not places in a stereo field at all.  A fixed beat and a shudder
    on the edge it came from fix both without saying anything out loud.

    The comparison is deliberately crude.  It does not care what you are
    facing, whether you stopped, or how you got there.  It cares that you went
    that way.  A miss is silent: the phone stops, and the town is exactly as
    it was, which is the point of a window that can be missed.
    """
    channel = channel_of(world.key)
    nxt = CHANNELS[(channel + 1) % len(CHANNELS)]

    s = Script()
    s.comment("the town rings at you, periodically, from a direction")
    with s.loop():
        # twenty seconds, counted down a tenth at a time so the interval can
        # be a variable rather than a constant
        s.var(VR_RING_WAIT, RING_INTERVAL)
        with s.loop():
            s.wait(1)
            s.var(VR_RING_WAIT, 1, 2)
            with s.if_var(VR_RING_WAIT, 0, 2):
                s.break_loop()

        s.var_random(VR_RING_DIR, 0, 3)
        s.var_from_event(VR_RING_X, 10001, 1)
        s.var_from_event(VR_RING_Y, 10001, 2)

        # the ring itself, placed in the stereo field, in the camera, and now
        # on the edge of the screen it came from
        for direction, balance in ((UP, 50), (RIGHT, 92), (DOWN, 50), (LEFT, 8)):
            with s.if_var(VR_RING_DIR, direction):
                s.se("PhoneFar", volume=58, balance=balance,
                     tempo=112 if direction == UP else
                     (88 if direction == DOWN else 100))
                s.pan(direction, 1, 3, wait=False)
                _shudder(s, direction)

        s.wait(WINDOW - SHUDDER_BEATS * 2)
        s.pan_reset(speed=3, wait=False)

        # where you are now, minus where you were: the whole judgement
        s.var_from_event(VR_RING_X, 10001, 1, 2)
        s.var_from_event(VR_RING_Y, 10001, 2, 2)
        # the subtraction above leaves (was - now); flip it so the sign reads
        # the way a direction does
        s.var(VR_RING_X, -1, 3)
        s.var(VR_RING_Y, -1, 3)

        followed = [
            (UP, VR_RING_Y, -COMMIT, 2, -WRAP_GUARD, 1),
            (RIGHT, VR_RING_X, COMMIT, 1, WRAP_GUARD, 2),
            (DOWN, VR_RING_Y, COMMIT, 1, WRAP_GUARD, 2),
            (LEFT, VR_RING_X, -COMMIT, 2, -WRAP_GUARD, 1),
        ]
        for direction, axis, threshold, op, guard, guard_op in followed:
            with s.if_var(VR_RING_DIR, direction):
                with s.if_var(axis, threshold, op):
                    # far enough, and not so far that the map wrapped
                    with s.if_var(axis, guard, guard_op):
                        _tune(s, world, nxt)
    return Page(script=s, trigger=TRIGGER_PARALLEL, layer=LAYER_BELOW,
                switch_a=SW_FACE_HEARD)


def _shudder(s: Script, direction: int) -> None:
    """Jitter one edge of the screen for as long as the phone is ringing.

    A picture, not the camera.  It is shown at the edge the sound is panned
    to, nudged back and forth by a few pixels a handful of times, and erased —
    so the cue is local to that side and the rest of the frame never moves.

    Left and right share one band and up and down share the other; the art
    fades out at both ends of itself so the same picture sits correctly on
    either edge of the pair.
    """
    name, cx, cy = SHUDDER[direction]
    horizontal = direction in (LEFT, RIGHT)
    s.show_picture(sys.PIC_SHUDDER, name, cx, cy, transparency=62)
    for beat in range(SHUDDER_BEATS):
        throw = SHUDDER_THROW if beat % 2 == 0 else -SHUDDER_THROW
        # the band moves along its own length, not across it: a strip of
        # broken lines sliding sideways reads as a wobble, and the same strip
        # sliding through its own thickness reads as nothing
        s.move_picture(sys.PIC_SHUDDER,
                       cx + (0 if horizontal else throw),
                       cy + (throw if horizontal else 0),
                       transparency=62 if beat < SHUDDER_BEATS - 2 else 88,
                       tenths=1, wait=True)
        s.wait(1)
    s.erase_picture(sys.PIC_SHUDDER)


def _tune(s: Script, world, target_key: str) -> None:
    """The picture changes and you do not move.

    A teleport to the same coordinates on the next channel's map, which is
    only possible because the four maps are the same map — the player ends the
    transition standing on the tile they were walking across, facing the way
    they were walking, with a different town around them.
    """
    s.se("Tune", volume=72)
    s.flash(240, 236, 226, 22, 2, False)
    s.bgm_fadeout(4)
    s.var_from_event(VR_RING_X, 10001, 1)
    s.var_from_event(VR_RING_Y, 10001, 2)
    s.call_event(sys.CE_OVERLAY_OFF)
    s.fade_out(atmosphere.of("faces").leave)
    s.teleport_var(_MAP_IDS[target_key], VR_RING_X, VR_RING_Y)
    s.fade_in(atmosphere.of("faces").enter)


# Filled in by :func:`grove_events` before any script is built, because the
# maps have to know each other's numbers and they are only allocated once
# every world has been generated.
_MAP_IDS: dict[str, int] = {}


def _receiver(world) -> None:
    """The payphone that is already ringing when you get here.

    The only tutorial the grove has.  It does not say what the phone is for,
    what the handset does, or that anything has changed — it rings, you lift
    it, it goes on ringing in your hand, and from then on the town rings too.
    """
    jx, jy = world.landmarks["junctions"][0]
    take = Script()
    take.se("PhoneNear", volume=80)
    take.msg("the phone in the box is ringing.")
    take.msg("you lift the handset.", "", "it goes on ringing.")
    take.se("PhoneNear", volume=44, balance=70)
    take.switch(SW_FACE_HEARD, True)
    take.var(VR_CHANNEL, 0)
    kept = Script()
    kept.se("PhoneNear", volume=26)
    kept.msg("the handset is warm and it has not stopped.")
    # It says "the phone in the box is ringing", so there has to be a box.
    #
    # This is the one event the entire world hangs off -- nothing rings, no
    # channel ever changes and none of the four receptions are reachable until
    # it has been used -- and it was a bare sparkle lying on a carpet at the
    # first junction, with the nearest actual phone box twenty-seven tiles
    # away.  Easy to walk straight past, and once you had, the grove was a
    # town with a broken mechanic in it.
    from . import gen
    from .events import _place_object

    pages = [
        gleam(script=take, trigger=TRIGGER_ACTION),
        Page(script=kept, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             switch_a=SW_FACE_HEARD),
    ]
    # Five east and two south of the crossing, which put it squarely in the
    # carriageway: the junction's road band runs from two north to two south
    # of the centre line, so the +2 was inside it.  The box is nudged onto the
    # verge rather than being given a different fixed offset, because the one
    # thing this town has proved is that fixed offsets do not know what they
    # are standing on.
    from .worlds import off_tarmac, tarmac_ids
    grid = world.chipset.obj("phone_box")
    bx, by = (jx + 5) % world.map.width, (jy + 2) % world.map.height
    road = tarmac_ids(world.chipset)
    if road:
        spot = off_tarmac(world.map, road, bx, by, grid.cols, grid.rows,
                          radius=8)
        if spot is not None:
            bx, by = spot
    if gen.stamp(world.map, world.chipset.obj("phone_box"), bx, by, pad=1):
        _place_object(world, "phone_box", pages, at=(bx, by))
    else:
        world.map.add_event("the phone", bx, (by + 1) % world.map.height,
                            pages)


# --- what is in the yards -----------------------------------------------------

# Every yard's contents, written out rather than generated: five rooms is few
# enough to author, and the whole point of them is that they are specific.
YARD_LOCKED = {
    "nursery": ("the trunk is grown shut.",
                "there is a slot in the bark at chest height,",
                "with tape heads in it."),
    "substation": ("the inspection hatch is locked.",
                   "the keyway has something growing in it."),
    "studio": ("the door has a coin slot and no handle."),
    "compound": ("the gate is chained.",
                 "past it the ground goes dark very suddenly."),
}

YARD_OPENED = {
    "nursery": ("the tape runs.", "",
                "the growth pulls back off the trunk like a sleeve,",
                "and does not come back."),
    "substation": ("the seed turns in the keyway.", "",
                   "the hatch swings.  the column is hollow",
                   "and there is one bulb left in it, still cold."),
    "studio": ("the coin goes in.", "",
               "something behind the door counts it,",
               "and stops holding the door."),
    "compound": ("the bulb goes into the socket by the gate.", "",
                 "the filament takes a long time to come up.", "",
                 "the chain is not locked.  it never was."),
}

YARD_ITEM = {
    "coin": ("in the coin return: one coin.", "",
             "it is stamped with a circle, a crosshatch",
             "and eight bars."),
    "tape": ("a cassette, unlabelled, rewound to the start.",
             "", "the leader is spliced. twice."),
    "seed": ("a house key the tree has grown around.", "",
             "the wood has taken the shape of the teeth",
             "and kept it."),
    "bulb": ("one street lamp bulb.", "",
             "it is the only thing in this yard",
             "that has not gone grey."),
}

YARD_SOUND = {"coin": "Coin", "tape": "TapeRoll", "seed": "Rustle",
              "bulb": "Filament"}
YARD_OPEN_SOUND = {"nursery": "TapeRoll", "substation": "Latch",
                   "studio": "Coin", "compound": "Filament"}

# What is written on the ground of each yard, for anyone who gets in.  Lore,
# never explanation: four fragments of the same document, and no fourth wall.
YARD_LORE = {
    "exchange": ("the directory is still chained to the shelf.", "",
                 "every name in it has been scratched out",
                 "with the same pen, in one sitting."),
    "nursery": ("seed trays, in rows, all of them empty.", "",
                "the labels say: SAME AGAIN. SAME AGAIN.",
                "SAME AGAIN."),
    "substation": ("a wall chart of the supply.", "",
                   "every street is on it.",
                   "the mast is not."),
    "studio": ("a running order, pinned up, for a programme",
               "that is eleven hours long.", "",
               "every item on it is the same item."),
    "compound": ("a logbook, open, in the rain.", "",
                 "the last entry is a date and the word",
                 "STILL."),
}


def _yard(world, index: int, spec: dict, rng: random.Random) -> None:
    """One sealed yard: its lock, its contents and what is written in it."""
    m = world.map
    name = spec["name"]
    x, y = _standable(world, *world.landmarks["pockets"][index])

    if spec["needs"] is None:
        # the exchange asks for nothing.  It is the first thing you find and
        # the only one that is simply lying there.
        _pickup(world, spec["thing"], x, y)
    else:
        shut = Script()
        shut.se("Wrong", volume=30)
        shut.msg(*_lines(YARD_LOCKED[name]))

        open_it = Script()
        open_it.se(YARD_OPEN_SOUND[name], volume=72)
        open_it.msg(*_lines(YARD_OPENED[name]))
        open_it.flash(240, 236, 226, 16, 3, False)
        open_it.switch(spec["gives"], True)
        if spec["thing"]:
            open_it.se(YARD_SOUND[spec["thing"]], volume=64)
            open_it.msg(*_lines(YARD_ITEM[spec["thing"]]))

        done = Script()
        done.msg("it is open.")

        m.add_event(f"{name} lock", x, y, [
            gleam(script=shut, trigger=TRIGGER_ACTION),
            Page(script=open_it, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
                 switch_a=spec["needs"]),
            Page(script=done, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
                 switch_a=spec["needs"], switch_b=spec["gives"]),
        ])

    lore = Script()
    lore.msg(*_lines(YARD_LORE[name]))
    px, py = _standable(world, x + 3, y - 2)
    m.add_event(f"{name} paper", px, py,
                [gleam(script=lore, trigger=TRIGGER_ACTION)])


def _pickup(world, thing: str, x: int, y: int) -> None:
    """Something lying in a yard, and the empty shelf it leaves behind."""
    from ..state import SW_FACE_ITEM
    switch = SW_FACE_ITEM[thing]
    m = world.map
    x, y = _standable(world, x, y)
    got = Script()
    got.se(YARD_SOUND[thing], volume=70)
    got.msg(*_lines(YARD_ITEM[thing]))
    got.switch(switch, True)
    m.add_event(f"the {thing}", x, y, [
        gleam(script=got, trigger=TRIGGER_ACTION),
        Page(script=Script(), trigger=TRIGGER_ACTION, switch_a=switch),
    ])


def _lines(value) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def _standable(world, x: int, y: int) -> tuple[int, int]:
    """The nearest tile to ``(x, y)`` that is not solid and not already taken.

    Yards are cut into the green *before* the world is furnished, so the
    density pass is free to drop a tree in the middle of one.  A lock event
    standing inside that tree is still reachable — the engine looks at the
    tile in front of the player — but it is invisible, and something you have
    to walk the whole yard to find by accident is not a lock, it is a bug.
    """
    from .layout import solid_ids

    m = world.map
    solid = solid_ids(world.chipset)
    taken = {(e.x, e.y) for e in m.events}

    def free(px: int, py: int) -> bool:
        return (m.get_lower(px, py) not in solid
                and m.get_upper(px, py) not in solid
                and (px, py) not in taken)

    x, y = x % m.width, y % m.height
    if free(x, y):
        return x, y
    for step in range(1, 6):
        for dy in range(-step, step + 1):
            for dx in range(-step, step + 1):
                if max(abs(dx), abs(dy)) != step:
                    continue
                spot = ((x + dx) % m.width, (y + dy) % m.height)
                if free(*spot):
                    return spot
    return x, y


# --- the signs ----------------------------------------------------------------

# One at the mouth of every seam, on every channel.  They are the only thing
# in the grove that is trying to tell you something, and what they are telling
# you is where, not how — which is why they are the same five signs on all
# four channels and why four of the five are always wrong for wherever you
# happen to be standing.
SIGN_TEXT = (
    ("EXCHANGE", "the arrow points into the green.", "there is no gap."),
    ("NURSERY", "the arrow points into the green.", "there is no gap."),
    ("SUB-STATION", "the arrow points into the green.", "there is no gap."),
    ("STUDIOS", "the arrow points into the green.", "there is no gap."),
    ("NO ADMITTANCE", "the arrow points into the green.", "there is no gap."),
)
SIGN_OPEN = (
    ("EXCHANGE", "and there is a way through here."),
    ("NURSERY", "and there is a way through here."),
    ("SUB-STATION", "and there is a way through here."),
    ("STUDIOS", "and there is a way through here."),
    ("NO ADMITTANCE", "and there is a way through here."),
)


def _signs(world) -> None:
    channel = channel_of(world.key)
    m = world.map
    for index, spec in enumerate(YARDS):
        mouth = world.landmarks["mouths"][index]
        text = SIGN_OPEN[index] if spec["channel"] == channel \
            else SIGN_TEXT[index]
        s = Script()
        s.msg(*text)
        m.add_event(f"sign {index}", (mouth[0] + 1) % m.width,
                    mouth[1] % m.height,
                    [gleam(script=s, trigger=TRIGGER_ACTION)])


# --- who is here --------------------------------------------------------------

# Sixteen people, and all sixteen live on all four channels.
#
# The town is one town.  If tuning changed who was in it, the receiver would
# be a teleport rather than a tuner, and the whole conceit would collapse into
# four maps that happen to share a street plan.  So the roster is fixed and
# what moves is *how everyone is*:
#
#     the grove     as they are
#     overgrown     happier, and a bit too happy — nothing here is worried
#     off-colour    sad, tired, and much more honest for it
#     no signal     angry, corrupted, and talking to you rather than at you
#
# Which is also how you find things out.  A person who will not tell you
# something on one channel says it on another because they are not being
# careful any more, and the red channel says it because it wants to hurt.
PEOPLE: dict[str, dict[str, tuple[str, ...]]] = {
    "gardener": {
        "faces": ("i keep the verge.", "", "the verge is now most of it."),
        "faces2": ("everything took!", "", "everything i put in took.", "",
                   "i have never had a year like it."),
        "faces3": ("nothing needs me now.", "",
                   "i come out anyway. it's a habit with a shape."),
        "faces4": ("I WATERED IT AND IT DIED ANYWAY.", "",
                   "DO YOU WANT TO KNOW WHAT ELSE I DID."),
    },
    "seedling": {
        "faces": ("i was planted at the wrong scale.",),
        "faces2": ("look at me!", "", "look at me. LOOK—", "",
                   "sorry. sorry."),
        "faces3": ("i stopped.", "", "not died. stopped."),
        "faces4": ("PUT ME BACK.",),
    },
    "commuter": {
        "faces": ("the 7 is due.", "", "it has been due."),
        "faces2": ("i walked instead!", "",
                   "it took nine hours and it was lovely."),
        "faces3": ("i've stopped checking the timetable.", "",
                   "i still stand here. i don't know what that is."),
        "faces4": ("IT CAME.", "", "IT CAME AND IT DIDN'T STOP."),
    },
    "leaf_head": {
        "faces": ("something is coming up.", "", "i am not going to look."),
        "faces2": ("IT FLOWERED.", "", "sorry. i can't tell how loud i am."),
        "faces3": ("it's bare now.", "", "i miss the weight of it."),
        "faces4": ("IT'S STILL GROWING.", "", "IT'S GROWING INWARDS."),
    },
    "ranger": {
        "faces": ("management plan's still current.",),
        "faces2": ("allow to develop!", "", "and it did! look at it!"),
        "faces3": ("there's nothing left to manage.", "",
                   "i log that. every day. nothing left to manage."),
        "faces4": ("I SIGNED IT OFF.", "", "ALL OF THIS. I SIGNED IT OFF."),
    },
    "grafter": {
        "faces": ("i joined a few things up.", "", "they took better than i did."),
        "faces2": ("that lamp post has buds on it!", "", "i did that. me."),
        "faces3": ("wood wants to join.", "",
                   "that's all a graft is. two things held together.", "",
                   "nobody held me anywhere."),
        "faces4": ("I NUMBERED THEM.", "", "14. 16. 18.", "",
                   "GO AND COUNT. GO ON."),
    },
    "swarm": {
        "faces": ("we are all of us here.", "", "we were fewer."),
        "faces2": ("we are MANY now!", "", "we agreed to be pleased about it."),
        "faces3": ("we are fewer again.", "",
                   "we do not talk about which ones."),
        "faces4": ("DO NOT COUNT US.", "",
                   "THE NUMBER CHANGES WHEN YOU DO."),
    },
    "bough_sleeper": {
        "faces": ("...the 7 is due...",),
        "faces2": ("...i can hear all four of them from up here...", "",
                   "...it's lovely..."),
        "faces3": ("...leave it on...", "", "...i sleep better with it on..."),
        "faces4": ("I AM NOT ASLEEP.", "", "I HAVE NEVER BEEN ASLEEP."),
    },
    "staffholder": {
        "faces": ("i'm sighting the new road.", "", "it goes through all of this."),
        "faces2": ("the new road's beautiful!", "",
                   "you can't see it yet. that's fine."),
        "faces3": ("we're waiting on a colour.", "",
                   "we've been waiting on a colour for a long time."),
        "faces4": ("HOLD THIS. DON'T MOVE.", "",
                   "I SAID DON'T MOVE."),
    },
    "meter_reader": {
        "faces": ("supply's still on.", "",
                  "nobody's drawing on it but the mast."),
        "faces2": ("readings are up!", "", "everything's up!"),
        "faces3": ("house four's been empty since before the trees.", "",
                   "it used four units last month.", "",
                   "i write it down. somebody has to have the numbers."),
        "faces4": ("ESTIMATED READINGS ARE A FORM OF LYING.", "",
                   "I WANT THAT UNDERSTOOD."),
    },
    "ash_walker": {
        "faces": ("it comes down at the same rate", "whatever the weather is."),
        "faces2": ("it's not falling today!", "", "isn't that lovely."),
        "faces3": ("i've stopped brushing it off.", "", "you will too."),
        "faces4": ("IT ISN'T ASH.", "", "YOU KNOW IT ISN'T ASH."),
    },
    "last_engineer": {
        "faces": ("it's transmitting.", "", "i checked. i keep checking."),
        "faces2": ("four carriers off one mast!", "",
                   "she's never run better. never."),
        "faces3": ("that's not how many we built it for.", "",
                   "if you hear a phone, walk towards it.", "",
                   "that's the last thing i'll say about it."),
        "faces4": ("SOMETHING ANSWERS ON THE FOURTH ONE.", "",
                   "YOU'RE STANDING IN IT."),
    },
    "presenter": {
        "faces": ("good evening.", "", "tonight, as every night—"),
        "faces2": ("AND WHAT A LOVELY EVENING IT IS.",),
        "faces3": ("we'll be back after this.", "", "we won't."),
        "faces4": ("PLEASE DO NOT ADJUST YOUR SET.", "",
                   "THERE IS NOTHING WRONG WITH YOUR SET.", "",
                   "THERE IS NOTHING WRONG."),
    },
    "caption": {
        "faces": ("[ SPEAKER UNIDENTIFIED ]",),
        "faces2": ("[ LAUGHTER ]", "", "[ LAUGHTER CONTINUES ]"),
        "faces3": ("[ SILENCE ]", "", "[ SILENCE CONTINUES ]"),
        "faces4": ("[ SPEAKER IS YOU ]",),
    },
    "test_tone": {
        "faces": ("————————————————",),
        "faces2": ("——————♪——————", "", "( it is trying )"),
        "faces3": ("——————", "", "( it stops. it starts again. )"),
        "faces4": ("————————————————————————", "",
                   "( it does not stop while you read this )"),
    },
    "continuity": {
        "faces": ("normal service will be resumed.",),
        "faces2": ("NORMAL SERVICE!", "", "ISN'T IT MARVELLOUS."),
        "faces3": ("normal service will not be resumed.", "",
                   "we are sorry. we are actually sorry."),
        "faces4": ("YOU ARE WATCHING.", "", "THAT IS THE PROGRAMME.", "",
                   "THE OTHER THREE ARE NOT AWARE OF THIS ONE."),
    },
}

# Where each of them stands.  Junctions are where the town still works and
# glades are where it has stopped, and which of the two somebody is found in
# says as much about them as anything they say.
STANDS = {
    "gardener": "glades", "seedling": "junctions", "commuter": "junctions",
    "leaf_head": "glades", "ranger": "junctions", "grafter": "glades",
    "swarm": "glades", "bough_sleeper": "junctions",
    "staffholder": "junctions", "meter_reader": "junctions",
    "ash_walker": "glades", "last_engineer": "glades",
    "presenter": "junctions", "caption": "junctions",
    "test_tone": "glades", "continuity": "glades",
}

# What each channel's designs are called on its own charset.
SUFFIX = {"faces": "", "faces2": "_g", "faces3": "_y", "faces4": "_r"}


# --- what each reception sounds like when nothing is happening -----------------
# Music says what kind of place this is; ambience says whether anything is in
# it with you.  One parallel process per channel, playing one sound at long
# and uneven intervals, panned somewhere you are not looking.
#
# The gaps matter more than the sounds.  A noise every four seconds is a
# soundtrack and stops being heard; a noise somewhere between eight and thirty
# seconds cannot be predicted, so the player keeps listening for it, and on
# the dead channel that is the whole effect.
AMBIENCE: dict[str, tuple[tuple[str, int, int], ...]] = {
    # birds, leaves, and a car radio a long way off
    "faces": (("Rustle", 26, 100), ("WindGust", 20, 100), ("Carrier", 14, 40)),
    # too many birds, too pleased, too often — the channel performing health
    "faces2": (("Rustle", 34, 100), ("ChimeFar", 22, 100),
               ("Rustle", 30, 100), ("WaterDrop", 18, 100)),
    # a fluorescent tube, wind through something empty, and long nothing
    "faces3": (("Filament", 18, 100), ("WindGust", 24, 100),
               ("TapeRoll", 14, 100)),
    # something large, below, that is not in a hurry.  The heartbeat is the
    # only sound in the game that is centred rather than panned: it is not
    # coming from anywhere in the town.
    "faces4": (("LowThud", 34, 50), ("Heartbeat", 26, 50),
               ("StaticBurst", 30, 100), ("LowThud", 22, 50),
               ("Buzzer", 20, 100)),
}

# How long between them, in tenths of a second: from, to.
AMBIENCE_GAP = {"faces": (90, 260), "faces2": (70, 200),
                "faces3": (140, 340), "faces4": (80, 300)}


def _ambience(world) -> Page:
    """One sound, at an interval nobody can learn, from somewhere off-screen."""
    sounds = AMBIENCE[world.key]
    low, high = AMBIENCE_GAP[world.key]

    s = Script()
    s.comment("what this reception sounds like when nothing is happening")
    with s.loop():
        s.var_random(VR_AMBIENCE, low, high)
        with s.loop():
            s.wait(1)
            s.var(VR_AMBIENCE, 1, 2)
            with s.if_var(VR_AMBIENCE, 0, 2):
                s.break_loop()
        s.var_random(VR_AMBIENCE, 0, len(sounds) - 1)
        for index, (name, volume, spread) in enumerate(sounds):
            with s.if_var(VR_AMBIENCE, index):
                # panned hard when it belongs to the town and centred when it
                # does not belong to anything
                s.se(name, volume=volume,
                     balance=50 + spread // 2 if index % 2 else 50 - spread // 2,
                     tempo=100 - spread // 8)
    return Page(script=s, trigger=TRIGGER_PARALLEL, layer=LAYER_BELOW)


def _residents(world, rng: random.Random) -> None:
    """All sixteen, once each, wherever this channel keeps them.

    One copy per design rather than five, because there are four times as many
    designs as there used to be: sixteen people standing about is a town, and
    sixteen designs at five copies each would be eighty events on a map that
    also has to hold a road network.
    """
    m = world.map
    suffix = SUFFIX[world.key]
    for index, (design, registers) in enumerate(PEOPLE.items()):
        sheet, slot = charset_slot(f"{design}{suffix}")
        spots = list(world.landmarks.get(STANDS[design], []))
        if not spots:
            continue
        ax, ay = spots[index % len(spots)]
        ax = (ax + rng.randint(-6, 6)) % m.width
        ay = (ay + rng.randint(-5, 5)) % m.height
        s = Script()
        s.move_route(0, [MV_FACE_HERO], frequency=8)
        s.msg(*registers[world.key])
        m.add_event(design, ax, ay, [
            Page(script=s, charset=sheet, charset_index=slot,
                 move_type=MOVE_STATIONARY if index % 3 == 0 else MOVE_RANDOM,
                 move_speed=2, move_frequency=3, trigger=TRIGGER_ACTION,
                 animation_type=ANIM_CONTINUOUS)])


# --- what is only here --------------------------------------------------------

# One thing per channel that nothing needs, nothing points at, and nothing
# will ever mention again.  They exist so that a player who tunes for no
# reason is rewarded for it.
EASTER: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "faces": ("glades", "Carrier",
              ("the dead car's radio is on.", "",
               "it is carrying a tone and nothing else.", "",
               "the battery has been flat for years.")),
    "faces2": ("glades", "Rustle",
               ("the graft marks on this trunk are numbers.", "",
                "14. 16. 18.", "",
                "they go up as you walk away from the road.")),
    "faces3": ("glades", "Watch",
               ("nine dishes, on one frame, all aimed the same way.", "",
                "you follow the line they are pointing along.", "",
                "it does not arrive at the mast.",
                "it goes a little to the left of it.")),
    "faces4": ("junctions", "StaticBurst",
               ("you stand in the black square.", "",
                "for as long as you are in it,",
                "the town is not carrying any sound at all.")),
}


def _easter(world, rng: random.Random) -> None:
    where, sound, lines = EASTER[world.key]
    spots = world.landmarks.get(where, [])
    if not spots:
        return
    x, y = spots[len(spots) // 2]
    m = world.map
    s = Script()
    s.se(sound, volume=52)
    s.msg(*lines)
    m.add_event("only here", (x - 4) % m.width, (y + 3) % m.height,
                [gleam(script=s, trigger=TRIGGER_ACTION)])


# --- the mast -----------------------------------------------------------------

MAST_LINES = (
    ("the mast is guyed to four points and its light is on.", "",
     "there is a plate at the foot of it."),
    ("the plate reads:", "",
     "RECEIVING STATION"),
    ("not transmitting.", "", "receiving."),
    ("you look back down the hill at the town.", "",
     "every window that is lit is lit the same amount."),
)


def _mast(world) -> None:
    """The end of the loop, and the one thing the grove does say outright.

    It says it in four lines, on a plate, and then it stops.  Everything else
    the player has to have worked out by having walked it: that the four
    channels are one place, that the place is not being broadcast, and what a
    town full of receivers is receiving.
    """
    m = world.map
    x, y = _standable(world, *world.landmarks["pockets"][4])
    s = Script()
    s.se("Carrier", volume=60)
    for lines in MAST_LINES:
        s.msg(*lines)
    s.switch(SW_FACE_ENDED, True)
    s.se("Tune", volume=40)
    mx, my = _standable(world, x, y - 3)
    m.add_event("the mast", mx, my, [
        Page(script=Script(), trigger=TRIGGER_ACTION),
        Page(script=s, trigger=TRIGGER_ACTION, layer=LAYER_SAME,
             switch_a=SW_FACE_MAST),
    ])


# --- assembly -----------------------------------------------------------------

def channel_layer_events(world, worlds: dict, rng: random.Random) -> None:
    """Arrival, and the door out, for the three channels that are not dreams.

    The door is at the same tile on all four, because it is the same door:
    whatever the town is being received as, that is still the way home, and a
    player who tunes by accident on their way out must not find the exit has
    moved.
    """
    from .events import _arrival_event
    from .worlds import NEXUS_ORDER

    world.map.add_event("arrive", 0, 0, [_arrival_event(world)])

    nexus = worlds["nexus"]
    nx, ny = nexus.landmarks["doors"][NEXUS_ORDER.index("faces")]
    bx, by = worlds["faces"].landmarks["door_face"][0]
    back = Script()
    back.se("DoorShut", volume=60)
    back.bgm_fadeout(10)
    back.weather(0, 0)
    back.pan_reset(speed=6, wait=False)
    back.fade_out(atmosphere.of("faces").leave)
    back.call_event(sys.CE_OVERLAY_OFF)
    back.teleport(nexus.map_id, nx + 1, ny + 3)
    back.fade_in(atmosphere.of("nexus").enter)
    world.map.add_event("door", bx % world.map.width, by % world.map.height,
                        [gleam(script=back, trigger=TRIGGER_ACTION)])


def grove_events(world, worlds: dict, rng: random.Random) -> None:
    """Everything one channel of the grove gets beyond the standard furniture.

    Called for all four, including the grove itself, which also goes through
    the ordinary dream authoring — it is a dream, it has the nexus door and
    the effect that lives in it.  The other three are layers: same chipset
    family, same cast family, same music family, no door of their own.
    """
    _MAP_IDS.update({key: worlds[key].map_id for key in CHANNELS})
    if os.environ.get("GROVE_DEBUG_RECEIVER"):
        # A build switch, for the engine test that has to prove the ring works
        # without also proving that a scripted walk can find a phone box.
        hand = Script()
        hand.switch(SW_FACE_HEARD, True)
        hand.erase_event()
        world.map.add_event("debug receiver", 2, 2, [
            Page(script=hand, trigger=TRIGGER_AUTO, layer=LAYER_BELOW)])

    channel = channel_of(world.key)
    world.map.add_event("ringer", 1, 1, [_ringer(world)])
    _signs(world)
    _residents(world, rng)
    world.map.add_event("ambience", 2, 1, [_ambience(world)])
    _easter(world, rng)
    if channel == 0:
        _receiver(world)
        _mast(world)
    for index, spec in enumerate(YARDS):
        if spec["channel"] == channel:
            _yard(world, index, spec, rng)
