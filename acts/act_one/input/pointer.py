import pygame

from acts.act_one.camera import get_act_one_cell_from_position
from acts.act_one.interface import act_one_hud_contains_position
from application.auto_movement import start_auto_move
from presentation.display import window_to_game_position


def handle_act_one_pointer_input(
    event,
    screen,
    camera,
    movement_state,
    game_state,
    enabled,
):
    if (
        event.type != pygame.MOUSEBUTTONDOWN
        or event.button != 1
        or game_state.floor.presentation_act != 1
        or not enabled
    ):
        return False

    game_position = window_to_game_position(
        screen,
        event.pos,
    )

    if not act_one_hud_contains_position(game_position):
        start_auto_move(
            movement_state,
            game_state,
            get_act_one_cell_from_position(
                camera,
                game_position,
            ),
        )

    return True
