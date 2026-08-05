"""Character sheets.

An RPG Maker 2000 charset is 288x256: four columns by two rows of character
blocks, each block 72x128 — three animation frames across (left step, idle,
right step) by four facings down (up, right, down, left, in that order).

Everyone here is drawn to the same rules: a head slightly too big, rounded
forms, three to six colours, an outline in a darker version of the local
colour rather than black, and exactly one memorable feature per character.
Nothing is grotesque.  The strangeness is meant to be quiet — a mailbox with
small legs, an umbrella that politely watches you — not frightening.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .canvas import (Canvas, RGB, TRANSPARENT, blend, cooler, outline_in,
                     shade_of, warmer)

CELL_W, CELL_H = 24, 32
SHEET_W, SHEET_H = 288, 256
FRAMES = 3
UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3

GROUND = 30          # the y coordinate the feet stand on


# --- humanoids ---------------------------------------------------------------

@dataclass
class Body:
    """A dream-person.

    ``feature`` is the one thing you will remember about them, and every
    character is required to have exactly one.
    """
    skin: RGB
    hair: RGB
    shirt: RGB
    trousers: RGB
    shoe: RGB | None = None
    eye: RGB = (46, 40, 54)
    head_w: int = 13
    head_h: int = 12
    body_w: int = 11
    faceless: bool = False
    translucent: bool = False
    glow: RGB | None = None
    tall: int = 0
    feature: str = ""            # hat / wide_hat / cone_hat / scarf / coat / ears / antenna
    feature_color: RGB = (220, 210, 200)
    carry: str = ""              # block / can / ring / lantern / pole / tape


# RPG Maker plays charset frames in the order 0, 1, 2, 1, so a bob of
# (-1, 0, -1) gives a two-beat bounce per cycle rather than a single hitch.
BOB = (-1, 0, -1)


def _legs(cell: Canvas, body: Body, facing: int, frame: int, leg_top: int,
          center: int | None = None) -> None:
    """Legs from the hip down to the floor.

    ``leg_top`` is the hip, which rides the bounce with the torso; the feet
    stay planted at :data:`GROUND`, so the legs stretch and compress instead of
    detaching from the body.

    In profile the body is only seven pixels wide, so the legs cannot swing
    sideways as a whole — doing that walked the near leg clean off the torso
    and left it hanging in the air beside the figure.  Both legs stay hung
    from the same hip and only the shin and foot swing, which is also what
    legs do.
    """
    trousers = body.trousers
    shoe = body.shoe or cooler(body.trousers, 0.30)
    cx = CELL_W // 2 if center is None else center
    leg_h = GROUND - leg_top
    if facing in (LEFT, RIGHT):
        sign = 1 if facing == RIGHT else -1
        swing = (-2, 0, 2)[frame] * sign
        hip_x = cx - 2
        thigh_h = max(3, leg_h - 3)
        knee = leg_top + thigh_h - 1
        shin_h = max(2, GROUND - knee - 2)
        for offset, leg, sole in ((-swing, cooler(trousers, 0.22),
                                   cooler(shoe, 0.2)),
                                  (swing, trousers, shoe)):
            cell.round_rect(hip_x, leg_top, 4, thigh_h, 1, leg)
            cell.round_rect(hip_x + offset, knee, 4, shin_h, 1, leg)
            cell.round_rect(hip_x + offset - 1, GROUND - 3, 6, 3, 1, sole)
    else:
        # Front and back: one leg swings forward and lifts, the other plants.
        lift_l = 2 if frame == 0 else 0
        lift_r = 2 if frame == 2 else 0
        cell.round_rect(cx - 5, leg_top, 4, leg_h - lift_l, 1, trousers)
        cell.round_rect(cx + 1, leg_top, 4, leg_h - lift_r, 1, trousers)
        cell.round_rect(cx - 6, GROUND - 3 - lift_l, 5, 3, 1, shoe)
        cell.round_rect(cx + 1, GROUND - 3 - lift_r, 5, 3, 1, shoe)


def _carried(cell: Canvas, body: Body, facing: int, frame: int,
             torso_top: int) -> None:
    """Draw whatever this person is holding, on the side they are facing.

    Everything below is drawn as if the figure were facing right or forward;
    a left-facing figure gets the same drawing mirrored.  Without this a
    character walking left carried their lantern out behind them and the
    measurer's tape ran off the back of their own head.
    """
    if facing == LEFT:
        held = Canvas(CELL_W, CELL_H, TRANSPARENT)
        _carried(held, body, RIGHT, frame, torso_top)
        cell.paste(held.flip_h(), 0, 0, mask=TRANSPARENT)
        return
    cx = CELL_W // 2
    bob = (0, -1, 0)[frame]
    kind, color = body.carry, body.feature_color
    # Everything is held at hand height, out to the side, and small enough to
    # leave the person visible.  These used to be drawn from the top of the
    # torso *upwards*, which put them squarely over the character's head — the
    # sprite carrying a block was a block with feet.
    hand = torso_top + 5 + bob
    out = cx + 3
    if kind == "block":
        cell.round_rect(out, hand - 5, 10, 10, 2, color)
        cell.round_rect(out, hand - 5, 10, 3, 2, warmer(color, 0.30))
        cell.blob(out + 5, hand, 2, warmer(color, 0.55))
    elif kind == "can":
        cell.round_rect(out, hand - 3, 8, 7, 2, color)
        cell.rect(out + 7, hand - 4, 4, 2, color)
        cell.rect(out + 1, hand - 5, 4, 2, cooler(color, 0.25))
    elif kind == "ring":
        cell.ellipse(out + 4, hand, 5, 5, color, filled=False)
        cell.ellipse(out + 4, hand, 4, 4, color, filled=False)
    elif kind == "lantern":
        cell.rect(out + 3, hand - 5, 1, 4, cooler(color, 0.4))
        cell.round_rect(out, hand - 1, 7, 7, 2, color)
        cell.blob(out + 3, hand + 2, 2, (255, 252, 226))
    elif kind == "pole":
        # the one thing allowed to be enormous: it runs off the top of the cell
        cell.rect(out + 2, 1 + bob, 2, GROUND - 3, color)
    elif kind == "tape":
        # a tape measure whose tape has gone much too far — it leaves the cell,
        # but at hand height, not across its owner's face
        cell.round_rect(out, hand - 3, 7, 6, 2, color)
        cell.rect(out + 7, hand - 1, CELL_W - out - 7, 2, warmer(color, 0.4))


def _feature(cell: Canvas, body: Body, facing: int, head_x: int, head_top: int,
             hw: int, hh: int) -> None:
    cx = CELL_W // 2
    color = body.feature_color
    kind = body.feature
    if kind == "hat":
        cell.ellipse(cx, head_top + 1, hw * 0.62, 4.5, color)
        cell.round_rect(head_x + 1, head_top - 4, hw - 2, 6, 3, color)
    elif kind == "wide_hat":
        cell.ellipse(cx, head_top + 2, 11.5, 4, color)
        cell.ellipse(cx, head_top - 1, 6, 4.5, warmer(color, 0.2))
    elif kind == "cone_hat":
        top = max(0, head_top - 8)
        for row in range(head_top + 2 - top):
            span = int(row * 0.68) + 1
            cell.hline(top + row, cx - span, cx + span, color)
        cell.ellipse(cx, head_top + 1, hw * 0.70, 3, warmer(color, 0.25))
        cell.blob(cx, top, 1.6, warmer(color, 0.55))
    elif kind == "tall_hat":
        cell.round_rect(cx - 5, max(0, head_top - 9), 11,
                        head_top + 1 - max(0, head_top - 9), 2, color)
        cell.ellipse(cx, head_top + 1, hw * 0.66, 3, cooler(color, 0.15))
    elif kind == "scarf":
        cell.round_rect(head_x, head_top + hh - 2, hw, 4, 2, color)
        tail = 1 if facing != UP else -1
        cell.round_rect(cx + 3 * tail, head_top + hh + 1, 4, 11, 2, color)
    elif kind == "coat":
        pass  # handled in the torso
    elif kind == "ears":
        # impossibly long ears, which is the whole personality
        top = max(0, head_top - 9)
        for sign in (-1, 1):
            cell.round_rect(cx + sign * 4 - 2, top, 4, head_top + 2 - top, 2,
                            color)
            cell.round_rect(cx + sign * 4 - 1, top + 2, 2,
                            max(1, head_top - top - 1), 1, warmer(color, 0.35))
    elif kind == "antenna":
        cell.rect(cx, head_top - 7, 1, 8, cooler(color, 0.3))
        cell.blob(cx, head_top - 8, 2.5, color)


def draw_figure(body: Body, facing: int, frame: int) -> Canvas:
    """Draw one 24x32 humanoid cell, built upward from the feet."""
    cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
    cx = CELL_W // 2
    side = facing in (LEFT, RIGHT)

    if body.glow is not None:
        for radius, amount in ((10, 0.12), (7.5, 0.26), (5, 0.42)):
            halo = Canvas(CELL_W, CELL_H, TRANSPARENT)
            halo.blob(cx - 0.5, max(radius, GROUND - 14 - body.tall), radius,
                      blend(body.glow, (255, 255, 255), amount))
            cell.paste(halo, 0, 0, mask=TRANSPARENT)

    # The hip rides the bounce and the legs follow it down to the floor, so
    # the torso and the legs can never come apart.
    bob = BOB[frame]
    hip = GROUND - 7 + bob
    # Profiles lean a pixel the way they are going; the hips have to lean with
    # them or the legs hang off the front of the body.
    lean = 0 if not side else (1 if facing == RIGHT else -1)
    _legs(cell, body, facing, frame, hip, cx + lean)

    # A cell is only 32 pixels tall, so a stretched figure buys its height by
    # shrinking its head and then by giving up whatever is still over budget.
    # Without this the tall characters walk around with no head at all.
    hh = max(8, body.head_h - min(4, body.tall // 2))
    torso_h = min(9 + body.tall, hip - hh + 1)
    torso_top = hip - torso_h
    # In profile the body is narrower and the head loses its cheeks, which is
    # most of what separates a side view from a front view at this size.
    hw = body.head_w if not side else body.head_w - 4
    head_top = torso_top - hh + 1
    head_x = cx - hw // 2 + lean

    # torso: a rounded box; a coat simply makes it reach the floor
    bw = body.body_w if not side else max(7, body.body_w - 4)
    torso_x = cx - bw // 2 + lean
    if body.feature == "coat":
        cell.round_rect(torso_x - 1, torso_top, bw + 2, GROUND - torso_top - 1,
                        4, body.shirt)
        cell.round_rect(torso_x - 1, torso_top, bw + 2, 4, 4,
                        warmer(body.shirt, 0.20))
    else:
        # two pixels of overlap into the hips, so the outline pass can never
        # find a seam to draw a dark band into
        cell.round_rect(torso_x, torso_top, bw, torso_h + 2, 3, body.shirt)
        cell.round_rect(torso_x, torso_top, bw, 4, 3, warmer(body.shirt, 0.18))

    # arms: in profile only the near one shows, and it swings hard
    arm = cooler(body.shirt, 0.20)
    arm_top = torso_top + 3
    arm_h = torso_h - 4
    if side:
        swing = (-2, 0, 2)[frame]
        ax = cx + lean + (1 if facing == RIGHT else -4)
        cell.round_rect(ax, arm_top + swing, 3, arm_h, 1, arm)
        cell.round_rect(ax, arm_top + swing + arm_h - 2, 3, 2, 1, body.skin)
    else:
        # front and back: both arms, swinging in opposition
        swing = (2, 0, -2)[frame]
        cell.round_rect(torso_x - 2, arm_top + swing, 3, arm_h, 1, arm)
        cell.round_rect(torso_x - 2, arm_top + swing + arm_h - 2, 3, 2, 1,
                        body.skin)
        cell.round_rect(torso_x + bw - 1, arm_top - swing, 3, arm_h, 1, arm)
        cell.round_rect(torso_x + bw - 1, arm_top - swing + arm_h - 2, 3, 2, 1,
                        body.skin)

    # head: a rounded box, deliberately a size too large
    cell.round_rect(head_x, head_top, hw, hh, 4, body.skin)
    if facing == UP:
        # from behind: all hair, and a collar so the back reads as a back
        cell.round_rect(head_x, head_top, hw, hh - 2, 4, body.hair)
        cell.round_rect(head_x + 2, head_top + hh - 3, hw - 4, 3, 1,
                        cooler(body.hair, 0.25))
        cell.round_rect(torso_x + 1, torso_top, bw - 2, 2, 1,
                        cooler(body.shirt, 0.30))
    else:
        cell.round_rect(head_x, head_top, hw, 5, 4, body.hair)
        if side:
            # Hair sweeps to the back of the head — the side *away* from the
            # way they are walking.  This was the wrong way round, so the hair
            # covered the face and the eye ended up jammed against it instead
            # of sitting forward where an eye goes.
            back = head_x if facing == RIGHT else head_x + hw - 3
            cell.round_rect(back, head_top, 3, hh - 3, 1, body.hair)
            nose_x = head_x + hw if facing == RIGHT else head_x - 1
            cell.rect(nose_x, head_top + 7, 1, 2, body.skin)
            chin = head_x + hw - 1 if facing == RIGHT else head_x
            cell.rect(chin, head_top + hh - 2, 1, 1, cooler(body.skin, 0.2))
    cell.round_rect(head_x + 2, head_top, hw - 4, 2, 1, warmer(body.hair, 0.22))

    if not body.faceless and facing != UP:
        eye_y = head_top + 7
        if facing == DOWN:
            cell.round_rect(cx - 4, eye_y, 2, 3, 1, body.eye)
            cell.round_rect(cx + 2, eye_y, 2, 3, 1, body.eye)
        elif facing == RIGHT:
            # forward in the face, not centred in it: a profile's eye sits
            # near the front of the head, with the hair well behind it
            cell.round_rect(head_x + hw - 3, eye_y, 2, 3, 1, body.eye)
        else:
            cell.round_rect(head_x + 1, eye_y, 2, 3, 1, body.eye)

    _feature(cell, body, facing, head_x, head_top, hw, hh)
    if body.carry:
        _carried(cell, body, facing, frame, torso_top)

    outline_in(cell, darken=0.58)
    if body.translucent:
        solid = np.any(cell.px != np.array(TRANSPARENT, np.uint8), axis=-1)
        cell.mix((255, 255, 255), 0.40, region=solid)
    return cell


# --- object-creatures --------------------------------------------------------
# Things that are not people but move like them.  Each gets small legs and a
# two-frame waddle, because that is what makes an object read as alive.

def _small_legs(cell: Canvas, frame: int, cx: int, top: int, color: RGB,
                spread: int = 5) -> None:
    """Two short legs from ``top`` (which bobs with the body) to the floor."""
    lift_l = 1 if frame == 0 else 0
    lift_r = 1 if frame == 2 else 0
    cell.round_rect(cx - spread, top, 3, GROUND - top - lift_l, 1, color)
    cell.round_rect(cx + spread - 2, top, 3, GROUND - top - lift_r, 1, color)
    cell.round_rect(cx - spread - 1, GROUND - lift_l - 2, 5, 2, 1,
                    cooler(color, 0.25))
    cell.round_rect(cx + spread - 3, GROUND - lift_r - 2, 5, 2, 1,
                    cooler(color, 0.25))


def _look(facing: int, amount: int = 2) -> int:
    """How far a face shifts to show which way an object is looking."""
    return {UP: 0, DOWN: 0, RIGHT: amount, LEFT: -amount}[facing]


def draw_mailbox(cell: Canvas, facing: int, frame: int) -> None:
    """A mailbox with tiny legs.  It is going somewhere."""
    cx = CELL_W // 2
    b = BOB[frame]
    look = _look(facing)
    body, dark = (128, 148, 176), (72, 88, 112)
    _small_legs(cell, frame, cx, 24 + b, dark, spread=4)
    cell.round_rect(cx - 8, 8 + b, 17, 16, 7, body)
    cell.rect(cx - 8, 16 + b, 17, 8, body)
    cell.round_rect(cx - 8, 8 + b, 17, 5, 6, warmer(body, 0.28))
    if facing == UP:
        # from behind it is just a box, and the flag is on the far side
        cell.round_rect(cx - 5, 14 + b, 11, 6, 2, cooler(body, 0.18))
    else:
        cell.round_rect(cx - 4 + look, 15 + b, 9, 3, 1, dark)
        cell.rect(cx + 8, 11 + b, 3, 2, (206, 96, 96))
        cell.round_rect(cx + 9, 6 + b, 2, 6, 1, (206, 96, 96))
    outline_in(cell, darken=0.55)


def draw_television(cell: Canvas, facing: int, frame: int) -> None:
    """A smiling television.  It is pleased to see you."""
    cx = CELL_W // 2
    b = BOB[frame]
    look = _look(facing)
    shell, screen = (196, 186, 172), (128, 176, 172)
    _small_legs(cell, frame, cx, 25 + b, cooler(shell, 0.45), spread=5)
    cell.round_rect(cx - 10, 8 + b, 21, 17, 4, shell)
    if facing == UP:
        # the back: a vent grille and a cable going nowhere
        cell.round_rect(cx - 7, 11 + b, 15, 11, 2, cooler(shell, 0.22))
        for y in range(13, 21, 3):
            cell.rect(cx - 5, y + b, 11, 1, cooler(shell, 0.45))
        cell.rect(cx + 3, 22 + b, 2, 6, cooler(shell, 0.6))
    else:
        cell.round_rect(cx - 8, 10 + b, 15, 13, 3, screen)
        eye = (40, 52, 56)
        cell.round_rect(cx - 5 + look, 13 + b, 2, 3, 1, eye)
        cell.round_rect(cx + 1 + look, 13 + b, 2, 3, 1, eye)
        # the smile widens by a pixel on the passing frame
        w = 7 if frame == 1 else 6
        cell.hline(19 + b, cx - w // 2 + look, cx + w // 2 + look, eye)
        cell.dot(cx - w // 2 - 1 + look, 18 + b, eye)
        cell.dot(cx + w // 2 + 1 + look, 18 + b, eye)
        cell.blob(cx + 9, 12 + b, 1.6, (226, 176, 96))
        cell.blob(cx + 9, 17 + b, 1.6, cooler((226, 176, 96), 0.4))
    outline_in(cell, darken=0.55)


def draw_cone(cell: Canvas, facing: int, frame: int) -> None:
    """A traffic cone, walking."""
    cx = CELL_W // 2
    b = BOB[frame]
    look = _look(facing)
    orange, band = (232, 142, 84), (244, 238, 226)
    _small_legs(cell, frame, cx, 26 + b, (86, 74, 70), spread=4)
    for row in range(18):
        span = int(row * 0.55) + 2
        cell.hline(8 + row + b, cx - span, cx + span, orange)
    cell.rect(cx - 7, 17 + b, 15, 4, band)
    cell.round_rect(cx - 10, 24 + b, 21, 3, 1, orange)
    if facing != UP:
        cell.round_rect(cx - 3 + look, 13 + b, 2, 2, 1, (72, 56, 50))
        cell.round_rect(cx + 1 + look, 13 + b, 2, 2, 1, (72, 56, 50))
    outline_in(cell, darken=0.55)


def draw_umbrella_watcher(cell: Canvas, facing: int, frame: int) -> None:
    """A floating umbrella that politely watches the player."""
    cx = CELL_W // 2
    color, shaft = (198, 112, 112), (120, 92, 78)
    lift = (0, -1, 0)[frame]
    brim = 16 + lift
    cell.ellipse(cx, brim, 11, 10, color)
    cell.rect(0, brim, CELL_W, CELL_H - brim, TRANSPARENT)
    for i in range(-2, 3):
        cell.blob(cx + i * 4.6, brim - 1, 2.6, color)
    for i in range(-2, 3):
        cell.line(cx, brim - 9, int(cx + i * 4.6), brim - 2,
                  cooler(color, 0.22))
    cell.ellipse(cx - 3, brim - 6, 4.5, 2.5, warmer(color, 0.32))
    cell.rect(cx, brim - 13, 1, 4, shaft)
    cell.rect(cx, brim - 1, 2, 11, shaft)
    cell.rect(cx - 3, brim + 8, 3, 2, shaft)
    # two small polite eyes under the brim, which follow you
    if facing != UP:
        look = _look(facing)
        cell.round_rect(cx - 4 + look, brim - 6, 2, 3, 1, (250, 246, 240))
        cell.round_rect(cx + 2 + look, brim - 6, 2, 3, 1, (250, 246, 240))
        cell.dot(cx - 4 + look, brim - 5, (40, 30, 34))
        cell.dot(cx + 3 + look, brim - 5, (40, 30, 34))
    outline_in(cell, darken=0.55)


def draw_walking_hand(cell: Canvas, facing: int, frame: int) -> None:
    """A hand that gets around on its fingers."""
    cx = CELL_W // 2
    b = BOB[frame]
    stone, dark = (208, 200, 198), (140, 132, 136)
    step = (0, 1, 0)[frame]
    cell.round_rect(cx - 8, 12 + b, 17, 11, 5, stone)
    cell.round_rect(cx - 8, 12 + b, 17, 4, 4, warmer(stone, 0.25))
    for index, dx in enumerate((-7, -2, 3, 7)):
        drop = 0 if (index + step) % 2 else 2
        cell.round_rect(cx + dx, 22 + b, 3, 7 - drop - b, 1, stone)
        cell.round_rect(cx + dx, 28 - drop, 3, 2, 1, dark)
    # the thumb points whichever way it is travelling
    thumb = cx - 11 if facing != RIGHT else cx + 8
    cell.round_rect(thumb, 14 + b, 4, 6, 2, stone)
    if facing != UP:
        look = _look(facing)
        cell.round_rect(cx - 4 + look, 16 + b, 2, 2, 1, (86, 80, 84))
        cell.round_rect(cx + 2 + look, 16 + b, 2, 2, 1, (86, 80, 84))
    outline_in(cell, darken=0.6)


def draw_zero(cell: Canvas, facing: int, frame: int) -> None:
    """A hollow ring, walking.  It is a zero, and it knows."""
    cx = CELL_W // 2
    b = BOB[frame]
    color = (246, 240, 220)
    _small_legs(cell, frame, cx, 23 + b, (168, 158, 140), spread=4)
    cell.ellipse(cx, 14 + b, 9, 10, color)
    cell.ellipse(cx, 14 + b, 5, 6, TRANSPARENT)
    cell.ellipse(cx - 3, 9 + b, 3, 2.5, warmer(color, 0.4))
    if facing != UP:
        look = _look(facing, 1)
        cell.round_rect(cx - 7 + look, 13 + b, 2, 3, 1, (120, 112, 100))
        cell.round_rect(cx + 5 + look, 13 + b, 2, 3, 1, (120, 112, 100))
    outline_in(cell, darken=0.6)


def draw_floating_eye(cell: Canvas, facing: int, frame: int) -> None:
    """An eye, at head height, keeping pace."""
    cx = CELL_W // 2
    lift = (0, -1, 0)[frame]
    sclera, iris = (96, 240, 226), (18, 30, 40)
    cell.ellipse(cx, 14 + lift, 11, 7, sclera)
    cell.ellipse(cx, 14 + lift, 9.5, 5.5, (226, 252, 248))
    look = {DOWN: 0, RIGHT: 4, LEFT: -4, UP: 0}[facing]
    cell.blob(cx + look, 14 + lift, 4, iris)
    cell.blob(cx + look, 14 + lift, 1.8, (96, 240, 226))
    cell.blob(cx + look - 1.5, 12.5 + lift, 1.2, (255, 255, 255))
    if facing == UP:
        # looking away: the lid closes over it
        cell.rect(cx - 12, 8 + lift, 24, 7, TRANSPARENT)
        cell.hline(14 + lift, cx - 10, cx + 9, sclera)
        cell.hline(15 + lift, cx - 9, cx + 8, cooler(sclera, 0.3))
    outline_in(cell, darken=0.5)


def draw_block_cat(cell: Canvas, facing: int, frame: int) -> None:
    """A cat assembled from two cubes, with impossibly long ears."""
    cx = CELL_W // 2
    b = BOB[frame]
    fur, dark = (238, 206, 126), (176, 148, 84)
    _small_legs(cell, frame, cx, 26 + b, dark, spread=6)
    cell.round_rect(cx - 8, 18 + b, 17, 9, 3, fur)
    cell.round_rect(cx - 7, 9 + b, 15, 11, 3, fur)
    # the ears are the entire personality, so they get half the cell
    for sign in (-1, 1):
        cell.round_rect(cx + sign * 5 - 2, 1 + b, 4, 11, 2, fur)
        cell.round_rect(cx + sign * 5 - 1, 3 + b, 2, 7, 1, warmer(fur, 0.35))
    if facing == UP:
        cell.round_rect(cx - 5, 12 + b, 11, 6, 2, cooler(fur, 0.16))
        cell.round_rect(cx - 1, 20 + b, 3, 8, 1, fur)
    else:
        look = _look(facing)
        cell.round_rect(cx - 4 + look, 13 + b, 2, 2, 1, (68, 56, 40))
        cell.round_rect(cx + 2 + look, 13 + b, 2, 2, 1, (68, 56, 40))
        cell.dot(cx + look, 16 + b, (198, 132, 128))
        tail = cx + 8 if facing != LEFT else cx - 11
        cell.round_rect(tail, 19 + b, 3, 7, 1, fur)
    outline_in(cell, darken=0.58)


def draw_cloud_ladder(cell: Canvas, facing: int, frame: int) -> None:
    """A small cloud carrying a ladder, which it does not explain."""
    cx = CELL_W // 2
    cloud, wood = (238, 240, 248), (198, 162, 108)
    lift = (0, -1, 0)[frame]
    cell.rect(cx + 2, 4 + lift, 2, 20, wood)
    cell.rect(cx + 9, 4 + lift, 2, 20, wood)
    for y in range(6, 24, 5):
        cell.rect(cx + 3, y + lift, 7, 2, warmer(wood, 0.25))
    cell.blob(cx - 3, 16 + lift, 7, cloud)
    cell.blob(cx - 9, 18 + lift, 5, cloud)
    cell.blob(cx + 2, 18 + lift, 5, cloud)
    cell.blob(cx - 5, 12 + lift, 4.5, (255, 255, 255))
    if facing != UP:
        look = _look(facing)
        cell.round_rect(cx - 6 + look, 15 + lift, 2, 2, 1, (140, 150, 172))
        cell.round_rect(cx - 1 + look, 15 + lift, 2, 2, 1, (140, 150, 172))
    outline_in(cell, darken=0.72)


def draw_seedling(cell: Canvas, facing: int, frame: int) -> None:
    """A sapling that has decided to walk."""
    cx = CELL_W // 2
    b = BOB[frame]
    leaf, stem = (150, 196, 128), (146, 118, 82)
    _small_legs(cell, frame, cx, 25 + b, stem, spread=4)
    cell.round_rect(cx - 3, 14 + b, 6, 12, 2, stem)
    cell.blob(cx, 10 + b, 8, leaf)
    cell.blob(cx - 7, 13 + b, 5, leaf)
    cell.blob(cx + 7, 13 + b, 5, leaf)
    cell.blob(cx - 3, 6 + b, 4, warmer(leaf, 0.25))
    if facing != UP:
        look = _look(facing)
        cell.round_rect(cx - 4 + look, 18 + b, 2, 2, 1, (78, 60, 44))
        cell.round_rect(cx + 2 + look, 18 + b, 2, 2, 1, (78, 60, 44))
        cell.hline(22 + b, cx - 2 + look, cx + 1 + look, (78, 60, 44))
    outline_in(cell, darken=0.58)


def draw_pawn(cell: Canvas, facing: int, frame: int) -> None:
    """A chess piece that left the board."""
    cx = CELL_W // 2
    b = BOB[frame]
    body = (240, 236, 228)
    _small_legs(cell, frame, cx, 26 + b, (150, 146, 142), spread=4)
    cell.round_rect(cx - 8, 22 + b, 17, 5, 2, body)
    for row in range(12):
        span = int(2 + row * 0.5)
        cell.hline(11 + row + b, cx - span, cx + span, body)
    cell.blob(cx, 8 + b, 5, body)
    cell.blob(cx - 2, 6 + b, 2, (255, 255, 255))
    if facing != UP:
        look = _look(facing, 1)
        cell.round_rect(cx - 3 + look, 7 + b, 2, 2, 1, (128, 122, 122))
        cell.round_rect(cx + 1 + look, 7 + b, 2, 2, 1, (128, 122, 122))
    outline_in(cell, darken=0.62)


def draw_wind_up(cell: Canvas, facing: int, frame: int) -> None:
    """A wind-up toy with a key that turns as it walks."""
    cx = CELL_W // 2
    b = BOB[frame]
    shell, metal = (226, 128, 128), (206, 206, 214)
    _small_legs(cell, frame, cx, 23 + b, metal, spread=5)
    cell.round_rect(cx - 8, 8 + b, 17, 16, 5, shell)
    cell.round_rect(cx - 8, 8 + b, 17, 5, 5, warmer(shell, 0.3))
    if facing != UP:
        look = _look(facing)
        cell.round_rect(cx - 4 + look, 14 + b, 2, 3, 1, (86, 44, 52))
        cell.round_rect(cx + 2 + look, 14 + b, 2, 3, 1, (86, 44, 52))
    # the key turns one step per frame, so it is always winding down
    kx, ky = cx + 10, 13 + b
    cell.blob(kx, ky, 2.5, metal)
    if frame == 0:
        cell.rect(kx - 1, ky - 5, 2, 10, metal)
    elif frame == 1:
        cell.line(kx - 4, ky - 4, kx + 4, ky + 4, metal)
    else:
        cell.rect(kx - 5, ky - 1, 10, 2, metal)
    outline_in(cell, darken=0.55)


def draw_long_bird(cell: Canvas, facing: int, frame: int) -> None:
    """Mostly beak."""
    cx = CELL_W // 2
    b = BOB[frame]
    feather, beak = (222, 226, 236), (238, 176, 96)
    _small_legs(cell, frame, cx, 23 + b, beak, spread=3)
    cell.ellipse(cx - 1, 18 + b, 8, 6, feather)
    cell.blob(cx + 1, 10 + b, 5, feather)
    if facing == UP:
        cell.blob(cx + 1, 9 + b, 4, cooler(feather, 0.14))
    else:
        sign = -1 if facing == LEFT else 1
        cell.round_rect(cx + (2 if sign > 0 else -13), 10 + b, 12, 3, 1, beak)
        cell.round_rect(cx + sign * 2 - 1, 8 + b, 2, 2, 1, (48, 52, 62))
    outline_in(cell, darken=0.6)


def draw_shade(cell: Canvas, facing: int, frame: int) -> None:
    """Another version of you, three shades paler."""
    body = Body(skin=(214, 210, 214), hair=(178, 174, 184),
                shirt=(198, 194, 206), trousers=(172, 168, 182),
                faceless=True, translucent=True)
    cell.paste(draw_figure(body, facing, frame), 0, 0)


# --- assembly ----------------------------------------------------------------

def figure_block(body: Body) -> Canvas:
    block = Canvas(CELL_W * FRAMES, CELL_H * 4, TRANSPARENT)
    for facing in range(4):
        for frame in range(FRAMES):
            block.paste(draw_figure(body, facing, frame),
                        frame * CELL_W, facing * CELL_H)
    return block


def creature_block(draw: Callable[[Canvas, int, int], None]) -> Canvas:
    block = Canvas(CELL_W * FRAMES, CELL_H * 4, TRANSPARENT)
    for facing in range(4):
        for frame in range(FRAMES):
            cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
            draw(cell, facing, frame)
            block.paste(cell, frame * CELL_W, facing * CELL_H)
    return block


def static_block(draw: Callable[[Canvas], None]) -> Canvas:
    """A block whose twelve cells are identical: an object that never turns."""
    cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
    draw(cell)
    block = Canvas(CELL_W * FRAMES, CELL_H * 4, TRANSPARENT)
    for facing in range(4):
        for frame in range(FRAMES):
            block.paste(cell, frame * CELL_W, facing * CELL_H)
    return block


def sheet(blocks: Sequence[Canvas]) -> Canvas:
    """Pack up to eight character blocks into a 288x256 charset."""
    out = Canvas(SHEET_W, SHEET_H, TRANSPARENT)
    for index, block in enumerate(blocks[:8]):
        out.paste(block, (index % 4) * CELL_W * FRAMES,
                  (index // 4) * CELL_H * 4)
    return out


def gleam_block() -> Canvas:
    """A tiny pulsing shine, for anything the player can interact with.

    Interactables were drawn on the ``Blank`` charset — literally invisible —
    and the only way to find one was to walk the whole world pressing the
    action key.  This is the smallest thing that fixes that without turning
    the sprinkling of secrets into a marked map: a four-pixel cross that
    breathes between two low-contrast values and vanishes entirely on one
    frame of the cycle.

    It reads as a glint on something, not as a quest marker.  You have to be
    looking at that part of the screen to catch it.
    """
    block = Canvas(CELL_W * FRAMES, CELL_H * 4, TRANSPARENT)
    faint, lit = (196, 190, 172), (238, 234, 214)
    for facing in range(4):
        for frame in range(FRAMES):
            cell = Canvas(CELL_W, CELL_H, TRANSPARENT)
            cx, cy = CELL_W // 2, GROUND - 8
            if frame == 1:
                # the whole point: one frame in three it is not there at all
                pass
            else:
                tone = lit if frame == 0 else faint
                cell.rect(cx - 1, cy - 3, 2, 7, tone)
                cell.rect(cx - 3, cy - 1, 7, 2, tone)
                if frame == 0:
                    cell.rect(cx - 1, cy - 1, 2, 2, (255, 252, 240))
            block.paste(cell, frame * CELL_W, facing * CELL_H)
    return block
