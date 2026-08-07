"""The keyboard, by way of Ineluki's Key Patch.

RPG Maker 2000's own Key Input Processing reads seven buttons and no more:
four directions, decision, cancel, shift.  Four of those are how you walk, so
a 2000 game has *three* keys to spend on everything that is not walking.
Remapping does not help — it changes which physical key produces one of those
seven signals, it does not make an eighth.

The patch RPG Maker 2000 games actually used for this was Ineluki's Key
Patch, and EasyRPG Player implements it (``src/game_ineluki.cpp``).  It works
sideways, the way everything in this engine works sideways:

* The game ships a small INI-shaped **script** naming the keys it cares about
  and a number to emit for each one.
* When a key is pressed the patch pushes that number onto a queue.
* The game reads the queue through **Control Variables -> Other -> MIDI play
  position**, which the patch hijacks: instead of the music's position it pops
  and returns the next queued number, or ``-1`` when the queue is empty.

So the whole keyboard arrives through a single variable, one press at a time,
and the seven-button ceiling stops being a ceiling.  Sixty-one keys are
available; the ones this game uses are listed in :data:`KEYS`.

Two consequences worth knowing before adding keys here:

**W, A, S and D stop being movement.**  ``enablekeysupport`` masks those four
in the engine's own input so a game can use them as letters
(``game_ineluki.cpp``, ``mask_kb``).  LIMINAL is played on the arrow keys, so
this costs nothing, but it is not optional and it is not configurable.

**There are no function keys.**  Ineluki's table has letters, digits, Tab,
Escape, Enter, Space, Backspace, the editing cluster and the modifiers — no
F1..F12.  Anything that wants a key wants one of those.
"""

from __future__ import annotations

from dataclasses import dataclass

# Where the queue is read from: the "other" operand of Control Variables,
# attribute 8, nominally the MIDI playback position.
MIDI_TICKS = 8

# What the queue returns when there is nothing left in it.
EMPTY = -1

# How many presses to take in one frame.  The queue is drained in a loop, and
# a loop that trusts EMPTY to stop it is a loop that never stops if the patch
# is switched off: with the patch off, attribute 8 is the *real* MIDI position,
# which counts upward and is never negative.  That would hang the game rather
# than merely disabling a key.  The counter is the difference between "the
# extra keys do nothing" and "the game freezes on the title screen".
#
# With the patch off the drain also reads music positions where it expects key
# numbers, so a track that happens to pass through one of the values below
# would fire that key once.  Hence values in the nine thousands: a track has to
# run for a couple of minutes to reach them, and it can only do it once.
DRAIN = 6


@dataclass(frozen=True)
class Key:
    """One physical key, and the number pressing it puts on the queue."""

    ineluki: str        # the name Ineluki's script language knows it by
    value: int          # what the queue emits; must be >= 0 and unique
    does: str           # what it is for, for the script's comments


# Keys the Player has already spoken for, and must not be given a second job.
#
# The patch reads the *physical* key, underneath the engine's own input layer,
# so a key that is already bound does both things at once.  The first version
# of this put the coordinates readout on C, which the Player binds to CANCEL
# (``input_buttons_desktop.cpp``): pressing it opened the menu on top of the
# readout every time, and the readout was only visible after backing out of a
# menu nobody asked for.  That is not a collision this game can detect at
# runtime -- so it is checked here, at build time, against what the Player
# actually binds.
#
# Read off ``Input::GetDefaultButtonMappings()``.  Only the entries that are
# also names Ineluki knows are listed; function keys and the mouse cannot
# collide because Ineluki cannot see them.
TAKEN = {
    "w": "up", "k": "up", "s": "down", "j": "down",
    "a": "left", "h": "left", "d": "right", "l": "right",
    "z": "decision", "(space)": "decision", "(enter)": "decision",
    "x": "cancel", "c": "cancel", "v": "cancel", "b": "cancel",
    "n": "cancel", "(esc)": "cancel",
    "(lshift runter)": "shift", "(rshift runter)": "shift",
    "(lshift hoch)": "shift", "(rshift hoch)": "shift",
    "f": "fast forward", "g": "fast forward",
    "(strg)": "walk through walls", "(alt)": "walk through walls",
    "(bildhoch)": "page up", "(bildrunter)": "page down",
    ".": "the 2003 keypad",
}

# Free, and worth knowing about before reaching for one:
#
#   digits 0-9   bound only to the 2003 number buttons, which a 2000 game
#                never reads.  The natural home for the television's channels.
#   e i m o p    the letters nothing else wants
#   q r t u y
#   (tab)        bound to nothing at all
#   (entf) (ende) (pos1) (einfg) (capslock) (numlock) (scrolllock)
#
# W A S D are listed as taken above and are *also* masked by the patch, which
# is a contradiction the engine resolves in the patch's favour: with key
# support on they stop moving the player.  They are still not free -- a player
# who walks with WASD has already lost them, and giving them a second job
# would make that worse rather than better.


# Values start high on purpose.  If the patch is ever off, attribute 8 returns
# a real MIDI position, and a track that has just started sits at 0, 1, 2...
# Small values would be indistinguishable from a keypress for the first few
# frames of every song.  Nothing plays for nine thousand ticks before the
# player has had a chance to notice something is wrong.
KEYS: tuple[Key, ...] = (
    Key("(tab)", 9001, "things i found"),
    Key("p", 9002, "where am i"),          # p for position; c was cancel
)

_clash = {k.ineluki: TAKEN[k.ineluki] for k in KEYS if k.ineluki in TAKEN}
if _clash:
    raise SystemExit(
        "keys.py: these are already engine buttons and would fire twice: "
        + ", ".join(f"{k} ({why})" for k, why in sorted(_clash.items())))
if len({k.value for k in KEYS}) != len(KEYS):
    raise SystemExit("keys.py: two keys share a queue value")

# The list file the Player reads at boot, and the script it names.  Both sit
# at the top of the game folder; paths in the list are relative to it.
LIST_FILE = "autorun.script"
SCRIPT_FILE = "liminal.script"


def script() -> str:
    """The key script itself.

    Ineluki scripts are INI files where each section performs one action and
    names the next in ``next``; the chain starts at ``[execute]`` and ends
    when a section names no successor.  Sections are numbered rather than
    named after their key so that renaming a key cannot break the chain.
    """
    blocks: list[tuple[str, list[str]]] = []

    # Switch the MIDI-position variable over to reading the key queue.  Until
    # this runs, reading it gives the music's position, which is what it says
    # on the tin and not what this game wants.
    blocks.append(("execute", ["action=miditickfunction", "command=output"]))
    blocks.append((None, ["action=enablekeysupport", "enable=true"]))
    for key in KEYS:
        blocks.append((None, [f"; {key.does}",
                              "action=registerkeydownevent",
                              f"key={key.ineluki}",
                              f"value={key.value}"]))

    out: list[str] = []
    for index, (name, lines) in enumerate(blocks):
        section = name or f"step{index}"
        following = f"step{index + 1}" if index + 1 < len(blocks) else None
        out.append(f"[{section}]")
        out.extend(lines)
        if following:
            out.append(f"next={following}")
        out.append("")
    return "\n".join(out)


def script_list() -> str:
    """``autorun.script``: the scripts to run at boot, one path per line."""
    return SCRIPT_FILE + "\n"


def ini() -> str:
    """``EasyRPG.ini``: turns the patch on without a command-line flag.

    The Player reads this out of the game folder itself
    (``game_config_game.cpp``), so a player who unzips the game and
    double-clicks it gets the keyboard with no setup and nothing to explain.
    """
    return ("[Patch]\n"
            "KeyPatch=1\n")
