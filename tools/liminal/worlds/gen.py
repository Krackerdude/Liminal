"""Layout helpers for looping worlds.

Every dream is a torus: walk off the right edge and you arrive at the left,
walk off the bottom and you arrive at the top.  That single fact drives all of
this code.

Two consequences worth stating, because they are what make the loop invisible:

*Placement wraps.*  :class:`Placer` measures distance the short way round, and
:func:`stamp` writes through ``Map.set_lower``, which is already modular — so a
landmark straddling an edge is automatically drawn on both sides and the seam
has nothing to give away.

*Emptiness is the content.*  These generators deliberately place very few
things.  A world with five landmarks in a hundred tiles reads as enormous;
the same world with fifty reads as a level.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from ..art.chipsets import TileGrid
from ..maps import Map


def wrapped_delta(a: int, b: int, size: int) -> int:
    """Shortest signed distance from ``a`` to ``b`` around a loop of ``size``."""
    d = (b - a) % size
    return d - size if d > size // 2 else d


class Placer:
    """Keeps track of what is occupied, measuring distances around the loop."""

    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.taken: set[tuple[int, int]] = set()
        self.landmarks: list[tuple[int, int, str]] = []

    def free(self, x: int, y: int, w: int, h: int, pad: int = 1) -> bool:
        for dy in range(-pad, h + pad):
            for dx in range(-pad, w + pad):
                if ((x + dx) % self.w, (y + dy) % self.h) in self.taken:
                    return False
        return True

    def mark(self, x: int, y: int, w: int, h: int, name: str = "") -> None:
        for dy in range(h):
            for dx in range(w):
                self.taken.add(((x + dx) % self.w, (y + dy) % self.h))
        if name:
            self.landmarks.append((x % self.w, y % self.h, name))

    def clear_area(self, x: int, y: int, w: int, h: int) -> None:
        for dy in range(h):
            for dx in range(w):
                self.taken.discard(((x + dx) % self.w, (y + dy) % self.h))


def stamp(m: Map, grid: TileGrid, x: int, y: int) -> None:
    """Place a multi-tile object with its top-left at (x, y).

    Coordinates wrap, so an object placed near an edge spills onto the far
    side and the join is hidden by the object itself.
    """
    setter = m.set_upper if grid.upper else m.set_lower
    for col, row, tile_id in grid:
        if tile_id:
            setter(x + col, y + row, tile_id)


def stamp_centered(m: Map, grid: TileGrid, cx: int, cy: int) -> None:
    stamp(m, grid, cx - grid.cols // 2, cy - grid.rows // 2)


def fill_ground(m: Map, tiles: dict[str, int], rng: random.Random, *,
                base: str = "ground", second: str = "ground_b",
                second_chance: float = 0.10,
                decal_chance: float = 0.012) -> None:
    """Lay the floor, with a scattering of the world's own ground marks.

    The decals are rare on purpose: they are landmarks, and a landmark that
    appears every few steps stops being one.
    """
    decals = [tiles[k] for k in ("decal_0", "decal_1", "decal_2") if k in tiles]
    for y in range(m.height):
        for x in range(m.width):
            roll = rng.random()
            if decals and roll < decal_chance:
                m.set_lower(x, y, rng.choice(decals))
            elif roll < decal_chance + second_chance:
                m.set_lower(x, y, tiles[second])
            else:
                m.set_lower(x, y, tiles[base])


def scatter(m: Map, placer: Placer, grid: TileGrid, rng: random.Random,
            count: int, *, pad: int = 2, tries: int = 60,
            name: str = "") -> list[tuple[int, int]]:
    """Drop ``count`` copies of an object anywhere they fit."""
    placed = []
    for _ in range(count):
        for _ in range(tries):
            x = rng.randrange(m.width)
            y = rng.randrange(m.height)
            if placer.free(x, y, grid.cols, grid.rows, pad):
                stamp(m, grid, x, y)
                placer.mark(x, y, grid.cols, grid.rows, name)
                placed.append((x, y))
                break
    return placed


def lattice(m: Map, placer: Placer, grid: TileGrid, rng: random.Random, *,
            spacing_x: int, spacing_y: int, jitter: int = 3,
            skip: float = 0.0, name: str = "") -> list[tuple[int, int]]:
    """Place an object on a jittered grid.

    This is the false-scale trick: a landmark repeating at a fixed interval
    reads as *distance travelled* rather than as repetition, and the jitter
    stops the eye from locking on to the period.
    """
    placed = []
    for gy in range(0, m.height, spacing_y):
        for gx in range(0, m.width, spacing_x):
            if rng.random() < skip:
                continue
            x = gx + rng.randint(-jitter, jitter)
            y = gy + rng.randint(-jitter, jitter)
            if placer.free(x, y, grid.cols, grid.rows, 1):
                stamp(m, grid, x, y)
                placer.mark(x, y, grid.cols, grid.rows, name)
                placed.append((x % m.width, y % m.height))
    return placed


def patch(m: Map, tile: int, cx: int, cy: int, radius: float,
          rng: random.Random, ragged: float = 0.35) -> None:
    """A soft round patch of a different ground tile."""
    r = int(math.ceil(radius))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy)
            if d <= radius * (1 - ragged * rng.random()):
                m.set_lower(cx + dx, cy + dy, tile)


def trail(m: Map, tile: int, x: int, y: int, length: int, rng: random.Random,
          *, width: int = 2, wander: float = 0.35) -> tuple[int, int]:
    """A meandering path.  Ends wherever it ends; nothing follows it."""
    angle = rng.uniform(0, math.tau)
    fx, fy = float(x), float(y)
    for _ in range(length):
        angle += rng.uniform(-wander, wander)
        fx += math.cos(angle)
        fy += math.sin(angle)
        for dy in range(width):
            for dx in range(width):
                m.set_lower(int(fx) + dx, int(fy) + dy, tile)
    return int(fx) % m.width, int(fy) % m.height


# --- mazes -------------------------------------------------------------------

@dataclass
class MazeSpec:
    cells_x: int
    cells_y: int
    cell: int = 5           # tiles per cell, including one wall
    seed: int = 0


def toroidal_maze(spec: MazeSpec) -> set[tuple[int, int]]:
    """Carve a perfect maze whose edges connect around the loop.

    Returns the set of *wall* tile coordinates.  Because neighbours are taken
    modulo the cell grid, corridors run off one side and continue on the other,
    which is what stops the maze from having a detectable border.
    """
    rng = random.Random(spec.seed)
    cx, cy = spec.cells_x, spec.cells_y
    visited = [[False] * cx for _ in range(cy)]
    # Walls between cell (x,y) and its east/south neighbour.
    east = [[True] * cx for _ in range(cy)]
    south = [[True] * cx for _ in range(cy)]

    stack = [(rng.randrange(cx), rng.randrange(cy))]
    visited[stack[0][1]][stack[0][0]] = True
    while stack:
        x, y = stack[-1]
        options = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = (x + dx) % cx, (y + dy) % cy
            if not visited[ny][nx]:
                options.append((dx, dy, nx, ny))
        if not options:
            stack.pop()
            continue
        dx, dy, nx, ny = rng.choice(options)
        if dx == 1:
            east[y][x] = False
        elif dx == -1:
            east[ny][nx] = False
        elif dy == 1:
            south[y][x] = False
        else:
            south[ny][nx] = False
        visited[ny][nx] = True
        stack.append((nx, ny))

    # A few extra openings, so the maze has loops and no dead-end feels final.
    for _ in range((cx * cy) // 6):
        x, y = rng.randrange(cx), rng.randrange(cy)
        (east if rng.random() < 0.5 else south)[y][x] = False

    walls: set[tuple[int, int]] = set()
    size = spec.cell
    for y in range(cy):
        for x in range(cx):
            ox, oy = x * size, y * size
            # the corner post is always solid
            walls.add((ox, oy))
            if east[y][x]:
                for i in range(1, size):
                    walls.add((ox, oy + i))
            if south[y][x]:
                for i in range(1, size):
                    walls.add((ox + i, oy))
    return walls


def render_walls(m: Map, walls: set[tuple[int, int]], *, face: int, cap: int,
                 shadow: int | None = None) -> None:
    """Draw a wall set, capping the tiles whose north side is open.

    The cap is what gives a top-down maze its sense of height: a wall you can
    see the top of reads as a wall, and one you cannot reads as paint.
    """
    for x, y in walls:
        open_above = (x, (y - 1) % m.height) not in walls
        m.set_lower(x, y, cap if open_above else face)
    if shadow is not None:
        for x, y in walls:
            if (x, (y + 1) % m.height) not in walls:
                m.set_upper(x, y + 1, shadow)


def carve(walls: set[tuple[int, int]], x: int, y: int, w: int, h: int,
          width: int, height: int) -> None:
    """Knock a hole in a wall set — for rooms, clearings and doorways."""
    for dy in range(h):
        for dx in range(w):
            walls.discard(((x + dx) % width, (y + dy) % height))


def open_space(walls: set[tuple[int, int]], rng: random.Random, width: int,
               height: int, count: int, size: tuple[int, int] = (5, 9)
               ) -> list[tuple[int, int]]:
    """Clear a few rooms out of a maze, so it is not corridors all the way."""
    rooms = []
    for _ in range(count):
        w = rng.randint(*size)
        h = rng.randint(*size)
        x = rng.randrange(width)
        y = rng.randrange(height)
        carve(walls, x, y, w, h, width, height)
        rooms.append(((x + w // 2) % width, (y + h // 2) % height))
    return rooms


def free_spot(m: Map, placer: Placer, rng: random.Random, *, w: int = 1,
              h: int = 1, pad: int = 1, tries: int = 400,
              solid: set[int] | None = None) -> tuple[int, int]:
    """Find somewhere an event can stand without being inside scenery."""
    for _ in range(tries):
        x, y = rng.randrange(m.width), rng.randrange(m.height)
        if not placer.free(x, y, w, h, pad):
            continue
        if solid is not None and m.get_lower(x, y) in solid:
            continue
        return x, y
    return rng.randrange(m.width), rng.randrange(m.height)
