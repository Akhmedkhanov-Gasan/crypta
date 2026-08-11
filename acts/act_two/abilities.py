from acts.act_two.settings import ABILITY_HITS_REQUIRED


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


def select_warrior_cleave_direction(
    game_state,
    column_change: int,
    row_change: int,
) -> bool:
    direction = (column_change, row_change)
    if direction not in CARDINAL_DIRECTIONS:
        return False

    player = game_state.player
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


def clear_act_two_ability_selection(game_state) -> None:
    game_state.player.act_two.selected_ability_direction = None
    game_state.player_attack_targets = []
