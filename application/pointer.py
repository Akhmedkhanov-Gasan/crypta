import pygame

from acts.act_one.input import handle_act_one_pointer_input
from acts.act_one.upgrades import handle_upgrade_pointer_input
from acts.act_three.input import handle_act_three_pointer_event
from acts.act_two.input.class_selection import handle_class_selection_pointer
from acts.act_two.input.pointer import handle_act_two_pointer_event
from presentation.display import window_to_game_position


class GameplayPointerController:
    def __init__(
        self,
        map_navigation,
        act_two_interface_input,
        movement_state,
        act_one_sounds,
        act_two_sounds,
    ):
        self.map_navigation = map_navigation
        self.act_two_interface_input = act_two_interface_input
        self.movement_state = movement_state
        self.act_one_sounds = act_one_sounds
        self.act_two_sounds = act_two_sounds

    def handle(
        self,
        event,
        game_state,
        app_runtime,
        dev_console,
        screen,
        game_surface,
        current_act,
        act_one_camera,
        act_two_camera,
        ground_item_window,
        continuous_movement_available,
        movement_profile,
    ):
        mouse_position = window_to_game_position(
            screen,
            getattr(event, "pos", pygame.mouse.get_pos()),
        )
        if ground_item_window.handle_event(
            event,
            game_state,
            self.movement_state,
            (
                self.act_one_sounds
                if current_act == 1
                else self.act_two_sounds if current_act == 2 else None
            ),
            mouse_position,
            game_surface.get_size(),
            (
                app_runtime.game_started
                and not app_runtime.menu_open
                and not dev_console.is_open
            ),
            pygame.time.get_ticks(),
        ):
            return True
        if self.map_navigation.handle_event(
            event,
            game_state,
            act_two_camera,
            mouse_position,
            enabled=continuous_movement_available,
        ):
            return True
        if current_act == 2 and self.act_two_interface_input.handle_event(
            event,
            game_state,
            act_two_camera,
            self.movement_state,
            self.act_two_sounds,
            mouse_position,
        ):
            return True
        if current_act == 3 and handle_act_three_pointer_event(
            event,
            game_state,
            screen,
            window_to_game_position,
            self.movement_state,
            continuous_movement_available,
        ):
            return True
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and game_state.upgrade_screen_open
        ):
            if mouse_position is not None:
                handle_upgrade_pointer_input(
                    game_state,
                    mouse_position,
                    pygame.time.get_ticks(),
                )
            return True
        if handle_class_selection_pointer(
            event,
            game_state,
            mouse_position,
            pygame.time.get_ticks(),
        ):
            return True
        if current_act == 2 and handle_act_two_pointer_event(
            event,
            game_state,
            act_two_camera,
            self.movement_state,
            movement_profile,
            mouse_position,
        ):
            return True
        return handle_act_one_pointer_input(
            event,
            screen,
            act_one_camera,
            self.movement_state,
            game_state,
            continuous_movement_available,
        )


__all__ = ["GameplayPointerController"]
