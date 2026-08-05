# LIMINAL

A walking simulator for the EasyRPG Player, built as an RPG Maker 2000 game.
No combat, no objectives, no explanation. Fourteen places, a diary of effects
you find in them, and a great deal that most players will never see.

Every asset is generated: tiles, sprites, interface and screen overlays are
drawn from code in `tools/liminal/art`, and the soundtrack and sound effects
are generated through ElevenLabs and post-processed into seamless loops.

## Reading order

Start with [`docs/GOLDEN_RULE.md`](docs/GOLDEN_RULE.md). It is the design
contract every world is held to, and it exists because an earlier draft of
this project failed it.

## Layout

    tools/liminal/
      art/          every pixel in the game, generated
        canvas.py     drawing primitives
        palette.py    one closed palette per world
        chipsets.py   tiles, boundaries, murals, animated surfaces
        sheets.py     per-world chipset assembly
        charsets.py   sprite construction
        cast.py       who lives in each dream
        menu.py       the dream diary
        ui.py         window skin, title, screen overlays
      audio/
        elevenlabs.py generation, crossfade looping, ogg encoding
        dsp.py        synthesis fallback
      worlds/
        layout.py     dream architecture: zones, boundaries, corridors
        rooms.py      per-room furnishing
        worlds.py     the fourteen places
        systems.py    common events: arrival, loop watch, diary, rare events
      lcfxml.py       liblcf XML emitter
      cmds.py         event scripting
      db.py / maps.py database and map construction

## Building

The data files are produced by converting generated XML through `lcf2xml`
from [liblcf](https://github.com/EasyRPG/liblcf):

    export ELEVENLABS_API_KEY=...        # only needed to regenerate audio
    python3 tools/build.py

Audio is cached in `assets/audio_cache` keyed by a hash of each request, so
rebuilding does not regenerate anything that has not changed.

## Playing

Point [EasyRPG Player](https://easyrpg.org/player/) at the **`game/`**
directory — not at the repository root.

    easyrpg-player --project-path game

The root is a source checkout, not a project. Opening it in the Player used to
find a stub `RPG_RT.ldb` left over from the first day of the project and play
*that* instead: a single grey map, a sprite called `Hero`, and the words
"hello there". Those files are gone, so the Player now correctly refuses the
root rather than quietly playing something else.

## Controls

Arrow keys walk. Enter interacts. Shift opens the diary. Escape opens the
engine menu. There is nothing to win.
