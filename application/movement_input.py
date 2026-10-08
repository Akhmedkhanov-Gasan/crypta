from dataclasses import dataclass

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


@dataclass(frozen=True)
class MovementInputProfile:
    start_delay_ms: int = HOLD_START_DELAY_MS
    repeat_interval_ms: int | None = None
    step_duration_ms: int = 0


DEFAULT_MOVEMENT_PROFILE = MovementInputProfile()


def _clear_pending_movement(state):
    state.pending_movement_direction = None
    state.pending_movement_at = 0


def _create_movement_event(direction, state, profile):
    attributes = {
        "key": pygame.K_UNKNOWN,
        "movement_direction": direction,
        "automatic_movement": True,
    }

    if profile.step_duration_ms > 0:
        attributes["movement_revision"] = state.movement_revision

    return pygame.event.Event(
        pygame.KEYDOWN,
        attributes,
    )


def sync_movement_scope(state, player, floor, profile):
    scope = (
        (id(player), id(floor))
        if profile.step_duration_ms > 0
        else None
    )

    if state.movement_scope == scope:
        return

    state.reset_held_movement()
    state.reset_auto_move()
    state.next_step_at = 0
    state.movement_scope = scope


def movement_event_is_current(state, event):
    revision = getattr(event, "movement_revision", None)
    return revision is None or revision == state.movement_revision


def begin_held_movement(
    state: MovementInputState,
    key: int,
    started_at: int,
    *,
    profile=DEFAULT_MOVEMENT_PROFILE,
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
            started_at + profile.start_delay_ms
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
            started_at + profile.start_delay_ms
        )
        return direction

    state.held_direction = direction
    state.pending_movement_direction = direction
    state.pending_movement_at = (
        started_at + DIAGONAL_CHORD_WINDOW_MS
    )

    if profile.step_duration_ms > 0:
        state.pending_movement_at = max(
            state.pending_movement_at,
            state.next_step_at,
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
    *,
    profile=DEFAULT_MOVEMENT_PROFILE,
):
    if not movement_available:
        if profile.step_duration_ms > 0:
            state.reset_held_movement()
        else:
            state.held_direction = (0, 0)
            _clear_pending_movement(state)
        return None

    if profile.step_duration_ms > 0:
        if movement_input_is_locked(state, current_time):
            state.reset_held_movement()
            return None

        if current_time < state.next_step_at:
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
                current_time + profile.start_delay_ms
            )
        else:
            state.next_held_move_at = 0

        state.cancel_auto_move()
        return _create_movement_event(
            pending_direction,
            state,
            profile,
        )

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
            current_time + profile.start_delay_ms
        )
        return None

    if current_time < state.next_held_move_at:
        return None

    repeat_interval = profile.repeat_interval_ms

    if repeat_interval is None:
        repeat_interval = (
            COMBAT_REPEAT_INTERVAL_MS
            if combat_active
            else SAFE_REPEAT_INTERVAL_MS
        )

    state.next_held_move_at = current_time + repeat_interval

    return _create_movement_event(
        direction,
        state,
        profile,
    )


def accept_movement_direction(
    state,
    direction,
    current_time,
    *,
    profile=DEFAULT_MOVEMENT_PROFILE,
    auto_path=False,
):
    if profile.step_duration_ms <= 0:
        return True

    if movement_input_is_locked(state, current_time):
        state.reset_held_movement()
        return False

    if direction == (0, 0):
        return False

    if current_time < state.next_step_at:
        if auto_path:
            state.next_auto_move_at = state.next_step_at
        else:
            state.pending_movement_direction = direction
            state.pending_movement_at = state.next_step_at
        return False

    _clear_pending_movement(state)
    return True


def mark_movement_step(
    state,
    started_at,
    *,
    profile=DEFAULT_MOVEMENT_PROFILE,
):
    if profile.step_duration_ms <= 0:
        return

    state.next_step_at = started_at + profile.step_duration_ms
    state.next_held_move_at = max(
        state.next_held_move_at,
        state.next_step_at,
    )
    state.next_auto_move_at = max(
        state.next_auto_move_at,
        state.next_step_at,
    )


def movement_input_is_locked(
    state: MovementInputState,
    current_time: int,
) -> bool:
    return current_time < state.movement_input_locked_until
