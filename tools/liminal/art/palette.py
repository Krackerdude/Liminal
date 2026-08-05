"""Per-world colour identity.

Each dream commits to one dominant hue.  Moving between worlds should feel
like the colour of the light changed, not like the level loaded.

Colours are muted rather than saturated — even the bright ones are soft.
Shadows shift cooler, highlights shift warmer, which is what lets a five-colour
sprite look like it has more colours than it does.
"""

from __future__ import annotations

from dataclasses import dataclass

from .canvas import RGB


@dataclass(frozen=True)
class Palette:
    """A closed six-colour world palette.

    ``ground``/``ground_b`` are the two floor tones, ``form`` is what the world
    is *built out of* (brick, digits, blocks, stone), ``form_dark`` shades it
    and doubles as its outline, ``accent`` is the one colour that carries
    meaning, and ``void`` is whatever lies past the edge.
    """
    ground: RGB
    ground_b: RGB
    form: RGB
    form_light: RGB
    form_dark: RGB
    accent: RGB
    accent_soft: RGB
    void: RGB

    def as_dict(self) -> dict[str, RGB]:
        return {f: getattr(self, f) for f in self.__annotations__}


PALETTES: dict[str, Palette] = {
    # The room you wake up in.  Warm, small and ordinary, so that everything
    # after it reads as a departure.
    "room": Palette(
        ground=(214, 176, 134), ground_b=(198, 158, 118),
        form=(232, 216, 196), form_light=(248, 238, 224), form_dark=(168, 142, 118),
        accent=(126, 168, 196), accent_soft=(182, 208, 222),
        void=(58, 46, 52),
    ),
    # Between the dreams.  Almost nothing but soft dark and the doors.
    "nexus": Palette(
        ground=(58, 52, 84), ground_b=(48, 44, 72),
        form=(84, 76, 116), form_light=(118, 108, 156), form_dark=(36, 32, 56),
        accent=(246, 214, 150), accent_soft=(196, 172, 220),
        void=(22, 20, 34),
    ),
    # Endless pink brick.  Every hallway nearly identical, almost no landmarks.
    "pink": Palette(
        ground=(232, 186, 196), ground_b=(220, 170, 182),
        form=(226, 158, 176), form_light=(244, 194, 204), form_dark=(178, 114, 138),
        accent=(250, 240, 236), accent_soft=(206, 140, 164),
        void=(120, 70, 96),
    ),
    # A landscape made of oversized digits.  Nothing acknowledges this.
    "numbers": Palette(
        ground=(168, 210, 198), ground_b=(150, 196, 186),
        form=(246, 240, 220), form_light=(255, 252, 240), form_dark=(150, 160, 152),
        accent=(240, 154, 96), accent_soft=(120, 172, 168),
        void=(52, 84, 84),
    ),
    # Children's building blocks at building scale.
    "blocks": Palette(
        ground=(186, 176, 214), ground_b=(170, 160, 202),
        form=(228, 128, 124), form_light=(244, 168, 160), form_dark=(160, 84, 92),
        accent=(120, 176, 226), accent_soft=(238, 206, 126),
        void=(74, 66, 104),
    ),
    # Floating staircases and nothing else at all.
    "stairs": Palette(
        ground=(58, 66, 104), ground_b=(48, 56, 92),
        form=(208, 206, 216), form_light=(238, 238, 244), form_dark=(132, 132, 152),
        accent=(250, 224, 156), accent_soft=(150, 160, 200),
        void=(24, 28, 52),
    ),
    # Pale empty sand.  The silence matters more than the visuals.
    "sand": Palette(
        ground=(238, 230, 210), ground_b=(228, 218, 196),
        form=(214, 202, 180), form_light=(248, 242, 228), form_dark=(178, 164, 144),
        accent=(120, 128, 148), accent_soft=(206, 210, 216),
        void=(196, 198, 204),
    ),
    # A peaceful forest.  The trunks are smiling.  None of them move.
    "faces": Palette(
        ground=(126, 166, 118), ground_b=(110, 150, 106),
        form=(150, 112, 84), form_light=(184, 146, 112), form_dark=(102, 74, 58),
        accent=(244, 232, 206), accent_soft=(92, 132, 96),
        void=(46, 70, 54),
    ),
    # Enormous stone hands coming out of a field.
    "hands": Palette(
        ground=(158, 176, 130), ground_b=(142, 162, 118),
        form=(206, 198, 196), form_light=(232, 226, 224), form_dark=(150, 140, 144),
        accent=(226, 196, 156), accent_soft=(120, 140, 108),
        void=(72, 86, 70),
    ),
    # Checkerboard country, with the occasional small house in the middle of it.
    "checker": Palette(
        ground=(236, 232, 224), ground_b=(88, 86, 92),
        form=(202, 198, 192), form_light=(240, 238, 234), form_dark=(122, 118, 118),
        accent=(198, 84, 78), accent_soft=(150, 148, 152),
        void=(48, 46, 50),
    ),
    # You are very small and the crayons are pillars.
    "toys": Palette(
        ground=(246, 224, 186), ground_b=(236, 210, 170),
        form=(232, 130, 132), form_light=(248, 176, 172), form_dark=(176, 90, 100),
        accent=(122, 190, 200), accent_soft=(248, 214, 118),
        void=(126, 96, 84),
    ),
    # A black void covered in enormous glowing scrawl.  No sky, no ground.
    "neon": Palette(
        ground=(22, 20, 34), ground_b=(30, 26, 44),
        form=(96, 240, 226), form_light=(190, 252, 246), form_dark=(40, 120, 130),
        accent=(244, 118, 196), accent_soft=(180, 138, 246),
        void=(10, 8, 16),
    ),
    # A forest where the trees are umbrellas.
    "umbrellas": Palette(
        ground=(126, 156, 156), ground_b=(112, 142, 144),
        form=(198, 96, 96), form_light=(224, 140, 132), form_dark=(140, 66, 74),
        accent=(242, 208, 130), accent_soft=(104, 132, 176),
        void=(56, 76, 82),
    ),
    # An ocean made of stars.
    "stars": Palette(
        ground=(40, 44, 92), ground_b=(32, 36, 78),
        form=(70, 78, 140), form_light=(120, 130, 196), form_dark=(24, 26, 58),
        accent=(252, 248, 226), accent_soft=(160, 200, 240),
        void=(14, 14, 34),
    ),

    # --- the grove, on its other three channels ------------------------------
    #
    # These are not other places.  They are the same town received differently,
    # so each one is built from the grove's palette with one thing done to it,
    # and the relationships between the colours are preserved exactly: whatever
    # was the brightest thing in the grove is still the brightest thing here.

    # OVERGROWN.  The growth never stopped.  Everything green is greener and
    # everything that was not green has had green put on it; the only colour
    # left that is not a leaf is the one lane marking still showing through.
    "faces2": Palette(
        ground=(96, 158, 92), ground_b=(78, 138, 78),
        form=(112, 104, 62), form_light=(150, 152, 78), form_dark=(52, 66, 40),
        accent=(176, 214, 118), accent_soft=(56, 122, 74),
        void=(20, 46, 28),
    ),
    # OFF-COLOUR.  The colour is draining out of the signal from the greens
    # inwards, which is why the concrete survives best: it had least to lose.
    # Nothing here is warm.  What green remains reads as damp, not alive.
    "faces3": Palette(
        ground=(146, 152, 144), ground_b=(130, 136, 130),
        form=(140, 138, 132), form_light=(186, 186, 180), form_dark=(84, 86, 84),
        accent=(226, 230, 232), accent_soft=(112, 126, 118),
        void=(52, 56, 58),
    ),
    # NO SIGNAL.  Not a place any more — the pattern a transmitter sends when
    # it has nothing to send, with the town still faintly legible underneath.
    # Test-card red, test-card white, and the black between the bars.
    "faces4": Palette(
        ground=(42, 20, 24), ground_b=(30, 15, 19),
        form=(206, 58, 54), form_light=(242, 128, 106), form_dark=(96, 22, 28),
        accent=(240, 236, 226), accent_soft=(74, 128, 148),
        void=(18, 10, 14),
    ),

    # --- inside the murals -------------------------------------------------
    #
    # Four paintings on the floor of the scrawl world, each of which is also a
    # way in.  A mural is drawn in two or three colours, so its interior gets
    # those two or three colours and no others — the discipline is the point.
    # Walking into a painting should feel like the world has been reduced to
    # what the painting had, not like another room with a filter on it.

    # THE EYE.  Cyan and white on black, concentric, and it does not blink.
    "neon2": Palette(
        ground=(10, 26, 34), ground_b=(14, 36, 46),
        form=(96, 240, 226), form_light=(214, 254, 250), form_dark=(20, 96, 108),
        accent=(240, 252, 250), accent_soft=(46, 158, 176),
        void=(4, 10, 14),
    ),
    # THE SPIRAL.  Magenta into violet, and it only goes one way.
    "neon3": Palette(
        ground=(26, 10, 34), ground_b=(36, 14, 48),
        form=(244, 118, 196), form_light=(254, 200, 234), form_dark=(112, 30, 96),
        accent=(180, 138, 246), accent_soft=(140, 54, 158),
        void=(12, 4, 18),
    ),
    # THE MOUTH.  Hot red on near-black, and everything in it is a tooth.
    "neon4": Palette(
        ground=(30, 8, 12), ground_b=(42, 12, 16),
        form=(250, 90, 96), form_light=(255, 190, 176), form_dark=(120, 22, 34),
        accent=(255, 236, 220), accent_soft=(168, 40, 62),
        void=(12, 2, 6),
    ),
    # THE STAR.  Gold and white, radial, with nothing at all in between.
    "neon5": Palette(
        ground=(28, 24, 8), ground_b=(38, 32, 12),
        form=(252, 210, 84), form_light=(255, 246, 200), form_dark=(122, 92, 20),
        accent=(255, 252, 236), accent_soft=(198, 142, 44),
        void=(10, 8, 2),
    ),

    # --- the ascent --------------------------------------------------------
    #
    # Four planes above the umbrella forest, and the palette does the whole
    # argument on its own: the colour drains, the contrast climbs, and the
    # warm accent that made the first plane feel like an arrival is gone by
    # the third.  What is left at the top is a very well-lit filing system.

    # The cloud.  Soft, bright, pale, high — and laying it on slightly thick.
    "umbrellas2": Palette(
        ground=(232, 236, 242), ground_b=(214, 222, 234),
        form=(250, 250, 252), form_light=(255, 255, 255), form_dark=(186, 196, 212),
        accent=(252, 226, 170), accent_soft=(198, 214, 238),
        void=(246, 248, 252),
    ),
    # Ordered, and less kind.  The soft edges have gone square.
    "umbrellas3": Palette(
        ground=(214, 218, 220), ground_b=(196, 202, 206),
        form=(236, 238, 238), form_light=(252, 252, 252), form_dark=(160, 168, 174),
        accent=(232, 214, 178), accent_soft=(176, 190, 200),
        void=(228, 232, 234),
    ),
    # Uniform.  Everything is the same size as everything else.
    "umbrellas4": Palette(
        ground=(196, 198, 196), ground_b=(180, 184, 182),
        form=(220, 222, 220), form_light=(240, 242, 240), form_dark=(140, 146, 148),
        accent=(206, 202, 190), accent_soft=(158, 168, 172),
        void=(206, 208, 206),
    ),
    # Administrative, with very good lighting.
    "umbrellas5": Palette(
        ground=(176, 178, 174), ground_b=(162, 164, 162),
        form=(206, 206, 202), form_light=(248, 248, 246), form_dark=(118, 122, 124),
        accent=(188, 188, 182), accent_soft=(140, 146, 148),
        void=(184, 186, 184),
    ),
}
