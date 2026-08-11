import random

from acts.act_one.generation import generate_warden_floor
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
from acts.act_three.tmx_loader import load_tmx_floor
from acts.act_three.room_generation import generate_tmx_room_floor


def choose_free_position(candidate_positions, occupied_positions):
    available_positions = [
        position
        for position in candidate_positions
        if position not in occupied_positions
    ]

    if not available_positions:
        return None

    return random.choice(available_positions)


def _create_room_floor(config, boss_room):
    map_columns = config.get("map_columns", MAP_COLUMNS)
    map_rows = config.get("map_rows", MAP_ROWS)
    generation_attempts = config.get("generation_attempts", 1)
    best_generation = None
    best_score = (-1, -1)

    for _ in range(generation_attempts):
        dungeon_map = [
            ["#" for _ in range(map_columns)]
            for _ in range(map_rows)
        ]
        rooms = create_rooms(
            dungeon_map,
            config["room_count"],
            blocked_rooms=[boss_room] if boss_room else None,
        )

        if not rooms:
            continue

        start_column, start_row = room_center(rooms[0])
        farthest_room = max(
            rooms[1:] or rooms,
            key=lambda room: (
                abs(room_center(room)[0] - start_column)
                + abs(room_center(room)[1] - start_row)
            ),
        )
        distance = (
            abs(room_center(farthest_room)[0] - start_column)
            + abs(room_center(farthest_room)[1] - start_row)
        )
        score = (len(rooms), distance)

        if score > best_score:
            best_generation = (dungeon_map, rooms, farthest_room)
            best_score = score

        if (
            len(rooms) >= config["room_count"]
            and distance
            >= config.get("minimum_start_exit_distance", 0)
        ):
            break

    if best_generation is None:
        raise RuntimeError("Unable to generate a dungeon floor")

    dungeon_map, rooms, farthest_room = best_generation
    if farthest_room is not rooms[-1]:
        rooms.remove(farthest_room)
        rooms.append(farthest_room)

    return dungeon_map, rooms


def _set_map_tile(dungeon_map, column, row, tile):
    dungeon_map[row][column] = tile


def _secret_room_candidate(
    dungeon_map,
    approach,
    direction,
):
    approach_column, approach_row = approach
    column_change, row_change = direction
    perpendicular = (-row_change, column_change)
    entrance = (
        approach_column + column_change,
        approach_row + row_change,
    )
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])

    if not (
        0 <= entrance[0] < map_width
        and 0 <= entrance[1] < map_height
        and dungeon_map[entrance[1]][entrance[0]] == "#"
    ):
        return None

    interior = {
        (
            entrance[0]
            + column_change * depth
            + perpendicular[0] * cross_offset,
            entrance[1]
            + row_change * depth
            + perpendicular[1] * cross_offset,
        )
        for depth in range(1, 4)
        for cross_offset in range(-1, 2)
    }
    protected_wall_cells = {
        (column + neighbor_column, row + neighbor_row)
        for column, row in interior
        for neighbor_column in (-1, 0, 1)
        for neighbor_row in (-1, 0, 1)
        if (column + neighbor_column, row + neighbor_row)
        not in interior
    }
    required_solid_cells = (
        interior | protected_wall_cells
    ) - {entrance}

    if any(
        not (0 <= column < map_width and 0 <= row < map_height)
        or dungeon_map[row][column] != "#"
        for column, row in required_solid_cells
    ):
        return None

    stash_positions = [
        (
            entrance[0]
            + column_change * 3
            + perpendicular[0] * cross_offset,
            entrance[1]
            + row_change * 3
            + perpendicular[1] * cross_offset,
        )
        for cross_offset in (-1, 1)
    ]
    return entrance, interior, stash_positions


def _add_secret_stash_room(dungeon_map, chance):
    if chance <= 0 or random.random() >= chance:
        return []

    approaches = [
        (column, row)
        for row, map_row in enumerate(dungeon_map)
        for column, tile in enumerate(map_row)
        if tile == "."
    ]
    random.shuffle(approaches)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for approach in approaches:
        random.shuffle(directions)
        for direction in directions:
            candidate = _secret_room_candidate(
                dungeon_map,
                approach,
                direction,
            )
            if candidate is None:
                continue
            entrance, interior, stash_positions = candidate
            for column, row in interior:
                _set_map_tile(dungeon_map, column, row, "s")
            _set_map_tile(
                dungeon_map,
                entrance[0],
                entrance[1],
                "S",
            )
            return [
                {
                    "position": position,
                    "contains": random.choice(("gold", "potion")),
                    "requires_key": False,
                    "appearance": "stash",
                }
                for position in stash_positions
            ]

    return []


def generate_floor(floor_index):
    config = FLOOR_CONFIGS[floor_index]

    if config.get("room_template_directory"):
        return generate_tmx_room_floor(
            config["map_path"],
            config["room_template_directory"],
            config.get("generated_piece_count", 2),
        )

    if config.get("map_path"):
        return load_tmx_floor(config["map_path"])

    boss_enemy_types = config.get("boss_enemy_types", [])
    boss_room_layout = config.get("boss_room_layout")

    if boss_room_layout == "warden_arena":
        return generate_warden_floor(config)

    if boss_room_layout == "oracle_arena":
        return generate_oracle_floor(config)

    boss_room = (
        create_reserved_boss_room(
            config.get("boss_room_width", BOSS_ROOM_WIDTH),
            config.get("boss_room_height", BOSS_ROOM_HEIGHT),
        )
        if boss_enemy_types
        else None
    )
    dungeon_map, rooms = _create_room_floor(
        config,
        boss_room,
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
        for row, map_row in enumerate(dungeon_map)
        for column, tile in enumerate(map_row)
        if tile == "."
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

    chests.extend(
        _add_secret_stash_room(
            dungeon_map,
            config.get("secret_room_chance", 0),
        )
    )

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
