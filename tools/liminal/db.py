"""RPG_RT.ldb construction.

The database is where LIMINAL's diegetic vocabulary lives.  There are no
battles, so every combat-flavoured field RPG Maker insists on is repurposed:
HP becomes PRESENCE, SP becomes CLARITY, "skills" become the effects you carry
around with you, and the shop/battle terminology is simply never surfaced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .cmds import Script
from .lcfxml import Node, collection, document, music, sound

# rpg::Item::Type
ITEM_NORMAL = 0
ITEM_ACCESSORY = 5
ITEM_MEDICINE = 6
ITEM_SPECIAL = 9
ITEM_SWITCH = 10

# rpg::Skill::Type
SKILL_NORMAL = 0
SKILL_TELEPORT = 1
SKILL_ESCAPE = 2
SKILL_SWITCH = 3

# rpg::CommonEvent::Trigger
TRIGGER_AUTOMATIC = 3
TRIGGER_PARALLEL = 4
TRIGGER_CALL = 5


@dataclass
class Item:
    ident: int
    name: str
    description: str = ""
    type: int = ITEM_SWITCH
    switch_id: int = 1
    price: int = 0
    uses: int = 0          # 0 = unlimited; the things you carry never run out
    entire_party: bool = False

    def to_node(self) -> Node:
        node = Node("Item")
        node.set("name", self.name)
        node.set("description", self.description)
        node.set("type", self.type)
        node.set("price", self.price)
        node.set("uses", self.uses)
        node.set("switch_id", self.switch_id)
        node.set("occasion_field2", True)
        node.set("occasion_battle", False)
        node.set("entire_party", self.entire_party)
        node.set("animation_id", 0)
        return node


@dataclass
class Skill:
    ident: int
    name: str
    description: str = ""
    type: int = SKILL_SWITCH
    switch_id: int = 1
    sp_cost: int = 0
    message1: str = ""
    message2: str = ""

    def to_node(self) -> Node:
        node = Node("Skill")
        node.set("name", self.name)
        node.set("description", self.description)
        node.set("using_message1", self.message1)
        node.set("using_message2", self.message2)
        node.set("type", self.type)
        node.set("switch_id", self.switch_id)
        node.set("sp_type", 0)
        node.set("sp_cost", self.sp_cost)
        node.set("sp_percent", 0)
        node.set("scope", 0)
        node.set("occasion_field", True)
        node.set("occasion_battle", False)
        node.set("animation_id", 0)
        return node


@dataclass
class CommonEvent:
    ident: int
    name: str
    trigger: int = TRIGGER_CALL
    switch_id: int | None = None
    script: Script = field(default_factory=Script)

    def to_node(self) -> Node:
        node = Node("CommonEvent")
        node.set("name", self.name)
        node.set("trigger", self.trigger)
        node.set("switch_flag", self.switch_id is not None)
        node.set("switch_id", self.switch_id or 1)
        node.add(Node("event_commands")).extend(self.script.to_nodes())
        return node


@dataclass
class Chipset:
    ident: int
    name: str
    chipset_name: str
    passable_lower: Sequence[int]
    passable_upper: Sequence[int]
    terrain: Sequence[int] | None = None
    animation_type: int = 0
    animation_speed: int = 0

    def to_node(self) -> Node:
        node = Node("Chipset")
        node.set("name", self.name)
        node.set("chipset_name", self.chipset_name)
        node.set("passable_data_lower", list(self.passable_lower))
        node.set("passable_data_upper", list(self.passable_upper))
        if self.terrain is not None:
            node.set("terrain_data", list(self.terrain))
        node.set("animation_type", self.animation_type)
        node.set("animation_speed", self.animation_speed)
        return node


@dataclass
class Actor:
    ident: int
    name: str
    title: str = ""
    charset: str = ""
    charset_index: int = 0
    face: str = ""
    face_index: int = 0
    max_hp: int = 30
    max_sp: int = 10


# Terms.  Nothing here says "battle", "gold", or "enemy" where the player can
# see it; the menu is meant to read like a page torn out of somebody's notes.
TERMS: dict[str, str] = {
    # main menu + status screen
    "command_item": "things",
    "command_skill": "effects",
    "menu_equipment": "worn",
    "menu_save": "remember",
    "menu_quit": "wake up",
    "status": "self",
    "possessed_items": "carried",
    "equipped_items": "worn",
    "gold": "coins",
    "level": "depth",
    "health_points": "presence",
    "spirit_points": "clarity",
    "normal_status": "here",
    "exp_short": "time",
    "lvl_short": "d",
    "hp_short": "pr",
    "sp_short": "cl",
    "attack": "reach",
    "defense": "weight",
    "spirit": "signal",
    "agility": "drift",
    "weapon": "in hand",
    "shield": "other hand",
    "armor": "body",
    "helmet": "head",
    "accessory": "pocket",
    # title / file screens
    "new_game": "begin",
    "load_game": "return",
    "exit_game": "leave",
    "file": "night",
    "save_game_message": "which night do you want to keep?",
    "load_game_message": "which night do you want back?",
    "exit_game_message": "stop?",
    "yes": "yes",
    "no": "not yet",
    # these never surface, but leaving RPG Maker's defaults in would be a
    # tonal leak if anything ever did surface them
    "level_up": " goes deeper.",
    "skill_learned": " remembers \\s.",
    "item_recieved": " is yours now.",
    "use_item": " uses \\o.",
    "battle_start": "",
    "miss": "nothing happens.",
}


def _terms_node() -> Node:
    node = Node("terms")
    inner = node.add(Node("Terms"))
    for key, value in TERMS.items():
        inner.set(key, value)
    return node


def _system_node(*, title_music: str, gameover_music: str, system_graphic: str,
                 title_graphic: str, gameover_graphic: str,
                 cursor_se: str, decision_se: str, cancel_se: str,
                 buzzer_se: str, item_se: str, show_title: bool = True) -> Node:
    node = Node("system")
    inner = node.add(Node("System"))
    inner.set("boat_name", "")
    inner.set("ship_name", "")
    inner.set("airship_name", "")
    inner.set("title_name", title_graphic)
    inner.set("gameover_name", gameover_graphic)
    inner.set("system_name", system_graphic)
    inner.set("party", [1])
    inner.set("menu_commands", [1, 2, 3, 4])
    inner.add(music(title_music, tag="title_music", fadein=40))
    inner.add(music("(OFF)", tag="battle_music"))
    inner.add(music("(OFF)", tag="battle_end_music"))
    inner.add(music("(OFF)", tag="inn_music"))
    inner.add(music(gameover_music, tag="gameover_music"))
    inner.add(sound(cursor_se, tag="cursor_se", volume=55))
    inner.add(sound(decision_se, tag="decision_se", volume=70))
    inner.add(sound(cancel_se, tag="cancel_se", volume=60))
    inner.add(sound(buzzer_se, tag="buzzer_se", volume=60))
    inner.add(sound(item_se, tag="item_se", volume=80))
    # Slow, soft screen transitions everywhere.  Nothing in this game should
    # ever cut hard except when it means to.
    inner.set("transition_out", 2)
    inner.set("transition_in", 2)
    inner.set("message_stretch", 0)
    inner.set("font_id", 0)
    inner.set("show_frame", False)
    inner.set("show_title", show_title)
    inner.set("easyrpg_max_savefiles", 8)
    return node


def _actor_node(actor: Actor) -> Node:
    node = Node("Actor")
    node.set("name", actor.name)
    node.set("title", actor.title)
    node.set("character_name", actor.charset)
    node.set("character_index", actor.charset_index)
    node.set("face_name", actor.face)
    node.set("face_index", actor.face_index)
    node.set("initial_level", 1)
    node.set("final_level", 50)
    node.set("exp_base", 30)
    node.set("exp_inflation", 30)
    node.set("class_id", 0)
    node.set("critical_hit", False)
    node.set("unarmed_animation", 0)
    node.set("battler_animation", 0)
    # A flat, nearly-static stat curve: the numbers exist so the status screen
    # has something to say, not so they can be optimised.
    params = node.add(Node("parameters")).add(Node("Parameters"))
    params.set("maxhp", [actor.max_hp] * 99)
    params.set("maxsp", [actor.max_sp] * 99)
    params.set("attack", [1] * 99)
    params.set("defense", [1] * 99)
    params.set("spirit", [1] * 99)
    params.set("agility", [4] * 99)
    return node


def _placeholder(tag: str, name: str = "") -> Node:
    node = Node(tag)
    node.set("name", name)
    return node


def build_database(*, actors: Sequence[Actor], items: Sequence[Item],
                   skills: Sequence[Skill], chipsets: Sequence[Chipset],
                   common_events: Sequence[CommonEvent],
                   switches: dict[int, str], variables: dict[int, str],
                   system: dict) -> str:
    """Serialise the whole database to liblcf's XML dialect."""
    db = Node("Database")

    db.add(collection("actors", [(a.ident, _actor_node(a)) for a in actors]))
    db.add(collection("skills", [(s.ident, s.to_node()) for s in skills]))
    db.add(collection("items", [(i.ident, i.to_node()) for i in items]))

    # RPG Maker refuses to load a database with empty combat tables even
    # though nothing in LIMINAL will ever read them.
    db.add(collection("enemies", [(1, _placeholder("Enemy", "-"))]))
    db.add(collection("troops", [(1, _placeholder("Troop", "-"))]))
    db.add(collection("terrains", [
        (1, _placeholder("Terrain", "floor")),
        (2, _placeholder("Terrain", "water")),
        (3, _placeholder("Terrain", "carpet")),
        (4, _placeholder("Terrain", "grass")),
        (5, _placeholder("Terrain", "concrete")),
    ]))
    db.add(collection("attributes", [(1, _placeholder("Attribute", "-"))]))
    db.add(collection("states", [(1, _placeholder("State", "here"))]))
    db.add(collection("animations", [(1, _placeholder("Animation", "-"))]))

    db.add(collection("chipsets", [(c.ident, c.to_node()) for c in chipsets]))
    db.add(_terms_node())
    db.add(_system_node(**system))

    db.add(collection("switches", [
        (i, _placeholder("Switch", name)) for i, name in sorted(switches.items())]))
    db.add(collection("variables", [
        (i, _placeholder("Variable", name)) for i, name in sorted(variables.items())]))
    db.add(collection("commonevents",
                      [(e.ident, e.to_node()) for e in common_events]))
    db.add(collection("classes", [(1, _placeholder("Class", "-"))]))

    return document("LDB", db)
