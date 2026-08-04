#!/usr/bin/env python3
"""Boot every map in the real engine and report what it complained about.

The build script proves the files parse.  This proves the Player will actually
run them: it starts a new game on each map in turn with video and audio
stubbed out, and reads back the diagnostics.

EasyRPG Player fails soft — a missing chipset is a black screen, a missing
charset is an invisible NPC, and neither stops the game — so every "Cannot
find" and every warning is treated as a failure here.  Faults that only show
up as an absence are exactly the ones that survive a play-test.

Usage::

    python3 tools/smoke.py                 # every map
    python3 tools/smoke.py --seconds 8     # let each map run longer
    python3 tools/smoke.py --map 9         # just one
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

GAME = ROOT / "game"

PLAYER_CANDIDATES = [
    ROOT / "tools" / "bin" / "easyrpg-player",
    Path("/tmp/claude-0/-home-user-Liminal/02fe31f5-4798-502e-89e5-55e7690bfc21"
         "/scratchpad/Player/build/easyrpg-player"),
]

# Noise from running headless in a container, not from the game.
IGNORE = [
    re.compile(r"Couldn't open audio"),
    re.compile(r"wine prefix not found"),
    re.compile(r"Cannot find: Font/"),
    re.compile(r"Cannot find: Logo/"),
    re.compile(r"Cannot find RPG_RT"),
    re.compile(r"Could not get the size of RPG_RT"),
]

INTERESTING = re.compile(r"\b(Warning|Error|Cannot find|Failed)\b")


def find_player() -> Path:
    for path in PLAYER_CANDIDATES:
        if path.exists() and os.access(path, os.X_OK):
            return path
    raise SystemExit("easyrpg-player not found; build it or drop it at "
                     "tools/bin/easyrpg-player")


SHOT_CONFIG = """[Player]
AutomaticScreenshots=1
AutomaticScreenshotsInterval=1
ScreenshotScale=2
ScreenshotTimestamp=0
"""


def boot(player: Path, map_id: int, seconds: int,
         shot: Path | None = None) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="smoke-") as tmp:
        log = Path(tmp) / "player.log"
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        cmd = [str(player), "--project-path", str(GAME), "--no-audio",
               "--new-game", "--no-vsync", "--window",
               "--save-path", tmp, "--log-file", str(log)]
        if map_id:
            cmd += ["--start-map-id", str(map_id)]
        if shot is not None:
            # The Player has no screenshot flag, but it will take one on a
            # timer if the config asks it to, and it writes them next to the
            # saves.  That is the only way to see this game rendered by the
            # thing that will actually render it.
            config = Path(tmp) / "config"
            config.mkdir()
            (config / "config.ini").write_text(SHOT_CONFIG)
            cmd += ["--config-path", str(config)]
        try:
            subprocess.run(cmd, env=env, timeout=seconds,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass          # the expected outcome: it ran until we stopped it
        if shot is not None:
            # Keep the last frame: the first few are still fading in.
            shots = sorted(Path(tmp).glob("auto_*.png"),
                           key=lambda p: int(p.stem.split("_")[1]))
            if shots:
                shot.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(shots[-1], shot)
        if not log.exists():
            return ["player wrote no log at all"]
        lines = log.read_text(errors="replace").splitlines()

    out = []
    for line in lines:
        if not INTERESTING.search(line):
            continue
        if any(pattern.search(line) for pattern in IGNORE):
            continue
        out.append(line.split("] ", 1)[-1])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Boot every map in the Player")
    parser.add_argument("--seconds", type=int, default=6,
                        help="how long to let each map run")
    parser.add_argument("--map", type=int, default=0,
                        help="boot only this map id")
    parser.add_argument("--shots", type=Path, default=None,
                        help="write one in-engine screenshot per map into DIR")
    args = parser.parse_args()

    from liminal.worlds import worlds as W

    player = find_player()
    print(f"  player: {player}")
    print(f"  {args.seconds}s per map\n")

    if args.map:
        targets = [(f"map {args.map}", args.map)]
    else:
        targets = [(key, index) for index, key in
                   enumerate(W.WORLD_ORDER, start=1)]

    failures = 0
    for name, map_id in targets:
        shot = args.shots / f"{map_id:02d}_{name}.png" if args.shots else None
        problems = boot(player, map_id, args.seconds, shot)
        # The same complaint repeats every frame; say it once.
        unique = list(dict.fromkeys(problems))
        if unique:
            failures += 1
            print(f"  {name:<12} {len(unique)} problem(s)")
            for line in unique[:8]:
                print(f"      {line}")
            if len(unique) > 8:
                print(f"      ... and {len(unique) - 8} more")
        else:
            print(f"  {name:<12} ok")

    print()
    if failures:
        print(f"  {failures} of {len(targets)} maps had something to say")
        return 1
    print(f"  all {len(targets)} maps booted clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
