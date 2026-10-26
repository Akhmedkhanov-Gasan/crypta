from dataclasses import dataclass

import pygame

from acts.act_one.presentation.death_scene import handle_act_one_death_event
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    handle_oracle_cutscene_event,
    oracle_cutscene_active,
)
from acts.act_two.presentation.death_score import handle_act_two_death_event
from application.directional_input import MOVEMENT_KEYS
from application.menu_actions import MenuActionState, handle_application_menu_action
from application.movement_input import release_held_movement
from presentation.display import window_to_game_position
from presentation.menu import handle_menu_event
from settings import GAME_HEIGHT, GAME_WIDTH


@dataclass(frozen=True)
class ModalEventResult:
    handled: bool
    state: MenuActionState


class ApplicationModalController:
    def __init__(
        self,
        screen_state,
        game_surface,
        run_session,
        loading,
        act_two_renderer,
        movement_state,
        menu_runtime,
        act_two_audio_runtime,
        act_three_audio_runtime,
        act_one_sounds,
        act_two_transition_sounds,
        act_two_sounds,
        act_three_sounds,
        death_score_layout,
    ):
        self.screen_state = screen_state
        self.game_surface = game_surface
        self.run_session = run_session
        self.loading = loading
        self.act_two_renderer = act_two_renderer
        self.movement_state = movement_state
        self.menu_runtime = menu_runtime
        self.act_two_audio_runtime = act_two_audio_runtime
        self.act_three_audio_runtime = act_three_audio_runtime
        self.act_one_sounds = act_one_sounds
        self.act_two_transition_sounds = act_two_transition_sounds
        self.act_two_sounds = act_two_sounds
        self.act_three_sounds = act_three_sounds
        self.death_score_layout = death_score_layout

    def handle(
        self,
        event,
        state,
        app_runtime,
        menu_state,
        current_act,
        active_menu_layouts,
    ):
        game_state = state.game_state
        if oracle_cutscene_active(game_state.floor):
            oracle_action = handle_oracle_cutscene_event(
                game_state.floor,
                event,
                self.game_surface,
                self._event_position(event),
            )
            self._stop_movement()
            if oracle_action == "summary":
                game_state.game_won = True
                game_state.run_stats.completed_floors.add(game_state.floor_index)
                game_state.player.act_two.death_score_open = True
                game_state.player.act_two.death_input_unlock_at = (
                    pygame.time.get_ticks() + 250
                )
                game_state.floor.oracle_death.finished = True
            elif event.type not in (pygame.QUIT, pygame.VIDEORESIZE):
                return ModalEventResult(True, state)

        if event.type == pygame.WINDOWFOCUSLOST:
            self.movement_state.reset_held_movement()
            self.movement_state.cancel_auto_move()
            return ModalEventResult(True, state)
        if event.type == pygame.KEYUP and event.key in MOVEMENT_KEYS:
            release_held_movement(self.movement_state, event.key)
            return ModalEventResult(True, state)

        death_menu_requested = False
        if (
            not app_runtime.menu_open
            and current_act == 1
            and game_state.player.health <= 0
            and event.type not in (pygame.QUIT, pygame.VIDEORESIZE)
        ):
            death_action = handle_act_one_death_event(
                event,
                game_state,
                self._event_position(event),
                pygame.time.get_ticks(),
                self.game_surface.get_size(),
            )
            if death_action != "menu":
                return ModalEventResult(True, state)
            self._stop_movement()
            app_runtime.menu_open = True
            death_menu_requested = True

        if (
            not app_runtime.menu_open
            and current_act == 2
            and (
                game_state.player.health <= 0
                or game_state.player.act_two.death_score_open
            )
            and event.type not in (pygame.QUIT, pygame.VIDEORESIZE)
        ):
            death_action = handle_act_two_death_event(
                event,
                game_state,
                self.death_score_layout,
                self._event_position(event),
                pygame.time.get_ticks(),
            )
            if death_action != "menu":
                return ModalEventResult(True, state)
            self._stop_movement()
            app_runtime.menu_open = True
            death_menu_requested = True

        if event.type == pygame.QUIT:
            app_runtime.request_quit()
            return ModalEventResult(True, state)
        if event.type == pygame.VIDEORESIZE and not self.screen_state.fullscreen:
            self.screen_state.resize_windowed(
                event.w,
                event.h,
                (GAME_WIDTH, GAME_HEIGHT),
            )
            return ModalEventResult(True, state)
        if app_runtime.menu_open:
            menu_action = (
                "abandon_run"
                if death_menu_requested
                else handle_menu_event(
                    event,
                    menu_state,
                    self._event_position(event),
                    app_runtime.game_started,
                    self.screen_state.fullscreen,
                    state.menu_progress.highest_act_reached,
                    menu_layout=active_menu_layouts[
                        "confirm"
                        if menu_state.page == "confirm_abandon"
                        else menu_state.page
                    ],
                )
            )
            state = handle_application_menu_action(
                menu_action,
                state,
                app_runtime,
                menu_state,
                self.run_session,
                self.loading,
                self.screen_state,
                self.act_two_renderer,
                self.movement_state,
                self.menu_runtime,
                self.act_two_audio_runtime,
                self.act_three_audio_runtime,
                self.act_one_sounds,
                self.act_two_transition_sounds,
                self.act_two_sounds,
                self.act_three_sounds,
            )
            return ModalEventResult(True, state)
        return ModalEventResult(
            game_state.floor_transition_started_at >= 0,
            state,
        )

    def _event_position(self, event):
        return window_to_game_position(
            self.screen_state.screen,
            getattr(event, "pos", pygame.mouse.get_pos()),
        )

    def _stop_movement(self):
        self.movement_state.reset_held_movement()
        self.movement_state.cancel_auto_move()
        self.movement_state.cancel_consumable_drag()


__all__ = ["ApplicationModalController", "ModalEventResult"]
