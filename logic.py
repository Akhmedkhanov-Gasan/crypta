from settings import ENEMY_AGGRO_RADIUS


def can_move_to(dungeon_map, column, row):
    return dungeon_map[row][column] != "#"


def distance_between(first_column, first_row, second_column, second_row):
    return abs(first_column - second_column) + abs(first_row - second_row)


def positions_are_adjacent(first_column, first_row, second_column, second_row):
    return (
        distance_between(
            first_column,
            first_row,
            second_column,
            second_row,
        )
        == 1
    )


def update_enemy_aggro(enemy, player_column, player_row):
    if enemy["is_aggro"]:
        return

    distance_to_player = distance_between(
        enemy["column"],
        enemy["row"],
        player_column,
        player_row,
    )

    if distance_to_player <= ENEMY_AGGRO_RADIUS:
        enemy["is_aggro"] = True


def move_enemy(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
):
    enemy_column = enemy["column"]
    enemy_row = enemy["row"]
    column_distance = player_column - enemy_column
    row_distance = player_row - enemy_row

    if positions_are_adjacent(
        enemy_column,
        enemy_row,
        player_column,
        player_row,
    ):
        return enemy_column, enemy_row

    column_step = 0
    row_step = 0

    if column_distance > 0:
        column_step = 1
    elif column_distance < 0:
        column_step = -1

    if row_distance > 0:
        row_step = 1
    elif row_distance < 0:
        row_step = -1

    if abs(column_distance) >= abs(row_distance):
        possible_moves = [
            (enemy_column + column_step, enemy_row),
            (enemy_column, enemy_row + row_step),
        ]
    else:
        possible_moves = [
            (enemy_column, enemy_row + row_step),
            (enemy_column + column_step, enemy_row),
        ]

    for new_column, new_row in possible_moves:
        target_position = (new_column, new_row)

        if (
            target_position != (player_column, player_row)
            and target_position not in occupied_positions
            and can_move_to(dungeon_map, new_column, new_row)
        ):
            return new_column, new_row

    return enemy_column, enemy_row
