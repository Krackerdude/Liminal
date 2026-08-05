#!/usr/bin/env python3
"""Save the game in the engine, load it back, and check it came back.

A save that writes but restores you to the wrong map is indistinguishable from
one that works until somebody actually reloads it, which is usually long after
the change that broke it.  So this plays the real menu: opens it, walks down
to save, picks a night, then relaunches the Player with --load-game-id and
reads which map it reports.

Menu taps are short on purpose.  RPG Maker's menus repeat-fire while a
direction is held, so a thirty-frame press moves the cursor twice and lands on
"quit" instead of "save" — which looks exactly like saving being broken.

Usage::

    python3 tools/saveload.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from smoke import find_player, staged_game                      # noqa: E402
from traverse import frames                                     # noqa: E402

DOWN, DECISION, CANCEL = 1, 4, 5
LOADED = re.compile(r"Loaded Map Map(\d{4})\.lmu")

# things / effects / equipment / save / quit — three steps down to save.
TO_SAVE = ([(300, [])] + [(90, [CANCEL]), (60, [])]
           + [(6, [DOWN]), (50, [])] * 3
           + [(60, [DECISION]), (80, []), (60, [DECISION]), (240, [])])


def play(player: Path, game: Path, tmp: Path, script, extra=()) -> str:
    log = tmp / "player.log"
    (tmp / "input.log").write_text(frames(script))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    cmd = [str(player), "--project-path", str(game), "--no-audio", "--no-vsync",
           "--window", "--replay-input", str(tmp / "input.log"),
           "--save-path", str(tmp), "--log-file", str(log), *extra]
    try:
        subprocess.run(cmd, env=env, timeout=20, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass
    return log.read_text(errors="replace") if log.exists() else ""


def main() -> int:
    from liminal.worlds import worlds as W

    player = find_player()
    worlds = W.build_all()
    want = worlds["pink"].map_id

    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        first, second = Path(a), Path(b)
        stage = staged_game(worlds, "pink", first)
        play(player, stage, first, TO_SAVE, extra=["--new-game"])

        saves = sorted(first.glob("Save*.lsd"))
        print(f"  wrote {[s.name for s in saves] or 'nothing'}")
        if not saves:
            print("\n  the game could not be saved")
            return 1

        for save in saves:
            shutil.copy(save, second / save.name)
        log = play(player, stage, second, [(400, [])],
                   extra=["--load-game-id", "1"])
        maps = [int(m) for m in LOADED.findall(log)]
        errors = [l.split("] ")[-1] for l in log.splitlines() if "Error" in l]

    print(f"  loaded map {maps[0] if maps else 'nothing'} "
          f"(saved in {want})")
    for line in errors[:3]:
        print(f"  ERROR {line}")
    if not maps or maps[0] != want or errors:
        print("\n  the save did not come back intact")
        return 1
    print("\n  save and load round-trips through the engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
