"""Where each character lives on which charset sheet."""

from __future__ import annotations

from functools import lru_cache

from ..art.cast import DREAMER_SLOTS, DREAMER_SLOTS_B, _sheets


@lru_cache(maxsize=None)
def _index() -> dict[str, tuple[str, int]]:
    table: dict[str, tuple[str, int]] = {}
    for slot, (name, _) in enumerate(DREAMER_SLOTS):
        table[f"dreamer_{name}"] = ("Dreamer", slot)
    for slot, (name, _) in enumerate(DREAMER_SLOTS_B):
        table[f"dreamer_{name}"] = ("DreamerB", slot)
    # _sheets(), not CAST: the per-world sheets carrying the extra
    # residents are built on top of CAST and are not in it.
    for sheet, entries in _sheets().items():
        for slot, (name, _) in enumerate(entries):
            table[name] = (sheet, slot)
    return table


def charset_slot(name: str) -> tuple[str, int]:
    """Return ``(charset file, index)`` for a named character."""
    return _index()[name]
