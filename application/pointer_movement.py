import pygame

from acts.act_three.presentation.hit_testing import get_act_three_cell_from_position
from acts.navigation import navigation_target_info, navigation_cell_is_visible
from application.movement_input import movement_input_is_locked
from presentation.display import window_to_game_position


def begin_pointer_movement(state, game_state, target, camera=None):
    if navigation_cell_is_visible(game_state, target) and not navigation_target_info(game_state, target)[1]:
        state.pointer_move_started_at = pygame.time.get_ticks()
        state.pointer_move_floor = game_state.floor
        state.pointer_move_camera = camera
        state.pointer_move_repeating = False
        state.next_pointer_move_at = state.pointer_move_started_at + 180


def create_pointer_movement_event(state, game_state, current_time, available, repeat_interval=160):
    if state.pointer_move_started_at is None:
        return None
    if (
        not available
        or state.pointer_move_floor is not game_state.floor
        or state.held_movement_keys
        or not pygame.mouse.get_focused()
        or not pygame.mouse.get_pressed()[0]
    ):
        if state.pointer_move_repeating:
            state.cancel_auto_move()
        state.pointer_move_started_at = None
        state.pointer_move_floor = None
        state.pointer_move_repeating = False
        state.pointer_move_camera = None
        return None
    if current_time - state.pointer_move_started_at < 180:
        return None
    state.pointer_move_repeating = True
    state.cancel_auto_move()
    if movement_input_is_locked(state, current_time) or current_time < max(state.next_step_at, state.next_pointer_move_at):
        return None
    screen = pygame.display.get_surface()
    if screen is None:
        return None
    position = window_to_game_position(screen, pygame.mouse.get_pos())
    act = game_state.floor.presentation_act
    target = None
    if position is not None:
        if act == 1:
            from acts.act_one.camera import get_act_one_cell_from_position
            from acts.act_one.interface import act_one_hud_contains_position

            if not act_one_hud_contains_position(position):
                target = get_act_one_cell_from_position(state.pointer_move_camera, position)
        elif act == 2:
            from acts.act_two.presentation.camera import act_two_screen_to_cell

            target = act_two_screen_to_cell(position, state.pointer_move_camera)
        else:
            target = get_act_three_cell_from_position(game_state, position)
    if not navigation_cell_is_visible(game_state, target):
        return None
    floor = game_state.floor
    dx = target[0] - floor.player_column
    dy = target[1] - floor.player_row
    direction = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
    if direction == (0, 0):
        return None
    adjacent = floor.player_column + direction[0], floor.player_row + direction[1]
    if navigation_target_info(game_state, adjacent)[1]:
        return None
    from acts.act_three.npcs import get_npc_at

    if act == 3 and get_npc_at(floor, adjacent) is not None:
        return None
    state.next_pointer_move_at = current_time + repeat_interval
    return pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_UNKNOWN,
        movement_direction=direction, automatic_movement=True,
        movement_revision=state.movement_revision,
        requires_pointer_movement=True,
    )
