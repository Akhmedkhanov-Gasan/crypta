import heapq
import random
from collections import deque

from settings import MAGE_RESONANCE_RANGE


def get_mage_arcane_burst_cells(
    floor,
    target: tuple[int, int],
    rune_id: str | None = None,
) -> list[tuple[int, int]]:
    if rune_id == "rune_of_concentration":
        return [target]

    fracture_active = rune_id == "rune_of_fracture"
    candidates = (
        [
            (target[0] + dx, target[1] + dy)
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
        ]
        if fracture_active
        else [
            target,
            (target[0], target[1] - 1),
            (target[0] + 1, target[1]),
            (target[0], target[1] + 1),
            (target[0] - 1, target[1]),
        ]
    )

    enemy_cells = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    target_is_pillar = any(
        enemy.type == "oracle_pillar"
        and enemy.health > 0
        and (enemy.column, enemy.row) == target
        for enemy in floor.enemies
    )

    return [
        position
        for position in candidates
        if (
            can_move_to(floor.map, *position)
            or (fracture_active and position in enemy_cells)
            or (position == target and target_is_pillar)
        )
    ]


def get_mage_resonance_cells(game_state) -> set[tuple[int, int]]:
    player = game_state.player
    if (
        player.player_class != "mage"
        or player.selected_rune_id != "rune_of_resonance"
    ):
        return set()

    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    enemy_cells = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }

    return {
        position
        for position in floor.visible_cells
        if (
            0 < distance_between(*origin, *position) <= MAGE_RESONANCE_RANGE
            and (
                position[0] == origin[0]
                or position[1] == origin[1]
            )
            and (
                can_move_to(floor.map, *position)
                or position in enemy_cells
            )
            and has_line_of_sight(
                floor.map,
                *origin,
                *position,
                barriers=floor.barriers,
            )
        )
    }


def get_mage_resonance_target(game_state, target):
    if target is None or target not in get_mage_resonance_cells(game_state):
        return None

    return next(
        (
            enemy
            for enemy in game_state.floor.enemies
            if enemy.health > 0
            and target in get_enemy_occupied_positions(enemy)
        ),
        None,
    )


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
    return dungeon_map[row][column] not in (
        "#",
        "B",
        "C",
        "S",
        "G",
        "H",
        "P",
        "T",
        "M",
        "A",
    )


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


def can_player_move_between(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
    barriers=(),
):
    column_change = target_column - start_column
    row_change = target_row - start_row
    if (
        max(abs(column_change), abs(row_change)) != 1
        or not can_move_to(dungeon_map, target_column, target_row)
    ):
        return False
    if column_change == 0 or row_change == 0:
        return can_move_between(
            dungeon_map,
            start_column,
            start_row,
            target_column,
            target_row,
            barriers,
        )

    horizontal_cell = (target_column, start_row)
    vertical_cell = (start_column, target_row)
    return (
        can_move_between(
            dungeon_map,
            start_column,
            start_row,
            *horizontal_cell,
            barriers,
        )
        and can_move_between(
            dungeon_map,
            *horizontal_cell,
            target_column,
            target_row,
            barriers,
        )
        and can_move_between(
            dungeon_map,
            start_column,
            start_row,
            *vertical_cell,
            barriers,
        )
        and can_move_between(
            dungeon_map,
            *vertical_cell,
            target_column,
            target_row,
            barriers,
        )
    )


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
    width = max(1, enemy.get("footprint_width", 1))
    height = max(1, enemy.get("footprint_height", 1))
    left = enemy["column"] - (width - 1) // 2
    top = enemy["row"] - (height - 1) // 2

    return {
        (column, row)
        for row in range(top, top + height)
        for column in range(left, left + width)
    }


def positions_are_adjacent(first_column, first_row, second_column, second_row):
    return max(
        abs(first_column - second_column),
        abs(first_row - second_row),
    ) == 1


def has_line_of_sight(
    dungeon_map,
    start_column,
    start_row,
    target_column,
    target_row,
    barriers=(),
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

        previous_position = (previous_column, previous_row)
        current_position = (current_column, current_row)
        crossed_edges = (
            (
                (previous_position, (current_column, previous_row)),
                ((current_column, previous_row), current_position),
                (previous_position, (previous_column, current_row)),
                ((previous_column, current_row), current_position),
            )
            if moved_diagonally
            else ((previous_position, current_position),)
        )
        if any(
            tuple(sorted(edge)) in barriers
            for edge in crossed_edges
        ):
            return False

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
    player_is_adjacent = positions_are_adjacent(
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
        if player_is_adjacent:
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
        if player_is_adjacent:
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

    if attack_kind == "cleave":
        player_is_in_straight_line = (
                enemy_column == player_column
                or enemy_row == player_row
        )
        player_is_in_cleave_range = (
                player_is_adjacent
                or (
                        player_is_in_straight_line
                        and distance_to_player <= enemy["attack_range"]
                )
        )

        if not player_is_in_cleave_range:
            return []

        raw_column_change = player_column - enemy_column
        raw_row_change = player_row - enemy_row
        column_change = (
            0
            if raw_column_change == 0
            else 1 if raw_column_change > 0 else -1
        )
        row_change = (
            0
            if raw_row_change == 0
            else 1 if raw_row_change > 0 else -1
        )

        return get_directional_line(
            dungeon_map,
            enemy_column,
            enemy_row,
            column_change,
            row_change,
            3,
            blocking_positions,
        )

    if not player_is_adjacent:
        return []

    return [(player_column, player_row)]


def get_enemy_attack_mode(enemy, player_column, player_row):
    if enemy["type"] in ("warden", "oracle"):
        return enemy["selected_attack_mode"]

    if (
        enemy["type"] in ("archer", "priest", "priest_ghost")
        and distance_between(
            enemy["column"],
            enemy["row"],
            player_column,
            player_row,
        )
        == 1
    ):
        return "melee"

    if enemy["type"] in ("priest", "priest_ghost"):
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
    hazard_costs=None,
):
    if hazard_costs is None:
        hazard_costs = {}
    start_position = (enemy["column"], enemy["row"])
    player_position = (player_column, player_row)

    if positions_are_adjacent(
        enemy["column"],
        enemy["row"],
        player_column,
        player_row,
    ):
        return start_position
    positions_to_visit = [(0, start_position)]
    path_costs = {start_position: 0}
    previous_position = {start_position: None}

    while positions_to_visit:
        current_cost, current_position = heapq.heappop(
            positions_to_visit
        )
        current_column, current_row = current_position

        if current_cost != path_costs[current_position]:
            continue

        if current_position == player_position:
            break

        neighboring_positions = ordered_neighboring_positions(
            current_column,
            current_row,
            player_column,
            player_row,
        )

        for next_position in neighboring_positions:
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

            if (
                not target_is_player
                and next_position in occupied_positions
            ):
                continue

            step_cost = 1 + hazard_costs.get(next_position, 0)
            next_cost = current_cost + step_cost

            if next_cost >= path_costs.get(
                next_position,
                float("inf"),
            ):
                continue

            path_costs[next_position] = next_cost
            previous_position[next_position] = current_position
            heapq.heappush(
                positions_to_visit,
                (next_cost, next_position),
            )

    if player_position not in previous_position:
        return start_position

    next_step = player_position

    while previous_position[next_step] != start_position:
        next_step = previous_position[next_step]

    return next_step

def move_enemy_toward_cell(
    dungeon_map,
    enemy,
    target_column,
    target_row,
    occupied_positions,
    barriers=(),
    hazard_costs=None,
):
    if hazard_costs is None:
        hazard_costs = {}

    start_position = (
        enemy["column"],
        enemy["row"],
    )
    target_position = (
        target_column,
        target_row,
    )

    if start_position == target_position:
        return start_position

    positions_to_visit = [(0, start_position)]
    path_costs = {start_position: 0}
    previous_position = {start_position: None}

    while positions_to_visit:
        current_cost, current_position = heapq.heappop(
            positions_to_visit
        )

        if current_cost != path_costs[current_position]:
            continue

        if current_position == target_position:
            break

        current_column, current_row = current_position
        neighboring_positions = ordered_neighboring_positions(
            current_column,
            current_row,
            target_column,
            target_row,
        )

        for next_position in neighboring_positions:
            if (
                next_position != target_position
                and next_position in occupied_positions
            ):
                continue

            if not can_move_between(
                dungeon_map,
                current_column,
                current_row,
                next_position[0],
                next_position[1],
                barriers,
            ):
                continue

            next_cost = (
                current_cost
                + 1
                + hazard_costs.get(next_position, 0)
            )

            if next_cost >= path_costs.get(
                next_position,
                float("inf"),
            ):
                continue

            path_costs[next_position] = next_cost
            previous_position[next_position] = current_position
            heapq.heappush(
                positions_to_visit,
                (next_cost, next_position),
            )

    if target_position not in previous_position:
        return start_position

    next_step = target_position

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
    hazard_costs=None,
):
    if hazard_costs is None:
        hazard_costs = {}

    enemy_position = (
        enemy["column"],
        enemy["row"],
    )
    enemy_column, enemy_row = enemy_position
    current_danger = hazard_costs.get(enemy_position, 0)
    must_escape = current_danger > 0

    if (
        not must_escape
        and random.random() >= enemy["wander_chance"]
    ):
        return enemy_position

    possible_moves = [
        (enemy_column, enemy_row - 1),
        (enemy_column, enemy_row + 1),
        (enemy_column - 1, enemy_row),
        (enemy_column + 1, enemy_row),
    ]

    valid_moves = [
        position
        for position in possible_moves
        if (
            position != (player_column, player_row)
            and position not in occupied_positions
            and can_move_between(
                dungeon_map,
                enemy_column,
                enemy_row,
                position[0],
                position[1],
                barriers,
            )
        )
    ]

    if not valid_moves:
        return enemy_position

    safe_moves = [
        position
        for position in valid_moves
        if hazard_costs.get(position, 0) == 0
    ]

    if safe_moves:
        return random.choice(safe_moves)

    if not must_escape:
        return enemy_position

    lowest_danger = min(
        hazard_costs.get(position, 0)
        for position in valid_moves
    )
    least_dangerous_moves = [
        position
        for position in valid_moves
        if hazard_costs.get(position, 0) == lowest_danger
    ]

    return random.choice(least_dangerous_moves)


def move_enemy_away(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
    maximum_steps=1,
    barriers=(),
    hazard_costs=None,
):
    if hazard_costs is None:
        hazard_costs = {}
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

            movement_bounds = enemy.get("movement_bounds")
            if movement_bounds is not None:
                left, top, right, bottom = movement_bounds
                if not (
                    left <= position[0] <= right
                    and top <= position[1] <= bottom
                ):
                    break

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

    def move_priority(
        position: tuple[int, int],
    ) -> tuple[int, int]:
        danger = hazard_costs.get(position, 0)
        player_distance = distance_between(
            position[0],
            position[1],
            player_column,
            player_row,
        )

        return danger, -player_distance

    best_priority = min(
        move_priority(position)
        for position in valid_moves
    )
    best_moves = [
        position
        for position in valid_moves
        if move_priority(position) == best_priority
    ]

    return random.choice(best_moves)
