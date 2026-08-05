"""The dream diary: art for the custom picture-driven menu.

RPG Maker's built-in menu is drawn by the engine and cannot be animated, so
the diary is built entirely out of pictures instead.  Each layer is a separate
image the interpreter can move, scale, spin, tint and fade independently,
which is what lets the menu assemble itself in stages rather than appear.

Layer order, back to front — this is also the order they animate in:

======  ======================================================
veil    a dimming wash over the world behind
panel   the diary page itself, which scales up with an overshoot
frame   the border, sliding down and settling
glint   a light streak that travels across the border
icons   the effects, popping in one at a time
cursor  last, with a ghost trailing one step behind it
dust    motes drifting over everything
======  ======================================================
"""

from __future__ import annotations

import math

import numpy as np

from .canvas import (BAYER4, BAYER8, Canvas, RGB, TRANSPARENT, blend, cooler,
                     outline_in, warmer)
from .glyphs import draw_text, draw_text_centered, text_width

SCREEN_W, SCREEN_H = 320, 240

PANEL_W, PANEL_H = 232, 168
ICON = 32
CURSOR = 40

# The diary's own colours.  Deliberately warmer and softer than any world, so
# opening it feels like stepping out of the dream for a moment.
PAPER = (238, 228, 212)
PAPER_DARK = (214, 200, 182)
INK = (78, 66, 74)
INK_SOFT = (140, 126, 132)
BORDER = (122, 100, 118)
BORDER_LIGHT = (176, 152, 168)
GOLD = (226, 190, 122)


def veil() -> Canvas:
    """A soft dark wash, shown at low opacity to push the world back."""
    art = Canvas(SCREEN_W, SCREEN_H, (18, 14, 26))
    return art


# --- garnishes ---------------------------------------------------------------
# The engine can rotate and wave a picture continuously, and it does that on its
# own clock rather than the interpreter's — so these keep moving while the menu
# sits blocked waiting for a keypress.  That is the whole trick: everything
# below is drawn once and animated by the engine forever.

HALO = (150, 122, 168)
HALO_LIGHT = (214, 184, 216)


def halo() -> Canvas:
    """A slow-turning bloom behind the page.  Soft, petalled, never sharp."""
    size = 288
    art = Canvas(size, size, TRANSPARENT)
    cx = cy = size / 2
    for petal in range(9):
        angle = petal * math.tau / 9
        for step in range(30):
            t = step / 29
            radius = 26 + t * 108
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            # petals taper and pale as they reach outward
            art.blob(x, y, 20 * (1 - t) + 4,
                     blend(HALO, HALO_LIGHT, t * 0.8))
    art.dither(TRANSPARENT, 0.34, BAYER8)
    art.blob(cx, cy, 34, blend(HALO_LIGHT, PAPER, 0.4))
    return art


def rings() -> Canvas:
    """Broken concentric rings, turning the other way from the halo.

    Counter-rotation is what stops two spinning layers from reading as one
    spinning layer.
    """
    size = 256
    art = Canvas(size, size, TRANSPARENT)
    cx = cy = size / 2
    for index, radius in enumerate((58, 82, 104, 122)):
        gaps = 3 + index
        color = blend(BORDER_LIGHT, PAPER, index / 5)
        for step in range(int(radius * 7)):
            angle = step / (radius * 7) * math.tau
            # leave a gap in each ring, rotated per ring
            if (angle + index * 0.7) % (math.tau / gaps) < 0.34:
                continue
            art.dot(int(cx + math.cos(angle) * radius),
                    int(cy + math.sin(angle) * radius), color)
    return art


def motes() -> Canvas:
    """Drifting specks, shown with the engine's wave effect so they swim."""
    art = Canvas(SCREEN_W, SCREEN_H, TRANSPARENT)
    rng = np.random.default_rng(4)
    for _ in range(110):
        x = int(rng.integers(4, SCREEN_W - 4))
        y = int(rng.integers(4, SCREEN_H - 4))
        size = rng.random()
        if size > 0.86:
            art.blob(x, y, 1.8, warmer(PAPER, 0.55))
        elif size > 0.5:
            art.dot(x, y, warmer(PAPER, 0.4))
            art.dot(x + 1, y, blend(PAPER, HALO, 0.4))
        else:
            art.dot(x, y, blend(PAPER, HALO_LIGHT, 0.5))
    return art


def bloom() -> Canvas:
    """A soft light that sits under whichever effect the cursor is over."""
    art = Canvas(CURSOR + 24, CURSOR + 24, TRANSPARENT)
    cx = cy = art.w / 2
    for radius, amount in ((30, 0.14), (23, 0.26), (16, 0.40), (10, 0.58)):
        art.blob(cx, cy, radius, blend(GOLD, PAPER, 1 - amount))
    art.dither(TRANSPARENT, 0.42, BAYER8)
    return art


def panel() -> Canvas:
    """The diary page.  Drawn at full size and scaled by the interpreter."""
    art = Canvas(PANEL_W, PANEL_H, TRANSPARENT)
    art.round_rect(0, 0, PANEL_W, PANEL_H, 10, BORDER)
    art.round_rect(3, 3, PANEL_W - 6, PANEL_H - 6, 8, PAPER)
    # a paper tone that is not flat, but is also not noisy
    art.dither(PAPER_DARK, 0.16, BAYER8)
    # the spine, so it reads as a book rather than a box
    art.rect(PANEL_W // 2 - 1, 6, 2, PANEL_H - 12, PAPER_DARK)
    art.rect(PANEL_W // 2 + 1, 6, 1, PANEL_H - 12, blend(PAPER, INK, 0.10))
    # faint ruled lines, as though somebody meant to write here
    for y in range(24, PANEL_H - 12, 20):
        art.rect(14, y, PANEL_W - 28, 1, blend(PAPER, INK_SOFT, 0.18))
    return art


# The one hard edge in the whole menu.  Everything else is soft and warm, so
# the border has to be the opposite of that or the page has no shape: near
# black on the outside, near white on the inside, three pixels apart.
EDGE_DARK = (28, 20, 36)
EDGE_LIGHT = (250, 244, 232)


def frame() -> Canvas:
    """The decorative border, animated in separately from the page.

    Deliberately the highest-contrast thing on screen.  A dreamlike menu that
    is soft all the way to its edges reads as a smudge; the eye needs one crisp
    line to tell it where the page stops.
    """
    art = Canvas(PANEL_W + 20, PANEL_H + 20, TRANSPARENT)
    w, h = art.w, art.h
    art.round_rect(0, 0, w, h, 13, EDGE_DARK)
    art.round_rect(2, 2, w - 4, h - 4, 12, BORDER)
    art.round_rect(5, 5, w - 10, h - 10, 10, EDGE_LIGHT)
    art.round_rect(7, 7, w - 14, h - 14, 9, BORDER)
    art.round_rect(9, 9, w - 18, h - 18, 8, EDGE_DARK)
    art.round_rect(11, 11, w - 22, h - 22, 7, TRANSPARENT)
    # corner studs: the only ornament, four of them
    for cx, cy in ((10, 10), (w - 11, 10), (10, h - 11), (w - 11, h - 11)):
        art.blob(cx, cy, 5, EDGE_DARK)
        art.blob(cx, cy, 3.5, GOLD)
        art.blob(cx - 1, cy - 1, 1.4, warmer(GOLD, 0.6))
    return art


def glint() -> Canvas:
    """A diagonal light streak that travels across the frame and leaves."""
    art = Canvas(64, PANEL_H + 16, TRANSPARENT)
    for y in range(art.h):
        x = int(y * 0.35)
        for offset in range(14):
            strength = 1 - abs(offset - 7) / 7
            if strength > BAYER4[y % 4, offset % 4]:
                art.dot(x + offset, y, warmer(GOLD, 0.55))
    return art


def cursor(color: RGB = GOLD) -> Canvas:
    """The selection box.  Corners only — a full box would cover the icon."""
    art = Canvas(CURSOR, CURSOR, TRANSPARENT)
    arm = 11
    for cx, cy, sx, sy in ((2, 2, 1, 1), (CURSOR - 3, 2, -1, 1),
                           (2, CURSOR - 3, 1, -1), (CURSOR - 3, CURSOR - 3, -1, -1)):
        for i in range(arm):
            art.dot(cx + sx * i, cy, color)
            art.dot(cx, cy + sy * i, color)
            art.dot(cx + sx * i, cy + sy, warmer(color, 0.4))
            art.dot(cx + sx, cy + sy * i, warmer(color, 0.4))
    return art


def cursor_ghost() -> Canvas:
    """A paler copy that lags one step behind, then fades."""
    art = cursor(blend(GOLD, PAPER, 0.55))
    return art


def dust_layer(seed: int = 0, count: int = 70) -> Canvas:
    """Motes over the whole menu, so the background is never frozen."""
    art = Canvas(SCREEN_W, SCREEN_H, TRANSPARENT)
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, SCREEN_W))
        y = int(rng.integers(0, SCREEN_H))
        art.dot(x, y, warmer(PAPER, 0.5))
        if rng.random() < 0.3:
            art.dot(x, y + 1, PAPER_DARK)
    return art


def title_plate(text: str = "THINGS I FOUND") -> Canvas:
    art = Canvas(PANEL_W - 40, 22, TRANSPARENT)
    art.round_rect(0, 0, art.w, art.h, 6, BORDER)
    art.round_rect(2, 2, art.w - 4, art.h - 4, 5, PAPER)
    draw_text_centered(art, text, 8, INK, scale=1, spacing=1)
    return art


# --- effect icons ------------------------------------------------------------
# One 32x32 icon per effect, in the same flat, rounded, few-colour style as
# everything else.  Each exaggerates its defining feature until it reads as an
# icon rather than an illustration.

def _icon() -> Canvas:
    return Canvas(ICON, ICON, TRANSPARENT)


def _plate(art: Canvas, tint: RGB) -> None:
    art.round_rect(1, 1, ICON - 2, ICON - 2, 7, blend(PAPER, tint, 0.35))
    art.round_rect(1, 1, ICON - 2, 4, 7, blend(PAPER, tint, 0.12))


def icon_lantern() -> Canvas:
    art = _icon()
    _plate(art, (246, 214, 150))
    art.rect(15, 5, 2, 4, (120, 100, 80))
    art.round_rect(9, 9, 14, 15, 5, (238, 200, 120))
    art.round_rect(11, 12, 10, 10, 4, (255, 250, 220))
    art.blob(16, 17, 3, (255, 255, 255))
    art.round_rect(8, 23, 16, 4, 2, (120, 100, 80))
    return outline_in(art, darken=0.6)


def icon_quiet() -> Canvas:
    art = _icon()
    _plate(art, (206, 214, 226))
    art.round_rect(11, 6, 11, 11, 5, (236, 240, 246))
    art.round_rect(9, 16, 15, 12, 5, (236, 240, 246))
    art.dither(TRANSPARENT, 0.35, BAYER4)
    return outline_in(art, darken=0.72)


def icon_tall() -> Canvas:
    art = _icon()
    _plate(art, (196, 206, 236))
    art.round_rect(13, 3, 7, 7, 3, (240, 220, 200))
    art.round_rect(12, 10, 9, 15, 3, (128, 148, 196))
    art.rect(13, 25, 3, 4, (78, 74, 96))
    art.rect(18, 25, 3, 4, (78, 74, 96))
    art.rect(6, 4, 2, 24, GOLD)
    art.rect(4, 4, 6, 2, GOLD)
    art.rect(4, 26, 6, 2, GOLD)
    return outline_in(art, darken=0.6)


def icon_hat() -> Canvas:
    art = _icon()
    _plate(art, (238, 190, 160))
    for row in range(15):
        span = int(row * 0.75) + 1
        art.hline(6 + row, 16 - span, 16 + span, (226, 156, 118))
    art.ellipse(16, 22, 12, 3.5, (198, 128, 96))
    art.blob(16, 5, 2, warmer((226, 156, 118), 0.6))
    return outline_in(art, darken=0.6)


def icon_ears() -> Canvas:
    art = _icon()
    _plate(art, (244, 226, 170))
    art.round_rect(10, 14, 13, 12, 5, (238, 206, 126))
    for sign in (-1, 1):
        art.round_rect(16 + sign * 5 - 2, 3, 4, 13, 2, (238, 206, 126))
        art.round_rect(16 + sign * 5 - 1, 5, 2, 9, 1, warmer((238, 206, 126), 0.4))
    art.round_rect(13, 19, 2, 2, 1, (96, 78, 52))
    art.round_rect(18, 19, 2, 2, 1, (96, 78, 52))
    return outline_in(art, darken=0.6)


def icon_coat() -> Canvas:
    art = _icon()
    _plate(art, (170, 164, 200))
    art.round_rect(11, 5, 10, 7, 3, (240, 220, 200))
    art.round_rect(8, 11, 16, 17, 4, (92, 84, 118))
    art.rect(15, 12, 2, 16, cooler((92, 84, 118), 0.35))
    art.round_rect(8, 11, 16, 3, 3, warmer((92, 84, 118), 0.25))
    return outline_in(art, darken=0.6)


def icon_pole() -> Canvas:
    art = _icon()
    _plate(art, (196, 214, 200))
    art.rect(15, 3, 3, 26, (160, 132, 96))
    art.rect(15, 3, 1, 26, warmer((160, 132, 96), 0.3))
    art.round_rect(12, 2, 9, 4, 2, (206, 180, 140))
    art.round_rect(12, 26, 9, 4, 2, (206, 180, 140))
    return outline_in(art, darken=0.6)


def icon_eye() -> Canvas:
    art = _icon()
    _plate(art, (176, 226, 220))
    art.ellipse(16, 16, 13, 8, (246, 250, 250))
    art.blob(16, 16, 6, (52, 96, 116))
    art.blob(16, 16, 3, (18, 24, 34))
    art.blob(13.5, 13.5, 1.8, (255, 255, 255))
    return outline_in(art, darken=0.55)


def icon_bell() -> Canvas:
    art = _icon()
    _plate(art, (238, 214, 160))
    art.rect(15, 4, 2, 3, (150, 124, 80))
    for row in range(14):
        span = int(4 + row * 0.62)
        art.hline(7 + row, 16 - span, 16 + span, (226, 190, 122))
    art.round_rect(6, 21, 21, 4, 2, (226, 190, 122))
    art.rect(9, 9, 2, 10, warmer((226, 190, 122), 0.45))
    art.blob(16, 26, 2.4, (150, 124, 80))
    return outline_in(art, darken=0.58)


def icon_key() -> Canvas:
    art = _icon()
    _plate(art, (214, 206, 216))
    art.ellipse(11, 11, 6, 6, (206, 206, 214), filled=False)
    art.ellipse(11, 11, 5, 5, (206, 206, 214), filled=False)
    art.rect(13, 14, 3, 14, (206, 206, 214))
    art.rect(16, 21, 5, 3, (206, 206, 214))
    art.rect(16, 26, 4, 3, (206, 206, 214))
    return outline_in(art, darken=0.55)


def icon_stone() -> Canvas:
    art = _icon()
    _plate(art, (188, 190, 186))
    art.round_rect(6, 12, 20, 15, 6, (168, 168, 164))
    art.round_rect(8, 13, 14, 5, 4, (206, 206, 200))
    art.round_rect(9, 20, 9, 4, 2, (132, 132, 132))
    return outline_in(art, darken=0.6)


def icon_static() -> Canvas:
    art = _icon()
    _plate(art, (188, 196, 204))
    art.round_rect(7, 8, 19, 16, 3, (48, 52, 58))
    rng = np.random.default_rng(4)
    for _ in range(90):
        x = int(rng.integers(9, 24))
        y = int(rng.integers(10, 22))
        v = int(rng.integers(90, 240))
        art.dot(x, y, (v, v, min(255, v + 8)))
    art.rect(9, 25, 4, 3, (96, 100, 108))
    art.rect(20, 25, 4, 3, (96, 100, 108))
    return outline_in(art, darken=0.6)


# The order here is the order they sit in the diary grid, and the order the
# switches and sprite variants are numbered in the database.
EFFECT_ICONS: dict[str, "Canvas"] = {}

EFFECTS: list[tuple[str, str, str]] = [
    # (id, display name, the line shown when you first pick it up)
    ("lantern", "lantern", "it was already lit."),
    ("quiet", "quiet", "nothing has to notice you."),
    ("tall", "tall", "the ceiling was never the limit."),
    ("hat", "hat", "somebody left it out for you."),
    ("ears", "ears", "you can hear the rooms next door."),
    ("coat", "coat", "it is exactly your size."),
    ("pole", "pole", "long enough to reach."),
    ("eye", "eye", "some things were waiting to be looked at."),
    ("bell", "bell", "something answers, eventually."),
    ("key", "key", "there was never only one door."),
    ("stone", "stone", "heavy enough to fall through."),
    ("static", "static", "you stop being a picture of yourself."),
]

_ICON_BUILDERS = {
    "lantern": icon_lantern, "quiet": icon_quiet, "tall": icon_tall,
    "hat": icon_hat, "ears": icon_ears, "coat": icon_coat, "pole": icon_pole,
    "eye": icon_eye, "bell": icon_bell, "key": icon_key, "stone": icon_stone,
    "static": icon_static,
}


def build_menu_art() -> dict[str, Canvas]:
    """Every picture the diary needs, by filename."""
    out: dict[str, Canvas] = {
        "MenuVeil": veil(),
        "MenuHalo": halo(),
        "MenuRings": rings(),
        "MenuMotes": motes(),
        "MenuBloom": bloom(),
        "MenuPanel": panel(),
        "MenuFrame": frame(),
        "MenuGlint": glint(),
        "MenuCursor": cursor(),
        "MenuGhost": cursor_ghost(),
        "MenuDust": dust_layer(seed=7),
        "MenuDustB": dust_layer(seed=19, count=50),
        "MenuTitle": title_plate(),
    }
    for index, (key, _, _) in enumerate(EFFECTS, start=1):
        out[f"Icon{index:02d}"] = _ICON_BUILDERS[key]()
    # A blank slot, for effects not found yet: the grid always shows twelve
    # spaces, so the player can see how much they are missing.
    blank = _icon()
    _plate(blank, (200, 194, 190))
    blank.round_rect(12, 12, 8, 8, 3, blend(PAPER, INK_SOFT, 0.30))
    out["IconBlank"] = outline_in(blank, darken=0.7)
    return out


# Where each icon sits on screen when the grid is laid out four across.
def icon_position(index: int) -> tuple[int, int]:
    """Screen centre coordinates for grid slot ``index`` (0..11)."""
    col, row = index % 4, index // 4
    x = SCREEN_W // 2 - 3 * 24 + col * 48
    y = SCREEN_H // 2 - 34 + row * 44
    return x, y
