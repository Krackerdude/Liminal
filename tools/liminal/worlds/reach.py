"""Can the player actually get to the things the game put in front of them?

The build proves the files parse.  The Player proves the maps boot.  Neither
proves the game is *playable*: an item on a tile behind a wall, a resident
standing on the far side of water, a prize three tiles into solid rock all
load perfectly and simply cannot be used.  That failure is invisible from a
screenshot, invisible from the map data, and only shows up when somebody walks
the whole game and finds that nothing is doable.

So it is checked here, mechanically, the way the player would find out: flood
fill from the arrival tile across the real tile ids and the real passability
table, then ask of every interaction whether the player can stand where they
would need to stand.

What "need to stand" means depends on the trigger:

* **action** events are talked to from an adjacent tile, so one of the four
  neighbours has to be reachable.  Standing *on* one is impossible -- an event
  on the player's layer blocks.
* **touch** and **collision** events are walked into, so the event's own tile
  has to be reachable.
* **parallel** and **auto** events run by themselves and are never approached.

Blocking events are part of the terrain.  A resident standing in a doorway
seals the room behind them exactly as a wall would, so the fill treats
same-layer events as solid, which is what the engine does.
"""

from __future__ import annotations

import re
from collections import deque

from ..maps import (LAYER_SAME, TRIGGER_AUTO, TRIGGER_COLLISION,
                    TRIGGER_PARALLEL, TRIGGER_TOUCH)
from .layout import solid_ids

STOOD_ON = {TRIGGER_TOUCH, TRIGGER_COLLISION}
UNATTENDED = {TRIGGER_PARALLEL, TRIGGER_AUTO}

# The suffix ``_place_object`` gives the extra tiles of a wide object.
RELAY = re.compile(r" (?:reach )?-?\d+,-?\d+$")

NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _first(event):
    """The page the player meets first.

    Later pages need switches nobody has thrown yet, so the page that decides
    whether a thing can be reached on arrival is page one.
    """
    return event.pages[0] if event.pages else None


def walkable(world) -> set[tuple[int, int]]:
    """Every tile the player can stand on, starting from where they arrive."""
    m = world.map
    solid = solid_ids(world.chipset)
    start = (world.spawn[0] % m.width, world.spawn[1] % m.height)
    stops = {(e.x % m.width, e.y % m.height) for e in m.events
             if (_first(e) is not None and _first(e).layer == LAYER_SAME
                 and (e.x % m.width, e.y % m.height) != start)}

    seen: set[tuple[int, int]] = set()
    queue = deque([start])
    while queue:
        spot = queue.popleft()
        if spot in seen or spot in stops:
            continue
        x, y = spot
        if m.get_lower(x, y) in solid or m.get_upper(x, y) in solid:
            continue
        seen.add(spot)
        for dx, dy in NEIGHBOURS:
            queue.append(((x + dx) % m.width, (y + dy) % m.height))
    return seen


def objects(world) -> list[tuple[str, list, int]]:
    """Fold the relay events back into the objects they came from.

    A wide object gets an interaction stamped on every tile it occupies, so a
    four-tile bed is four events.  Judging those separately would call three
    quarters of every bed in the game unreachable, which is true and useless --
    the player only has to be able to touch one tile of it.

    Two beds in two rooms share a name, so same-named events are only merged
    when their tiles actually touch.
    """
    m = world.map
    groups: dict[str, list] = {}
    for event in m.events:
        page = _first(event)
        if page is None or page.trigger in UNATTENDED:
            continue
        groups.setdefault(RELAY.sub("", event.name), []).append(event)

    def near(a, b) -> bool:
        dx = abs((a[0] - b[0] + m.width // 2) % m.width - m.width // 2)
        dy = abs((a[1] - b[1] + m.height // 2) % m.height - m.height // 2)
        return dx <= 1 and dy <= 1

    out = []
    for name, events in groups.items():
        clusters: list[list] = []
        for event in sorted(events, key=lambda e: (e.y, e.x)):
            here = (event.x % m.width, event.y % m.height)
            touching = [c for c in clusters
                        if any(near((e.x % m.width, e.y % m.height), here)
                               for e in c)]
            if touching:
                keep = touching[0]
                keep.append(event)
                for extra in touching[1:]:
                    keep.extend(extra)
                    clusters.remove(extra)
            else:
                clusters.append([event])
        for cluster in clusters:
            out.append((name, cluster, _first(cluster[0]).trigger))
    return out


def usable(world, tiles, trigger, open_tiles) -> bool:
    """Could the player use something occupying ``tiles``?"""
    m = world.map
    if trigger in STOOD_ON:
        return any(t in open_tiles for t in tiles)
    sides = {((x + dx) % m.width, (y + dy) % m.height)
             for x, y in tiles for dx, dy in NEIGHBOURS}
    return bool(sides & open_tiles)


def stranded(world, open_tiles=None) -> list[tuple[str, int, int, str]]:
    """Every object the player cannot use, with where it is and why."""
    m = world.map
    open_tiles = walkable(world) if open_tiles is None else open_tiles
    out = []
    for name, cluster, trigger in objects(world):
        tiles = [(e.x % m.width, e.y % m.height) for e in cluster]
        if usable(world, tiles, trigger, open_tiles):
            continue
        why = ("cannot be stepped on" if trigger in STOOD_ON
               else "nothing beside it is reachable")
        out.append((name, tiles[0][0], tiles[0][1], why))
    return out


def rehome(world, *, radius: int = 8, rounds: int = 3) -> list[str]:
    """Move anything the player cannot get to onto ground where they can.

    The last line of defence, and it exists because there are forty-odd places
    in this codebase that add an event directly, each with its own idea of
    where its thing belongs -- a mural's centre, a lever bank's front, the
    fifth tip of a star.  Every one of those coordinates was right about the
    art and none of them checked whether the finished world had put a wall
    there.  Rather than teach forty call sites to ask, the question is asked
    once, here, of the finished map.

    Only **single** events move.  A multi-tile object has its interaction
    stamped on every tile it occupies, and one of those tiles being
    unapproachable is not a bug -- it is the back of the wardrobe.  Moving one
    would tear the object's interaction off the object.

    Moving an event changes what is reachable, since an event on the player's
    layer blocks, so this repeats until it settles.  Returns what it moved.
    """
    m = world.map
    moved: list[str] = []
    for _ in range(rounds):
        open_tiles = walkable(world)
        stuck = False
        for name, cluster, trigger in objects(world):
            tiles = [(e.x % m.width, e.y % m.height) for e in cluster]
            if usable(world, tiles, trigger, open_tiles):
                continue
            if len(cluster) > 1:
                continue                      # part of a stamped object
            event = cluster[0]
            spot = spot_for(world, *tiles[0],
                            stand_on=trigger in STOOD_ON,
                            avoid={(e.x, e.y) for e in m.events
                                   if e is not event},
                            open_tiles=open_tiles, radius=radius)
            if spot is None or spot == tiles[0]:
                continue
            moved.append(f"{world.key}/{name} {tiles[0]} -> {spot}")
            event.x, event.y = spot
            stuck = True
        if not stuck:
            break
    return moved


def spot_for(world, x: int, y: int, *, stand_on: bool, avoid=(),
             open_tiles=None, radius: int = 12) -> tuple[int, int] | None:
    """The nearest tile to (x, y) that the player could actually use.

    Returns the tile unchanged when it already works, the closest one that
    does within ``radius``, or ``None`` when there is nowhere -- which is a
    signal to drop the thing rather than to put it somewhere absurd.

    Used for things that have no object of their own to sit on: a resident, a
    prize, a mirror.  A relay tile belonging to a wide object must *not* be
    moved this way -- it belongs to its object, and an object's tile that
    cannot be approached is simply one of the tiles that cannot be approached.
    """
    m = world.map
    open_tiles = walkable(world) if open_tiles is None else open_tiles
    avoid = set(avoid)
    best: tuple[int, tuple[int, int]] | None = None
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            spot = ((x + dx) % m.width, (y + dy) % m.height)
            if spot in avoid:
                continue
            if stand_on:
                if spot not in open_tiles:
                    continue
            else:
                # Somewhere to put a thing that blocks: the tile itself must
                # not be floor the player needs, but a neighbour must be open.
                if not usable(world, [spot], 0, open_tiles):
                    continue
            cost = dx * dx + dy * dy
            if best is None or cost < best[0]:
                best = (cost, spot)
    return best[1] if best else None
