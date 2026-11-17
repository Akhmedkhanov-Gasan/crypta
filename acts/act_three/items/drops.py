import random

import pygame

from acts.act_three.tile_catalog import (
    ENVIRONMENT_OBJECTS_TILESET_PATH,
    TILED_GID_MASK,
    tileset_catalog,
)
from acts.act_two.state import DroppedConsumableState
from systems.ground_items import DROPPED_ITEM_FLIGHT_MS


CRATE_DROPS = (
    ("potion", 3600),
    ("regeneration_draught", 1400),
    ("silverware", 300),
    ("healing_scroll", 50),
    ("ironblood_tonic", 50),
    ("scroll_of_stoneflesh", 50),
    ("scroll_of_binding", 50),
    ("scroll_of_arcane_impulse", 50),
    ("fire_bomb", 50),
    ("flash_bomb", 50),
    ("spring_trap", 50),
    ("blast_charge", 50),
    ("burial_relic", 10),
)
URN_DROPS = (("silverware", 300),)
MONSTER_DROPS = (("monster_parts", 1500), ("burial_relic", 10))
ORE_DROPS = (("gemstone", 1200),)
ENVIRONMENT_OBJECT_DROPS = {
    0: CRATE_DROPS,
    9: URN_DROPS,
    18: CRATE_DROPS,
    36: CRATE_DROPS,
}
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


def drop_from_monster(floor, enemy):
    _roll_ground_drop(floor, (enemy.column, enemy.row), MONSTER_DROPS, animate=True)


def drop_from_ore(floor, position):
    _roll_ground_drop(floor, position, ORE_DROPS, animate=True)
