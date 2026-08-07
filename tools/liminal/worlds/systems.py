"""The common events: the machinery every world runs on.

Four systems live here.

**Arrival** grades the screen and starts the music whenever you enter a world.
Every dream has its own tint and its own overlay picture, applied through the
same code path, so the colour of the light is the first thing that tells you
where you are.

**The loop watch** is what makes a looping world mean something.  It samples
the player's position every frame; when a coordinate jumps by more than half
the map, the player has crossed the seam, and the distance walked is added to
a running total that never resets.  Events elsewhere read that total, so a
world can quietly change the more of it you have walked.

**The diary** is a custom menu built entirely from pictures, because the
engine's own menu cannot be animated.  It assembles itself in layers and comes
apart the same way.

**The roll** gives rare things a chance to happen without ever announcing that
a die was thrown.
"""

from __future__ import annotations

from ..art import ui
from ..art.menu import EFFECTS, icon_position
from . import atmosphere, mechanics
from ..cmds import (MSG_BOTTOM, MSG_MIDDLE, MSG_TOP, MV_SPEED_UP, PLAYER,
                    Script)
from ..db import TRIGGER_CALL, TRIGGER_PARALLEL, CommonEvent
from ..state import (SW_DEEP_UNLOCKED, SW_EFFECT_ACTIVE, SW_EYE_ACTIVE,
                     SW_FOLLOWER, SW_HAS_EFFECT, SW_MENU_BUSY, SW_MENU_OPEN,
                     SW_OVERLAY_ON, SW_QUIET_ACTIVE, SW_TITLE_CHANGED,
                     SW_WOKE_ONCE, SW_WORLD_STATE_BASE, VR_DREAM_DISTANCE, VR_EFFECTS_FOUND,
                     VR_EQUIPPED, VR_LAST_X, VR_LAST_Y, VR_LOOPS,
                     VR_MENU_CURSOR, VR_PREV_WORLD, VR_ROLL, VR_SCRATCH,
                     VR_KEY, VR_REG_BASE, REG_MAX, VR_STEPS, VR_STILL,
                     VR_TEMP_X, VR_TEMP_Y,
                     VR_FILM, VR_FILM_FRAME, VR_FILM_SPEED, VR_FILM_TICK,
                     VR_VISITS_BASE, VR_WORLD)

# Common event numbers.  Referenced by name everywhere else.
CE_BOOT = 1
CE_ARRIVE = 2
CE_LOOP_WATCH = 3
CE_DIARY = 4
CE_EQUIP = 5
CE_UNEQUIP = 6
CE_ROLL = 7
CE_GIVE_EFFECT = 8
CE_OVERLAY_ON = 9
CE_OVERLAY_OFF = 10
CE_WAKE = 11
CE_DIARY_KEY = 12
CE_ATMOSPHERE = 13
# Ids must run without gaps: the engine walks the common event list by
# position, and a missing number is a null it will happily dereference.
CE_KEYBOARD = 14          # drains Ineluki's key queue; see keys.py
CE_WHEREAMI = 15
CE_FILM = 16              # turns animated overlays over; see art/ui.py

# Picture layers.  Higher numbers draw in front.
PIC_OVERLAY = 5           # the world's own film: grain, haze, scanlines
# The diary, back to front.  Ids *are* the draw order, so the garnishes that
# turn behind the page have to be numbered below it.
PIC_VEIL = 6
PIC_HALO = 7              # rotates one way, forever
PIC_RINGS = 8             # rotates the other way, faster
PIC_PANEL = 11
PIC_FRAME = 12
PIC_TITLE = 13
PIC_ICON_BASE = 14        # 14..25, one per effect slot
PIC_BLOOM = 26            # the light under whatever is selected
PIC_GHOST = 27
PIC_CURSOR = 28
PIC_GLINT = 29
PIC_DUST = 30
PIC_MOTES = 31            # waves, forever
PIC_FLASH = 40            # for anomalies: static, eye, white
PIC_SHUDDER = 41          # the grove's ring, on the edge it came from

EFFECT_KEYS = [key for key, _, _ in EFFECTS]


# --- boot --------------------------------------------------------------------

def boot() -> CommonEvent:
    """Runs once at the very start, then never again.

    Called by the first arrival event to run on a new game, which recognises
    itself by ``VR_WORLD`` still being zero — no map has an index of zero, so
    that value can only mean nothing has happened yet.
    """
    s = Script()
    s.comment("first frame of a new game")
    s.var(VR_EQUIPPED, 0)
    s.var(VR_DREAM_DISTANCE, 0)
    s.var(VR_EFFECTS_FOUND, 0)
    s.var(VR_WORLD, 1)
    s.switch(SW_WOKE_ONCE, False)
    # The number world starts with everything present and nothing turned
    # down; every register is at its own maximum, which is the state a world
    # is in before anybody has counted it.
    for reg, top in enumerate(REG_MAX):
        s.var(VR_REG_BASE + reg, top)
    s.tint(100, 100, 100, 100, 0, False)
    # The pace of the whole game, set once and deliberately.  RPG Maker's
    # default is 4, one tile roughly every four frames; the worlds here are a
    # hundred and forty tiles across and meant to be walked rather than
    # crossed, so this is a decision and not an inherited default.
    return CommonEvent(CE_BOOT, "boot", TRIGGER_CALL, None, s)


# --- the film ----------------------------------------------------------------
#
# RPG Maker 2000 cannot animate a picture.  It can wave one and it can rotate
# one, and for a vignette or a light shaft that is the right amount of motion,
# but grain that waves is still the same grain -- the pattern never changes,
# so it reads as a dirty screen rather than as film.  The only way to actually
# animate an overlay is to re-show the same picture id with the next frame's
# file, which is what the film watcher does.
#
# A world's film is identified by the pair (picture, opacity) rather than by
# the world, because a dozen worlds wear grain at the same strength and there
# is no reason to write that dozen times.  Arrival stores the pair's index in
# VR_FILM; the watcher turns the index and the frame number back into a
# filename.


def _moves(world) -> bool:
    """Is this world's overlay one of the ones that animates?"""
    return world.overlay in ui.ANIMATED


def films(worlds) -> dict[tuple[str, int], int]:
    """Every distinct (picture, opacity) an animated overlay is worn at.

    Numbered from one, because zero in VR_FILM means "this world's overlay
    does not move" and the watcher leaves it alone.
    """
    from .worlds import WORLD_ORDER

    found: dict[tuple[str, int], int] = {}
    for key in WORLD_ORDER:
        world = worlds[key]
        if _moves(world):
            found.setdefault((world.overlay, world.overlay_opacity),
                             len(found) + 1)
    # The overlay a permanently-changed world wears, which arrival shows from
    # inside its own branch and at its own strength.
    found.setdefault(("StaticB", 58), len(found) + 1)
    return found


def _first_frame(known: dict[tuple[str, int], int], world) -> str:
    return f"{world.overlay}1" if _moves(world) else world.overlay


def _arm_film(s: Script, known: dict[tuple[str, int], int], world) -> None:
    """Tell the watcher what this world's overlay is, or that it is still."""
    if not _moves(world):
        s.var(VR_FILM_SPEED, 0)
        return
    s.var(VR_FILM, known[(world.overlay, world.overlay_opacity)])
    s.var(VR_FILM_SPEED, ui.ANIMATED[world.overlay])
    s.var(VR_FILM_TICK, 0)
    s.var(VR_FILM_FRAME, 0)


def film(worlds) -> CommonEvent:
    """Turn the overlay over, a frame at a time.

    Runs every frame, and on most of them does almost nothing: it adds one to
    a counter and compares it to how long this world holds a frame for.  Only
    when the counter comes round does it walk the table and re-show the
    picture.  Grain turns over about ten times a second, static thirty, dust
    five; the numbers live in ``ui.ANIMATED`` beside the art they describe.

    Opacity is baked into each branch because Show Picture takes a literal
    and not a variable -- which is also why the table is keyed by the pair
    rather than by the picture alone.
    """
    known = films(worlds)

    s = Script()
    s.comment("turn the film over")
    with s.if_switch(SW_OVERLAY_ON):
        with s.if_var(VR_FILM_SPEED, 0, 3):        # > 0: this world's film moves
            s.var(VR_FILM_TICK, 1, op=1)
            with s.if_var_var(VR_FILM_TICK, VR_FILM_SPEED, 1):   # >=
                s.var(VR_FILM_TICK, 0)
                s.var(VR_FILM_FRAME, 1, op=1)
                with s.if_var(VR_FILM_FRAME, ui.FILM_FRAMES, 1):
                    s.var(VR_FILM_FRAME, 0)
                for (picture, opacity), kind in known.items():
                    with s.if_var(VR_FILM, kind):
                        for frame in range(ui.FILM_FRAMES):
                            with s.if_var(VR_FILM_FRAME, frame):
                                s.show_picture(PIC_OVERLAY,
                                               f"{picture}{frame + 1}",
                                               160, 120,
                                               transparency=opacity,
                                               use_transparent_color=True)
    return CommonEvent(CE_FILM, "film", TRIGGER_PARALLEL, None, s)


# --- arrival -----------------------------------------------------------------

def arrival(worlds) -> CommonEvent:
    """Grade the screen and start the music for whichever world we are in.

    Called by each map's own arrival event after it has set ``VR_WORLD``.
    One code path for every world keeps the transitions consistent, and means
    a world's identity is data rather than duplicated script.
    """
    from .worlds import WORLD_ORDER

    known = films(worlds)

    s = Script()
    # The stock menu was switched off for a while, back when cancel was one of
    # only three keys this game had and saving had to be bolted onto it.  With
    # a real keyboard there is nothing to gain by keeping it off, and plenty to
    # lose: it is where the items are, and turning it off left the player
    # unable to open their own inventory.  Re-enabled here rather than in
    # ``boot`` because ``boot`` runs once on a new game, and a save made while
    # the menu was off would otherwise keep it off forever.
    s.allow_menu(True)
    s.comment("apply this world's colour grade, film and music")
    for index, key in enumerate(WORLD_ORDER, start=1):
        world = worlds[key]
        with s.if_var(VR_WORLD, index):
            r, g, b, sat = world.tint
            s.tint(r, g, b, sat, 8, False)
            s.bgm(world.music, fadein=25, volume=82)
            air = atmosphere.of(key)
            if world.overlay:
                # The film each world wears.  A still overlay gets the
                # engine's own wave or rotation and then looks after itself;
                # one that moves is handed to the film watcher instead, which
                # cycles it frame by frame.  The two cannot be combined --
                # re-showing a picture restarts its wave, so a waving grain
                # would jitter in place rather than wave.
                _arm_film(s, known, world)
                s.show_picture(PIC_OVERLAY, _first_frame(known, world),
                               160, 120,
                               transparency=world.overlay_opacity,
                               use_transparent_color=True,
                               effect=0 if _moves(world) else air.film,
                               power=0 if _moves(world) else air.film_power)
                s.call_event(CE_OVERLAY_ON)
            # Weather, camera tremor and camera drift, in that order: the
            # first two are set and forgotten, the third has to be re-armed
            # every time the screen is re-graded.
            s.weather(*(air.weather or (0, 0)))
            if air.drift:
                s.pan(*air.drift, wait=False)
            # A world its own mechanic has permanently changed is graded,
            # scored and filmed differently from then on, on every visit for
            # the rest of the save.  Nothing announces it; it is simply how
            # the place is now.
            with s.if_switch(SW_WORLD_STATE_BASE + index - 1):
                s.tint(58, 62, 60, 24, 10, False)
                s.bgm("Wrong", fadein=20, volume=80)
                # A world that has gone wrong wears live static, not a
                # photograph of static.
                s.var(VR_FILM, known[("StaticB", 58)])
                s.var(VR_FILM_SPEED, ui.ANIMATED["StaticB"])
                s.var(VR_FILM_TICK, 0)
                s.var(VR_FILM_FRAME, 0)
                s.show_picture(PIC_OVERLAY, "StaticB1", 160, 120,
                               transparency=58, use_transparent_color=True)
            s.var(VR_VISITS_BASE + index - 1, 1, op=1)
    # entering anywhere resets the sense of having gone in a circle
    s.var(VR_LOOPS, 0)
    s.var_from_event(VR_LAST_X, PLAYER, 1)
    s.var_from_event(VR_LAST_Y, PLAYER, 2)
    return CommonEvent(CE_ARRIVE, "arrive", TRIGGER_CALL, None, s)


# --- the loop watch ----------------------------------------------------------

def loop_watch() -> CommonEvent:
    """Detect wrapping and accumulate distance walked.

    A jump of more than forty tiles in one frame is impossible on foot, so it
    can only mean the player crossed an edge and came out the other side.
    """
    s = Script()
    s.comment("count how far this dream has been walked")
    s.var_from_event(VR_TEMP_X, PLAYER, 1)
    s.var_from_event(VR_TEMP_Y, PLAYER, 2)

    # horizontal seam
    s.var_from_var(VR_SCRATCH, VR_TEMP_X)
    s.var_from_var(VR_SCRATCH, VR_LAST_X, op=2)
    with s.if_var(VR_SCRATCH, 40, 1):          # jumped a long way right
        s.var(VR_LOOPS, 1, op=1)
        s.var(VR_DREAM_DISTANCE, 1, op=1)
    with s.if_var(VR_SCRATCH, -40, 2):         # jumped a long way left
        s.var(VR_LOOPS, 1, op=1)
        s.var(VR_DREAM_DISTANCE, 1, op=1)

    # vertical seam
    s.var_from_var(VR_SCRATCH, VR_TEMP_Y)
    s.var_from_var(VR_SCRATCH, VR_LAST_Y, op=2)
    with s.if_var(VR_SCRATCH, 40, 1):
        s.var(VR_LOOPS, 1, op=1)
        s.var(VR_DREAM_DISTANCE, 1, op=1)
    with s.if_var(VR_SCRATCH, -40, 2):
        s.var(VR_LOOPS, 1, op=1)
        s.var(VR_DREAM_DISTANCE, 1, op=1)

    s.var_from_var(VR_LAST_X, VR_TEMP_X)
    s.var_from_var(VR_LAST_Y, VR_TEMP_Y)
    s.var(VR_STEPS, 1, op=1)
    s.wait(1)
    return CommonEvent(CE_LOOP_WATCH, "loop watch", TRIGGER_PARALLEL, None, s)


# --- rare events -------------------------------------------------------------

def roll() -> CommonEvent:
    """Throw a die every few seconds and, very occasionally, let it land.

    The odds are deliberately steep.  Most of these should be things a player
    describes to somebody else and is not believed about.
    """
    s = Script()
    s.wait(90)
    s.var_random(VR_ROLL, 1, 1000)

    # ~1 in 500: the light changes for a moment and goes back
    with s.if_var(VR_ROLL, 2, 2):
        s.tint(70, 70, 88, 60, 25, True)
        s.wait(20)
        s.call_event(CE_ARRIVE)

    # ~1 in 250: something is heard that has no source
    with s.if_var(VR_ROLL, 6, 0):
        s.se("ChimeFar", volume=45)

    # ~1 in 1000, and only once you have walked a long way: you are followed
    with s.if_var(VR_ROLL, 1, 0):
        with s.if_var(VR_DREAM_DISTANCE, 6, 1):
            s.switch(SW_FOLLOWER, True)

    # ~1 in 500: the title screen is quietly different from now on
    with s.if_var(VR_ROLL, 999, 1):
        s.switch(SW_TITLE_CHANGED, True)

    # ~1 in 200: a single breath, very close
    with s.if_var(VR_ROLL, 12, 0):
        s.se("Breath", volume=35)
    return CommonEvent(CE_ROLL, "roll", TRIGGER_PARALLEL, None, s)


# --- the diary ---------------------------------------------------------------

def _icon_pic(slot: int) -> int:
    return PIC_ICON_BASE + slot


def diary_open() -> Script:
    """Build the menu in layers, back to front, each with its own motion."""
    s = Script()
    s.switch(SW_MENU_BUSY, True)
    s.se("MenuOpen", volume=70)
    s.halt_movement()

    # 1. the world dims and pushes back
    s.show_picture(PIC_VEIL, "MenuVeil", 160, 120, transparency=100,
                   use_transparent_color=False)
    s.move_picture(PIC_VEIL, 160, 120, transparency=45, tenths=2)

    # 2. the garnishes.  ``effect=1`` is the engine's continuous rotation and
    # ``effect=2`` its wave, and both are driven by the engine's own clock
    # rather than the interpreter's — so these keep turning through the
    # blocking key-wait below.  Everything else in this menu is a one-shot
    # animation; these are the parts that never stop.
    s.show_picture(PIC_HALO, "MenuHalo", 160, 120, magnify=30,
                   transparency=100, effect=1, power=3)
    s.move_picture(PIC_HALO, 160, 120, magnify=104, transparency=62, tenths=4,
                   effect=1, power=3)
    s.show_picture(PIC_RINGS, "MenuRings", 160, 120, magnify=140,
                   transparency=100, effect=1, power=-5)
    s.move_picture(PIC_RINGS, 160, 120, magnify=100, transparency=72, tenths=4,
                   effect=1, power=-5)

    # 3. the page arrives small and overshoots before settling
    s.show_picture(PIC_PANEL, "MenuPanel", 160, 128, magnify=20,
                   transparency=100)
    s.move_picture(PIC_PANEL, 160, 118, magnify=108, transparency=0, tenths=2,
                   wait=True)
    s.move_picture(PIC_PANEL, 160, 120, magnify=100, tenths=1, wait=True)

    # 4. the border drops in behind it and lands hard — this is the one crisp
    # edge in the menu, so it gets the one abrupt movement
    s.show_picture(PIC_FRAME, "MenuFrame", 160, 88, magnify=112,
                   transparency=100)
    s.move_picture(PIC_FRAME, 160, 126, magnify=100, transparency=0, tenths=2,
                   wait=True)
    s.move_picture(PIC_FRAME, 160, 120, tenths=1, wait=True)
    s.se("LowThud", volume=40)

    # 5. a light travels across the border, once
    s.show_picture(PIC_GLINT, "MenuGlint", 30, 120, transparency=40)
    s.move_picture(PIC_GLINT, 292, 120, transparency=100, tenths=6)

    s.show_picture(PIC_TITLE, "MenuTitle", 160, 52, transparency=100)
    s.move_picture(PIC_TITLE, 160, 48, transparency=0, tenths=1)

    # 5. the effects pop in one at a time, found ones solid, the rest ghosted
    for slot, key in enumerate(EFFECT_KEYS):
        x, y = icon_position(slot)
        pic = _icon_pic(slot)
        with s.if_else_switch(SW_HAS_EFFECT[key]) as arm:
            with arm(False):
                s.show_picture(pic, f"Icon{slot + 1:02d}", x, y - 4, magnify=60,
                               transparency=100)
                s.move_picture(pic, x, y, magnify=112, transparency=0, tenths=1,
                               wait=True)
                s.move_picture(pic, x, y, magnify=100, tenths=1)
            with arm(True):
                s.show_picture(pic, "IconBlank", x, y, magnify=100,
                               transparency=55)
        if slot % 4 == 3:
            s.se("Cursor", volume=28)

    # 7. the light under the selection, then dust, then the cursor last of all.
    # The bloom and the motes are the other two things that never stop: the
    # bloom breathes on the engine's rotation, the motes swim on its wave.
    s.show_picture(PIC_BLOOM, "MenuBloom", *icon_position(0), magnify=60,
                   transparency=100, effect=1, power=2)
    s.move_picture(PIC_BLOOM, *icon_position(0), magnify=100, transparency=40,
                   tenths=2, effect=1, power=2)
    s.show_picture(PIC_DUST, "MenuDust", 160, 120, transparency=72)
    s.show_picture(PIC_MOTES, "MenuMotes", 160, 120, transparency=100,
                   effect=2, power=6)
    s.move_picture(PIC_MOTES, 160, 120, transparency=62, tenths=3,
                   effect=2, power=6)
    s.show_picture(PIC_GHOST, "MenuGhost", *icon_position(0), transparency=100)
    s.show_picture(PIC_CURSOR, "MenuCursor", *icon_position(0), magnify=150,
                   transparency=60, effect=1, power=1)
    s.move_picture(PIC_CURSOR, *icon_position(0), magnify=100, transparency=0,
                   tenths=1, effect=1, power=1)
    s.switch(SW_MENU_BUSY, False)
    return s


def diary_close() -> Script:
    """Take it apart in the reverse order, and faster."""
    s = Script()
    s.switch(SW_MENU_BUSY, True)
    s.se("MenuClose", volume=65)
    s.erase_picture(PIC_CURSOR)
    s.erase_picture(PIC_GHOST)
    for slot in range(len(EFFECT_KEYS)):
        x, y = icon_position(slot)
        s.move_picture(_icon_pic(slot), x, y + 6, magnify=40, transparency=100,
                       tenths=1)
    s.erase_picture(PIC_BLOOM)
    s.move_picture(PIC_TITLE, 160, 40, transparency=100, tenths=1)
    s.move_picture(PIC_MOTES, 160, 120, transparency=100, tenths=1,
                   effect=2, power=14)
    s.move_picture(PIC_FRAME, 160, 150, magnify=108, transparency=100, tenths=2)
    s.move_picture(PIC_PANEL, 160, 120, magnify=16, transparency=100, tenths=2)
    # the garnishes wind down rather than cutting: the halo spins away small,
    # the rings open outward
    s.move_picture(PIC_HALO, 160, 120, magnify=18, transparency=100, tenths=2,
                   effect=1, power=7)
    s.move_picture(PIC_RINGS, 160, 120, magnify=190, transparency=100, tenths=2,
                   effect=1, power=-9, wait=True)
    s.move_picture(PIC_VEIL, 160, 120, transparency=100, tenths=1, wait=True)
    for pic in (PIC_VEIL, PIC_HALO, PIC_RINGS, PIC_PANEL, PIC_FRAME, PIC_TITLE,
                PIC_GLINT, PIC_DUST, PIC_MOTES):
        s.erase_picture(pic)
    for slot in range(len(EFFECT_KEYS)):
        s.erase_picture(_icon_pic(slot))
    s.switch(SW_MENU_OPEN, False)
    s.switch(SW_MENU_BUSY, False)
    return s


def diary() -> CommonEvent:
    """The diary loop: open, take input, equip, close."""
    s = Script()
    s.extend(diary_open())
    s.var(VR_MENU_CURSOR, 0)

    with s.loop():
        s.key_input(VR_SCRATCH, wait=True, decision=True, cancel=True,
                    directions=True)
        # 1 down, 2 left, 3 right, 4 up, 5 decision, 6 cancel
        with s.if_var(VR_SCRATCH, 6):
            s.break_loop()
        with s.if_var(VR_SCRATCH, 5):
            s.call_event(CE_EQUIP)
            s.break_loop()

        # the ghost is left where the cursor was, then fades
        s.show_picture(PIC_GHOST, "MenuGhost", 160, 120, transparency=45)
        with s.if_var(VR_SCRATCH, 3):
            s.var(VR_MENU_CURSOR, 1, op=1)
        with s.if_var(VR_SCRATCH, 2):
            s.var(VR_MENU_CURSOR, 1, op=2)
        with s.if_var(VR_SCRATCH, 1):
            s.var(VR_MENU_CURSOR, 4, op=1)
        with s.if_var(VR_SCRATCH, 4):
            s.var(VR_MENU_CURSOR, 4, op=2)
        with s.if_var(VR_MENU_CURSOR, 0, 4):
            s.var(VR_MENU_CURSOR, 11)
        with s.if_var(VR_MENU_CURSOR, 11, 3):
            s.var(VR_MENU_CURSOR, 0)

        s.se("Cursor", volume=45)
        # move the cursor to the new slot with a squash on landing
        for slot in range(len(EFFECT_KEYS)):
            x, y = icon_position(slot)
            with s.if_var(VR_MENU_CURSOR, slot):
                s.move_picture(PIC_GHOST, x, y, transparency=100, tenths=2)
                # the light gets there first and the cursor catches up, which
                # is what makes the selection feel like it is being lit rather
                # than being pointed at
                s.move_picture(PIC_BLOOM, x, y, magnify=118, transparency=28,
                               tenths=1, effect=1, power=2)
                s.move_picture(PIC_CURSOR, x, y, magnify=118, tenths=1,
                               effect=1, power=1, wait=True)
                s.move_picture(PIC_CURSOR, x, y, magnify=100, tenths=1,
                               effect=1, power=1)
                s.move_picture(PIC_BLOOM, x, y, magnify=100, transparency=40,
                               tenths=1, effect=1, power=2)

    s.extend(diary_close())
    return CommonEvent(CE_DIARY, "diary", TRIGGER_CALL, None, s)


def diary_key() -> CommonEvent:
    """Shift opens the diary too.

    Tab is where the diary lives (``keys.py``), but Tab only exists because
    Ineluki's Key Patch is switched on, and the patch is a thing that can be
    absent: a platform without raw keyboard support, or a player who launched
    with ``--no-patch-keypatch``.  Shift needs nothing and costs nothing --
    it is one of the engine's own seven and no longer wanted for anything
    else -- so it stays as the way in that cannot fail.
    """
    s = Script()
    with s.if_switch(SW_MENU_OPEN, False):
        with s.if_switch(SW_MENU_BUSY, False):
            s.key_input(VR_KEY, wait=False, decision=False, cancel=False,
                        directions=False, shift=True)
            with s.if_var(VR_KEY, 7):
                s.switch(SW_MENU_OPEN, True)
                s.call_event(CE_DIARY)
    # No wait.  RPG Maker measures a wait in *tenths of a second*, so the
    # habitual `wait 1` at the end of a parallel loop polls six frames apart,
    # and a tap shorter than that is a keypress the game never sees.
    return CommonEvent(CE_DIARY_KEY, "diary key", TRIGGER_PARALLEL, None, s)


def equip() -> CommonEvent:
    """Put on (or take off) whatever the cursor is over."""
    s = Script()
    for slot, key in enumerate(EFFECT_KEYS):
        with s.if_var(VR_MENU_CURSOR, slot):
            with s.if_switch(SW_HAS_EFFECT[key]):
                with s.if_else_var(VR_EQUIPPED, slot + 1) as arm:
                    with arm(False):
                        # already wearing it: take it off
                        s.call_event(CE_UNEQUIP)
                    with arm(True):
                        s.call_event(CE_UNEQUIP)
                        s.var(VR_EQUIPPED, slot + 1)
                        s.switch(SW_EFFECT_ACTIVE[key], True)
                        # thirteen selves across two sheets: the plain one
                        # and the first seven effects on Dreamer, the rest on
                        # DreamerB.  Wearing something has to look like it.
                        if slot < 7:
                            s.set_sprite(1, "Dreamer", slot + 1)
                        else:
                            s.set_sprite(1, "DreamerB", slot - 7)
                        s.se("Decision", volume=70)
                        s.flash(255, 250, 230, 22, 3, False)
            with s.if_switch(SW_HAS_EFFECT[key], False):
                s.se("Buzzer", volume=50)
    return CommonEvent(CE_EQUIP, "equip", TRIGGER_CALL, None, s)


def unequip() -> CommonEvent:
    s = Script()
    s.var(VR_EQUIPPED, 0)
    for key in EFFECT_KEYS:
        s.switch(SW_EFFECT_ACTIVE[key], False)
    s.set_sprite(1, "Dreamer", 0)
    return CommonEvent(CE_UNEQUIP, "unequip", TRIGGER_CALL, None, s)


def give_effect() -> CommonEvent:
    """Shared pickup ceremony.  ``VR_SCRATCH`` names which one."""
    s = Script()
    s.comment("scratch holds the effect number 1..12")
    s.se("ItemGet", volume=90)
    s.flash(255, 252, 236, 26, 6, True)
    s.var(VR_EFFECTS_FOUND, 1, op=1)
    for slot, (key, name, line) in enumerate(EFFECTS, start=1):
        with s.if_var(VR_SCRATCH, slot):
            s.switch(SW_HAS_EFFECT[key], True)
            s.give_item(slot, 1)
            s.msg_options(MSG_MIDDLE)
            s.msg(name, "", line)
            s.msg_options(MSG_BOTTOM)
    # finding the twelfth one opens something
    with s.if_var(VR_EFFECTS_FOUND, 12, 1):
        s.switch(SW_DEEP_UNLOCKED, True)
    return CommonEvent(CE_GIVE_EFFECT, "give effect", TRIGGER_CALL, None, s)


def wake(worlds) -> CommonEvent:
    """Waking up: the way back to the room, and it costs nothing.

    Called from the nexus mirror.  The destination is read from the room
    itself rather than written down here, because a hardcoded spawn is a
    softlock waiting for somebody to move the bed.
    """
    s = Script()
    s.bgm_fadeout(20)
    s.tint(200, 200, 200, 0, 12, True)
    s.se("TapeStop", volume=60)
    s.fade_out(2)
    s.call_event(CE_OVERLAY_OFF)
    room = worlds["room"]
    s.weather(0, 0)
    s.pan_reset(speed=6, wait=False)
    s.teleport(room.map_id, *room.spawn)
    s.var(VR_WORLD, 1)
    s.call_event(CE_ARRIVE)
    s.tint(100, 100, 100, 100, 0, False)
    s.fade_in(atmosphere.of("room").enter)
    return CommonEvent(CE_WAKE, "wake", TRIGGER_CALL, None, s)


def overlay_on() -> CommonEvent:
    s = Script()
    s.switch(SW_OVERLAY_ON, True)
    return CommonEvent(CE_OVERLAY_ON, "overlay on", TRIGGER_CALL, None, s)


def overlay_off() -> CommonEvent:
    s = Script()
    s.erase_picture(PIC_OVERLAY)
    s.switch(SW_OVERLAY_ON, False)
    return CommonEvent(CE_OVERLAY_OFF, "overlay off", TRIGGER_CALL, None, s)


def keyboard() -> CommonEvent:
    """The wider keyboard, drained one press at a time.

    Ineluki's Key Patch does not answer "is this key down"; it keeps a queue
    of the keys that have gone down and hands them over one at a time through
    the variable that nominally holds the music's position.  So this reads
    that variable repeatedly until it comes back empty, dispatching whatever
    it finds.  ``keys.py`` explains the arrangement; the two things that
    matter here are that the queue is LIFO and that empty reads as ``-1``.

    The drain is **counted**, not merely bounded by the empty marker.  With
    the patch switched off, the same variable returns the real MIDI position,
    which counts upward and never goes negative -- a loop waiting for ``-1``
    would spin forever inside a parallel event and take the whole game with
    it.  Six presses a frame is more than a hand can produce and cheap enough
    to pay every frame regardless.
    """
    from ..state import VR_KEY_DRAIN, VR_KEY_QUEUE
    from .. import keys as K

    s = Script()
    s.comment("ineluki: drain the key queue")
    s.var(VR_KEY_DRAIN, K.DRAIN)
    with s.loop():
        with s.if_var(VR_KEY_DRAIN, 0, 2):      # <= 0: enough for one frame
            s.break_loop()
        s.var(VR_KEY_DRAIN, 1, op=2)
        s.var_from_other(VR_KEY_QUEUE, K.MIDI_TICKS)
        with s.if_var(VR_KEY_QUEUE, 0, 4):      # < 0: the queue is empty
            s.break_loop()
        for key in K.KEYS:
            with s.if_var(VR_KEY_QUEUE, key.value):
                _PRESSES[key.ineluki](s)
    return CommonEvent(CE_KEYBOARD, "keyboard", TRIGGER_PARALLEL, None, s)


def _open_diary(s: Script) -> None:
    """Tab: the things you found.  Guarded, because the diary is a stack of
    pictures that takes several frames to build and several to take apart --
    a second press part-way through would build it on top of itself."""
    with s.if_switch(SW_MENU_OPEN, False):
        with s.if_switch(SW_MENU_BUSY, False):
            s.switch(SW_MENU_OPEN, True)
            s.call_event(CE_DIARY)


def _show_position(s: Script) -> None:
    """P for position: coordinates."""
    s.call_event(CE_WHEREAMI)


# What each registered key does.  Keyed by Ineluki's own name for the key so
# that the roster in ``keys.py`` stays a list of keys and nothing else; a key
# named there with no entry here is a build error rather than a key that
# silently does nothing, which is the failure this game keeps having.
_PRESSES = {
    "(tab)": _open_diary,
    "p": _show_position,
}


def whereami(worlds) -> CommonEvent:
    """Press C and the game tells you where you are.

    A testing aid, and off unless you ask for it: nothing shows until the key
    is pressed, so a player who never presses it never learns it exists.

    It has a key of its own now.  It lived on cancel for exactly as long as
    the engine's seven buttons were all there was, and cancel was never a
    good home for it -- a readout that interrupts you every time you try to
    back out of something is a readout that gets in the way.

    RPG Maker cannot draw text on the screen outside a message box, so the
    readout *is* a message box.  It reads the hero's tile straight out of the
    engine rather than tracking it, which means it cannot drift out of step
    with where you actually are.
    """
    from ..state import VR_DEBUG_X, VR_DEBUG_Y, VR_WORLD

    s = Script()
    s.var_from_event(VR_DEBUG_X, PLAYER, 1)
    s.var_from_event(VR_DEBUG_Y, PLAYER, 2)
    s.msg_options(MSG_TOP)
    # Built from the constants rather than typed: the first version had the
    # world's variable written out as \\v[1] when it is six, so the readout
    # confidently reported the wrong world.
    s.msg(f"x \\v[{VR_DEBUG_X}]   y \\v[{VR_DEBUG_Y}]", "",
          f"world \\v[{VR_WORLD}]")
    s.msg_options(MSG_BOTTOM)
    return CommonEvent(CE_WHEREAMI, "where am i", TRIGGER_CALL, None, s)


def atmosphere_watch(worlds) -> CommonEvent:
    """Footsteps, and the tremor some worlds never stop having.

    RPG Maker's shake is a one-shot, so a *continuous* tremor has to be
    re-armed — which is fine, because this event is already running every
    frame to watch the ground.  Footing is read from the terrain id under the
    player rather than from which world it is: a world with one footstep sound
    is a world with one surface, whatever its art is doing.
    """
    from .worlds import WORLD_ORDER

    s = Script()
    s.comment("footing and tremor")
    s.var_from_event(VR_TEMP_X, PLAYER, 1)
    s.var_from_event(VR_TEMP_Y, PLAYER, 2)
    # only when the player has actually moved onto a new tile
    s.var_from_var(VR_SCRATCH, VR_TEMP_X)
    s.var_from_var(VR_SCRATCH, VR_LAST_X, op=2)
    s.var_from_var(VR_KEY, VR_TEMP_Y)
    s.var_from_var(VR_KEY, VR_LAST_Y, op=2)
    # Standing still is the only input this game has that is not walking, so
    # several worlds read it.  The counter climbs while the tile under the
    # player does not change and resets the moment it does.
    s.var_from_var(VR_KEY, VR_TEMP_X)
    s.var_from_var(VR_KEY, VR_LAST_X, op=2)
    with s.if_var(VR_KEY, 0):
        s.var_from_var(VR_KEY, VR_TEMP_Y)
        s.var_from_var(VR_KEY, VR_LAST_Y, op=2)
        with s.if_var(VR_KEY, 0):
            s.var(VR_STILL, 2, op=1)
    with s.if_var(VR_KEY, 0, 1):
        s.var(VR_STILL, 0)

    s.store_terrain(VR_SCRATCH, VR_TEMP_X, VR_TEMP_Y)

    for index, key in enumerate(WORLD_ORDER, start=1):
        air = atmosphere.of(key)
        rule = mechanics.RULES.get(key)
        with s.if_var(VR_WORLD, index):
            for terrain, sound in enumerate(air.steps, start=1):
                with s.if_var(VR_SCRATCH, terrain):
                    s.se(sound, volume=air.step_volume)
            if air.shake:
                pass    # camera shake is banned; see atmosphere.Atmosphere
            # and whatever this world alone is allowed to do
            if rule is not None:
                rule(s)
    s.wait(2)
    return CommonEvent(CE_ATMOSPHERE, "atmosphere", TRIGGER_PARALLEL, None, s)


def build(worlds) -> list[CommonEvent]:
    return [
        boot(),
        arrival(worlds),
        loop_watch(),
        diary(),
        equip(),
        unequip(),
        roll(),
        give_effect(),
        overlay_on(),
        overlay_off(),
        wake(worlds),
        diary_key(),
        atmosphere_watch(worlds),
        keyboard(),
        film(worlds),
        whereami(worlds),
    ]
