from acts.act_two.settings import (
    ABILITY_HITS_REQUIRED,
    MAGE_ARCANE_BURST_RANGE,
)
from logic import can_move_to, distance_between, get_directional_line


CARDINAL_DIRECTIONS = {
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
}


def ability_charge_required(player) -> int:
    if player.player_class is not None and player.subclass is None:
        return ABILITY_HITS_REQUIRED
    return 2


def get_warrior_cleave_cells(
    floor,
    column_change: int,
    row_change: int,
) -> list[tuple[int, int]]:
    direction = (column_change, row_change)
    if direction not in CARDINAL_DIRECTIONS:
        return []

    perpendicular = (-row_change, column_change)
    cells = []
    # Center first keeps the existing attack sprite facing forward.
    for lateral_offset in (0, -1, 1):
        column = (
            floor.player_column
            + column_change
            + perpendicular[0] * lateral_offset
        )
        row = (
            floor.player_row
            + row_change
            + perpendicular[1] * lateral_offset
        )
        if (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[row])
            and floor.map[row][column] not in ("#", "P")
        ):
            cells.append((column, row))
    return cells


def get_warrior_aftershock_cells(
    floor,
    column_change: int,
    row_change: int,
) -> list[tuple[int, int]]:
    aftershock_cells = []
    for column, row in get_warrior_cleave_cells(
        floor,
        column_change,
        row_change,
    ):
        destination = (
            column + column_change,
            row + row_change,
        )
        if can_move_to(floor.map, *destination):
            aftershock_cells.append(destination)
    return aftershock_cells


def get_mage_arcane_cells(
    floor,
    column_change: int,
    row_change: int,
) -> list[tuple[int, int]]:
    direction = (column_change, row_change)
    if direction not in CARDINAL_DIRECTIONS:
        return []

    blocking_positions = {
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    }
    blocking_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    return get_directional_line(
        floor.map,
        floor.player_column,
        floor.player_row,
        column_change,
        row_change,
        MAGE_ARCANE_BURST_RANGE,
        blocking_positions,
    )


def get_mage_arcane_burst_cells(
    floor,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    candidates = (
        target,
        (target[0], target[1] - 1),
        (target[0] + 1, target[1]),
        (target[0], target[1] + 1),
        (target[0] - 1, target[1]),
    )
    return [
        position
        for position in candidates
        if can_move_to(floor.map, position[0], position[1])
    ]


def is_valid_mage_arcane_burst_target(
    game_state,
    target: tuple[int, int] | None,
) -> bool:
    if target is None:
        return False
    floor = game_state.floor
    return (
        target in floor.visible_cells
        and can_move_to(floor.map, target[0], target[1])
        and distance_between(
            floor.player_column,
            floor.player_row,
            target[0],
            target[1],
        )
        <= MAGE_ARCANE_BURST_RANGE
    )


def select_directional_ability_direction(
    game_state,
    column_change: int,
    row_change: int,
) -> bool:
    direction = (column_change, row_change)
    if direction not in CARDINAL_DIRECTIONS:
        return False

    player = game_state.player
    if player.player_class != "warrior":
        return False
    if player.act_two.selected_ability_direction == direction:
        return True

    player.act_two.selected_ability_direction = direction
    player.act_two_facing_direction = direction
    game_state.player_attack_targets = get_warrior_cleave_cells(
        game_state.floor,
        column_change,
        row_change,
    )
    return False


def select_warrior_cleave_direction(
    game_state,
    column_change: int,
    row_change: int,
) -> bool:
    return select_directional_ability_direction(
        game_state,
        column_change,
        row_change,
    )


def clear_act_two_ability_selection(game_state) -> None:
    game_state.player.act_two.selected_ability_direction = None
    game_state.player_attack_targets = []
