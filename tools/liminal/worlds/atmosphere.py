"""What each world does to the screen, and to you, while you walk in it.

Colour grading told you where you were before you consciously registered why.
This is the rest of that job: how the world *arrives*, how it moves while you
stand still, what the air is doing, and what the ground sounds like underfoot.

Four instruments, all of them the engine's own:

**transition**  RPG Maker has twenty ways to erase the screen and twenty to
                restore it — blinds, mosaic, an iris, a wave, a vertical
                scroll, random blocks. One fade for every world wastes
                nineteen of them.
**camera**      a locked pan is a held breath; a continuous shake at power one
                is a tremor you feel rather than see; a slow drift makes a
                still screen refuse to settle.
**film**        the overlay picture each world already wears, given the
                engine's continuous wave or rotation so it moves on its own
                clock rather than the interpreter's.
**footing**     the terrain id under the player, read every step, chooses the
                sound. A world with one footstep sound is a world with one
                surface, whatever the art says.

The rule from the roadmap still holds: **effects run at a whisper during
ordinary walking.** A world that is constantly distorting has nothing left for
the moment that matters. Everything here is tuned low enough that a player
would struggle to name it and would notice immediately if it stopped.
"""

from __future__ import annotations

from dataclasses import dataclass

# rpg::EventCommand ERASE/SHOW transition indices, in the order the engine
# lists them.  Named because "fade_out(11)" tells nobody anything.
FADE, RANDOM_BLOCKS, BLOCKS_DOWN, BLOCKS_UP = 0, 1, 2, 3
BLINDS, STRIPES_VERT, STRIPES_HORZ, OUT_TO_IN = 4, 5, 6, 7
IN_TO_OUT, SCROLL_UP, SCROLL_DOWN, SCROLL_LEFT = 8, 9, 10, 11
SCROLL_RIGHT, DIVIDE_HORZ, DIVIDE_VERT, DIVIDE_QUAD = 12, 13, 14, 15
ZOOM, MOSAIC, WAVER, INSTANT = 16, 17, 18, 19

# Weather kinds.
CLEAR, RAIN, SNOW, FOG, SAND_STORM = 0, 1, 2, 3, 4

# Picture effect modes.
STILL, ROTATE, WAVE = 0, 1, 2

# Pan directions.
PAN_UP, PAN_RIGHT, PAN_DOWN, PAN_LEFT = 0, 1, 2, 3


@dataclass(frozen=True)
class Atmosphere:
    """One world's behaviour, as data rather than as duplicated script."""
    enter: int = FADE          # how the world assembles when you arrive
    leave: int = FADE          # how it comes apart when you go
    film: int = STILL          # what the overlay picture does, forever
    film_power: int = 0
    shake: tuple[int, int] | None = None      # (strength, speed), continuous
    drift: tuple[int, int, int] | None = None  # (direction, distance, speed)
    weather: tuple[int, int] | None = None     # (kind, strength)
    # Which sound each terrain plays underfoot.  Terrain ids come from the
    # chipset: 1 floor, 2 water, 3 carpet, 4 grass, 5 concrete.
    steps: tuple[str, ...] = ("StepSoft",)
    step_volume: int = 22


# The whisper settings.  Nothing here is allowed to be loud.
ATMOSPHERE: dict[str, Atmosphere] = {
    # Home. It should feel like nothing is happening, because nothing is.
    "room": Atmosphere(enter=FADE, leave=MOSAIC, film=STILL,
                       steps=("StepSoft", "StepSoft", "Rustle")),

    # The hub between. Held still — the only place in the game whose camera
    # does not move at all, so arriving here reads as a pause.
    "nexus": Atmosphere(enter=OUT_TO_IN, leave=IN_TO_OUT, film=WAVE,
                        film_power=2, steps=("StepStone",), step_volume=18),

    # Brick. The walls close in, so the screen closes in with them.
    "pink": Atmosphere(enter=BLINDS, leave=DIVIDE_VERT, film=WAVE, film_power=3,
                       drift=(PAN_RIGHT, 1, 1),
                       steps=("StepStone", "StepStone", "StepSoft")),

    # Counting. Blocks, in and out, like something being tallied.
    "numbers": Atmosphere(enter=BLOCKS_DOWN, leave=BLOCKS_UP, film=STILL,
                          shake=(1, 1), steps=("StepStone",), step_volume=20),

    # The nursery. Everything is bright and a little unstable.
    "blocks": Atmosphere(enter=RANDOM_BLOCKS, leave=RANDOM_BLOCKS, film=WAVE,
                         film_power=4, shake=(1, 2),
                         steps=("StepSoft", "LowThud")),

    # Up. The screen scrolls up as you arrive and up again as you leave: you
    # never come back down, whatever the stairs are doing.
    "stairs": Atmosphere(enter=SCROLL_UP, leave=SCROLL_UP, film=STILL,
                         drift=(PAN_UP, 2, 1),
                         steps=("StepStone", "StepStone", "GlassRing"),
                         step_volume=26),

    # Nothing much. It blows in and blows out, and the air is full of it.
    "sand": Atmosphere(enter=MOSAIC, leave=MOSAIC, film=WAVE, film_power=5,
                       weather=(FOG, 1), drift=(PAN_LEFT, 3, 1),
                       steps=("StepSoft",), step_volume=16),

    # The grove. Light through leaves: it wavers going in and going out.
    "faces": Atmosphere(enter=WAVER, leave=WAVER, film=WAVE, film_power=3,
                        steps=("Rustle", "Rustle", "StepStone"),
                        step_volume=24),

    # The field. Nothing moves here at all, and that is the effect.
    "hands": Atmosphere(enter=IN_TO_OUT, leave=OUT_TO_IN, film=STILL,
                        steps=("StepStone",), step_volume=20),

    # Squares. Divides into quarters, because of course it does.
    "checker": Atmosphere(enter=DIVIDE_QUAD, leave=DIVIDE_QUAD, film=STILL,
                          shake=(1, 1), steps=("StepStone", "GlassRing"),
                          step_volume=22),

    # Small. Everything trembles slightly, the way a toy does when walked past.
    "toys": Atmosphere(enter=ZOOM, leave=ZOOM, film=WAVE, film_power=4,
                       shake=(1, 3), steps=("LowThud", "StepSoft"),
                       step_volume=26),

    # Scrawl. The loudest world, and the only one allowed to be.
    "neon": Atmosphere(enter=STRIPES_HORZ, leave=STRIPES_VERT, film=WAVE,
                       film_power=7, shake=(1, 4), drift=(PAN_RIGHT, 2, 2),
                       steps=("StaticBurst", "StepStone"), step_volume=18),

    # No rain. It is damp, and the screen is damp with it.
    "umbrellas": Atmosphere(enter=SCROLL_DOWN, leave=SCROLL_DOWN, film=WAVE,
                            film_power=4, weather=(RAIN, 1),
                            steps=("WaterStep", "WaterDrop", "StepSoft"),
                            step_volume=20),

    # The shallows. Everything ripples, slowly, all the time.
    "stars": Atmosphere(enter=DIVIDE_HORZ, leave=DIVIDE_HORZ, film=WAVE,
                        film_power=6, drift=(PAN_DOWN, 1, 1),
                        steps=("WaterStep", "WaterStep", "WaterDrop"),
                        step_volume=18),
}


def of(key: str) -> Atmosphere:
    return ATMOSPHERE.get(key, Atmosphere())
