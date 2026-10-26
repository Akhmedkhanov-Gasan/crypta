import pygame

from acts.act_one.upgrades import handle_upgrade_key_input
from acts.act_three.input import (
    handle_act_three_flow_key,
    handle_act_three_key_event,
)
from acts.act_two.abilities import select_directional_ability_direction
from acts.act_two.controls import (
    CONSUMABLE_KEYS,
    visual_direction as act_two_visual_direction,
)
from acts.act_two.enemies.oracle.combat import finish_oracle_animation_before_action
from acts.act_two.input.action_request import ActTwoActionRequest
from acts.act_two.input.class_selection import handle_class_selection_key
from application.directional_input import (
    MOVEMENT_KEYS,
    WAIT_KEYS,
    movement_direction_for_key,
)
from application.movement_input import (
    accept_movement_direction,
    begin_held_movement,
    movement_input_is_locked,
)
from application.player_stun import stunned_wait_event
from application.player_turn import resolve_player_turn
from levels import FLOOR_CONFIGS
from presentation.control_effects import forced_movement_is_active
from presentation.cursors import set_archer_attack_cursor
from systems.player_abilities import (
    AbilityRequestResult,
    cancel_ability_aiming,
    request_class_ability,
)


class GameplayKeyboardController:
    def __init__(
        self,
        loading,
        window_state,
        movement_state,
        act_three_audio_runtime,
        act_two_transition_sounds,
        act_one_sounds,
        act_two_sounds,
        act_three_sounds,
        first_act_final_floor,
    ):
        self.loading = loading
        self.window_state = window_state
        self.movement_state = movement_state
        self.act_three_audio_runtime = act_three_audio_runtime
        self.act_two_transition_sounds = act_two_transition_sounds
        self.act_one_sounds = act_one_sounds
        self.act_two_sounds = act_two_sounds
        self.act_three_sounds = act_three_sounds
        self.first_act_final_floor = first_act_final_floor

    def handle(
        self,
        event,
        game_state,
        app_runtime,
        menu_state,
        game_surface,
        current_act,
        continuous_movement_available,
        movement_profile,
    ):
        barrage_resume = getattr(event, "archer_barrage_resume", False)
        automatic_movement = getattr(event, "automatic_movement", False)
        if (
            (
                event.key in MOVEMENT_KEYS
                or getattr(event, "movement_direction", None) is not None
            )
            and not (
                current_act == 3
                and (
                    game_state.player.archer_basic_aiming
                    or game_state.player.archer_piercing_aiming
                    or game_state.player.archer_barrage_zone_aiming
                )
            )
            and movement_input_is_locked(
                self.movement_state,
                pygame.time.get_ticks(),
            )
        ):
            self.movement_state.reset_held_movement()
            return game_state

        if not automatic_movement:
            self.movement_state.cancel_auto_move()
        if event.key == pygame.K_F11:
            self.window_state.toggle_fullscreen()
            return game_state

        if handle_act_three_key_event(event, game_state):
            if movement_profile.step_duration_ms > 0:
                self.movement_state.reset_held_movement()
                self.movement_state.cancel_auto_move()
            return game_state

        flow_result = handle_act_three_flow_key(
            event,
            game_state,
            self.loading,
            self.act_three_audio_runtime,
            app_runtime,
            barrage_resume,
        )
        game_state = flow_result.game_state
        if flow_result.handled:
            return game_state

        if handle_class_selection_key(
            event,
            game_state,
            self.act_two_transition_sounds,
            pygame.time.get_ticks(),
        ):
            return game_state
        if handle_upgrade_key_input(
            game_state,
            event.key,
            pygame.time.get_ticks(),
        ):
            return game_state

        if current_act == 2 and (
            event.key in MOVEMENT_KEYS
            or event.key in WAIT_KEYS
            or event.key in CONSUMABLE_KEYS
            or event.key in (pygame.K_UNKNOWN, pygame.K_e)
        ):
            oracle_interrupted_player = finish_oracle_animation_before_action(
                game_state,
                pygame.time.get_ticks(),
                self.act_two_sounds,
            )
            if oracle_interrupted_player:
                self.movement_state.cancel_auto_move()
            if game_state.player.health <= 0:
                self.movement_state.reset_held_movement()
                self.movement_state.cancel_auto_move()
                return game_state

        stunned_action = False
        if game_state.player.stun_turns > 0 and not barrage_resume:
            if forced_movement_is_active(
                game_state.player,
                pygame.time.get_ticks(),
            ):
                self.movement_state.reset_held_movement()
                self.movement_state.cancel_auto_move()
                return game_state
            if not (
                event.key in MOVEMENT_KEYS
                or event.key in WAIT_KEYS
                or event.key in CONSUMABLE_KEYS
                or event.key
                in (
                    pygame.K_UNKNOWN,
                    pygame.K_e,
                    pygame.K_h,
                    pygame.K_1,
                )
            ):
                return game_state
            event = stunned_wait_event(
                game_state,
                next(iter(WAIT_KEYS)),
            )
            stunned_action = True
            self.movement_state.reset_held_movement()
            self.movement_state.cancel_auto_move()

        game_state.clear_events()
        action_request = ActTwoActionRequest.from_event(
            event,
            game_state,
            enabled=current_act == 2,
        )
        mage_ability_target = action_request.mage_ability_target
        if current_act == 2 and action_request.handle_aiming(
            event,
            game_state,
            self.movement_state,
        ):
            return game_state

        column_change = 0
        row_change = 0
        movement_direction = getattr(event, "movement_direction", None)
        direction_key = event.key in MOVEMENT_KEYS
        if direction_key and game_state.player.directional_ability_aiming:
            self.movement_state.reset_held_movement()
            movement_direction = movement_direction_for_key(event.key)
        elif direction_key or movement_direction is not None:
            if not continuous_movement_available:
                self.movement_state.reset_held_movement()
                return game_state
            if direction_key and not automatic_movement:
                movement_direction = begin_held_movement(
                    self.movement_state,
                    event.key,
                    pygame.time.get_ticks(),
                    profile=movement_profile,
                )

        if movement_direction is not None:
            if (
                not game_state.player.directional_ability_aiming
                and not accept_movement_direction(
                    self.movement_state,
                    movement_direction,
                    pygame.time.get_ticks(),
                    profile=movement_profile,
                    auto_path=hasattr(event, "auto_move_revision"),
                )
            ):
                return game_state
            column_change, row_change = movement_direction
            game_state.player.facing_direction = act_two_visual_direction(
                movement_direction
            )

        player_tried_to_move = column_change != 0 or row_change != 0
        directional_ability_cast = (
            game_state.player.player_class == "warrior"
            and game_state.player.directional_ability_aiming
            and player_tried_to_move
        )
        if directional_ability_cast and current_act in (2, 3):
            directional_ability_cast = select_directional_ability_direction(
                game_state,
                column_change,
                row_change,
            )
            if not directional_ability_cast:
                return game_state

        rogue_ability_activated = False
        assassin_ability_pressed = (
            event.key == pygame.K_1
            and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
            and game_state.player.subclass == "assassin"
        )
        if event.key == pygame.K_e or assassin_ability_pressed:
            ability_request = request_class_ability(game_state)
            if current_act == 3 and game_state.player.player_class == "warrior":
                set_archer_attack_cursor(
                    game_state.player.directional_ability_aiming
                )
            rogue_ability_activated = (
                ability_request is AbilityRequestResult.ROGUE_ACTIVATED
            )
            if ability_request in (
                AbilityRequestResult.NOT_READY,
                AbilityRequestResult.AIMING_TOGGLED,
            ):
                return game_state

        if (
            game_state.player.directional_ability_aiming
            and game_state.player.player_class == "mage"
            and mage_ability_target is None
        ):
            if event.key == pygame.K_ESCAPE:
                cancel_ability_aiming(game_state)
            return game_state
        if (
            game_state.player.directional_ability_aiming
            and not player_tried_to_move
            and mage_ability_target is None
        ):
            if event.key == pygame.K_ESCAPE:
                cancel_ability_aiming(game_state)
            return game_state

        if event.key == pygame.K_ESCAPE:
            self.movement_state.reset_held_movement()
            self.movement_state.cancel_auto_move()
            self.movement_state.cancel_consumable_drag()
            menu_state.pause_background = game_surface.copy()
            app_runtime.open_menu(pygame.time.get_ticks())
            menu_state.page = "pause"
            menu_state.selected_index = 0
            return game_state

        resolve_player_turn(
            game_state,
            current_act,
            event,
            (column_change, row_change),
            action_request,
            mage_ability_target,
            directional_ability_cast,
            rogue_ability_activated,
            stunned_action,
            barrage_resume,
            automatic_movement,
            self.first_act_final_floor,
            self.movement_state,
            movement_profile,
            self.act_one_sounds,
            self.act_two_sounds,
            self.act_three_sounds,
        )
        return game_state


__all__ = ["GameplayKeyboardController"]
