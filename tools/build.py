#!/usr/bin/env python3
"""Assemble LIMINAL into a folder EasyRPG Player will open.

One command, start to finish:

    art  ->  PNG  ->  world generation  ->  event authoring  ->  LCF  ->  game/

Everything upstream of this script has been written, rendered and measured
without the engine ever seeing it.  This is the first point at which any of it
becomes a game, so the script is deliberately loud: it reports what it wrote,
and it round-trips every binary it produces back through ``lcf2xml`` on the
way out.  A file that will not re-read is a file the Player will refuse to
load, and the Player refuses silently.

Usage::

    python3 tools/build.py                 # everything
    python3 tools/build.py --skip-art      # maps and data only, much faster
    python3 tools/build.py --no-verify     # skip the round-trip
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from liminal import db, keys, state, validate                    # noqa: E402
from liminal.art import cast, menu, ui                           # noqa: E402
from liminal.art.canvas import save_indexed                      # noqa: E402
from liminal.maps import MapInfo, build_treemap                  # noqa: E402
from liminal.worlds import (ascent, events, grove, hills_events,  # noqa: E402
                            murals, systems, worlds as W)         # noqa: E402

GAME = ROOT / "game"

# Directories RPG Maker looks in.  Music and Sound already hold the generated
# soundtrack, so they are never cleared.
ASSET_DIRS = ["ChipSet", "CharSet", "Picture", "System", "Title", "GameOver",
              "FaceSet", "Panorama", "Backdrop", "Movie", "Battle", "Monster",
              "System2", "Battle2", "BattleCharSet", "BattleWeapon", "Frame"]
GENERATED_DIRS = ["ChipSet", "CharSet", "Picture", "System", "Title", "GameOver"]

# Built out of tree, in the scratch space, because it is 40MB of C++.
LCF2XML_CANDIDATES = [
    ROOT / "tools" / "bin" / "lcf2xml",
    Path("/tmp/claude-0/-home-user-Liminal/02fe31f5-4798-502e-89e5-55e7690bfc21"
         "/scratchpad/liblcf/build/lcf2xml"),
]


def find_lcf2xml() -> Path:
    for path in LCF2XML_CANDIDATES:
        if path.exists() and os.access(path, os.X_OK):
            return path
    found = shutil.which("lcf2xml")
    if found:
        return Path(found)
    raise SystemExit(
        "lcf2xml not found.  Build liblcf, or drop the binary at "
        "tools/bin/lcf2xml.")


class Timer:
    """Prints how long each stage took, because some of them are slow."""

    def __init__(self) -> None:
        self.start = time.time()
        self.mark = self.start

    def step(self, label: str) -> None:
        now = time.time()
        print(f"  {label:<44} {now - self.mark:6.2f}s")
        self.mark = now

    def total(self) -> float:
        return time.time() - self.start


# --- art ---------------------------------------------------------------------

def export_art(worlds: dict[str, W.World], timer: Timer) -> int:
    """Write every generated image as an indexed PNG with index 0 transparent."""
    count = 0

    chip_dir = GAME / "ChipSet"
    for key in W.WORLD_ORDER:
        build = worlds[key].chipset
        save_indexed(build.sheet, str(chip_dir / f"{build.name}.png"))
        count += 1
    timer.step(f"chipsets ({len(W.WORLD_ORDER)})")

    char_dir = GAME / "CharSet"
    sheets = cast.build_sheets()
    for name, sheet in sheets.items():
        save_indexed(sheet, str(char_dir / f"{name}.png"))
        count += 1
    timer.step(f"charsets ({len(sheets)})")

    pic_dir = GAME / "Picture"
    pictures: dict = {}
    pictures.update(ui.build_overlays())
    pictures.update(menu.build_menu_art())
    for name, art in pictures.items():
        save_indexed(art, str(pic_dir / f"{name}.png"))
        count += 1
    timer.step(f"pictures ({len(pictures)})")

    save_indexed(ui.system_graphic(), str(GAME / "System" / "System.png"))
    save_indexed(ui.title_screen(), str(GAME / "Title" / "Title.png"),
                 transparent=False)
    save_indexed(ui.game_over_screen(), str(GAME / "GameOver" / "GameOver.png"),
                 transparent=False)
    count += 3
    timer.step("system / title / game over")
    return count


# --- data --------------------------------------------------------------------

def build_items() -> list[db.Item]:
    """One carried thing per effect, numbered the way ``give_effect`` expects."""
    return [
        db.Item(index, name, description=line, type=db.ITEM_SWITCH,
                switch_id=state.SW_EFFECT_ACTIVE[key])
        for index, (key, name, line) in enumerate(menu.EFFECTS, start=1)
    ]


def build_skills() -> list[db.Skill]:
    """The same twelve, as menu entries under "effects"."""
    return [
        db.Skill(index, name, description=line, type=db.SKILL_SWITCH,
                 switch_id=state.SW_EFFECT_ACTIVE[key])
        for index, (key, name, line) in enumerate(menu.EFFECTS, start=1)
    ]


def build_chipsets(worlds: dict[str, W.World]) -> list[db.Chipset]:
    out = []
    for key in W.WORLD_ORDER:
        world = worlds[key]
        build = world.chipset
        out.append(db.Chipset(
            ident=world.chipset_id,
            name=build.name,
            chipset_name=build.name,
            passable_lower=build.passable_lower,
            passable_upper=build.passable_upper,
            terrain=build.terrain,
            animation_type=build.animation_type,
            animation_speed=build.animation_speed,
        ))
    return out


SYSTEM = {
    "title_music": "Title",
    # There is no game over.  The screen exists, nothing reaches it, and if
    # anything ever does it should arrive in silence.
    "gameover_music": "(OFF)",
    "system_graphic": "System",
    "title_graphic": "Title",
    "gameover_graphic": "GameOver",
    "cursor_se": "Cursor",
    "decision_se": "Decision",
    "cancel_se": "Cancel",
    "buzzer_se": "Buzzer",
    "item_se": "ItemGet",
}


def author_events(worlds: dict[str, W.World]) -> int:
    """Hang every event in the game onto its map."""
    import random
    import zlib

    for key in W.HILLS_ORDER:
        hills_events.hills_events(worlds[key], worlds,
                                  random.Random(zlib.crc32(key.encode())))
    events.room_events(worlds["room"], worlds)
    events.balcony_events(worlds["balcony"], worlds)
    for key in W.BLOCK_ORDER:
        events.block_events(worlds[key], worlds)
    events.nexus_events(worlds["nexus"], worlds)
    for key in W.DREAM_ORDER:
        rng = random.Random(zlib.crc32(f"events:{key}".encode()))
        events.dream_events(worlds[key], worlds, rng)
    # Deeper floors are not dreams: no nexus door, no effect of their own.
    for key in W.STAIR_FLOORS:
        rng = random.Random(zlib.crc32(f"events:{key}".encode()))
        events.floor_events(worlds[key], worlds, rng)
    # The grove's other three channels are layers too, but of a different kind
    # — not further in, only differently received — so they get arrival and
    # the same door out, and then all four go through the grove's own system.
    for key in W.FACE_CHANNELS[1:]:
        rng = random.Random(zlib.crc32(f"events:{key}".encode()))
        grove.channel_layer_events(worlds[key], worlds, rng)
    for key in W.FACE_CHANNELS:
        rng = random.Random(zlib.crc32(f"grove:{key}".encode()))
        grove.grove_events(worlds[key], worlds, rng)
    # The grove's hidden half: the ways in, on each channel, and the rooms
    # themselves.  Entrances go on last so they can see which tiles the town
    # has already claimed.
    from liminal.worlds import hidden
    for key in W.FACE_CHANNELS:
        rng = random.Random(zlib.crc32(f"hidden:{key}".encode()))
        hidden.entrances(worlds[key], worlds, rng)
    for key in W.HIDDEN_ORDER:
        hidden.events(worlds[key], worlds)
    # The four paintings on the floor of the scrawl world, and their insides.
    murals.entrances(worlds["neon"], worlds,
                     random.Random(zlib.crc32(b"murals")))
    for key in W.MURAL_INSIDE_ORDER:
        rng = random.Random(zlib.crc32(f"mural:{key}".encode()))
        murals.inside_events(worlds[key], worlds, rng)

    # Everything is placed; now check the player can actually get to it.
    # Forty-odd places in this codebase add an event directly, each with its
    # own idea of where its thing belongs, and none of them can see the
    # finished world.  Asking once, here, is cheaper and more reliable than
    # teaching all of them -- and whatever this cannot rescue, the validator
    # refuses to ship.
    from liminal.worlds import reach
    rehomed = []
    for key in W.WORLD_ORDER:
        rehomed += reach.rehome(worlds[key])
    if rehomed:
        print(f"  moved {len(rehomed)} unreachable events onto usable ground")
    # The ascent.  The forest at the bottom only gets the umbrellas that lift
    # you; it already has its door, its effect and its residents.
    ascent.register(worlds)
    ascent.lifts(worlds["umbrellas"], worlds,
                 random.Random(zlib.crc32(b"ascent:base")))
    for key in W.ASCENT_ORDER:
        rng = random.Random(zlib.crc32(f"ascent:{key}".encode()))
        ascent.plane_events(worlds[key], worlds, rng)
    return sum(len(worlds[k].map.events) for k in W.WORLD_ORDER)


def map_infos(worlds: dict[str, W.World]) -> list[MapInfo]:
    """The map tree.  Music is set by the arrival event, not by the tree.

    Leaving the tree's music at "none" means a map never starts a track on its
    own, so the fade the arrival event runs is the only thing the player ever
    hears change.
    """
    infos = []
    for key in W.WORLD_ORDER:
        world = worlds[key]
        infos.append(MapInfo(
            ident=world.map_id,
            name=f"{world.map_id:02d} {world.title}",
            parent=0,
            indentation=1,
            music_type=1,
            music_name="(OFF)",
            teleport=1,
            escape=2,
            save=1,
        ))
    return infos


# --- LCF ---------------------------------------------------------------------

def run_lcf2xml(tool: Path, source: Path) -> Path:
    """Convert one file and return whatever came out.

    lcf2xml decides both the direction and the output name for itself: it
    reads the root tag (or the binary signature), writes into the *current
    working directory*, and picks the extension from the format it found —
    ``.lmu``/``.ldb``/``.lmt`` going in, ``.emu``/``.edb``/``.emt`` coming
    back out.  Rather than predict that, run it in an empty directory and take
    the file that appears.
    """
    with tempfile.TemporaryDirectory(prefix="lcf-") as tmp:
        work = Path(tmp)
        local = work / source.name
        shutil.copy(source, local)
        before = {p.name for p in work.iterdir()}
        result = subprocess.run([str(tool), local.name], cwd=str(work),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        produced = [p for p in work.iterdir() if p.name not in before]
        if result.returncode != 0 or not produced:
            raise SystemExit(
                f"lcf2xml failed on {source.name}:\n{result.stdout.strip()}")
        if len(produced) > 1:
            raise SystemExit(f"lcf2xml produced {len(produced)} files for "
                             f"{source.name}, expected one")
        keep = work.parent / f"kept-{produced[0].name}"
        shutil.copy(produced[0], keep)
    return keep


def convert(tool: Path, xml_path: Path, out_dir: Path, final_name: str) -> Path:
    """XML in, binary out, under the name RPG_RT expects."""
    produced = run_lcf2xml(tool, xml_path)
    target = out_dir / final_name
    shutil.move(str(produced), target)
    return target


def emit(worlds: dict[str, W.World], common_events, timer: Timer,
         verify: bool) -> list[Path]:
    """Write RPG_RT.ldb, RPG_RT.lmt and one Map####.lmu per world."""
    tool = find_lcf2xml()
    written: list[Path] = []
    world_names = [worlds[k].title for k in W.WORLD_ORDER]

    with tempfile.TemporaryDirectory(prefix="liminal-xml-") as tmp:
        stage = Path(tmp)

        database = db.build_database(
            actors=[db.Actor(1, "you", charset="Dreamer", charset_index=0,
                             max_hp=30, max_sp=10)],
            items=build_items(),
            skills=build_skills(),
            chipsets=build_chipsets(worlds),
            common_events=common_events,
            switches=state.switch_names(world_names),
            variables=state.variable_names(world_names),
            system=SYSTEM,
        )
        # (staged name, final name).  The staged stem is arbitrary; the final
        # name is what RPG_RT looks for.
        jobs = [("database.xml", database, "RPG_RT.ldb")]

        room = worlds["room"]
        treemap = build_treemap(map_infos(worlds), start_map=room.map_id,
                                start_x=room.spawn[0], start_y=room.spawn[1])
        jobs.append(("treemap.xml", treemap, "RPG_RT.lmt"))

        for key in W.WORLD_ORDER:
            world = worlds[key]
            jobs.append((f"Map{world.map_id:04d}.xml", world.map.to_xml(),
                         f"Map{world.map_id:04d}.lmu"))

        staged = []
        for name, text, final in jobs:
            path = stage / name
            path.write_text(text, encoding="utf-8")
            staged.append((path, final))
        timer.step(f"xml staged ({len(jobs)} files)")

        for path, final in staged:
            written.append(convert(tool, path, GAME, final))
        timer.step(f"lcf written ({len(written)} files)")

        if verify:
            round_trip(tool, staged, written)
            timer.step("round-trip verified")

    return written


def round_trip(tool: Path, staged: list[tuple[Path, str]],
               written: list[Path]) -> None:
    """Read every emitted binary back and confirm it still says the same thing.

    A byte-identical XML is not expected — liblcf normalises defaults and fills
    in every field we left out — so the check is structural: the same number of
    events, pages, commands, maps and records has to come back.  A truncated
    event list or a miscounted tile array fails here, where it is a stack
    trace, rather than in the Player, where it is a blank screen.
    """
    for (source, _), binary in zip(staged, written):
        produced = run_lcf2xml(tool, binary)
        try:
            if produced.stat().st_size < 64:
                raise SystemExit(f"{binary.name} did not survive the round trip")
            before = _shape(source.read_text(encoding="utf-8"))
            after = _shape(produced.read_text(encoding="utf-8"))
            if before != after:
                changed = {k: (before[k], after[k])
                           for k in before if before[k] != after[k]}
                raise SystemExit(
                    f"{binary.name} changed shape on re-read: "
                    + ", ".join(f"{k} {a} -> {b}"
                                for k, (a, b) in changed.items()))
        finally:
            produced.unlink(missing_ok=True)


def _shape(xml: str) -> dict[str, int]:
    """A cheap structural fingerprint: how many of each interesting element."""
    interesting = ("<Event ", "<EventPage ", "<EventCommand>", "<Map>",
                   "<MapInfo ", "<Chipset ", "<CommonEvent ", "<Item ",
                   "<Skill ", "<Actor ")
    return {tag.strip("< "): xml.count(tag) for tag in interesting}


def write_ini() -> None:
    (GAME / "RPG_RT.ini").write_text(
        "[RPG_RT]\n"
        "GameTitle=LIMINAL\n"
        "MapEditMode=0\n"
        "MapEditZoom=0\n"
        "FullPackageFlag=1\n",
        encoding="utf-8")

    # The keyboard.  Three plain-text files and the game stops being limited
    # to the engine's seven buttons -- see liminal/keys.py for what they say
    # and why.  They are written last, with the rest of the loose files,
    # because nothing generates them: they are the same every build.
    (GAME / "EasyRPG.ini").write_text(keys.ini(), encoding="utf-8")
    (GAME / keys.LIST_FILE).write_text(keys.script_list(), encoding="utf-8")
    (GAME / keys.SCRIPT_FILE).write_text(keys.script(), encoding="utf-8")


# --- reporting ---------------------------------------------------------------

def summary(worlds: dict[str, W.World], images: int,
            files: list[Path]) -> None:
    print()
    print(f"  {'world':<12}{'map':>4}{'size':>10}{'events':>8}"
          f"{'npcs':>6}  music")
    print("  " + "-" * 58)
    for key in W.WORLD_ORDER:
        world = worlds[key]
        m = world.map
        print(f"  {key:<12}{world.map_id:>4}{f'{m.width}x{m.height}':>10}"
              f"{len(m.events):>8}{W.POPULATION.get(key, 0):>6}  {world.music}")
    total_events = sum(len(worlds[k].map.events) for k in W.WORLD_ORDER)
    print("  " + "-" * 58)
    print(f"  {'':<12}{'':>4}{'':>10}{total_events:>8}"
          f"{sum(W.POPULATION.values()):>6}")
    print()
    print(f"  {images} images, {len(files)} data files, "
          f"{len(list((GAME / 'Music').glob('*.ogg')))} tracks, "
          f"{len(list((GAME / 'Sound').glob('*.ogg')))} sounds")


def prepare_dirs(clean_art: bool) -> None:
    GAME.mkdir(exist_ok=True)
    for name in ASSET_DIRS:
        (GAME / name).mkdir(exist_ok=True)
    if clean_art:
        for name in GENERATED_DIRS:
            for old in (GAME / name).glob("*.png"):
                old.unlink()
    for old in GAME.glob("Map*.lmu"):
        old.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LIMINAL into game/")
    parser.add_argument("--skip-art", action="store_true",
                        help="reuse the PNGs already on disk")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip the LCF round-trip check")
    parser.add_argument("--force", action="store_true",
                        help="write the game even if validation failed")
    args = parser.parse_args()

    print("LIMINAL")
    timer = Timer()
    prepare_dirs(clean_art=not args.skip_art)

    worlds = W.build_all()
    timer.step(f"worlds generated ({len(worlds)})")

    images = 0
    if args.skip_art:
        images = sum(len(list((GAME / d).glob("*.png"))) for d in GENERATED_DIRS)
        print("  (art skipped)")
    else:
        images = export_art(worlds, timer)

    count = author_events(worlds)
    timer.step(f"events authored ({count})")

    common = systems.build(worlds)
    timer.step(f"common events ({len(common)})")

    world_names = [worlds[k].title for k in W.WORLD_ORDER]
    report = validate.check(worlds, common,
                            state.switch_names(world_names),
                            state.variable_names(world_names),
                            GAME, system=SYSTEM)
    timer.step(f"validated ({len(report.errors)} errors, "
               f"{len(report.warnings)} warnings)")
    if report.errors or report.warnings:
        print(report.render())
    if not report.ok and not args.force:
        print(f"\n  {len(report.errors)} error(s); nothing written. "
              f"Use --force to emit anyway.")
        return 1

    files = emit(worlds, common, timer, verify=not args.no_verify)
    write_ini()

    summary(worlds, images, files)
    print(f"\n  built in {timer.total():.1f}s -> {GAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
