import random

from enemies import ENEMY_TYPES
from generation import generate_floor
from game.state import (
    ChestState,
    EnemyState,
    FloorState,
    GameState,
    PlayerState,
    PotionState,
    RoomState,
)
from settings import (
    PLAYER_DAMAGE_MAX,
    PLAYER_DAMAGE_MIN,
    PLAYER_MAX_HEALTH,
)


def create_floor_state(floor_index: int) -> FloorState:
    floor = generate_floor(floor_index)
    player_column, player_row = floor["player_start"]
    enemies = []
    enemy_type_counts = {}

    for enemy_data in floor["enemies"]:
        enemy_column, enemy_row = enemy_data["position"]
        enemy_type = enemy_data["type"]
        belongs_to_boss_group = enemy_data.get(
            "boss_group",
            False,
        )
        enemy_config = ENEMY_TYPES[enemy_type]
        enemy_type_counts[enemy_type] = (
            enemy_type_counts.get(enemy_type, 0) + 1
        )
        enemy_number = enemy_type_counts[enemy_type]
        enemy_name = (
            enemy_config["display_name"]
            if enemy_config.get("is_unique", False)
            else f"{enemy_config['display_name']} {enemy_number}"
        )
        enemies.append(
            EnemyState.from_config(
                enemy_type=enemy_type,
                column=enemy_column,
                row=enemy_row,
                name=enemy_name,
                config=enemy_config,
                belongs_to_boss_group=belongs_to_boss_group,
            )
        )

    eligible_key_carriers = [
        enemy
        for enemy in enemies
        if (
            (enemy.column, enemy.row) != floor["stairs"]
            and not enemy.boss_group
        )
    ]
    other_key_carriers = [
        enemy
        for enemy in enemies
        if enemy not in eligible_key_carriers
    ]
    possible_key_carriers = (
        eligible_key_carriers + other_key_carriers
    )
    key_carrier_count = min(
        len(floor["chests"]),
        len(possible_key_carriers),
    )

    for key_carrier in random.sample(
        possible_key_carriers,
        key_carrier_count,
    ):
        key_carrier.has_key = True

    chests = []

    for chest_data in floor["chests"]:
        chest_column, chest_row = chest_data["position"]
        chests.append(
            ChestState(
                column=chest_column,
                row=chest_row,
                contains=chest_data["contains"],
            )
        )

    potions = [
        PotionState(
            column=potion_position[0],
            row=potion_position[1],
        )
        for potion_position in floor["potions"]
    ]
    boss_room = (
        RoomState.from_mapping(floor["boss_room"])
        if floor["boss_room"] is not None
        else None
    )

    return FloorState(
        map=floor["map"],
        player_column=player_column,
        player_row=player_row,
        enemies=enemies,
        chests=chests,
        potions=potions,
        stairs_column=floor["stairs"][0],
        stairs_row=floor["stairs"][1],
        boss_door=floor["boss_door"],
        boss_room=boss_room,
        boss_columns=floor["boss_columns"],
        boss_emitters=floor["boss_emitters"],
        seal_boss_door_during_fight=floor[
            "seal_boss_door_during_fight"
        ],
        boss_fight_started=floor["boss_door"] is None,
        torches=floor.get("torches", []),
        visual_seed=floor.get("visual_seed", 0),
    )


def create_player_state() -> PlayerState:
    return PlayerState(
        max_health=PLAYER_MAX_HEALTH,
        health=PLAYER_MAX_HEALTH,
        damage_min=PLAYER_DAMAGE_MIN,
        damage_max=PLAYER_DAMAGE_MAX,
    )


def create_game_state(
    floor_index: int = 0,
    opening_message: str = "The descent begins.",
) -> GameState:
    return GameState(
        floor_index=floor_index,
        floor=create_floor_state(floor_index),
        player=create_player_state(),
        combat_log=[opening_message],
    )
