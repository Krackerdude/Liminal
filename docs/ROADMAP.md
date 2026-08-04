# LIMINAL — production plan

Everything left to build, in the order that fails fastest.

The ordering principle: **each phase must produce something runnable that the
next phase can be tested inside.** Content built on top of a system that has
never executed is content that gets thrown away. The current state is the
worst case of that — fourteen fully generated worlds, forty characters and a
complete soundtrack, none of which has ever been loaded by the engine.

Sizes are relative (S / M / L), not calendar estimates.

---

## Where it stands

**On disk and finished**
- 18 music tracks, 26 sound effects, crossfade-looped and encoded

**Written, generates correctly, never exported**
- 14 chipsets, 5 charsets (40 characters), window skin, title, game-over,
  17 screen overlays, diary menu art, 12 effect icons
- 14 worlds, zero unreachable floor, reproducible from a fixed seed
- 12 common events, a switch/variable registry, the LCF authoring layer

**Half-written**
- `worlds/events.py` — room, nexus, the twelve doors, dialogue for all 28
  characters. References a `HIDDEN` table that does not exist and will raise
  the first time it is called.

**Not started**
- The build script. NPC and pickup placement. Secrets. Subworlds. Per-world
  camera behaviour. Per-world mechanics.

---

## Phase 0 — Assembly · **L** · blocks everything

Produce a folder EasyRPG Player will open.

- `tools/build.py`: one command, art → PNG → world generation → event
  authoring → LCF, into `game/`
- Export every generated image as an indexed PNG with palette index 0 held
  transparent, into `ChipSet/ CharSet/ Picture/ System/ Title/ GameOver/`
- Emit `RPG_RT.ldb` (database, terms, items, skills, chipsets, common events),
  `RPG_RT.lmt` (map tree, start position), one `.lmu` per map
- `RPG_RT.ini` so the engine identifies the project

**Verification.** Round-trip every emitted file back through `lcf2xml` and
diff; a file that will not re-read is a file the engine will not read either.
The LCF layer already passes this on a synthetic game, so the risk is in the
volume and the edge cases, not the approach.

**Done when:** the Player boots to the title screen and a new game puts the
player in the room.

**Risk:** highest in the project. Fourteen maps of up to 152×132 with full
event lists is far past anything the emitter has been tested against, and
format faults surface as a silent refusal to load rather than as an error.

---

## Phase 1 — Traversal · **M**

Make all fourteen places reachable and leaveable.

- Fix the `HIDDEN` landmine
- Arrival event per map: set world id, apply grade, start music, erase itself
- The twelve nexus doors, wired to real map ids and spawn points
- A way back from every world
- Bed → nexus, and waking → room
- Player sprite, spawn, movement speed

**Verification.** A scripted walk that visits every map and returns, asserting
the player's map id changes as expected — plus a screenshot per world from
inside the running engine, which is the first time any of this art will have
been seen at play scale rather than as an overhead render.

**Done when:** you can walk out of the room, through the nexus, into and out
of all twelve dreams.

---

## Phase 2 — Systems · **M**

The things the menu implies.

- Place the 12 effects, one per dream, each somewhere that takes finding
- Pickup ceremony (already written) wired to real events
- Diary menu: open, navigate, equip, close — the animation is written and has
  never run
- Equip changes the player sprite and sets its switch
- Engine menu terms, stats, save and load
- Title → room → nexus flow, including returning to a save

**Done when:** you can find all twelve, wear any of them, save, quit and come
back wearing it.

---

## Phase 3 — Inhabitants · **M**

Twenty-eight characters exist and none of them are anywhere.

- Place each world's residents; nobody appears outside their own dream
  (until much later, when exactly one does)
- Movement routines: wandering, stationary, asleep, pacing a fixed route
- Dialogue, already written, wired to the right characters
- Reactive behaviour: what changes when QUIET is worn, when the EYE is worn,
  on a second encounter, when you have already spoken to them once
- Ambient behaviour with no interaction at all — the ones that only watch

**Done when:** every world has people in it who are busy with something that
made sense before you arrived.

---

## Phase 4 — Atmosphere · **M**

The camera as a storytelling instrument rather than a viewport.

- Per-world camera behaviour: slow drift in the void worlds, the procession
  pan down the avenue, wave distortion in the umbrella wood, micro-shake in
  the toy district
- Per-world entry and exit transitions drawn from the engine's real set —
  mosaic, blinds, iris, paper-fold, wave — chosen per world rather than one
  fade everywhere
- Overlay behaviour: the film each world wears, moving rather than static
- Footsteps that follow the terrain under the player
- Ambient one-shots on timers, positioned rather than global

**Rule.** Effects run at a whisper during ordinary walking and are only
allowed to be loud when something is happening. A world that is constantly
distorting has nothing left for the moment that matters.

---

## Phase 5 — Mechanics · **M**

One local rule per world, never explained.

Candidates, one each: the stairwell only permits ascent; the checkerboard
teleports you between identical cells; the sand hides its structures until you
stand still; the number world counts your steps back at you; the star ocean
only bears your weight while something is lit; the brick warren rearranges
behind you; the toy city is navigable only at the scale you are not.

**Done when:** each world does something the others do not, and none of them
mention it.

---

## Phase 6 — Secrets · **L**

Three layers, per the design contract. Nothing is labelled, nothing is
rewarded with an item, and nothing is ever acknowledged.

- **Visible** — findable by walking: things behind the obvious, things at the
  end of a corridor that looked like a dead end
- **Hidden** — conditional: an effect equipped somewhere unrelated, standing
  still for minutes, walking a world's full loop, arriving for the second
  time, leaving an NPC alone
- **Deep** — rare enough to be argued about: one-in-a-thousand anomalies,
  world states that persist forever once seen, a room that only exists after
  you have seen something in another world
- **World memory** — changes that stay changed. An object moved stays moved. A
  door unlocked stays unlocked. Nobody confirms any of it.
- **Loop corruption** — the dream-distance counter already runs; wire worlds
  to change quietly the further you have walked them

---

## Phase 7 — Subworlds · **L**

The graph behind the graph. Yume Nikki's chart is mostly *these*, not the
twelve headline worlds.

- Sub-areas reached from inside a world by means that are never signposted
- Recursive layers — a place inside a place inside the first place
- One-way exits that drop you somewhere unrelated
- Deep-layer areas carrying whatever lore this game has
- Hidden effects that open previously closed routes

**Sequenced last on purpose.** A subworld graph is only interesting if the
worlds it hangs off are worth returning to, and it is the single easiest thing
to over-build before the base game is proven.

---

## Phase 8 — Ship · **M**

- Pacing pass: walk every world end to end and cut whatever is boring
- Title screen variations, save-file oddities, menu anomalies
- Balance the rare-event odds against real playtime rather than guesswork
- Player-facing README and controls
- Packaged build

---

## Standing rules

1. **Nothing is designed without being rendered, and nothing is trusted
   without being played.** Every fault so far was found by looking at output,
   not by reasoning about code.
2. **Measure instead of eyeballing.** Bare-floor percentage and unreachable
   tile count both caught problems that looked fine in a screenshot.
3. **Reachability is not negotiable.** Every world must report zero stranded
   floor, sealed rooms excepted, on every build.
4. **The Golden Rule applies to content as it applied to layout.** No secret
   exists because a secret was needed there.
5. **Generation stays reproducible.** Same seed, same game, every time.
