import random

from levels import FLOOR_CONFIGS
from worldgen.passages import create_north_wall_passage
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
            center_row + row_offset - 1,
        )
        for column_offset in (-5, 5)
        for row_offset in (-3, 0, 3)
    ]

    for column, row in columns:
        dungeon_map[row][column] = "C"

    return columns


def generate_oracle_floor(config, floor_index):
    room_width = config["boss_room_width"]
    room_height = config["boss_room_height"]
    map_columns = max(MAP_COLUMNS, room_width + 4)
    map_rows = room_height + 8

    dungeon_map = [
        ["#" for _ in range(map_columns)]
        for _ in range(map_rows)
    ]

    boss_room = {
        "x": (map_columns - room_width) // 2,
        "y": 2,
        "width": room_width,
        "height": room_height,
    }
    boss_column, boss_row = room_center(boss_room)
    boss_row -= 3

    door_row = boss_room["y"] + boss_room["height"] - 1
    boss_door = (boss_column, door_row)

    approach_room = {
        "x": boss_column - 4,
        "y": door_row,
        "width": 9,
        "height": 5,
    }

    for room in (boss_room, approach_room):
        for row in range(
            room["y"] + 1,
            room["y"] + room["height"] - 1,
        ):
            for column in range(
                room["x"] + 1,
                room["x"] + room["width"] - 1,
            ):
                dungeon_map[row][column] = "."

    for row in range(door_row - 2, door_row + 1):
        for column in range(
            boss_room["x"],
            boss_room["x"] + boss_room["width"],
        ):
            dungeon_map[row][column] = (
                "." if column == boss_column else "#"
            )

    for column in (boss_column - 2, boss_column + 2):
        dungeon_map[door_row + 1][column] = "B"

    boss_columns = create_oracle_arena(
        dungeon_map,
        boss_room,
    )
    boss_emitters = list(boss_columns)

    return_wall_row = (
        approach_room["y"] + approach_room["height"] - 1
    )
    player_start = (boss_column, return_wall_row - 1)

    passages = [
        {
            "passage_id": "entrance",
            "wall_position": (boss_column, return_wall_row),
            "trigger_position": player_start,
            "target_floor_index": floor_index - 1,
            "target_passage_id": "exit",
            "requires_clear": False,
        },
        create_north_wall_passage(
            dungeon_map,
            boss_room,
            "exit",
            (
                floor_index + 1
                if floor_index + 1 < len(FLOOR_CONFIGS)
                else None
            ),
            None,
        ),
    ]

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": [
            {
                "position": (boss_column, boss_row),
                "type": "oracle",
                "boss_group": True,
            }
        ],
        "chests": [],
        "potions": [],
        "passages": passages,
        "stairs": (boss_column, boss_row),
        "boss_door": boss_door,
        "boss_room": boss_room,
        "boss_columns": boss_columns,
        "boss_emitters": boss_emitters,
        "has_oracle_gate": True,
        "seal_boss_door_during_fight": True,
        "torches": [],
        "visual_seed": random.randrange(1, 2**31),
    }
