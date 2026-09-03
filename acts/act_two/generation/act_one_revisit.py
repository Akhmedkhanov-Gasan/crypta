import random

from acts.act_one.generation import generate_warden_floor
from generation import generate_floor
from levels import FLOOR_CONFIGS
from worldgen.passages import create_north_wall_passage

ACT_ONE_REVISIT_ENEMY_COUNTS = {
    0: 6,
    1: 5,
    2: 4,
}


ACT_ONE_REVISIT_GENERATION = {
    0: {
        "map_columns": 35,
        "map_rows": 23,
        "room_count": 7,
        "minimum_start_exit_distance": 18,
        "spike_trap_count": 3,
        "breakable_crate_count": 5,
    },
    1: {
        "map_columns": 39,
        "map_rows": 25,
        "room_count": 8,
        "minimum_start_exit_distance": 21,
        "spike_trap_count": 4,
        "breakable_crate_count": 6,
    },
}


ACT_ONE_REVISIT_CORPSE_TYPES = {
    0: (
        "goblin",
        "goblin",
    ),
    1: (
        "goblin",
        "goblin",
        "brute",
    ),
    2: (
        "goblin",
        "brute",
        "goblin",
        "archer",
        "archer",
    ),
}


TRADER_GROUP_GUARD_TYPES = (
    "goblin",
    "brute",
    "archer",
    "sentinel",
)


def _revisit_generation_config(
    source_floor_index,
    revisit_floor_index,
):
    config = {
        **FLOOR_CONFIGS[source_floor_index],
        **ACT_ONE_REVISIT_GENERATION[
            revisit_floor_index
        ],
    }

    config["treasury_room"] = False
    config["rune_room"] = False
    config["bloody_altar"] = False

    return config


def _create_trader_group_site(floor):
    blocked_positions = {
        floor["player_start"],
        floor["stairs"],
        *(
            enemy["position"]
            for enemy in floor["enemies"]
        ),
        *(
            chest["position"]
            for chest in floor["chests"]
        ),
        *floor["potions"],
        *(
            crate["position"]
            for crate in floor.get(
                "breakable_crates",
                [],
            )
        ),
        *(
            trap["position"]
            for trap in floor.get(
                "spike_traps",
                [],
            )
        ),
        *(
            passage["wall_position"]
            for passage in floor["passages"]
        ),
        *(
            passage["trigger_position"]
            for passage in floor["passages"]
        ),
    }

    candidate_rooms = list(
        floor.get("rooms", [])[1:-1]
    )
    random.shuffle(candidate_rooms)

    for room in candidate_rooms:
        available_positions = [
            (column, row)
            for row in range(
                room["y"],
                room["y"] + room["height"],
            )
            for column in range(
                room["x"],
                room["x"] + room["width"],
            )
            if (
                floor["map"][row][column] == "."
                and (
                    column,
                    row,
                )
                not in blocked_positions
            )
        ]

        if len(available_positions) < 9:
            continue

        room_center = (
            room["x"] + room["width"] // 2,
            room["y"] + room["height"] // 2,
        )

        random.shuffle(available_positions)
        available_positions.sort(
            key=lambda position: (
                abs(position[0] - room_center[0])
                + abs(position[1] - room_center[1])
            )
        )

        seal_position = available_positions[0]
        corpse_positions = available_positions[1:5]
        guard_positions = available_positions[5:9]

        movement_bounds = (
            room["x"],
            room["y"],
            room["x"] + room["width"] - 1,
            room["y"] + room["height"] - 1,
        )

        guards = [
            {
                "type": enemy_type,
                "position": position,
                "boss_group": False,
                "movement_bounds": movement_bounds,
            }
            for enemy_type, position in zip(
                TRADER_GROUP_GUARD_TYPES,
                guard_positions,
            )
        ]

        return {
            "seal_position": seal_position,
            "corpse_positions": corpse_positions,
            "guards": guards,
            "reserved_positions": {
                seal_position,
                *corpse_positions,
                *guard_positions,
            },
        }

    raise RuntimeError(
        "Unable to place the trader group site "
        "on the Act One revisit floor"
    )


def _create_old_enemy_corpses(
    floor,
    revisit_floor_index,
    reserved_positions=(),
):
    blocked_positions = {
        floor["player_start"],
        floor["stairs"],
        *(
            enemy["position"]
            for enemy in floor["enemies"]
        ),
        *(
            chest["position"]
            for chest in floor["chests"]
        ),
        *floor["potions"],
        *(
            crate["position"]
            for crate in floor.get(
                "breakable_crates",
                [],
            )
        ),
        *(
            passage["trigger_position"]
            for passage in floor["passages"]
        ),
        *reserved_positions,
    }

    available_positions = [
        (column, row)
        for row, line in enumerate(floor["map"])
        for column, cell in enumerate(line)
        if (
            cell == "."
            and (column, row) not in blocked_positions
        )
    ]

    corpse_types = (
        ACT_ONE_REVISIT_CORPSE_TYPES[
            revisit_floor_index
        ]
    )

    corpse_count = min(
        len(corpse_types),
        len(available_positions),
    )

    corpse_positions = random.sample(
        available_positions,
        corpse_count,
    )

    return [
        {
            "enemy_type": enemy_type,
            "position": position,
        }
        for enemy_type, position in zip(
            corpse_types,
            corpse_positions,
        )
    ]


def _respawn_enemies(enemies, revisit_floor_index):
    ordinary_enemies = [
        enemy
        for enemy in enemies
        if (
            enemy["type"] != "warden"
            and not enemy.get("boss_group", False)
        )
    ]

    respawn_count = min(
        ACT_ONE_REVISIT_ENEMY_COUNTS[
            revisit_floor_index
        ],
        len(ordinary_enemies),
    )

    if respawn_count <= 0:
        return []

    respawned_enemies = random.sample(
        ordinary_enemies,
        respawn_count,
    )

    return [
        {
            **enemy,
            "boss_group": False,
        }
        for enemy in respawned_enemies
    ]


def _procedural_act_two_source_indices():
    source_indices = [
        floor_index
        for floor_index, config in enumerate(FLOOR_CONFIGS)
        if (
            config["act"] == 2
            and config.get("room_count", 0) > 0
            and config.get("boss_room_layout") is None
        )
    ]

    if len(source_indices) < 2:
        raise RuntimeError(
            "Act One revisit requires two procedural "
            "Act Two floor configurations"
        )

    return source_indices[:2]


def _prepare_first_revisit_floor(source_floor_index):
    floor = generate_floor(
        source_floor_index,
        config_override=_revisit_generation_config(
            source_floor_index,
            0,
        ),
    )

    exit_passage = next(
        passage
        for passage in floor["passages"]
        if passage["passage_id"] == "exit"
    )
    exit_passage["target_floor_index"] = 1
    exit_passage["target_passage_id"] = "entrance"
    exit_passage["requires_clear"] = False

    floor["passages"] = [exit_passage]
    floor["enemies"] = _respawn_enemies(
        floor["enemies"],
        0,
    )

    trader_group_site = _create_trader_group_site(
        floor
    )
    floor["enemies"].extend(
        trader_group_site["guards"]
    )

    floor["trader"] = None
    floor["bloody_altar"] = None
    floor["presentation_act"] = 2
    floor["act_one_revisit"] = {
        "dead_boss_position": None,
        "guild_seal_position": (
            trader_group_site["seal_position"]
        ),
        "trader_corpse_positions": (
            trader_group_site["corpse_positions"]
        ),
        "enemy_corpses": _create_old_enemy_corpses(
            floor,
            0,
            trader_group_site[
                "reserved_positions"
            ],
        ),
    }

    return floor


def _prepare_second_revisit_floor(source_floor_index):
    floor = generate_floor(
        source_floor_index,
        config_override=_revisit_generation_config(
            source_floor_index,
            1,
        ),
    )

    entrance_passage = next(
        passage
        for passage in floor["passages"]
        if passage["passage_id"] == "entrance"
    )
    entrance_passage["target_floor_index"] = 0
    entrance_passage["target_passage_id"] = "exit"
    entrance_passage["requires_clear"] = False

    exit_passage = next(
        passage
        for passage in floor["passages"]
        if passage["passage_id"] == "exit"
    )
    exit_passage["target_floor_index"] = 2
    exit_passage["target_passage_id"] = "entrance"
    exit_passage["requires_clear"] = False

    floor["passages"] = [
        entrance_passage,
        exit_passage,
    ]
    floor["enemies"] = _respawn_enemies(
        floor["enemies"],
        1,
    )
    floor["trader"] = None
    floor["bloody_altar"] = None
    floor["presentation_act"] = 2
    floor["act_one_revisit"] = {
        "dead_boss_position": None,
        "enemy_corpses": _create_old_enemy_corpses(
            floor,
            1,
        ),
        "guild_seal_position": None,
        "trader_corpse_positions": [],
    }

    return floor


def _prepare_boss_revisit_floor():
    floor_index = 2
    floor = generate_warden_floor(
        FLOOR_CONFIGS[floor_index],
        floor_index,
    )

    safe_arrival_room = {
        "x": 1,
        "y": 5,
        "width": 5,
        "height": 5,
    }

    entrance_passage = create_north_wall_passage(
        floor["map"],
        safe_arrival_room,
        "entrance",
        1,
        "exit",
    )

    exit_passage = next(
        passage
        for passage in floor["passages"]
        if passage["passage_id"] == "exit"
    )
    exit_passage["target_floor_index"] = 3
    exit_passage["target_passage_id"] = "entrance"
    exit_passage["requires_clear"] = False

    floor["passages"] = [
        entrance_passage,
        exit_passage,
    ]
    floor["player_start"] = entrance_passage[
        "trigger_position"
    ]
    floor["enemies"] = _respawn_enemies(
        floor["enemies"],
        2,
    )
    floor["boss_door"] = None
    floor["seal_boss_door_during_fight"] = False
    floor["potions"] = []
    floor["presentation_act"] = 2
    floor["act_one_revisit"] = {
        "dead_boss_position": (19, 7),
        "enemy_corpses": _create_old_enemy_corpses(
            floor,
            2,
        ),
        "guild_seal_position": None,
        "trader_corpse_positions": [],
    }

    return floor


def generate_act_one_revisit_floors():
    first_source_index, second_source_index = (
        _procedural_act_two_source_indices()
    )

    return {
        0: _prepare_first_revisit_floor(
            first_source_index
        ),
        1: _prepare_second_revisit_floor(
            second_source_index
        ),
        2: _prepare_boss_revisit_floor(),
    }


__all__ = ["generate_act_one_revisit_floors"]