"""Generates the game's music and sound with ElevenLabs.

Two endpoints do the work: ``/v1/music`` for the world themes and
``/v1/sound-generation`` for everything short.  Both return MP3, which is then
post-processed into what RPG Maker actually wants:

* **Music** is crossfade-looped.  A generated track has a beginning and an end,
  and a walking simulator needs neither — so the tail is folded back over the
  head, which removes the seam and shortens the file at the same time.
* **Everything** is converted to Ogg Vorbis at a low bitrate.  EasyRPG plays
  ogg natively, and the compression is part of the aesthetic rather than a
  compromise.

Results are cached by a hash of the request, so re-running a build does not
re-generate (or re-bill) anything that has not changed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

API_ROOT = "https://api.elevenlabs.io/v1"
CACHE_DIR = os.environ.get(
    "LIMINAL_AUDIO_CACHE",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "audio_cache"))


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set; export it before building audio")
    return key


@dataclass(frozen=True)
class Music:
    """One looping world theme."""
    name: str
    prompt: str
    seconds: int = 45
    loop_overlap: float = 4.0     # how much tail is folded back over the head
    gain: float = 1.0


@dataclass(frozen=True)
class Sfx:
    name: str
    prompt: str
    seconds: float = 2.0
    influence: float = 0.55
    loop: bool = False
    gain: float = 1.0


# --- the score ---------------------------------------------------------------
# One theme per world.  Each prompt names the instrument palette, the emotion
# and the negative space, and every one of them forbids drums and vocals — a
# beat would give these places a pulse they are not supposed to have.

_NO = ("no drums, no percussion loop, no vocals, no speech, no build-up, "
       "no climax, steady and unchanging throughout")

MUSIC: list[Music] = [
    Music("Room",
          "Very quiet lo-fi ambient loop for a small bedroom at an unclear hour. "
          "Soft detuned music box playing four slow notes, warm tape hiss, distant "
          "room tone, gentle low pad underneath. Safe but hollow, like a memory of "
          f"a room rather than a room. Nostalgic, melancholy, extremely sparse. {_NO}."),
    Music("Nexus",
          "Slow dark ambient loop for an endless corridor of doors in a void. "
          "Deep sub drone, distant reverberant bell every few bars, faint choir pad "
          "far away, tape wobble. Patient, expectant, not frightening. Enormous "
          f"empty space. {_NO}."),
    Music("Pink",
          "Hypnotic lo-fi ambient loop for an infinite maze of soft pink brick. "
          "Detuned celesta repeating the same gentle five-note motif over and over, "
          "long plate reverb, faint tape flutter, quiet warm drone underneath. "
          f"Dreamlike repetition, mild unease, pastel and endless. {_NO}."),
    Music("Numbers",
          "Ambient loop for a landscape built from enormous floating digits. "
          "Metronomic muted marimba and small bells counting in an irregular cycle, "
          "whole-tone scale, cold clean reverb, faint electrical hum. Precise, "
          f"impersonal, quietly absurd. {_NO}."),
    Music("Blocks",
          "Gentle wonky ambient loop for a country made of giant children's "
          "building blocks. Slightly out-of-tune toy piano and soft mallets playing "
          "a simple major pentatonic phrase, tape warble, warm lo-fi. Playful but "
          f"lonely, like a nursery nobody is in. {_NO}."),
    Music("Stairs",
          "Ambient loop of an endlessly rising Shepard tone for a dimension of "
          "floating staircases in empty space. Slowly ascending sine and string "
          "pads that never arrive, cold wide reverb, faint high shimmer. Vertigo, "
          f"awe, infinite ascent. {_NO}."),
    Music("Sand",
          "Almost-silent ambient loop for a vast pale empty desert. Mostly soft "
          "wind and room tone, one distant sustained tone appearing rarely, very "
          "long reverb tails, huge negative space. Loneliness and scale. Barely "
          f"any musical content at all. {_NO}."),
    Music("Faces",
          "Pastoral lo-fi ambient loop for a quiet forest where the tree trunks "
          "have carved smiling faces. Soft nylon guitar harmonics and warm flute "
          "pad in lydian mode, gentle tape hiss, birdsong far away and slightly "
          f"wrong. Peaceful, nostalgic, faintly uncanny. {_NO}."),
    # The grove's other three receptions.  One town, four carriers, and the
    # music is the fastest thing the player will read: it tells them what kind
    # of reception this is before they have looked at a single tile.
    Music("Overgrown",
          "Bright pastoral lo-fi ambient loop for a town the forest has taken "
          "back completely, and which is delighted about it. Warm nylon guitar "
          "and flute in lydian, major and unclouded, layered birdsong, sun "
          "through leaves. Upbeat and liminal — a little too pleased with "
          "itself, slightly too sweet, as though it is performing "
          f"contentment. Never sinister, never loud. {_NO}."),
    Music("OffColour",
          "Sad, sparse ambient loop for the same town with the colour going "
          "out of it. One muted felt piano figure repeating with long gaps, "
          "faint tape hiss, distant room tone, a low pad that never resolves. "
          "Empty corridors, fluorescent afternoons, the feeling of a place "
          "still running with nobody left to run it. Quietly grieving rather "
          f"than frightening. {_NO}.", seconds=35),
    Music("NoSignal",
          "Dark oppressive ambient loop for a broadcast that has stopped "
          "carrying a picture. Heavy detuned sub drone, slow metallic groan "
          "far below, brief bursts of filtered static swelling and receding, "
          "hollow reverb, occasional low sustained horn-like tone that sounds "
          "almost like a voice. Dread, wrongness, something aware on the "
          f"other end. Never a jumpscare — a long unbroken threat. {_NO}.",
          seconds=40),
    Music("Hands",
          "Slow monumental ambient loop for a grassy plain with enormous stone "
          "hands rising out of the earth. Deep slow choir pad and low strings "
          "moving between two chords, stone-hall reverb, distant wind. Solemn, "
          f"ancient, unexplained. {_NO}."),
    Music("Checker",
          "Clockwork ambient loop for a checkerboard landscape with isolated "
          "little houses. Two chords alternating forever on muted vibraphone, soft "
          "mechanical ticking, cold clean space. Orderly, obsessive, and empty. "
          f"{_NO}."),
    Music("Toys",
          "Warped music box loop for a room where the player is tiny and the "
          "crayons are pillars. Old music box with heavy tape wobble and pitch "
          "drift, soft childhood melody slightly too slow, dusty lo-fi. Nostalgia "
          f"tipping into unease. {_NO}."),
    Music("Neon",
          "Throbbing lo-fi synth ambient loop for a black void covered in "
          "enormous glowing graffiti. Detuned analogue saw pad pulsing slowly, "
          "bright neon arpeggio far in the background, tape saturation. Electric, "
          f"psychedelic, hypnotic. {_NO}."),
    Music("Umbrellas",
          "Ambient loop for a forest where the trees are umbrellas and it is not "
          "raining. Soft granular rain-like texture with no actual rain, warm "
          "muted piano chords, deep reverb, tape hiss. Melancholy, gentle, waiting "
          f"for weather that never comes. {_NO}."),
    Music("Stars",
          "Shimmering ambient loop for an ocean made of stars. Glassy high sine "
          "pads, slow sub bass swell, sparse twinkling bell tones, enormous "
          f"reverberant space. Weightless, awed, cold and beautiful. {_NO}."),
    Music("Title",
          "Very slow title-screen ambient loop: a single door ajar in a dark "
          "room. One distant detuned bell motif, deep warm drone, long reverb, "
          f"tape hiss. Inviting and slightly sad. {_NO}.", seconds=40),
    Music("Menu",
          "Quiet lo-fi ambient bed for a dream-diary menu screen. Soft warm pad, "
          "faint music box, tape hiss, very slow movement. Intimate and small. "
          f"{_NO}.", seconds=30),
    Music("Deep",
          "Very low ambient loop for a hidden layer beneath a dream. Sub bass "
          "drone, reversed cymbal swells far away, muffled as though heard through "
          f"a floor, heavy tape degradation. Submerged and secret. {_NO}."),
    Music("Wrong",
          "Unsettling ambient loop for a place that has changed while you were "
          "away. Detuned strings sliding microtonally, reversed piano, tape "
          f"dropouts, hollow reverb. Wrong but never loud. {_NO}.", seconds=35),
]


SFX: list[Sfx] = [
    # interface
    Sfx("Cursor", "a very soft short muted wooden tick, quiet UI blip", 0.5, 0.7),
    Sfx("Decision", "a soft warm low chime, gentle confirmation, short reverb", 1.0),
    Sfx("Cancel", "a short soft muted thud, quiet UI back sound", 0.7),
    Sfx("Buzzer", "a very short dull muted buzz, quiet and soft, not harsh", 0.6),
    Sfx("MenuOpen",
        "a soft mechanical iris opening, quiet shutter unfolding, tape texture", 1.2),
    Sfx("MenuClose", "a soft mechanical iris closing, quiet shutter folding shut", 1.0),
    # world interaction
    Sfx("ItemGet",
        "a gentle bright bell shimmer with soft reverb, something found in a "
        "dream, warm and small", 1.8),
    Sfx("DoorOpen",
        "an old wooden door opening slowly in a large empty room, soft creak, "
        "long reverb", 2.5),
    Sfx("DoorShut", "an old wooden door closing softly in a large empty room", 2.0),
    Sfx("StepSoft", "a single soft footstep on carpet in an empty room", 0.5, 0.7),
    Sfx("StepStone", "a single footstep on cold stone in a huge empty hall", 0.8, 0.7),
    Sfx("WaterStep", "a single soft footstep in very shallow still water", 0.8, 0.7),
    # atmosphere and events
    Sfx("Heartbeat", "two slow muffled heartbeats heard from inside the chest",
        2.0, 0.6),
    Sfx("StaticBurst", "a short burst of analogue television static, tape noise",
        1.2, 0.7),
    Sfx("ChimeFar",
        "a single distant bell heard across a huge empty space, very long reverb",
        3.5),
    Sfx("WindGust", "a soft low wind gust across an empty pale desert", 3.0),
    Sfx("GlassRing", "a single high glass tone ringing and slowly fading", 2.5),
    Sfx("LowThud", "a deep soft muffled impact felt through a floor", 1.5),
    Sfx("TapeStop", "an old tape player stopping abruptly, mechanical clunk", 1.0),
    Sfx("Breath", "one slow quiet human exhale in a small room", 1.5),
    Sfx("WaterDrop", "a single water drop falling into still water, tiled room echo",
        1.5),
    Sfx("Rustle", "soft leaves rustling briefly with no wind", 1.5),
    Sfx("Wrong",
        "a short reversed piano note with tape wobble, quietly unsettling", 2.0),
    Sfx("Appear",
        "a soft reversed shimmer, something arriving quietly, dreamlike", 2.0),
    Sfx("Vanish", "a soft short descending shimmer, something leaving quietly", 1.8),
    Sfx("Watch",
        "a very quiet low sustained tone that feels like being noticed", 2.5),
    # the grove's four channels.  The ring is the only instruction the world
    # ever gives, so it has to be unmistakable and it has to have a direction.
    Sfx("PhoneFar",
        "an old payphone ringing somewhere out of sight in a wood, two rings, "
        "muffled by distance and leaves, damp reverb, no music", 2.6),
    Sfx("PhoneNear",
        "an old mechanical payphone bell ringing once, very close, metallic "
        "and loud in a small glass box", 1.4),
    Sfx("Coin",
        "a single coin dropping through a payphone and landing in the metal "
        "coin return, small hollow clatter", 1.2),
    Sfx("TapeRoll",
        "a cassette player starting: mechanism engaging, capstan spinning up, "
        "tape hiss rising, no music", 2.2),
    Sfx("Latch",
        "a small metal inspection hatch unlocking and swinging open, cold "
        "and mechanical, outdoors", 1.6),
    Sfx("Filament",
        "an old street lamp warming on: a mains hum rising, glass ticking as "
        "the filament heats", 2.4),
    Sfx("Carrier",
        "a steady analogue test tone with television static underneath it, "
        "as heard from outside a building", 3.0),
    Sfx("Tune",
        "an analogue television changing channel: a swallow of static, a "
        "hard click, then the new picture settling", 1.8),
]


# --- generation --------------------------------------------------------------

def _post(path: str, payload: dict, timeout: int = 420) -> bytes:
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": api_key(), "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _cache_path(kind: str, name: str, payload: dict) -> str:
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{kind}_{name}_{digest}.mp3")


def _ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


# Mastering.  The first pass applied a bare volume multiplier and nothing
# else, and the generator hands back material with a great deal of energy
# below 80Hz — the result was tracks that measured fine and physically hurt on
# headphones.  Everything now goes through the same chain:
#
#   highpass    everything under 70Hz is rumble this game has no use for, and
#               it is most of what was making the low end feel "boosted"
#   lowshelf    a further 4dB off the bottom two octaves, because ambient pads
#               generated from a text prompt are reliably bass-heavy
#   loudnorm    one integrated target for every track, so no world is louder
#               than its neighbour and nothing has to be ridden on the mixer
#   alimiter    a true-peak ceiling well under full scale, so the quiet game
#               has headroom and nothing ever clips into the ear
#
# Music sits quieter than the effects: it is a bed, not an event.
MUSIC_LUFS = -20.0
SFX_LUFS = -16.0
PEAK = 0.89


def _master(gain: float, lufs: float) -> str:
    return ",".join([
        f"volume={gain:.3f}",
        "highpass=f=70:poles=2",
        "lowshelf=f=160:g=-4",
        f"loudnorm=I={lufs}:TP=-2.0:LRA=9",
        f"alimiter=limit={PEAK}:level=disabled",
    ])


def _to_ogg(source: str, target: str, *, quality: int = 2, gain: float = 1.0,
            mono: bool = False, rate: int = 32000,
            lufs: float = SFX_LUFS) -> None:
    args = ["-i", source, "-af", _master(gain, lufs), "-ar", str(rate)]
    if mono:
        args += ["-ac", "1"]
    args += ["-c:a", "libvorbis", "-q:a", str(quality), target]
    _ffmpeg(args)


def _loop_music(source: str, target: str, overlap: float, gain: float) -> None:
    """Fold the tail back over the head so the track has no seam.

    The last ``overlap`` seconds are faded out and mixed on top of the first
    ``overlap`` seconds faded in; the result is trimmed to end exactly where
    the crossfade began, so playing it end-to-start is continuous.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", source],
        capture_output=True, text=True, check=True)
    duration = float(probe.stdout.strip())
    overlap = max(0.5, min(overlap, duration / 3))
    body = duration - overlap

    with tempfile.TemporaryDirectory() as tmp:
        head = os.path.join(tmp, "head.wav")
        tail = os.path.join(tmp, "tail.wav")
        mixed = os.path.join(tmp, "mixed.wav")
        # everything except the final overlap
        _ffmpeg(["-i", source, "-t", f"{body:.3f}", "-c:a", "pcm_s16le", head])
        # the final overlap, faded out
        _ffmpeg(["-i", source, "-ss", f"{body:.3f}",
                 "-af", f"afade=t=out:st=0:d={overlap:.3f}",
                 "-c:a", "pcm_s16le", tail])
        # lay the faded tail over the (faded-in) start of the body
        _ffmpeg(["-i", head, "-i", tail, "-filter_complex",
                 f"[0:a]afade=t=in:st=0:d={overlap:.3f}[a];"
                 f"[a][1:a]amix=inputs=2:duration=first:dropout_transition=0,"
                 f"volume=2.0[out]",
                 "-map", "[out]", "-c:a", "pcm_s16le", mixed])
        _to_ogg(mixed, target, quality=1, gain=gain, lufs=MUSIC_LUFS)


def generate_music(spec: Music, out_dir: str, *, force: bool = False) -> str:
    payload = {"prompt": spec.prompt, "music_length_ms": spec.seconds * 1000}
    cache = _cache_path("music", spec.name, payload)
    if force or not os.path.exists(cache) or os.path.getsize(cache) == 0:
        # Fetch first, then write: opening the file up front would leave a
        # zero-byte cache entry behind whenever a request failed, and that
        # empty file would then be treated as a valid cache hit forever.
        audio = _post("/music", payload)
        with open(cache, "wb") as handle:
            handle.write(audio)
    target = os.path.join(out_dir, f"{spec.name}.ogg")
    _loop_music(cache, target, spec.loop_overlap, spec.gain)
    return target


def generate_sfx(spec: Sfx, out_dir: str, *, force: bool = False) -> str:
    payload = {
        "text": spec.prompt,
        "duration_seconds": spec.seconds,
        "prompt_influence": spec.influence,
    }
    if spec.loop:
        payload["loop"] = True
    cache = _cache_path("sfx", spec.name, payload)
    if force or not os.path.exists(cache) or os.path.getsize(cache) == 0:
        audio = _post("/sound-generation", payload)
        with open(cache, "wb") as handle:
            handle.write(audio)
    target = os.path.join(out_dir, f"{spec.name}.ogg")
    _to_ogg(cache, target, quality=0, gain=spec.gain, mono=True, rate=22050)
    return target


def build_all(music_dir: str, sound_dir: str, *, workers: int = 4,
              force: bool = False) -> dict[str, list[str]]:
    """Generate everything, in parallel, reusing the cache where possible."""
    os.makedirs(music_dir, exist_ok=True)
    os.makedirs(sound_dir, exist_ok=True)
    made: dict[str, list[str]] = {"music": [], "sound": []}
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        music_jobs = {pool.submit(generate_music, spec, music_dir, force=force): spec
                      for spec in MUSIC}
        sfx_jobs = {pool.submit(generate_sfx, spec, sound_dir, force=force): spec
                    for spec in SFX}
        for job, spec in music_jobs.items():
            try:
                made["music"].append(job.result())
                print(f"  music  {spec.name}")
            except Exception as exc:                      # noqa: BLE001
                errors.append(f"music {spec.name}: {exc}")
        for job, spec in sfx_jobs.items():
            try:
                made["sound"].append(job.result())
                print(f"  sound  {spec.name}")
            except Exception as exc:                      # noqa: BLE001
                errors.append(f"sfx {spec.name}: {exc}")

    if errors:
        print("\n".join(f"  FAILED {line}" for line in errors))
    return made


if __name__ == "__main__":
    import sys

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    build_all(os.path.join(root, "game", "Music"),
              os.path.join(root, "game", "Sound"),
              force="--force" in sys.argv)
