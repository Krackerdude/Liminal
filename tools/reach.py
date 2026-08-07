#!/usr/bin/env python3
"""Report everything in the game the player cannot actually get to.

A thin command line over ``liminal.worlds.reach``, which is also what the
build validator uses -- so this and the build always agree.

Usage::

    python3 tools/reach.py                  # every world
    python3 tools/reach.py --world faces    # one
    python3 tools/reach.py --verbose        # name them
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liminal.worlds import reach                                     # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Reachability audit")
    parser.add_argument("--world", default="", help="check only this world")
    parser.add_argument("--verbose", action="store_true",
                        help="name every stranded object")
    parser.add_argument("--limit", type=int, default=10,
                        help="how many to name per world")
    args = parser.parse_args()

    import build
    from liminal.worlds import worlds as W

    # Events are authored after the maps are generated, and events are most of
    # what this checks -- a world straight out of build_all has nothing in it.
    worlds = W.build_all()
    build.author_events(worlds)
    keys = [args.world] if args.world else list(W.WORLD_ORDER)

    total = 0
    rows = []
    for key in keys:
        world = worlds[key]
        open_tiles = reach.walkable(world)
        bad = reach.stranded(world, open_tiles)
        total += len(bad)
        if bad:
            rows.append((key, bad, len(reach.objects(world)), len(open_tiles)))

    print(f"\n  {'world':<12}{'stranded':>9}{'of':>7}{'floor':>9}")
    print("  " + "-" * 40)
    for key, bad, count, floor in rows:
        print(f"  {key:<12}{len(bad):>9}{count:>7}{floor:>9}")
        if args.verbose:
            for name, x, y, why in bad[:args.limit]:
                print(f"      {name:<28} ({x:>3},{y:>3})  {why}")
            if len(bad) > args.limit:
                print(f"      ... and {len(bad) - args.limit} more")
    print("  " + "-" * 40)
    print(f"  {total} unreachable across {len(rows)} worlds\n")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
