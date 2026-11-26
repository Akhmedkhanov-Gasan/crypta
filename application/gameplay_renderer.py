from dataclasses import dataclass, field

import pygame

from acts.act_one.presentation.renderer import draw_act_one_gameplay
from acts.act_one.runtime import update_act_one_view
from acts.act_three.presentation import draw_act_three_gameplay
from acts.act_three.presentation.renderer import draw_act_three_foreground
from acts.act_three.presentation.hud.native import NativeActThreeHud
from acts.act_three.presentation.pickup_feedback import draw_pickup_feedback
from acts.act_three.awakening.selection import draw_selection
from application.frame_overlays import draw_frame_overlays
from application.ground_items import ground_item_input_available
from presentation.display import game_viewport, present_game, window_to_game_position
from settings import BACKGROUND_COLOR, FPS


@dataclass
class GameplayRenderer:
    act_one_fonts: object
    act_one_gameplay_assets: object
    act_two_fonts: object
    act_two_sprites: object
    act_three_fonts: object
    act_three_gameplay_assets: object
    act_three_transition_assets: object
    act_one_world_surface: object
    act_two_renderer: object
    act_two_interface: object
    cutscene_skip: object
    dev_console: object
    native_act_three_hud: NativeActThreeHud = field(default_factory=NativeActThreeHud)

    def _draw_native_subclass_selection(self, target, window, game_state):
        viewport, _ = game_viewport(window.get_size())
        mouse = pygame.mouse.get_pos()
        mouse_position = (
            (mouse[0] - viewport.x, mouse[1] - viewport.y)
            if viewport.collidepoint(mouse) else None
        )
        draw_selection(
            target, self.act_three_fonts["title"], self.act_three_fonts["heading"],
            self.act_three_fonts["text"], self.act_three_transition_assets,
            mouse_position, game_state.player.subclass, game_state.player.player_class,
            pressed_subclass=game_state.act_three.subclass_pressed_option,
        )
        self.dev_console.draw(target)

    def draw(
        self,
        screen,
        game_surface,
        clock,
        game_state,
        current_act,
        current_act_floor,
        current_time,
        act_one_camera,
        act_two_camera,
        act_two_input_state,
        ground_item_window,
        continuous_movement_available,
    ):
        mouse_position = window_to_game_position(
            screen,
            pygame.mouse.get_pos(),
        )
        overlay_target = game_surface

        if current_act == 1:
            update_act_one_view(act_one_camera, game_state, current_time)
            draw_act_one_gameplay(
                game_surface,
                self.act_one_world_surface,
                act_one_camera,
                game_state,
                self.act_one_fonts,
                self.act_one_gameplay_assets,
                self.act_two_sprites,
                current_time,
                current_act_floor,
                mouse_position,
            )
        elif current_act >= 3:
            game_surface.fill(BACKGROUND_COLOR)
            draw_act_three_gameplay(
                game_surface,
                game_state,
                self.act_three_fonts,
                self.act_three_gameplay_assets,
                current_time,
                mouse_position,
                defer_interface=True,
            )
            overlay_target = self.native_act_three_hud.foreground(game_surface.get_size())
            draw_act_three_foreground(
                overlay_target,
                game_state,
                self.act_three_fonts,
                self.act_three_gameplay_assets,
                current_time,
                background=game_surface,
                mouse_position=mouse_position,
                defer_rune_menu=True,
            )
            if ground_item_input_available(game_state) and not ground_item_window.is_open:
                draw_pickup_feedback(
                    overlay_target,
                    game_state,
                    ground_item_window,
                    current_time,
                    show_prompt=continuous_movement_available,
                )
        else:
            game_surface.fill(BACKGROUND_COLOR)
            oracle_world_frame = self.act_two_renderer.draw_gameplay(
                game_surface,
                game_state,
                act_two_camera,
                self.act_two_sprites,
                self.act_two_fonts,
                self.act_two_fonts["status"],
                current_time,
                current_act_floor,
                mouse_position,
                act_two_input_state,
                ground_item_window,
            )
            if not game_state.act_three_transition_open:
                self.act_two_interface.draw(
                    game_surface,
                    game_state,
                    act_two_camera,
                    ground_item_window,
                    act_two_input_state,
                    current_time,
                    mouse_position,
                    oracle_world_frame,
                    continuous_movement_available,
                )

        draw_frame_overlays(
            overlay_target,
            game_state,
            current_act,
            current_time,
            self.act_one_fonts,
            self.act_two_fonts,
            self.act_three_fonts,
            self.act_two_sprites,
            self.act_three_transition_assets,
            self.cutscene_skip,
            self.dev_console,
            mouse_position,
            act_two_camera,
            defer_subclass_selection=current_act >= 3,
        )
        if current_act >= 3:
            native_overlay = None
            if game_state.subclass_selection_open:
                native_overlay = lambda target: self._draw_native_subclass_selection(target, screen, game_state)
            elif game_state.act_three.rune_menu is not None:
                from acts.act_three.rune_master.presentation import draw_native_rune_menu

                native_overlay = lambda target: draw_native_rune_menu(
                    target, game_state, self.act_three_gameplay_assets, current_time, mouse_position,
                )
            elif ground_item_window.is_open and ground_item_input_available(game_state) and not self.dev_console.is_open:
                from acts.act_three.presentation.items.loot_window import draw_native_loot_overlay

                native_overlay = lambda target: draw_native_loot_overlay(
                    target, game_state, ground_item_window,
                    self.act_three_gameplay_assets, self.act_three_fonts, current_time,
                )
            self.native_act_three_hud.present(
                screen, game_surface, overlay_target, game_state,
                self.act_three_fonts, self.act_three_gameplay_assets, current_time,
                native_overlay=native_overlay,
            )
        else:
            present_game(screen, game_surface)
        clock.tick(FPS)
