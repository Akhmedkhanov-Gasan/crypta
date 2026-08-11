import random
from collections import deque

def roll_player_damage(damage_minimum, damage_maximum):
    return random.randint(damage_minimum, damage_maximum)


def roll_enemy_damage(enemy, attack_mode):
    damage_by_mode = enemy["damage_by_mode"]

    if (
        enemy.get("oracle_awakened", False)
        and enemy.get("phase_two_damage_by_mode")
    ):
        damage_by_mode = enemy["phase_two_damage_by_mode"]

    damage_values, damage_weights = damage_by_mode[attack_mode]

    return random.choices(
        damage_values,
        weights=damage_weights,
        k=1,
    )[0]


def can_move_to(dungeon_map, column, row):
    if not (
        0 <= row < len(dungeon_map)
        and 0 <= column < len(dungeon_map[row])
    ):
        return False
    return dungeon_map[row][column] not in ("#", "B", "C", "S")


def can_move_between(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
    barriers=(),
):
    if (
        abs(target_column - start_column)
        + abs(target_row - start_row)
        != 1
    ):
        return False
    if not can_move_to(dungeon_map, target_column, target_row):
        return False

    edge = tuple(
        sorted(
            (
                (start_column, start_row),
                (target_column, target_row),
            )
        )
    )
    return edge not in barriers


def distance_between(first_column, first_row, second_column, second_row):
    return abs(first_column - second_column) + abs(first_row - second_row)


def direction_toward(
    start_column,
    start_row,
    target_column,
    target_row,
):
    column_distance = target_column - start_column
    row_distance = target_row - start_row

    if abs(column_distance) >= abs(row_distance):
        return (1 if column_distance > 0 else -1, 0)

    return (0, 1 if row_distance > 0 else -1)


def get_directional_line(
    dungeon_map,
    start_column,
    start_row,
    column_change,
    row_change,
    maximum_range,
    blocking_positions,
):
    positions = []
    map_height = len(dungeon_map)
    map_width = len(dungeon_map[0])

    for distance in range(1, maximum_range + 1):
        column = start_column + column_change * distance
        row = start_row + row_change * distance

        if not (
            0 <= column < map_width
            and 0 <= row < map_height
            and can_move_to(dungeon_map, column, row)
        ):
            break

        if (column, row) in blocking_positions:
            break

        positions.append((column, row))

    return positions


def get_enemy_occupied_positions(enemy):
    half_width = enemy.get("footprint_width", 1) // 2
    half_height = enemy.get("footprint_height", 1) // 2

    return {
        (column, row)
        for row in range(
            enemy["row"] - half_height,
            enemy["row"] + half_height + 1,
        )
        for column in range(
            enemy["column"] - half_width,
            enemy["column"] + half_width + 1,
        )
    }


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


def has_line_of_sight(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
):
    current_column = start_column
    current_row = start_row
    column_distance = abs(target_column - start_column)
    row_distance = abs(target_row - start_row)
    column_step = 1 if start_column < target_column else -1
    row_step = 1 if start_row < target_row else -1
    error = column_distance - row_distance

    while (current_column, current_row) != (
        target_column,
        target_row,
    ):
        previous_column = current_column
        previous_row = current_row
        doubled_error = error * 2

        if doubled_error > -row_distance:
            error -= row_distance
            current_column += column_step

        if doubled_error < column_distance:
            error += column_distance
            current_row += row_step

        moved_diagonally = (
            current_column != previous_column
            and current_row != previous_row
        )

        if moved_diagonally:
            horizontal_side_is_wall = not can_move_to(
                dungeon_map,
                current_column,
                previous_row,
            )
            vertical_side_is_wall = not can_move_to(
                dungeon_map,
                previous_column,
                current_row,
            )

            if horizontal_side_is_wall and vertical_side_is_wall:
                return False

        if (
            (current_column, current_row)
            != (target_column, target_row)
            and not can_move_to(
                dungeon_map,
                current_column,
                current_row,
            )
        ):
            return False

    return True


def update_enemy_aggro(
    dungeon_map,
    enemy,
    player_column,
    player_row,
):
    if enemy["is_aggro"]:
        return

    distance_to_player = distance_between(
        enemy["column"],
        enemy["row"],
        player_column,
        player_row,
    )

    if (
        distance_to_player <= enemy["aggro_radius"]
        and has_line_of_sight(
            dungeon_map,
            enemy["column"],
            enemy["row"],
            player_column,
            player_row,
        )
    ):
        enemy["is_aggro"] = True


def has_clear_line(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
    blocking_positions,
):
    if start_row == target_row:
        line_positions = [
            (column, start_row)
            for column in range(
                min(start_column, target_column) + 1,
                max(start_column, target_column),
            )
        ]
    elif start_column == target_column:
        line_positions = [
            (start_column, row)
            for row in range(
                min(start_row, target_row) + 1,
                max(start_row, target_row),
            )
        ]
    else:
        return False

    return all(
        position not in blocking_positions
        and can_move_to(dungeon_map, position[0], position[1])
        for position in line_positions
    )


def get_oracle_ray(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
    blocking_positions,
):
    column_direction = target_column - start_column
    row_direction = target_row - start_row

    if column_direction == 0 and row_direction == 0:
        return []

    ray_scale = len(dungeon_map) + len(dungeon_map[0])
    end_column = start_column + column_direction * ray_scale
    end_row = start_row + row_direction * ray_scale
    column = start_column
    row = start_row
    column_distance = abs(end_column - start_column)
    row_distance = abs(end_row - start_row)
    column_step = 1 if start_column < end_column else -1
    row_step = 1 if start_row < end_row else -1
    error = column_distance - row_distance
    ray_positions = []

    while True:
        doubled_error = error * 2

        if doubled_error > -row_distance:
            error -= row_distance
            column += column_step

        if doubled_error < column_distance:
            error += column_distance
            row += row_step

        if not (
            0 <= row < len(dungeon_map)
            and 0 <= column < len(dungeon_map[0])
        ):
            break

        position = (column, row)

        if (
            position in blocking_positions
            or not can_move_to(dungeon_map, column, row)
        ):
            break

        ray_positions.append(position)

    return ray_positions


def get_enemy_attack_targets(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    blocking_positions,
):
    enemy_column = enemy["column"]
    enemy_row = enemy["row"]
    attack_kind = enemy["attack_kind"]
    distance_to_player = distance_between(
        enemy_column,
        enemy_row,
        player_column,
        player_row,
    )

    if attack_kind == "oracle":
        second_phase = enemy["health"] <= enemy["max_health"] // 2
        available_attack_modes = [
            mode
            for mode in ("gaze", "revelation", "shockwave")
            if mode != enemy["last_attack_mode"]
        ]
        attack_mode = random.choice(available_attack_modes)
        enemy["selected_attack_mode"] = attack_mode
        enemy["last_attack_mode"] = attack_mode

        if attack_mode == "gaze":
            return get_oracle_ray(
                dungeon_map,
                enemy_column,
                enemy_row,
                player_column,
                player_row,
                blocking_positions,
            )

        if attack_mode == "revelation":
            ray_directions = [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ]

            if second_phase:
                ray_directions.extend(
                    [
                        (-1, -1),
                        (1, -1),
                        (-1, 1),
                        (1, 1),
                    ]
                )

            revelation_targets = []

            for column_change, row_change in ray_directions:
                revelation_targets.extend(
                    get_oracle_ray(
                        dungeon_map,
                        enemy_column,
                        enemy_row,
                        enemy_column + column_change,
                        enemy_row + row_change,
                        blocking_positions,
                    )
                )

            return revelation_targets

        return [
            (column, row)
            for row in range(len(dungeon_map))
            for column in range(len(dungeon_map[0]))
            if (
                max(
                    abs(column - enemy_column),
                    abs(row - enemy_row),
                )
                == 2
                and (column, row) not in blocking_positions
                and can_move_to(dungeon_map, column, row)
            )
        ]

    if attack_kind == "boss":
        if (
            distance_to_player > enemy["attack_range"]
            or not has_line_of_sight(
                dungeon_map,
                enemy_column,
                enemy_row,
                player_column,
                player_row,
            )
        ):
            return []

        second_phase = enemy["health"] <= enemy["max_health"] // 2
        available_attack_modes = [
            mode
            for mode in ("cross", "sweep", "runes")
            if mode != enemy["last_attack_mode"]
        ]
        attack_mode = random.choice(available_attack_modes)
        enemy["selected_attack_mode"] = attack_mode
        enemy["last_attack_mode"] = attack_mode

        if attack_mode == "cross":
            arm_length = 3 if second_phase else 2
            potential_targets = [
                (player_column, player_row),
                *[
                    (player_column + distance, player_row)
                    for distance in range(-arm_length, arm_length + 1)
                    if abs(distance) >= 2
                ],
                *[
                    (player_column, player_row + distance)
                    for distance in range(-arm_length, arm_length + 1)
                    if abs(distance) >= 2
                ],
            ]
        elif attack_mode == "sweep":
            half_length = 3 if second_phase else 2

            if random.choice((True, False)):
                potential_targets = [
                    (player_column + distance, player_row)
                    for distance in range(-half_length, half_length + 1)
                ]
            else:
                potential_targets = [
                    (player_column, player_row + distance)
                    for distance in range(-half_length, half_length + 1)
                ]
        else:
            neighboring_targets = [
                (player_column - 1, player_row - 1),
                (player_column + 1, player_row - 1),
                (player_column - 1, player_row + 1),
                (player_column + 1, player_row + 1),
            ]
            potential_targets = [
                (player_column, player_row),
                *neighboring_targets,
            ]

            if second_phase:
                potential_targets.extend(
                    [
                        (player_column - 2, player_row),
                        (player_column + 2, player_row),
                        (player_column, player_row - 2),
                        (player_column, player_row + 2),
                    ]
                )

        return [
            position
            for position in potential_targets
            if (
                0 <= position[1] < len(dungeon_map)
                and 0 <= position[0] < len(dungeon_map[0])
                and can_move_to(
                    dungeon_map,
                    position[0],
                    position[1],
                )
            )
        ]

    if attack_kind == "ranged":
        if distance_to_player == 1:
            return [(player_column, player_row)]

        if (
            2 <= distance_to_player <= enemy["attack_range"]
            and has_clear_line(
                dungeon_map,
                enemy_column,
                enemy_row,
                player_column,
                player_row,
                blocking_positions,
            )
        ):
            neighboring_targets = [
                (player_column, player_row - 1),
                (player_column, player_row + 1),
                (player_column - 1, player_row),
                (player_column + 1, player_row),
            ]
            valid_neighboring_targets = [
                position
                for position in neighboring_targets
                if can_move_to(
                    dungeon_map,
                    position[0],
                    position[1],
                )
            ]
            extra_target_count = min(
                2,
                len(valid_neighboring_targets),
            )

            return [
                (player_column, player_row),
                *random.sample(
                    valid_neighboring_targets,
                    extra_target_count,
                ),
            ]

        return []

    if attack_kind == "priest_magic":
        if distance_to_player == 1:
            return [(player_column, player_row)]

        if (
            2 <= distance_to_player <= enemy["attack_range"]
            and has_clear_line(
                dungeon_map,
                enemy_column,
                enemy_row,
                player_column,
                player_row,
                blocking_positions,
            )
        ):
            return [(player_column, player_row)]

        return []

    if distance_to_player != 1:
        return []

    if attack_kind == "cleave":
        if random.choice((True, False)):
            potential_targets = [
                (player_column - 1, player_row),
                (player_column, player_row),
                (player_column + 1, player_row),
            ]
        else:
            potential_targets = [
                (player_column, player_row - 1),
                (player_column, player_row),
                (player_column, player_row + 1),
            ]

        return [
            position
            for position in potential_targets
            if can_move_to(
                dungeon_map,
                position[0],
                position[1],
            )
        ]

    return [(player_column, player_row)]


def get_enemy_attack_mode(enemy, player_column, player_row):
    if enemy["type"] in ("warden", "oracle"):
        return enemy["selected_attack_mode"]

    if (
        enemy["type"] in ("archer", "priest")
        and distance_between(
            enemy["column"],
            enemy["row"],
            player_column,
            player_row,
        )
        == 1
    ):
        return "melee"

    if enemy["type"] == "priest":
        return "magic"

    return enemy["attack_kind"]


def move_enemy_toward_position(
    dungeon_map,
    enemy,
    target_column,
    target_row,
    occupied_positions,
):
    start_position = (enemy["column"], enemy["row"])
    target_position = (target_column, target_row)

    if positions_are_adjacent(
        enemy["column"],
        enemy["row"],
        target_column,
        target_row,
    ):
        return start_position

    positions_to_visit = deque([start_position])
    previous_position = {start_position: None}
    destination = None

    while positions_to_visit:
        current_position = positions_to_visit.popleft()
        current_column, current_row = current_position

        if positions_are_adjacent(
            current_column,
            current_row,
            target_column,
            target_row,
        ):
            destination = current_position
            break

        neighboring_positions = ordered_neighboring_positions(
            current_column,
            current_row,
            target_column,
            target_row,
        )

        for next_position in neighboring_positions:
            if (
                next_position in previous_position
                or next_position == target_position
                or next_position in occupied_positions
            ):
                continue

            next_column, next_row = next_position

            if not can_move_to(
                dungeon_map,
                next_column,
                next_row,
            ):
                continue

            previous_position[next_position] = current_position
            positions_to_visit.append(next_position)

    if destination is None:
        return start_position

    next_step = destination

    while previous_position[next_step] != start_position:
        next_step = previous_position[next_step]

    return next_step


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
    barriers=(),
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

            if not can_move_between(
                dungeon_map,
                current_column,
                current_row,
                next_column,
                next_row,
                barriers,
            ):
                continue

            if not target_is_player and next_position in occupied_positions:
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
    barriers=(),
):
    enemy_column = enemy["column"]
    enemy_row = enemy["row"]

    if random.random() >= enemy["wander_chance"]:
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
            and can_move_between(
                dungeon_map,
                enemy_column,
                enemy_row,
                new_column,
                new_row,
                barriers,
            )
        ):
            return new_column, new_row

    return enemy_column, enemy_row


def move_enemy_away(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
    maximum_steps=1,
    barriers=(),
):
    enemy_column = enemy["column"]
    enemy_row = enemy["row"]
    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
    ]
    valid_moves = []

    for column_change, row_change in directions:
        last_valid_position = None

        for step_count in range(1, maximum_steps + 1):
            position = (
                enemy_column + column_change * step_count,
                enemy_row + row_change * step_count,
            )

            if (
                position == (player_column, player_row)
                or position in occupied_positions
                or not can_move_between(
                    dungeon_map,
                    enemy_column + column_change * (step_count - 1),
                    enemy_row + row_change * (step_count - 1),
                    position[0],
                    position[1],
                    barriers,
                )
            ):
                break

            last_valid_position = position

        if last_valid_position is not None:
            valid_moves.append(last_valid_position)

    if not valid_moves:
        return enemy_column, enemy_row

    greatest_distance = max(
        distance_between(
            position[0],
            position[1],
            player_column,
            player_row,
        )
        for position in valid_moves
    )
    best_moves = [
        position
        for position in valid_moves
        if distance_between(
            position[0],
            position[1],
            player_column,
            player_row,
        )
        == greatest_distance
    ]

    return random.choice(best_moves)
