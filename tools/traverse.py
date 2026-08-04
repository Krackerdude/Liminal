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


# Arrive, let the fade and the arrival event finish, turn to face the door
# (the door is solid, so this only turns), then open it and wait out the
# transition on the other side.
WALK_OUT = [
    (150, []),
    (24, [UP]),
    (12, []),
    (10, [DECISION]),
    (300, []),
]


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

    print(f"  walking out of {len(keys)} world(s)\n")
    failures = 0
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
        print(f"  {failures} of {len(keys)} worlds could not be left")
        return 1
    print(f"  all {len(keys)} worlds can be left through their door")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
