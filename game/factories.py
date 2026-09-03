import random

from acts.act_one.settings import (
    PLAYER_STARTING_ATTRIBUTE_RANKS,
    PLAYER_STARTING_STATS,
)
from acts.act_two.state import (
    ActOneRevisitCorpseState,
    ActOneRevisitState,
)
from acts.player_stats import ATTRIBUTE_NAMES
from enemies import ENEMY_TYPES
from generation import generate_floor
from levels import FLOOR_CONFIGS
from game.state import (
    BreakableCrateState,
    BloodyAltarState,
    ChestState,
    EnemyState,
    FloorState,
    GameState,
    PassageState,
    PlayerState,
    PotionState,
    RoomState,
    RuneRoomState,
    SpikeTrapState,
    TreasuryRoomState,
    TraderState,
)


def create_floor_state(
    floor_index: int,
    floor_data=None,
    spawn_quest_trader: bool = False,
) -> FloorState:
    if floor_data is not None:
        floor = floor_data
    else:
        floor_config = {
            **FLOOR_CONFIGS[floor_index],
            "quest_trader": spawn_quest_trader,
        }
        floor = generate_floor(
            floor_index,
            config_override=floor_config,
        )
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
        enemy_config = enemy_data.get(
            "config",
            ENEMY_TYPES[enemy_type],
        )
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
            loot_kind=crate_data.get("loot_kind"),
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

    trader_data = floor.get("trader")
    trader = (
        TraderState(
            column=trader_data["position"][0],
            row=trader_data["position"][1],
        )
        if trader_data is not None
        else None
    )

    quest_trader_data = floor.get("quest_trader")
    quest_trader = (
        TraderState(
            column=quest_trader_data["position"][0],
            row=quest_trader_data["position"][1],
        )
        if quest_trader_data is not None
        else None
    )

    bloody_altar_data = floor.get("bloody_altar")
    bloody_altar = (
        BloodyAltarState(
            column=bloody_altar_data["position"][0],
            row=bloody_altar_data["position"][1],
        )
        if bloody_altar_data is not None
        else None
    )
    act_one_revisit_data = floor.get("act_one_revisit")
    act_one_revisit = (
        ActOneRevisitState(
            dead_boss_position=(
                tuple(
                    act_one_revisit_data[
                        "dead_boss_position"
                    ]
                )
                if act_one_revisit_data.get(
                    "dead_boss_position"
                )
                   is not None
                else None
            ),
            guild_seal_position=(
                tuple(
                    act_one_revisit_data[
                        "guild_seal_position"
                    ]
                )
                if act_one_revisit_data.get(
                    "guild_seal_position"
                )
                   is not None
                else None
            ),
            trader_corpse_positions=[
                tuple(position)
                for position in (
                    act_one_revisit_data.get(
                        "trader_corpse_positions",
                        [],
                    )
                )
            ],
            enemy_corpses=[
                ActOneRevisitCorpseState(
                    enemy_type=corpse_data[
                        "enemy_type"
                    ],
                    column=corpse_data[
                        "position"
                    ][0],
                    row=corpse_data[
                        "position"
                    ][1],
                )
                for corpse_data in (
                    act_one_revisit_data.get(
                        "enemy_corpses",
                        [],
                    )
                )
            ],
        )
        if act_one_revisit_data is not None
        else None
    )
    passages = [
        PassageState(
            passage_id=passage_data["passage_id"],
            wall_position=passage_data["wall_position"],
            trigger_position=passage_data["trigger_position"],
            target_floor_index=passage_data["target_floor_index"],
            target_passage_id=passage_data.get("target_passage_id"),
            requires_clear=passage_data.get(
                "requires_clear",
                False,
            ),
            discovered=passage_data.get("discovered", False),
        )
        for passage_data in floor.get("passages", [])
    ]
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
        has_oracle_gate=floor.get("has_oracle_gate", False),
        passages=passages,
        act_one_revisit=act_one_revisit,
        upgrade_altar=floor.get("upgrade_altar"),
        bloody_altar=bloody_altar,
        trader=trader,
        quest_trader=quest_trader,
        breakable_crates=breakable_crates,
        spike_traps=spike_traps,
        treasury_room=treasury_room,
        rune_room=rune_room,
        torches=floor.get("torches", []),
        tile_layers=floor.get("tile_layers", {}),
        barriers=floor.get("barriers", set()),
        connectors=floor.get("connectors", []),
        visual_seed=floor.get("visual_seed", 0),
        presentation_act=floor.get(
            "presentation_act",
            FLOOR_CONFIGS[floor_index]["act"],
        ),
    )


def prepare_act_one_revisit_floors(game_state: GameState):
    if game_state.act_one_revisit_prepared:
        return

    from acts.act_two.generation.act_one_revisit import (
        generate_act_one_revisit_floors,
    )

    generated_floors = generate_act_one_revisit_floors()

    for floor_index, floor_data in generated_floors.items():
        game_state.visited_floors[floor_index] = (
            create_floor_state(
                floor_index,
                floor_data,
            )
        )

    game_state.act_one_revisit_prepared = True

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
    possible_trader_floors = [
        index
        for index, config in enumerate(FLOOR_CONFIGS)
        if (
            config["act"] == 2
            and config["act_floor"] == 1
        )
    ]

    act_two_trader_floor_index = (
        random.choice(possible_trader_floors)
        if possible_trader_floors
        else None
    )

    initial_floor = create_floor_state(
        floor_index,
        spawn_quest_trader=(
            floor_index == act_two_trader_floor_index
        ),
    )

    game_state = GameState(
        floor_index=floor_index,
        floor=initial_floor,
        player=create_player_state(),
        combat_log=[opening_message],
        act_two_trader_floor_index=(
            act_two_trader_floor_index
        ),
    )
    game_state.visited_floors[floor_index] = game_state.floor
    if FLOOR_CONFIGS[floor_index]["act"] == 2:
        from acts.act_two.consumables import (
            initialize_act_two_consumable_belt,
        )

        initialize_act_two_consumable_belt(game_state.player)

    return game_state
