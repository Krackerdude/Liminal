"""Room kinds: what makes one chamber different from the one next door.

A world of thirty identical rooms is a corridor with extra steps.  Each world
declares a list of *room kinds*, and every zone is dealt one, so walking from
room to room always turns up something that was not in the last one.

A room kind decides four things:

``props``        the scenery, placed in a deliberate arrangement rather than
                 scattered — a ring, a row along the back wall, one thing dead
                 centre, a pair facing each other
``interactable`` the one thing in the room worth pressing the button at
``line``         what that thing says, which is never an explanation
``floor``        an optional change to the floor, so the room reads as
                 different before the player has looked at anything in it

Nothing is ever placed on a corridor tile or its shoulders: see
``Field.protected``.  A room that swallows the only way through is a bug, not
a secret.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

from . import gen
from .layout import Field, Zone, zone_spots


@dataclass
class Room:
    """A furnished zone, and the hooks the event pass needs."""
    zone: Zone
    kind: str
    interactables: list[tuple[int, int, str, str]] = field(default_factory=list)
    # (x, y, charset-or-"", line)
    spots: list[tuple[int, int]] = field(default_factory=list)

    @property
    def centre(self) -> tuple[int, int]:
        return self.zone.cx, self.zone.cy


# --- arrangements ------------------------------------------------------------
# How props are laid out inside a room.  Arrangement is most of what makes a
# room feel composed rather than filled.

def ring(zone: Zone, count: int, *, inset: int = 4,
         squash: float = 1.0) -> list[tuple[int, int]]:
    out = []
    for step in range(count):
        angle = step * math.tau / count
        x = int(zone.cx + math.cos(angle) * (zone.w / 2 - inset))
        y = int(zone.cy + math.sin(angle) * (zone.h / 2 - inset) * squash)
        out.append((x, y))
    return out


def back_wall(zone: Zone, count: int, *, spacing: int = 3,
              inset: int = 2) -> list[tuple[int, int]]:
    """A row along the top of the room, like a skyline."""
    start = zone.cx - (count * spacing) // 2
    y = zone.cy - zone.h // 2 + inset
    return [(start + i * spacing, y) for i in range(count)]


def facing_pair(zone: Zone, gap: int = 6) -> list[tuple[int, int]]:
    return [(zone.cx - gap, zone.cy), (zone.cx + gap, zone.cy)]


def corners(zone: Zone, inset: int = 4) -> list[tuple[int, int]]:
    return [(zone.cx - zone.w // 2 + inset, zone.cy - zone.h // 2 + inset),
            (zone.cx + zone.w // 2 - inset, zone.cy - zone.h // 2 + inset),
            (zone.cx - zone.w // 2 + inset, zone.cy + zone.h // 2 - inset),
            (zone.cx + zone.w // 2 - inset, zone.cy + zone.h // 2 - inset)]


def avenue(zone: Zone, count: int, *, spacing: int = 4) -> list[tuple[int, int]]:
    """Two facing rows, like an aisle."""
    out = []
    start = zone.cx - (count * spacing) // 2
    for i in range(count):
        out.append((start + i * spacing, zone.cy - zone.h // 4))
        out.append((start + i * spacing, zone.cy + zone.h // 4))
    return out


def spiral_out(zone: Zone, count: int) -> list[tuple[int, int]]:
    out = []
    for step in range(count):
        angle = step * 1.1
        radius = 2 + step * (min(zone.w, zone.h) / 2 - 4) / max(count, 1)
        out.append((int(zone.cx + math.cos(angle) * radius),
                    int(zone.cy + math.sin(angle) * radius * 0.8)))
    return out


class Furnisher:
    """Places props into a room, refusing anything that would block a route."""

    def __init__(self, m, field: Field, chipset, rng: random.Random):
        self.m = m
        self.field = field
        self.cs = chipset
        self.rng = rng
        self.placed: list[tuple[int, int, int, int]] = []

    def _clear(self, x: int, y: int, w: int, h: int, pad: int = 1) -> bool:
        """Free of routes, and free of anything already standing there.

        The occupancy half of this question is asked of the *map*, not of a
        list this furnisher keeps to itself.  Two placement paths keeping two
        separate records is how a world ended up with objects the furnisher
        had refused and a bare stamp had put down anyway.
        """
        if not self.field.open_space(x, y, w, h, pad):
            return False
        return self.m.is_clear(x, y, w, h, pad=1)

    def put(self, obj_name: str, x: int, y: int, *, centred: bool = True,
            pad: int = 1) -> bool:
        grid = self.cs.obj(obj_name)
        ox = x - grid.cols // 2 if centred else x
        oy = y - grid.rows // 2 if centred else y
        if not self._clear(ox, oy, grid.cols, grid.rows, pad):
            return False
        if not gen.stamp(self.m, grid, ox, oy):
            return False
        self.placed.append((ox, oy, grid.cols, grid.rows))
        return True

    def put_many(self, obj_names: list[str], positions: list[tuple[int, int]],
                 *, pad: int = 1) -> int:
        count = 0
        for index, (x, y) in enumerate(positions):
            if self.put(obj_names[index % len(obj_names)], x, y, pad=pad):
                count += 1
        return count

    def floor_patch(self, tile: int, zone: Zone, *, radius: float = 0.0) -> None:
        r = radius or min(zone.w, zone.h) / 3
        for dy in range(-int(r), int(r) + 1):
            for dx in range(-int(r), int(r) + 1):
                if math.hypot(dx, dy) <= r and self.field.is_floor(
                        zone.cx + dx, zone.cy + dy):
                    self.m.set_lower(zone.cx + dx, zone.cy + dy, tile)

    def free_spot(self, zone: Zone, *, w: int = 1, h: int = 1,
                  pad: int = 1) -> tuple[int, int] | None:
        for x, y in zone_spots(self.field, zone, self.rng, 6, w=w, h=h, pad=pad):
            if self._clear(x, y, w, h, pad):
                return x, y
        return None


# A room kind is a function that furnishes one zone and returns a Room.
RoomKind = Callable[[Furnisher, Zone, dict], Room]
