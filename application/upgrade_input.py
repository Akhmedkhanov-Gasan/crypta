from acts.act_one.upgrades import (
    handle_act_one_upgrade_input,
    handle_act_one_upgrade_pointer,
)


def handle_upgrade_key_input(
    game_state,
    key: int,
    current_time: int,
) -> bool:
    if not game_state.upgrade_screen_open:
        return False

    return handle_act_one_upgrade_input(
        game_state,
        key,
        current_time,
    )


def handle_upgrade_pointer_input(
    game_state,
    position: tuple[int, int],
    current_time: int,
) -> bool:
    if not game_state.upgrade_screen_open:
        return False

    return handle_act_one_upgrade_pointer(
        game_state,
        position,
        current_time,
    )
