# The Golden Rule

**DO NOT MAKE RANDOM SURREALISM.**

Random objects do not create dreams. A dream is a place with impossible logic.

Before creating any world, define — in this order, and in writing:

1. The core theme
2. The emotional feeling
3. The map layout
4. The connected zones
5. The environmental rules
6. The unique mechanic
7. The secrets
8. The hidden lore
9. The visual effects

Only after those are defined should assets be created.

The goal: create worlds that feel like they have existed forever. Places where
every hallway, object, NPC, transition and secret feels intentional. Not a
random surreal playground. A living dream.

---

## What this rules out

These are the specific mistakes this document exists to prevent, all of which
were made in an earlier draft of this project and had to be thrown away:

- **A big open field with props scattered on it.** "Add trees, rocks and weird
  objects" is not a design. If the layout would still work with the props
  swapped for different props, there is no layout.
- **"The woods."** A concept you could describe with one mundane noun is not a
  dream. *Forest* is not a concept; *a forest where the trees form a grid and
  every trunk is watching* is.
- **Unbounded space.** If the player cannot tell where the playable area ends,
  the space has no shape, and a space with no shape cannot be remembered.
- **Uncontrolled scale.** The player sprite is the unit. Every object is sized
  in relation to it deliberately — oversized or undersized *on purpose*, never
  arbitrarily.
- **Detail spam.** Density is not richness. One deliberate landmark beats forty
  scattered decorations.

## Structural requirements

Every world is a **collection of connected zones**, even outdoors:

- a central area or landmark that orients the player
- several sub-zones, each with its own shape and its own reason to exist
- **thick, visible boundaries** — patterned wall bands, void, water, a wall of
  trees, an impossibly long hallway — that contain the player and define the
  playable area
- strange transitions between zones: a doorway standing in the open, a
  staircase that leaves the environment, a corridor far too long for what it
  connects
- void or negative space *outside* the playable area, so the world reads as a
  place rather than a level

The result should feel maze-*like* without being a maze. The player should
think "how did I end up here?" and "why does this connect to that?" — never
"which way is the exit?"

## Scale reference

The player is 24x32 pixels on a 16x16 tile grid: roughly one and a half tiles
wide and two tall. The visible screen is 20x15 tiles.

- a **room** is one to two screens across (20–40 tiles)
- a **corridor** is 3–5 tiles wide; anything wider stops reading as a corridor
- a **landmark** should be at least 3x4 tiles to register, and 6x8 or larger to
  dominate a zone
- an object meant to feel enormous must be **taller than the screen** so the
  player cannot see all of it at once

## The check

After generating any world, render it and ask, honestly:

> Did I make an incoherent mess of objects, or a designed layout with zones,
> boundaries and a path of discovery?

If the answer is the first one, it does not ship.

---

## The interaction rule

**Every world must contain one core interactive system that is deeply tied to
its theme.**

That system has to be usable *throughout* the world, not confined to one
puzzle room. It should encourage curiosity, experimentation and traversal by
letting the player interact with the environment over and over in ways that
mean something. Objects belonging to the world's theme should all respond to
it consistently, so the place reads as cohesive and alive.

It should unlock alternate routes, reveal hidden spaces, change how the
residents behave, transform scenery, or create new interactions — and it must
never feel like a puzzle-game mechanic, and never need a tutorial.

**When a player enters a new world they should immediately find a new way to
physically engage with that place that exists nowhere else in the game.**

The test: if you removed the mechanic and the world still played identically
apart from a few locked doors, it was a puzzle, not a system.

---

## The sequencing rule

The interaction rule above says every world needs a verb. This says what the
verb has to be *worth*.

**Reference points: *Please, Don't Touch Anything*, *Blue Prince*, *House.wad*,
and the deep easter eggs in Call of Duty Zombies.** What those share is not
difficulty — it is that the world is holding information the player has to
assemble themselves, across the whole space, with nothing acknowledging that
they are doing it.

So:

**Sequence over switches.** A mechanic that opens one door when you press one
thing is a lock. A mechanic worth building has an *order* to it — do these in
this sequence, in this state, and something happens that would not otherwise.
The order is discoverable somewhere in the world, never in a menu.

**Hints live in the environment.** Scratched into a wall, spelled out by where
things are standing, audible only in one place, visible only in one state of
the map. The player finds the instruction, not the tutorial.

**Reward the ones who go the extra mile.** Most players should finish a world
having used its verb casually and seen most of it. The player who pays close
attention gets somewhere the casual one never knew existed. Both are correct
outcomes; only the second is earned.

**Some consequences are permanent, and some of those are terrible.** A world is
allowed to be worse forever because of something you did. It must never warn
you first, and it must never be undoable. The game does not have a bad ending
to reach — it has states you can put it into and cannot take back.

**The tone is allowed to break.** A world that has been childlike for an hour
may stop being childlike. Palette, overlay, music and residents all move
together when it does, and nothing comments on it.

**Hide things properly.** If every instance of a mechanic is in plain sight, the
mechanic has no depth. Some should be somewhere nobody would look, and finding
one should feel like the world made a mistake.
