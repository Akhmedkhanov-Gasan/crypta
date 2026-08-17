import random

from acts.act_one.settings import (
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.player_stats import ATTRIBUTE_NAMES
from enemies import ENEMY_TYPES
from generation import generate_floor
from levels import FLOOR_CONFIGS
from game.state import (
    BreakableCrateState,
    ChestState,
    EnemyState,
    FloorState,
    GameState,
    PlayerState,
    PotionState,
    RoomState,
    RuneRoomState,
    SpikeTrapState,
    TreasuryRoomState,
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
        enemies[-1].movement_bounds = enemy_data.get("movement_bounds")

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
    locked_chest_count = sum(
        chest_data.get("requires_key", True)
        for chest_data in floor["chests"]
    )
    key_carrier_count = min(
        locked_chest_count,
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
                requires_key=chest_data.get("requires_key", True),
                appearance=chest_data.get("appearance", "standard"),
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
    spike_traps = [
        SpikeTrapState(
            column=trap_data["position"][0],
            row=trap_data["position"][1],
        )
        for trap_data in floor.get("spike_traps", [])
    ]
    breakable_crates = [
        BreakableCrateState(
            column=crate_data["position"][0],
            row=crate_data["position"][1],
            variant=crate_data["variant"],
        )
        for crate_data in floor.get("breakable_crates", [])
    ]
    treasury_room = (
        TreasuryRoomState.from_mapping(floor["treasury_room"])
        if floor.get("treasury_room") is not None
        else None
    )
    rune_room = (
        RuneRoomState.from_mapping(floor["rune_room"])
        if floor.get("rune_room") is not None
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
        upgrade_altar=floor.get("upgrade_altar"),
        breakable_crates=breakable_crates,
        spike_traps=spike_traps,
        treasury_room=treasury_room,
        rune_room=rune_room,
        torches=floor.get("torches", []),
        tile_layers=floor.get("tile_layers", {}),
        barriers=floor.get("barriers", set()),
        connectors=floor.get("connectors", []),
        visual_seed=floor.get("visual_seed", 0),
    )


def create_player_state() -> PlayerState:
    return PlayerState(
        max_health=PLAYER_STARTING_STATS.max_health,
        health=PLAYER_STARTING_STATS.max_health,
        damage_min=PLAYER_STARTING_STATS.damage_min,
        damage_max=PLAYER_STARTING_STATS.damage_max,
        crit_chance=PLAYER_STARTING_STATS.crit_chance,
        dodge_chance=PLAYER_STARTING_STATS.dodge_chance,
        critical_damage_multiplier=(
            PLAYER_STARTING_STATS.critical_damage_multiplier
        ),
        spell_power=PLAYER_STARTING_STATS.spell_power,
        attribute_ranks={
            attribute: PLAYER_STARTING_ATTRIBUTE_RANKS.get(attribute, 0)
            for attribute in ATTRIBUTE_NAMES
        },
    )


def create_game_state(
    floor_index: int = 0,
    opening_message: str = "The descent begins.",
) -> GameState:
    game_state = GameState(
        floor_index=floor_index,
        floor=create_floor_state(floor_index),
        player=create_player_state(),
        combat_log=[opening_message],
    )
    if FLOOR_CONFIGS[floor_index]["act"] == 2:
        from acts.act_two.consumables import (
            initialize_act_two_consumable_belt,
        )

        initialize_act_two_consumable_belt(game_state.player)
    return game_state
