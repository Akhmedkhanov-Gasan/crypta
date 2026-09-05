import pygame

from acts.navigation import (
    activate_navigation_action,
    navigation_action,
    navigation_cell_is_visible,
    navigation_target_info,
    player_attack_warnings,
)
from application.movement_input import movement_input_is_locked
from logic import get_enemy_occupied_positions
from systems.player_navigation import find_player_path


AUTO_MOVE_INTERVAL_MS = 175


def auto_move_has_new_warning(state, game_state):
    if state.auto_move_target is None:
        return False

    return any(
        not any(
            warning is acknowledged
            for acknowledged in state.auto_move_acknowledged_warnings
        )
        for warning in player_attack_warnings(game_state)
    )


def start_auto_move(state, game_state, target):
    state.reset_held_movement()
    state.cancel_auto_move()

    floor = game_state.floor
    if (
        not navigation_cell_is_visible(game_state, target)
        or target == (floor.player_column, floor.player_row)
    ):
        return

    enemy, interaction = navigation_target_info(game_state, target)
    state.auto_move_target = target
    state.auto_move_enemy = enemy
    state.auto_move_floor_index = game_state.floor_index
    state.auto_move_acknowledged_warnings = (
        player_attack_warnings(game_state)
    )
    state.next_auto_move_at = 0


def _target_cells(state, game_state):
    floor = game_state.floor
    enemy = state.auto_move_enemy

    if enemy is None:
        return (state.auto_move_target,)

    if (
        enemy.health <= 0
        or not any(candidate is enemy for candidate in floor.enemies)
    ):
        return ()

    return tuple(
        position
        for position in get_enemy_occupied_positions(enemy)
        if navigation_cell_is_visible(game_state, position)
    )


def create_auto_move_event(
    state,
    game_state,
    current_time,
    movement_available,
    repeat_interval,
):
    if state.auto_move_target is None:
        return None

    if (
        not movement_available
        or state.held_movement_keys
        or state.auto_move_floor_index != game_state.floor_index
        or auto_move_has_new_warning(state, game_state)
    ):
        state.cancel_auto_move()
        return None

    if (
        movement_input_is_locked(state, current_time)
        or current_time < state.next_auto_move_at
    ):
        return None

    cells = _target_cells(state, game_state)
    if not cells:
        state.cancel_auto_move()
        return None

    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    target = min(
        cells,
        key=lambda position: max(
            abs(position[0] - origin[0]),
            abs(position[1] - origin[1]),
        ),
    )
    enemy, interaction = navigation_target_info(game_state, target)

    def action_from(position, cell):
        return navigation_action(
            game_state,
            position,
            cell,
            enemy is not None,
        )

    def can_finish(position):
        if interaction:
            return any(
                action_from(position, cell) is not None
                for cell in cells
            )
        return position == target

    final_action = can_finish(origin)
    if final_action:
        if not interaction:
            state.cancel_auto_move()
            return None

        action = next(
            result
            for cell in cells
            if (result := action_from(origin, cell)) is not None
        )
    else:
        path = find_player_path(
            floor,
            target,
            can_finish=can_finish,
        )
        if not path:
            state.cancel_auto_move()
            return None

        destination = path[0]
        action = {
            "movement_direction": (
                destination[0] - origin[0],
                destination[1] - origin[1],
            )
        }

    attributes = {
        "key": pygame.K_UNKNOWN,
        "automatic_movement": True,
        "auto_move_revision": state.auto_move_revision,
        "auto_move_origin": origin,
        "auto_move_final_action": final_action,
        **action,
    }
    state.next_auto_move_at = current_time + repeat_interval
    return pygame.event.Event(pygame.KEYDOWN, attributes)


def accept_auto_move_event(state, game_state, event, current_time):
    if (
        event.auto_move_revision != state.auto_move_revision
        or state.auto_move_target is None
    ):
        return False

    floor = game_state.floor
    if (
        state.auto_move_floor_index != game_state.floor_index
        or event.auto_move_origin
        != (floor.player_column, floor.player_row)
        or auto_move_has_new_warning(state, game_state)
    ):
        state.cancel_auto_move()
        return False

    if movement_input_is_locked(state, current_time):
        return False

    if event.auto_move_final_action:
        state.cancel_auto_move()
        return activate_navigation_action(game_state, event)

    return True
