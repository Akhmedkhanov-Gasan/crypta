from dataclasses import dataclass

import pygame

from acts.act_three.movement import ACT_THREE_MOVEMENT_PROFILE
from application.auto_movement import accept_auto_move_event
from application.directional_input import MOVEMENT_KEYS
from application.input_policy import act_one_cutscene_active
from application.movement_input import (
    DEFAULT_MOVEMENT_PROFILE,
    movement_event_is_current,
    sync_movement_scope,
)


@dataclass(frozen=True)
class EventGateResult:
    handled: bool
    movement_profile: object


class ApplicationEventGate:
    def __init__(self, movement_state, cutscene_skip, dev_console):
        self.movement_state = movement_state
        self.cutscene_skip = cutscene_skip
        self.dev_console = dev_console

    def handle(
        self,
        event,
        game_state,
        app_runtime,
        current_act,
        continuous_movement_available,
        console_available,
    ):
        movement_profile = (
            ACT_THREE_MOVEMENT_PROFILE
            if game_state.floor.presentation_act == 3
            else DEFAULT_MOVEMENT_PROFILE
        )
        if (
            current_act == 3
            and game_state.act_three.barrage_turn is not None
            and event.type
            in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
            and not getattr(event, "archer_barrage_resume", False)
            and not (
                event.type == pygame.KEYDOWN
                and event.key
                in (pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4)
            )
        ):
            return EventGateResult(True, movement_profile)

        if (
            act_one_cutscene_active(game_state)
            and app_runtime.game_started
            and not app_runtime.menu_open
            and event.type not in (pygame.QUIT, pygame.VIDEORESIZE)
            and not (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            )
        ):
            self.movement_state.reset_held_movement()
            self.movement_state.cancel_auto_move()
            self.movement_state.cancel_consumable_drag()
            return EventGateResult(True, movement_profile)

        if self.cutscene_skip.handle_event(
            game_state,
            event,
            enabled=app_runtime.game_started and not app_runtime.menu_open,
        ):
            return EventGateResult(True, movement_profile)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            self.movement_state.cancel_auto_move()
            self.movement_state.reset_held_movement()
        elif (
            event.type == pygame.KEYDOWN
            and event.key in MOVEMENT_KEYS
            and not getattr(event, "automatic_movement", False)
        ):
            self.movement_state.cancel_auto_move()

        sync_movement_scope(
            self.movement_state,
            game_state.player,
            game_state.floor,
            movement_profile,
        )
        if not movement_event_is_current(self.movement_state, event):
            return EventGateResult(True, movement_profile)

        if (
            movement_profile.step_duration_ms > 0
            and event.type == pygame.KEYDOWN
            and not getattr(event, "automatic_movement", False)
            and event.key not in MOVEMENT_KEYS
        ):
            self.movement_state.reset_held_movement()

        if hasattr(event, "auto_move_revision"):
            if (
                app_runtime.menu_open
                or self.dev_console.is_open
                or not continuous_movement_available
            ):
                self.movement_state.cancel_auto_move()
                return EventGateResult(True, movement_profile)
            if not accept_auto_move_event(
                self.movement_state,
                game_state,
                event,
                pygame.time.get_ticks(),
            ):
                return EventGateResult(True, movement_profile)

        console_toggle_pressed = event.type == pygame.KEYDOWN and (
            event.key == pygame.K_BACKQUOTE
            or getattr(event, "scancode", None) == 53
        )
        if console_toggle_pressed and (
            console_available or self.dev_console.is_open
        ):
            if self.dev_console.is_open:
                self.dev_console.close()
            elif console_available:
                self.dev_console.open()
                self.movement_state.reset_held_movement()
                self.movement_state.reset_auto_move()
                self.movement_state.cancel_consumable_drag()
                game_state.act_two_journal_dragging = False
            return EventGateResult(True, movement_profile)

        return EventGateResult(
            self.dev_console.handle_event(event, game_state),
            movement_profile,
        )


__all__ = ["ApplicationEventGate", "EventGateResult"]
