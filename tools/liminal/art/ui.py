"""Interface art and full-screen overlays.

Two jobs live here.

The first is the RPG Maker system graphic — a 160x80 sheet holding the window
background, its frame, the two cursor phases, the text shadow colour and the
twenty text-colour swatches the font is masked through.  Getting the swatch
grid right is what makes menu text look like it belongs to this game rather
than to RPG Maker.

The second is the overlay library.  These are 320x240 pictures the interpreter
shows on top of the map to give each world its own camera: a vignette, CRT
scanlines, drifting dust, a light shaft, analogue static.  They are drawn at
full strength and then faded with ShowPicture's transparency parameter, so one
picture can serve as both a hint and a shout.
"""

from __future__ import annotations

import math

import numpy as np

from .canvas import (BAYER4, BAYER8, Canvas, RGB, TRANSPARENT, blend, cooler,
                     warmer)
from .glyphs import draw_text, draw_text_centered, text_width

SCREEN_W, SCREEN_H = 320, 240
SYS_W, SYS_H = 160, 80


# --- system graphic ----------------------------------------------------------

def system_graphic(*, back: RGB = (44, 38, 66), back_edge: RGB = (30, 26, 48),
                   frame: RGB = (206, 178, 122), frame_dark: RGB = (120, 96, 66),
                   cursor: RGB = (238, 214, 158)) -> Canvas:
    """The window skin.

    Region map (all coordinates in the 160x80 sheet):
    ``(0,0,32,32)`` window background, ``(32,0,32,32)`` the 8px frame ring,
    ``(64,0,32,32)`` and ``(96,0,32,32)`` the two cursor phases,
    ``(16,32,16,16)`` the text shadow colour, and ``(0,48,160,32)`` the twenty
    text-colour swatches — ten across, two down, each sampled from two pixels
    in and four pixels down.
    """
    sheet = Canvas(SYS_W, SYS_H, (0, 0, 0))

    # -- window background: a soft vertical wash, tiled behind every window
    for y in range(32):
        t = y / 31
        sheet.rect(0, y, 32, 1, blend(back, back_edge, t))
    sheet.dither(warmer(back, 0.06), 0.18, BAYER8)

    # -- frame: an 8px ring.  Corners are the four 8x8 blocks, and the middle
    # 16px of each side is tiled along the window edge.
    fx = 32
    sheet.rect(fx, 0, 32, 32, TRANSPARENT)
    for corner_x, corner_y in ((0, 0), (24, 0), (0, 24), (24, 24)):
        sheet.round_rect(fx + corner_x, corner_y, 8, 8, 3, frame)
        sheet.round_rect(fx + corner_x + 1, corner_y + 1, 6, 6, 2,
                         warmer(frame, 0.25))
        sheet.round_rect(fx + corner_x + 2, corner_y + 2, 4, 4, 1, frame_dark)
    for x in range(8, 24):
        sheet.rect(fx + x, 2, 1, 4, frame)
        sheet.rect(fx + x, 2, 1, 1, warmer(frame, 0.3))
        sheet.rect(fx + x, 26, 1, 4, frame)
        sheet.rect(fx + x, 29, 1, 1, frame_dark)
    for y in range(8, 24):
        sheet.rect(fx + 2, y, 4, 1, frame)
        sheet.rect(fx + 2, y, 1, 1, warmer(frame, 0.3))
        sheet.rect(fx + 26, y, 4, 1, frame)
        sheet.rect(fx + 29, y, 1, 1, frame_dark)

    # -- cursors: two phases of a soft rounded highlight
    for index, (cx, strength) in enumerate(((64, 0.55), (96, 0.85))):
        sheet.rect(cx, 0, 32, 32, TRANSPARENT)
        tone = blend(back, cursor, strength)
        sheet.round_rect(cx + 1, 1, 30, 30, 4, tone)
        sheet.round_rect(cx + 3, 3, 26, 26, 3, blend(back, cursor, strength * 0.35))
        sheet.round_rect(cx + 1, 1, 30, 3, 3, warmer(cursor, 0.3 * strength))

    # -- shop-party icons and airship shadow: unused, but must not be garbage
    sheet.rect(128, 0, 32, 48, back_edge)

    # -- text shadow colour, read from a 16x16 block at (16, 32)
    sheet.rect(16, 32, 16, 16, (20, 16, 30))
    sheet.rect(0, 32, 16, 16, back_edge)

    # -- the twenty text colours.  The font masks a 12-pixel-tall band from the
    # bottom of each swatch, so each one is a two-step vertical ramp.
    palette: list[RGB] = [
        (246, 240, 226),   # 0  default: warm paper
        (238, 206, 132),   # 1  headings
        (196, 226, 236),   # 2  cool emphasis
        (140, 134, 148),   # 3  disabled
        (226, 132, 128),   # 4  critical
        (158, 108, 128),   # 5  knocked out
        (206, 190, 246),   # 6
        (168, 210, 198),   # 7
        (244, 178, 206),   # 8
        (176, 226, 168),   # 9  healing
        (232, 226, 214),
        (214, 186, 150),
        (160, 190, 214),
        (120, 116, 128),
        (206, 154, 148),
        (140, 120, 156),
        (186, 206, 226),
        (150, 190, 180),
        (222, 172, 190),
        (160, 200, 160),
    ]
    for index, color in enumerate(palette):
        sx = (index % 10) * 16
        sy = 48 + (index // 10) * 16
        top = warmer(color, 0.30)
        bottom = cooler(color, 0.26)
        for row in range(16):
            t = row / 15
            sheet.rect(sx, sy + row, 16, 1, blend(top, bottom, t))
    return sheet


# --- title and game over -----------------------------------------------------

def title_screen() -> Canvas:
    """A door, ajar, in the dark.  The only thing the game asks of you."""
    art = Canvas(SCREEN_W, SCREEN_H, (16, 14, 26))

    # a very soft floor, so the door has something to stand on
    for y in range(150, SCREEN_H):
        t = (y - 150) / (SCREEN_H - 150)
        art.rect(0, y, SCREEN_W, 1, blend((24, 21, 36), (14, 12, 22), t))

    # the light spilling out of the gap, as a wedge on the floor
    for y in range(148, 214):
        t = (y - 148) / 66
        span = int(6 + t * 52)
        amount = (1 - t) ** 1.6
        for x in range(SCREEN_W // 2 - span, SCREEN_W // 2 + span):
            edge = abs(x - SCREEN_W // 2) / max(span, 1)
            strength = amount * (1 - edge * 0.75)
            if strength > BAYER8[y % 8, x % 8] * 0.9:
                art.dot(x, y, blend((24, 21, 36), (250, 226, 168),
                                    min(0.85, strength)))

    # the door itself
    dx, dy, dw, dh = SCREEN_W // 2 - 34, 62, 68, 92
    art.round_rect(dx - 4, dy - 4, dw + 8, dh + 8, 30, (40, 34, 54))
    art.round_rect(dx, dy, dw, dh, 26, (58, 50, 76))
    art.round_rect(dx + 3, dy + 3, 8, dh - 6, 4, (74, 64, 96))
    # the gap: a bright vertical sliver down the right-hand edge
    art.rect(dx + dw - 13, dy + 8, 9, dh - 8, (250, 226, 168))
    art.rect(dx + dw - 13, dy + 8, 3, dh - 8, (255, 248, 226))
    art.round_rect(dx + 16, dy + 20, dw - 34, 26, 3, (48, 41, 64))
    art.round_rect(dx + 16, dy + 54, dw - 34, 26, 3, (48, 41, 64))
    art.blob(dx + dw - 20, dy + dh // 2, 3, (226, 196, 140))

    draw_text_centered(art, "LIMINAL", 26, (246, 240, 226), scale=4, spacing=2,
                       shadow=(30, 26, 44))
    # Right at the bottom edge.  The engine puts its own command window in the
    # middle of the lower half and will not be moved, so anything written
    # there is written underneath "begin / return / leave".
    draw_text_centered(art, "A PLACE THAT WAS ALREADY HERE", 228,
                       (128, 120, 148), scale=1, spacing=1)
    return art


def game_over_screen() -> Canvas:
    """Not death — waking up.  There is nothing to lose in this game."""
    art = Canvas(SCREEN_W, SCREEN_H, (232, 228, 236))
    for y in range(SCREEN_H):
        t = y / (SCREEN_H - 1)
        art.rect(0, y, SCREEN_W, 1, blend((240, 238, 244), (206, 202, 216), t))
    art.ellipse(SCREEN_W / 2, 118, 92, 62, (250, 248, 252))
    draw_text_centered(art, "YOU WOKE UP", 108, (118, 112, 136), scale=3,
                       spacing=2)
    draw_text_centered(art, "THE ROOM KEPT GOING WITHOUT YOU", 150,
                       (168, 162, 184), scale=1)
    return art


# --- overlays ----------------------------------------------------------------
# Every overlay is a full-screen picture.  They are drawn opaque and faded at
# display time, so the same asset can be a hint or a shout.

def _screen() -> Canvas:
    return Canvas(SCREEN_W, SCREEN_H, TRANSPARENT)


def vignette(color: RGB = (10, 8, 16), strength: float = 1.0,
             power: float = 2.2) -> Canvas:
    """Darkened corners.  Used to make a world feel like it is being observed."""
    art = _screen()
    ys, xs = np.mgrid[0:SCREEN_H, 0:SCREEN_W]
    cx, cy = (SCREEN_W - 1) / 2, (SCREEN_H - 1) / 2
    d = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2) / math.sqrt(2)
    amount = np.clip(d, 0, 1) ** power * strength
    threshold = BAYER8[ys % 8, xs % 8]
    art.px[amount > threshold] = color
    art.px[amount * 0.55 > threshold] = color
    return art


def scanlines(color: RGB = (12, 14, 20), period: int = 3) -> Canvas:
    """CRT lines, for the worlds that are being transmitted rather than visited."""
    art = _screen()
    for y in range(0, SCREEN_H, period):
        art.rect(0, y, SCREEN_W, 1, color)
    return art


def dust(seed: int = 0, count: int = 150, color: RGB = (255, 252, 238)) -> Canvas:
    """Motes floating in light.  Sparse and hand-placed rather than noisy."""
    art = _screen()
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, SCREEN_W))
        y = int(rng.integers(0, SCREEN_H))
        art.dot(x, y, color)
        if rng.random() < 0.25:
            art.dot(x + 1, y, color)
    return art


def static_field(seed: int = 0, density: float = 0.55) -> Canvas:
    """Untuned broadcast."""
    art = _screen()
    rng = np.random.default_rng(seed)
    mask = rng.random((SCREEN_H, SCREEN_W)) < density
    values = rng.integers(90, 250, size=(SCREEN_H, SCREEN_W))
    grey = np.stack([values, values, np.clip(values + 8, 0, 255)], axis=-1)
    art.px[mask] = grey[mask].astype(np.uint8)
    for _ in range(4):
        y = int(rng.integers(0, SCREEN_H))
        art.rect(0, y, SCREEN_W, 2, (226, 232, 236))
    return art


def light_shaft(color: RGB = (255, 244, 206), tilt: float = 0.35,
                count: int = 3) -> Canvas:
    """Diagonal beams, as though something above has a window in it."""
    art = _screen()
    for index in range(count):
        origin = 40 + index * 96
        width = 30 + index * 6
        for y in range(SCREEN_H):
            x0 = int(origin + y * tilt)
            fade = (1 - y / SCREEN_H) ** 1.2
            for x in range(x0, x0 + width):
                if not 0 <= x < SCREEN_W:
                    continue
                edge = 1 - abs((x - x0) / width - 0.5) * 2
                strength = fade * edge * 0.9
                if strength > BAYER8[y % 8, x % 8]:
                    art.dot(x, y, color)
    return art


def haze(color: RGB = (255, 255, 255)) -> Canvas:
    """A flat wash, for worlds where the air itself is doing something."""
    art = _screen()
    art.px[:, :] = color
    return art


def grain(seed: int = 0, density: float = 0.10) -> Canvas:
    """Film grain: sparse, monochrome, and never animated fast."""
    art = _screen()
    rng = np.random.default_rng(seed)
    mask = rng.random((SCREEN_H, SCREEN_W)) < density
    art.px[mask] = (236, 232, 226)
    mask2 = rng.random((SCREEN_H, SCREEN_W)) < density * 0.6
    art.px[mask2] = (34, 32, 38)
    return art


def watching_eye(color: RGB = (232, 246, 244),
                 iris: RGB = (26, 34, 44)) -> Canvas:
    """One enormous eye, for the moments a world decides to look back."""
    art = _screen()
    cx, cy = SCREEN_W / 2, SCREEN_H / 2
    art.ellipse(cx, cy, 130, 62, color)
    art.ellipse(cx, cy, 124, 56, warmer(color, 0.3))
    art.blob(cx, cy, 46, iris)
    art.blob(cx, cy, 40, blend(iris, (60, 130, 150), 0.55))
    art.blob(cx, cy, 20, (10, 12, 18))
    art.blob(cx - 16, cy - 16, 9, (255, 255, 255))
    return art


def horizon_band(color: RGB, height: int = 70) -> Canvas:
    """A soft band across the middle of the screen, for false horizons."""
    art = _screen()
    top = SCREEN_H // 2 - height // 2
    for row in range(height):
        t = abs(row / height - 0.5) * 2
        if (1 - t) > BAYER4[row % 4, 0]:
            art.rect(0, top + row, SCREEN_W, 1, color)
    return art


def card(text: str, sub: str = "", *, ink: RGB = (240, 236, 228),
         back: RGB = (14, 12, 20)) -> Canvas:
    """A full-screen title card, for the handful of moments that earn one."""
    art = Canvas(SCREEN_W, SCREEN_H, back)
    draw_text_centered(art, text, SCREEN_H // 2 - 18, ink, scale=3, spacing=2)
    if sub:
        draw_text_centered(art, sub, SCREEN_H // 2 + 16, cooler(ink, 0.45),
                           scale=1)
    return art


OVERLAYS: dict[str, "Canvas"] = {}


def build_overlays() -> dict[str, Canvas]:
    """Every overlay picture the game can show, by filename."""
    return {
        "Vignette": vignette(strength=1.0),
        "VignetteSoft": vignette(color=(30, 24, 40), strength=0.75, power=3.0),
        "Scanline": scanlines(),
        "Dust": dust(seed=11),
        "DustB": dust(seed=29, count=110),
        "Static": static_field(seed=5),
        "StaticB": static_field(seed=17, density=0.7),
        "Shaft": light_shaft(),
        "Haze": haze(),
        "HazePink": haze((250, 224, 232)),
        "HazeGold": haze((252, 236, 196)),
        "Grain": grain(seed=3),
        "GrainB": grain(seed=23),
        "Eye": watching_eye(),
        "Horizon": horizon_band((250, 240, 214)),
        "White": haze((255, 255, 255)),
        "Black": haze((0, 0, 0)),
    }
