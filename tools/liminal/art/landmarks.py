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
