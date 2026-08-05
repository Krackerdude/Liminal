"""Chipset construction.

An RPG Maker 2000 chipset is a 480x256 sheet whose regions mean different
things.  We use three of them:

* **Block E** (ids 5000..5143) — 144 plain lower-layer tiles.  Columns 12..17
  hold the first 96, columns 18..23 rows 0..7 the rest.
* **Block F** (ids 10000..10143) — 144 plain upper-layer tiles.  Columns 18..23
  rows 8..15 hold the first 48, columns 24..29 the rest.
* **Block C** (ids 3000, 3050, 3100) — three animated lower tiles, each a
  four-frame strip down rows 4..7 of columns 3..5, cycling at 10fps.

Because dreams are built at the wrong scale, most of what goes in here is not
a 16x16 tile but a *multi-tile object*: a giant digit, a stone hand, a house
sized like a toy.  :meth:`ChipsetBuilder.add_object` slices those into tiles
and hands back a grid the map generator can stamp down in one go.

House rules, enforced by what these primitives will and won't do:
flat colour with one or two shades, rounded corners, outlines in a darker
version of the local colour, and no texture noise anywhere.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .canvas import (BAYER4, BAYER8, Canvas, RGB, TRANSPARENT, blend, cooler,
                     outline_in, shade_of, warmer)
from .palette import Palette

TILE = 16
SHEET_W, SHEET_H = 480, 256

# Passability bits (EasyRPG Player's Passable enum).
PASS_DOWN, PASS_LEFT, PASS_RIGHT, PASS_UP = 1, 2, 4, 8
PASS_ALL = PASS_DOWN | PASS_LEFT | PASS_RIGHT | PASS_UP
PASS_NONE = 0
PASS_ABOVE = 16

BLOCK_A, BLOCK_E, BLOCK_F, BLOCK_C = 0, 5000, 10000, 3000


def _block_e_cell(index: int) -> tuple[int, int]:
    if index < 96:
        return 12 + index % 6, index // 6
    return 18 + (index - 96) % 6, (index - 96) // 6


def _block_f_cell(index: int) -> tuple[int, int]:
    if index < 48:
        return 18 + index % 6, 8 + index // 6
    return 24 + (index - 48) % 6, (index - 48) // 6


@dataclass
class TileGrid:
    """A multi-tile object, as a grid of tile ids ready to stamp onto a map."""
    name: str
    cols: int
    rows: int
    ids: list[list[int]]
    upper: bool = False

    def __iter__(self):
        for row in range(self.rows):
            for col in range(self.cols):
                yield col, row, self.ids[row][col]


@dataclass
class ChipsetBuild:
    """The finished sheet plus everything the database and maps need."""
    name: str
    sheet: Canvas
    tiles: dict[str, int]
    objects: dict[str, TileGrid]
    passable_lower: list[int]
    passable_upper: list[int]
    terrain: list[int]
    animation_type: int = 0
    animation_speed: int = 12

    def tile(self, name: str) -> int:
        return self.tiles[name]

    def obj(self, name: str) -> TileGrid:
        return self.objects[name]


class ChipsetBuilder:
    def __init__(self, name: str, palette: Palette):
        self.name = name
        self.pal = palette
        self.sheet = Canvas(SHEET_W, SHEET_H, palette.void)
        self.tiles: dict[str, int] = {}
        self.objects: dict[str, TileGrid] = {}
        self._lower_next = 0
        self._upper_next = 0
        self._animated_next = 0
        self.passable_lower = [PASS_ALL] * 162
        self.passable_upper = [PASS_ALL] * 144
        self.terrain = [1] * 162
        self.animation_type = 0
        self.animation_speed = 12
        # Identical artwork gets one slot, not one per user.  Objects repeat
        # themselves constantly — the flat middle of a block, a run of wall,
        # the same shadow under six different props — and a sheet has only 144
        # slots per layer to spend.
        self._seen_lower: dict[tuple, int] = {}
        self._seen_upper: dict[tuple, int] = {}
        # Upper index 0 is reserved and blank: it is what an empty upper cell
        # points at.  See maps.EMPTY_UPPER for why an empty cell cannot simply
        # be zero.
        #
        # ``above=True`` is load-bearing and not about draw order.  The engine
        # reads a passable upper tile that is *not* marked above-hero as "this
        # cell is walkable, ignore the lower layer" — so a blank passable tile
        # covering every cell in the map made the entire world walkable, walls
        # and all.  Marked above-hero, it defers to the floor underneath, which
        # is what "nothing here" is supposed to mean.
        self.add_upper("empty", Canvas(TILE, TILE, TRANSPARENT), above=True)

    # -- single tiles --------------------------------------------------------
    def add(self, name: str, tile: Canvas, *, passable: bool = True,
            terrain: int = 1) -> int:
        if self._lower_next >= 144:
            raise ValueError(f"{self.name}: out of block E slots")
        if _has_transparency(tile):
            # The lower layer has nothing behind it, so a see-through tile
            # would punch a black hole in the floor.
            raise ValueError(
                f"{self.name}: lower tile {name!r} has transparent pixels; "
                f"it belongs on the upper layer")
        key = (tile.px.tobytes(), passable, terrain)
        if key in self._seen_lower:
            tile_id = self._seen_lower[key]
            self.tiles[name] = tile_id
            return tile_id
        index = self._lower_next
        self._lower_next += 1
        col, row = _block_e_cell(index)
        self.sheet.paste(tile, col * TILE, row * TILE)
        self.passable_lower[18 + index] = PASS_ALL if passable else PASS_NONE
        self.terrain[18 + index] = terrain
        tile_id = BLOCK_E + index
        self.tiles[name] = tile_id
        self._seen_lower[key] = tile_id
        return tile_id

    def add_upper(self, name: str, tile: Canvas, *, passable: bool = True,
                  above: bool = False) -> int:
        """Add an overlay tile.  ``above`` draws it in front of the player."""
        key = (tile.px.tobytes(), passable, above)
        if key in self._seen_upper:
            tile_id = self._seen_upper[key]
            self.tiles[name] = tile_id
            return tile_id
        if self._upper_next >= 144:
            raise ValueError(f"{self.name}: out of block F slots")
        index = self._upper_next
        self._upper_next += 1
        col, row = _block_f_cell(index)
        self.sheet.paste(tile, col * TILE, row * TILE)
        bits = PASS_ALL if passable else PASS_NONE
        if above:
            bits |= PASS_ABOVE
        self.passable_upper[index] = bits
        tile_id = BLOCK_F + index
        self.tiles[name] = tile_id
        self._seen_upper[key] = tile_id
        return tile_id

    def add_animated(self, name: str, frames: Sequence[Canvas], *,
                     passable: bool = True, terrain: int = 1) -> int:
        """Add a four-frame animated lower tile (three slots exist per sheet)."""
        if self._animated_next >= 3:
            raise ValueError(f"{self.name}: only three block C slots exist")
        slot = self._animated_next
        self._animated_next += 1
        col = 3 + slot
        for step in range(4):
            self.sheet.paste(frames[step % len(frames)], col * TILE,
                             (4 + step) * TILE)
        self.passable_lower[3 + slot] = PASS_ALL if passable else PASS_NONE
        self.terrain[3 + slot] = terrain
        tile_id = BLOCK_C + slot * 50
        self.tiles[name] = tile_id
        return tile_id

    # -- multi-tile objects --------------------------------------------------
    def add_object(self, name: str, art: Canvas, *, solid: str = "all",
                   upper: bool | None = None, above: bool | None = None,
                   terrain: int = 1) -> TileGrid:
        """Slice a large drawing into tiles and register it as one object.

        ``solid`` says which sub-tiles block movement:

        ``"all"``      every tile (a wall, a block, a mountain)
        ``"none"``     nothing (decals, shadows, painted ground)
        ``"bottom"``   only the lowest row, so you can walk behind the top of
                       a tree or a hand and be drawn in front of it
        ``"bottom2"``  the lowest two rows, for very tall things

        **The art decides the layer, not the caller.**  Anything with a
        transparent pixel in it goes on the upper layer, where whatever floor
        is really underneath shows through; only art that is opaque to the
        edges may sit on the lower layer, which is a *surface* and not a place
        to put things.

        This used to work the other way round — objects were composited onto a
        copy of the ground tile so they could live on the lower layer — and the
        result was that every prop carried a square of plain floor around with
        it and stamped it over whatever pattern, mural or carpet it landed on.
        Densely painted floors were being punched full of holes by the objects
        standing on them.  An object is an object; it does not get to decide
        what it is standing on.

        Draw order follows from the same rule: a non-solid row with solid rows
        beneath it is the part of a standing thing you can walk behind, so it
        is drawn in front of the player.  Everything else draws behind them.
        """
        cols, rows = art.w // TILE, art.h // TILE
        pieces: dict[tuple[int, int], Canvas] = {}
        opaque = True
        for row in range(rows):
            for col in range(cols):
                piece = art.sub(col * TILE, row * TILE, TILE, TILE)
                if _is_blank(piece):
                    continue
                pieces[(col, row)] = piece
                if _has_transparency(piece):
                    opaque = False
        if upper is None:
            upper = not opaque

        def row_solid(row: int) -> bool:
            if solid == "all":
                return True
            if solid == "bottom":
                return row == rows - 1
            if solid == "bottom2":
                return row >= rows - 2
            return False

        ids = [[0] * cols for _ in range(rows)]
        for (col, row), piece in pieces.items():
            blocking = row_solid(row)
            piece_name = f"{name}:{col},{row}"
            if upper:
                in_front = above
                if in_front is None:
                    in_front = not blocking and any(row_solid(r)
                                                    for r in range(row + 1, rows))
                ids[row][col] = self.add_upper(
                    piece_name, piece, passable=not blocking, above=in_front)
            else:
                ids[row][col] = self.add(
                    piece_name, piece, passable=not blocking, terrain=terrain)
        grid = TileGrid(name, cols, rows, ids, upper=upper)
        self.objects[name] = grid
        return grid

    def add_flow(self, frames: Sequence[Canvas], *, speed: int = 8,
                 name: str = "flow", passable: bool = True,
                 terrain: int = 1) -> int:
        """A fourth animated tile, using the block A autotile slot.

        Block C only gives three animated tiles per sheet, which is not enough
        for a world that is supposed to be moving everywhere you look.  The
        autotile machinery composes tile id 0 out of quarters taken from row 4
        of columns 0..2, so filling those three cells with three frames yields
        one more animated tile — and unlike block C its speed is adjustable.
        """
        for step in range(3):
            self.sheet.paste(frames[step % len(frames)], step * TILE, 4 * TILE)
        self.animation_type = 1          # three frames, cycled
        self.animation_speed = speed
        self.tiles[name] = BLOCK_A
        self.passable_lower[0] = PASS_ALL if passable else PASS_NONE
        self.terrain[0] = terrain
        self._flow_used = True
        return BLOCK_A

    def fill_autotile_area(self, tile: Canvas) -> None:
        """Paint the unused autotile region so stray ids never show garbage."""
        for col in range(0, 12):
            for row in range(0, 16):
                if 3 <= col <= 5 and 4 <= row <= 7:
                    continue          # block C animation strips live here
                if getattr(self, "_flow_used", False) and col <= 2 and row == 4:
                    continue          # and the block A frames live here
                self.sheet.paste(tile, col * TILE, row * TILE)

    def finish(self) -> ChipsetBuild:
        return ChipsetBuild(
            name=self.name, sheet=self.sheet, tiles=dict(self.tiles),
            objects=dict(self.objects),
            passable_lower=list(self.passable_lower),
            passable_upper=list(self.passable_upper),
            terrain=list(self.terrain),
            animation_type=self.animation_type,
            animation_speed=self.animation_speed,
        )


def _has_transparency(tile: Canvas) -> bool:
    return bool(np.any(np.all(tile.px == np.array(TRANSPARENT, dtype=np.uint8),
                              axis=-1)))


def _is_blank(tile: Canvas) -> bool:
    return bool(np.all(tile.px == np.array(TRANSPARENT, dtype=np.uint8)))


# --- ground ------------------------------------------------------------------
# Ground tiles are the one place a little dithering earns its keep: a soft
# two-tone blend over a very large area reads as light, not as texture.

def flat(color: RGB) -> Canvas:
    return Canvas(TILE, TILE, color)


def soft_ground(base: RGB, second: RGB, amount: float = 0.25,
                offset: tuple[int, int] = (0, 0)) -> Canvas:
    """Flat ground with a whisper of a second tone mixed through it."""
    tile = Canvas(TILE, TILE, base)
    tile.dither(second, amount, BAYER8, offset=offset)
    return tile


def brick_ground(pal: Palette, *, course: int = 8, offset: int = 0) -> Canvas:
    """Big soft brick.  Two tones and a mortar line, nothing else."""
    tile = Canvas(TILE, TILE, pal.form)
    for row in range(0, TILE, course):
        stagger = (offset + (row // course) * (TILE // 2)) % TILE
        tile.hline(row, 0, TILE - 1, pal.form_light)
        for x in range(stagger, stagger + TILE + 1, TILE // 2):
            tile.vline(x % TILE, row, row + course - 1, pal.form_light)
    return tile


def checker_ground(a: RGB, b: RGB, size: int = 8) -> Canvas:
    return Canvas(TILE, TILE).checker(a, b, size)


def star_ground(pal: Palette, seed: int = 0, *, density: int = 3) -> Canvas:
    """Deep water with a few stars in it — placed by hand, not scattered."""
    tile = Canvas(TILE, TILE, pal.ground)
    tile.dither(pal.ground_b, 0.35, BAYER8)
    spots = [(3, 4), (11, 9), (6, 13), (13, 2), (1, 10)][:density]
    for x, y in spots:
        tile.dot(x, y, pal.accent)
        tile.dot(x - 1, y, pal.accent_soft)
        tile.dot(x + 1, y, pal.accent_soft)
        tile.dot(x, y - 1, pal.accent_soft)
        tile.dot(x, y + 1, pal.accent_soft)
    return tile


def path_ground(pal: Palette) -> Canvas:
    """A lighter walked-on strip, for suggesting where people went."""
    tile = Canvas(TILE, TILE, pal.ground_b)
    tile.dither(warmer(pal.ground, 0.3), 0.55, BAYER4)
    return tile


def grass_ground(pal: Palette, seed: int = 0) -> Canvas:
    """Grass implied by six blades, not three hundred."""
    tile = Canvas(TILE, TILE, pal.ground)
    tile.dither(pal.ground_b, 0.3, BAYER8)
    blades = [(2, 5), (7, 3), (12, 8), (5, 12), (10, 14), (14, 11)]
    tint = cooler(pal.ground, 0.18)
    for i, (x, y) in enumerate(blades):
        if (i + seed) % 3 == 0:
            continue
        tile.dot(x, y, tint)
        tile.dot(x, y - 1, tint)
    return tile


def void_tile(pal: Palette) -> Canvas:
    return Canvas(TILE, TILE, pal.void)


# --- large forms -------------------------------------------------------------
# Everything below returns a canvas whose size is a multiple of 16, meant for
# ChipsetBuilder.add_object.

def _canvas(cols: int, rows: int) -> Canvas:
    return Canvas(cols * TILE, rows * TILE, TRANSPARENT)


def wall_run(pal: Palette, *, height: int = 3, brick: bool = True) -> Canvas:
    """A single tile-wide column of wall with a lit cap.

    Walls are drawn as one tall object rather than three loose tiles so the
    cap highlight lines up with the shadow at the base every time.
    """
    art = _canvas(1, height)
    art.rect(0, 0, TILE, height * TILE, pal.form)
    art.rect(0, 0, TILE, 4, pal.form_light)
    if brick:
        for row in range(4, height * TILE, 8):
            art.hline(row, 0, TILE - 1, cooler(pal.form, 0.12))
            stagger = 0 if (row // 8) % 2 else TILE // 2
            art.vline(stagger, row, row + 7, cooler(pal.form, 0.12))
    art.rect(0, height * TILE - 3, TILE, 3, pal.form_dark)
    return art


def big_digit(pal: Palette, digit: int, cols: int = 3, rows: int = 4) -> Canvas:
    """An oversized numeral, standing in the landscape like architecture."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    thick = max(5, w // 6)
    body, shade, edge = pal.form, pal.form_dark, pal.form_light

    def bar(x, y, bw, bh):
        art.round_rect(x, y, bw, bh, min(thick // 2, 4), body)

    inset = thick
    top, mid, bot = inset, h // 2 - thick // 2, h - inset - thick
    left, right = inset, w - inset - thick
    seg = {
        "a": (left, top, w - 2 * inset, thick),
        "d": (left, bot, w - 2 * inset, thick),
        "g": (left, mid, w - 2 * inset, thick),
        "f": (left, top, thick, mid - top + thick),
        "b": (right, top, thick, mid - top + thick),
        "e": (left, mid, thick, bot - mid + thick),
        "c": (right, mid, thick, bot - mid + thick),
    }
    lit = {
        0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc",
        5: "afgcd", 6: "afgecd", 7: "abc", 8: "abcdefg", 9: "abcfgd",
    }[digit % 10]
    for key in lit:
        bar(*seg[key])
    solid = np.any(art.px != np.array(TRANSPARENT, np.uint8), axis=-1)
    lower = np.zeros_like(solid)
    lower[3:, :] = solid[:-3, :]
    art.px[solid & ~lower] = edge
    bottom = np.zeros_like(solid)
    bottom[:-2, :] = solid[2:, :]
    art.px[solid & ~bottom] = shade
    return outline_in(art, cooler(pal.form_dark, 0.3))


def toy_block(pal: Palette, color: RGB, cols: int = 3, rows: int = 3, *,
              mark: str = "dot") -> Canvas:
    """A children's building block, scaled up to the size of a house."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(0, 0, w, h, 5, color)
    art.round_rect(0, 0, w, 6, 5, warmer(color, 0.3))
    art.rect(0, h - 5, w, 5, cooler(color, 0.28))
    art.rect(w - 5, 6, 5, h - 11, cooler(color, 0.16))
    face = warmer(color, 0.55)
    cx, cy = w // 2, h // 2
    if mark == "dot":
        art.blob(cx, cy, min(w, h) * 0.22, face)
    elif mark == "ring":
        art.ellipse(cx, cy, min(w, h) * 0.26, min(w, h) * 0.26, face, filled=False)
    elif mark == "square":
        art.round_rect(cx - w // 6, cy - h // 6, w // 3, h // 3, 2, face)
    elif mark == "cross":
        art.rect(cx - w // 5, cy - 3, 2 * w // 5, 6, face)
        art.rect(cx - 3, cy - h // 5, 6, 2 * h // 5, face)
    return outline_in(art, cooler(color, 0.45))


def round_tree(pal: Palette, cols: int = 3, rows: int = 4, *,
               face: bool = False) -> Canvas:
    """A chunky tree: one big canopy, one thick trunk, no leaf texture."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    trunk_w = max(8, w // 4)
    trunk_top = int(h * 0.52)
    art.round_rect(w // 2 - trunk_w // 2, trunk_top, trunk_w, h - trunk_top - 1,
                   3, pal.form)
    art.rect(w // 2 - trunk_w // 2, trunk_top, 3, h - trunk_top - 1, pal.form_light)
    art.rect(w // 2 + trunk_w // 2 - 3, trunk_top, 3, h - trunk_top - 1, pal.form_dark)

    canopy = pal.accent_soft
    art.blob(w * 0.5, h * 0.30, w * 0.44, canopy, squash=0.86)
    art.blob(w * 0.28, h * 0.36, w * 0.26, canopy)
    art.blob(w * 0.72, h * 0.36, w * 0.26, canopy)
    art.blob(w * 0.40, h * 0.22, w * 0.22, warmer(canopy, 0.22))

    if face:
        # A carved smile, at trunk height.  It does not move.
        eye = cooler(pal.form_dark, 0.35)
        fy = trunk_top + 7
        art.rect(w // 2 - 4, fy, 2, 3, eye)
        art.rect(w // 2 + 2, fy, 2, 3, eye)
        art.hline(fy + 6, w // 2 - 4, w // 2 + 3, eye)
        art.dot(w // 2 - 5, fy + 5, eye)
        art.dot(w // 2 + 4, fy + 5, eye)
    return outline_in(art, cooler(pal.form_dark, 0.35))


def stone_hand(pal: Palette, cols: int = 3, rows: int = 4, *,
               pose: str = "up") -> Canvas:
    """An enormous hand coming out of the ground.  No explanation is given."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    stone, light, dark = pal.form, pal.form_light, pal.form_dark

    palm_top = int(h * 0.46)
    art.round_rect(w // 2 - w // 4, palm_top, w // 2, h - palm_top, 6, stone)

    if pose == "broken":
        # A hand that fell over: the palm lies flat, fingers splayed towards
        # the right, and the wrist ends in a shadowed break.
        art.px[:, :] = TRANSPARENT
        palm_w = int(w * 0.42)
        palm_h = int(h * 0.46)
        palm_x = 4
        palm_y = h - palm_h - 3
        art.round_rect(palm_x, palm_y, palm_w, palm_h, 6, stone)
        art.round_rect(palm_x, palm_y, palm_w, 5, 4, light)
        art.rect(palm_x, palm_y + palm_h - 4, palm_w, 4, dark)
        finger_h = max(5, palm_h // 5)
        for index, length in enumerate((0.34, 0.42, 0.38, 0.28)):
            fx = palm_x + palm_w - 3
            fy = palm_y + 3 + index * (finger_h + 1)
            art.round_rect(fx, fy, int(w * length), finger_h,
                           finger_h // 2, stone)
            art.rect(fx, fy, int(w * length), 2, light)
        # the break: a hard vertical face where the wrist snapped off
        art.rect(palm_x, palm_y, 5, palm_h, dark)
        art.rect(palm_x + 1, palm_y + 4, 3, palm_h - 9, cooler(dark, 0.4))
        return outline_in(art, cooler(dark, 0.3))

    finger_w = max(5, w // 8)
    lengths = (0.30, 0.16, 0.12, 0.20) if pose == "up" else (0.20, 0.14, 0.10, 0.16)
    for index, frac in enumerate(lengths):
        fx = w // 2 - w // 4 + 2 + index * (finger_w + 2)
        top = int(palm_top - h * frac)
        art.round_rect(fx, top, finger_w, palm_top - top + 8, finger_w // 2, stone)
        art.rect(fx, top, 2, palm_top - top + 8, light)
    thumb_x = w // 2 + w // 5
    art.round_rect(thumb_x, palm_top + 4, finger_w, int(h * 0.22),
                   finger_w // 2, stone)
    art.rect(w // 2 - w // 4, palm_top, 4, h - palm_top, light)
    art.rect(w // 2 + w // 4 - 4, palm_top, 4, h - palm_top, dark)
    return outline_in(art, cooler(dark, 0.3))


def floating_stair(pal: Palette, cols: int = 4, rows: int = 3, *,
                   rising: bool = True) -> Canvas:
    """A flight of steps with nothing holding it up."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    steps = cols * 2
    step_w = w // steps
    step_h = max(4, h // (steps + 1))
    for index in range(steps):
        x = index * step_w
        y = (h - step_h * (index + 1)) if rising else (step_h * index)
        art.rect(x, y, step_w + 1, step_h + 2, pal.form)
        art.rect(x, y, step_w + 1, 2, pal.form_light)
        art.rect(x, y + step_h, step_w + 1, 2, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.25))


def umbrella(pal: Palette, color: RGB, cols: int = 3, rows: int = 4) -> Canvas:
    """An umbrella standing where a tree should be."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    canopy_y = int(h * 0.36)
    canopy_r = w * 0.50

    # Canopy first: a dome, clipped flat, then scalloped along its lower edge
    # so it gets the little bumps a real umbrella has.
    art.ellipse(w / 2, canopy_y, canopy_r, canopy_r * 0.82, color)
    art.rect(0, canopy_y, w, h - canopy_y, TRANSPARENT)
    scallop_r = canopy_r * 0.24
    for i in range(-2, 3):
        art.blob(w / 2 + i * canopy_r * 0.44, canopy_y - 1, scallop_r, color)
    for i in range(-2, 3):
        art.line(int(w / 2), int(canopy_y - canopy_r * 0.74),
                 int(w / 2 + i * canopy_r * 0.44), canopy_y - 1,
                 cooler(color, 0.22))
    art.ellipse(w / 2 - canopy_r * 0.20, canopy_y - canopy_r * 0.40,
                canopy_r * 0.32, canopy_r * 0.20, warmer(color, 0.32))
    # Finial, then the shaft and a hooked handle, drawn last so nothing clips
    # them away.
    art.rect(w // 2 - 1, canopy_y - int(canopy_r * 0.95), 2,
             int(canopy_r * 0.26), pal.form_dark)
    art.rect(w // 2 - 1, canopy_y - 2, 2, h - canopy_y - 4, pal.form_dark)
    art.rect(w // 2 - 4, h - 7, 3, 2, pal.form_dark)
    art.rect(w // 2 - 4, h - 6, 2, 4, pal.form_dark)
    return outline_in(art, cooler(color, 0.4))


def little_house(pal: Palette, color: RGB, cols: int = 4, rows: int = 4) -> Canvas:
    """A small house, alone, in the middle of nowhere."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    body_top = int(h * 0.38)
    art.round_rect(4, body_top, w - 8, h - body_top - 2, 3, pal.form_light)
    # roof: a big simple triangle, wider than the house
    for row in range(body_top):
        span = int((row / body_top) * (w - 2))
        art.hline(row + 2, w // 2 - span // 2, w // 2 + span // 2, color)
    art.hline(body_top + 1, 1, w - 2, cooler(color, 0.3))
    door_w = max(8, w // 5)
    art.round_rect(w // 2 - door_w // 2, h - 2 - int(h * 0.28), door_w,
                   int(h * 0.28), 2, pal.form_dark)
    art.round_rect(7, body_top + 6, 9, 8, 2, pal.accent)
    art.round_rect(w - 16, body_top + 6, 9, 8, 2, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def crayon(pal: Palette, color: RGB, cols: int = 2, rows: int = 5) -> Canvas:
    """A crayon standing up like a pillar, because you are three inches tall."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    tip = int(h * 0.16)
    for row in range(tip):
        span = int((row / tip) * (w - 8)) + 3
        art.hline(row + 1, w // 2 - span // 2, w // 2 + span // 2,
                  warmer(color, 0.35))
    art.rect(4, tip, w - 8, h - tip - 1, color)
    art.rect(4, tip, 3, h - tip - 1, warmer(color, 0.3))
    art.rect(w - 7, tip, 3, h - tip - 1, cooler(color, 0.28))
    art.rect(4, tip + 6, w - 8, 4, warmer(color, 0.55))
    art.rect(4, h - 12, w - 8, 4, warmer(color, 0.55))
    return outline_in(art, cooler(color, 0.42))


def die_block(pal: Palette, cols: int = 3, rows: int = 3, pips: int = 5) -> Canvas:
    """A die the size of a hill."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(0, 0, w, h, 6, (246, 242, 234))
    art.round_rect(0, 0, w, 5, 6, (255, 254, 250))
    art.rect(0, h - 5, w, 5, (206, 198, 190))
    spots = {
        1: [(0.5, 0.5)],
        2: [(0.28, 0.28), (0.72, 0.72)],
        3: [(0.26, 0.26), (0.5, 0.5), (0.74, 0.74)],
        5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
    }[pips]
    for fx, fy in spots:
        art.blob(w * fx, h * fy, max(2.5, w * 0.09), (58, 52, 58))
    return outline_in(art, (176, 168, 162))


def door_frame(pal: Palette, cols: int = 2, rows: int = 3, *,
               glow: RGB | None = None, leaf: RGB | None = None,
               arch: bool = True) -> Canvas:
    """A door standing on its own.  The most important object in the game.

    Flat colour, an arched head, two sunken panels and a round handle — it has
    to read as *door* at a glance from across a dark room, because that glance
    is the only invitation the game ever offers.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    body = leaf or pal.form
    jamb = pal.form_dark

    top = 2
    radius = (w // 2 - 1) if arch else 3
    art.round_rect(0, top, w, h - top, radius, jamb)
    art.round_rect(2, top + 2, w - 4, h - top - 2, max(0, radius - 2), body)
    art.round_rect(2, top + 2, 3, h - top - 2, 1, warmer(body, 0.22))
    art.rect(w - 5, top + 6, 3, h - top - 8, cooler(body, 0.20))

    if glow is not None:
        # An open door: the leaf is replaced by soft light, flat-shaded in two
        # steps rather than a gradient.
        art.round_rect(2, top + 2, w - 4, h - top - 2, max(0, radius - 2),
                       cooler(glow, 0.35))
        art.round_rect(4, top + 5, w - 8, h - top - 5, max(0, radius - 4), glow)
        art.round_rect(6, top + 8, w - 12, h - top - 10, max(0, radius - 6),
                       warmer(glow, 0.45))
    else:
        panel_w, panel_h = w - 12, (h - top - 12) // 2
        art.round_rect(6, top + 8, panel_w, panel_h, 2, cooler(body, 0.16))
        art.round_rect(7, top + 9, panel_w - 2, panel_h - 2, 2, body)
        art.round_rect(6, top + 12 + panel_h, panel_w, panel_h, 2,
                       cooler(body, 0.16))
        art.round_rect(7, top + 13 + panel_h, panel_w - 2, panel_h - 2, 2, body)
        art.blob(w - 7, h // 2 + 2, 2.2, pal.accent)
        art.dot(w - 8, h // 2 + 1, warmer(pal.accent, 0.5))
    return outline_in(art, cooler(jamb, 0.35))


def lamp_post(pal: Palette, cols: int = 1, rows: int = 4) -> Canvas:
    """A light on a pole.  In most of these worlds it is the only weather."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 1, 10, 3, h - 12, pal.form_dark)
    art.blob(w / 2, 8, 6, pal.accent_soft)
    art.blob(w / 2, 8, 4, pal.accent)
    art.blob(w / 2 - 1, 6.5, 2, warmer(pal.accent, 0.6))
    art.round_rect(w // 2 - 4, h - 4, 9, 4, 2, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def scrawl(pal: Palette, kind: str, cols: int = 4, rows: int = 4) -> Canvas:
    """Enormous glowing graffiti on a black void: an eye, a spiral, a mouth."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    ink, halo = pal.form, pal.form_dark

    def stroke(points, thickness=3, color=None):
        color = color or ink
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            steps = int(max(abs(x1 - x0), abs(y1 - y0), 1))
            for s in range(steps + 1):
                t = s / steps
                cx = round(x0 + (x1 - x0) * t)
                cy = round(y0 + (y1 - y0) * t)
                art.blob(cx, cy, thickness / 2, color)

    if kind == "eye":
        art.ellipse(w / 2, h / 2, w * 0.44, h * 0.26, ink, filled=False)
        art.ellipse(w / 2, h / 2, w * 0.42, h * 0.24, halo)
        art.blob(w / 2, h / 2, w * 0.16, ink)
        art.blob(w / 2, h / 2, w * 0.08, pal.void)
        art.blob(w / 2 - w * 0.06, h / 2 - h * 0.05, w * 0.04, pal.form_light)
    elif kind == "spiral":
        import math
        points = []
        for step in range(64):
            angle = step * 0.42
            radius = 3 + step * (w * 0.007)
            points.append((w / 2 + math.cos(angle) * radius,
                           h / 2 + math.sin(angle) * radius * 0.9))
        stroke(points, 3)
    elif kind == "mouth":
        # A wide grin: a filled lens shape with teeth notched out of it, so it
        # reads as a mouth rather than as two strokes that happen to meet.
        art.ellipse(w / 2, h * 0.42, w * 0.42, h * 0.30, ink)
        art.rect(0, 0, w, int(h * 0.42), TRANSPARENT)
        art.ellipse(w / 2, h * 0.44, w * 0.34, h * 0.22, pal.void)
        for i in range(6):
            x = int(w * (0.20 + i * 0.12))
            art.rect(x, int(h * 0.44), 3, int(h * 0.16), ink)
        art.hline(int(h * 0.42), int(w * 0.09), int(w * 0.91), ink)
        art.hline(int(h * 0.43), int(w * 0.09), int(w * 0.91), ink)
    elif kind == "arrow":
        stroke([(w * 0.5, h * 0.85), (w * 0.5, h * 0.18)], 4)
        stroke([(w * 0.22, h * 0.45), (w * 0.5, h * 0.15), (w * 0.78, h * 0.45)], 4)
    else:  # "star"
        import math
        pts = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = (w * 0.44) if i % 2 == 0 else (w * 0.18)
            pts.append((w / 2 + math.cos(angle) * radius,
                        h / 2 + math.sin(angle) * radius))
        pts.append(pts[0])
        stroke(pts, 3)
    return art


def tiny_structure(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """A small pale shape alone in the sand.  Deliberately unreadable."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(w // 4, h // 3, w // 2, h - h // 3 - 2, 3, pal.form)
    art.rect(w // 4, h // 3, 3, h - h // 3 - 2, pal.form_light)
    art.round_rect(w // 4 - 3, h // 3 - 4, w // 2 + 6, 5, 2, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.25))


def telephone_pole(pal: Palette, cols: int = 3, rows: int = 5) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 2, 6, 5, h - 8, pal.form)
    art.rect(w // 2 - 2, 6, 2, h - 8, pal.form_light)
    for y in (14, 24):
        art.rect(6, y, w - 12, 3, pal.form)
        art.rect(6, y, w - 12, 1, pal.form_light)
    art.rect(w // 2 - 5, h - 4, 11, 4, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.3))


# --- overlays and animation --------------------------------------------------

def soft_shadow(pal: Palette, side: str = "top", depth: int = 5) -> Canvas:
    """A gentle occlusion strip laid on the ground beside a solid form."""
    tile = Canvas(TILE, TILE, TRANSPARENT)
    for i in range(depth):
        amount = 0.42 * (1 - i / depth)
        color = blend(pal.ground, cooler(pal.ground, 0.55), amount)
        if side == "top":
            tile.hline(i, 0, TILE - 1, color)
        elif side == "bottom":
            tile.hline(TILE - 1 - i, 0, TILE - 1, color)
        elif side == "left":
            tile.vline(i, 0, TILE - 1, color)
        else:
            tile.vline(TILE - 1 - i, 0, TILE - 1, color)
    return tile


def glow_pool(pal: Palette) -> Canvas:
    """The soft patch of light a lamp throws onto the ground below it."""
    tile = Canvas(TILE, TILE, pal.ground)
    ys, xs = np.mgrid[0:TILE, 0:TILE]
    d = np.sqrt((xs - 7.5) ** 2 + (ys - 7.5) ** 2) / 11.0
    amount = np.clip(1 - d, 0, 1) ** 1.3
    threshold = BAYER8[ys % 8, xs % 8]
    tile.px[amount > threshold] = blend(pal.ground, pal.accent, 0.30)
    tile.px[amount * 0.5 > threshold] = blend(pal.ground, pal.accent, 0.55)
    return tile


def ripple_frames(pal: Palette) -> list[Canvas]:
    """Four frames of something almost still."""
    frames = []
    for phase in range(4):
        tile = Canvas(TILE, TILE, pal.ground)
        tile.dither(pal.ground_b, 0.3, BAYER8, offset=(phase, 0))
        for x in range(TILE):
            y = int(6 + 3 * np.sin((x + phase * 4) * 0.45))
            tile.dot(x, y, pal.accent_soft)
            tile.dot((x + 8) % TILE, (y + 7) % TILE, pal.accent_soft)
        return_frames = frames
        frames.append(tile)
    return frames


def pulse_frames(pal: Palette, color: RGB | None = None) -> list[Canvas]:
    """A light that breathes rather than flickers."""
    tone = color or pal.accent
    frames = []
    for level in (1.0, 0.82, 0.66, 0.82):
        tile = Canvas(TILE, TILE, pal.ground)
        tile.blob(7.5, 7.5, 7, blend(pal.ground, tone, 0.30 * level))
        tile.blob(7.5, 7.5, 5, blend(pal.ground, tone, 0.62 * level))
        tile.blob(7.5, 7.5, 2.5, blend(tone, (255, 255, 255), 0.45 * level))
        frames.append(tile)
    return frames


def blink_frames(pal: Palette) -> list[Canvas]:
    """An eye in the ground that opens once every few seconds."""
    frames = []
    for openness in (1.0, 1.0, 0.35, 0.0):
        tile = Canvas(TILE, TILE, pal.ground)
        if openness <= 0.01:
            tile.hline(8, 3, 12, pal.form_dark)
        else:
            ry = max(1.5, 5 * openness)
            tile.ellipse(7.5, 8, 6, ry, pal.accent)
            tile.blob(7.5, 8, min(3.0, ry), pal.form_dark)
            tile.blob(7.5, 8, min(1.5, ry * 0.5), pal.void)
        frames.append(tile)
    return frames


# --- world-specific forms ----------------------------------------------------
# Everything below belongs to exactly one dream.  Shared props make worlds feel
# like levels of the same game; these are what make them feel like places.

def brick_arch(pal: Palette, cols: int = 4, rows: int = 4) -> Canvas:
    """An archway of the same brick as everything else, leading nowhere."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(0, 0, w, h, pal.form)
    art.rect(0, 0, w, 4, pal.form_light)
    for row in range(4, h, 8):
        art.hline(row, 0, w - 1, cooler(pal.form, 0.12))
        stagger = 0 if (row // 8) % 2 else TILE // 2
        for x in range(stagger, w, TILE):
            art.vline(x, row, row + 7, cooler(pal.form, 0.12))

    # The opening: straight jambs up to a spring line, then a true semicircle.
    # Punched out of the brick rather than drawn on top of it, so the arch
    # reads as a way through and not as a dark medallion.
    half = (w - 16) // 2
    cx = w // 2
    spring = h - int(h * 0.42)
    for row in range(spring - half, h):
        if row < spring:
            dy = spring - row
            span = int((half * half - dy * dy) ** 0.5) if dy <= half else 0
        else:
            span = half
        if span > 0:
            art.hline(row, cx - span, cx + span - 1, pal.void)
    # a lighter soffit just inside the opening, so it has depth
    for row in range(spring - half, h):
        if row < spring:
            dy = spring - row
            span = int((half * half - dy * dy) ** 0.5) if dy <= half else 0
        else:
            span = half
        if span > 2:
            art.dot(cx - span, row, cooler(pal.form, 0.30))
            art.dot(cx + span - 1, row, cooler(pal.form, 0.45))
    return outline_in(art, cooler(pal.form_dark, 0.3))


def wall_niche(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """A recess in the brick with nothing in it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(0, 0, w, h, pal.form)
    art.rect(0, 0, w, 4, pal.form_light)
    art.round_rect(5, 10, w - 10, h - 18, 6, cooler(pal.form, 0.35))
    art.round_rect(7, 12, w - 14, h - 22, 5, cooler(pal.form, 0.55))
    return outline_in(art, cooler(pal.form_dark, 0.3))


def operator_sign(pal: Palette, kind: str, cols: int = 2, rows: int = 2) -> Canvas:
    """A floating arithmetic symbol.  It is not part of any sum."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    thick = max(5, w // 6)
    body = pal.form
    cx, cy = w // 2, h // 2
    if kind == "plus":
        art.round_rect(cx - w // 3, cy - thick // 2, 2 * w // 3, thick, 2, body)
        art.round_rect(cx - thick // 2, cy - h // 3, thick, 2 * h // 3, 2, body)
    elif kind == "minus":
        art.round_rect(cx - w // 3, cy - thick // 2, 2 * w // 3, thick, 2, body)
    elif kind == "equals":
        art.round_rect(cx - w // 3, cy - thick - 2, 2 * w // 3, thick, 2, body)
        art.round_rect(cx - w // 3, cy + 2, 2 * w // 3, thick, 2, body)
    else:  # times
        for sign in (1, -1):
            for step in range(-w // 3, w // 3):
                art.blob(cx + step, cy + step * sign, thick / 2, body)
    solid = np.any(art.px != np.array(TRANSPARENT, np.uint8), axis=-1)
    lower = np.zeros_like(solid)
    lower[2:, :] = solid[:-2, :]
    art.px[solid & ~lower] = pal.form_light
    return outline_in(art, cooler(pal.form_dark, 0.3))


def number_plinth(pal: Palette, cols: int = 3, rows: int = 2) -> Canvas:
    """A step of pale stone for digits to stand on."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(0, 6, w, h - 6, 3, pal.form_dark)
    art.round_rect(3, 2, w - 6, h - 6, 3, pal.form)
    art.rect(3, 2, w - 6, 3, pal.form_light)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def ball_toy(pal: Palette, color: RGB, cols: int = 2, rows: int = 2) -> Canvas:
    """A big soft ball with a stripe, like every ball ever drawn for a child."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    r = min(w, h) / 2 - 1
    art.blob(w / 2, h / 2, r, color)
    art.ellipse(w / 2, h / 2 + r * 0.30, r * 0.98, r * 0.24, warmer(color, 0.5))
    art.ellipse(w / 2, h / 2 - r * 0.34, r * 0.86, r * 0.22, warmer(color, 0.5))
    art.blob(w / 2 - r * 0.34, h / 2 - r * 0.38, r * 0.20, warmer(color, 0.75))
    art.ellipse(w / 2, h / 2 + r * 0.62, r * 0.72, r * 0.26, cooler(color, 0.22))
    return outline_in(art, cooler(color, 0.42))


def ring_stack(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """The stacking-rings toy, which every one of us has held."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 2, 6, 4, h - 10, (216, 200, 176))
    colors = ((238, 206, 126), (140, 200, 152), (120, 176, 226), (228, 128, 124))
    y = h - 8
    for index, color in enumerate(colors):
        rw = 10 + index * 5
        art.round_rect(w // 2 - rw // 2, y, rw, 7, 3, color)
        art.rect(w // 2 - rw // 2 + 2, y, rw - 4, 2, warmer(color, 0.35))
        y -= 7
    art.blob(w / 2, 5, 3.5, (228, 128, 124))
    return outline_in(art, cooler(pal.form_dark, 0.3))


def jack_toy(pal: Palette, cols: int = 2, rows: int = 2) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    metal = (198, 200, 210)
    cx, cy = w // 2, h // 2 + 2
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        art.round_rect(cx + dx * 9 - 3, cy + dy * 9 - 3, 6, 6, 2, metal)
        art.line(cx, cy, cx + dx * 8, cy + dy * 8, metal)
    art.blob(cx, cy, 4, warmer(metal, 0.2))
    return outline_in(art, cooler(metal, 0.42))


def stair_landing(pal: Palette, cols: int = 3, rows: int = 2) -> Canvas:
    """A platform hanging in nothing, where several flights meet."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(0, 2, w, h - 6, 3, pal.form)
    art.rect(0, 2, w, 3, pal.form_light)
    art.rect(0, h - 8, w, 4, pal.form_dark)
    for x in range(4, w - 4, 10):
        art.rect(x, h - 4, 4, 4, cooler(pal.form_dark, 0.3))
    return outline_in(art, cooler(pal.form_dark, 0.25))


def spiral_stair(pal: Palette, cols: int = 3, rows: int = 5) -> Canvas:
    """A staircase that turns back through itself."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 2, 4, 5, h - 6, pal.form_dark)
    for index in range(9):
        y = h - 8 - index * (h - 14) // 9
        phase = index % 4
        offset = (-1, 0, 1, 0)[phase]
        step_w = (14, 20, 14, 20)[phase]
        x = w // 2 + offset * 10 - step_w // 2
        art.round_rect(x, y, step_w, 5, 2, pal.form)
        art.rect(x, y, step_w, 2, pal.form_light)
    return outline_in(art, cooler(pal.form_dark, 0.25))


def broken_stair(pal: Palette, cols: int = 3, rows: int = 2) -> Canvas:
    """A flight that simply stops."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    steps = 4
    step_w = w // (steps + 2)
    for index in range(steps):
        x = index * step_w
        y = h - 8 - index * 6
        art.rect(x, y, step_w + 1, 7, pal.form)
        art.rect(x, y, step_w + 1, 2, pal.form_light)
    art.rect(steps * step_w, h - 8 - steps * 6, 4, 5, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.25))


def obelisk(pal: Palette, cols: int = 2, rows: int = 5) -> Canvas:
    """A pale marker in the sand.  There is nothing written on it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    for row in range(h - 6):
        t = row / (h - 6)
        span = int(6 + t * (w - 14))
        art.hline(row + 4, w // 2 - span // 2, w // 2 + span // 2, pal.form)
    art.round_rect(2, h - 8, w - 4, 8, 2, pal.form_dark)
    art.vline(w // 2 - 3, 6, h - 9, pal.form_light)
    return outline_in(art, cooler(pal.form_dark, 0.28))


def dead_tree(pal: Palette, cols: int = 3, rows: int = 4) -> Canvas:
    """A tree with no canopy at all, which is somehow worse than a stump."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(w // 2 - 4, int(h * 0.30), 9, int(h * 0.68), 3, pal.form)
    art.rect(w // 2 - 4, int(h * 0.30), 3, int(h * 0.68), pal.form_light)
    for sign, y0, y1, reach in ((-1, 0.42, 0.20, 0.34), (1, 0.52, 0.26, 0.30),
                                (-1, 0.62, 0.46, 0.22)):
        art.line(w // 2, int(h * y0), int(w / 2 + sign * w * reach), int(h * y1),
                 pal.form)
        art.line(w // 2, int(h * y0) + 1, int(w / 2 + sign * w * reach),
                 int(h * y1) + 1, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def stump_face(pal: Palette, cols: int = 2, rows: int = 2) -> Canvas:
    """A stump, still smiling."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(3, 8, w - 6, h - 10, 5, pal.form)
    art.ellipse(w / 2, 9, (w - 6) / 2, 4, pal.form_light)
    art.ellipse(w / 2, 9, (w - 12) / 2, 2.5, warmer(pal.form_light, 0.25))
    eye = cooler(pal.form_dark, 0.35)
    art.rect(w // 2 - 6, 16, 2, 3, eye)
    art.rect(w // 2 + 4, 16, 2, 3, eye)
    art.hline(22, w // 2 - 5, w // 2 + 4, eye)
    art.dot(w // 2 - 6, 21, eye)
    art.dot(w // 2 + 5, 21, eye)
    return outline_in(art, cooler(pal.form_dark, 0.32))


def mushroom(pal: Palette, color: RGB, cols: int = 2, rows: int = 2) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    cap_y = int(h * 0.46)
    # Cap first, clipped to a dome, then the stalk under it.
    art.ellipse(w / 2, cap_y, w * 0.44, h * 0.30, color)
    art.rect(0, cap_y, w, h - cap_y, TRANSPARENT)
    art.round_rect(w // 2 - 4, cap_y - 2, 9, h - cap_y, 3, pal.accent)
    art.rect(w // 2 - 4, cap_y - 2, 3, h - cap_y, warmer(pal.accent, 0.3))
    art.ellipse(w / 2, cap_y - 1, w * 0.44, h * 0.30, color)
    art.rect(0, cap_y, w, h - cap_y, TRANSPARENT)
    art.round_rect(w // 2 - 4, cap_y - 1, 9, h - cap_y + 1, 3, pal.accent)
    for dx, dy, r in ((-6, -6, 2.4), (5, -8, 2.0), (0, -11, 1.6)):
        art.blob(w / 2 + dx, cap_y + dy, r, warmer(color, 0.6))
    return outline_in(art, cooler(color, 0.4))


# --- props that only exist on one channel of the grove -----------------------
# The grove is broadcast four ways.  These are the things that are only there
# on one of them — not decoration, but the evidence that a channel is a
# different reception of the same street rather than a different street.

def bramble(pal: Palette, cols: int = 2, rows: int = 2) -> Canvas:
    """A tangle across the ground, thick enough to stop a person.

    Drawn as one continuous run of stems rather than a bush, because the point
    is that it is *growing across* something — a road, a doorway, a gap in a
    wall that used to be a route.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    stem = pal.form_dark
    for index in range(7):
        x0 = int(w * index / 7)
        art.line(x0, h - 2, x0 + w // 3, int(h * 0.18), stem)
        art.line(x0 + 1, h - 2, x0 + w // 3 + 1, int(h * 0.18), pal.form)
        art.line(x0 + w // 3, int(h * 0.18), x0 - w // 6, int(h * 0.42), stem)
    for index in range(9):
        art.blob(3 + (index * 7) % (w - 6), 6 + (index * 11) % (h - 8), 2.6,
                 pal.accent_soft)
    for index in range(5):
        art.dot(5 + (index * 13) % (w - 6), 9 + (index * 7) % (h - 6),
                pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.35))


def hive(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """Something built in the fork of a tree, by something that is not a bird."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 2, int(h * 0.60), 5, h - int(h * 0.60), pal.form_dark)
    for index, radius in enumerate((0.34, 0.40, 0.34, 0.24)):
        art.ellipse(w / 2, h * (0.16 + index * 0.13), w * radius, h * 0.09,
                    pal.form_light if index % 2 else pal.form)
    art.ellipse(w / 2, h * 0.52, 3.2, 2.2, cooler(pal.form_dark, 0.4))
    return outline_in(art, cooler(pal.form_dark, 0.3))


def tree_glyph(pal: Palette, cols: int = 3, rows: int = 4) -> Canvas:
    """The symbol for a tree, at the size of a tree.

    On the dead channel nothing is rendered any more, only indicated: a stroke
    for the trunk and a triangle for everything above it.  It occupies the
    exact footprint of the real tree it has replaced.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    ink = pal.accent
    art.rect(w // 2 - 2, int(h * 0.55), 5, int(h * 0.42), ink)
    for row in range(int(h * 0.55)):
        span = int((row / (h * 0.55)) * (w * 0.46))
        art.dot(w // 2 - span, row, ink)
        art.dot(w // 2 + span, row, ink)
    art.hline(int(h * 0.55) - 1, int(w * 0.04), int(w * 0.96), ink)
    art.rect(w // 2 - 4, int(h * 0.30), 9, 2, pal.form)
    return art


def aerial(pal: Palette, cols: int = 2, rows: int = 4) -> Canvas:
    """A rooftop aerial on a pole, in a wood, pointing at nothing nearby."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 1, int(h * 0.22), 3, h - int(h * 0.22) - 1, pal.form)
    art.rect(w // 2 - 1, int(h * 0.22), 1, h - int(h * 0.22) - 1, pal.form_light)
    art.line(w // 2, int(h * 0.30), w - 3, int(h * 0.12), pal.form_dark)
    for index in range(6):
        y = int(h * 0.13) + index * 3
        x0 = w // 2 + index
        art.hline(y, x0, min(w - 2, x0 + 9 - index), pal.form_light)
    art.blob(w // 2, int(h * 0.22), 2.0, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def meter_box(pal: Palette, cols: int = 1, rows: int = 2) -> Canvas:
    """A supply meter on a post.  Its dial is still turning."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(w // 2 - 1, h // 2, 3, h // 2, pal.form_dark)
    art.round_rect(1, 2, w - 2, h // 2, 2, pal.form)
    art.rect(2, 3, w - 4, h // 2 - 3, pal.form_light)
    art.rect(3, 5, w - 6, 4, cooler(pal.form_dark, 0.2))
    art.dot(w // 2, 7, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def tone_pillar(pal: Palette, cols: int = 1, rows: int = 4) -> Canvas:
    """A column of the test tone, stood upright and made solid.

    It is the sound drawn as an object, which is only possible on the channel
    where the picture has already stopped pretending to be a place.
    """
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    for row in range(h):
        phase = (row * 3) % 12
        width = 2 + abs(6 - phase) // 2
        tone = pal.accent if phase < 6 else pal.form
        art.rect(w // 2 - width, row, width * 2, 1, tone)
    art.rect(w // 2 - 1, 0, 3, h, pal.accent)
    return art


def checker_pillar(pal: Palette, cols: int = 1, rows: int = 4) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(2, 0, w - 4, h, pal.form)
    for row in range(0, h, 8):
        color = pal.ground if (row // 8) % 2 == 0 else pal.ground_b
        art.rect(2, row, w - 4, 8, color)
    art.round_rect(0, h - 6, w, 6, 2, pal.form_dark)
    art.round_rect(0, 0, w, 5, 2, pal.form_light)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def picket_fence(pal: Palette, cols: int = 3, rows: int = 1) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.rect(0, 6, w, 3, pal.form_light)
    art.rect(0, 11, w, 3, pal.form_light)
    for x in range(2, w, 8):
        art.round_rect(x, 2, 4, h - 3, 2, pal.form_light)
        art.rect(x, 2, 1, h - 3, pal.form)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def buoy(pal: Palette, cols: int = 1, rows: int = 2) -> Canvas:
    """Something floating, marking a channel nobody sails."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(w // 2 - 6, h // 2 - 3, 13, h // 2 + 1, 5, pal.accent)
    art.rect(w // 2 - 6, h // 2 + 2, 13, 4, warmer(pal.accent, 0.55))
    art.rect(w // 2 - 6, h - 5, 13, 3, cooler(pal.accent, 0.30))
    art.rect(w // 2 - 1, 5, 3, h // 2 - 6, pal.form_light)
    art.blob(w / 2, 4, 3.5, pal.accent)
    art.blob(w / 2 - 1, 3, 1.5, warmer(pal.accent, 0.7))
    return outline_in(art, cooler(pal.accent, 0.45))


def pier(pal: Palette, cols: int = 4, rows: int = 2) -> Canvas:
    """A wooden walkway going out over the stars."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    deck = pal.accent_soft
    art.rect(0, 4, w, 13, deck)
    art.rect(0, 4, w, 3, warmer(deck, 0.35))
    art.rect(0, 15, w, 2, cooler(deck, 0.30))
    for x in range(0, w, 7):
        art.vline(x, 5, 14, cooler(deck, 0.22))
    for x in range(4, w, 15):
        art.rect(x, 17, 4, h - 18, cooler(deck, 0.45))
    return outline_in(art, cooler(deck, 0.55))


def floating_island(pal: Palette, cols: int = 4, rows: int = 3) -> Canvas:
    """A piece of ground with no planet under it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    # Rock underside first, tapering to a point, then the lit top surface on
    # top of it — otherwise the island reads as a bowl.
    for row in range(int(h * 0.34), h - 1):
        t = (row - h * 0.34) / (h * 0.66)
        span = int(w * 0.46 * (1 - t * t))
        if span > 0:
            art.hline(row, w // 2 - span, w // 2 + span, pal.form_dark)
    art.ellipse(w / 2, h * 0.34, w * 0.46, h * 0.22, pal.form)
    art.ellipse(w / 2, h * 0.30, w * 0.44, h * 0.19, pal.accent_soft)
    art.ellipse(w / 2 - w * 0.10, h * 0.26, w * 0.22, h * 0.09,
                warmer(pal.accent_soft, 0.30))
    return outline_in(art, cooler(pal.form_dark, 0.35))


def wardrobe(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """A wardrobe.  You already know you are going to open it."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(1, 2, w - 2, h - 3, 3, pal.form_dark)
    art.round_rect(3, 5, w // 2 - 4, h - 9, 2, pal.form)
    art.round_rect(w // 2 + 1, 5, w // 2 - 4, h - 9, 2, pal.form)
    art.blob(w / 2 - 2, h / 2, 1.6, pal.accent)
    art.blob(w / 2 + 2, h / 2, 1.6, pal.accent)
    art.rect(2, h - 4, w - 4, 3, cooler(pal.form_dark, 0.3))
    return outline_in(art, cooler(pal.form_dark, 0.4))


def old_television(pal: Palette, cols: int = 2, rows: int = 2) -> Canvas:
    """A television showing nothing in particular."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(1, 4, w - 2, h - 10, 4, pal.form_dark)
    art.round_rect(4, 7, w - 12, h - 16, 3, (196, 206, 202))
    art.round_rect(5, 8, w - 14, h - 18, 2, (150, 168, 168))
    art.blob(w - 6, 12, 1.6, pal.accent)
    art.blob(w - 6, 17, 1.6, cooler(pal.accent, 0.4))
    art.rect(4, h - 6, 5, 5, cooler(pal.form_dark, 0.3))
    art.rect(w - 9, h - 6, 5, 5, cooler(pal.form_dark, 0.3))
    return outline_in(art, cooler(pal.form_dark, 0.45))


def standing_mirror(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """A mirror.  It works, which is the problem."""
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(2, 2, w - 4, h - 6, w // 2 - 2, pal.form_dark)
    art.round_rect(5, 5, w - 10, h - 12, w // 2 - 5, pal.accent_soft)
    art.round_rect(7, 7, w - 14, h - 16, w // 2 - 7, warmer(pal.accent_soft, 0.35))
    art.round_rect(4, h - 5, w - 8, 4, 2, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def bench_seat(pal: Palette, cols: int = 3, rows: int = 2) -> Canvas:
    art = _canvas(cols, rows)
    w, h = cols * TILE, rows * TILE
    art.round_rect(2, 6, w - 4, 8, 3, pal.form)
    art.rect(3, 6, w - 6, 2, pal.form_light)
    art.round_rect(2, 2, w - 4, 4, 2, pal.form)
    art.rect(6, 14, 4, h - 15, pal.form_dark)
    art.rect(w - 10, 14, 4, h - 15, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.35))


# --- per-world decals --------------------------------------------------------
# Small ground marks, three or four per world.  They exist so that the litter
# of one dream can never be mistaken for the litter of another, and so a
# looping map has enough small landmarks to lie about its size.

def decal(base: Canvas, motif: str, color: RGB, second: RGB | None = None,
          seed: int = 0) -> Canvas:
    """Draw a small mark onto a copy of a ground tile."""
    art = base.copy()
    other = second or cooler(color, 0.3)
    cx = cy = TILE // 2

    if motif == "crack":
        art.line(2, 3, 7, 8, other)
        art.line(7, 8, 6, 13, other)
        art.line(7, 8, 12, 10, other)
    elif motif == "loose_brick":
        art.round_rect(4, 6, 9, 5, 1, color)
        art.rect(4, 6, 9, 1, warmer(color, 0.3))
    elif motif == "drainhole":
        art.ellipse(cx, cy, 4, 3, other)
        art.ellipse(cx, cy, 2.4, 1.6, cooler(other, 0.5))
    elif motif == "point":
        art.blob(cx, cy + 3, 2.2, color)
    elif motif == "tally":
        for x in (5, 8, 11):
            art.rect(x, 5, 1, 7, color)
        art.line(4, 12, 12, 4, color)
    elif motif == "equals":
        art.rect(4, 6, 9, 2, color)
        art.rect(4, 10, 9, 2, color)
    elif motif == "peg":
        art.ellipse(cx, cy, 3, 3, other)
        art.ellipse(cx, cy - 1, 2, 2, cooler(other, 0.4))
    elif motif == "scribble":
        art.line(3, 11, 7, 5, color)
        art.line(7, 5, 10, 11, color)
        art.line(10, 11, 13, 6, color)
    elif motif == "marble":
        art.blob(cx, cy, 3.4, color)
        art.blob(cx - 1, cy - 1, 1.4, warmer(color, 0.6))
    elif motif == "step_shard":
        art.round_rect(3, 7, 10, 4, 1, color)
        art.rect(3, 7, 10, 1, warmer(color, 0.35))
    elif motif == "rope":
        for y in range(3, 13, 3):
            art.rect(7, y, 2, 2, color)
    elif motif == "bone":
        art.round_rect(4, 7, 8, 3, 1, color)
        art.blob(4, 8.5, 2, color)
        art.blob(12, 8.5, 2, color)
    elif motif == "prints":
        art.round_rect(4, 4, 3, 4, 1, other)
        art.round_rect(9, 9, 3, 4, 1, other)
    elif motif == "halfring":
        art.ellipse(cx, cy + 2, 5, 3, color, filled=False)
    elif motif == "leaves":
        for dx, dy in ((-3, 1), (2, -2), (4, 3)):
            art.blob(cx + dx, cy + dy, 2.2, color)
    elif motif == "sigil":
        art.ellipse(cx, cy, 4.5, 4.5, color, filled=False)
        art.rect(cx - 1, cy - 4, 2, 8, color)
    elif motif == "ringcaps":
        for angle in range(0, 360, 60):
            x = cx + int(4.5 * math.cos(math.radians(angle)))
            y = cy + int(4.5 * math.sin(math.radians(angle)))
            art.blob(x, y, 1.6, color)
    elif motif == "fingerprint":
        for radius in (2.0, 3.4, 4.8):
            art.ellipse(cx, cy, radius, radius * 0.8, other, filled=False)
    elif motif == "pebble":
        art.blob(cx - 2, cy + 2, 2.4, color)
        art.blob(cx + 3, cy - 1, 1.6, other)
    elif motif == "ring":
        art.ellipse(cx, cy, 4, 4, color, filled=False)
        art.ellipse(cx, cy, 3, 3, color, filled=False)
    elif motif == "offsquare":
        art.round_rect(3, 4, 8, 8, 1, color)
    elif motif == "jackmark":
        art.line(4, 4, 12, 12, other)
        art.line(12, 4, 4, 12, other)
        art.blob(cx, cy, 1.8, color)
    elif motif == "shaving":
        art.line(4, 10, 9, 6, color)
        art.line(9, 6, 12, 9, color)
    elif motif == "glyph":
        art.rect(5, 4, 2, 9, color)
        art.rect(5, 4, 7, 2, color)
        art.rect(5, 8, 5, 2, color)
    elif motif == "spark":
        art.rect(cx - 1, cy - 5, 2, 10, color)
        art.rect(cx - 5, cy - 1, 10, 2, color)
        art.blob(cx, cy, 2, warmer(color, 0.6))
    elif motif == "scanline":
        art.rect(0, 5, TILE, 1, color)
        art.rect(0, 9, TILE, 1, cooler(color, 0.3))
    elif motif == "puddle":
        art.ellipse(cx, cy + 1, 6, 3.4, color)
        art.ellipse(cx - 1, cy, 3, 1.6, warmer(color, 0.4))
    elif motif == "dropped":
        art.round_rect(3, 8, 11, 3, 1, color)
        art.blob(3, 9.5, 2, other)
    elif motif == "waterring":
        art.ellipse(cx, cy, 6, 3.4, color, filled=False)
        art.ellipse(cx, cy, 3.4, 2, color, filled=False)
    elif motif == "constellation":
        pts = ((3, 4), (7, 7), (11, 5), (9, 11), (5, 12))
        for index in range(len(pts) - 1):
            art.line(*pts[index], *pts[index + 1], other)
        for x, y in pts:
            art.blob(x, y, 1.4, color)
    elif motif == "ripple":
        for radius in (2.0, 4.0, 6.0):
            art.ellipse(cx, cy, radius, radius * 0.55, other, filled=False)
    elif motif == "fallen_star":
        art.blob(cx, cy, 2.6, color)
        art.line(cx - 4, cy + 4, cx, cy, other)

    # --- the grove's other three channels ------------------------------------
    elif motif == "creeper":
        # a runner crossing the tile with leaves paired off it, so that a floor
        # scattered with these reads as one plant rather than many marks
        art.line(0, 11, 15, 4, other)
        for x, y in ((3, 9), (7, 7), (11, 5)):
            art.blob(x, y - 2, 1.8, color)
            art.blob(x + 1, y + 2, 1.8, color)
    elif motif == "seedhead":
        art.vline(cx, cy - 1, TILE - 2, other)
        for angle in range(0, 360, 45):
            x = cx + int(3.4 * math.cos(math.radians(angle)))
            y = cy - 2 + int(3.4 * math.sin(math.radians(angle)))
            art.dot(x, y, color)
        art.blob(cx, cy - 2, 1.4, warmer(color, 0.4))
    elif motif == "windfall":
        art.ellipse(cx - 3, cy + 2, 2.4, 2.0, color)
        art.ellipse(cx + 2, cy + 3, 2.0, 1.6, other)
        art.dot(cx - 3, cy, other)
    elif motif == "ashfall":
        for x, y in ((3, 4), (9, 3), (6, 9), (12, 8), (4, 12), (11, 13)):
            art.dot(x, y, color)
            art.dot(x + 1, y + 1, other)
    elif motif == "chalkline":
        # a surveyor's mark: something was measured here and never dug
        art.line(2, 13, 13, 2, other)
        art.line(2, 13, 6, 12, other)
        art.line(13, 2, 9, 3, other)
        art.dot(cx, cy, color)
    elif motif == "tapeloop":
        art.ellipse(cx - 2, cy, 3.2, 3.2, other, filled=False)
        art.ellipse(cx + 3, cy + 1, 2.2, 2.2, other, filled=False)
        art.line(cx - 2, cy - 3, cx + 3, cy - 2, color)
    elif motif == "colourbar":
        for index, x in enumerate(range(3, 14, 2)):
            art.rect(x, 5, 2, 7, color if index % 2 else other)
    elif motif == "cornerpip":
        # the registration mark in the corner of a test card
        art.line(3, 3, 7, 3, color)
        art.line(3, 3, 3, 7, color)
        art.line(12, 12, 8, 12, color)
        art.line(12, 12, 12, 8, color)
    elif motif == "tone":
        art.ellipse(cx, cy, 5, 5, other, filled=False)
        art.ellipse(cx, cy, 2.6, 2.6, color, filled=False)
        art.dot(cx, cy, color)
    return art


# --- boundaries --------------------------------------------------------------
# Every world's walls are built from its own motif, densely repeated.  This is
# the single most identifying surface in a dream: it is what the player is
# looking at whenever they cannot go somewhere, which is most of the time.

def wall_band(pal: Palette, motif: str, *, face: bool = False,
              accent: RGB | None = None, base: RGB | None = None,
              light: RGB | None = None, dark: RGB | None = None) -> Canvas:
    """One tile of boundary.

    ``face`` draws the lit front edge used where a wall meets walkable floor,
    which is what turns a flat band of colour into something the player reads
    as standing in front of them.
    """
    # Overridable, because a world's boundary is not always made of the same
    # material as its props — a forest wall is canopy, not trunk.
    base = base or pal.form
    light = light or pal.form_light
    dark = dark or pal.form_dark
    ink = accent or pal.accent
    art = Canvas(TILE, TILE, base)

    if motif == "brick":
        for row in range(0, TILE, 8):
            art.hline(row, 0, TILE - 1, light)
            stagger = 0 if (row // 8) % 2 else TILE // 2
            art.vline(stagger, row, row + 7, light)
    elif motif == "digits":
        art.px[:, :] = dark
        for oy in (1, 9):
            for ox in (1, 9):
                art.round_rect(ox, oy, 6, 6, 1, base)
                art.rect(ox + 2, oy + 1, 2, 4, ink)
    elif motif == "blocks":
        for oy in (0, 8):
            for ox in (0, 8):
                art.round_rect(ox + 1, oy + 1, 6, 6, 2, light)
                art.round_rect(ox + 2, oy + 2, 4, 4, 1, ink)
    elif motif == "steps":
        for i in range(4):
            art.rect(0, i * 4, TILE, 3, light if i % 2 else base)
            art.rect(i * 4, 0, 3, TILE, dark)
    elif motif == "strata":
        for row in range(0, TILE, 3):
            tone = light if (row // 3) % 2 else base
            art.hline(row, 0, TILE - 1, tone)
            art.hline(row + 1, 0, TILE - 1, blend(tone, dark, 0.3))
    elif motif == "trunks":
        # Overlapping canopy, not stacked timber: this is a solid mass of
        # leaves seen from above, and it has to read as impenetrable rather
        # than as a wall built out of logs.
        art.px[:, :] = dark
        for ox, oy, r in ((4, 4, 5.5), (12, 3, 4.8), (3, 12, 4.6),
                          (11, 12, 5.2), (8, 8, 4.4), (15, 8, 4.0),
                          (0, 8, 4.0), (8, 0, 4.0), (8, 15, 4.0)):
            art.blob(ox, oy, r, base)
            art.blob(ox - 1, oy - 1, r * 0.55, light)
        for ox, oy in ((6, 6), (13, 5), (5, 13)):
            art.dot(ox, oy, cooler(dark, 0.3))
    elif motif == "fingers":
        for ox in range(0, TILE, 5):
            art.round_rect(ox, 0, 4, TILE, 2, light)
            art.rect(ox, 0, 1, TILE, base)
        art.hline(0, 0, TILE - 1, dark)
    elif motif == "checker":
        art.checker(light, dark, 4)
    elif motif == "toybox":
        art.round_rect(0, 0, 8, 8, 2, ink)
        art.round_rect(8, 0, 8, 8, 2, light)
        art.round_rect(0, 8, 8, 8, 2, light)
        art.round_rect(8, 8, 8, 8, 2, pal.accent_soft)
    elif motif == "neon":
        art.px[:, :] = pal.void
        art.outline(0, 0, TILE, TILE, ink)
        art.outline(2, 2, TILE - 4, TILE - 4, pal.accent)
        art.outline(5, 5, TILE - 10, TILE - 10, pal.accent_soft)
        art.rect(7, 7, 2, 2, ink)
    elif motif == "scallops":
        art.px[:, :] = dark
        for ox in (0, 8):
            for oy in (0, 8):
                art.ellipse(ox + 4, oy + 5, 4.5, 4, light)
                art.ellipse(ox + 4, oy + 4, 3, 2.5, ink)
    elif motif == "starfield":
        art.px[:, :] = pal.void
        for x, y in ((2, 3), (9, 6), (5, 11), (13, 13), (11, 1), (1, 9)):
            art.dot(x, y, ink)
            art.dot(x + 1, y, pal.accent_soft)
            art.dot(x, y + 1, pal.accent_soft)
        art.outline(0, 0, TILE, TILE, blend(pal.void, ink, 0.25))
    elif motif == "paper":
        for ox in range(0, TILE, 5):
            art.vline(ox, 0, TILE - 1, light)
            art.vline(ox + 1, 0, TILE - 1, blend(light, base, 0.5))
    elif motif == "doors":
        art.px[:, :] = dark
        art.round_rect(3, 2, 10, 13, 4, base)
        art.round_rect(5, 4, 6, 11, 3, light)
        art.dot(11, 9, ink)
    elif motif == "thicket":
        # The grove's canopy, but grown shut.  Same overlapping mass as
        # "trunks" and then filled in again at a second, finer scale, so that
        # the gaps the eye reads as depth in the grove are not there any more.
        art.px[:, :] = dark
        for ox, oy, r in ((4, 4, 6.2), (12, 3, 5.6), (3, 12, 5.4),
                          (11, 12, 6.0), (8, 8, 5.4), (15, 8, 4.8),
                          (0, 8, 4.8), (8, 0, 4.8), (8, 15, 4.8)):
            art.blob(ox, oy, r, base)
            art.blob(ox - 1, oy - 1, r * 0.5, light)
        for ox, oy in ((2, 6), (7, 2), (13, 9), (6, 13), (11, 6)):
            art.blob(ox, oy, 2.2, warmer(light, 0.25))
            art.dot(ox, oy, ink)
        # runners crossing the whole tile, which is what makes it read as
        # tangled rather than merely leafy
        art.line(0, 13, 15, 2, blend(dark, base, 0.4))
        art.line(1, 1, 14, 15, blend(dark, base, 0.4))
    elif motif == "bare":
        # The same canopy with the leaves gone: nothing but the branch
        # structure that was holding them up, and daylight behind it.
        art.px[:, :] = light
        for x0, y0, x1, y1 in ((8, 16, 8, 7), (8, 10, 2, 3), (8, 10, 14, 4),
                               (8, 7, 5, 0), (8, 7, 12, 1), (4, 6, 0, 2),
                               (12, 5, 16, 1)):
            art.line(x0, y0, x1, y1, dark)
        for x0, y0, x1, y1 in ((6, 12, 3, 9), (10, 11, 13, 8), (9, 5, 11, 2)):
            art.line(x0, y0, x1, y1, blend(dark, light, 0.35))
        art.rect(7, 10, 3, 6, base)
    elif motif == "cumulus":
        # PLANE ONE.  Not a wall — the edge of the cloud, seen from on top of
        # it.  Soft the whole way down, and it is the last soft thing.
        art.px[:, :] = light
        for ox, oy, r in ((3, 4, 6.0), (11, 3, 5.4), (7, 9, 6.4),
                          (15, 8, 5.0), (0, 9, 5.0), (12, 13, 5.4)):
            art.blob(ox, oy, r, base)
            art.blob(ox - 1, oy - 1, r * 0.6, light)
        art.dither(blend(base, dark, 0.35), 0.22, BAYER8)
    elif motif == "cornice":
        # PLANE TWO.  Somebody has run a moulding along it.  It is beautifully
        # made and it is the first thing here that was decided rather than
        # grown.
        art.px[:, :] = base
        for row, height in ((0, 3), (4, 2), (7, 4), (12, 2)):
            art.rect(0, row, TILE, height,
                     light if row % 8 == 0 else blend(base, dark, 0.4))
            art.hline(row, 0, TILE - 1, light)
        art.hline(TILE - 1, 0, TILE - 1, dark)
        for x in range(2, TILE, 6):
            art.rect(x, 7, 3, 4, light)
    elif motif == "lockers":
        # PLANE THREE.  A run of identical doors, each with a number plate and
        # no number on it.
        art.px[:, :] = dark
        for ox in (0, 8):
            art.rect(ox + 1, 1, 6, 14, base)
            art.rect(ox + 1, 1, 6, 1, light)
            art.rect(ox + 2, 4, 4, 2, blend(base, dark, 0.5))
            art.dot(ox + 5, 10, ink)
        art.hline(0, 0, TILE - 1, blend(light, dark, 0.4))
    elif motif == "cards":
        # PLANE FOUR.  Filed.  Nothing is behind it because everything is
        # already in it.
        art.px[:, :] = blend(base, dark, 0.3)
        for row in range(0, TILE, 4):
            art.rect(0, row, TILE, 3, base)
            art.hline(row, 0, TILE - 1, light)
            art.hline(row + 3, 0, TILE - 1, dark)
            for x in range(1, TILE, 5):
                art.dot(x, row + 1, blend(dark, base, 0.5))
        art.vline(TILE - 1, 0, TILE - 1, dark)
    elif motif == "rings":
        # THE EYE, from inside it: rings all the way out, and one of them is
        # always the one you are standing next to.
        art.px[:, :] = pal.void
        for radius in (2.2, 5.0, 7.8):
            art.ellipse(TILE / 2, TILE / 2, radius, radius, base, filled=False)
            art.ellipse(TILE / 2, TILE / 2, radius - 0.8, radius - 0.8, light,
                        filled=False)
        art.blob(TILE / 2, TILE / 2, 1.6, ink)
    elif motif == "coil":
        # THE SPIRAL: one line, entering at a corner and leaving at another,
        # so the boundary itself is continuous around a room.
        art.px[:, :] = pal.void
        for step in range(34):
            angle = step * 0.46
            radius = 0.8 + step * 0.24
            x = int(TILE / 2 + radius * math.cos(angle))
            y = int(TILE / 2 + radius * math.sin(angle))
            art.dot(x, y, base)
            art.dot(x, y - 1, light if step % 3 else base)
        art.dot(TILE // 2, TILE // 2, ink)
    elif motif == "teeth":
        # THE MOUTH: a bite, top and bottom, not quite meeting.
        art.px[:, :] = pal.void
        for index, x in enumerate(range(0, TILE, 4)):
            height = 5 + (index % 2) * 2
            art.rect(x, 0, 3, height, base)
            art.rect(x, 0, 3, 2, light)
            art.rect(x + 2, TILE - height - 1, 3, height + 1, base)
            art.rect(x + 2, TILE - 2, 3, 2, dark)
        art.hline(TILE // 2, 0, TILE - 1, blend(pal.void, ink, 0.35))
    elif motif == "rays":
        # THE STAR: everything points away from a centre that is not in shot.
        art.px[:, :] = pal.void
        for angle in range(0, 360, 30):
            radians = math.radians(angle)
            art.line(TILE // 2, TILE // 2,
                     int(TILE / 2 + 11 * math.cos(radians)),
                     int(TILE / 2 + 11 * math.sin(radians)),
                     base if angle % 60 else light)
        art.blob(TILE / 2, TILE / 2, 2.4, ink)
    elif motif == "bars":
        # Where the picture stops carrying the town.  Almost entirely black —
        # the roads on this channel are full-brightness colour bars, and a
        # boundary that shouts louder than the streets turns the whole map
        # into noise.  What is left of the bars is a narrow strip along the
        # bottom edge, the way a test card runs out at the frame.
        art.px[:, :] = pal.void
        art.dither(blend(pal.void, dark, 0.5), 0.35, BAYER8)
        widths = (3, 2, 3, 2, 3, 3)
        tones = (ink, blend(ink, base, 0.5), base, dark,
                 blend(base, dark, 0.5), light)
        x = 0
        for width, tone in zip(widths, tones):
            art.rect(x, TILE - 4, width, 3, blend(tone, pal.void, 0.45))
            x += width
        art.hline(TILE - 5, 0, TILE - 1, blend(base, pal.void, 0.5))
    else:
        art.dither(light, 0.4, BAYER8)

    if face:
        # a lit cap along the top and a shadowed lip along the bottom
        art.rect(0, 0, TILE, 3, warmer(light, 0.30))
        art.rect(0, 3, TILE, 1, light)
        art.rect(0, TILE - 3, TILE, 3, cooler(dark, 0.25))
        art.rect(0, TILE - 4, TILE, 1, dark)
    return art


# --- dense surfaces ----------------------------------------------------------
# Yume Nikki's floors are not empty ground with a landmark on them; they are
# *carpeted* in pattern, and the pattern is the world.  These are the tiles
# that fill a floor.  Density here is deliberate, not spam: they are laid down
# in borders, lattices and murals, never scattered at random.

def pattern_tile(pal: Palette, kind: str, ink: RGB | None = None,
                 back: RGB | None = None) -> Canvas:
    """One small repeating floor motif, of the kind that tiles into carpet."""
    bg = back or pal.ground
    fg = ink or pal.accent
    art = Canvas(TILE, TILE, bg)

    if kind == "square_frame":
        art.rect(2, 2, 12, 12, fg)
        art.rect(4, 4, 8, 8, bg)
        art.rect(6, 6, 4, 4, pal.accent_soft)
    elif kind == "concentric":
        for r, c in ((7, fg), (5, bg), (3, pal.accent_soft), (1, fg)):
            art.ellipse(7.5, 7.5, r, r, c)
    elif kind == "stripes":
        for x in range(0, TILE, 4):
            art.rect(x, 0, 2, TILE, fg)
            art.rect(x + 2, 0, 2, TILE, pal.accent_soft)
    elif kind == "dots":
        for ox, oy in ((3, 3), (11, 3), (3, 11), (11, 11), (7, 7)):
            art.blob(ox, oy, 2, fg)
    elif kind == "cross":
        art.rect(6, 0, 4, TILE, fg)
        art.rect(0, 6, TILE, 4, fg)
        art.rect(6, 6, 4, 4, pal.accent_soft)
    elif kind == "diamond":
        art.ellipse(7.5, 7.5, 7, 7, fg)
        art.ellipse(7.5, 7.5, 4, 4, bg)
        for dx, dy in ((0, -7), (0, 7), (-7, 0), (7, 0)):
            art.dot(7 + dx // 1, 7 + dy // 1, pal.accent_soft)
    elif kind == "weave":
        for y in range(0, TILE, 8):
            art.rect(0, y, TILE, 3, fg)
        for x in range(4, TILE, 8):
            art.rect(x, 0, 3, TILE, pal.accent_soft)
    elif kind == "chevron":
        for i in range(0, TILE, 4):
            art.line(0, i, 7, i + 7, fg)
            art.line(8, i + 7, 15, i, fg)
    elif kind == "grid":
        art.outline(0, 0, TILE, TILE, fg)
        art.outline(4, 4, 8, 8, pal.accent_soft)
    elif kind == "tick":
        art.rect(7, 2, 2, 12, fg)
        art.rect(2, 7, 12, 2, pal.accent_soft)
        art.blob(7.5, 7.5, 2, fg)
    elif kind == "bloom":
        for angle in range(0, 360, 60):
            x = 7.5 + 4.5 * math.cos(math.radians(angle))
            y = 7.5 + 4.5 * math.sin(math.radians(angle))
            art.blob(x, y, 2.4, fg)
        art.blob(7.5, 7.5, 2.6, pal.accent_soft)
    elif kind == "spiral":
        # An arm of a spiral that carries on into the next tile, so a floor of
        # these reads as one turning surface rather than as repeated coils.
        for step in range(26):
            angle = step * 0.52
            radius = 0.9 + step * 0.30
            art.dot(int(7.5 + radius * math.cos(angle)),
                    int(7.5 + radius * math.sin(angle)),
                    fg if step % 4 else pal.accent_soft)
    else:
        art.dither(fg, 0.35, BAYER4)
    return art


def floor_mural(pal: Palette, kind: str, cols: int = 4, rows: int = 4,
                ground: Canvas | None = None) -> Canvas:
    """A large painting on the floor.

    Murals are the reason a dream floor is worth looking down at.  They are
    walkable — nothing here ever blocks — and each one is big enough that the
    player cannot see all of it from one position.
    """
    art = Canvas(cols * TILE, rows * TILE, pal.ground)
    if ground is not None:
        for y in range(rows):
            for x in range(cols):
                art.paste(ground, x * TILE, y * TILE)
    w, h = art.w, art.h
    cx, cy = w / 2, h / 2
    ink, soft, deep = pal.accent, pal.accent_soft, pal.form

    if kind == "eye":
        art.ellipse(cx, cy, w * 0.46, h * 0.28, soft)
        art.ellipse(cx, cy, w * 0.42, h * 0.24, pal.void)
        art.blob(cx, cy, w * 0.17, ink)
        art.blob(cx, cy, w * 0.09, pal.void)
        art.blob(cx - w * 0.06, cy - h * 0.05, w * 0.04, soft)
        art.ellipse(cx, cy, w * 0.46, h * 0.28, ink, filled=False)
    elif kind == "rings":
        for index, radius in enumerate((0.46, 0.36, 0.26, 0.16, 0.07)):
            art.ellipse(cx, cy, w * radius, h * radius,
                        ink if index % 2 == 0 else soft, filled=False)
            art.ellipse(cx, cy, w * radius - 1, h * radius - 1,
                        ink if index % 2 == 0 else soft, filled=False)
    elif kind == "sun":
        art.blob(cx, cy, w * 0.16, ink)
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            for step in range(int(w * 0.20), int(w * 0.46)):
                art.dot(int(cx + math.cos(rad) * step),
                        int(cy + math.sin(rad) * step),
                        ink if (step // 3) % 2 else soft)
    elif kind == "lattice":
        for offset in range(0, w, 8):
            for y in range(h):
                x = (offset + y) % w
                art.dot(x, y, soft)
                art.dot((offset - y) % w, y, ink)
    elif kind == "waves":
        for y in range(h):
            for x in range(w):
                v = math.sin(x * 0.18) + math.sin(y * 0.22)
                if v > 0.9:
                    art.dot(x, y, ink)
                elif v > 0.2:
                    art.dot(x, y, soft)
    elif kind == "star":
        points = []
        for index in range(10):
            angle = -math.pi / 2 + index * math.pi / 5
            radius = (w * 0.46) if index % 2 == 0 else (w * 0.19)
            points.append((cx + math.cos(angle) * radius,
                           cy + math.sin(angle) * radius))
        points.append(points[0])
        for index in range(len(points) - 1):
            x0, y0 = points[index]
            x1, y1 = points[index + 1]
            steps = int(max(abs(x1 - x0), abs(y1 - y0), 1))
            for step in range(steps + 1):
                t = step / steps
                art.blob(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 2.0, ink)
    elif kind == "hand":
        art.round_rect(int(w * 0.28), int(h * 0.44), int(w * 0.44),
                       int(h * 0.44), 8, soft)
        for index in range(4):
            fx = int(w * 0.30) + index * int(w * 0.11)
            art.round_rect(fx, int(h * 0.16), int(w * 0.08), int(h * 0.32), 5,
                           soft)
        art.round_rect(int(w * 0.68), int(h * 0.48), int(w * 0.10),
                       int(h * 0.22), 5, soft)
    elif kind == "spiral":
        points = []
        for step in range(120):
            angle = step * 0.28
            radius = 2 + step * (w * 0.0038)
            points.append((cx + math.cos(angle) * radius,
                           cy + math.sin(angle) * radius * 0.92))
        for x, y in points:
            art.blob(x, y, 2.2, ink)
    elif kind == "grid":
        for x in range(0, w, 6):
            art.vline(x, 0, h - 1, soft)
        for y in range(0, h, 6):
            art.hline(y, 0, w - 1, soft)
        art.rect(int(w * 0.3), int(h * 0.3), int(w * 0.4), int(h * 0.4), ink)
        art.rect(int(w * 0.36), int(h * 0.36), int(w * 0.28), int(h * 0.28),
                 deep)
    return art


def glow_frames(pal: Palette, kind: str = "pulse") -> list[Canvas]:
    """Four frames of a floor tile that will not sit still."""
    frames = []
    for step in range(4):
        art = Canvas(TILE, TILE, pal.ground)
        level = (1.0, 0.7, 0.45, 0.7)[step]
        if kind == "pulse":
            art.ellipse(7.5, 7.5, 7, 7, blend(pal.ground, pal.accent_soft,
                                              0.35 * level))
            art.ellipse(7.5, 7.5, 4.5, 4.5, blend(pal.ground, pal.accent,
                                                  0.75 * level))
            art.blob(7.5, 7.5, 2, warmer(pal.accent, 0.5 * level))
        elif kind == "crawl":
            for x in range(TILE):
                y = (x + step * 4) % TILE
                art.dot(x, y, pal.accent)
                art.dot(x, (y + 8) % TILE, pal.accent_soft)
        elif kind == "checkerflip":
            art.checker(pal.accent if step % 2 else pal.accent_soft,
                        pal.ground, 8)
        elif kind == "scan":
            art.px[:, :] = pal.ground
            art.rect(0, (step * 4) % TILE, TILE, 3, pal.accent)
            art.rect(0, (step * 4 + 8) % TILE, TILE, 2, pal.accent_soft)
        frames.append(art)
    return frames
