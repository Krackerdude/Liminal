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
