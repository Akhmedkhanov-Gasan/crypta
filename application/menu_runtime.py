from dataclasses import dataclass

import pygame
import resource_store as resources

from acts.act_one.music import ACT_ONE_MENU_MUSIC_PATH
from game.combat_log import add_log_message
from presentation.display import present_game
from presentation.layout import ACT_TWO_MENU_MUSIC_PATH
from presentation.menu import draw_menu, draw_run_save_error
from settings import FPS


@dataclass
class ApplicationMenuRuntime:
    act_one_music_playing: bool = False
    act_two_music_playing: bool = False

    @property
    def music_playing(self):
        return self.act_one_music_playing or self.act_two_music_playing

    def reset_music_tracking(self):
        self.act_one_music_playing = False
        self.act_two_music_playing = False

    def stop_music(self):
        if self.music_playing and pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        self.reset_music_tracking()

    @staticmethod
    def _play_music(path, volume, game_state, error_message):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            resources.load_music(str(path))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1, fade_ms=1200)
        except pygame.error as audio_error:
            add_log_message(
                game_state.combat_log,
                f"{error_message}: {audio_error}",
                category="system",
            )

    def update_music(
        self,
        game_state,
        game_started,
        menu_theme,
        music_volume,
    ):
        should_play_act_one = not game_started and menu_theme == 1
        should_play_act_two = not game_started and menu_theme == 2
        if should_play_act_one and not self.act_one_music_playing:
            self.act_one_music_playing = True
            self.act_two_music_playing = False
            self._play_music(
                ACT_ONE_MENU_MUSIC_PATH,
                music_volume,
                game_state,
                "Act I menu music unavailable",
            )
        elif should_play_act_two and not self.act_two_music_playing:
            self.act_one_music_playing = False
            self.act_two_music_playing = True
            self._play_music(
                ACT_TWO_MENU_MUSIC_PATH,
                music_volume,
                game_state,
                "Act II menu music unavailable",
            )
        elif not should_play_act_one and not should_play_act_two and self.music_playing:
            if pygame.mixer.get_init() is not None:
                pygame.mixer.music.fadeout(500)
            self.reset_music_tracking()

    def draw(
        self,
        screen,
        game_surface,
        clock,
        game_state,
        app_runtime,
        run_session,
        menu_state,
        menu_visual_theme,
        active_menu_layouts,
        menu_layouts,
        menu_fonts,
        menu_assets,
        highest_act_reached,
        current_time,
        fullscreen,
    ):
        self.update_music(
            game_state,
            app_runtime.game_started,
            menu_visual_theme,
            menu_state.music_volume,
        )
        menu_state.can_continue = run_session.can_continue(
            game_state,
            app_runtime,
        )
        if (
            menu_state.page == "main"
            and not menu_state.can_continue
            and menu_state.selected_index == 0
        ):
            menu_state.selected_index = 1

        draw_menu(
            game_surface,
            menu_fonts[menu_visual_theme],
            menu_state,
            current_time - app_runtime.menu_started_at,
            app_runtime.game_started,
            fullscreen,
            menu_assets,
            menu_visual_theme,
            highest_act_reached,
            menu_layout=(
                active_menu_layouts["confirm"]
                if menu_state.page == "confirm_abandon"
                else active_menu_layouts[menu_state.page]
            ),
            menu_layouts=menu_layouts,
        )
        draw_run_save_error(game_surface, run_session.error)
        present_game(screen, game_surface)
        clock.tick(FPS)


__all__ = ["ApplicationMenuRuntime"]
