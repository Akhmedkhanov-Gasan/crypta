from acts.act_one.upgrades import (
    handle_act_one_upgrade_input,
    handle_act_one_upgrade_pointer,
)
from acts.act_three.upgrade_input import (
    handle_act_three_upgrade_input,
    handle_act_three_upgrade_pointer,
)
from acts.act_two.upgrade_input import (
    handle_act_two_upgrade_input,
    handle_act_two_upgrade_pointer,
)
from levels import FLOOR_CONFIGS


def _current_upgrade_act(
    game_state,
) -> int:
    return FLOOR_CONFIGS[
        game_state.floor_index
    ]["act"]


def handle_upgrade_key_input(
    game_state,
    key: int,
    current_time: int,
) -> bool:
    if not game_state.upgrade_screen_open:
        return False

    current_act = _current_upgrade_act(
        game_state
    )

    handlers = {
        1: handle_act_one_upgrade_input,
        2: handle_act_two_upgrade_input,
        3: handle_act_three_upgrade_input,
    }
    handler = handlers.get(current_act)

    if handler is not None:
        handler(
            game_state,
            key,
            current_time,
        )

    return True


def handle_upgrade_pointer_input(
    game_state,
    position: tuple[int, int],
    current_time: int,
) -> bool:
    if not game_state.upgrade_screen_open:
        return False

    current_act = _current_upgrade_act(
        game_state
    )

    if current_act == 1:
        handle_act_one_upgrade_pointer(
            game_state,
            position,
            current_time,
        )
    elif current_act == 2:
        handle_act_two_upgrade_pointer(
            game_state,
            position,
        )
    elif current_act == 3:
        handle_act_three_upgrade_pointer(
            game_state,
            position,
        )

    return True
