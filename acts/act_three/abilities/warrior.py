from acts.act_two.abilities import (
    clear_act_two_ability_selection,
    select_directional_ability_direction,
)


def warrior_cleave_direction_to_target(
    game_state,
    target: tuple[int, int] | None,
) -> tuple[int, int] | None:
    if target is None:
        return None

    floor = game_state.floor
    column_difference = (
        target[0] - floor.player_column
    )
    row_difference = (
        target[1] - floor.player_row
    )

    if column_difference == 0 and row_difference == 0:
        return None

    if abs(column_difference) >= abs(row_difference):
        return (
            1 if column_difference > 0 else -1,
            0,
        )

    return (
        0,
        1 if row_difference > 0 else -1,
    )


def update_warrior_cleave_preview(
    game_state,
    target: tuple[int, int] | None,
) -> tuple[int, int] | None:
    direction = warrior_cleave_direction_to_target(
        game_state,
        target,
    )

    if direction is None:
        clear_act_two_ability_selection(game_state)
        return None

    select_directional_ability_direction(
        game_state,
        direction[0],
        direction[1],
    )
    return direction
