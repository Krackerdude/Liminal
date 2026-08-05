#!/usr/bin/env python3
"""Measure how much each character actually changes when it turns.

Four facings exist for every design in the game, but existing is not the same
as differing.  The creature draws in particular shift an eye two pixels and
call that a new view, so a cone seen from behind is a cone seen from in front.
This reports the share of pixels that change between front and back, and
between left and right, and fails any design that does not really turn.

A design passes at 12% on both axes — enough that the silhouette or the
features have genuinely changed rather than a highlight having moved.

Usage::

    python3 tools/facings.py            # every design, worst first
    python3 tools/facings.py --strict   # exit non-zero if any design fails
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from liminal.art.cast import WORLD_CAST, _sheets              # noqa: E402
from liminal.art.charsets import (Body, CELL_H, CELL_W, creature_block,
                                  draw_figure)                # noqa: E402

THRESHOLD = 12.0


def views(spec) -> list[np.ndarray]:
    if isinstance(spec, Body):
        return [draw_figure(spec, f, 1).px for f in range(4)]
    block = creature_block(spec)
    return [block.sub(CELL_W, f * CELL_H, CELL_W, CELL_H).px for f in range(4)]


def changed(a: np.ndarray, b: np.ndarray) -> float:
    return 100.0 * float(np.mean(np.any(a != b, axis=-1)))


def main() -> int:
    parser = argparse.ArgumentParser(description="How much does each design turn?")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    spec = {n: s for entries in _sheets().values() for n, s in entries}
    rows = []
    for world, names in WORLD_CAST.items():
        for name in names:
            v = views(spec[name])
            rows.append((world, name, changed(v[2], v[0]), changed(v[1], v[3])))
    rows.sort(key=lambda r: min(r[2], r[3]))

    print(f"  {'world':<11}{'design':<19}{'front/back':>11}{'left/right':>12}")
    print("  " + "-" * 53)
    failed = 0
    for world, name, back, side in rows:
        bad = back < THRESHOLD or side < THRESHOLD
        failed += bad
        print(f"  {world:<11}{name:<19}{back:>10.0f}%{side:>11.0f}%"
              f"{'   <- barely turns' if bad else ''}")
    print(f"\n  {failed} of {len(rows)} designs do not really turn "
          f"(under {THRESHOLD:.0f}% on an axis)")
    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
