import random


ACT_THREE_MAP_COLUMNS = 39
ACT_THREE_MAP_ROWS = 25


def _room_center(room):
    return (
        room["x"] + room["width"] // 2,
        room["y"] + room["height"] // 2,
    )


def _rooms_overlap(first_room, second_room, padding=1):
    return not (
        first_room["x"] + first_room["width"] + padding
        <= second_room["x"]
        or second_room["x"] + second_room["width"] + padding
        <= first_room["x"]
        or first_room["y"] + first_room["height"] + padding
        <= second_room["y"]
        or second_room["y"] + second_room["height"] + padding
        <= first_room["y"]
    )


def _create_rooms(columns, rows, room_count):
    rooms = []

    for _ in range(500):
        if len(rooms) >= room_count:
            break

        width = random.randint(5, 9)
        height = random.randint(5, 8)
        room = {
            "x": random.randint(2, columns - width - 3),
            "y": random.randint(2, rows - height - 3),
            "width": width,
            "height": height,
        }

        if any(
            _rooms_overlap(room, existing_room)
            for existing_room in rooms
        ):
            continue

        rooms.append(room)

    if len(rooms) < 4:
        return _create_rooms(columns, rows, room_count)

    return rooms


def _carve_room(dungeon_map, room):
    for row in range(room["y"], room["y"] + room["height"]):
        for column in range(
            room["x"],
            room["x"] + room["width"],
        ):
            dungeon_map[row][column] = "."


def _carve_horizontal(dungeon_map, start, end, row):
    for column in range(min(start, end), max(start, end) + 1):
        dungeon_map[row][column] = "."


def _carve_vertical(dungeon_map, start, end, column):
    for row in range(min(start, end), max(start, end) + 1):
        dungeon_map[row][column] = "."


def _connect_positions(dungeon_map, first, second):
    first_column, first_row = first
    second_column, second_row = second

    if random.random() < 0.5:
        _carve_horizontal(
            dungeon_map,
            first_column,
            second_column,
            first_row,
        )
        _carve_vertical(
            dungeon_map,
            first_row,
            second_row,
            second_column,
        )
    else:
        _carve_vertical(
            dungeon_map,
            first_row,
            second_row,
            first_column,
        )
        _carve_horizontal(
            dungeon_map,
            first_column,
            second_column,
            second_row,
        )


def _positions_in_room(room):
    return [
        (column, row)
        for row in range(room["y"], room["y"] + room["height"])
        for column in range(
            room["x"],
            room["x"] + room["width"],
        )
    ]


def _choose_position(candidates, occupied_positions):
    available_positions = [
        position
        for position in candidates
        if position not in occupied_positions
    ]

    if not available_positions:
        return None

    return random.choice(available_positions)


def _place_torches(dungeon_map, torch_count):
    rows = len(dungeon_map)
    columns = len(dungeon_map[0])
    candidates = []

    for row in range(1, rows - 1):
        for column in range(1, columns - 1):
            is_exposed_top_wall = (
                dungeon_map[row][column] == "#"
                and dungeon_map[row + 1][column] == "."
                and dungeon_map[row - 1][column] != "."
            )

            if not is_exposed_top_wall:
                continue

            candidates.append((column, row))

    random.shuffle(candidates)
    torches = []

    for minimum_distance in (4, 3, 2, 1):
        for candidate in candidates:
            if candidate in torches:
                continue
            if any(
                abs(candidate[0] - torch[0])
                + abs(candidate[1] - torch[1])
                < minimum_distance
                for torch in torches
            ):
                continue

            torches.append(candidate)

            if len(torches) >= torch_count:
                return torches

    return torches


def generate_act_three_floor(config):
    columns = config.get(
        "map_columns",
        ACT_THREE_MAP_COLUMNS,
    )
    rows = config.get("map_rows", ACT_THREE_MAP_ROWS)
    dungeon_map = [
        ["#" for _ in range(columns)]
        for _ in range(rows)
    ]
    rooms = _create_rooms(
        columns,
        rows,
        config["room_count"],
    )

    for room in rooms:
        _carve_room(dungeon_map, room)

    ordered_rooms = [rooms[0]]
    remaining_rooms = rooms[1:]

    while remaining_rooms:
        previous_center = _room_center(ordered_rooms[-1])
        next_room = min(
            remaining_rooms,
            key=lambda room: (
                abs(_room_center(room)[0] - previous_center[0])
                + abs(_room_center(room)[1] - previous_center[1])
            ),
        )
        ordered_rooms.append(next_room)
        remaining_rooms.remove(next_room)

    for first_room, second_room in zip(
        ordered_rooms,
        ordered_rooms[1:],
    ):
        _connect_positions(
            dungeon_map,
            _room_center(first_room),
            _room_center(second_room),
        )

    extra_connection_count = min(3, len(ordered_rooms) // 2)

    for _ in range(extra_connection_count):
        first_room, second_room = random.sample(
            ordered_rooms,
            2,
        )
        _connect_positions(
            dungeon_map,
            _room_center(first_room),
            _room_center(second_room),
        )

    player_start = _room_center(ordered_rooms[0])
    stairs_room = max(
        ordered_rooms[1:],
        key=lambda room: (
            abs(_room_center(room)[0] - player_start[0])
            + abs(_room_center(room)[1] - player_start[1])
        ),
    )
    stairs = _room_center(stairs_room)
    occupied_positions = {player_start, stairs}
    encounter_rooms = [
        room
        for room in ordered_rooms[1:]
        if room is not stairs_room
    ]
    encounter_positions = [
        position
        for room in encounter_rooms
        for position in _positions_in_room(room)
    ]
    random.shuffle(encounter_positions)
    enemies = []

    for enemy_type in config["enemy_types"]:
        enemy_position = _choose_position(
            encounter_positions,
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

    loot_positions = [
        position
        for room in ordered_rooms[1:]
        if room is not stairs_room
        for position in _positions_in_room(room)
    ]
    chests = []

    for _ in range(config["chest_count"]):
        chest_position = _choose_position(
            loot_positions,
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

    potions = []

    for _ in range(config["potion_count"]):
        potion_position = _choose_position(
            loot_positions,
            occupied_positions,
        )

        if potion_position is None:
            break

        occupied_positions.add(potion_position)
        potions.append(potion_position)

    torches = _place_torches(
        dungeon_map,
        config.get("torch_count", 14),
    )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "stairs": stairs,
        "boss_door": None,
        "boss_room": None,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": False,
        "torches": torches,
        "visual_seed": random.randrange(1, 2**31),
    }
