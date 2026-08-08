"""What lives on the island.

Original animals, not borrowed ones.  The world is a homage and they are
drawn to fit it — small, round, two-tone, built from masses rather than lines
— but nothing here is a traced sprite and none of them is anybody else's
character.  The lineage is the game's own: the same ``_mass`` and ``_round``
that light every resident of the grove, the same rule that a mass takes the
light and a detail stays flat.

**One anatomy per design, four views of it.**  The first version drew each
facing freehand and they drifted: heads changed size between front and side,
proportions wandered, and the frightening ones fell apart in profile because
a grin drawn as scattered dots reads as a white smear from the side.  So the
body plan is a dataclass now — one head radius, one body radius, one set of
offsets — and every facing is built from the same numbers.  What changes
between views is *what is visible*, not how big anything is.

Three kinds live here:

**the small ones**   birds and beach animals.  Nothing is wrong with them and
                     nothing ever happens to them, which is the point.
**the wrong ones**   the same animals with something taken out or added.  They
                     only appear in the regions that have gone.
**him**              drawn to the same twenty-four pixels as a bird, because
                     the horror is not that he is large.
"""

from __future__ import annotations

from dataclasses import dataclass

from .canvas import Canvas, RGB, blend
from .charsets import DOWN, GROUND, LEFT, RIGHT, UP, _small_legs
from .kin import CX, _bob, _mass, _round


# --- one body plan, four views ------------------------------------------------

@dataclass(frozen=True)
class Bird:
    """The measurements every view of one bird agrees on.

    Radii, not rectangles.  A head that is 4.5 across the front and 4.5 in
    profile is the same head; a head drawn by eye twice is two heads, and at
    twenty-four pixels the eye notices.
    """
    body: RGB
    wing: RGB
    beak: RGB
    body_r: float = 6.8
    body_ry: float = 6.2
    head_r: float = 4.8
    head_ry: float = 4.4
    head_lift: int = 7          # how far above the body centre the head sits
    head_reach: int = 4         # how far forward it leans in profile
    # Body centre, measured from the top of the cell.  These are small
    # animals in a cell sized for a person, so they sit LOW in it: the body
    # has to come down far enough that the legs reach the floor at GROUND
    # without stretching.  Drawn head-high, as it was, the feet ended up
    # eight pixels adrift under the bird and the whole cast looked unattached.
    top: int = 20
    ink: RGB = (26, 24, 34)
    hops: bool = True


def _bird_base(cell: Canvas, plan: Bird, facing: int, frame: int,
               *, turn: bool = False) -> tuple[int, int, int, int]:
    """Body, wings, tail and legs.  Returns where the head goes.

    Everything common to all four views lives here, so a bird cannot come out
    a different size depending on which way it is looking.

    ``turn`` is off by default and the default is the bluebird's drawing,
    untouched.  The smaller birds switch it on: at their size one ellipse per
    view left the front and the back reading as the same picture, so they get
    a profile that is longer than it is wide and a back that is covered by
    the folded wings.  It changes colour and length, never the height or the
    place anything sits.
    """
    b = _bob(frame) if plan.hops else 0
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = plan.top + b
    hx = CX + (plan.head_reach * lead if side else 0)
    hy = cy - plan.head_lift

    rx, ry = plan.body_r, plan.body_ry
    if turn:
        rx = plan.body_r * (1.24 if side else 0.88)

    back = turn and facing == UP
    _round(cell, CX, cy, rx, ry, plan.wing if back else plan.body)
    if back:
        seam = blend(plan.wing, (0, 0, 0), 0.34)
        cell.vline(CX, cy - int(ry) + 1, cy + int(ry) - 1, seam)
        cell.ellipse(CX, cy - ry * 0.6, rx * 0.5, ry * 0.26,
                     blend(plan.wing, (255, 255, 255), 0.16))
    elif turn and not side:
        cell.ellipse(CX, cy + 1, rx * 0.58, ry * 0.62,
                     blend(plan.body, (255, 255, 255), 0.26))

    spread = 1 if frame == 1 and plan.hops else 0
    if side:
        # One wing, on the near side, and the tail behind the body.
        _mass(cell, CX - 2, cy - 2, 5 + spread, 7 + spread, plan.wing, top=2)
        # The tail is the other half of the profile: it runs out behind and
        # is simply not there from the front.
        tail_x = CX - lead * (int(rx) + 2)
        _mass(cell, tail_x - (3 if lead > 0 else 0), cy, 6, 4, plan.wing)
    else:
        # Walking away, the wings are folded over the back rather than hanging
        # at the sides, so they sit in tighter and a little higher.
        inset = 2 if back else 0
        for wx in (CX - int(rx) - 2 + inset, CX + int(rx) - 2 - inset):
            _mass(cell, wx, cy - 2 - inset // 2, 4 + spread, 7 + spread,
                  plan.wing, top=2)
        if facing == UP:
            _mass(cell, CX - 2, cy + 2, 4, 6, plan.wing)     # tail, straight up

    # Legs start where the body ends, not at a fixed height off the floor.
    _small_legs(cell, frame, CX, min(GROUND - 3, int(cy + ry) - 1),
                plan.beak, spread=3)
    return hx, hy, lead, 1 if side else 0


def _bird_head(cell: Canvas, plan: Bird, facing: int, hx: int, hy: int,
               lead: int) -> None:
    """The head, at the same radius in every view.  No face on it yet."""
    colour = plan.body if facing != UP else plan.wing
    _round(cell, hx, hy, plan.head_r, plan.head_ry, colour)
    if facing == UP:
        return
    if facing in (LEFT, RIGHT):
        # Beak in profile: a wedge, thicker at the head and coming to a point.
        for step in range(3):
            x = hx + lead * (int(plan.head_r) + step)
            cell.vline(x, hy - 1 + step // 2, hy + 1 - step // 2, plan.beak)
    else:
        cell.rect(CX - 1, hy + 2, 3, 2, plan.beak)


def _eyes(cell: Canvas, plan: Bird, facing: int, hx: int, hy: int, lead: int,
          *, ink: RGB | None = None, iris: RGB | None = None,
          size: int = 2) -> None:
    """Eyes, placed off the head centre so they sit the same in every view."""
    ink = ink or plan.ink
    if facing == UP:
        return
    if facing in (LEFT, RIGHT):
        ex = hx + lead * 1
        cell.rect(ex - (size - 1 if lead < 0 else 0), hy - 2, size, size, ink)
        if iris:
            cell.dot(ex, hy - 1, iris)
    else:
        for ex in (hx - 3, hx + 4 - size):
            cell.rect(ex, hy - 2, size, size, ink)
        if iris:
            cell.dot(hx - 2, hy - 1, iris)
            cell.dot(hx + 3, hy - 1, iris)


def _grin(cell: Canvas, plan: Bird, facing: int, hx: int, hy: int, lead: int,
          teeth: RGB = (238, 234, 226)) -> None:
    """A mouth that reads from every angle.

    Drawn as a dark jaw band with teeth cut into it, never as loose dots: in
    profile a row of dots is a white smear, and that is exactly how the first
    version of the smiler failed.
    """
    dark = blend(plan.ink, (0, 0, 0), 0.4)
    if facing == UP:
        return
    if facing in (LEFT, RIGHT):
        x0 = hx - (int(plan.head_r) if lead > 0 else 0)
        _mass(cell, x0, hy + 2, int(plan.head_r) + 2, 3, dark, top=1)
        for step in range(1, int(plan.head_r) + 1, 2):
            cell.vline(x0 + step, hy + 2, hy + 3, teeth)
    else:
        width = int(plan.head_r * 1.9)
        _mass(cell, hx - width // 2, hy + 2, width, 4, dark, top=1)
        for step in range(1, width - 1, 2):
            cell.vline(hx - width // 2 + step, hy + 2, hy + 4, teeth)


# --- the ordinary ones --------------------------------------------------------

BLUEBIRD = Bird(body=(78, 140, 226), wing=(52, 104, 190), beak=(246, 190, 72))
FINCH = Bird(body=(238, 156, 186), wing=(202, 108, 148), beak=(250, 214, 120),
             body_r=5.6, body_ry=5.2, head_r=4.0, head_ry=3.8,
             head_lift=6, head_reach=3, top=21)


def draw_bluebird(cell: Canvas, facing: int, frame: int) -> None:
    """A round blue bird that never stops hopping.

    The friendliest thing on the island and the one every other design here
    is a variation on.  Left alone: it was the one that already worked.
    """
    hx, hy, lead, _ = _bird_base(cell, BLUEBIRD, facing, frame)
    _bird_head(cell, BLUEBIRD, facing, hx, hy, lead)
    _eyes(cell, BLUEBIRD, facing, hx, hy, lead)


def draw_finch(cell: Canvas, facing: int, frame: int) -> None:
    """Smaller, pink, and always facing slightly the wrong way.

    The first version was a pink blob because the head was the same value as
    the body and only two pixels smaller.  It is a clear third narrower now
    and sits properly proud of the shoulders.
    """
    hx, hy, lead, _ = _bird_base(cell, FINCH, facing, frame, turn=True)
    _bird_head(cell, FINCH, facing, hx, hy, lead)
    _eyes(cell, FINCH, facing, hx, hy, lead)


def draw_hoglet(cell: Canvas, facing: int, frame: int) -> None:
    """A small spined animal.  Nothing to do with anybody: a hedgehog.

    Which is the joke, and it is never said aloud.  The spines are the
    silhouette, so they are drawn on every facing at the same length -- the
    first version lost them in profile and it read as a potato.
    """
    b = _bob(frame)
    coat, spine = (150, 126, 108), (88, 70, 62)
    snout, ink = (208, 180, 158), (30, 26, 30)
    cy = 23 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    rx, ry = (9.4, 4.8) if side else (7.2, 6.2)
    # In profile the animal is not a symmetrical lump: the rump carries the
    # weight and sits back, the snout end tapers away in front of it, and the
    # spines lie back along the body rather than standing straight up.  That
    # is what tells left from right at this size -- it was a mirror of itself
    # before, and read as facing neither way.
    bx = CX - (lead * 2 if side else 0)
    _round(cell, bx, cy, rx, ry, coat)

    # The quills are a coat, not a row of aerials.  Drawn as free-standing
    # lines they floated above the animal with daylight under them; here they
    # are one mass sitting on the back with points cut into its top edge, so
    # the spiky outline is the silhouette of something attached.
    # Walking away it is all quill: the coat comes right down over the rump
    # and there is no pale underside or face to see at all, which is a real
    # back view rather than the front with the eyes rubbed out.
    away = facing == UP
    qy = cy + (1 if away else -1)
    qry = ry * (1.02 if away else 0.92)
    _round(cell, bx, qy, rx * (1.0 if away else 0.9), qry, spine)
    top = int(qy - qry)
    tip_hi = blend(spine, (255, 255, 255), 0.3)
    for index, offset in enumerate(range(-int(rx) + 3, int(rx) - 2, 2)):
        sx = bx + offset
        tall = (5, 3, 4, 2)[index % 4]      # uneven, so it is not a battlement
        for step in range(tall + 3):        # the last rows root into the coat
            y = top - tall + step
            drift = -lead if side and step < 2 else 0
            cell.dot(sx + drift, y, spine)
            if step >= tall:                # widens where it meets the coat
                cell.hline(y, sx - 1, sx + 1, spine)
        cell.dot(sx + (-lead if side else 0), top - tall, tip_hi)

    if away:
        cell.ellipse(bx, cy + ry * 0.55, 2.4, 1.8,        # the tail, and that
                     blend(spine, (0, 0, 0), 0.3))        # is all there is
    else:
        hx = bx + (lead * 8 if side else 0)
        hy = cy + (1 if side else 4)
        _round(cell, hx, hy, 3.4, 2.8, snout)
        if side:
            cell.rect(hx + lead * 2, hy - 1, 2, 2, ink)
            cell.dot(hx + lead * 3, hy + 1, ink)
        else:
            cell.rect(hx - 3, hy - 1, 2, 2, ink)
            cell.rect(hx + 2, hy - 1, 2, 2, ink)
            cell.dot(hx, hy + 2, ink)
    _small_legs(cell, frame, CX, min(GROUND - 3, int(cy + ry) - 1),
                spine, spread=4)


def draw_shellback(cell: Canvas, facing: int, frame: int) -> None:
    """A beach animal carrying a shell far too big for it.

    The shell is the whole silhouette and never changes size; what changes is
    how much of the animal is out from under it.
    """
    b = _bob(frame)
    # Shell and animal were within a shade of each other and the whole design
    # came out as one tan lump.  They are now two clearly separate materials:
    # a hard, saturated, ridged shell and a pale soft animal underneath.
    shell, ridge = (172, 116, 58), (108, 68, 30)
    body, ink = (238, 216, 186), (36, 30, 32)
    cy = 22 + b
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1

    back = facing == UP
    rx, ry = (9.2, 5.0) if side else (7.0, 6.6)
    bx = CX - (lead * 2 if side else 0)

    # The shell: a hard dome with ribs fanning down from the umbo -- the point
    # it grew out from, which sits over the head end and so tells you which
    # way the animal is pointing even when the head is tucked in.
    # It is an egg, not a circle: narrow over the head, broad over the rump.
    # So when the animal turns to walk away the whole shell turns with it and
    # the broad end swaps ends -- which is the only thing you can see change
    # on an animal whose head is tucked away under a lid.
    _round(cell, bx, cy, rx * 0.88, ry * 0.94, shell)
    _round(cell, bx, cy + ry * (0.30 if back else -0.30), rx, ry * 0.70, shell)
    # The umbo sits over the head end, so from behind it is at the far side
    # and the ribs fan the other way -- the one mark that says which end of
    # the animal you are looking at when the head is not showing.
    ux = bx + (lead * 3 if side else 0)
    uy = cy + int(ry * 0.5) if back else cy - int(ry * 0.5)
    fan = -1 if back else 1
    rib = blend(shell, ridge, 0.55)
    for dx, dy in ((-6, 5), (0, 7), (6, 5)):
        cell.line(ux + int(dx * rx / 18.0), uy + fan,
                  ux + int(dx * rx / 7.0), uy + fan * int(dy * ry / 6.0), rib)

    # The animal itself, over the shell's rim: whatever is sticking out of it
    # is nearer the eye than the shell is, and has to be drawn last or the
    # dome swallows it and the design goes back to being one lump.
    reach = 1 if frame == 1 else 0
    if back:
        # Walking away, the head is on the far side of the shell and simply
        # is not there: two hind feet and a stub of tail, nothing else.
        cell.rect(CX - 1, int(cy + ry) - 1, 3, 2, body)
        _mass(cell, CX - 9, int(cy + ry) - 4 + reach, 4, 3, body)
        _mass(cell, CX + 5, int(cy + ry) - 4 + reach, 4, 3, body)
    else:
        hx = CX + (lead * 8 if side else 0)
        hy = cy + (2 if side else int(ry) - 1)
        _round(cell, hx, hy, 3.0, 2.4, body)
        if side:
            cell.rect(hx + lead * 1, hy - 1, 2, 2, ink)
        else:
            cell.rect(hx - 3, hy - 1, 2, 2, ink)
            cell.rect(hx + 2, hy - 1, 2, 2, ink)
        if side:
            _mass(cell, CX + lead * 5 - (2 if lead < 0 else 0), cy + 3,
                  4 + reach, 3, body)
        else:
            _mass(cell, CX - 9, cy + 3 + reach, 4, 3, body)
            _mass(cell, CX + 5, cy + 3 + reach, 4, 3, body)
    cell.ellipse(ux, uy, rx * 0.2, ry * 0.2,
                 blend(shell, (0, 0, 0), 0.2) if back
                 else blend(shell, (255, 255, 255), 0.28))
    _small_legs(cell, frame, CX, min(GROUND - 3, int(cy + ry) - 1),
                blend(body, ridge, 0.4), spread=5)


# --- the wrong ones -----------------------------------------------------------

def draw_smiler(cell: Canvas, facing: int, frame: int) -> None:
    """The bluebird, with a mouth it should not have.

    Same plan, same colours, same hop -- it has to be *that* bird or the joke
    does not land.  The only differences are the mouth and the pupils, and
    from behind there is no difference at all.
    """
    hx, hy, lead, _ = _bird_base(cell, BLUEBIRD, facing, frame)
    _bird_head(cell, BLUEBIRD, facing, hx, hy, lead)
    _eyes(cell, BLUEBIRD, facing, hx, hy, lead, iris=(214, 38, 34))
    _grin(cell, BLUEBIRD, facing, hx, hy, lead)


def draw_watcher(cell: Canvas, facing: int, frame: int) -> None:
    """A finch that has stopped doing anything except look.

    ``hops=False``, so it is the only small thing on the island that does not
    move on its idle frames -- which at this size is the most unsettling
    thing a sprite can do while everything around it does.
    """
    plan = Bird(body=(190, 130, 150), wing=(140, 90, 112),
                beak=(228, 190, 110), body_r=5.6, body_ry=5.2,
                head_r=4.0, head_ry=3.8, head_lift=6, head_reach=3,
                top=21, ink=(12, 10, 14), hops=False)
    hx, hy, lead, _ = _bird_base(cell, plan, facing, frame, turn=True)
    _bird_head(cell, plan, facing, hx, hy, lead)
    _eyes(cell, plan, facing, hx, hy, lead, iris=(206, 44, 40), size=3)


def draw_hollow(cell: Canvas, facing: int, frame: int) -> None:
    """A bird-shaped absence.

    Drawn flat, which is the whole trick.  Every other figure in this game
    goes through ``_mass`` and ``_round`` and takes the light -- and running
    a hole through them lit it, which produced a muddy brown bird instead of
    a gap.  This is the one design that refuses the shading: three flat
    values, no highlight anywhere, and a thin dark rim so the silhouette has
    an edge to read against the grass.

    The silhouette itself is the bluebird's, to the pixel, so what the player
    recognises is the shape of something they have already met.
    """
    plan = BLUEBIRD
    void, rim = (12, 10, 16), (58, 18, 20)
    side = facing in (LEFT, RIGHT)
    lead = -1 if facing == LEFT else 1
    cy = plan.top
    hx = CX + (plan.head_reach * lead if side else 0)
    hy = cy - plan.head_lift

    # body and head: flat fills with a rim, no lighting, and the bluebird's
    # own radii so the outline stays the outline of the bird it is missing.
    rx, ry = plan.body_r, plan.body_ry
    cell.ellipse(CX, cy, rx + 0.6, ry + 0.6, rim)
    cell.ellipse(CX, cy, rx, ry, void)
    if side:
        cell.rect(CX - 2, cy - 2, 5, 7, void)
        tail = CX - lead * (int(rx) + 1)
        cell.rect(tail - (2 if lead > 0 else 0), cy + 1, 4, 3, void)
    else:
        for wx in (CX - int(rx) - 2, CX + int(rx) - 2):
            cell.rect(wx, cy - 2, 4, 7, void)
        if facing == UP:
            cell.rect(CX - 2, cy + 2, 4, 6, void)

    # From behind, the hole is open towards you: the lip of it catches what
    # little light there is and you can see some way down.  Nothing about the
    # shape changes -- it is the inside that shows.
    if facing == UP:
        cell.ellipse(CX, cy + 1.5, rx * 0.82, ry * 0.70, rim)
        cell.ellipse(CX, cy + 2.5, rx * 0.50, ry * 0.40,
                     blend(rim, (0, 0, 0), 0.45))
        cell.ellipse(hx, hy, plan.head_r + 0.6, plan.head_ry + 0.6, rim)
        cell.ellipse(hx, hy, plan.head_r, plan.head_ry, void)
        cell.ellipse(hx, hy + 0.5, plan.head_r * 0.66, plan.head_ry * 0.54, rim)
    else:
        cell.ellipse(hx, hy, plan.head_r + 0.6, plan.head_ry + 0.6, rim)
        cell.ellipse(hx, hy, plan.head_r, plan.head_ry, void)
        if side:                                       # the beak is still there
            for step in range(3):
                x = hx + lead * (int(plan.head_r) + step)
                cell.vline(x, hy - 1 + step // 2, hy + 1 - step // 2, rim)
            cell.rect(hx + lead - (1 if lead < 0 else 0), hy - 2, 2, 2,
                      (198, 40, 36))
        else:
            cell.rect(CX - 1, hy + 2, 3, 2, rim)
            cell.rect(hx - 3, hy - 2, 2, 2, (198, 40, 36))
            cell.rect(hx + 2, hy - 2, 2, 2, (198, 40, 36))

    # no legs: it is not standing on anything
    cell.ellipse(CX, GROUND - 2, 5.0, 1.6, rim)


# --- him ----------------------------------------------------------------------

def _quill(cell: Canvas, x0: int, y0: int, x1: int, y1: int, colour: RGB,
           thick: int = 5) -> None:
    """One swept spine: thick where it leaves the skull, a point at the end.

    Drawn as a tapering run rather than a rectangle, because a rectangle at
    this size merges into the head and the silhouette stops being his.  The
    taper is what makes a handful of these read as quills rather than lumps.
    """
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    flat = abs(x1 - x0) >= abs(y1 - y0)
    for index in range(steps + 1):
        t = index / steps
        x = round(x0 + (x1 - x0) * t)
        y = round(y0 + (y1 - y0) * t)
        half = int(round(thick * (1.0 - t) / 2.0))
        if flat:
            cell.vline(x, y - half, y + half, colour)
        else:
            cell.hline(y, x - half, x + half, colour)


def draw_him(cell: Canvas, facing: int, frame: int) -> None:
    """The thing the world is about.

    He stands at the player's height -- the full thirty-two pixels, the same
    as anybody else who walks around in this game -- because the horror is
    not that he is large.  It is that he is a person-sized figure standing in
    a field of small animals, and none of them will go near him.

    Three quills, not a hedge.  The silhouette only works if each spine is
    big enough to be read on its own and the skull stays a clear round mass
    underneath them.

    There are no teeth.  A row of white pixels across a face this small reads
    as a typewriter -- what sits under the quills is a socket with something
    lit a long way down inside it, and the red coming out of it.
    """
    fur_dk, fur, fur_hi = (20, 20, 58), (44, 44, 108), (82, 84, 164)
    skin, skin_dk = (224, 168, 126), (170, 116, 84)
    glove, glove_dk = (238, 234, 228), (166, 164, 174)
    shoe, shoe_dk, sole = (186, 26, 24), (120, 14, 14), (214, 212, 216)
    socket, iris, glint = (8, 6, 12), (222, 32, 28), (255, 250, 244)
    blood = (150, 14, 14)

    side = facing in (LEFT, RIGHT)
    back = facing == UP
    lead = -1 if facing == LEFT else 1
    hy = 8                                            # skull centre
    swing = (0, 1, -1)[frame % 3]

    # --- legs, socks and shoes ------------------------------------------------
    for sign in (-1, 1):
        step = swing if (sign * (lead if side else 1)) > 0 else -swing
        lx = CX + (lead * sign * 2 if side else sign * 4) - 1
        cell.rect(lx, 21, 3, 5 + step, fur)
        cell.vline(lx, 21, 25 + step, fur_dk)
        cell.rect(lx - 1, 24 + step, 5, 2, glove)                 # sock cuff
        fx = lx - 3
        cell.round_rect(fx, 26 + step, 8, 4, 1, shoe)
        cell.hline(26 + step, fx + 1, fx + 6, sole)
        cell.rect(fx, 29 + step, 8, 1, shoe_dk)

    # --- torso ----------------------------------------------------------------
    cell.ellipse(CX, 18, 4.6, 4.4, fur_dk)
    cell.ellipse(CX, 17, 4.0, 3.8, fur)
    if not back:
        cell.ellipse(CX + (lead * 2 if side else 0), 19,
                     1.8 if side else 2.8, 2.4, skin)

    # --- arms and gloves ------------------------------------------------------
    for sign in (-1, 1):
        reach = swing if sign > 0 else -swing
        ax = CX + sign * 4
        cell.rect(ax - 1, 15 + reach, 3, 4, skin)
        cell.round_rect(ax + (0 if sign > 0 else -3), 18 + reach, 4, 4, 1,
                        glove)
        cell.hline(21 + reach, ax + (1 if sign > 0 else -2),
                   ax + (2 if sign > 0 else -1), glove_dk)

    # --- quills ---------------------------------------------------------------
    hx = CX + (lead * 2 if side else 0)
    if side:
        root = hx - lead * 4
        for dy, drop, thick in ((-4, -7, 6), (0, 0, 7), (4, 7, 6)):
            _quill(cell, root, hy + dy, root - lead * 10, hy + drop, fur_dk,
                   thick)
            _quill(cell, root, hy + dy - 1, root - lead * 7, hy + drop - 1,
                   fur, thick - 3)
    elif back:
        for dx, ex, ey, thick in ((-4, -11, 2, 7), (-2, -5, 11, 7),
                                  (2, 5, 11, 7), (4, 11, 2, 7)):
            _quill(cell, CX + dx, hy, CX + ex, hy + ey, fur_dk, thick)
            _quill(cell, CX + dx, hy - 1, CX + int(ex * .7), hy + int(ey * .7),
                   fur, thick - 3)
    else:
        for sign in (-1, 1):
            for dy, drop in ((-3, -6), (2, 8)):
                _quill(cell, CX + sign * 3, hy + dy, CX + sign * 11, hy + drop,
                       fur_dk, 7)
                _quill(cell, CX + sign * 3, hy + dy - 1, CX + sign * 8,
                       hy + drop - 1, fur, 4)

    # --- the skull ------------------------------------------------------------
    cell.ellipse(hx, hy, 5.6, 5.4, fur_dk)
    cell.ellipse(hx, hy - 1, 5.0, 4.6, fur)
    cell.ellipse(hx - lead, hy - 3, 2.6, 1.6, fur_hi)
    for sign in ((lead,) if side else (-1, 1)):                   # ears
        _quill(cell, hx + sign * 3, hy - 4, hx + sign * 4, hy - 9, fur, 4)

    if back:
        return                                    # nothing on this side to read

    # --- face -----------------------------------------------------------------
    if side:
        mx = hx + lead * 4
        cell.ellipse(mx, hy + 3, 3.6, 2.8, skin)
        cell.ellipse(mx, hy + 4, 3.0, 1.8, skin_dk)
        cell.rect(mx + lead * 2 - (1 if lead < 0 else 0), hy + 1, 2, 2, fur_dk)
        cell.rect(hx - (1 if lead > 0 else 3), hy - 3, 5, 5, socket)
        cell.rect(hx + lead - (1 if lead < 0 else 0), hy - 1, 2, 2, iris)
        cell.dot(hx + lead, hy - 1, glint)
        cell.vline(hx + lead, hy + 2, hy + 6, blood)
        cell.vline(hx + lead * 3, hy + 2, hy + 4, blood)
        cell.hline(hy + 5, mx - 2, mx + 1, blood)
    else:
        cell.ellipse(hx, hy + 4, 4.4, 2.8, skin)
        cell.ellipse(hx, hy + 5, 3.8, 1.8, skin_dk)
        cell.rect(hx - 1, hy + 2, 2, 2, fur_dk)
        for sign in (-1, 1):
            cell.rect(hx + (1 if sign > 0 else -5), hy - 3, 4, 5, socket)
            cell.rect(hx + (2 if sign > 0 else -3), hy - 1, 2, 2, iris)
            cell.dot(hx + (2 if sign > 0 else -2), hy - 1, glint)
            cell.vline(hx + (2 if sign > 0 else -3), hy + 2, hy + 5, blood)
        cell.hline(hy + 6, hx - 2, hx + 2, blood)
