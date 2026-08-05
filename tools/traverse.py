#!/usr/bin/env python3
"""Walk out of every world, in the engine, and prove it landed.

The build script proves the files parse and `smoke.py` proves the maps load.
Neither of them presses a button. This does: it starts the game on a world's
real arrival tile, turns the player around to face the door they came out of,
opens it, and then reads the Player's own log to see which map it loaded next.

A door that is one tile off, an event sitting on a tile you cannot face, a
teleport that lands in a wall — none of those show up as a warning anywhere.
They show up as a player who cannot get home, and this is the only check in
the project that would notice.

Input is fed through EasyRPG's `--replay-input`, whose legacy format is one
line per frame holding the state of all 42 buttons as a bitstring, most
significant bit first.

Usage::

    python3 tools/traverse.py              # every world
    python3 tools/traverse.py --world neon
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build                                                     # noqa: E402
from smoke import find_player, staged_game                       # noqa: E402

# Index into EasyRPG's InputButton enum.
UP, DOWN, LEFT, RIGHT, DECISION, CANCEL = 0, 1, 2, 3, 4, 5
BUTTON_COUNT = 42

LOADED = re.compile(r"Loaded Map Map(\d{4})\.lmu")


def frames(script: list[tuple[int, list[int]]]) -> str:
    """Render (count, buttons) pairs as one bitstring line per frame."""
    lines = []
    for count, buttons in script:
        bits = ["0"] * BUTTON_COUNT
        for button in buttons:
            bits[BUTTON_COUNT - 1 - button] = "1"
        lines.extend(["".join(bits)] * count)
    return "\n".join(lines) + "\n"


# Frames to hold a direction so the engine registers a turn against a wall.
# Eight was not enough and produced a player standing correctly in front of a
# door that would not open — the failure looks identical to a broken door.
FACE = 24

# Long enough to cross any room and come to rest against the far wall.  Legs
# are expressed as "walk until something stops you" rather than as a tile
# count on purpose: a tile count is really a frame count, and it silently
# stopped being right the moment the walking speed was tuned.
UNTIL_BLOCKED = 140

# How long to settle after arriving, before touching anything.
SETTLE = 150


def until_blocked(button: int) -> tuple[int, list[int]]:
    return (UNTIL_BLOCKED, [button])


def walk(*legs: tuple[int, list[int]], face: int | None = None,
         presses: int = 1) -> list[tuple[int, list[int]]]:
    """Settle, walk the legs, turn to face the target, then act.

    The gaps are load-bearing: pressing decision on the same frame a direction
    is released catches the player mid-step and the press is swallowed.
    ``presses`` is for targets that answer with a message and a choice rather
    than acting immediately.
    """
    seq: list[tuple[int, list[int]]] = [(SETTLE, []), *legs]
    if face is not None:
        seq += [(12, []), (FACE, [face])]
    for _ in range(presses):
        seq += [(12, []), (10, [DECISION])]
    seq += [(300, [])]
    return seq


# Every world's own door stands directly above the tile you arrive on, so
# leaving is the same three beats everywhere: turn round, open it, wait.
WALK_OUT = walk(face=UP)

# The room: into the back wall, then along it until the bed stops us.  The bed
# asks before it does anything, so this needs the extra presses to get through
# the message and pick "yes".
TO_BED = walk(until_blocked(UP), (12, []), until_blocked(LEFT),
              face=LEFT, presses=4)

# The nexus: the first door is above the arrival tile, like every other door.
TO_FIRST_DOOR = walk(face=UP)


def run(player: Path, game: Path, input_log: Path, seconds: int) -> list[int]:
    """Play the recorded input and return the map ids the engine loaded.

    Waits for the *second* map load rather than for a fixed wall-clock time.
    A timeout that merely looks generous is a flake generator: killing the
    Player mid-run loses whatever it had buffered, so a machine under load
    reports a working door as a broken one.
    """
    with tempfile.TemporaryDirectory(prefix="traverse-") as tmp:
        log = Path(tmp) / "player.log"
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        cmd = [str(player), "--project-path", str(game), "--no-audio",
               "--new-game", "--no-vsync", "--window",
               "--replay-input", str(input_log),
               "--save-path", tmp, "--log-file", str(log)]
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        deadline = time.time() + seconds
        try:
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                if log.exists() and len(LOADED.findall(
                        log.read_text(errors="replace"))) >= 2:
                    break
                time.sleep(0.25)
        finally:
            if proc.poll() is None:
                proc.terminate()          # SIGTERM, so the log gets flushed
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        if not log.exists():
            return []
        return [int(m.group(1)) for m in LOADED.finditer(log.read_text(errors="replace"))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Walk out of every world")
    parser.add_argument("--world", default=None, help="only this world key")
    parser.add_argument("--seconds", type=int, default=25)
    args = parser.parse_args()

    from liminal.worlds import worlds as W

    player = find_player()
    worlds = W.build_all()
    keys = [args.world] if args.world else list(W.DREAM_ORDER)
    nexus_id = worlds["nexus"].map_id

    failures = 0

    if not args.world:
        # The two links that are not a dream's own door, checked the same way:
        # play the input, then ask the engine which map it loaded.
        print("  the way in\n")
        for label, key, script, expect in (
                ("room -> nexus", "room", TO_BED, worlds["nexus"].map_id),
                ("nexus -> pink", "nexus", TO_FIRST_DOOR, worlds["pink"].map_id)):
            with tempfile.TemporaryDirectory(prefix="stage-") as tmp:
                stage = staged_game(worlds, key, Path(tmp))
                log = Path(tmp) / "input.log"
                log.write_text(frames(script))
                loaded = run(player, stage, log, args.seconds)
            went = loaded[1:]
            if went and went[0] == expect:
                print(f"  {label:<16} ok")
            else:
                failures += 1
                print(f"  {label:<16} FAILED (loaded {loaded})")
        print()

    print(f"  walking out of {len(keys)} world(s)\n")
    for key in keys:
        world = worlds[key]
        with tempfile.TemporaryDirectory(prefix="stage-") as tmp:
            stage = staged_game(worlds, key, Path(tmp))
            input_log = Path(tmp) / "input.log"
            input_log.write_text(frames(WALK_OUT))
            loaded = run(player, stage, input_log, args.seconds)

        # The first load is the world itself; anything after it is where the
        # door took us.
        went = [m for m in loaded[1:]]
        if went and went[0] == nexus_id:
            print(f"  {key:<11} map {world.map_id:>2} -> nexus  ok")
        else:
            failures += 1
            where = went[0] if went else "nowhere"
            print(f"  {key:<11} map {world.map_id:>2} -> {where}  "
                  f"FAILED (loaded {loaded})")

    print()
    if failures:
        print(f"  {failures} link(s) broken")
        return 1
    print(f"  the loop closes: room -> nexus -> dream -> nexus, "
          f"and all {len(keys)} worlds can be left through their door")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
