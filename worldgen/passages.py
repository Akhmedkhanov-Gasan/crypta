def can_create_north_wall_passage(
    dungeon_map,
    room,
) -> bool:
    candidate_wall_rows = (
        room["y"] - 1,
        room["y"],
    )

    return any(
        dungeon_map[wall_row][column] == "#"
        and dungeon_map[wall_row + 1][column] == "."
        for wall_row in candidate_wall_rows
        for column in range(
            room["x"],
            room["x"] + room["width"],
        )
    )


def create_north_wall_passage(
    dungeon_map,
    room,
    passage_id,
    target_floor_index,
    target_passage_id,
    requires_clear=False,
):
    room_center_column = room["x"] + room["width"] // 2
    candidate_columns = sorted(
        range(room["x"], room["x"] + room["width"]),
        key=lambda column: abs(column - room_center_column),
    )

    candidate_wall_rows = (
        room["y"] - 1,
        room["y"],
    )

    for wall_row in candidate_wall_rows:
        trigger_row = wall_row + 1

        for column in candidate_columns:
            if (
                dungeon_map[wall_row][column] == "#"
                and dungeon_map[trigger_row][column] == "."
            ):
                return {
                    "passage_id": passage_id,
                    "wall_position": (column, wall_row),
                    "trigger_position": (column, trigger_row),
                    "target_floor_index": target_floor_index,
                    "target_passage_id": target_passage_id,
                    "requires_clear": requires_clear,
                }

    raise RuntimeError(
        f"Unable to place passage {passage_id!r} "
        f"in room at ({room['x']}, {room['y']})"
    )
