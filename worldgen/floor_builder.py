import random

from acts.act_one.generation import generate_warden_floor
from acts.act_two.settings import ACT_TWO_CHEST_LOOT_WEIGHTS
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


TREASURY_ROOM_WIDTH = 7
TREASURY_ROOM_HEIGHT = 6
RUNE_ROOM_WIDTH = 5
RUNE_ROOM_HEIGHT = 5
BREAKABLE_CRATE_MIN_SPACING_TILES = 3


def choose_free_position(candidate_positions, occupied_positions):
    available_positions = [
        position
        for position in candidate_positions
        if position not in occupied_positions
    ]

    if not available_positions:
        return None

    return random.choice(available_positions)


def _place_breakable_crates(
    dungeon_map,
    candidate_positions,
    count,
    occupied_positions,
    protected_positions,
):
    candidates = list(candidate_positions)
    random.shuffle(candidates)
    crates = []

    for position in candidates:
        if len(crates) >= count:
            break
        if position in occupied_positions:
            continue
        column, row = position
        if not any(
            dungeon_map[row + row_change][column + column_change]
            in ("#", "S")
            for column_change, row_change in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            )
        ):
            continue
        if any(
            abs(position[0] - protected[0])
            + abs(position[1] - protected[1])
            < BREAKABLE_CRATE_MIN_SPACING_TILES
            for protected in protected_positions
        ):
            continue
        if any(
            abs(position[0] - crate["position"][0])
            + abs(position[1] - crate["position"][1])
            < BREAKABLE_CRATE_MIN_SPACING_TILES
            for crate in crates
        ):
            continue
        occupied_positions.add(position)
        crates.append(
            {
                "position": position,
                "variant": random.randint(1, 3),
            }
        )

    return crates


def _treasury_room_candidates(dungeon_map):
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])
    width = TREASURY_ROOM_WIDTH
    height = TREASURY_ROOM_HEIGHT
    candidates = []

    for top in range(1, map_height - height - 1):
        for left in range(1, map_width - width - 1):
            footprint = {
                (column, row)
                for row in range(top - 1, top + height + 1)
                for column in range(left - 1, left + width + 1)
            }
            if any(
                dungeon_map[row][column] != "#"
                for column, row in footprint
            ):
                continue

            center_column = left + width // 2
            center_row = top + height // 2
            entrances = (
                (
                    (center_column, top - 1),
                    (center_column, top - 2),
                    "horizontal",
                ),
                (
                    (center_column, top + height),
                    (center_column, top + height + 1),
                    "horizontal",
                ),
                (
                    (left - 1, center_row),
                    (left - 2, center_row),
                    "vertical",
                ),
                (
                    (left + width, center_row),
                    (left + width + 1, center_row),
                    "vertical",
                ),
            )

            for door_position, approach, orientation in entrances:
                if not (
                    0 <= approach[0] < map_width
                    and 0 <= approach[1] < map_height
                    and dungeon_map[approach[1]][approach[0]] == "."
                ):
                    continue
                candidates.append(
                    {
                        "x": left,
                        "y": top,
                        "width": width,
                        "height": height,
                        "door_position": door_position,
                        "door_orientation": orientation,
                    }
                )

    return candidates


def _rune_room_candidates(dungeon_map):
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])
    width = RUNE_ROOM_WIDTH
    height = RUNE_ROOM_HEIGHT
    candidates = []

    for top in range(1, map_height - height - 1):
        for left in range(1, map_width - width - 1):
            footprint = {
                (column, row)
                for row in range(top - 1, top + height + 1)
                for column in range(left - 1, left + width + 1)
            }
            if any(
                dungeon_map[row][column] != "#"
                for column, row in footprint
            ):
                continue

            center_column = left + width // 2
            center_row = top + height // 2
            entrances = (
                (
                    (center_column, top - 1),
                    (center_column, top - 2),
                    (0, 1),
                ),
                (
                    (center_column, top + height),
                    (center_column, top + height + 1),
                    (0, -1),
                ),
                (
                    (left - 1, center_row),
                    (left - 2, center_row),
                    (1, 0),
                ),
                (
                    (left + width, center_row),
                    (left + width + 1, center_row),
                    (-1, 0),
                ),
            )
            for door_position, approach, inward_direction in entrances:
                if not (
                    0 <= approach[0] < map_width
                    and 0 <= approach[1] < map_height
                    and dungeon_map[approach[1]][approach[0]] == "."
                ):
                    continue
                candidates.append(
                    {
                        "x": left,
                        "y": top,
                        "width": width,
                        "height": height,
                        "door_position": door_position,
                        "inward_direction": inward_direction,
                    }
                )

    return candidates


def _candidate_footprint(room):
    return {
        (column, row)
        for row in range(room["y"] - 1, room["y"] + room["height"] + 1)
        for column in range(
            room["x"] - 1,
            room["x"] + room["width"] + 1,
        )
    }


def _candidate_has_compatible_room(candidate, other_candidates):
    footprint = _candidate_footprint(candidate)
    return any(
        footprint.isdisjoint(_candidate_footprint(other))
        for other in other_candidates
    )


def _add_treasury_room(dungeon_map, compatible_rooms=()):
    candidates = _treasury_room_candidates(dungeon_map)
    if compatible_rooms:
        candidates = [
            candidate
            for candidate in candidates
            if _candidate_has_compatible_room(
                candidate,
                compatible_rooms,
            )
        ]
    if not candidates:
        raise RuntimeError("Unable to place the Act Two treasury room")

    room = random.choice(candidates)
    left = room["x"]
    top = room["y"]
    width = room["width"]
    height = room["height"]
    center_column = left + width // 2

    for row in range(top, top + height):
        for column in range(left, left + width):
            _set_map_tile(dungeon_map, column, row, "r")

    chest_position = (center_column, top + 1)
    statue_positions = (
        (center_column - 1, top + 1),
        (center_column + 1, top + 1),
    )
    enemy_spawn_positions = (
        (left + 1, top + 2),
        (left + width - 2, top + 2),
        (left + 1, top + height - 2),
        (left + width - 2, top + height - 2),
    )

    _set_map_tile(dungeon_map, chest_position[0], chest_position[1], "H")
    for statue_position in statue_positions:
        _set_map_tile(
            dungeon_map,
            statue_position[0],
            statue_position[1],
            "T",
        )
    _set_map_tile(
        dungeon_map,
        room["door_position"][0],
        room["door_position"][1],
        ".",
    )

    room.update(
        {
            "chest_position": chest_position,
            "statue_positions": statue_positions,
            "enemy_spawn_positions": enemy_spawn_positions,
        }
    )
    return room


def _add_rune_room(dungeon_map):
    candidates = _rune_room_candidates(dungeon_map)
    if not candidates:
        raise RuntimeError("Unable to place the Act Two rune room")

    room = random.choice(candidates)
    left = room["x"]
    top = room["y"]
    width = room["width"]
    height = room["height"]
    door_column, door_row = room["door_position"]
    inward_column, inward_row = room["inward_direction"]
    perpendicular = (-inward_row, inward_column)

    for row in range(top, top + height):
        for column in range(left, left + width):
            _set_map_tile(dungeon_map, column, row, "r")

    pedestal_position = (
        door_column + inward_column * 4,
        door_row + inward_row * 4,
    )
    floor_rune_center = (
        door_column + inward_column * 3,
        door_row + inward_row * 3,
    )
    floor_rune_positions = tuple(
        (
            floor_rune_center[0] + perpendicular[0] * offset,
            floor_rune_center[1] + perpendicular[1] * offset,
        )
        for offset in (-1, 0, 1)
    )
    _set_map_tile(
        dungeon_map,
        pedestal_position[0],
        pedestal_position[1],
        "P",
    )
    _set_map_tile(dungeon_map, door_column, door_row, ".")
    room.update(
        {
            "pedestal_position": pedestal_position,
            "floor_rune_positions": floor_rune_positions,
            "wall_rune_positions": (),
        }
    )
    return room


def _treasury_reserved_positions(room):
    if room is None:
        return set()
    return {
        (column, row)
        for row in range(room["y"], room["y"] + room["height"])
        for column in range(room["x"], room["x"] + room["width"])
    } | {room["door_position"]}


def _rune_reserved_positions(room):
    if room is None:
        return set()
    return {
        (column, row)
        for row in range(room["y"], room["y"] + room["height"])
        for column in range(room["x"], room["x"] + room["width"])
    } | {room["door_position"]}


def _place_rune_wall_positions(dungeon_map, room):
    if room is None:
        return ()

    door_column, door_row = room["door_position"]
    room_cells = _rune_reserved_positions(room)
    walkable_tiles = {"."}
    candidates = []
    for row, map_row in enumerate(dungeon_map):
        for column, tile in enumerate(map_row):
            if tile != "#" or (column, row) in room_cells:
                continue
            distance = abs(column - door_column) + abs(row - door_row)
            if distance < 8:
                continue
            neighbors = (
                (column - 1, row),
                (column + 1, row),
                (column, row - 1),
                (column, row + 1),
            )
            if any(
                0 <= neighbor_row < len(dungeon_map)
                and 0 <= neighbor_column < len(map_row)
                and dungeon_map[neighbor_row][neighbor_column]
                in walkable_tiles
                for neighbor_column, neighbor_row in neighbors
            ):
                candidates.append((column, row))

    if len(candidates) < 3:
        raise RuntimeError("Unable to place three Act Two wall runes")

    random.shuffle(candidates)
    selected = [
        max(
            candidates,
            key=lambda position: (
                abs(position[0] - door_column)
                + abs(position[1] - door_row)
            ),
        )
    ]
    while len(selected) < 3:
        remaining = [
            position
            for position in candidates
            if position not in selected
        ]
        selected.append(
            max(
                remaining,
                key=lambda position: (
                    min(
                        abs(position[0] - other[0])
                        + abs(position[1] - other[1])
                        for other in selected
                    ),
                    abs(position[0] - door_column)
                    + abs(position[1] - door_row),
                ),
            )
        )
    return tuple(selected)



def _create_room_floor(config, boss_room):
    map_columns = config.get("map_columns", MAP_COLUMNS)
    map_rows = config.get("map_rows", MAP_ROWS)
    treasury_enabled = config.get("treasury_room", False)
    rune_room_enabled = config.get("rune_room", False)
    generation_attempts = config.get("generation_attempts", 1)
    if treasury_enabled or rune_room_enabled:
        generation_attempts = max(80, generation_attempts)
    best_generation = None
    best_score = (-1, -1, -1)

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
        treasury_candidates = (
            _treasury_room_candidates(dungeon_map)
            if treasury_enabled
            else ()
        )
        rune_room_candidates = (
            _rune_room_candidates(dungeon_map)
            if rune_room_enabled
            else ()
        )
        compatible_special_rooms = (
            not treasury_enabled
            or not rune_room_enabled
            or any(
                _candidate_has_compatible_room(
                    treasury_candidate,
                    rune_room_candidates,
                )
                for treasury_candidate in treasury_candidates
            )
        )
        special_rooms_available = (
            (not treasury_enabled or bool(treasury_candidates))
            and (not rune_room_enabled or bool(rune_room_candidates))
            and compatible_special_rooms
        )
        score = (
            int(special_rooms_available),
            len(rooms),
            distance,
        )

        if score > best_score:
            best_generation = (dungeon_map, rooms, farthest_room)
            best_score = score

        if (
            len(rooms) >= config["room_count"]
            and distance
            >= config.get("minimum_start_exit_distance", 0)
            and special_rooms_available
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


def _place_spike_traps(
    dungeon_map,
    count,
    protected_positions,
    player_start,
    stairs,
):
    if count <= 0:
        return []

    candidates = [
        (column, row)
        for row, map_row in enumerate(dungeon_map)
        for column, tile in enumerate(map_row)
        if tile == "."
    ]
    random.shuffle(candidates)
    selected_positions = []

    for position in candidates:
        if (
            abs(position[0] - player_start[0])
            + abs(position[1] - player_start[1])
            < 5
        ):
            continue
        if (
            abs(position[0] - stairs[0])
            + abs(position[1] - stairs[1])
            < 3
        ):
            continue
        if any(
            abs(position[0] - protected[0])
            + abs(position[1] - protected[1])
            < 2
            for protected in protected_positions
        ):
            continue
        if any(
            abs(position[0] - selected[0])
            + abs(position[1] - selected[1])
            < 5
            for selected in selected_positions
        ):
            continue

        selected_positions.append(position)
        if len(selected_positions) >= count:
            break

    return [
        {"position": position}
        for position in selected_positions
    ]


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
    rune_room_candidates = (
        _rune_room_candidates(dungeon_map)
        if config.get("rune_room", False)
        else ()
    )
    treasury_room = (
        _add_treasury_room(
            dungeon_map,
            rune_room_candidates,
        )
        if config.get("treasury_room", False)
        else None
    )
    rune_room = (
        _add_rune_room(dungeon_map)
        if config.get("rune_room", False)
        else None
    )
    treasury_reserved_positions = _treasury_reserved_positions(
        treasury_room
    )
    rune_reserved_positions = _rune_reserved_positions(rune_room)
    special_room_reserved_positions = (
        treasury_reserved_positions | rune_reserved_positions
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
        and position not in special_room_reserved_positions
    ]
    non_boss_floor_position_set = set(non_boss_floor_positions)
    ordinary_room_floor_positions = [
        (column, row)
        for room in rooms
        for row in range(room["y"], room["y"] + room["height"])
        for column in range(
            room["x"],
            room["x"] + room["width"],
        )
        if (
            (column, row) in non_boss_floor_position_set
            and dungeon_map[row][column] == "."
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
                "contains": (
                    random.choices(
                        [
                            item
                            for item, _weight
                            in ACT_TWO_CHEST_LOOT_WEIGHTS
                        ],
                        weights=[
                            weight
                            for _item, weight
                            in ACT_TWO_CHEST_LOOT_WEIGHTS
                        ],
                        k=1,
                    )[0]
                    if config["act"] == 2
                    else "gold"
                ),
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

    breakable_crates = _place_breakable_crates(
        dungeon_map,
        ordinary_room_floor_positions,
        config.get("breakable_crate_count", 0),
        occupied_positions,
        (player_start, stairs),
    )

    chests.extend(
        _add_secret_stash_room(
            dungeon_map,
            config.get("secret_room_chance", 0),
        )
    )
    if rune_room is not None:
        rune_room["wall_rune_positions"] = _place_rune_wall_positions(
            dungeon_map,
            rune_room,
        )
    protected_positions = {
        player_start,
        stairs,
        *(enemy["position"] for enemy in enemies),
        *(chest["position"] for chest in chests),
        *potions,
        *(crate["position"] for crate in breakable_crates),
        *special_room_reserved_positions,
    }
    spike_traps = _place_spike_traps(
        dungeon_map,
        config.get("spike_trap_count", 0),
        protected_positions,
        player_start,
        stairs,
    )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "breakable_crates": breakable_crates,
        "spike_traps": spike_traps,
        "treasury_room": treasury_room,
        "rune_room": rune_room,
        "rooms": rooms,
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
