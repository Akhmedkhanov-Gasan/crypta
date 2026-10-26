import pygame

from acts.act_one.dev_commands import (
    prepare_act_one_awakening_debug_state,
)
from game.factories import create_game_state


DEBUG_FLOOR_KEYS = (
    pygame.K_F1,
    pygame.K_F2,
    pygame.K_F3,
    pygame.K_F4,
)


def create_debug_game_state(
    event,
    current_time,
    first_act_final_floor,
    first_act_three_floor,
    class_selection_ready_ms,
):
    debug_target = getattr(
        event,
        "debug_target",
        None,
    )
    if debug_target is not None:
        if debug_target != "act_one_awakening":
            return None

        game_state = create_game_state(
            floor_index=first_act_final_floor,
            opening_message=(
                "Debug: post-Warden awakening scene."
            ),
        )
        prepare_act_one_awakening_debug_state(
            game_state,
            current_time,
        )
        return game_state

    if (
        event.type != pygame.KEYDOWN
        or event.key not in DEBUG_FLOOR_KEYS
    ):
        return None

    if event.key == pygame.K_F1:
        return create_game_state(
            floor_index=first_act_final_floor,
            opening_message=(
                "Debug: Act I final room."
            ),
        )

    if event.key == pygame.K_F2:
        game_state = create_game_state(
            floor_index=first_act_final_floor,
            opening_message=(
                "Debug jump: choose an Act II class."
            ),
        )
        game_state.class_selection_open = True
        game_state.class_transition_started_at = (
            current_time
            - class_selection_ready_ms
        )
        return game_state

    if event.key == pygame.K_F3:
        game_state = create_game_state(
            floor_index=first_act_final_floor,
            opening_message=(
                "Debug: choose an Act II class "
                "to test the Oracle arena."
            ),
        )
        game_state.oracle_debug_mode = True
        game_state.class_selection_open = True
        game_state.class_transition_started_at = (
            current_time
            - class_selection_ready_ms
        )
        return game_state

    game_state = create_game_state(
        floor_index=first_act_three_floor,
        opening_message=(
            "Debug: Act III environment v3."
        ),
    )
    game_state.act_three_test_mode = True
    game_state.act_three_debug_class_selection_open = True

    return game_state


__all__ = [
    "DEBUG_FLOOR_KEYS",
    "create_debug_game_state",
]
