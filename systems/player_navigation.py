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


def find_player_path(floor, target, *, can_finish=None):
    start = (floor.player_column, floor.player_row)
    if can_finish is None:
        can_finish = lambda position: position == target

    if can_finish(start):
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
    positions_to_visit = deque([start])
    previous_position = {start: None}
    destination = None

    while positions_to_visit:
        current = positions_to_visit.popleft()
        if can_finish(current):
            destination = current
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

    if destination is None:
        return []

    path = []
    position = destination
    while position != start:
        path.append(position)
        position = previous_position[position]
    path.reverse()
    return path
