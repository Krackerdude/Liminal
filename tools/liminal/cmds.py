"""Event-command scripting for RPG Maker 2000 data files.

RPG Maker stores event logic as a flat list of ``(code, indent, string,
parameters)`` records.  Nesting is expressed purely through the indent column
plus explicit terminator opcodes, which is miserable to write by hand, so
``Script`` wraps it in context managers that keep the two in sync.

Opcode numbers and parameter layouts were taken from liblcf's
``rpg::EventCommand::Code`` enum and EasyRPG Player's ``game_interpreter.cpp``.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Sequence

from .lcfxml import Node

# --- opcodes -----------------------------------------------------------------
END = 10
CALL_COMMON_EVENT = 1005
SHOW_MESSAGE = 10110
SHOW_MESSAGE_2 = 20110
MESSAGE_OPTIONS = 10120
CHANGE_FACE = 10130
SHOW_CHOICE = 10140
SHOW_CHOICE_OPTION = 20140
SHOW_CHOICE_END = 20141
CONTROL_SWITCHES = 10210
CONTROL_VARS = 10220
TIMER_OPERATION = 10230
CHANGE_ITEMS = 10320
CHANGE_EXP = 10410
CHANGE_LEVEL = 10420
CHANGE_PARAMETERS = 10430
CHANGE_SKILLS = 10440
CHANGE_HP = 10460
CHANGE_SP = 10470
FULL_HEAL = 10490
CHANGE_HERO_NAME = 10610
CHANGE_SPRITE = 10630
CHANGE_SYSTEM_GRAPHICS = 10680
TELEPORT = 10810
MEMORIZE_LOCATION = 10820
RECALL_LOCATION = 10830
CHANGE_EVENT_LOCATION = 10860
STORE_TERRAIN_ID = 10910
STORE_EVENT_ID = 10920
ERASE_SCREEN = 11010
SHOW_SCREEN = 11020
TINT_SCREEN = 11030
FLASH_SCREEN = 11040
SHAKE_SCREEN = 11050
PAN_SCREEN = 11060
WEATHER = 11070
SHOW_PICTURE = 11110
MOVE_PICTURE = 11120
ERASE_PICTURE = 11130
PLAYER_VISIBILITY = 11310
FLASH_SPRITE = 11320
MOVE_EVENT = 11330
PROCEED_WITH_MOVEMENT = 11340
HALT_ALL_MOVEMENT = 11350
WAIT = 11410
PLAY_BGM = 11510
FADEOUT_BGM = 11520
MEMORIZE_BGM = 11530
PLAY_MEMORIZED_BGM = 11540
PLAY_SOUND = 11550
KEY_INPUT = 11610
CHANGE_TILESET = 11710
CHANGE_PBG = 11720
TILE_SUBSTITUTION = 11750
OPEN_SAVE_MENU = 11910
CHANGE_SAVE_ACCESS = 11930
OPEN_MAIN_MENU = 11950
CHANGE_MENU_ACCESS = 11960
CONDITIONAL_BRANCH = 12010
ELSE_BRANCH = 22010
END_BRANCH = 22011
LABEL = 12110
JUMP_TO_LABEL = 12120
LOOP = 12210
BREAK_LOOP = 12220
END_LOOP = 22210
END_EVENT_PROCESSING = 12310
ERASE_EVENT = 12320
CALL_EVENT = 12330
COMMENT = 12410
COMMENT_2 = 22410

# Character ids accepted where an event id is expected.
THIS_EVENT = 0
PLAYER = 10001

# Move-route command ids (rpg::MoveCommand::Code).
MV_UP, MV_RIGHT, MV_DOWN, MV_LEFT = 0, 1, 2, 3
MV_RANDOM = 8
MV_TOWARD_HERO = 9
MV_AWAY_FROM_HERO = 10
MV_FORWARD = 11
MV_FACE_UP, MV_FACE_RIGHT, MV_FACE_DOWN, MV_FACE_LEFT = 12, 13, 14, 15
MV_TURN_180 = 18
MV_FACE_RANDOM = 20
MV_FACE_HERO = 21
MV_WAIT = 23
MV_LOCK_FACING = 26
MV_UNLOCK_FACING = 27
MV_SPEED_UP = 28
MV_SPEED_DOWN = 29
MV_FREQ_UP = 30
MV_FREQ_DOWN = 31
MV_SWITCH_ON = 32
MV_SWITCH_OFF = 33
MV_CHANGE_GRAPHIC = 34
MV_PLAY_SOUND = 35
MV_WALK_EVERYWHERE_ON = 36
MV_WALK_EVERYWHERE_OFF = 37
MV_STOP_ANIMATION = 38
MV_START_ANIMATION = 39
MV_INCREASE_TRANSP = 40
MV_DECREASE_TRANSP = 41

# Message-window positions.
MSG_TOP, MSG_MIDDLE, MSG_BOTTOM = 0, 1, 2


class Command:
    __slots__ = ("code", "indent", "string", "params")

    def __init__(self, code: int, indent: int, string: str, params: Sequence[int]):
        self.code = code
        self.indent = indent
        self.string = string
        self.params = list(params)

    def to_node(self) -> Node:
        node = Node("EventCommand")
        node.set("code", self.code)
        node.set("indent", self.indent)
        node.set("string", self.string)
        node.set("parameters", self.params)
        return node


class Script:
    """Builds an event-command list.

    Every method returns ``self`` so short scripts read as a single chain, and
    the block helpers are context managers so nesting is impossible to get out
    of sync with the terminator opcodes.
    """

    def __init__(self) -> None:
        self.commands: list[Command] = []
        self.indent = 0

    # -- plumbing ------------------------------------------------------------
    def raw(self, code: int, params: Sequence[int] = (), string: str = "") -> "Script":
        self.commands.append(Command(code, self.indent, string, params))
        return self

    def _raw_at(self, code: int, indent: int, params: Sequence[int] = (),
                string: str = "") -> None:
        self.commands.append(Command(code, indent, string, params))

    def to_nodes(self) -> list[Node]:
        """Serialise the command list.

        No terminator is emitted: liblcf writes the four zero bytes that close
        a command list itself, and adding our own makes the reader consume it
        as the terminator and then trip over the real one.
        """
        return [c.to_node() for c in self.commands]

    def extend(self, other: "Script") -> "Script":
        """Splice another script in at the current indent level."""
        for cmd in other.commands:
            self.commands.append(
                Command(cmd.code, cmd.indent + self.indent, cmd.string, cmd.params))
        return self

    # -- text ----------------------------------------------------------------
    def msg(self, *lines: str) -> "Script":
        """Show a message.  RPG Maker fits four lines per window."""
        flat: list[str] = []
        for line in lines:
            flat.extend(line.split("\n"))
        for chunk_start in range(0, len(flat), 4):
            chunk = flat[chunk_start:chunk_start + 4]
            self.raw(SHOW_MESSAGE, [], chunk[0])
            for extra in chunk[1:]:
                self.raw(SHOW_MESSAGE_2, [], extra)
        return self

    def msg_options(self, position: int = MSG_BOTTOM, *, fixed: bool = False,
                    transparent: bool = False, dont_hide_hero: bool = False) -> "Script":
        return self.raw(MESSAGE_OPTIONS,
                        [1 if transparent else 0, position,
                         0 if fixed else 1, 1 if dont_hide_hero else 0])

    def face(self, name: str = "", index: int = 0, *, right: bool = False,
             flip: bool = False) -> "Script":
        return self.raw(CHANGE_FACE, [index, 1 if right else 0, 1 if flip else 0], name)

    def comment(self, *lines: str) -> "Script":
        if not lines:
            return self
        self.raw(COMMENT, [], lines[0])
        for extra in lines[1:]:
            self.raw(COMMENT_2, [], extra)
        return self

    @contextmanager
    def choice(self, options: Sequence[str], cancel: int = 0):
        """Present a choice menu.

        Yields a function that opens each branch in turn::

            with script.choice(["yes", "no"]) as branch:
                with branch(0):
                    ...
        """
        # The option labels live on the ShowChoiceOption commands that follow,
        # at the same indent as ShowChoice itself.  The single parameter here
        # is the cancel type (0 disallow, 1..4 jump to that option, 5 own arm).
        padded = list(options)[:4] + [""] * (4 - len(options))
        self.raw(SHOW_CHOICE, [cancel], "/".join(options[:4]))
        base = self.indent

        @contextmanager
        def branch(index: int):
            self._raw_at(SHOW_CHOICE_OPTION, base, [index], padded[index])
            self.indent = base + 1
            try:
                yield self
            finally:
                self.indent = base

        try:
            yield branch
        finally:
            self.indent = base
            self.raw(SHOW_CHOICE_END)

    # -- state ---------------------------------------------------------------
    def switch(self, switch_id: int, value: bool | None = True) -> "Script":
        """Set a switch.  ``value=None`` toggles it."""
        mode = 2 if value is None else (0 if value else 1)
        return self.raw(CONTROL_SWITCHES, [0, switch_id, switch_id, mode])

    def switch_range(self, first: int, last: int, value: bool = True) -> "Script":
        return self.raw(CONTROL_SWITCHES, [1, first, last, 0 if value else 1])

    def var(self, var_id: int, value: int, op: int = 0) -> "Script":
        """Assign a constant to a variable (``op``: 0 set, 1 add, 2 sub, ...)."""
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 0, value])

    def var_from_var(self, var_id: int, source: int, op: int = 0) -> "Script":
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 1, source])

    def var_random(self, var_id: int, low: int, high: int, op: int = 0) -> "Script":
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 3, low, high])

    def var_from_hero(self, var_id: int, actor_id: int, attribute: int,
                      op: int = 0) -> "Script":
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 5, actor_id, attribute])

    def var_from_event(self, var_id: int, event_id: int, attribute: int,
                       op: int = 0) -> "Script":
        """Attribute: 0 map, 1 x, 2 y, 3 facing, 4 screen x, 5 screen y."""
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 6, event_id, attribute])

    def var_from_other(self, var_id: int, attribute: int, op: int = 0) -> "Script":
        """Attribute: 0 gold, 1 timer1 sec, 2 party size, 3 saves, 4 battles, ...
        7 is the frame counter, which we use as a cheap clock."""
        return self.raw(CONTROL_VARS, [0, var_id, var_id, op, 7, attribute])

    def timer(self, seconds: int, *, start: bool = True, visible: bool = False,
              during_battle: bool = False) -> "Script":
        self.raw(TIMER_OPERATION, [0, seconds * 60, 0, 0, 0])
        if start:
            self.raw(TIMER_OPERATION,
                     [1, 0, 0, 1 if visible else 0, 1 if during_battle else 0])
        return self

    def timer_stop(self) -> "Script":
        return self.raw(TIMER_OPERATION, [2, 0, 0, 0, 0])

    def give_item(self, item_id: int, count: int = 1) -> "Script":
        return self.raw(CHANGE_ITEMS, [0, 0, item_id, 0, count])

    def take_item(self, item_id: int, count: int = 1) -> "Script":
        return self.raw(CHANGE_ITEMS, [1, 0, item_id, 0, count])

    def give_skill(self, actor_id: int, skill_id: int) -> "Script":
        return self.raw(CHANGE_SKILLS, [0, actor_id, 0, skill_id, 0])

    def change_hp(self, actor_id: int, amount: int, *, add: bool = True) -> "Script":
        return self.raw(CHANGE_HP,
                        [0, actor_id, 0 if add else 1, 0, abs(amount), 0])

    def change_sp(self, actor_id: int, amount: int, *, add: bool = True) -> "Script":
        return self.raw(CHANGE_SP, [0, actor_id, 0 if add else 1, 0, abs(amount)])

    def change_level(self, actor_id: int, amount: int, *, add: bool = True,
                     show: bool = False) -> "Script":
        return self.raw(CHANGE_LEVEL,
                        [0, actor_id, 0 if add else 1, 0, abs(amount),
                         1 if show else 0])

    def change_parameter(self, actor_id: int, which: int, amount: int,
                         *, add: bool = True) -> "Script":
        """which: 0 maxhp, 1 maxsp, 2 attack, 3 defense, 4 spirit, 5 agility."""
        return self.raw(CHANGE_PARAMETERS,
                        [0, actor_id, 0 if add else 1, which, 0, abs(amount)])

    def full_heal(self, actor_id: int = 0) -> "Script":
        return self.raw(FULL_HEAL, [0 if actor_id == 0 else 1, actor_id])

    def rename_hero(self, actor_id: int, name: str) -> "Script":
        return self.raw(CHANGE_HERO_NAME, [actor_id], name)

    def set_sprite(self, actor_id: int, charset: str, index: int,
                   transparent: bool = False) -> "Script":
        return self.raw(CHANGE_SPRITE,
                        [actor_id, index, 1 if transparent else 0], charset)

    def set_system_graphic(self, name: str) -> "Script":
        return self.raw(CHANGE_SYSTEM_GRAPHICS, [0, 0], name)

    # -- movement / place ----------------------------------------------------
    def teleport(self, map_id: int, x: int, y: int) -> "Script":
        return self.raw(TELEPORT, [map_id, x, y])

    def store_terrain(self, var_id: int, x_var: int, y_var: int) -> "Script":
        """Read the terrain id at a position held in two variables.

        Mode 1 means "the coordinates are in variables"; mode 0 would take
        them as constants, which is useless for following a moving player.
        """
        return self.raw(STORE_TERRAIN_ID, [1, x_var, y_var, var_id])

    def memorize_location(self, map_var: int, x_var: int, y_var: int) -> "Script":
        return self.raw(MEMORIZE_LOCATION, [map_var, x_var, y_var])

    def recall_location(self, map_var: int, x_var: int, y_var: int) -> "Script":
        return self.raw(RECALL_LOCATION, [0, map_var, x_var, y_var])

    def move_event_to(self, event_id: int, x: int, y: int) -> "Script":
        return self.raw(CHANGE_EVENT_LOCATION, [event_id, 0, x, y])

    def move_event_to_vars(self, event_id: int, x_var: int, y_var: int) -> "Script":
        return self.raw(CHANGE_EVENT_LOCATION, [event_id, 1, x_var, y_var])

    def move_route(self, target: int, commands: Sequence[int], *,
                   frequency: int = 8, repeat: bool = False,
                   skippable: bool = True) -> "Script":
        """Force a move route.  Only parameterless move commands are supported
        here; for graphic/sound/switch moves put the route on an event page
        instead (see :func:`move_route_nodes`)."""
        return self.raw(MOVE_EVENT,
                        [target, frequency, 1 if repeat else 0,
                         1 if skippable else 0, *commands])

    def await_movement(self) -> "Script":
        return self.raw(PROCEED_WITH_MOVEMENT)

    def halt_movement(self) -> "Script":
        return self.raw(HALT_ALL_MOVEMENT)

    def player_visible(self, visible: bool) -> "Script":
        return self.raw(PLAYER_VISIBILITY, [1 if visible else 0])

    def flash_sprite(self, event_id: int, r: int, g: int, b: int, power: int,
                     tenths: int, wait: bool = False) -> "Script":
        return self.raw(FLASH_SPRITE,
                        [event_id, r, g, b, power, tenths, 1 if wait else 0])

    def erase_event(self) -> "Script":
        return self.raw(ERASE_EVENT)

    def call_event(self, common_event_id: int) -> "Script":
        return self.raw(CALL_EVENT, [0, common_event_id, 0])

    def end_event(self) -> "Script":
        return self.raw(END_EVENT_PROCESSING)

    # -- screen --------------------------------------------------------------
    def tint(self, r: int = 100, g: int = 100, b: int = 100, sat: int = 100,
             tenths: int = 0, wait: bool = True) -> "Script":
        """Tint the screen.  100 is neutral for every channel; range is 0..200."""
        return self.raw(TINT_SCREEN, [r, g, b, sat, tenths, 1 if wait else 0])

    def flash(self, r: int, g: int, b: int, power: int, tenths: int,
              wait: bool = True) -> "Script":
        return self.raw(FLASH_SCREEN, [r, g, b, power, tenths, 1 if wait else 0])

    def shake(self, strength: int, speed: int, tenths: int,
              wait: bool = True) -> "Script":
        return self.raw(SHAKE_SCREEN,
                        [strength, speed, tenths, 1 if wait else 0])

    def pan(self, direction: int, distance: int, speed: int,
            wait: bool = True) -> "Script":
        """direction: 0 up, 1 right, 2 down, 3 left."""
        return self.raw(PAN_SCREEN, [1, direction, distance, speed,
                                     1 if wait else 0])

    def pan_reset(self, speed: int = 4, wait: bool = True) -> "Script":
        return self.raw(PAN_SCREEN, [2, 0, 0, speed, 1 if wait else 0])

    def pan_lock(self) -> "Script":
        return self.raw(PAN_SCREEN, [0, 0, 0, 0, 0])

    def pan_unlock(self) -> "Script":
        return self.raw(PAN_SCREEN, [3, 0, 0, 0, 0])

    def weather(self, kind: int, strength: int = 1) -> "Script":
        """kind: 0 none, 1 rain, 2 snow."""
        return self.raw(WEATHER, [kind, strength])

    def fade_out(self, transition: int = 0) -> "Script":
        return self.raw(ERASE_SCREEN, [transition])

    def fade_in(self, transition: int = 0) -> "Script":
        return self.raw(SHOW_SCREEN, [transition])

    def show_picture(self, pic_id: int, name: str, x: int = 160, y: int = 120, *,
                     fixed_to_map: bool = False, magnify: int = 100,
                     transparency: int = 0, use_transparent_color: bool = True,
                     r: int = 100, g: int = 100, b: int = 100, sat: int = 100,
                     effect: int = 0, power: int = 0) -> "Script":
        return self.raw(SHOW_PICTURE,
                        [pic_id, 0, x, y, 1 if fixed_to_map else 0, magnify,
                         transparency, 1 if use_transparent_color else 0,
                         r, g, b, sat, effect, power], name)

    def move_picture(self, pic_id: int, x: int, y: int, *, magnify: int = 100,
                     transparency: int = 0, r: int = 100, g: int = 100,
                     b: int = 100, sat: int = 100, effect: int = 0,
                     power: int = 0, tenths: int = 10,
                     wait: bool = False) -> "Script":
        return self.raw(MOVE_PICTURE,
                        [pic_id, 0, x, y, 0, magnify, transparency, 0,
                         r, g, b, sat, effect, power, tenths,
                         1 if wait else 0], "")

    def erase_picture(self, pic_id: int) -> "Script":
        return self.raw(ERASE_PICTURE, [pic_id])

    def change_tileset(self, chipset_id: int) -> "Script":
        return self.raw(CHANGE_TILESET, [chipset_id])

    def change_panorama(self, name: str, *, loop_h: bool = True, loop_v: bool = False,
                        auto_h: bool = False, speed_h: int = 0,
                        auto_v: bool = False, speed_v: int = 0) -> "Script":
        return self.raw(CHANGE_PBG,
                        [1 if loop_h else 0, 1 if loop_v else 0,
                         1 if auto_h else 0, speed_h,
                         1 if auto_v else 0, speed_v], name)

    def substitute_tile(self, layer: int, old_id: int, new_id: int) -> "Script":
        """Swap one tile for another map-wide (layer 0 lower, 1 upper)."""
        return self.raw(TILE_SUBSTITUTION, [layer, old_id, new_id])

    # -- audio ---------------------------------------------------------------
    def bgm(self, name: str, *, fadein: int = 0, volume: int = 100,
            tempo: int = 100, balance: int = 50) -> "Script":
        return self.raw(PLAY_BGM, [fadein, volume, tempo, balance], name)

    def bgm_fadeout(self, tenths: int = 20) -> "Script":
        return self.raw(FADEOUT_BGM, [tenths])

    def bgm_memorize(self) -> "Script":
        return self.raw(MEMORIZE_BGM)

    def bgm_restore(self) -> "Script":
        return self.raw(PLAY_MEMORIZED_BGM)

    def se(self, name: str, *, volume: int = 100, tempo: int = 100,
           balance: int = 50) -> "Script":
        return self.raw(PLAY_SOUND, [volume, tempo, balance], name)

    # -- flow ----------------------------------------------------------------
    def wait(self, tenths: int) -> "Script":
        return self.raw(WAIT, [tenths, 0])

    def key_input(self, var_id: int, *, wait: bool = True, decision: bool = True,
                  cancel: bool = False, directions: bool = False,
                  shift: bool = False) -> "Script":
        """Read a key into a variable.

        Results: 1 down, 2 left, 3 right, 4 up, 5 decision, 6 cancel, 7 shift,
        0 nothing (only possible when ``wait`` is false).

        The ten-parameter RPG Maker **2000** v1.50+ layout, which is the only
        one with individual direction and shift flags::

            [var, wait, legacy_all_directions, decision, cancel,
             shift, down, left, right, up]

        RPG Maker 2003 uses a longer list with a different order; do not
        confuse the two.  The engine only reads past parameter four at all if
        it believes it is running 1.50 or later, which it decides by looking
        for an MP3 in ``Music/`` — see ``audio/elevenlabs.py``.  On a game it
        judges to be older, shift is not read and the diary cannot be opened.
        """
        d = 1 if directions else 0
        return self.raw(KEY_INPUT,
                        [var_id, 1 if wait else 0, 0, 1 if decision else 0,
                         1 if cancel else 0, 1 if shift else 0, d, d, d, d])

    def open_menu(self) -> "Script":
        return self.raw(OPEN_MAIN_MENU)

    def open_save(self) -> "Script":
        return self.raw(OPEN_SAVE_MENU)

    def allow_menu(self, allowed: bool) -> "Script":
        return self.raw(CHANGE_MENU_ACCESS, [1 if allowed else 0])

    def allow_save(self, allowed: bool) -> "Script":
        return self.raw(CHANGE_SAVE_ACCESS, [1 if allowed else 0])

    def label(self, n: int) -> "Script":
        return self.raw(LABEL, [n])

    def goto(self, n: int) -> "Script":
        return self.raw(JUMP_TO_LABEL, [n])

    def break_loop(self) -> "Script":
        return self.raw(BREAK_LOOP)

    @contextmanager
    def loop(self):
        self.raw(LOOP)
        base = self.indent
        self.indent += 1
        try:
            yield self
        finally:
            self.indent = base
            self.raw(END_LOOP)

    @contextmanager
    def _branch(self, params: Sequence[int], has_else: bool):
        self.raw(CONDITIONAL_BRANCH, [*params, 1 if has_else else 0])
        base = self.indent
        self.indent = base + 1
        try:
            yield self
        finally:
            self.indent = base

    @contextmanager
    def if_switch(self, switch_id: int, value: bool = True):
        with self._branch([0, switch_id, 0 if value else 1], False):
            yield self
        self.raw(END_BRANCH)

    @contextmanager
    def if_else_switch(self, switch_id: int, value: bool = True):
        """Yields ``(then, else)`` context managers for a two-armed branch."""
        base = self.indent
        self.raw(CONDITIONAL_BRANCH, [0, switch_id, 0 if value else 1, 1])

        @contextmanager
        def arm(is_else: bool):
            if is_else:
                self._raw_at(ELSE_BRANCH, base)
            self.indent = base + 1
            try:
                yield self
            finally:
                self.indent = base

        try:
            yield arm
        finally:
            self.indent = base
            self.raw(END_BRANCH)

    @contextmanager
    def if_var(self, var_id: int, value: int, operator: int = 0):
        """operator: 0 ==, 1 >=, 2 <=, 3 >, 4 <, 5 !=."""
        with self._branch([1, var_id, 0, value, operator], False):
            yield self
        self.raw(END_BRANCH)

    @contextmanager
    def if_else_var(self, var_id: int, value: int, operator: int = 0):
        base = self.indent
        self.raw(CONDITIONAL_BRANCH, [1, var_id, 0, value, operator, 1])

        @contextmanager
        def arm(is_else: bool):
            if is_else:
                self._raw_at(ELSE_BRANCH, base)
            self.indent = base + 1
            try:
                yield self
            finally:
                self.indent = base

        try:
            yield arm
        finally:
            self.indent = base
            self.raw(END_BRANCH)

    @contextmanager
    def if_var_var(self, var_id: int, other_var: int, operator: int = 0):
        with self._branch([1, var_id, 1, other_var, operator], False):
            yield self
        self.raw(END_BRANCH)

    @contextmanager
    def if_item(self, item_id: int, has: bool = True):
        with self._branch([4, item_id, 0 if has else 1], False):
            yield self
        self.raw(END_BRANCH)

    @contextmanager
    def if_timer(self, seconds: int, at_least: bool = True):
        with self._branch([2, seconds, 0 if at_least else 1], False):
            yield self
        self.raw(END_BRANCH)

    @contextmanager
    def if_hero_facing(self, direction: int):
        """Player facing: 0 up, 1 right, 2 down, 3 left."""
        with self._branch([5, 10001, 5, direction], False):
            yield self
        self.raw(END_BRANCH)


def mv_graphic(charset: str, index: int) -> tuple:
    return (MV_CHANGE_GRAPHIC, charset, index, 0, 0)


def mv_sound(name: str, volume: int = 100, tempo: int = 100,
             balance: int = 50) -> tuple:
    return (MV_PLAY_SOUND, name, volume, tempo, balance)


def mv_switch(switch_id: int, on: bool = True) -> tuple:
    return (MV_SWITCH_ON if on else MV_SWITCH_OFF, "", switch_id, 0, 0)


def move_route_nodes(commands: Sequence, repeat: bool = True,
                     skippable: bool = False) -> Node:
    """Build the ``<move_route>`` sub-record used by event pages.

    Accepts bare command ids, or the tuples produced by the ``mv_*`` helpers
    for the few commands that carry parameters.
    """
    holder = Node("move_route")
    route = holder.add(Node("MoveRoute"))
    cmd_list = route.add(Node("move_commands"))
    for entry in commands:
        if isinstance(entry, tuple):
            code, string, a, b, c = entry
        else:
            code, string, a, b, c = entry, "", 0, 0, 0
        item = cmd_list.add(Node("MoveCommand"))
        item.set("command_id", code)
        if code in (MV_SWITCH_ON, MV_SWITCH_OFF):
            item.set("parameter_a", a)
        elif code == MV_CHANGE_GRAPHIC:
            item.set("parameter_string", string)
            item.set("parameter_a", a)
        elif code == MV_PLAY_SOUND:
            item.set("parameter_string", string)
            item.set("parameter_a", a)
            item.set("parameter_b", b)
            item.set("parameter_c", c)
    route.set("repeat", repeat)
    route.set("skippable", skippable)
    return holder
