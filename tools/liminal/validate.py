"""Engine-level checks the LCF round-trip cannot make.

A file can be perfectly well-formed and still be a broken game.  liblcf will
happily write a teleport to map 99, a charset name with no PNG behind it, or a
message that plays a sound effect nobody ever generated — and the Player's
response to all three is to carry on quietly with a blank sprite, silence, or
a black screen, which is much harder to notice than a crash.

So this walks the finished, in-memory game and asserts the things that are
true of a game and not merely of a file:

* every asset an event names exists on disk
* every teleport lands on a real map, inside its bounds
* every common event that is called exists
* every switch and variable an event touches is declared in the database
* every event stands somewhere on the map it belongs to
* every command list closes all of its own blocks

Everything is reported at once.  Fixing faults one build at a time when the
build takes two seconds is a waste of both of us.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .maps import LAYER_SAME, TRIGGER_ACTION
from .worlds.layout import solid_ids
from .cmds import (CALL_EVENT, CHANGE_SPRITE, CONDITIONAL_BRANCH,
                   CONTROL_SWITCHES, CONTROL_VARS, ELSE_BRANCH, END_BRANCH,
                   END_LOOP, LOOP, PLAY_BGM, PLAY_SOUND, SHOW_CHOICE,
                   SHOW_CHOICE_END, SHOW_CHOICE_OPTION, SHOW_PICTURE, TELEPORT,
                   Command)

# Commands that open a block, and the ones that close it.  Everything else
# leaves the indent alone.
OPENERS = {CONDITIONAL_BRANCH, LOOP, SHOW_CHOICE}
CLOSERS = {END_BRANCH, END_LOOP, SHOW_CHOICE_END}

# Branch labels sit at the indent of the command that opened the block, not
# inside it: an "else" or a choice label is a divider, not a statement.
LABELS = {ELSE_BRANCH, SHOW_CHOICE_OPTION}

# The engine's "no track" sentinel, which is not a missing file.
SILENCE = {"", "(OFF)"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        lines = []
        for text in self.errors:
            lines.append(f"  ERROR  {text}")
        for text in self.warnings:
            lines.append(f"  warn   {text}")
        return "\n".join(lines)


class Assets:
    """What is actually on disk, by the names RPG Maker will look them up by."""

    def __init__(self, game: Path):
        self.game = game
        self.charsets = self._names("CharSet", ".png")
        self.chipsets = self._names("ChipSet", ".png")
        self.pictures = self._names("Picture", ".png")
        self.music = self._names("Music", ".ogg") | self._names("Music", ".mp3")
        self.sounds = self._names("Sound", ".ogg") | self._names("Sound", ".wav")
        self.system = self._names("System", ".png")
        self.title = self._names("Title", ".png")
        self.gameover = self._names("GameOver", ".png")

    def _names(self, folder: str, suffix: str) -> set[str]:
        path = self.game / folder
        if not path.is_dir():
            return set()
        return {p.stem for p in path.glob(f"*{suffix}")}


def _walk(commands: list[Command], where: str, report: Report,
          assets: Assets, maps: dict[int, tuple[int, int]],
          common_ids: set[int], switches: set[int], variables: set[int],
          standable) -> None:
    """Check one command list."""
    depth = 0
    for position, cmd in enumerate(commands):
        code, params, text = cmd.code, list(cmd.params), cmd.string
        here = f"{where}[{position}]"

        if code in CLOSERS:
            depth -= 1
            if depth < 0:
                report.error(here, "closes a block that was never opened")
                depth = 0
        expected = depth - 1 if code in LABELS else depth
        if cmd.indent != expected:
            report.error(here, f"indent {cmd.indent} where the block depth "
                               f"is {expected} (code {code})")
        if code in OPENERS:
            depth += 1

        # -- assets -------------------------------------------------------
        if code == PLAY_BGM and text not in SILENCE:
            if text not in assets.music:
                report.error(here, f"plays missing track {text!r}")
        elif code == PLAY_SOUND and text not in SILENCE:
            if text not in assets.sounds:
                report.error(here, f"plays missing sound {text!r}")
        elif code == SHOW_PICTURE and text:
            if text not in assets.pictures:
                report.error(here, f"shows missing picture {text!r}")
        elif code == CHANGE_SPRITE and text:
            if text not in assets.charsets:
                report.error(here, f"sets missing charset {text!r}")

        # -- destinations -------------------------------------------------
        elif code == TELEPORT and len(params) >= 3:
            target, x, y = params[0], params[1], params[2]
            if target not in maps:
                report.error(here, f"teleports to map {target}, which does not exist")
            else:
                w, h = maps[target]
                if not (0 <= x < w and 0 <= y < h):
                    report.error(here, f"teleports to ({x},{y}) on map {target}, "
                                       f"which is {w}x{h}")
                elif not standable(target, x, y):
                    # The classic softlock: arrive inside a wall and the only
                    # way out is the title screen.
                    report.error(here, f"teleports into solid ground at "
                                       f"({x},{y}) on map {target}")
        elif code == CALL_EVENT and len(params) >= 2 and params[0] == 0:
            if params[1] not in common_ids:
                report.error(here, f"calls common event {params[1]}, "
                                   f"which does not exist")

        # -- state --------------------------------------------------------
        elif code == CONTROL_SWITCHES and len(params) >= 3:
            for switch_id in _range_of(params):
                if switch_id not in switches:
                    report.error(here, f"writes undeclared switch {switch_id}")
        elif code == CONTROL_VARS and len(params) >= 3:
            for var_id in _range_of(params):
                if var_id not in variables:
                    report.error(here, f"writes undeclared variable {var_id}")

    if depth != 0:
        report.error(where, f"ends with {depth} block(s) still open")


def _range_of(params: list[int]) -> range:
    """The id range a switch/variable command writes to.

    Mode 0 is a single id, mode 1 is a range; mode 2 addresses indirectly and
    cannot be checked statically.
    """
    if params[0] == 0:
        return range(params[1], params[1] + 1)
    if params[0] == 1:
        return range(params[1], params[2] + 1)
    return range(0)


def check(worlds, common_events, switches: dict[int, str],
          variables: dict[int, str], game: Path, *,
          system: dict | None = None) -> Report:
    """Validate the whole assembled game."""
    from .worlds.worlds import WORLD_ORDER

    report = Report()
    assets = Assets(game)
    maps = {worlds[k].map_id: (worlds[k].map.width, worlds[k].map.height)
            for k in WORLD_ORDER}
    common_ids = {e.ident for e in common_events}
    switch_ids, variable_ids = set(switches), set(variables)

    by_id = {worlds[k].map_id: worlds[k] for k in WORLD_ORDER}
    solids = {mid: solid_ids(w.chipset) for mid, w in by_id.items()}

    def standable(map_id: int, x: int, y: int) -> bool:
        world = by_id[map_id]
        solid = solids[map_id]
        return (world.map.get_lower(x, y) not in solid
                and world.map.get_upper(x, y) not in solid)

    for event in common_events:
        _walk(event.script.commands, f"common/{event.name}", report, assets,
              maps, common_ids, switch_ids, variable_ids, standable)

    for key in WORLD_ORDER:
        world = worlds[key]
        m = world.map
        if world.chipset.name not in assets.chipsets:
            report.error(key, f"uses missing chipset {world.chipset.name!r}")
        if world.overlay and world.overlay not in assets.pictures:
            report.error(key, f"wears missing overlay {world.overlay!r}")
        if world.music not in assets.music:
            report.error(key, f"plays missing track {world.music!r}")

        sx, sy = world.spawn
        if not (0 <= sx < m.width and 0 <= sy < m.height):
            report.error(key, f"spawns at ({sx},{sy}) on a {m.width}x{m.height} map")
        elif not standable(world.map_id, sx, sy):
            report.error(key, f"spawns inside solid ground at ({sx},{sy})")

        seen: dict[tuple[int, int], str] = {}
        for event in m.events:
            where = f"{key}/{event.name}"
            if not (0 <= event.x < m.width and 0 <= event.y < m.height):
                report.error(where, f"stands at ({event.x},{event.y}) outside "
                                    f"a {m.width}x{m.height} map")
            # Two events on one tile is legal but means one of them can never
            # be reached with the action key, which is almost never intended.
            spot = (event.x, event.y)
            if spot in seen:
                report.warn(where, f"shares tile {spot} with {seen[spot]!r}")
            else:
                seen[spot] = event.name

            for number, page in enumerate(event.pages, start=1):
                if page.charset and page.charset not in assets.charsets:
                    report.error(f"{where}#{number}",
                                 f"uses missing charset {page.charset!r}")
                # The engine only looks for action events on the same layer as
                # the player.  On any other layer the event exists, runs its
                # conditions, draws its sprite — and can never be talked to.
                if (page.trigger == TRIGGER_ACTION
                        and page.layer != LAYER_SAME):
                    report.error(f"{where}#{number}",
                                 "is action-triggered but not on the player's "
                                 "layer, so nothing can ever talk to it")
                _walk(page.script.commands, f"{where}#{number}", report, assets,
                      maps, common_ids, switch_ids, variable_ids, standable)

        # A world nobody can leave is a bug, not a statement.
        if key != "room" and not _has_exit(m):
            report.error(key, "has no teleport out of it")

    if system:
        for field_name, folder in (("system_graphic", assets.system),
                                   ("title_graphic", assets.title),
                                   ("gameover_graphic", assets.gameover)):
            name = system.get(field_name)
            if name and name not in folder:
                report.error("system", f"{field_name} {name!r} is missing")
        for field_name in ("title_music", "gameover_music"):
            name = system.get(field_name)
            if name not in SILENCE and name not in assets.music:
                report.error("system", f"{field_name} {name!r} is missing")
        for field_name in ("cursor_se", "decision_se", "cancel_se",
                           "buzzer_se", "item_se"):
            name = system.get(field_name)
            if name not in SILENCE and name not in assets.sounds:
                report.error("system", f"{field_name} {name!r} is missing")

    return report


def _has_exit(m) -> bool:
    for event in m.events:
        for page in event.pages:
            for cmd in page.script.commands:
                if cmd.code == TELEPORT:
                    return True
    return False
