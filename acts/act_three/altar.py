ALTAR_WIDTH = 2
ALTAR_HEIGHT = 2


def get_upgrade_altar_cells(floor):
    if floor.upgrade_altar is None:
        return set()

    altar_column, altar_row = floor.upgrade_altar
    return {
        (column, row)
        for row in range(altar_row, altar_row + ALTAR_HEIGHT)
        for column in range(
            altar_column,
            altar_column + ALTAR_WIDTH,
        )
    }


def player_is_next_to_upgrade_altar(game_state):
    player_position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    return any(
        abs(player_position[0] - column)
        + abs(player_position[1] - row)
        == 1
        for column, row in get_upgrade_altar_cells(
            game_state.floor
        )
    )
