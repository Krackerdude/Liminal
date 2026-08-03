"""Where each character lives on which charset sheet."""

from __future__ import annotations

from functools import lru_cache

from ..art.cast import CAST, DREAMER_SLOTS


@lru_cache(maxsize=None)
def _index() -> dict[str, tuple[str, int]]:
    table: dict[str, tuple[str, int]] = {}
    for slot, (name, _) in enumerate(DREAMER_SLOTS):
        table[f"dreamer_{name}"] = ("Dreamer", slot)
    for sheet, entries in CAST.items():
        for slot, (name, _) in enumerate(entries):
            table[name] = (sheet, slot)
    return table


def charset_slot(name: str) -> tuple[str, int]:
    """Return ``(charset file, index)`` for a named character."""
    return _index()[name]
