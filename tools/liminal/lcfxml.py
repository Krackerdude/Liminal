"""Minimal emitter for liblcf's XML dialect.

liblcf ships readers/writers that round-trip RPG Maker 2000 data files through
an XML representation (``lcf2xml``).  Fields that are absent from the XML keep
the defaults baked into liblcf's generated structs, so we only ever have to
write the handful of nodes we actually care about.

Everything in this module is deliberately dumb: it builds a tree of nested
lists and serialises it.  The interesting decisions live in ``db.py`` and
``maps.py``.
"""

from __future__ import annotations

from typing import Iterable, Sequence
from xml.sax.saxutils import escape


class Node:
    """An XML element with either child elements or a text body."""

    __slots__ = ("tag", "attrs", "children", "text")

    def __init__(self, tag: str, text: str | None = None, **attrs: str):
        self.tag = tag
        self.attrs = attrs
        self.children: list[Node] = []
        self.text = text

    def add(self, child: "Node") -> "Node":
        self.children.append(child)
        return child

    def set(self, tag: str, value) -> "Node":
        """Append a leaf node, converting Python values to liblcf's notation."""
        return self.add(Node(tag, fmt(value)))

    def extend(self, nodes: Iterable["Node"]) -> "Node":
        self.children.extend(nodes)
        return self

    def render(self, out: list[str], depth: int = 0) -> None:
        pad = " " * depth
        attr = "".join(f' {k}="{escape(str(v))}"' for k, v in self.attrs.items())
        if self.children:
            out.append(f"{pad}<{self.tag}{attr}>")
            for child in self.children:
                child.render(out, depth + 1)
            out.append(f"{pad}</{self.tag}>")
        else:
            body = escape(self.text) if self.text else ""
            out.append(f"{pad}<{self.tag}{attr}>{body}</{self.tag}>")


def fmt(value) -> str:
    """Render a Python value the way liblcf's XML writer would."""
    if isinstance(value, bool):
        return "T" if value else "F"
    if isinstance(value, Node):
        raise TypeError("use Node.add() for element children")
    if isinstance(value, (list, tuple)):
        return " ".join(str(int(v)) for v in value)
    return str(value)


def eid(n: int) -> str:
    """liblcf writes collection element ids as zero-padded 4-digit strings."""
    return f"{n:04d}"


def document(root_tag: str, body: Node) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>', f"<{root_tag}>"]
    body.render(out, 1)
    out.append(f"</{root_tag}>")
    out.append("")
    return "\n".join(out)


def music(name: str, *, fadein: int = 0, volume: int = 100,
          tempo: int = 100, balance: int = 50, tag: str = "music") -> Node:
    """A ``Music`` sub-record.  ``(OFF)`` is RPG Maker's "no track" sentinel."""
    holder = Node(tag)
    inner = holder.add(Node("Music"))
    inner.set("name", name)
    inner.set("fadein", fadein)
    inner.set("volume", volume)
    inner.set("tempo", tempo)
    inner.set("balance", balance)
    return holder


def sound(name: str, *, volume: int = 100, tempo: int = 100,
          balance: int = 50, tag: str = "sound") -> Node:
    holder = Node(tag)
    inner = holder.add(Node("Sound"))
    inner.set("name", name)
    inner.set("volume", volume)
    inner.set("tempo", tempo)
    inner.set("balance", balance)
    return holder


def collection(tag: str, items: Sequence[tuple[int, Node]]) -> Node:
    """Wrap ``(id, node)`` pairs in a parent element, stamping the id attribute."""
    parent = Node(tag)
    for ident, node in items:
        node.attrs["id"] = eid(ident)
        parent.add(node)
    return parent
