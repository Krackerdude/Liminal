"""Dream architecture: zones, boundaries and corridors.

This module exists because of one mistake.  An earlier version of this project
generated worlds by scattering props across open ground, and the result read
as a level with decorations rather than as a place.  Nothing here places a
single prop; it builds the *shape* of a world first, and props come later.

The structural model is taken from how Yume Nikki's worlds are actually
assembled — Neon World is not objects on a field, it is octagonal chambers cut
out of black void, wrapped in thick patterned wall bands and joined by
corridors.  So:

1. Everything starts as :data:`VOID`.
2. Zones are **carved** out of it, each with a deliberate shape.
3. Zones are **connected** by corridors narrow enough to read as corridors.
4. Whatever touches the carved space becomes :data:`WALL` — a thick, visible
   boundary that contains the player.
5. Everything still untouched stays void, and the player can never reach it.

The player is roughly 1.5 tiles wide and 2 tall, and sees 20x15 tiles at once.
Every size in here is chosen against that.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

VOID = 0
FLOOR = 1
WALL = 2
FLOOR_ALT = 3      # a second floor tone, for marking sub-areas within a zone


@dataclass
class Zone:
    """One room of a dream, and everything the decorator needs to know."""
    name: str
    cx: int
    cy: int
    w: int
    h: int
    shape: str = "rect"
    tag: str = ""

    @property
    def left(self) -> int:
        return self.cx - self.w // 2

    @property
    def top(self) -> int:
        return self.cy - self.h // 2

    def contains(self, x: int, y: int, width: int, height: int) -> bool:
        dx = abs(((x - self.cx + width // 2) % width) - width // 2)
        dy = abs(((y - self.cy + height // 2) % height) - height // 2)
        return dx <= self.w // 2 and dy <= self.h // 2


class Field:
    """A torus of cell states, carved rather than filled."""

    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.cells = [[VOID] * width for _ in range(height)]
        self.zones: list[Zone] = []
        # Corridor tiles and their shoulders.  Nothing is ever allowed to be
        # placed here: a prop dropped in a doorway can cut a world in half,
        # and the player has no way to move it.
        self.protected: set[tuple[int, int]] = set()

    def get(self, x: int, y: int) -> int:
        return self.cells[y % self.h][x % self.w]

    def set(self, x: int, y: int, value: int) -> None:
        self.cells[y % self.h][x % self.w] = value

    # -- carving -------------------------------------------------------------
    def carve(self, zone: Zone, value: int = FLOOR) -> Zone:
        """Cut a zone's shape out of the void."""
        shape = zone.shape
        half_w, half_h = zone.w / 2, zone.h / 2
        for dy in range(-zone.h // 2 - 1, zone.h // 2 + 2):
            for dx in range(-zone.w // 2 - 1, zone.w // 2 + 2):
                if not _inside(shape, dx, dy, half_w, half_h):
                    continue
                self.set(zone.cx + dx, zone.cy + dy, value)
        self.zones.append(zone)
        return zone

    def protect(self, x: int, y: int, pad: int = 1) -> None:
        for dy in range(-pad, pad + 1):
            for dx in range(-pad, pad + 1):
                self.protected.add(((x + dx) % self.w, (y + dy) % self.h))

    def is_protected(self, x: int, y: int) -> bool:
        return ((x % self.w), (y % self.h)) in self.protected

    def corridor(self, a: tuple[int, int], b: tuple[int, int], *,
                 width: int = 3, bend: str = "hv") -> None:
        """Join two points with an L-shaped passage, the short way round.

        Corridors are three tiles wide by default: wide enough to walk without
        catching on corners, narrow enough that it still reads as a passage
        rather than as more room.
        """
        ax, ay = a
        bx, by = b
        dx = _short(ax, bx, self.w)
        dy = _short(ay, by, self.h)
        half = width // 2
        if bend == "hv":
            for i in range(abs(dx) + 1):
                x = ax + (1 if dx > 0 else -1) * i
                for o in range(-half, half + 1):
                    self.set(x, ay + o, FLOOR)
                    self.protect(x, ay + o, 1)
            for i in range(abs(dy) + 1):
                y = ay + (1 if dy > 0 else -1) * i
                for o in range(-half, half + 1):
                    self.set(bx + o, y, FLOOR)
                    self.protect(bx + o, y, 1)
        else:
            for i in range(abs(dy) + 1):
                y = ay + (1 if dy > 0 else -1) * i
                for o in range(-half, half + 1):
                    self.set(ax + o, y, FLOOR)
                    self.protect(ax + o, y, 1)
            for i in range(abs(dx) + 1):
                x = ax + (1 if dx > 0 else -1) * i
                for o in range(-half, half + 1):
                    self.set(x, by + o, FLOOR)
                    self.protect(x, by + o, 1)

    def long_hall(self, x: int, y: int, length: int, *, vertical: bool = False,
                  width: int = 3) -> tuple[int, int]:
        """A passage far longer than anything it connects.

        This is a boundary disguised as a route: walking it takes long enough
        that the player stops being sure the far end exists.
        """
        half = width // 2
        for i in range(length):
            for o in range(-half, half + 1):
                if vertical:
                    self.set(x + o, y + i, FLOOR)
                    self.protect(x + o, y + i, 0)
                else:
                    self.set(x + i, y + o, FLOOR)
                    self.protect(x + i, y + o, 0)
        return (x, y + length) if vertical else (x + length, y)

    def band(self, x: int, y: int, w: int, h: int, value: int = FLOOR_ALT) -> None:
        for dy in range(h):
            for dx in range(w):
                if self.get(x + dx, y + dy) != VOID:
                    self.set(x + dx, y + dy, value)

    def release_zone_interiors(self, keep_margin: int = 3) -> None:
        """Stop protecting the parts of a corridor that run inside a room.

        Corridors are carved centre-to-centre, so without this every room
        centre counts as a doorway and nothing can ever be placed there.  What
        actually needs protecting is the passage *between* rooms plus the few
        tiles either side of where it enters one.
        """
        inside: set[tuple[int, int]] = set()
        for zone in self.zones:
            half_w = max(1, zone.w // 2 - keep_margin)
            half_h = max(1, zone.h // 2 - keep_margin)
            for dy in range(-half_h, half_h + 1):
                for dx in range(-half_w, half_w + 1):
                    inside.add(((zone.cx + dx) % self.w,
                                (zone.cy + dy) % self.h))
        self.protected -= inside

    # -- boundaries ----------------------------------------------------------
    def build_walls(self, thickness: int = 2) -> None:
        """Grow a wall band around everything walkable.

        This is what makes a zone read as a room rather than as a clearing.
        The band is grown outward from the floor so it always follows the
        shape exactly, however strange that shape is.
        """
        frontier = {(x, y) for y in range(self.h) for x in range(self.w)
                    if self.cells[y][x] in (FLOOR, FLOOR_ALT)}
        for _ in range(thickness):
            nxt: set[tuple[int, int]] = set()
            for x, y in frontier:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx, ny = (x + dx) % self.w, (y + dy) % self.h
                    if self.cells[ny][nx] == VOID:
                        self.cells[ny][nx] = WALL
                        nxt.add((nx, ny))
            frontier = nxt

    # -- queries -------------------------------------------------------------
    def is_floor(self, x: int, y: int) -> bool:
        return self.get(x, y) in (FLOOR, FLOOR_ALT)

    def floor_cells(self) -> list[tuple[int, int]]:
        return [(x, y) for y in range(self.h) for x in range(self.w)
                if self.cells[y][x] in (FLOOR, FLOOR_ALT)]

    def open_space(self, x: int, y: int, w: int, h: int, pad: int = 0,
                   *, respect_protected: bool = True) -> bool:
        """True when a w x h footprint sits entirely on unprotected floor."""
        for dy in range(-pad, h + pad):
            for dx in range(-pad, w + pad):
                if not self.is_floor(x + dx, y + dy):
                    return False
                if respect_protected and self.is_protected(x + dx, y + dy):
                    return False
        return True

    def wall_edge(self, x: int, y: int) -> bool:
        """A wall tile with floor directly below it — the face you can see."""
        return self.get(x, y) == WALL and self.is_floor(x, y + 1)


def _short(a: int, b: int, size: int) -> int:
    d = (b - a) % size
    return d - size if d > size // 2 else d


def _inside(shape: str, dx: int, dy: int, half_w: float, half_h: float) -> bool:
    if half_w <= 0 or half_h <= 0:
        return False
    nx, ny = dx / half_w, dy / half_h
    if shape == "rect":
        return abs(nx) <= 1 and abs(ny) <= 1
    if shape == "octagon":
        return abs(nx) <= 1 and abs(ny) <= 1 and abs(nx) + abs(ny) <= 1.58
    if shape == "diamond":
        return abs(nx) + abs(ny) <= 1
    if shape == "round":
        return nx * nx + ny * ny <= 1
    if shape == "cross":
        return abs(nx) <= 0.42 or abs(ny) <= 0.42
    if shape == "ring":
        d = math.sqrt(nx * nx + ny * ny)
        return 0.52 <= d <= 1.0
    if shape == "terrace":
        # stepped, like a floor plan drawn with a set square
        step = int((dy + half_h) // max(1, half_h / 3))
        return abs(nx) <= 1 - 0.22 * step and abs(ny) <= 1
    if shape == "hall":
        return abs(nx) <= 1 and abs(ny) <= 1
    return abs(nx) <= 1 and abs(ny) <= 1


# --- zone graphs -------------------------------------------------------------

def hub_and_spokes(field: Field, rng: random.Random, *, hub: Zone,
                   spokes: list[Zone], corridor_width: int = 3) -> None:
    """A central landmark with rooms hanging off it.

    The most legible dream structure there is: you always know where the
    middle was, even when you cannot find your way back to it.
    """
    field.carve(hub)
    for zone in spokes:
        field.carve(zone)
        field.corridor((hub.cx, hub.cy), (zone.cx, zone.cy),
                       width=corridor_width,
                       bend="hv" if rng.random() < 0.5 else "vh")


def chambers(field: Field, rng: random.Random, *, cols: int, rows: int,
             size: tuple[int, int], shape: str = "octagon",
             corridor_width: int = 3, skip: float = 0.15,
             jitter: int = 2, tag: str = "") -> list[Zone]:
    """A lattice of chambers joined to their neighbours.

    This is the Neon World structure: a grid of rooms with thick walls between
    them, so the world is enormous but every part of it is a defined space.
    Some cells are skipped, which stops the grid from reading as a grid.
    """
    step_x = field.w // cols
    step_y = field.h // rows
    grid: dict[tuple[int, int], Zone] = {}
    for gy in range(rows):
        for gx in range(cols):
            if rng.random() < skip:
                continue
            cx = gx * step_x + step_x // 2 + rng.randint(-jitter, jitter)
            cy = gy * step_y + step_y // 2 + rng.randint(-jitter, jitter)
            w = size[0] + rng.randint(-2, 2)
            h = size[1] + rng.randint(-2, 2)
            zone = field.carve(Zone(f"{tag}{gx}_{gy}", cx, cy, w, h, shape,
                                    tag=tag))
            grid[(gx, gy)] = zone
    for (gx, gy), zone in grid.items():
        for dx, dy in ((1, 0), (0, 1)):
            other = grid.get(((gx + dx) % cols, (gy + dy) % rows))
            if other is None:
                continue
            field.corridor((zone.cx, zone.cy), (other.cx, other.cy),
                           width=corridor_width,
                           bend="hv" if (gx + gy) % 2 == 0 else "vh")
    return list(grid.values())


def terraces(field: Field, rng: random.Random, *, count: int,
             size: tuple[int, int], corridor_width: int = 3) -> list[Zone]:
    """Stepped platforms at different heights, joined end to end.

    Numbers World's structure: hard-edged shelves in a black void, connected
    so that walking is always along an edge.
    """
    zones = []
    x, y = rng.randrange(field.w), rng.randrange(field.h)
    for index in range(count):
        w = size[0] + rng.randint(-4, 6)
        h = size[1] + rng.randint(-2, 4)
        zone = field.carve(Zone(f"terrace{index}", x, y, w, h, "terrace"))
        zones.append(zone)
        if index:
            field.corridor((zones[index - 1].cx, zones[index - 1].cy),
                           (zone.cx, zone.cy), width=corridor_width,
                           bend="vh" if index % 2 else "hv")
        x = (x + rng.choice((-1, 1)) * rng.randint(size[0], size[0] + 12)) % field.w
        y = (y + rng.choice((-1, 1)) * rng.randint(size[1] // 2, size[1] + 8)) % field.h
    # close the ring so the layout has no dead end
    field.corridor((zones[-1].cx, zones[-1].cy), (zones[0].cx, zones[0].cy),
                   width=corridor_width)
    return zones


def clusters(field: Field, rng: random.Random, *, count: int, blobs: int = 5,
             radius: tuple[int, int] = (5, 9), thread: int = 1) -> list[Zone]:
    """Dense organic masses joined by threads.

    Mural World's structure: big irregular regions connected by paths only
    just wide enough to walk, so the space between them feels like distance.
    """
    zones = []
    centres = []
    for index in range(count):
        cx, cy = rng.randrange(field.w), rng.randrange(field.h)
        centres.append((cx, cy))
        for _ in range(blobs):
            r = rng.randint(*radius)
            ox = cx + rng.randint(-r, r)
            oy = cy + rng.randint(-r, r)
            field.carve(Zone(f"cluster{index}", ox, oy, r * 2, r * 2, "round"))
        zones.append(Zone(f"cluster{index}", cx, cy, radius[1] * 2,
                          radius[1] * 2, "round"))
    for index in range(len(centres)):
        field.corridor(centres[index], centres[(index + 1) % len(centres)],
                       width=thread, bend="hv" if index % 2 else "vh")
    field.zones = zones
    return zones


def ring_world(field: Field, rng: random.Random, *, rooms: int,
               radius: int, size: tuple[int, int], shape: str = "rect",
               corridor_width: int = 3) -> list[Zone]:
    """Rooms around a circle, joined to their neighbours and to the middle."""
    zones = []
    for index in range(rooms):
        angle = index * math.tau / rooms
        cx = int(field.w / 2 + math.cos(angle) * radius)
        cy = int(field.h / 2 + math.sin(angle) * radius * 0.78)
        zones.append(field.carve(Zone(f"ring{index}", cx, cy, size[0], size[1],
                                      shape)))
    for index, zone in enumerate(zones):
        other = zones[(index + 1) % len(zones)]
        field.corridor((zone.cx, zone.cy), (other.cx, other.cy),
                       width=corridor_width)
    return zones


# --- painting ----------------------------------------------------------------

def carpet(m, field: Field, zone: Zone, tiles: dict[str, int],
           rng: random.Random, style: str, *, patterns: list[str] | None = None,
           density: float = 1.0) -> None:
    """Lay dense, *composed* pattern across a room's floor.

    Density on its own is noise; density in an arrangement is decoration.
    Every style here is a rule about where a tile goes, so the floor reads as
    something somebody laid rather than something that fell.
    """
    keys = patterns or [k for k in tiles if k.startswith("pattern_")]
    if not keys:
        return
    ids = [tiles[k] for k in keys]
    hw, hh = zone.w // 2, zone.h // 2
    # Carpet is laid *under* the furniture: only tiles still showing bare
    # ground may be painted, or the pass would erase every prop in the room.
    bare = {tiles[k] for k in ("ground", "ground_b", "path") if k in tiles}
    bare |= set(ids)

    def put(dx: int, dy: int, tile: int) -> None:
        x, y = zone.cx + dx, zone.cy + dy
        if field.is_floor(x, y) and m.get_lower(x, y) in bare:
            m.set_lower(x, y, tile)

    if style == "border":
        # a framed rug: two courses in from the wall, all the way round
        for inset in (2, 3):
            for dx in range(-hw + inset, hw - inset + 1):
                put(dx, -hh + inset, ids[0])
                put(dx, hh - inset, ids[0])
            for dy in range(-hh + inset, hh - inset + 1):
                put(-hw + inset, dy, ids[inset % len(ids)])
                put(hw - inset, dy, ids[inset % len(ids)])
    elif style == "lattice":
        for dy in range(-hh, hh + 1):
            for dx in range(-hw, hw + 1):
                if (dx + dy) % 4 == 0:
                    put(dx, dy, ids[(dx // 2 + dy // 2) % len(ids)])
    elif style == "checker":
        for dy in range(-hh, hh + 1):
            for dx in range(-hw, hw + 1):
                if ((dx // 2) + (dy // 2)) % 2 == 0:
                    put(dx, dy, ids[abs(dx + dy) % len(ids)])
    elif style == "rings":
        for dy in range(-hh, hh + 1):
            for dx in range(-hw, hw + 1):
                d = int(math.hypot(dx, dy * (zone.w / max(zone.h, 1))))
                if d % 3 == 0:
                    put(dx, dy, ids[(d // 3) % len(ids)])
    elif style == "stripe":
        for dy in range(-hh, hh + 1):
            for dx in range(-hw, hw + 1):
                if dx % 3 == 0:
                    put(dx, dy, ids[(dx // 3) % len(ids)])
    elif style == "full":
        for dy in range(-hh, hh + 1):
            for dx in range(-hw, hw + 1):
                put(dx, dy, ids[(abs(dx) // 2 + abs(dy) // 2) % len(ids)])
    elif style == "corners":
        for sx in (-1, 1):
            for sy in (-1, 1):
                for dy in range(2, 6):
                    for dx in range(2, 6):
                        put(sx * (hw - dx), sy * (hh - dy),
                            ids[(dx + dy) % len(ids)])
    elif style == "cross":
        for dy in range(-hh, hh + 1):
            put(0, dy, ids[0])
            put(1, dy, ids[0])
        for dx in range(-hw, hw + 1):
            put(dx, 0, ids[1 % len(ids)])
            put(dx, 1, ids[1 % len(ids)])


def glow_floor(m, field: Field, zone: Zone, tiles: dict[str, int],
               anim: str, positions: list[tuple[int, int]]) -> None:
    """Drop animated tiles onto the floor at chosen points."""
    tile = tiles.get(anim)
    if tile is None:
        return
    bare = {tiles[k] for k in ("ground", "ground_b", "path") if k in tiles}
    bare |= {v for k, v in tiles.items() if k.startswith("pattern_")}
    for x, y in positions:
        if field.is_floor(x, y) and m.get_lower(x, y) in bare:
            m.set_lower(x, y, tile)


def paint(m, field: Field, tiles: dict[str, int], *, floor: str = "ground",
          floor_alt: str = "ground_b", wall: str = "wall_core",
          wall_face: str = "wall_face", void: str = "void",
          decals: tuple[str, ...] = ("decal_0", "decal_1", "decal_2"),
          decal_chance: float = 0.010, rng: random.Random | None = None) -> None:
    """Write a field onto a map.

    Wall tiles that have floor directly below them get the *face* tile, which
    is the lit front of the boundary; the rest get the flat core.  That single
    distinction is what turns a band of colour into something that reads as a
    wall you are standing in front of.
    """
    rng = rng or random.Random(0)
    marks = [tiles[k] for k in decals if k in tiles]
    for y in range(m.height):
        for x in range(m.width):
            state = field.get(x, y)
            if state == VOID:
                m.set_lower(x, y, tiles[void])
            elif state == WALL:
                # two wall patterns, alternating in broad bands, so a long
                # boundary has some rhythm to it
                alt = ((x // 7) + (y // 9)) % 3 == 0 and "wall_alt" in tiles
                if field.wall_edge(x, y):
                    m.set_lower(x, y, tiles["wall_alt_face" if alt else wall_face])
                else:
                    m.set_lower(x, y, tiles["wall_alt" if alt else wall])
            elif state == FLOOR_ALT:
                m.set_lower(x, y, tiles[floor_alt])
            else:
                if marks and rng.random() < decal_chance:
                    m.set_lower(x, y, rng.choice(marks))
                else:
                    m.set_lower(x, y, tiles[floor])


def shade_walls(m, field: Field, tiles: dict[str, int],
                shadow: str = "shadow_t") -> None:
    """Lay a soft shadow on the floor directly beneath every wall face."""
    if shadow not in tiles:
        return
    for y in range(m.height):
        for x in range(m.width):
            if field.get(x, y) == WALL and field.is_floor(x, y + 1):
                m.set_upper(x, y + 1, tiles[shadow])


def zone_spots(field: Field, zone: Zone, rng: random.Random, count: int, *,
               w: int = 1, h: int = 1, pad: int = 1,
               tries: int = 200) -> list[tuple[int, int]]:
    """Positions inside one zone that a prop or event can occupy."""
    found: list[tuple[int, int]] = []
    for _ in range(tries):
        if len(found) >= count:
            break
        x = zone.cx + rng.randint(-zone.w // 2, zone.w // 2)
        y = zone.cy + rng.randint(-zone.h // 2, zone.h // 2)
        if not field.open_space(x, y, w, h, pad):
            continue
        if any(abs(_short(x, fx, field.w)) < w + 2 and
               abs(_short(y, fy, field.h)) < h + 2 for fx, fy in found):
            continue
        found.append((x % field.w, y % field.h))
    return found


# --- making sure the player can actually get around ---------------------------

def reachable(m, solid: set[int], start: tuple[int, int]) -> set[tuple[int, int]]:
    """Flood fill the walkable tiles of a finished map from ``start``.

    Run against the real tile ids and the real passability table, so it
    catches props that block a route as well as walls that do.
    """
    seen: set[tuple[int, int]] = set()
    stack = [(start[0] % m.width, start[1] % m.height)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen:
            continue
        if m.get_lower(x, y) in solid or m.get_upper(x, y) in solid:
            continue
        seen.add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = ((x + dx) % m.width, (y + dy) % m.height)
            if nxt not in seen:
                stack.append(nxt)
    return seen


def solid_ids(chipset) -> set[int]:
    """Every tile id that blocks movement, for the reachability check."""
    out: set[int] = set()
    for index, bits in enumerate(chipset.passable_lower):
        if bits == 0:
            if 18 <= index < 162:
                out.add(5000 + index - 18)
            elif 3 <= index < 6:
                out.add(3000 + (index - 3) * 50)
    for index, bits in enumerate(chipset.passable_upper):
        if bits & 0x0F == 0:
            out.add(10000 + index)
    return out


def repair_connectivity(m, field: Field, chipset, start: tuple[int, int],
                        floor_tile: int) -> int:
    """Delete anything that has cut the world into pieces.

    Props are placed by rules that are careful but not proof; this is the
    proof.  Any walkable-by-design tile the player cannot actually reach has
    whatever was standing on it removed, and the pass repeats until the
    reachable set stops growing.  A world that cannot be walked is worse than
    a world that is missing one crayon.
    """
    solid = solid_ids(chipset)
    removed = 0
    for _ in range(8):
        seen = reachable(m, solid, start)
        stranded = [(x, y) for (x, y) in field.floor_cells()
                    if (x, y) not in seen]
        if not stranded:
            break
        for x, y in stranded:
            if m.get_lower(x, y) in solid:
                m.set_lower(x, y, floor_tile)
                removed += 1
            if m.get_upper(x, y) in solid:
                m.set_upper(x, y, 0)
                removed += 1
    return removed


# --- other architectures -----------------------------------------------------
# A grid of chambers is one structure, not the only one.  Yume Nikki's worlds
# differ in *shape* before they differ in colour, so each of these builds a
# fundamentally different kind of place.

def warren(field: Field, rng: random.Random, *, halls: int = 7,
           cell_size: tuple[int, int] = (11, 9), cells_per_hall: int = 4,
           hall_width: int = 3) -> list[Zone]:
    """Long corridors with small rooms hanging off them.

    Corridor-dominant rather than room-dominant: you spend most of your time
    in the halls, and the rooms are things you glance into.  This is what
    makes a building feel endless rather than large.
    """
    zones: list[Zone] = []
    for index in range(halls):
        vertical = index % 2 == 1
        x = rng.randrange(field.w)
        y = rng.randrange(field.h)
        length = (field.h if vertical else field.w) - rng.randint(4, 20)
        field.long_hall(x, y, length, vertical=vertical, width=hall_width)
        for step in range(cells_per_hall):
            along = int(length * (step + 0.5) / cells_per_hall)
            side = rng.choice((-1, 1))
            if vertical:
                cx = x + side * (cell_size[0] // 2 + hall_width)
                cy = y + along
            else:
                cx = x + along
                cy = y + side * (cell_size[1] // 2 + hall_width)
            zone = field.carve(Zone(f"cell{index}_{step}", cx, cy,
                                    cell_size[0] + rng.randint(-2, 3),
                                    cell_size[1] + rng.randint(-2, 3), "rect"))
            field.corridor((x + (0 if vertical else along),
                            y + (along if vertical else 0)),
                           (cx, cy), width=hall_width)
            zones.append(zone)
    return zones


def platforms(field: Field, rng: random.Random, *, count: int = 26,
              size: tuple[int, int] = (13, 11), bridge: int = 2,
              shape: str = "rect") -> list[Zone]:
    """Isolated slabs floating in void, joined by narrow bridges.

    Nothing touches anything else.  The gaps are the point: the player can see
    where they are going long before they can work out how to get there.
    """
    zones: list[Zone] = []
    cols = int(math.sqrt(count * field.w / max(field.h, 1))) or 1
    rows = max(1, count // cols)
    step_x, step_y = field.w // cols, field.h // rows
    for gy in range(rows):
        for gx in range(cols):
            cx = gx * step_x + step_x // 2 + rng.randint(-3, 3)
            cy = gy * step_y + step_y // 2 + rng.randint(-3, 3)
            zones.append(field.carve(Zone(f"slab{gx}_{gy}", cx, cy,
                                          size[0] + rng.randint(-3, 4),
                                          size[1] + rng.randint(-2, 3), shape)))
    # thin bridges, and deliberately not to every neighbour
    for index, zone in enumerate(zones):
        for other in (zones[(index + 1) % len(zones)],
                      zones[(index + cols) % len(zones)]):
            if rng.random() < 0.78:
                field.corridor((zone.cx, zone.cy), (other.cx, other.cy),
                               width=bridge,
                               bend="hv" if index % 2 else "vh")
    return zones


def carved_mass(field: Field, rng: random.Random, *, walks: int = 14,
                length: int = 70, width: int = 4,
                clearings: int = 12,
                clearing_size: tuple[int, int] = (13, 11)) -> list[Zone]:
    """Start from solid and wander paths through it.

    The negative-space approach: the world is a block of forest and the
    playable space is what has been worn away.  Paths meander, so no sightline
    is ever long and the boundary is never a straight line.
    """
    zones: list[Zone] = []
    for _ in range(walks):
        fx, fy = float(rng.randrange(field.w)), float(rng.randrange(field.h))
        angle = rng.uniform(0, math.tau)
        for _ in range(length):
            angle += rng.uniform(-0.45, 0.45)
            fx += math.cos(angle)
            fy += math.sin(angle)
            for dy in range(width):
                for dx in range(width):
                    field.set(int(fx) + dx, int(fy) + dy, FLOOR)
                    field.protect(int(fx) + dx, int(fy) + dy, 0)
    for index in range(clearings):
        cx, cy = rng.randrange(field.w), rng.randrange(field.h)
        zones.append(field.carve(Zone(f"clearing{index}", cx, cy,
                                      clearing_size[0] + rng.randint(-2, 5),
                                      clearing_size[1] + rng.randint(-2, 4),
                                      "round")))
    # make sure the clearings are actually on the path network
    for index in range(len(zones) - 1):
        field.corridor((zones[index].cx, zones[index].cy),
                       (zones[index + 1].cx, zones[index + 1].cy), width=3)
    return zones


def great_hall(field: Field, rng: random.Random, *, alcoves: int = 9,
               fill: float = 0.62) -> list[Zone]:
    """One enormous open space with a handful of recesses off it.

    White Desert's structure.  Almost no interior boundaries, so the walls are
    always visible in the far distance and never anywhere near you.
    """
    hall = field.carve(Zone("hall", field.w // 2, field.h // 2,
                            int(field.w * fill), int(field.h * fill),
                            "round"))
    zones = [hall]
    for index in range(alcoves):
        angle = index * math.tau / alcoves + rng.uniform(-0.2, 0.2)
        cx = int(field.w / 2 + math.cos(angle) * field.w * fill * 0.56)
        cy = int(field.h / 2 + math.sin(angle) * field.h * fill * 0.56)
        zone = field.carve(Zone(f"alcove{index}", cx, cy,
                                rng.randint(11, 17), rng.randint(9, 15),
                                rng.choice(("rect", "round", "diamond"))))
        field.corridor((hall.cx, hall.cy), (zone.cx, zone.cy), width=3)
        zones.append(zone)
    return zones


def strict_grid(field: Field, rng: random.Random, *, cols: int = 6,
                rows: int = 5, size: tuple[int, int] = (13, 11),
                corridor_width: int = 3) -> list[Zone]:
    """Identical cells on an exact grid, with no variation at all.

    The Teleport Maze structure.  The repetition *is* the effect: every room
    is the same room, and after a while the player stops trusting that they
    have moved.
    """
    zones = []
    step_x, step_y = field.w // cols, field.h // rows
    for gy in range(rows):
        for gx in range(cols):
            cx = gx * step_x + step_x // 2
            cy = gy * step_y + step_y // 2
            zones.append(field.carve(Zone(f"cell{gx}_{gy}", cx, cy,
                                          size[0], size[1], "rect")))
    for gy in range(rows):
        for gx in range(cols):
            here = zones[gy * cols + gx]
            right = zones[gy * cols + (gx + 1) % cols]
            down = zones[((gy + 1) % rows) * cols + gx]
            field.corridor((here.cx, here.cy), (right.cx, right.cy),
                           width=corridor_width)
            field.corridor((here.cx, here.cy), (down.cx, down.cy),
                           width=corridor_width, bend="vh")
    return zones


def canyons(field: Field, rng: random.Random, *, blocks: int = 34,
            block_size: tuple[int, int] = (11, 9), margin: int = 5
            ) -> list[Zone]:
    """A wide open floor with tall masses standing on it.

    The inverse of carving rooms: the floor is continuous and the *obstacles*
    make the shape, so the space between them reads as streets and canyons.

    The floor is still a carved region rather than the whole map — an
    unbounded plain with things standing on it is exactly the failure this
    module exists to prevent.  The masses then divide that region into streets
    narrow enough to read as streets.
    """
    outer = field.carve(Zone("district", field.w // 2, field.h // 2,
                             int(field.w * 0.88), int(field.h * 0.88),
                             "octagon"))
    zones = [outer]
    placed: list[tuple[int, int, int, int]] = []
    for index in range(blocks):
        for _ in range(60):
            w = block_size[0] + rng.randint(-3, 6)
            h = block_size[1] + rng.randint(-2, 5)
            x = rng.randrange(field.w)
            y = rng.randrange(field.h)
            if any(abs(_short(x, px, field.w)) < (w + pw) // 2 + margin and
                   abs(_short(y, py, field.h)) < (h + ph) // 2 + margin
                   for px, py, pw, ph in placed):
                continue
            for dy in range(-h // 2, h // 2 + 1):
                for dx in range(-w // 2, w // 2 + 1):
                    field.set(x + dx, y + dy, VOID)
            placed.append((x, y, w, h))
            break
    # the walkable pockets between the masses are the rooms
    for index, (x, y, w, h) in enumerate(placed):
        zones.append(Zone(f"street{index}", (x + w // 2 + margin) % field.w,
                          y % field.h, margin * 2, h, "rect"))
    # one avenue straight through the district, so there is always a way that
    # obviously goes somewhere
    field.long_hall(0, field.h // 2 - 1, field.w, width=4)
    field.zones = zones
    return zones


def archipelago(field: Field, rng: random.Random, *, islands: int = 24,
                size: tuple[int, int] = (15, 12), pier: int = 2
                ) -> list[Zone]:
    """Islands in open water, strung together with narrow boards."""
    zones = []
    for index in range(islands):
        cx, cy = rng.randrange(field.w), rng.randrange(field.h)
        zones.append(field.carve(Zone(f"isle{index}", cx, cy,
                                      size[0] + rng.randint(-4, 6),
                                      size[1] + rng.randint(-3, 5), "round")))
    order = sorted(range(len(zones)), key=lambda i: (zones[i].cy, zones[i].cx))
    for step in range(len(order)):
        a = zones[order[step]]
        b = zones[order[(step + 1) % len(order)]]
        field.corridor((a.cx, a.cy), (b.cx, b.cy), width=pier,
                       bend="hv" if step % 2 else "vh")
    return zones
