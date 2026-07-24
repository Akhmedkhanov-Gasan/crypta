import random
from collections import deque

from settings import (
    ENEMY_AGGRO_RADIUS,
    ENEMY_DAMAGE_VALUES,
    ENEMY_DAMAGE_WEIGHTS,
    ENEMY_WANDER_CHANCE,
    PLAYER_DAMAGE_MAX,
    PLAYER_DAMAGE_MIN,
)


def roll_player_damage():
    return random.randint(PLAYER_DAMAGE_MIN, PLAYER_DAMAGE_MAX)


def roll_enemy_damage():
    return random.choices(
        ENEMY_DAMAGE_VALUES,
        weights=ENEMY_DAMAGE_WEIGHTS,
        k=1,
    )[0]


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


def ordered_neighboring_positions(
    column,
    row,
    target_column,
    target_row,
):
    neighboring_positions = [
        (column, row - 1),
        (column, row + 1),
        (column - 1, row),
        (column + 1, row),
    ]
    horizontal_distance = abs(target_column - column)
    vertical_distance = abs(target_row - row)
    prefer_horizontal = horizontal_distance >= vertical_distance

    def position_priority(position):
        next_column, next_row = position
        distance_to_target = distance_between(
            next_column,
            next_row,
            target_column,
            target_row,
        )
        move_is_horizontal = next_row == row
        preferred_axis = move_is_horizontal == prefer_horizontal

        return distance_to_target, not preferred_axis

    neighboring_positions.sort(key=position_priority)
    return neighboring_positions


def move_enemy(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
):
    start_position = (enemy["column"], enemy["row"])
    player_position = (player_column, player_row)

    if positions_are_adjacent(
        enemy["column"],
        enemy["row"],
        player_column,
        player_row,
    ):
        return start_position

    positions_to_visit = deque([start_position])
    previous_position = {start_position: None}

    while positions_to_visit:
        current_column, current_row = positions_to_visit.popleft()

        if (current_column, current_row) == player_position:
            break

        neighboring_positions = ordered_neighboring_positions(
            current_column,
            current_row,
            player_column,
            player_row,
        )

        for next_position in neighboring_positions:
            if next_position in previous_position:
                continue

            next_column, next_row = next_position
            target_is_player = next_position == player_position

            if not target_is_player and (
                next_position in occupied_positions
                or not can_move_to(dungeon_map, next_column, next_row)
            ):
                continue

            previous_position[next_position] = (
                current_column,
                current_row,
            )
            positions_to_visit.append(next_position)

    if player_position not in previous_position:
        return start_position

    next_step = player_position

    while previous_position[next_step] != start_position:
        next_step = previous_position[next_step]

    return next_step


def move_enemy_randomly(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
):
    enemy_column = enemy["column"]
    enemy_row = enemy["row"]

    if random.random() >= ENEMY_WANDER_CHANCE:
        return enemy_column, enemy_row

    possible_moves = [
        (enemy_column, enemy_row - 1),
        (enemy_column, enemy_row + 1),
        (enemy_column - 1, enemy_row),
        (enemy_column + 1, enemy_row),
    ]
    random.shuffle(possible_moves)

    for new_column, new_row in possible_moves:
        target_position = (new_column, new_row)

        if (
            target_position != (player_column, player_row)
            and target_position not in occupied_positions
            and can_move_to(dungeon_map, new_column, new_row)
        ):
            return new_column, new_row

    return enemy_column, enemy_row
