"""Map (.lmu) and map-tree (.lmt) construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .cmds import Script, move_route_nodes
from .lcfxml import Node, collection, document, music

# rpg::Map::ScrollType — "both" is what makes a world feel like it has no edge.
SCROLL_NONE = 0
SCROLL_VERTICAL = 1
SCROLL_HORIZONTAL = 2
SCROLL_BOTH = 3

# rpg::EventPage::Trigger
TRIGGER_ACTION = 0
TRIGGER_TOUCH = 1
TRIGGER_COLLISION = 2
TRIGGER_AUTO = 3
TRIGGER_PARALLEL = 4

# rpg::EventPage::MoveType
MOVE_STATIONARY = 0
MOVE_RANDOM = 1
MOVE_VERTICAL = 2
MOVE_HORIZONTAL = 3
MOVE_TOWARD = 4
MOVE_AWAY = 5
MOVE_CUSTOM = 6

# rpg::EventPage::Layers
LAYER_BELOW = 0
LAYER_SAME = 1
LAYER_ABOVE = 2

# rpg::EventPage::AnimType
ANIM_NON_CONTINUOUS = 0
ANIM_CONTINUOUS = 1
ANIM_FIXED_NON_CONTINUOUS = 2
ANIM_FIXED_CONTINUOUS = 3
ANIM_FIXED_GRAPHIC = 4
ANIM_SPIN = 5

DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT = 0, 1, 2, 3

# Tile-id bases (EasyRPG Player's map_data.h).
BLOCK_A = 0        # animated water autotiles
BLOCK_B = 2000
BLOCK_C = 3000     # animated, non-autotile
BLOCK_D = 4000     # terrain autotiles, 12 sets of 50
BLOCK_E = 5000     # 144 plain lower tiles
BLOCK_F = 10000    # 144 plain upper tiles

# "Nothing on the upper layer" is written as block F tile zero, **not** as a
# literal zero.  The engine reads an upper cell as ``value - BLOCK_F`` and uses
# the result to index a 144-entry table, so a stored 0 indexes that table at
# -10000: an out-of-bounds read whose answer is whatever happens to be in
# memory.  It cost a day of chasing doors that opened on some builds and not
# others.  Every chipset therefore reserves upper index 0 as a blank, passable
# tile, and an empty cell points at it.
EMPTY_UPPER = BLOCK_F


def lower(index: int) -> int:
    """Tile id for plain lower-layer tile ``index`` (0..143)."""
    return BLOCK_E + index


def upper(index: int) -> int:
    """Tile id for plain upper-layer tile ``index`` (0..143)."""
    return BLOCK_F + index


def autotile(set_index: int, shape: int = 0) -> int:
    """Tile id for one of the twelve block-D autotile sets (0..11)."""
    return BLOCK_D + set_index * 50 + shape


@dataclass
class Page:
    """One page of an event.  Later pages win when their conditions hold."""
    script: Script = field(default_factory=Script)
    # "Blank" is a real, fully transparent charset.  Leaving this empty makes
    # the engine fall back to drawing chipset tile zero — the void — so every
    # invisible trigger becomes a black square.  Nothing is graphic-less by
    # accident; it is graphic-less on purpose, and says so.
    charset: str = "Blank"
    charset_index: int = 0
    direction: int = DIR_DOWN
    pattern: int = 1
    translucent: bool = False
    move_type: int = MOVE_STATIONARY
    move_speed: int = 3
    move_frequency: int = 3
    move_commands: Sequence = ()
    move_repeat: bool = True
    trigger: int = TRIGGER_ACTION
    # RPG Maker's own default, and load-bearing: the engine only looks for
    # action-triggered events on the *same* layer as the player.  An event on
    # the below layer can never be talked to from the tile in front of it, so
    # every door, resident and object in the game was silently unreachable.
    layer: int = LAYER_SAME
    overlap_forbidden: bool = False
    animation_type: int = ANIM_NON_CONTINUOUS
    switch_a: int | None = None
    switch_b: int | None = None
    variable: tuple[int, int] | None = None   # (variable id, minimum value)
    item: int | None = None

    def to_node(self) -> Node:
        node = Node("EventPage")
        cond = node.add(Node("condition")).add(Node("EventPageCondition"))
        flags = cond.add(Node("flags")).add(Node("EventPageCondition_Flags"))
        flags.set("switch_a", self.switch_a is not None)
        flags.set("switch_b", self.switch_b is not None)
        flags.set("variable", self.variable is not None)
        flags.set("item", self.item is not None)
        flags.set("actor", False)
        flags.set("timer", False)
        cond.set("switch_a_id", self.switch_a or 1)
        cond.set("switch_b_id", self.switch_b or 1)
        cond.set("variable_id", self.variable[0] if self.variable else 1)
        cond.set("variable_value", self.variable[1] if self.variable else 0)
        cond.set("item_id", self.item or 1)
        cond.set("actor_id", 1)
        cond.set("compare_operator", 1)

        node.set("character_name", self.charset)
        node.set("character_index", self.charset_index)
        node.set("character_direction", self.direction)
        node.set("character_pattern", self.pattern)
        node.set("translucent", self.translucent)
        node.set("move_type", self.move_type)
        node.set("move_frequency", self.move_frequency)
        node.set("trigger", self.trigger)
        node.set("layer", self.layer)
        node.set("overlap_forbidden", self.overlap_forbidden)
        node.set("animation_type", self.animation_type)
        node.set("move_speed", self.move_speed)
        node.add(move_route_nodes(self.move_commands, repeat=self.move_repeat))
        node.add(Node("event_commands")).extend(self.script.to_nodes())
        return node


@dataclass
class Event:
    ident: int
    name: str
    x: int
    y: int
    pages: list[Page] = field(default_factory=list)

    def to_node(self) -> Node:
        node = Node("Event")
        node.set("name", self.name)
        node.set("x", self.x)
        node.set("y", self.y)
        pages = node.add(Node("pages"))
        for index, page in enumerate(self.pages, start=1):
            child = page.to_node()
            child.attrs["id"] = f"{index:04d}"
            pages.add(child)
        return node


class Map:
    """A single map.  Layers are flat row-major lists of tile ids."""

    def __init__(self, width: int, height: int, chipset_id: int = 1, *,
                 scroll_type: int = SCROLL_BOTH, fill: int = BLOCK_E):
        self.width = width
        self.height = height
        self.chipset_id = chipset_id
        self.scroll_type = scroll_type
        self.lower = [fill] * (width * height)
        self.upper = [EMPTY_UPPER] * (width * height)
        self.events: list[Event] = []
        # Every cell an object has been stamped into.  One record, owned by the
        # map, so that *all* placement paths share it — the furnisher and the
        # bare stamp alike.  Before this existed the two disagreed: Furnisher
        # kept its own private list and refused overlaps, gen.stamp kept none
        # and allowed them, so any world that stamped directly could pile
        # objects on top of each other indefinitely.
        self.claimed: set[tuple[int, int]] = set()
        self.parallax: str | None = None
        self.parallax_loop_x = True
        self.parallax_loop_y = True
        self.parallax_auto_x = 0
        self.parallax_auto_y = 0
        self._next_event_id = 1

    # -- occupancy ------------------------------------------------------------
    def is_clear(self, x: int, y: int, w: int, h: int, pad: int = 0) -> bool:
        """Is a footprint free of every object already placed?"""
        for row in range(-pad, h + pad):
            for col in range(-pad, w + pad):
                if ((x + col) % self.width, (y + row) % self.height) \
                        in self.claimed:
                    return False
        return True

    def claim(self, x: int, y: int, w: int, h: int) -> None:
        for row in range(h):
            for col in range(w):
                self.claimed.add(((x + col) % self.width,
                                  (y + row) % self.height))

    # -- tiles ---------------------------------------------------------------
    def idx(self, x: int, y: int) -> int:
        return (y % self.height) * self.width + (x % self.width)

    def set_lower(self, x: int, y: int, tile: int) -> None:
        self.lower[self.idx(x, y)] = tile

    def get_lower(self, x: int, y: int) -> int:
        return self.lower[self.idx(x, y)]

    def set_upper(self, x: int, y: int, tile: int) -> None:
        # Callers write 0 to mean "clear this cell"; the engine needs that
        # spelled as block F tile zero.  See EMPTY_UPPER.
        self.upper[self.idx(x, y)] = tile or EMPTY_UPPER

    def get_upper(self, x: int, y: int) -> int:
        return self.upper[self.idx(x, y)]

    def fill_rect(self, x: int, y: int, w: int, h: int, tile: int,
                  layer: str = "lower") -> None:
        setter = self.set_lower if layer == "lower" else self.set_upper
        for dy in range(h):
            for dx in range(w):
                setter(x + dx, y + dy, tile)

    def rect_outline(self, x: int, y: int, w: int, h: int, tile: int,
                     layer: str = "lower") -> None:
        setter = self.set_lower if layer == "lower" else self.set_upper
        for dx in range(w):
            setter(x + dx, y, tile)
            setter(x + dx, y + h - 1, tile)
        for dy in range(h):
            setter(x, y + dy, tile)
            setter(x + w - 1, y + dy, tile)

    # -- events --------------------------------------------------------------
    def add_event(self, name: str, x: int, y: int,
                  pages: Sequence[Page]) -> Event:
        event = Event(self._next_event_id, name, x, y, list(pages))
        self._next_event_id += 1
        self.events.append(event)
        return event

    def to_xml(self) -> str:
        node = Node("Map")
        node.set("chipset_id", self.chipset_id)
        node.set("width", self.width)
        node.set("height", self.height)
        node.set("scroll_type", self.scroll_type)
        node.set("parallax_flag", self.parallax is not None)
        node.set("parallax_name", self.parallax or "")
        node.set("parallax_loop_x", self.parallax_loop_x)
        node.set("parallax_loop_y", self.parallax_loop_y)
        node.set("parallax_auto_loop_x", self.parallax_auto_x != 0)
        node.set("parallax_sx", self.parallax_auto_x)
        node.set("parallax_auto_loop_y", self.parallax_auto_y != 0)
        node.set("parallax_sy", self.parallax_auto_y)
        node.set("lower_layer", self.lower)
        node.set("upper_layer", self.upper)
        node.add(collection("events", [(e.ident, e.to_node()) for e in self.events]))
        node.set("save_count", 0)
        return document("LMU", node)


@dataclass
class MapInfo:
    ident: int
    name: str
    parent: int = 0
    indentation: int = 1
    type: int = 1              # 0 root, 1 map, 2 area
    music_type: int = 0        # 0 inherit, 1 none, 2 specified
    music_name: str = "(OFF)"
    music_fadein: int = 0
    background_type: int = 0
    background_name: str = ""
    teleport: int = 0          # 0 inherit, 1 allow, 2 forbid
    escape: int = 0
    save: int = 0

    def to_node(self) -> Node:
        node = Node("MapInfo")
        node.set("name", self.name)
        node.set("parent_map", self.parent)
        node.set("indentation", self.indentation)
        node.set("type", self.type)
        node.set("expanded_node", True)
        node.set("music_type", self.music_type)
        node.add(music(self.music_name, fadein=self.music_fadein, volume=90))
        node.set("background_type", self.background_type)
        node.set("background_name", self.background_name)
        node.set("teleport", self.teleport)
        node.set("escape", self.escape)
        node.set("save", self.save)
        node.set("encounter_steps", 0)
        return node


def build_treemap(infos: Sequence[MapInfo], *, start_map: int, start_x: int,
                  start_y: int) -> str:
    root = MapInfo(0, "LIMINAL", parent=0, indentation=0, type=0,
                   music_type=1, music_name="(OFF)")
    node = Node("TreeMap")
    node.add(collection("maps",
                        [(info.ident, info.to_node()) for info in [root, *infos]]))
    node.set("tree_order", [0] + [info.ident for info in infos])
    node.set("active_node", 1)
    start = node.add(Node("start")).add(Node("Start"))
    start.set("party_map_id", start_map)
    start.set("party_x", start_x)
    start.set("party_y", start_y)
    start.set("boat_map_id", 0)
    start.set("boat_x", 0)
    start.set("boat_y", 0)
    start.set("ship_map_id", 0)
    start.set("ship_x", 0)
    start.set("ship_y", 0)
    start.set("airship_map_id", 0)
    start.set("airship_x", 0)
    start.set("airship_y", 0)
    return document("LMT", node)
