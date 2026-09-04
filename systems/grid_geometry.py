from collections.abc import Collection

from logic import can_move_to


GridPosition = tuple[int, int]
GridDirection = tuple[int, int]
GridEdge = tuple[GridPosition, GridPosition]


def direction_between_adjacent_cells(
    origin: GridPosition,
    target: GridPosition,
) -> GridDirection | None:
    column_change = target[0] - origin[0]
    row_change = target[1] - origin[1]

    if (
        column_change == 0
        and row_change == 0
    ):
        return None

    if max(
        abs(column_change),
        abs(row_change),
    ) != 1:
        return None

    return column_change, row_change


def _edge_between(
    first: GridPosition,
    second: GridPosition,
) -> GridEdge:
    return tuple(sorted((first, second)))


def can_reach_adjacent_cell(
    dungeon_map,
    origin: GridPosition,
    target: GridPosition,
    barriers: Collection[GridEdge] = (),
    target_must_be_walkable: bool = True,
) -> bool:
    direction = direction_between_adjacent_cells(
        origin,
        target,
    )

    if direction is None:
        return False

    if (
        target_must_be_walkable
        and not can_move_to(
            dungeon_map,
            target[0],
            target[1],
        )
    ):
        return False

    column_change, row_change = direction

    if column_change == 0 or row_change == 0:
        return _edge_between(origin, target) not in barriers

    horizontal_cell = (
        target[0],
        origin[1],
    )
    vertical_cell = (
        origin[0],
        target[1],
    )

    if (
        not can_move_to(
            dungeon_map,
            horizontal_cell[0],
            horizontal_cell[1],
        )
        or not can_move_to(
            dungeon_map,
            vertical_cell[0],
            vertical_cell[1],
        )
    ):
        return False

    crossed_edges = (
        _edge_between(origin, horizontal_cell),
        _edge_between(horizontal_cell, target),
        _edge_between(origin, vertical_cell),
        _edge_between(vertical_cell, target),
    )

    return all(
        edge not in barriers
        for edge in crossed_edges
    )
