import random

from levels import FLOOR_CONFIGS
from settings import ENEMY_AGGRO_RADIUS, MAP_COLUMNS, MAP_ROWS


MIN_ROOM_WIDTH = 4
MAX_ROOM_WIDTH = 7
MIN_ROOM_HEIGHT = 4
MAX_ROOM_HEIGHT = 6
MAX_ROOM_ATTEMPTS = 250


def room_center(room):
    return (
        room["x"] + room["width"] // 2,
        room["y"] + room["height"] // 2,
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


def create_rooms(dungeon_map, room_count):
    rooms = []

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

        if any(rooms_overlap(room, other_room) for other_room in rooms):
            continue

        carve_room(dungeon_map, room)

        if rooms:
            connect_rooms(dungeon_map, rooms[-1], room)

        rooms.append(room)

    return rooms


def positions_inside_room(room):
    return [
        (column, row)
        for row in range(room["y"] + 1, room["y"] + room["height"] - 1)
        for column in range(
            room["x"] + 1,
            room["x"] + room["width"] - 1,
        )
    ]


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
    dungeon_map = [
        ["#" for _ in range(MAP_COLUMNS)]
        for _ in range(MAP_ROWS)
    ]
    rooms = create_rooms(dungeon_map, config["room_count"])

    player_start = room_center(rooms[0])
    stairs = room_center(rooms[-1])
    occupied_positions = {player_start, stairs}
    all_floor_positions = [
        (column, row)
        for row in range(MAP_ROWS)
        for column in range(MAP_COLUMNS)
        if dungeon_map[row][column] == "."
    ]

    distant_positions = [
        position
        for room in rooms[1:]
        for position in positions_inside_room(room)
        if (
            abs(position[0] - player_start[0])
            + abs(position[1] - player_start[1])
            > ENEMY_AGGRO_RADIUS
        )
    ]
    random.shuffle(distant_positions)

    enemies = []

    for _ in range(config["enemy_count"]):
        enemy_position = choose_free_position(
            distant_positions,
            occupied_positions,
        )

        if enemy_position is None:
            enemy_position = choose_free_position(
                all_floor_positions,
                occupied_positions,
            )

        if enemy_position is None:
            break

        occupied_positions.add(enemy_position)
        enemies.append(
            {
                "position": enemy_position,
                "health": config["enemy_health"],
            }
        )

    chest_rooms = rooms[1:-1] or rooms[1:]
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
                all_floor_positions,
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
        potion_position = choose_free_position(
            all_floor_positions,
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
    }
