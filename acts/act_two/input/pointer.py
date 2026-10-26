import pygame

from game.state import GameState

from acts.act_two.abilities import is_valid_mage_arcane_burst_target
from acts.act_two.consumables import (
    cancel_fire_bomb_aiming,
    cancel_scroll_aiming,
    enemy_at_scroll_target,
    is_valid_fire_bomb_target,
)
from acts.act_two.presentation.camera import act_two_screen_to_cell
from application.auto_movement import start_auto_move
from application.movement_input import movement_input_is_locked
from logic import get_enemy_occupied_positions, get_mage_resonance_target
from systems.grid_geometry import direction_between_adjacent_cells
from systems.player_abilities import cancel_ability_aiming


def _post_target_event(**attributes):
    pygame.event.post(
        pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_UNKNOWN,
            **attributes,
        )
    )


def handle_act_two_pointer_event(
    event,
    game_state: GameState,
    camera,
    input_state,
    movement_profile,
    mouse_position,
) -> bool:
    player = game_state.player
    floor = game_state.floor

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        if not (
            player.directional_ability_aiming
            or player.act_two.fire_bomb_aiming
            or player.act_two.scroll_aiming_kind is not None
        ):
            return False
        if player.directional_ability_aiming:
            cancel_ability_aiming(game_state)
        cancel_fire_bomb_aiming(game_state)
        cancel_scroll_aiming(game_state)
        return True

    if not (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and not game_state.class_selection_open
        and not game_state.upgrade_screen_open
        and player.health > 0
    ):
        return False

    target_cell = (
        act_two_screen_to_cell(mouse_position, camera)
        if mouse_position is not None
        else None
    )
    if player.player_class == "mage" and player.directional_ability_aiming:
        if is_valid_mage_arcane_burst_target(game_state, target_cell):
            _post_target_event(mage_ability_target=target_cell)
        return True

    if player.act_two.fire_bomb_aiming:
        if is_valid_fire_bomb_target(game_state, target_cell):
            _post_target_event(
                fire_bomb_target=target_cell,
                fire_bomb_slot=player.act_two.fire_bomb_aiming_slot,
            )
        return True

    if player.act_two.scroll_aiming_kind is not None:
        if enemy_at_scroll_target(game_state, target_cell):
            _post_target_event(
                scroll_target=target_cell,
                scroll_slot=player.act_two.scroll_aiming_slot,
            )
        return True

    enemy_targeted = (
        target_cell is not None
        and target_cell in floor.visible_cells
        and any(
            enemy.health > 0
            and target_cell in get_enemy_occupied_positions(enemy)
            for enemy in floor.enemies
        )
    )
    if (
        player.player_class == "mage"
        and player.selected_rune_id == "rune_of_resonance"
        and enemy_targeted
    ):
        input_state.cancel_auto_move()
        input_state.reset_held_movement()
        if get_mage_resonance_target(game_state, target_cell) is not None:
            _post_target_event(resonance_target=target_cell)
        else:
            start_auto_move(input_state, game_state, target_cell)
        return True

    if target_cell is None or target_cell not in floor.visible_cells:
        return True

    player_position = (floor.player_column, floor.player_row)
    adjacent_direction = direction_between_adjacent_cells(
        player_position,
        target_cell,
    )
    if adjacent_direction is None:
        start_auto_move(input_state, game_state, target_cell)
        return True

    input_state.cancel_auto_move()
    input_state.reset_held_movement()
    if not movement_input_is_locked(input_state, pygame.time.get_ticks()):
        _post_target_event(
            movement_direction=adjacent_direction,
            movement_revision=(
                input_state.movement_revision
                if movement_profile.step_duration_ms > 0
                else None
            ),
        )
    return True


__all__ = ["handle_act_two_pointer_event"]
