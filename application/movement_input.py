import pygame

from application.directional_input import (
    IMMEDIATE_MOVEMENT_KEYS,
    movement_direction_for_keys,
)
from application.movement_state import MovementInputState


DIAGONAL_CHORD_WINDOW_MS = 50
HOLD_START_DELAY_MS = 240
SAFE_REPEAT_INTERVAL_MS = 160
COMBAT_REPEAT_INTERVAL_MS = 160


def _clear_pending_movement(
    state: MovementInputState,
) -> None:
    state.pending_movement_direction = None
    state.pending_movement_at = 0


def _create_movement_event(direction):
    return pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_UNKNOWN,
        movement_direction=direction,
        automatic_movement=True,
    )


def begin_held_movement(
    state: MovementInputState,
    key: int,
    started_at: int,
) -> tuple[int, int] | None:
    key_was_already_held = key in state.held_movement_keys
    state.held_movement_keys.add(key)

    direction = movement_direction_for_keys(
        state.held_movement_keys
    )

    if key_was_already_held:
        return None

    if key in IMMEDIATE_MOVEMENT_KEYS:
        _clear_pending_movement(state)
        state.held_direction = direction
        state.next_held_move_at = (
            started_at + HOLD_START_DELAY_MS
        )
        return direction

    if direction == (0, 0):
        _clear_pending_movement(state)
        state.held_direction = direction
        state.next_held_move_at = 0
        return None

    direction_is_diagonal = (
        direction[0] != 0
        and direction[1] != 0
    )

    if direction_is_diagonal:
        _clear_pending_movement(state)
        state.held_direction = direction
        state.next_held_move_at = (
            started_at + HOLD_START_DELAY_MS
        )
        return direction

    state.held_direction = direction
    state.pending_movement_direction = direction
    state.pending_movement_at = (
        started_at + DIAGONAL_CHORD_WINDOW_MS
    )
    state.next_held_move_at = 0

    return None


def release_held_movement(
    state: MovementInputState,
    key: int,
) -> None:
    state.held_movement_keys.discard(key)

    if not state.held_movement_keys:
        state.held_direction = (0, 0)
        state.next_held_move_at = 0


def create_held_movement_event(
    state: MovementInputState,
    current_time: int,
    movement_available: bool,
    combat_active: bool,
):
    if not movement_available:
        state.held_direction = (0, 0)
        _clear_pending_movement(state)
        return None

    if state.pending_movement_direction is not None:
        if current_time < state.pending_movement_at:
            return None

        pending_direction = state.pending_movement_direction
        _clear_pending_movement(state)

        held_direction = movement_direction_for_keys(
            state.held_movement_keys
        )
        state.held_direction = held_direction

        if held_direction == pending_direction:
            state.next_held_move_at = (
                current_time + HOLD_START_DELAY_MS
            )
        else:
            state.next_held_move_at = 0

        state.cancel_auto_move()
        return _create_movement_event(pending_direction)

    direction = movement_direction_for_keys(
        state.held_movement_keys
    )

    if direction == (0, 0):
        state.held_direction = (0, 0)
        return None

    state.cancel_auto_move()

    if direction != state.held_direction:
        state.held_direction = direction
        state.next_held_move_at = (
            current_time + HOLD_START_DELAY_MS
        )
        return None

    if current_time < state.next_held_move_at:
        return None

    repeat_interval = (
        COMBAT_REPEAT_INTERVAL_MS
        if combat_active
        else SAFE_REPEAT_INTERVAL_MS
    )

    state.next_held_move_at = (
        current_time + repeat_interval
    )

    return _create_movement_event(direction)


def movement_input_is_locked(
    state: MovementInputState,
    current_time: int,
) -> bool:
    return current_time < state.movement_input_locked_until