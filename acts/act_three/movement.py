from application.movement_input import (
    create_held_movement_event,
    movement_input_is_locked,
)
from acts.act_three.movement_timing import PLAYER_STEP_MS


def create_act_three_held_movement_event(
    state,
    current_time,
    movement_available,
    combat_active,
):
    if movement_input_is_locked(state, current_time):
        state.reset_held_movement()
        return None

    event = create_held_movement_event(
        state,
        current_time,
        movement_available,
        combat_active,
    )

    if event is not None and state.next_held_move_at > 0:
        state.next_held_move_at = current_time + PLAYER_STEP_MS

    return event
