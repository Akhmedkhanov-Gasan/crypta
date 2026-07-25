import random

from enemies import ENEMY_TYPES
from levels import FLOOR_CONFIGS
from settings import MAP_COLUMNS, MAP_ROWS


MIN_ROOM_WIDTH = 4
MAX_ROOM_WIDTH = 7
MIN_ROOM_HEIGHT = 4
MAX_ROOM_HEIGHT = 6
MAX_ROOM_ATTEMPTS = 250
BOSS_ROOM_WIDTH = 9
BOSS_ROOM_HEIGHT = 9


def room_center(room):
    return (
        room["x"] + room["width"] // 2,
        room["y"] + room["height"] // 2,
    )


def position_is_in_room(position, room):
    return (
        room["x"] <= position[0] < room["x"] + room["width"]
        and room["y"] <= position[1] < room["y"] + room["height"]
    )


def position_is_in_room_interior(position, room):
    return (
        room["x"] < position[0] < room["x"] + room["width"] - 1
        and room["y"] < position[1] < room["y"] + room["height"] - 1
    )


def rooms_overlap(first_room, second_room):
    return not (
        first_room["x"] + first_room["width"] + 1
        <= second_room["x"]
        or second_room["x"] + second_room["width"] + 1
        <= first_room["x"]
        or first_room["y"] + first_room["height"] + 1
        <= second_room["y"]
        or second_room["y"] + second_room["height"] + 1
        <= first_room["y"]
    )


def carve_room(dungeon_map, room):
    for row in range(room["y"], room["y"] + room["height"]):
        for column in range(
            room["x"],
            room["x"] + room["width"],
        ):
            dungeon_map[row][column] = "."


def carve_horizontal_corridor(dungeon_map, first_column, second_column, row):
    corridor_start = min(first_column, second_column)
    corridor_end = max(first_column, second_column)

    for column in range(corridor_start, corridor_end + 1):
        dungeon_map[row][column] = "."


def carve_vertical_corridor(dungeon_map, first_row, second_row, column):
    corridor_start = min(first_row, second_row)
    corridor_end = max(first_row, second_row)

    for row in range(corridor_start, corridor_end + 1):
        dungeon_map[row][column] = "."


def connect_rooms(dungeon_map, first_room, second_room):
    first_column, first_row = room_center(first_room)
    second_column, second_row = room_center(second_room)
    corridor_path = []

    if random.choice((True, False)):
        carve_horizontal_corridor(
            dungeon_map,
            first_column,
            second_column,
            first_row,
        )
        carve_vertical_corridor(
            dungeon_map,
            first_row,
            second_row,
            second_column,
        )
        horizontal_step = 1 if second_column >= first_column else -1
        vertical_step = 1 if second_row >= first_row else -1
        corridor_path.extend(
            (column, first_row)
            for column in range(
                first_column,
                second_column + horizontal_step,
                horizontal_step,
            )
        )
        corridor_path.extend(
            (second_column, row)
            for row in range(
                first_row + vertical_step,
                second_row + vertical_step,
                vertical_step,
            )
        )
    else:
        carve_vertical_corridor(
            dungeon_map,
            first_row,
            second_row,
            first_column,
        )
        carve_horizontal_corridor(
            dungeon_map,
            first_column,
            second_column,
            second_row,
        )
        vertical_step = 1 if second_row >= first_row else -1
        horizontal_step = 1 if second_column >= first_column else -1
        corridor_path.extend(
            (first_column, row)
            for row in range(
                first_row,
                second_row + vertical_step,
                vertical_step,
            )
        )
        corridor_path.extend(
            (column, second_row)
            for column in range(
                first_column + horizontal_step,
                second_column + horizontal_step,
                horizontal_step,
            )
        )

    for position_index, position in enumerate(corridor_path):
        if not position_is_in_room_interior(position, second_room):
            continue

        if position_index > 0:
            previous_position = corridor_path[position_index - 1]

            if position_is_in_room(
                previous_position,
                second_room,
            ):
                return previous_position

        return position

    return room_center(second_room)


def create_rooms(dungeon_map, room_count, blocked_rooms=None):
    rooms = []
    blocked_rooms = blocked_rooms or []

    for _ in range(MAX_ROOM_ATTEMPTS):
        if len(rooms) >= room_count:
            break

        width = random.randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
        height = random.randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
        room = {
            "x": random.randint(1, MAP_COLUMNS - width - 2),
            "y": random.randint(1, MAP_ROWS - height - 2),
            "width": width,
            "height": height,
        }

        unavailable_rooms = [*rooms, *blocked_rooms]

        if any(
            rooms_overlap(room, other_room)
            for other_room in unavailable_rooms
        ):
            continue

        carve_room(dungeon_map, room)

        if rooms:
            room["entrance"] = connect_rooms(
                dungeon_map,
                rooms[-1],
                room,
            )

        rooms.append(room)

    return rooms


def create_reserved_boss_room(
    width=BOSS_ROOM_WIDTH,
    height=BOSS_ROOM_HEIGHT,
):
    maximum_x = MAP_COLUMNS - width - 2
    maximum_y = MAP_ROWS - height - 2

    return {
        "x": random.choice((1, maximum_x)),
        "y": random.randint(1, maximum_y),
        "width": width,
        "height": height,
    }


def seal_room_except_door(dungeon_map, room, door_position):
    left = room["x"]
    right = room["x"] + room["width"] - 1
    top = room["y"]
    bottom = room["y"] + room["height"] - 1

    for column in range(left, right + 1):
        dungeon_map[top][column] = "#"
        dungeon_map[bottom][column] = "#"

    for row in range(top, bottom + 1):
        dungeon_map[row][left] = "#"
        dungeon_map[row][right] = "#"

    door_column, door_row = door_position
    dungeon_map[door_row][door_column] = "."


def create_boss_room_entrance(
    dungeon_map,
    previous_room,
    boss_room,
):
    previous_column, previous_row = room_center(previous_room)
    boss_column, boss_row = room_center(boss_room)
    horizontal_distance = previous_column - boss_column
    vertical_distance = previous_row - boss_row
    left = boss_room["x"]
    right = boss_room["x"] + boss_room["width"] - 1
    top = boss_room["y"]
    bottom = boss_room["y"] + boss_room["height"] - 1

    if abs(horizontal_distance) >= abs(vertical_distance):
        door_column = left if horizontal_distance < 0 else right
        door_row = boss_row
        outside_column = (
            door_column - 1
            if door_column == left
            else door_column + 1
        )
        outside_row = door_row

        seal_room_except_door(
            dungeon_map,
            boss_room,
            (door_column, door_row),
        )
        carve_vertical_corridor(
            dungeon_map,
            previous_row,
            outside_row,
            previous_column,
        )
        carve_horizontal_corridor(
            dungeon_map,
            previous_column,
            outside_column,
            outside_row,
        )
    else:
        door_column = boss_column
        door_row = top if vertical_distance < 0 else bottom
        outside_column = door_column
        outside_row = (
            door_row - 1
            if door_row == top
            else door_row + 1
        )

        seal_room_except_door(
            dungeon_map,
            boss_room,
            (door_column, door_row),
        )
        carve_horizontal_corridor(
            dungeon_map,
            previous_column,
            outside_column,
            previous_row,
        )
        carve_vertical_corridor(
            dungeon_map,
            previous_row,
            outside_row,
            outside_column,
        )

    return door_column, door_row


def positions_inside_room(room):
    return [
        (column, row)
        for row in range(room["y"] + 1, room["y"] + room["height"] - 1)
        for column in range(
            room["x"] + 1,
            room["x"] + room["width"] - 1,
        )
    ]


def create_oracle_arena(dungeon_map, boss_room):
    center_column, center_row = room_center(boss_room)
    columns = [
        (
            center_column + column_offset,
            center_row + row_offset,
        )
        for row_offset in (-3, 3)
        for column_offset in (-6, -2, 2, 6)
    ]

    for column, row in columns:
        dungeon_map[row][column] = "C"

    return columns


def generate_oracle_floor(config):
    dungeon_map = [
        ["#" for _ in range(MAP_COLUMNS)]
        for _ in range(MAP_ROWS)
    ]
    boss_room = {
        "x": 5,
        "y": 1,
        "width": config["boss_room_width"],
        "height": config["boss_room_height"],
    }
    carve_room(dungeon_map, boss_room)
    boss_column, boss_row = room_center(boss_room)
    boss_door = (boss_room["x"], boss_row)
    seal_room_except_door(
        dungeon_map,
        boss_room,
        boss_door,
    )

    for row in range(boss_row - 2, boss_row + 3):
        for column in range(1, boss_room["x"]):
            dungeon_map[row][column] = "."

    boss_columns = create_oracle_arena(
        dungeon_map,
        boss_room,
    )
    boss_emitters = [
        position
        for position in boss_columns
        if abs(position[0] - boss_column) == 6
    ]

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": (2, boss_row),
        "enemies": [
            {
                "position": (boss_column, boss_row),
                "type": "oracle",
                "boss_group": True,
            }
        ],
        "chests": [],
        "potions": [],
        "stairs": (boss_column, boss_row),
        "boss_door": boss_door,
        "boss_room": boss_room,
        "boss_columns": boss_columns,
        "boss_emitters": boss_emitters,
        "seal_boss_door_during_fight": True,
    }


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
    }
