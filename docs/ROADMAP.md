# LIMINAL — production plan

Everything left to build, in the order that fails fastest.

The ordering principle: **each phase must produce something runnable that the
next phase can be tested inside.** Content built on top of a system that has
never executed is content that gets thrown away. The current state is the
worst case of that — fourteen fully generated worlds, forty characters and a
complete soundtrack, none of which has ever been loaded by the engine.

Sizes are relative (S / M / L), not calendar estimates.

---

## Content targets

The numbers this plan is sized against. These are the contract; phases below
are how they get built.

| | Target |
|---|---|
| Worlds | 14 |
| Doors per world | **1** — the way in is the way out. No world is a junction. |
| Effects | **1 per world**, 14 total, each hidden inside its own world |
| NPCs | **182**, unevenly distributed |
| Secrets per world | **~10** |
| Subworlds | **34** |
| Secrets per subworld | **1–5** |
| Subworld music | **one generated track each**, 34 additional tracks |
| World layers | **15 extra maps**, and they are *not* subworlds |

**Uneven NPC density is a requirement, not an accident.** Some worlds have
none at all and are meant to feel emptied rather than unfinished. Others are
crowded to the point of discomfort. A world with thirty residents and a world
with zero are both correct; fourteen worlds with thirteen each is the failure
mode. Density is a statement about the place.

**Subworlds carry no basic concepts.** Everything obvious was spent on the
fourteen. A subworld earns its existence by being harder to reach and worse to
be inside than anything above it — mechanics that break the rules the main
worlds established, visuals that do not read as places, features that are
genuinely frightening rather than merely strange. If a subworld could be
described as "the X world but smaller", it is cut.

**Layers are not subworlds.** Four worlds need more maps than they have, and
they are additional *states or floors of the same world*, reached by that
world's own verb and sharing its identity, music family and cast:

Counted as *planes including the base world*, so "5" means the world plus
four more maps. Fifteen extra maps in all.

| world | planes | what they are | built |
|---|---|---|---|
| stairs | 5 | floors, each more corrupted than the last, reached by falling in a particular order | ✅ |
| umbrellas | 5 | planes, ascending, the imagery coming apart the higher you get | ✅ |
| faces | 4 | broadcast states of one map, each a different palette with its own residents and items | ✅ |
| neon | 4 | the insides of murals, entered by standing on them | ✅ |

A subworld is secret, hostile and unrelated. A layer is the world continuing.

**The grove, in detail**, because it is the one that sets the bar for the
other three. All four channels are generated from one fixed seed at one size,
so the street plan is bit-identical across them — tuning must never move a
kerb, or the player reads four maps instead of one place. What differs is a
whole chipset each (its own palette, wall motif, ground marks, floor patterns,
murals and animation speed), its own four bespoke residents drawn per facing,
its own props, its own easter egg and its own fragment of the lore.

Five yards are cut into the green mass and sealed. Each is reachable on
exactly one channel, because on that channel the seam of wood between it and
the street is not rendered as wood — the seam stays *wall* in the layout, so
every shared pass treats it as solid, and only the tiles written per channel
differ. Four of the yards hold one carried thing each, and every one of them
is used on a channel other than the one that had it:

    the grove  →  coin  →  no signal  →  tape  →  overgrown
                                                     ↓
    the grove  ←  bulb  ←  off-colour  ←  seed  ←────┘

which is a closed loop that cannot be short-circuited. The fifth yard is the
compound at the foot of the transmitting mast, and it opens for the bulb.

Tuning is the ring: a payphone somewhere out of sight starts ringing, panned
in stereo left and right and with the camera drifting one tile for up and
down. Walk that way inside a two-second window and the picture changes around
you — a teleport to the same coordinates on the next channel, which is only
possible because the four maps are the same map. Miss it and nothing at all
happens.

**The paintings, in detail.** Four floor murals in the scrawl world are also
ways into it. Step on one — touch, not action, because facing a picture on the
floor and pressing a button would make it a door — and you are inside it. Each
interior is built out of that painting's shape and its two colours and nothing
else, so the layout carries the same information as the picture:

| painting | inside it | its secret |
|---|---|---|
| the eye | concentric rings round a pupil, gaps that never line up | stand in the pupil and stop moving |
| the spiral | one corridor, in and back out again | walk it outward, from the middle |
| the mouth | a throat that narrows, pockets between the teeth | go all the way down instead of into a pocket |
| the star | five arms and a hub, nothing in between | touch the tips in the order the points are longest |

None of these are a torus. Everywhere else wraps, which is what makes walking
feel endless; a painting is a finite object, and finding its edge is the
difference. Each keeps one thing — the lens, the thread, the loose tooth, the
long point — and two residents made of the painting itself. They are a set
rather than a chain: any order, but the plaza in the middle of the scrawl
world answers to all four and to nothing less.

**The ascent, in detail.** Opening an umbrella under yourself lifts you one
plane. That is the whole verb — no ladder, no lift, no stair, nothing that
looks like a way up, only a furled umbrella lying about and the ordinary act
of opening one. The argument is carried by what happens to three things on the
way up:

| plane | layout | who is on it | palette |
|---|---|---|---|
| higher | soft blobs joined by curves | three designs, wandering, talkative | warm cream, saturation 88 |
| higher still | squared courts, colonnaded | two designs, wandering | cooler, saturation 62 |
| the tiers | thirty identical cells on a grid | one design, stationary, identical | grey, saturation 38 |
| the top | corridors of counters | one, and it is a fitting with a face | flat, saturation 16 |

Nothing is ever named. There is no scripture, no iconography anybody could
point at, nothing that says the word out loud. One sentence is written across
the four planes, one fragment per plane, and it is only readable by somebody
who went all the way up.

Coming down is the waterfalls. Every plane pours off its own edge and stepping
into one drops you the whole way to the bottom in a single go — no stages, no
gentle descent. The climb and the fall are deliberately not the same shape.

**Reaching a subworld is never signposted.** No door is drawn as a door. The
route is a behaviour, a condition, or a coincidence — not an exit.

---

## Where it stands

**Built, and proven inside the engine**
- `tools/build.py` assembles the whole game in about three seconds
- 62 images, 16 LCF files, 18 tracks, 26 sounds in `game/`
- All 14 maps boot in EasyRPG Player with no warnings and no missing assets
- `tools/validate.py` checks what the file format cannot: dangling asset
  names, teleports to nowhere, undeclared switches, events stacked on one
  tile, a world with no way out
- `tools/smoke.py` boots every map in the real Player and screenshots it

**Written, generates correctly, thin against target**
- 5 charsets — 40 characters against a target of 182
- 12 effect icons against a target of 14, one per world
- 12 common events, a switch/variable registry, the LCF authoring layer

**Not started**
- Secrets. Subworlds and their music. Per-world camera behaviour. Per-world
  mechanics. 142 more characters.

**Open fault, found by the engine**
Measured across every 20×15 window of every world, the share that contains
nothing but bare floor:

| stairs | hands | sand | numbers | umbrellas | stars | toys | rest |
|---|---|---|---|---|---|---|---|
| 36% | 27% | 16% | 14% | 4% | 3% | 1% | 0% |

An overview render at one pixel per tile made all fourteen look furnished.
A single screen is 300 tiles, and in the stairwell more than a third of them
are a flat colour with the player standing in the middle of it. **Density has
to be measured per screen, not per world** — that is the scale the player
actually experiences, and it is the metric Phase 4 is held to.

---

## Phase 0 — Assembly · **L** · ✅ done

Produce a folder EasyRPG Player will open.

- `tools/build.py`: one command, art → PNG → world generation → event
  authoring → LCF, into `game/`
- Export every generated image as an indexed PNG with palette index 0 held
  transparent, into `ChipSet/ CharSet/ Picture/ System/ Title/ GameOver/`
- Emit `RPG_RT.ldb` (database, terms, items, skills, chipsets, common events),
  `RPG_RT.lmt` (map tree, start position), one `.lmu` per map
- `RPG_RT.ini` so the engine identifies the project

**Verification.** Three layers, and each one caught something the one above it
could not:

1. Round-trip every emitted file back through `lcf2xml` and compare structure
2. `validate.py` on the in-memory game, before a byte is written
3. `smoke.py` boots all fourteen maps in the real Player and reads its log

**What it found.** The choice-command indent rule, a game-over track that was
never generated, two events standing on the same tile in the nexus, and the
one that mattered: **an event with no charset is not invisible.** The engine
falls back to drawing chipset tile zero, which is the void, so every silent
trigger in the game rendered as a black square next to the thing it was
attached to. Fixed with a real, deliberately empty `Blank` charset.

**Done:** the Player boots, a new game puts the player in the room, and every
map loads clean.

---

## Phase 1 — Traversal · **M** · ✅ done

Make all fourteen places reachable and leaveable.

- Arrival event per map: set world id, apply grade, start music, erase itself
- **One door per world** — fourteen nexus doors, wired to real map ids and
  spawn points. A world is a dead end by design; the only way on is back
  through the nexus.
- A way back from every world, at the point you arrived and nowhere else
- Bed → nexus, and waking → room
- Player sprite, spawn, movement speed

**Verification.** `tools/traverse.py` plays recorded button input through the
Player and reads its log to see which map it loaded next — the only check in
the project that presses a key. Every link is covered: room to nexus through
the bed, nexus to a dream through its door, and all twelve dreams back out
through their own.

**What it found.** Three engine rules that no amount of reading the format
would have surfaced, all in the commit above. Then two of its own: an empty
upper-layer cell is not zero, and a test that walks a fixed number of frames
is really a test of the walking speed — the room route now walks *into walls*
so it lands in the same place whatever the pace is set to.

**Done:** the loop closes. Room, nexus, all twelve dreams, and back.

---

## Phase 2 — Systems · **M** · ✅ done

The things the menu implies.

- Draw the two missing effect icons — the set is **one per world, fourteen**
- Place the 14 effects, one per world, each somewhere that takes finding
- Pickup ceremony (already written) wired to real events
- Diary menu: open, navigate, equip, close — the animation is written and has
  never run
- Equip changes the player sprite and sets its switch
- Engine menu terms, stats, save and load
- Title → room → nexus flow, including returning to a save

**Verification.** `tools/saveload.py` plays the real menu — opens it, walks
down to save, picks a night — then relaunches the Player with
`--load-game-id` and reads back which map it reports.

**What it found.** Two things that both looked like something else. Anything
past the eighth effect silently reused the eighth sprite, because a charset
holds eight and there are thirteen selves; half the collection changed nothing
about you. And RPG Maker's menus repeat-fire while a direction is held, so a
thirty-frame press moves the cursor twice and lands on "quit" instead of
"save" — which is indistinguishable from saving being broken.

**Done:** the diary opens and animates, twelve effects sit on the far side of
their worlds, wearing one changes who you are, and a save round-trips through
the engine.

---

## Phase 3 — Inhabitants · **L**

**The cast contract, non-negotiable:** four *bespoke* designs per populated
world, each fitting that world's idea, each genuinely drawn from all four
sides. Not four palettes of one body, and not one view reused with an eye
shifted two pixels.

`tools/facings.py` measures the second half of that: the share of pixels that
change between front and back, and between left and right. A design passes at
12% on both. **24 of the current 49 fail**, and the creatures fail hardest —
the cone changes 1% when it turns around, the pawn 1%, the walking hand 1%.
The humanoids turn acceptably in profile (22–47%) but their back view is only
"hair instead of a face" (6–12%).

Passing this is what will make the worlds feel inhabited rather than
decorated, and it is the measure to hold the work to.

**182 NPCs.** Twenty-eight are drawn and written; none of them are anywhere.

The bulk of this phase is cast expansion — 142 more designs, sheets and voices
— not placement. Placement is the cheap half.

- **Density is authored, never averaged.** Some worlds get none. Worlds that
  have residents do not get comparable counts. A crowd and a vacancy are both
  deliberate, and the emptiest world should read as *emptied*.
- Extend `art/cast.py` from 40 characters to 182, and the charsets that carry
  them — roughly 23 sheets at 8 per sheet
- Place each world's residents; nobody appears outside their own world
  (until much later, when exactly one does)
- Movement routines: wandering, stationary, asleep, pacing a fixed route
- Dialogue for all 182 — most say one thing, some say nothing, a few say
  something different the second time
- Reactive behaviour: what changes when QUIET is worn, when the EYE is worn,
  on a second encounter, when you have already spoken to them once
- Ambient behaviour with no interaction at all — the ones that only watch

**Rule.** A hundred and eighty-two speaking parts is a hundred and eighty-two
chances to write filler. Silence is a valid design for an NPC; a line that
exists because the character needed a line is not.

**Done when:** every world has exactly as many people in it as that world
should have, and they are busy with something that made sense before you
arrived.

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

**~10 per world, ~140 total.** Three layers, per the design contract. Nothing
is labelled, nothing is rewarded with an item, and nothing is ever
acknowledged.

Ten per world is a mix, not ten of the same kind: roughly half visible, a
third conditional, the rest deep. A world whose ten secrets are ten hidden
alcoves has one secret repeated ten times.

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

**34 of them.** The graph behind the graph. Yume Nikki's chart is mostly
*these*, not the headline worlds.

- Sub-areas reached from inside a world by means that are never signposted —
  no drawn doors, no glowing tile. The route is a condition, a behaviour, or
  an accident.
- **No basic concepts.** Everything legible was spent upstairs. A subworld
  must do something the fourteen cannot: a mechanic that contradicts the rules
  the main worlds taught, a space that does not resolve into a place, a
  presence that is meant to actually frighten. "The X world but smaller" is
  cut on sight.
- **1–5 secrets each** — a subworld can be a single held breath with one thing
  in it, or a nest. Uniform counts are a failure here too.
- **One generated track per subworld**, 34 additional pieces, written at
  generation time alongside the space rather than assigned from a pool. A
  subworld that shares a main world's music is not a subworld.
- Recursive layers — a place inside a place inside the first place
- One-way exits that drop you somewhere unrelated
- Deep-layer areas carrying whatever lore this game has
- Hidden effects that open previously closed routes

**Sequenced last on purpose.** A subworld graph is only interesting if the
worlds it hangs off are worth returning to, and it is the single easiest thing
to over-build before the base game is proven. Thirty-four of them makes that
risk larger, not smaller.

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
