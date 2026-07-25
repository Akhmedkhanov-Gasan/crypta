import random

from worldgen.geometry import (
    carve_horizontal_corridor,
    carve_room,
    carve_vertical_corridor,
    room_center,
)
from settings import MAP_COLUMNS, MAP_ROWS


BOSS_ROOM_WIDTH = 9
BOSS_ROOM_HEIGHT = 9


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
