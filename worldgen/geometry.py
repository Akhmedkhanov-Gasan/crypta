import random

from settings import MAP_COLUMNS, MAP_ROWS


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
