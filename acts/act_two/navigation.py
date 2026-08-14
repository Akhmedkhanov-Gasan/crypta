from collections import deque

from logic import can_player_move_between, get_enemy_occupied_positions


_DIRECTIONS = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)


def _direction_priority(current, target, direction):
    column_distance = target[0] - current[0]
    row_distance = target[1] - current[1]
    preferred_direction = (
        0 if column_distance == 0 else (1 if column_distance > 0 else -1),
        0 if row_distance == 0 else (1 if row_distance > 0 else -1),
    )
    next_position = (
        current[0] + direction[0],
        current[1] + direction[1],
    )
    remaining_distance = max(
        abs(target[0] - next_position[0]),
        abs(target[1] - next_position[1]),
    )
    return remaining_distance, direction != preferred_direction


def find_act_two_path(floor, target):
    start = (floor.player_column, floor.player_row)
    if target == start:
        return []

    blocked_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    blocked_positions.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )
    blocked_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    if target in blocked_positions:
        return []

    positions_to_visit = deque([start])
    previous_position = {start: None}

    while positions_to_visit:
        current = positions_to_visit.popleft()
        if current == target:
            break
        directions = sorted(
            _DIRECTIONS,
            key=lambda direction: _direction_priority(
                current,
                target,
                direction,
            ),
        )
        for column_change, row_change in directions:
            next_position = (
                current[0] + column_change,
                current[1] + row_change,
            )
            if (
                next_position in previous_position
                or next_position in blocked_positions
                or not can_player_move_between(
                    floor.map,
                    *current,
                    *next_position,
                    floor.barriers,
                )
            ):
                continue
            previous_position[next_position] = current
            positions_to_visit.append(next_position)

    if target not in previous_position:
        return []

    path = []
    position = target
    while position != start:
        path.append(position)
        position = previous_position[position]
    path.reverse()
    return path
