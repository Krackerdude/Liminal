#!/usr/bin/env python3
"""Render each world from above, with every resident marked.

A screenshot shows twenty tiles of a world that is a hundred and fifty across,
which is exactly the wrong scale for judging where people are.  This draws the
whole map at a few pixels per tile — every tile coloured by what it actually
looks like in the chipset — and puts a marker on each event, so the *pattern*
of a population is visible: clustered, scattered, or absent.

Usage::

    python3 tools/overview.py                 # every world, into /tmp/overview
    python3 tools/overview.py --scale 4
    python3 tools/overview.py --world neon
"""

from __future__ import annotations

import argparse
import random
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liminal.art.canvas import Canvas, save_indexed        # noqa: E402
from liminal.art.chipsets import (BLOCK_A, BLOCK_C, BLOCK_E, BLOCK_F, TILE,
                                  _block_e_cell, _block_f_cell)  # noqa: E402
from liminal.worlds import events, worlds as W             # noqa: E402

# What each kind of marker means.
DOOR = (255, 80, 80)
EFFECT = (255, 230, 90)
RESIDENT = (90, 255, 255)
OTHER = (255, 140, 240)


def tile_patch(sheet: Canvas, tile_id: int, scale: int) -> np.ndarray | None:
    """The real artwork of one tile, sampled down to ``scale`` pixels square.

    Averaging a tile to a single colour turns a hundred-and-fifty-tile world
    into a hundred-and-fifty-pixel smudge — a heatmap of where things are,
    which is useless for looking at what they *are*.  This keeps the art and
    only drops resolution.
    """
    if tile_id >= BLOCK_F:
        col, row = _block_f_cell(tile_id - BLOCK_F)
    elif tile_id >= BLOCK_E:
        col, row = _block_e_cell(tile_id - BLOCK_E)
    elif tile_id >= BLOCK_C:
        col, row = 3 + (tile_id - BLOCK_C) // 50, 4
    elif tile_id == BLOCK_A:
        col, row = 0, 4
    else:
        return None
    patch = sheet.px[row * TILE:(row + 1) * TILE, col * TILE:(col + 1) * TILE]
    step = max(1, TILE // scale)
    return patch[::step, ::step][:scale, :scale]


TRANS = np.array((255, 0, 255), np.uint8)


def render(world, scale: int) -> Canvas:
    m, sheet = world.map, world.chipset.sheet
    art = Canvas(m.width * scale, m.height * scale, (0, 0, 0))
    cache: dict[int, np.ndarray | None] = {}

    def patch(tile_id: int) -> np.ndarray | None:
        if tile_id not in cache:
            cache[tile_id] = tile_patch(sheet, tile_id, scale)
        return cache[tile_id]

    for y in range(m.height):
        for x in range(m.width):
            px, py = x * scale, y * scale
            low = patch(m.get_lower(x, y))
            if low is not None:
                art.px[py:py + scale, px:px + scale] = low
            up = patch(m.get_upper(x, y))
            if up is not None:
                solid = np.any(up != TRANS, axis=-1)
                target = art.px[py:py + scale, px:px + scale]
                target[solid] = up[solid]

    # Markers sit on top, ringed in black and white so they stay legible on a
    # world whose own palette is fluorescent.
    residents = set(_resident_names(world.key))
    for event in m.events:
        base = event.name.rsplit(" ", 1)[0]
        if event.name == "door":
            kind = DOOR
        elif event.name.startswith("effect"):
            kind = EFFECT
        elif base in residents:
            kind = RESIDENT
        elif event.name == "arrive":
            continue
        else:
            kind = OTHER
        size = scale + 2
        px, py = event.x * scale - 1, event.y * scale - 1
        art.rect(px, py, size, size, (0, 0, 0))
        art.rect(px + 1, py + 1, size - 2, size - 2, kind)
        art.rect(px + 2, py + 2, max(1, size - 4), max(1, size - 4), (255, 255, 255))
    return art


def _resident_names(key: str) -> list[str]:
    from liminal.art.cast import WORLD_CAST
    return WORLD_CAST.get(key, [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Draw every world from above")
    parser.add_argument("--scale", type=int, default=8,
                        help="pixels per tile")
    parser.add_argument("--world", default=None)
    parser.add_argument("--out", type=Path, default=Path("/tmp/overview"))
    args = parser.parse_args()

    worlds = W.build_all()
    events.room_events(worlds["room"], worlds)
    events.nexus_events(worlds["nexus"], worlds)
    for key in W.DREAM_ORDER:
        events.dream_events(worlds[key], worlds,
                            random.Random(zlib.crc32(f"events:{key}".encode())))

    args.out.mkdir(parents=True, exist_ok=True)
    keys = [args.world] if args.world else W.WORLD_ORDER
    for index, key in enumerate(keys):
        world = worlds[key]
        art = render(world, args.scale)
        path = args.out / f"{world.map_id:02d}_{key}.png"
        save_indexed(art, str(path), transparent=False, max_colors=255)
        people = W.POPULATION.get(key, 0)
        print(f"  {key:<11} {world.map.width:>3}x{world.map.height:<3} "
              f"{people:>3} residents  -> {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
