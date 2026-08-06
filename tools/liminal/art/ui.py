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

# The title's palette.  Deliberately much wider than anything in the game
# proper: every world lends it one colour, so the menu is the only screen in
# LIMINAL where all fourteen dreams are in the same picture at once.  They are
# never named and never explained — the player meets them again later and does
# not know why they are familiar.
TITLE_PALETTE = {
    "void":     (13, 11, 22),      # the nexus
    "void_lit": (30, 25, 46),
    "haze":     (46, 38, 66),
    "brick":    (198, 122, 150),   # pink
    "digit":    (176, 196, 190),   # numbers
    "block":    (226, 176, 92),    # blocks
    "step":     (150, 158, 196),   # stairs
    "dune":     (208, 190, 154),   # sand
    "leaf":     (108, 176, 104),   # the grove
    "stone":    (144, 140, 148),   # hands
    "square":   (214, 212, 218),   # checker
    "toy":      (232, 150, 168),   # toys
    "neon":     (128, 236, 220),   # scrawl
    "brolly":   (196, 106, 118),   # umbrellas
    "star":     (156, 190, 236),   # the shallows
    "lamp":     (250, 226, 168),   # the one warm light in the room
    "glass":    (176, 206, 226),
    "silver":   (232, 232, 240),
    "frame":    (86, 74, 108),
    "frame_lit": (128, 112, 156),
    "frame_dark": (44, 36, 60),
    "ink":      (246, 240, 226),
    "sub":      (150, 140, 178),
}


def _sky(art: Canvas) -> None:
    """The dark, dithered three ways so it is never flat and never noisy.

    Three matrices doing three jobs: an eight-by-eight ordered dither carries
    the long vertical fall from violet to black, a four-by-four breaks the
    band edges where the eye would otherwise find a step, and a two-by-two
    checker lifts the very top so the corners do not close up.  A gradient
    this long done with one matrix bands visibly at this bit depth.
    """
    P = TITLE_PALETTE
    ys, xs = np.mgrid[0:SCREEN_H, 0:SCREEN_W]
    # distance from the mirror, which is what everything here is lit by
    cx, cy = SCREEN_W / 2, 92.0
    d = np.sqrt(((xs - cx) / 190) ** 2 + ((ys - cy) / 150) ** 2)
    glow = np.clip(1.0 - d, 0, 1) ** 1.7

    coarse = BAYER8[ys % 8, xs % 8]
    fine = BAYER4[ys % 4, xs % 4]
    for y in range(SCREEN_H):
        for x in range(SCREEN_W):
            t = glow[y, x]
            if t > coarse[y, x] * 0.92:
                tone = P["haze"] if t > 0.62 else P["void_lit"]
            elif t > fine[y, x] * 0.55:
                tone = P["void_lit"]
            else:
                tone = P["void"]
            art.px[y, x] = tone
    # the very top, lifted with a two-pixel checker so the corners stay open
    for y in range(0, 34):
        for x in range(SCREEN_W):
            if (x + y) % 2 == 0 and (y % 3) == 0:
                art.dot(x, y, blend(P["void"], P["haze"], 0.5))


def _relics(art: Canvas) -> None:
    """One thing from every dream, standing in the dark around the mirror.

    None of them is drawn in full and none of them is lit — they are
    silhouettes at the edge of what the mirror is throwing, at the size they
    would be if they were a long way off.  The point is that a player who has
    finished the game recognises all fourteen and a player who has not sees
    furniture in a dark room.
    """
    P = TITLE_PALETTE

    def ghost(colour, amount=0.34):
        return blend(P["void_lit"], colour, amount)

    # far left to far right, ordered so nothing overlaps its neighbour
    art.rect(6, 96, 22, 58, ghost(P["brick"], 0.30))          # a brick wall
    for row in range(100, 152, 6):
        art.hline(row, 6, 27, ghost(P["brick"], 0.16))
    art.rect(34, 118, 3, 36, ghost(P["step"]))                 # a flight, edge on
    for step in range(5):
        art.rect(34, 148 - step * 7, 5 + step * 2, 3, ghost(P["step"], 0.26))
    art.ellipse(58, 150, 18, 6, ghost(P["dune"], 0.22))        # a dune
    art.rect(76, 108, 3, 46, ghost(P["leaf"], 0.30))           # a tree
    art.blob(77, 104, 13, ghost(P["leaf"], 0.26))
    art.blob(70, 110, 8, ghost(P["leaf"], 0.20))
    art.rect(96, 132, 14, 22, ghost(P["stone"], 0.24))         # a hand
    for finger in range(3):
        art.rect(98 + finger * 5, 118, 3, 16, ghost(P["stone"], 0.24))
    art.rect(208, 128, 16, 26, ghost(P["block"], 0.26))        # a block
    art.rect(212, 132, 8, 8, ghost(P["block"], 0.14))
    for sq in range(4):                                        # a checkerboard
        art.rect(230 + (sq % 2) * 9, 138 + (sq // 2) * 9, 9, 9,
                 ghost(P["square"], 0.20 if sq % 3 else 0.08))
    art.rect(258, 96, 3, 58, ghost(P["brolly"]))               # an umbrella
    for rib in range(-3, 4):
        art.line(259, 96, 259 + rib * 7, 106, ghost(P["brolly"], 0.28))
    art.rect(282, 116, 22, 38, ghost(P["toy"], 0.22))          # a toy
    art.blob(293, 112, 7, ghost(P["toy"], 0.16))
    for scrawl in range(3):                                    # a scrawl
        art.line(276 + scrawl * 6, 76, 290 + scrawl * 4, 92,
                 ghost(P["neon"], 0.30))
    for spark in ((20, 40), (52, 26), (88, 58), (240, 34), (272, 52),
                  (300, 76), (14, 70), (196, 22), (152, 16), (128, 34)):
        art.dot(spark[0], spark[1], ghost(P["star"], 0.55))    # the shallows
        art.dot(spark[0] + 1, spark[1], ghost(P["star"], 0.28))
    for digit in range(4):                                     # a number
        art.rect(120 + digit * 3, 24 + digit % 2 * 4, 2, 9,
                 ghost(P["digit"], 0.24))


def title_screen() -> Canvas:
    """A standing mirror in the dark, and everywhere else in the game around it.

    This was a door, and a door is the wrong object: every threshold in
    LIMINAL is a mirror, the room you wake up in has one, the nexus is a ring
    of them, and the four ways down out of the grove are four more.  A title
    screen showing a door was advertising a different game.
    """
    P = TITLE_PALETTE
    art = Canvas(SCREEN_W, SCREEN_H, P["void"])
    _sky(art)
    _relics(art)

    # The engine draws its own command window in the middle of the lower half
    # and will not be moved, so the mirror has to end above it.  Sitting at
    # fifty-eight the plinth came out directly underneath "begin", and the
    # menu looked like it was resting on the frame.
    mx, my, mw, mh = SCREEN_W // 2 - 30, 48, 60, 80

    # the pool of light the mirror throws, dithered rather than blended, so it
    # reads as light in a dark room rather than as a soft brush
    for y in range(my + mh - 6, SCREEN_H):
        t = (y - (my + mh - 6)) / max(1, SCREEN_H - my - mh + 6)
        span = int(14 + t * 96)
        for x in range(SCREEN_W // 2 - span, SCREEN_W // 2 + span):
            if not 0 <= x < SCREEN_W:
                continue
            edge = abs(x - SCREEN_W // 2) / max(span, 1)
            strength = ((1 - t) ** 1.5) * (1 - edge * edge)
            if strength > BAYER8[y % 8, x % 8]:
                art.dot(x, y, blend(P["void_lit"], P["lamp"],
                                    min(0.72, strength)))
            elif strength > BAYER4[y % 4, x % 4] * 1.35:
                art.dot(x, y, blend(P["void_lit"], P["lamp"], 0.16))

    # the frame: square-shouldered with a plinth, exactly as every mirror in
    # the game is built, so the title object and the game object are one object
    art.rect(mx - 5, my - 5, mw + 10, mh + 12, P["frame_dark"])
    art.rect(mx - 3, my - 3, mw + 6, mh + 8, P["frame"])
    art.rect(mx - 3, my - 3, mw + 6, 3, P["frame_lit"])
    art.rect(mx - 3, my - 3, 3, mh + 8, P["frame_lit"])
    art.rect(mx + mw, my - 3, 3, mh + 8, P["frame_dark"])
    art.rect(mx - 8, my + mh + 5, mw + 16, 6, P["frame"])       # the plinth
    art.rect(mx - 8, my + mh + 5, mw + 16, 2, P["frame_lit"])

    # the glass.  Lit from inside, and the light in it is *not* the light in
    # the room: it falls the other way, which is the whole idea of the game.
    for y in range(mh):
        t = y / (mh - 1)
        for x in range(mw):
            u = x / (mw - 1)
            depth = ((1 - t) ** 1.2) * (0.45 + 0.55 * (1 - abs(u - 0.42) * 1.6))
            if depth > BAYER8[(my + y) % 8, (mx + x) % 8] * 0.88:
                tone = blend(P["glass"], P["silver"], min(1.0, depth * 0.9))
            elif depth > BAYER4[(my + y) % 4, (mx + x) % 4] * 0.7:
                tone = blend(P["haze"], P["glass"], 0.55)
            else:
                tone = blend(P["frame_dark"], P["haze"], 0.6)
            art.dot(mx + x, my + y, tone)

    # what is standing in it.  Not the player: a doorway, a long way back,
    # with somebody in it who has not turned round.
    art.rect(mx + 20, my + 26, 20, 62, blend(P["haze"], P["void"], 0.5))
    art.rect(mx + 22, my + 30, 16, 58, blend(P["void_lit"], P["lamp"], 0.30))
    art.rect(mx + 27, my + 44, 7, 34, P["frame_dark"])          # the figure
    art.blob(mx + 30, my + 40, 4, P["frame_dark"])
    art.rect(mx + 27, my + 44, 2, 34, blend(P["frame_dark"], P["lamp"], 0.22))
    # a checkerboard sheen across the glass, two values, on the diagonal
    for y in range(mh):
        for x in range(mw):
            if (x + y * 2) % 23 < 2 and (x + y) % 2 == 0:
                art.dot(mx + x, my + y,
                        blend(art.px[my + y, mx + x], P["silver"], 0.34))

    draw_text_centered(art, "LIMINAL", 12, P["ink"], scale=4, spacing=2,
                       shadow=(24, 20, 38))
    # Right at the bottom edge.  The engine puts its own command window in the
    # middle of the lower half and will not be moved, so anything written
    # there is written underneath "begin / return / leave".
    draw_text_centered(art, "WALK TO THE OTHER SIDE OF THE LOOKING GLASS", 228,
                       P["sub"], scale=1, spacing=1)
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


def shudder(vertical: bool, *, color: RGB = (226, 232, 244),
            span: int = 96, seed: int = 41) -> Canvas:
    """A band of broken displacement lines, for one edge of the screen.

    The grove's telephone rings from a direction, and the side it rings from
    is supposed to *move*.  Camera shake is not available — it is banned in
    this project and it would be the wrong tool anyway, because a shake moves
    the whole picture and the whole picture is not what is ringing.

    So this is a small picture, positioned over one edge and jittered a few
    pixels while the ring is sounding.  It is mostly transparent: a scatter of
    short bright runs that read as nothing at all standing still, and read as
    that side of the screen quivering the moment they move.  The band fades
    out at both ends so it can be used on either the left or the right edge
    without a second asset.
    """
    art = Canvas(span if vertical else SCREEN_W,
                 SCREEN_H if vertical else span, TRANSPARENT)
    rng = np.random.default_rng(seed)
    across = art.w if vertical else art.h
    along = art.h if vertical else art.w
    for step in range(0, along, 3):
        # how present the band is here: strongest in the middle of its own
        # length, gone at both ends
        for _ in range(2):
            offset = int(rng.integers(0, across))
            reach = 1 - abs(offset / max(1, across - 1) - 0.5) * 2
            if reach < BAYER4[step % 4, offset % 4]:
                continue
            run = int(rng.integers(3, 9))
            if vertical:
                art.rect(max(0, offset - run // 2), step, run, 1, color)
            else:
                art.rect(step, max(0, offset - run // 2), 1, run, color)
    return art


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
        "ShudderV": shudder(True),
        "ShudderH": shudder(False),
    }
