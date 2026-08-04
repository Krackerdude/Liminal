"""Landmarks: the structures that make a world worth walking through.

A world built from repeated props is a tileset. A world with landmarks is a
place. These are large, unique, one-per-world structures — the things a player
stops walking to look at, and the reason a screenshot of one dream is never
mistakable for a screenshot of another.

They live on the **upper** tile layer. The lower layer is nearly full in most
worlds, while the upper one sits almost empty at ten of a hundred and
forty-four slots, and upper-layer tiles draw over the floor with the player in
front of them — which is exactly right for something tall that you walk past
rather than onto.

Every one of them obeys the same rule as the rest of the art: flat colour,
selective shading, rounded forms, outlines in a darker local colour. Scale is
the variable. Several of these are deliberately taller than the screen, so the
player can never see all of one at once.
"""

from __future__ import annotations

import math

from .canvas import (BAYER4, BAYER8, Canvas, RGB, TRANSPARENT, blend, cooler,
                     outline_in, warmer)
from .palette import Palette

TILE = 16


def _art(cols: int, rows: int) -> Canvas:
    return Canvas(cols * TILE, rows * TILE, TRANSPARENT)


# --- pink: compression -------------------------------------------------------

def knot_of_halls(pal: Palette, cols: int = 8, rows: int = 8) -> Canvas:
    """Corridors intersecting at six levels without ever meeting.

    Read as a cross-section: each band is a hallway seen end-on, and none of
    them connect to any other. It is the world's own logic, drawn in one place.
    """
    art = _art(cols, rows)
    w, h = art.w, art.h
    for level in range(6):
        y = 6 + level * (h - 14) // 6
        inset = 4 + (level % 3) * 10
        art.round_rect(inset, y, w - inset * 2, 11, 3, pal.form_dark)
        art.round_rect(inset + 2, y + 2, w - inset * 2 - 4, 7, 2, pal.form)
        # the tiny inaccessible windows
        for x in range(inset + 5, w - inset - 5, 7):
            art.rect(x, y + 4, 3, 3, pal.void)
            art.rect(x, y + 4, 3, 1, pal.form_light)
    for level in range(4):
        x = 10 + level * (w - 20) // 4
        art.round_rect(x, 4, 9, h - 8, 3, cooler(pal.form_dark, 0.2))
        art.round_rect(x + 2, 6, 5, h - 12, 2, pal.form)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def sealed_room(pal: Palette, cols: int = 6, rows: int = 5) -> Canvas:
    """A room entirely enclosed by corridors, with no entrance at all."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 5, pal.form_dark)
    art.round_rect(5, 5, w - 10, h - 10, 4, pal.form)
    art.round_rect(14, 14, w - 28, h - 28, 3, pal.void)
    # a warm light inside something you can never enter
    art.round_rect(18, 18, w - 36, h - 36, 2, blend(pal.void, pal.accent, 0.45))
    for x in range(8, w - 8, 9):
        art.rect(x, 8, 4, 3, pal.form_light)
        art.rect(x, h - 11, 4, 3, pal.form_light)
    return outline_in(art, cooler(pal.form_dark, 0.4))


# --- numbers: material language ----------------------------------------------

def calculator_terrace(pal: Palette, cols: int = 7, rows: int = 5) -> Canvas:
    """A terrace built entirely from calculator buttons."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 4, w, h - 6, 4, pal.form_dark)
    keys = ((246, 240, 220), (200, 206, 200), (240, 154, 96))
    for row in range(4):
        for col in range(7):
            x, y = 5 + col * 15, 9 + row * 13
            tone = keys[(row + col) % 3]
            art.round_rect(x, y, 12, 10, 3, tone)
            art.round_rect(x + 1, y + 1, 10, 4, 2, warmer(tone, 0.35))
            art.rect(x + 4, y + 4, 4, 3, cooler(tone, 0.4))
    return outline_in(art, cooler(pal.form_dark, 0.35))


def pierced_terrace(pal: Palette, cols: int = 7, rows: int = 6) -> Canvas:
    """One perfectly circular hole, through every level."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for level in range(4):
        y = level * (h - 18) // 4
        art.round_rect(level * 4, y, w - level * 8, 22, 4,
                       pal.form if level % 2 else pal.form_light)
        art.rect(level * 4, y + 18, w - level * 8, 4, pal.form_dark)
    art.ellipse(w / 2, h / 2, w * 0.16, h * 0.20, pal.void)
    art.ellipse(w / 2, h / 2, w * 0.16, h * 0.20, cooler(pal.form_dark, 0.3),
                filled=False)
    return outline_in(art, cooler(pal.form_dark, 0.35))


# --- blocks: every slab a different geometry ---------------------------------

def door_slab(pal: Palette, cols: int = 6, rows: int = 5) -> Canvas:
    """A platform consisting only of doors, none of which open."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 6, w, h - 8, 4, pal.form_dark)
    for row in range(2):
        for col in range(5):
            x, y = 4 + col * 18, 10 + row * 30
            art.round_rect(x, y, 14, 26, 6, pal.form)
            art.round_rect(x + 2, y + 2, 10, 22, 5, pal.form_light)
            art.blob(x + 11, y + 14, 1.8, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def furniture_slab(pal: Palette, cols: int = 6, rows: int = 6) -> Canvas:
    """A platform made of stacked furniture, which somehow holds."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    tones = (pal.form, pal.form_light, pal.accent_soft, pal.form_dark)
    y = h - 8
    widths = (w - 4, w - 18, w - 34, w - 50, w - 62)
    for index, band in enumerate(widths):
        if band <= 8:
            break
        x = (w - band) // 2
        height = 13 - index
        art.round_rect(x, y - height, band, height, 3, tones[index % 4])
        art.round_rect(x + 2, y - height + 1, band - 4, 3, 2,
                       warmer(tones[index % 4], 0.3))
        # legs, so each layer reads as a separate object
        art.rect(x + 3, y, 4, 4, cooler(tones[index % 4], 0.4))
        art.rect(x + band - 7, y, 4, 4, cooler(tones[index % 4], 0.4))
        y -= height + 4
    return outline_in(art, cooler(pal.form_dark, 0.4))


# --- toys: a city assembled from playsets ------------------------------------

def brick_tower(pal: Palette, color: RGB, cols: int = 4, rows: int = 8) -> Canvas:
    """An apartment block that is a stack of building bricks."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for level in range(7):
        y = h - 18 - level * 16
        if y < 0:
            break
        tone = color if level % 2 else warmer(color, 0.22)
        art.round_rect(2, y, w - 4, 16, 3, tone)
        art.round_rect(2, y, w - 4, 4, 3, warmer(tone, 0.3))
        art.rect(2, y + 13, w - 4, 3, cooler(tone, 0.3))
        # studs on top, and windows in the side
        for sx in range(6, w - 8, 12):
            art.blob(sx + 4, y - 1, 3.2, warmer(tone, 0.45))
        for wx in range(6, w - 10, 12):
            art.round_rect(wx, y + 5, 7, 6, 1, blend(tone, pal.accent, 0.55))
    art.round_rect(0, h - 6, w, 6, 2, cooler(color, 0.45))
    return outline_in(art, cooler(color, 0.5))


def board_game_plaza(pal: Palette, cols: int = 8, rows: int = 8) -> Canvas:
    """A public square that is a board game nobody is playing."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 6, pal.form_dark)
    art.round_rect(3, 3, w - 6, h - 6, 5, (246, 240, 226))
    # the track: squares round the edge, in four colours
    tones = ((232, 130, 132), (122, 190, 200), (248, 214, 118), (150, 200, 160))
    step, index = 13, 0
    for x in range(8, w - 12, step):
        art.round_rect(x, 8, 11, 11, 2, tones[index % 4]); index += 1
        art.round_rect(x, h - 19, 11, 11, 2, tones[(index + 2) % 4])
    for y in range(21, h - 20, step):
        art.round_rect(8, y, 11, 11, 2, tones[index % 4]); index += 1
        art.round_rect(w - 19, y, 11, 11, 2, tones[(index + 1) % 4])
    art.ellipse(w / 2, h / 2, w * 0.18, h * 0.18, (210, 204, 196))
    art.ellipse(w / 2, h / 2, w * 0.13, h * 0.13, (246, 240, 226))
    return outline_in(art, cooler(pal.form_dark, 0.4))


def track_junction(pal: Palette, cols: int = 6, rows: int = 6) -> Canvas:
    """Where the roads, which are train tracks, cross."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    sleeper = (168, 132, 96)
    rail = (196, 200, 208)
    for y in range(4, h - 4, 8):
        art.rect(6, y, w - 12, 4, sleeper)
    for y in range(0, h, 1):
        art.dot(w // 2 - 8, y, rail)
        art.dot(w // 2 + 7, y, rail)
    for x in range(6, w - 6, 8):
        art.rect(x, 6, 4, h - 12, sleeper)
    for x in range(0, w, 1):
        art.dot(x, h // 2 - 8, rail)
        art.dot(x, h // 2 + 7, rail)
    art.ellipse(w / 2, h / 2, 9, 9, (206, 96, 96))
    art.ellipse(w / 2, h / 2, 6, 6, (246, 226, 200))
    return outline_in(art, cooler(sleeper, 0.45))


# --- umbrellas: umbrellas as architecture ------------------------------------

def umbrella_tower(pal: Palette, color: RGB, cols: int = 3,
                   rows: int = 9) -> Canvas:
    """A closed umbrella the size of a tower block."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(w // 2 - 7, 10, 15, h - 24, 6, color)
    art.rect(w // 2 - 7, 10, 5, h - 24, warmer(color, 0.28))
    art.rect(w // 2 + 3, 10, 5, h - 24, cooler(color, 0.28))
    for y in range(18, h - 20, 14):
        art.rect(w // 2 - 7, y, 15, 3, cooler(color, 0.4))
        art.round_rect(w // 2 - 4, y + 5, 8, 6, 1, blend(color, pal.accent, 0.5))
    for row in range(9):
        span = 7 - row
        if span <= 0:
            break
        art.hline(2 + row, w // 2 - span, w // 2 + span, warmer(color, 0.15))
    art.rect(w // 2 - 1, h - 14, 3, 12, pal.form_dark)
    art.rect(w // 2 - 5, h - 4, 4, 3, pal.form_dark)
    return outline_in(art, cooler(color, 0.5))


def rib_bridge(pal: Palette, cols: int = 8, rows: int = 3) -> Canvas:
    """A walkway made from the ribs of something enormous."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.rect(0, h // 2 - 3, w, 7, pal.form)
    art.rect(0, h // 2 - 3, w, 2, pal.form_light)
    for x in range(4, w - 4, 11):
        art.line(x, h // 2 + 3, x + 5, h - 2, pal.form_dark)
        art.line(x, h // 2 - 3, x + 5, 1, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.35))


# --- stars: islands that are different realities -----------------------------

def eye_island(pal: Palette, cols: int = 7, rows: int = 5) -> Canvas:
    """An island that is a giant eye, looking up."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.ellipse(w / 2, h / 2, w * 0.48, h * 0.44, pal.accent)
    art.ellipse(w / 2, h / 2, w * 0.44, h * 0.38, (246, 248, 240))
    art.blob(w / 2, h / 2, h * 0.30, (58, 92, 130))
    art.blob(w / 2, h / 2, h * 0.16, (14, 16, 30))
    art.blob(w / 2 - w * 0.07, h / 2 - h * 0.11, h * 0.07, (255, 255, 255))
    return outline_in(art, cooler(pal.form_dark, 0.3))


def chair_island(pal: Palette, cols: int = 4, rows: int = 4) -> Canvas:
    """Entirely water, except for one chair."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.ellipse(w / 2, h * 0.66, w * 0.40, h * 0.22, pal.form)
    art.ellipse(w / 2, h * 0.62, w * 0.34, h * 0.17, pal.accent_soft)
    cx, cy = w // 2, int(h * 0.56)
    art.round_rect(cx - 8, cy - 16, 16, 18, 3, (168, 132, 96))
    art.round_rect(cx - 10, cy, 20, 5, 2, (196, 158, 116))
    art.rect(cx - 8, cy + 4, 3, 9, (140, 108, 78))
    art.rect(cx + 5, cy + 4, 3, 9, (140, 108, 78))
    return outline_in(art, cooler(pal.form_dark, 0.35))


def indoor_island(pal: Palette, cols: int = 6, rows: int = 5) -> Canvas:
    """An island that is somehow interior: wallpaper, a floor, a ceiling."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 3, (78, 66, 92))
    art.rect(4, 4, w - 8, h - 14, (170, 150, 168))
    for x in range(4, w - 8, 6):
        art.rect(x, 4, 2, h - 14, (150, 130, 152))
    art.rect(4, h - 12, w - 8, 9, (128, 96, 76))
    art.rect(4, h - 12, w - 8, 2, (162, 128, 98))
    art.round_rect(w // 2 - 8, h - 34, 17, 22, 5, (58, 48, 66))
    art.round_rect(w // 2 - 6, h - 32, 13, 20, 4, (226, 200, 150))
    return outline_in(art, (44, 36, 54))


# --- faces: a solid green mass ------------------------------------------------

def hollow_trunk(pal: Palette, cols: int = 7, rows: int = 9) -> Canvas:
    """A trunk with an apartment block inside it."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(4, 0, w - 8, h, 12, pal.form)
    art.round_rect(8, 4, w - 16, h - 8, 10, warmer(pal.form, 0.15))
    art.round_rect(w // 2 - 20, 18, 40, h - 30, 6, pal.void)
    for row in range(5):
        y = 26 + row * 14
        if y > h - 24:
            break
        for col in range(3):
            art.round_rect(w // 2 - 15 + col * 11, y, 8, 9, 1,
                           blend(pal.void, pal.accent, 0.62))
    art.round_rect(w // 2 - 6, h - 26, 13, 18, 5, pal.form_dark)
    for canopy in range(3):
        art.blob(w * (0.28 + canopy * 0.22), 8, 14, pal.accent_soft)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def root_arch(pal: Palette, cols: int = 8, rows: int = 5) -> Canvas:
    """Exposed roots the size of motorway flyovers."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for index in range(3):
        base = h - 4 - index * 3
        thickness = 11 - index * 2
        for x in range(w):
            y = int(base - math.sin(x / w * math.pi) * (h * 0.62 - index * 6))
            art.rect(x, y, 1, thickness, pal.form if index % 2 else
                     pal.form_light)
            art.dot(x, y, warmer(pal.form_light, 0.25))
    return outline_in(art, cooler(pal.form_dark, 0.4))


# --- stairs: impossible circulation ------------------------------------------

def stair_knot(pal: Palette, cols: int = 8, rows: int = 8) -> Canvas:
    """Four flights that arrive at each other and at nothing."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    steps = 9
    for side in range(4):
        for index in range(steps):
            t = index / steps
            if side == 0:
                x, y = int(t * (w - 22)) + 4, int(h * 0.5 - t * h * 0.34)
            elif side == 1:
                x, y = int(w - 22 - t * (w - 22)), int(h * 0.5 + t * h * 0.34)
            elif side == 2:
                x, y = int(w * 0.5 - t * w * 0.34), int(t * (h - 22)) + 4
            else:
                x, y = int(w * 0.5 + t * w * 0.34), int(h - 22 - t * (h - 22))
            art.round_rect(x, y, 18, 7, 2, pal.form)
            art.rect(x, y, 18, 2, pal.form_light)
            art.rect(x, y + 5, 18, 2, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.3))


def stair_arena(pal: Palette, cols: int = 9, rows: int = 7) -> Canvas:
    """A room whose floor is entirely stairs, all of them descending."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for ring in range(7):
        inset = ring * 7
        if w - inset * 2 < 10:
            break
        tone = pal.form if ring % 2 else pal.form_light
        art.round_rect(inset, inset, w - inset * 2, h - inset * 2, 4, tone)
        art.rect(inset, inset, w - inset * 2, 2, warmer(tone, 0.3))
        art.rect(inset, h - inset * 2 + inset - 2, w - inset * 2, 2,
                 cooler(tone, 0.3))
    art.ellipse(w / 2, h / 2, 7, 6, pal.void)
    return outline_in(art, cooler(pal.form_dark, 0.3))


# --- checker: the anomalies ---------------------------------------------------

def circular_room_marker(pal: Palette, cols: int = 5, rows: int = 5) -> Canvas:
    """The only round thing in a world of squares."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.ellipse(w / 2, h / 2, w * 0.46, h * 0.46, pal.form_dark)
    art.ellipse(w / 2, h / 2, w * 0.40, h * 0.40, pal.accent)
    art.ellipse(w / 2, h / 2, w * 0.30, h * 0.30, pal.form_light)
    art.ellipse(w / 2, h / 2, w * 0.16, h * 0.16, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.35))


# --- sand: regions of one enormous room --------------------------------------

def ladder_forest(pal: Palette, cols: int = 7, rows: int = 8) -> Canvas:
    """Suspended ladders, hanging from a ceiling nobody has seen."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    wood = pal.form_dark
    for index in range(5):
        x = 6 + index * 21
        top = index * 7
        length = h - top - (6 + (index % 3) * 12)
        art.rect(x, top, 3, length, wood)
        art.rect(x + 12, top, 3, length, wood)
        for y in range(top + 6, top + length, 11):
            art.rect(x, y, 15, 3, warmer(wood, 0.28))
    return outline_in(art, cooler(wood, 0.4))


def upside_down_cathedral(pal: Palette, cols: int = 9, rows: int = 8) -> Canvas:
    """Hanging from the unseen ceiling, pointing the wrong way."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(6, 0, w - 12, int(h * 0.44), 4, pal.form)
    art.rect(6, 0, w - 12, 5, pal.form_light)
    for x in range(14, w - 14, 16):
        art.round_rect(x, int(h * 0.16), 10, int(h * 0.26), 5, pal.form_dark)
        art.round_rect(x + 2, int(h * 0.19), 6, int(h * 0.20), 3,
                       blend(pal.form_dark, pal.accent, 0.5))
    # the spire, downward
    for row in range(int(h * 0.50)):
        span = int((1 - row / (h * 0.50)) * (w * 0.20)) + 1
        art.hline(int(h * 0.44) + row, w // 2 - span, w // 2 + span, pal.form)
    art.blob(w / 2, h - 4, 3.5, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def ceramic_sea(pal: Palette, cols: int = 6, rows: int = 4) -> Canvas:
    """A drift of broken tiles, all of them face up."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    tones = (pal.form_light, pal.accent_soft, pal.form, pal.accent)
    for index in range(46):
        x = (index * 37) % (w - 12)
        y = (index * 23) % (h - 10)
        art.round_rect(x, y, 10 + index % 4, 8 + index % 3, 1,
                       tones[index % 4])
        art.rect(x, y, 10 + index % 4, 2, warmer(tones[index % 4], 0.3))
    return outline_in(art, cooler(pal.form_dark, 0.3))


# --- neon: density -----------------------------------------------------------

def billboard_room(pal: Palette, cols: int = 7, rows: int = 6) -> Canvas:
    """A room inside a sign, with the sign still switched on."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h - 12, 3, pal.void)
    art.outline(0, 0, w, h - 12, pal.form)
    art.outline(3, 3, w - 6, h - 18, pal.accent)
    for row in range(3):
        for col in range(5):
            x, y = 9 + col * 19, 9 + row * 15
            art.round_rect(x, y, 14, 11, 2, blend(pal.void, pal.form, 0.30))
            art.outline(x, y, 14, 11, pal.form)
            art.rect(x + 4, y + 3, 6, 5, pal.accent_soft)
    art.rect(w // 2 - 3, h - 12, 6, 12, pal.form_dark)
    art.rect(w // 2 - 10, h - 4, 20, 4, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.35))


def hanging_neighbourhood(pal: Palette, cols: int = 8, rows: int = 7) -> Canvas:
    """Houses suspended from cables, one above the other."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for index in range(5):
        x = 5 + index * 24
        drop = 10 + (index % 3) * 22
        art.rect(x + 9, 0, 2, drop, pal.form_dark)
        art.round_rect(x, drop, 21, 19, 4, pal.form)
        art.round_rect(x + 2, drop + 2, 17, 7, 3, pal.accent)
        for wx in range(x + 4, x + 17, 6):
            art.round_rect(wx, drop + 11, 4, 5, 1, pal.accent_soft)
    return outline_in(art, cooler(pal.form_dark, 0.4))


# --- hands: the procession ----------------------------------------------------

def door_court(pal: Palette, cols: int = 7, rows: int = 5) -> Canvas:
    """A court filled with hundreds of tiny doors."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 4, pal.form_dark)
    art.round_rect(3, 3, w - 6, h - 6, 3, pal.form)
    for row in range(6):
        for col in range(13):
            x, y = 7 + col * 8, 7 + row * 11
            if x + 6 > w - 5 or y + 9 > h - 5:
                continue
            art.round_rect(x, y, 6, 9, 2, pal.form_light if (row + col) % 2
                           else pal.accent_soft)
            art.dot(x + 4, y + 5, pal.form_dark)
    return outline_in(art, cooler(pal.form_dark, 0.4))


# --- the city the forest ate --------------------------------------------------
# Things that have no business being here, which is the entire point.  These
# are drawn as though the forest arrived second and simply grew through
# everything without moving any of it, and nothing was ever switched off.

def traffic_light(pal: Palette, cols: int = 1, rows: int = 4) -> Canvas:
    """Still working. Still cycling. Nothing has driven past in a long time."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.rect(w // 2 - 2, 12, 4, h - 14, (72, 76, 74))
    art.rect(w // 2 - 2, 12, 1, h - 14, (108, 112, 108))
    art.round_rect(w // 2 - 6, 2, 12, 26, 3, (48, 52, 50))
    for index, tone in enumerate(((198, 74, 68), (238, 190, 96),
                                  (120, 196, 130))):
        cy = 7 + index * 8
        art.blob(w / 2, cy, 3.4, cooler(tone, 0.55))
    # only the amber is lit, and it is the only warm thing for a long way
    art.blob(w / 2, 15, 3.4, (238, 190, 96))
    art.blob(w / 2 - 1, 14, 1.4, (255, 240, 190))
    art.round_rect(w // 2 - 5, h - 3, 11, 3, 1, (40, 44, 42))
    return outline_in(art, (26, 30, 28))


def bus_shelter(pal: Palette, cols: int = 4, rows: int = 3) -> Canvas:
    """A timetable nobody has read, under glass nobody has broken."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.rect(3, 2, w - 6, 4, (150, 156, 160))
    art.rect(3, 2, w - 6, 2, (188, 194, 198))
    art.rect(4, 6, 3, h - 10, (120, 126, 130))
    art.rect(w - 7, 6, 3, h - 10, (120, 126, 130))
    art.rect(8, 7, w - 16, h - 13, blend((176, 200, 200), pal.ground, 0.35))
    art.round_rect(w - 16, 9, 9, 12, 1, (230, 226, 214))
    for line in range(4):
        art.rect(w - 14, 11 + line * 3, 5, 1, (140, 140, 136))
    art.rect(6, h - 6, w - 12, 3, (110, 96, 84))
    art.rect(6, h - 3, 2, 3, (80, 84, 86))
    art.rect(w - 8, h - 3, 2, 3, (80, 84, 86))
    return outline_in(art, (52, 58, 58))


def phone_box(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """The light inside is on. The receiver is off the hook."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(2, 2, w - 4, h - 3, 3, (166, 62, 62))
    art.round_rect(4, 6, w - 8, h - 12, 2, (226, 232, 226))
    art.round_rect(5, 7, w - 10, h - 14, 2, blend((226, 232, 226),
                                                  (240, 220, 150), 0.55))
    art.rect(2, 2, w - 4, 4, (196, 84, 80))
    art.rect(4, 3, w - 8, 2, (250, 226, 180))
    for y in range(9, h - 9, 5):
        art.rect(4, y, w - 8, 1, (150, 56, 56))
    art.rect(3, h - 3, w - 6, 3, (108, 40, 40))
    return outline_in(art, (68, 26, 26))


def apartment_facade(pal: Palette, cols: int = 6, rows: int = 8) -> Canvas:
    """A block of flats with a trunk growing out through the middle of it.

    Half the windows are lit. Nobody has come to a single one of them.
    """
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 4, w, h - 4, 3, (128, 124, 130))
    art.rect(2, 6, w - 4, h - 8, (150, 146, 152))
    art.rect(0, 4, w, 3, (176, 172, 178))
    lit = ((240, 222, 158), (226, 236, 240))
    for row in range(6):
        for col in range(4):
            x, y = 6 + col * 20, 11 + row * 15
            if y + 10 > h - 6:
                continue
            on = (row * 4 + col) % 3 == 0
            art.round_rect(x, y, 13, 10, 1,
                           lit[(row + col) % 2] if on else (66, 66, 74))
            if on:
                art.rect(x + 1, y + 1, 11, 3, warmer(lit[(row + col) % 2], 0.4))
            art.rect(x, y + 4, 13, 1, (96, 94, 100))
    # the trunk, straight through the building, undisturbed
    trunk = pal.form
    art.round_rect(w // 2 - 9, 0, 18, h, 7, trunk)
    art.rect(w // 2 - 9, 0, 5, h, warmer(trunk, 0.22))
    art.rect(w // 2 + 4, 0, 5, h, cooler(trunk, 0.25))
    art.blob(w * 0.30, 6, 15, pal.accent_soft)
    art.blob(w * 0.70, 4, 13, pal.accent_soft)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def escalator(pal: Palette, cols: int = 3, rows: int = 6) -> Canvas:
    """Going up, into the canopy, out of sight. It is still running."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.rect(4, 0, w - 8, h, (104, 108, 112))
    for step in range(h // 5):
        y = h - 6 - step * 5
        art.rect(6, y, w - 12, 3, (156, 160, 164))
        art.rect(6, y + 3, w - 12, 1, (72, 76, 80))
    art.rect(2, 0, 3, h, (132, 136, 140))
    art.rect(w - 5, 0, 3, h, (132, 136, 140))
    art.rect(2, 0, 3, h, (132, 136, 140))
    for y in range(2, h, 9):
        art.rect(1, y, 5, 2, (88, 92, 96))
        art.rect(w - 6, y, 5, 2, (88, 92, 96))
    art.blob(w * 0.5, 3, 11, pal.accent_soft)
    return outline_in(art, (46, 50, 54))


def pylon_overgrown(pal: Palette, cols: int = 4, rows: int = 7) -> Canvas:
    """An electricity pylon with a tree grown through the lattice."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    steel = (128, 132, 138)
    for row in range(h):
        t = row / h
        span = int(4 + t * (w * 0.42))
        art.dot(w // 2 - span, row, steel)
        art.dot(w // 2 + span, row, steel)
    for y in range(6, h - 4, 11):
        span = int(4 + (y / h) * (w * 0.42))
        art.rect(w // 2 - span, y, span * 2, 2, steel)
        art.line(w // 2 - span, y, w // 2 + span, y + 9, steel)
        art.line(w // 2 + span, y, w // 2 - span, y + 9, steel)
    for y in (10, 24):
        art.rect(4, y - 2, w - 8, 2, (96, 100, 106))
    art.round_rect(w // 2 - 6, h // 3, 13, h - h // 3, 5, pal.form)
    art.blob(w * 0.5, h * 0.30, 17, pal.accent_soft)
    art.blob(w * 0.26, h * 0.38, 11, pal.accent_soft)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def dead_car(pal: Palette, cols: int = 3, rows: int = 2) -> Canvas:
    """Parked, and then left, and then grown over."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    body = (108, 118, 132)
    art.round_rect(2, h - 17, w - 4, 13, 5, body)
    art.round_rect(9, h - 23, w - 20, 9, 4, cooler(body, 0.15))
    art.round_rect(11, h - 21, w - 24, 6, 3, (150, 172, 176))
    art.blob(10, h - 4, 4, (44, 46, 50))
    art.blob(w - 11, h - 4, 4, (44, 46, 50))
    art.blob(10, h - 4, 2, (86, 88, 92))
    art.blob(w - 11, h - 4, 2, (86, 88, 92))
    # the forest, reclaiming it
    art.blob(6, h - 18, 6, pal.accent_soft)
    art.blob(w - 8, h - 20, 5, pal.accent_soft)
    art.blob(w // 2, h - 24, 4, pal.accent_soft)
    return outline_in(art, cooler(body, 0.5))


def vending_machine(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """Lit from inside. Fully stocked. Miles from any road."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(2, 3, w - 4, h - 5, 2, (70, 76, 92))
    art.rect(4, 6, w - 12, h - 12, (236, 240, 246))
    tones = ((226, 96, 96), (120, 176, 226), (238, 206, 126), (150, 200, 160))
    for row in range(4):
        for col in range(3):
            x, y = 6 + col * 6, 9 + row * 8
            if y + 5 > h - 8:
                continue
            art.rect(x, y, 4, 5, tones[(row + col) % 4])
    art.rect(w - 8, 6, 4, h - 12, (52, 58, 72))
    art.rect(w - 7, 9, 2, 6, (240, 226, 150))
    art.rect(3, h - 4, w - 6, 3, (44, 50, 62))
    return outline_in(art, (28, 32, 42))


def road_sign(pal: Palette, cols: int = 2, rows: int = 3) -> Canvas:
    """It still says something. It is not in any language you know."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.rect(w // 2 - 1, 12, 3, h - 14, (140, 144, 148))
    art.round_rect(1, 2, w - 2, 13, 2, (96, 156, 118))
    art.round_rect(2, 3, w - 4, 11, 2, (120, 180, 138))
    for line, width in ((5, 14), (8, 20), (11, 11)):
        art.rect(5, line, width, 2, (238, 244, 238))
    art.round_rect(w // 2 - 4, h - 3, 9, 3, 1, (100, 104, 108))
    return outline_in(art, (48, 72, 58))


# --- hands: the procession ----------------------------------------------------

def colossal_hand(pal: Palette, cols: int = 9, rows: int = 12) -> Canvas:
    """A hand taller than the screen. You cannot see all of it at once."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    stone, light, dark = pal.form, pal.form_light, pal.form_dark
    palm_top = int(h * 0.52)
    art.round_rect(int(w * 0.16), palm_top, int(w * 0.68), h - palm_top, 14,
                   stone)
    finger_w = int(w * 0.13)
    for index, frac in enumerate((0.40, 0.50, 0.46, 0.34)):
        fx = int(w * 0.19) + index * (finger_w + 4)
        top = int(palm_top - h * frac)
        art.round_rect(fx, top, finger_w, palm_top - top + 14, finger_w // 2,
                       stone)
        art.rect(fx, top, 4, palm_top - top + 14, light)
        art.rect(fx + finger_w - 4, top, 4, palm_top - top + 14, dark)
        # a joint line, so it reads as a finger and not a column
        art.rect(fx, top + int(h * 0.10), finger_w, 2, cooler(dark, 0.2))
    art.round_rect(int(w * 0.74), palm_top + 8, finger_w, int(h * 0.26),
                   finger_w // 2, stone)
    art.rect(int(w * 0.16), palm_top, 5, h - palm_top, light)
    art.rect(int(w * 0.80), palm_top, 5, h - palm_top, dark)
    # an eye set into the palm, open
    art.ellipse(w / 2, palm_top + h * 0.22, w * 0.19, h * 0.075, light)
    art.ellipse(w / 2, palm_top + h * 0.22, w * 0.16, h * 0.055, (238, 240, 234))
    art.blob(w / 2, palm_top + h * 0.22, h * 0.042, (48, 62, 74))
    art.blob(w / 2, palm_top + h * 0.22, h * 0.018, (12, 14, 20))
    return outline_in(art, cooler(dark, 0.35))


def hand_ring(pal: Palette, cols: int = 10, rows: int = 8) -> Canvas:
    """Nine hands in a circle, all of them pointing inward at nothing."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for index in range(9):
        angle = index * math.tau / 9
        cx = w / 2 + math.cos(angle) * w * 0.36
        cy = h / 2 + math.sin(angle) * h * 0.36
        lean = -math.cos(angle) * 4
        art.round_rect(int(cx - 7), int(cy - 4), 15, 18, 6, pal.form)
        for finger in range(3):
            fx = int(cx - 5 + finger * 5 + lean)
            art.round_rect(fx, int(cy - 14 + abs(finger - 1) * 3), 4,
                           16 - abs(finger - 1) * 3, 2, pal.form)
        art.rect(int(cx - 7), int(cy - 4), 4, 18, pal.form_light)
    art.ellipse(w / 2, h / 2, w * 0.13, h * 0.13, pal.void)
    art.ellipse(w / 2, h / 2, w * 0.10, h * 0.10, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.35))


def hand_holding_door(pal: Palette, cols: int = 6, rows: int = 9) -> Canvas:
    """A hand coming out of the ground with a door held upright in it."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(int(w * 0.14), int(h * 0.56), int(w * 0.72),
                   int(h * 0.44), 12, pal.form)
    for index in range(4):
        fx = int(w * 0.16) + index * 13
        art.round_rect(fx, int(h * 0.40), 10, int(h * 0.26), 5, pal.form)
        art.rect(fx, int(h * 0.40), 3, int(h * 0.26), pal.form_light)
    # the door, standing in the palm, ajar and lit
    dx, dy, dw, dh = w // 2 - 16, int(h * 0.10), 32, int(h * 0.48)
    art.round_rect(dx, dy, dw, dh, 14, pal.form_dark)
    art.round_rect(dx + 3, dy + 3, dw - 6, dh - 3, 12, pal.accent_soft)
    art.rect(dx + dw - 13, dy + 6, 9, dh - 8, warmer(pal.accent, 0.5))
    art.blob(dx + dw - 8, dy + dh // 2, 2.2, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.35))


# --- blocks: scale that will not hold still -----------------------------------

def monolith_block(pal: Palette, color: RGB, cols: int = 10,
                   rows: int = 10) -> Canvas:
    """One block, the size of a district. It has a stud you can stand on."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 10, color)
    art.round_rect(0, 0, w, 10, 10, warmer(color, 0.30))
    art.rect(0, h - 10, w, 10, cooler(color, 0.32))
    art.rect(w - 10, 10, 10, h - 20, cooler(color, 0.18))
    for row in range(3):
        for col in range(3):
            art.blob(w * (0.22 + col * 0.28), h * (0.24 + row * 0.26),
                     w * 0.075, warmer(color, 0.50))
            art.blob(w * (0.22 + col * 0.28) - 2, h * (0.24 + row * 0.26) - 2,
                     w * 0.030, warmer(color, 0.75))
    return outline_in(art, cooler(color, 0.5))


def fractal_block(pal: Palette, color: RGB, cols: int = 7,
                  rows: int = 7) -> Canvas:
    """A block made of blocks made of blocks."""
    art = _art(cols, rows)
    w, h = art.w, art.h

    def square(x, y, size, depth):
        tone = warmer(color, 0.12 * depth) if depth % 2 else cooler(color,
                                                                    0.10 * depth)
        art.round_rect(int(x), int(y), int(size), int(size), max(1, int(size / 8)),
                       tone)
        art.round_rect(int(x), int(y), int(size), max(2, int(size / 6)),
                       max(1, int(size / 8)), warmer(tone, 0.28))
        if depth >= 3 or size < 16:
            return
        half = size / 2
        for ox, oy in ((0, 0), (half, 0), (0, half), (half, half)):
            if (ox or oy) and depth < 2:
                square(x + ox + size / 16, y + oy + size / 16, half - size / 8,
                       depth + 1)

    square(0, 0, min(w, h), 0)
    return outline_in(art, cooler(color, 0.5))


# --- umbrellas: canopies as terrain -------------------------------------------

def upturned_pool(pal: Palette, color: RGB, cols: int = 5,
                  rows: int = 4) -> Canvas:
    """An umbrella lying on its back, full of water it never caught."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    art.ellipse(w / 2, h * 0.58, w * 0.46, h * 0.36, color)
    art.ellipse(w / 2, h * 0.56, w * 0.40, h * 0.30, cooler(color, 0.25))
    art.ellipse(w / 2, h * 0.56, w * 0.34, h * 0.25, pal.accent_soft)
    art.ellipse(w / 2 - w * 0.08, h * 0.50, w * 0.13, h * 0.07,
                warmer(pal.accent_soft, 0.40))
    for index in range(6):
        angle = index * math.tau / 6
        art.line(int(w / 2), int(h * 0.56),
                 int(w / 2 + math.cos(angle) * w * 0.44),
                 int(h * 0.58 + math.sin(angle) * h * 0.34),
                 cooler(color, 0.35))
    art.rect(w // 2 - 1, int(h * 0.10), 3, int(h * 0.40), pal.form_dark)
    return outline_in(art, cooler(color, 0.45))


def handle_grove(pal: Palette, cols: int = 6, rows: int = 5) -> Canvas:
    """Handles, with no canopies on any of them."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for index in range(7):
        x = 5 + index * 13
        top = 4 + (index % 3) * 9
        art.rect(x, top, 4, h - top - 6, pal.form_dark)
        art.rect(x, top, 2, h - top - 6, warmer(pal.form_dark, 0.3))
        # the hook, curling the wrong way
        art.rect(x - 5, top, 6, 3, pal.form_dark)
        art.rect(x - 5, top, 3, 7, pal.form_dark)
        art.blob(x + 2, h - 5, 3.4, cooler(pal.form_dark, 0.25))
    return outline_in(art, cooler(pal.form_dark, 0.45))


# --- stars: islands that are other places -------------------------------------

def spiral_island(pal: Palette, cols: int = 8, rows: int = 7) -> Canvas:
    """An island that is a single path coiled into itself."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for step in range(240):
        angle = step * 0.13
        radius = 3 + step * (min(w, h) * 0.0017)
        x = w / 2 + math.cos(angle) * radius
        y = h / 2 + math.sin(angle) * radius * 0.82
        art.blob(x, y, 4.6, pal.form)
        art.blob(x, y - 1, 3.0, pal.accent_soft)
    art.blob(w / 2, h / 2, 5, pal.accent)
    return outline_in(art, cooler(pal.form_dark, 0.4))


def inverted_island(pal: Palette, cols: int = 6, rows: int = 6) -> Canvas:
    """The same island, upside down, with its sky underneath it."""
    art = _art(cols, rows)
    w, h = art.w, art.h
    for row in range(int(h * 0.55)):
        t = row / (h * 0.55)
        span = int(w * 0.44 * (1 - (1 - t) ** 2))
        if span > 0:
            art.hline(row, w // 2 - span, w // 2 + span, pal.form_dark)
    art.ellipse(w / 2, h * 0.58, w * 0.44, h * 0.15, pal.form)
    art.ellipse(w / 2, h * 0.62, w * 0.42, h * 0.13, pal.accent_soft)
    # a tree, hanging down
    art.rect(w // 2 - 2, int(h * 0.66), 5, int(h * 0.16), pal.form_dark)
    art.blob(w / 2, h * 0.88, w * 0.16, pal.accent_soft)
    art.blob(w / 2 - w * 0.11, h * 0.82, w * 0.10, pal.accent_soft)
    return outline_in(art, cooler(pal.form_dark, 0.4))
