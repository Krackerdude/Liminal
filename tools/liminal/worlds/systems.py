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

from ..art.menu import EFFECTS, icon_position
from ..cmds import (MSG_BOTTOM, MSG_MIDDLE, MSG_TOP, MV_SPEED_UP, PLAYER,
                    Script)
from ..db import TRIGGER_CALL, TRIGGER_PARALLEL, CommonEvent
from ..state import (SW_DEEP_UNLOCKED, SW_EFFECT_ACTIVE, SW_EYE_ACTIVE,
                     SW_FOLLOWER, SW_HAS_EFFECT, SW_MENU_BUSY, SW_MENU_OPEN,
                     SW_OVERLAY_ON, SW_QUIET_ACTIVE, SW_TITLE_CHANGED,
                     SW_WOKE_ONCE, VR_DREAM_DISTANCE, VR_EFFECTS_FOUND,
                     VR_EQUIPPED, VR_LAST_X, VR_LAST_Y, VR_LOOPS,
                     VR_MENU_CURSOR, VR_PREV_WORLD, VR_ROLL, VR_SCRATCH,
                     VR_STEPS, VR_TEMP_X, VR_TEMP_Y, VR_VISITS_BASE, VR_WORLD)

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

# Picture layers.  Higher numbers draw in front.
PIC_OVERLAY = 5           # the world's own film: grain, haze, scanlines
PIC_VEIL = 10
PIC_PANEL = 11
PIC_FRAME = 12
PIC_TITLE = 13
PIC_ICON_BASE = 14        # 14..25, one per effect slot
PIC_GHOST = 27
PIC_CURSOR = 28
PIC_GLINT = 29
PIC_DUST = 30
PIC_FLASH = 40            # for anomalies: static, eye, white

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
    s.tint(100, 100, 100, 100, 0, False)
    # The pace of the whole game, set once and deliberately.  RPG Maker's
    # default is 4, one tile roughly every four frames; the worlds here are a
    # hundred and forty tiles across and meant to be walked rather than
    # crossed, so this is a decision and not an inherited default.
    s.move_route(PLAYER, [MV_SPEED_UP], frequency=8)
    s.await_movement()
    return CommonEvent(CE_BOOT, "boot", TRIGGER_CALL, None, s)


# --- arrival -----------------------------------------------------------------

def arrival(worlds) -> CommonEvent:
    """Grade the screen and start the music for whichever world we are in.

    Called by each map's own arrival event after it has set ``VR_WORLD``.
    One code path for every world keeps the transitions consistent, and means
    a world's identity is data rather than duplicated script.
    """
    from .worlds import WORLD_ORDER

    s = Script()
    s.comment("apply this world's colour grade, film and music")
    for index, key in enumerate(WORLD_ORDER, start=1):
        world = worlds[key]
        with s.if_var(VR_WORLD, index):
            r, g, b, sat = world.tint
            s.tint(r, g, b, sat, 8, False)
            s.bgm(world.music, fadein=25, volume=82)
            if world.overlay:
                s.show_picture(PIC_OVERLAY, world.overlay, 160, 120,
                               transparency=world.overlay_opacity,
                               use_transparent_color=True)
                s.call_event(CE_OVERLAY_ON)
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

    # 2. the page arrives small and overshoots before settling
    s.show_picture(PIC_PANEL, "MenuPanel", 160, 128, magnify=20,
                   transparency=100)
    s.move_picture(PIC_PANEL, 160, 118, magnify=108, transparency=0, tenths=2,
                   wait=True)
    s.move_picture(PIC_PANEL, 160, 120, magnify=100, tenths=1, wait=True)

    # 3. the border drops in behind it
    s.show_picture(PIC_FRAME, "MenuFrame", 160, 92, transparency=100)
    s.move_picture(PIC_FRAME, 160, 124, transparency=0, tenths=2, wait=True)
    s.move_picture(PIC_FRAME, 160, 120, tenths=1)

    # 4. a light travels across the border, once
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

    # 6. dust over everything, then the cursor last of all
    s.show_picture(PIC_DUST, "MenuDust", 160, 120, transparency=72)
    s.show_picture(PIC_GHOST, "MenuGhost", *icon_position(0), transparency=100)
    s.show_picture(PIC_CURSOR, "MenuCursor", *icon_position(0), magnify=150,
                   transparency=60)
    s.move_picture(PIC_CURSOR, *icon_position(0), magnify=100, transparency=0,
                   tenths=1)
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
    s.move_picture(PIC_TITLE, 160, 40, transparency=100, tenths=1)
    s.move_picture(PIC_FRAME, 160, 150, transparency=100, tenths=2)
    s.move_picture(PIC_PANEL, 160, 120, magnify=16, transparency=100, tenths=2,
                   wait=True)
    s.move_picture(PIC_VEIL, 160, 120, transparency=100, tenths=1, wait=True)
    for pic in (PIC_VEIL, PIC_PANEL, PIC_FRAME, PIC_TITLE, PIC_GLINT, PIC_DUST):
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
                s.move_picture(PIC_CURSOR, x, y, magnify=118, tenths=1,
                               wait=True)
                s.move_picture(PIC_CURSOR, x, y, magnify=100, tenths=1)

    s.extend(diary_close())
    return CommonEvent(CE_DIARY, "diary", TRIGGER_CALL, None, s)


def diary_key() -> CommonEvent:
    """Watches for the shift key and opens the diary."""
    s = Script()
    with s.if_switch(SW_MENU_OPEN, False):
        with s.if_switch(SW_MENU_BUSY, False):
            s.key_input(VR_SCRATCH, wait=False, decision=False, cancel=False,
                        directions=False, shift=True)
            with s.if_var(VR_SCRATCH, 7):
                s.switch(SW_MENU_OPEN, True)
                s.call_event(CE_DIARY)
    s.wait(1)
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
                        s.set_sprite(1, "Dreamer", min(slot, 7))
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
    s.teleport(room.map_id, *room.spawn)
    s.var(VR_WORLD, 1)
    s.call_event(CE_ARRIVE)
    s.tint(100, 100, 100, 100, 0, False)
    s.fade_in(2)
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
    ]
