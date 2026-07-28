import random

from enemies import ENEMY_TYPES
from levels import FLOOR_CONFIGS
from settings import MAP_COLUMNS, MAP_ROWS
from worldgen.boss_rooms import (
    BOSS_ROOM_HEIGHT,
    BOSS_ROOM_WIDTH,
    create_boss_room_entrance,
    create_oracle_arena,
    create_reserved_boss_room,
    generate_oracle_floor,
    positions_inside_room,
)
from worldgen.geometry import (
    carve_room,
    create_rooms,
    position_is_in_room,
    room_center,
)
from worldgen.act_three import generate_act_three_floor, generate_act_three_test_floor


def choose_free_position(candidate_positions, occupied_positions):
    available_positions = [
        position
        for position in candidate_positions
        if position not in occupied_positions
    ]

    if not available_positions:
        return None

    return random.choice(available_positions)


def generate_floor(floor_index):
    config = FLOOR_CONFIGS[floor_index]

    if config.get("generator") == "act_three":
        return generate_act_three_floor(config)
    if config.get("generator") == "act_three_test":
        return generate_act_three_test_floor(config)

    boss_enemy_types = config.get("boss_enemy_types", [])
    boss_room_layout = config.get("boss_room_layout")

    if boss_room_layout == "oracle_arena":
        return generate_oracle_floor(config)

    dungeon_map = [
        ["#" for _ in range(MAP_COLUMNS)]
        for _ in range(MAP_ROWS)
    ]
    boss_room = (
        create_reserved_boss_room(
            config.get("boss_room_width", BOSS_ROOM_WIDTH),
            config.get("boss_room_height", BOSS_ROOM_HEIGHT),
        )
        if boss_enemy_types
        else None
    )
    rooms = create_rooms(
        dungeon_map,
        config["room_count"],
        blocked_rooms=[boss_room] if boss_room else None,
    )

    if boss_enemy_types:
        carve_room(dungeon_map, boss_room)
        boss_door = create_boss_room_entrance(
            dungeon_map,
            rooms[-1],
            boss_room,
        )
        boss_columns = (
            create_oracle_arena(dungeon_map, boss_room)
            if boss_room_layout == "oracle_arena"
            else []
        )
    else:
        boss_door = None
        boss_columns = []

    player_start = room_center(rooms[0])
    stairs = room_center(boss_room or rooms[-1])
    occupied_positions = {player_start, stairs}
    all_floor_positions = [
        (column, row)
        for row in range(MAP_ROWS)
        for column in range(MAP_COLUMNS)
        if dungeon_map[row][column] == "."
    ]
    non_boss_floor_positions = [
        position
        for position in all_floor_positions
        if (
            boss_room is None
            or not position_is_in_room(position, boss_room)
        )
    ]

    enemy_candidate_positions = [
        position
        for room in rooms[1:]
        for position in positions_inside_room(room)
    ]
    random.shuffle(enemy_candidate_positions)

    enemies = []

    for enemy_type in config["enemy_types"]:
        aggro_radius = ENEMY_TYPES[enemy_type]["aggro_radius"]
        distant_positions = [
            position
            for position in enemy_candidate_positions
            if (
                abs(position[0] - player_start[0])
                + abs(position[1] - player_start[1])
                > aggro_radius
            )
        ]
        enemy_position = choose_free_position(
            distant_positions,
            occupied_positions,
        )

        if enemy_position is None:
            enemy_position = choose_free_position(
                non_boss_floor_positions,
                occupied_positions,
            )

        if enemy_position is None:
            break

        occupied_positions.add(enemy_position)
        enemies.append(
            {
                "position": enemy_position,
                "type": enemy_type,
                "boss_group": False,
            }
        )

    if boss_enemy_types:
        boss_positions = [
            position
            for position in positions_inside_room(boss_room)
            if dungeon_map[position[1]][position[0]] == "."
        ]

        for enemy_type in boss_enemy_types:
            if enemy_type == "oracle":
                enemy_position = room_center(boss_room)
            else:
                enemy_position = choose_free_position(
                    boss_positions,
                    occupied_positions,
                )

            if enemy_position is None:
                break

            occupied_positions.add(enemy_position)
            enemies.append(
                {
                    "position": enemy_position,
                    "type": enemy_type,
                    "boss_group": True,
                }
            )

    chest_rooms = (
        rooms[1:]
        if boss_enemy_types
        else rooms[1:-1] or rooms[1:]
    )
    chest_positions = [
        position
        for room in chest_rooms
        for position in positions_inside_room(room)
    ]
    chests = []

    for _ in range(config["chest_count"]):
        chest_position = choose_free_position(
            chest_positions,
            occupied_positions,
        )

        if chest_position is None:
            chest_position = choose_free_position(
                non_boss_floor_positions,
                occupied_positions,
            )

        if chest_position is None:
            break

        occupied_positions.add(chest_position)
        chests.append(
            {
                "position": chest_position,
                "contains": "gold",
            }
        )

    potion_positions = non_boss_floor_positions

    potions = []

    for _ in range(config["potion_count"]):
        potion_position = choose_free_position(
            potion_positions,
            occupied_positions,
        )

        if potion_position is None:
            break

        occupied_positions.add(potion_position)
        potions.append(potion_position)

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "stairs": stairs,
        "boss_door": (
            boss_door
        ),
        "boss_room": boss_room,
        "boss_columns": boss_columns,
        "boss_emitters": [],
        "seal_boss_door_during_fight": config.get(
            "seal_boss_door_during_fight",
            False,
        ),
        "torches": [],
        "visual_seed": random.randrange(1, 2**31),
    }
