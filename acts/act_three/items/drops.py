import random

import pygame

from acts.act_three.environment_objects import CRATE_TILE_IDS
from acts.act_three.tile_catalog import (
    ENVIRONMENT_OBJECTS_TILESET_PATH,
    TILED_GID_MASK,
    tileset_catalog,
)
from acts.act_two.state import DroppedConsumableState
from systems.ground_items import DROPPED_ITEM_FLIGHT_MS


CRATE_DROPS = (
    ("potion", 2000),
    ("regeneration_draught", 700),
    ("silverware", 300),
    ("healing_scroll", 25),
    ("ironblood_tonic", 25),
    ("scroll_of_stoneflesh", 25),
    ("scroll_of_binding", 25),
    ("scroll_of_arcane_impulse", 25),
    ("fire_bomb", 25),
    ("flash_bomb", 25),
    ("spring_trap", 25),
    ("blast_charge", 25),
    ("burial_relic", 10),
)
MONSTER_DROPS = (("monster_parts", 1800), ("burial_relic", 10))
LANTERN_WARDEN_DROPS = (
    ("monster_parts", 0.85),
    ("silverware", 0.60),
    ("healing_scroll", 0.35),
    ("ironblood_tonic", 0.30),
    ("gemstone", 0.15),
)
ORE_DROPS = (("gemstone", 1200),)
ENVIRONMENT_OBJECT_DROPS = dict.fromkeys(CRATE_TILE_IDS, CRATE_DROPS)
DROP_ITEM_IDS = frozenset(
    item for table in (*ENVIRONMENT_OBJECT_DROPS.values(), MONSTER_DROPS) for item, _ in table
)


def place_ground_drop(floor, item, position, current_time, *, animate=False):
    floor.dropped_consumables.append(
        DroppedConsumableState(
            kind=item,
            origin=position,
            destination=position,
            thrown_at=current_time if animate else current_time - DROPPED_ITEM_FLIGHT_MS,
        )
    )


def _roll_ground_drop(floor, position, drop_table, *, animate=False):
    roll = random.randrange(10_000)
    for item, chance in drop_table:
        if roll < chance:
            place_ground_drop(floor, item, position, pygame.time.get_ticks(), animate=animate)
            return
        roll -= chance


def drop_from_environment_object(floor, crate):
    first_gid, _ = tileset_catalog()[ENVIRONMENT_OBJECTS_TILESET_PATH]
    tile_id = (crate.variant & TILED_GID_MASK) - first_gid
    drop_table = ENVIRONMENT_OBJECT_DROPS.get(tile_id)
    if drop_table:
        _roll_ground_drop(floor, (crate.column, crate.row), drop_table)


def drop_from_monster(game_state, enemy):
    floor = game_state.floor
    if enemy.type == "lantern_warden":
        from acts.act_three.quests.blacksmith import claim_pickaxe_drop

        game_state.act_three.pending_monster_loot.append({
            "floor": floor,
            "enemy": enemy,
            "pickaxe": claim_pickaxe_drop(game_state, enemy),
        })
        return
    _roll_ground_drop(floor, (enemy.column, enemy.row), MONSTER_DROPS, animate=True)


def advance_monster_loot(game_state, current_time):
    from acts.act_three.enemies.lantern_warden.settings import WARDEN_DEATH_DURATION_MS
    from acts.act_three.items.special import PICKAXE

    pending = game_state.act_three.pending_monster_loot
    for entry in tuple(pending):
        enemy = entry["enemy"]
        if enemy.death_animation_started_at < 0 or current_time - enemy.death_animation_started_at < WARDEN_DEATH_DURATION_MS:
            continue
        floor = entry["floor"]
        position = (enemy.column, enemy.row)
        place_ground_drop(floor, "burial_relic", position, current_time, animate=True)
        for item, chance in LANTERN_WARDEN_DROPS:
            if random.random() < chance:
                place_ground_drop(floor, item, position, current_time, animate=True)
        if entry["pickaxe"]:
            place_ground_drop(floor, PICKAXE, position, current_time, animate=True)
        pending.remove(entry)


def drop_from_ore(floor, position):
    _roll_ground_drop(floor, position, ORE_DROPS, animate=True)
