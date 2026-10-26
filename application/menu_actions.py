from dataclasses import dataclass

import pygame

from acts.act_one.camera import ActOneCamera
from acts.act_two.presentation.camera import ActTwoCamera
from application.ground_items import GroundItemInput
from game.factories import create_game_state
from game.progress_store import select_menu_theme
from presentation.cursors import set_default_cursor


@dataclass(frozen=True)
class MenuActionState:
    game_state: object
    act_one_camera: object
    act_two_camera: object
    ground_item_window: object
    menu_progress: object
    act_one_music_attempted: bool
    act_one_warden_music_attempted: bool
    act_one_warden_music_channel: object | None


def _stop_run_audio(
    state,
    menu_runtime,
    act_two_audio_runtime,
    act_three_audio_runtime,
    stop_effect_channel,
    force_music_stop=False,
    reset_act_two=True,
):
    if (
        force_music_stop
        or state.act_one_music_attempted
        or menu_runtime.music_playing
        or act_two_audio_runtime.music_attempted
        or act_three_audio_runtime.music_attempted
    ) and pygame.mixer.get_init() is not None:
        pygame.mixer.music.stop()
    if state.act_one_warden_music_channel is not None:
        state.act_one_warden_music_channel.stop()
    if stop_effect_channel and pygame.mixer.get_init() is not None:
        pygame.mixer.Channel(0).stop()
    menu_runtime.reset_music_tracking()
    if reset_act_two:
        act_two_audio_runtime.reset()
    else:
        act_two_audio_runtime.music_attempted = False
    act_three_audio_runtime.music_attempted = False
    return MenuActionState(
        game_state=state.game_state,
        act_one_camera=state.act_one_camera,
        act_two_camera=state.act_two_camera,
        ground_item_window=state.ground_item_window,
        menu_progress=state.menu_progress,
        act_one_music_attempted=False,
        act_one_warden_music_attempted=False,
        act_one_warden_music_channel=None,
    )


def handle_application_menu_action(
    action,
    state: MenuActionState,
    app_runtime,
    menu_state,
    run_session,
    loading,
    window_state,
    act_two_renderer,
    movement_state,
    menu_runtime,
    act_two_audio_runtime,
    act_three_audio_runtime,
    act_one_sounds,
    act_two_transition_sounds,
    act_two_sounds,
    act_three_sounds,
) -> MenuActionState:
    if action == "resume":
        if not menu_state.can_continue:
            return state
        menu_runtime.stop_music()
        if not app_runtime.run_in_progress:
            game_state = loading.run(run_session.resume, app_runtime)
            state = MenuActionState(
                game_state=game_state,
                act_one_camera=ActOneCamera(),
                act_two_camera=ActTwoCamera(),
                ground_item_window=GroundItemInput(),
                menu_progress=state.menu_progress,
                act_one_music_attempted=state.act_one_music_attempted,
                act_one_warden_music_attempted=(
                    state.act_one_warden_music_attempted
                ),
                act_one_warden_music_channel=state.act_one_warden_music_channel,
            )
            act_two_renderer.reset()
            movement_state.reset_for_loading()
            menu_state.pause_background = None
            menu_state.transition_from_theme = None
        app_runtime.start_game()
        return state

    if action in ("abandon_run", "new_run"):
        if not run_session.discard():
            return state
        state = _stop_run_audio(
            state,
            menu_runtime,
            act_two_audio_runtime,
            act_three_audio_runtime,
            stop_effect_channel=True,
        )
        game_state = (
            loading.run(create_game_state)
            if action == "new_run"
            else create_game_state()
        )
        state = MenuActionState(
            game_state=game_state,
            act_one_camera=state.act_one_camera,
            act_two_camera=state.act_two_camera,
            ground_item_window=state.ground_item_window,
            menu_progress=state.menu_progress,
            act_one_music_attempted=state.act_one_music_attempted,
            act_one_warden_music_attempted=state.act_one_warden_music_attempted,
            act_one_warden_music_channel=state.act_one_warden_music_channel,
        )
        app_runtime.progress_tracking_enabled = True
        app_runtime.game_started = False
        app_runtime.run_in_progress = False
        menu_state.page = "main"
        menu_state.can_continue = False
        menu_state.selected_index = 1
        app_runtime.menu_started_at = pygame.time.get_ticks()
        if action == "new_run":
            app_runtime.start_game()
            menu_state.can_continue = True
            menu_state.selected_index = 0
        set_default_cursor()
        return state

    if action == "quit":
        if not app_runtime.game_started:
            app_runtime.request_quit()
            return state
        if not run_session.save(state.game_state, app_runtime):
            return state
        state = _stop_run_audio(
            state,
            menu_runtime,
            act_two_audio_runtime,
            act_three_audio_runtime,
            stop_effect_channel=True,
            force_music_stop=True,
            reset_act_two=False,
        )
        movement_state.reset_for_loading()
        app_runtime.return_to_main_menu(pygame.time.get_ticks())
        menu_state.page = "main"
        menu_state.selected_index = 0 if menu_state.can_continue else 1
        return state

    if action == "toggle_fullscreen":
        window_state.toggle_fullscreen()
        return state

    if action == "act_one_volume_changed":
        for sounds in (
            act_one_sounds,
            act_two_transition_sounds,
            act_two_sounds,
            act_three_sounds,
        ):
            sounds.set_master_volume(menu_state.effects_volume)
        if (
            act_three_audio_runtime.music_attempted
            and pygame.mixer.get_init() is not None
        ):
            act_three_sounds.set_music_volume(menu_state.music_volume)
        elif (
            state.act_one_music_attempted
            or menu_runtime.music_playing
            or act_two_audio_runtime.music_attempted
        ) and pygame.mixer.get_init() is not None:
            pygame.mixer.music.set_volume(menu_state.music_volume)
        if state.act_one_warden_music_channel is not None:
            state.act_one_warden_music_channel.set_volume(menu_state.music_volume)
        return state

    if action == "menu_theme_changed":
        return MenuActionState(
            game_state=state.game_state,
            act_one_camera=state.act_one_camera,
            act_two_camera=state.act_two_camera,
            ground_item_window=state.ground_item_window,
            menu_progress=select_menu_theme(
                state.menu_progress,
                menu_state.menu_theme,
            ),
            act_one_music_attempted=state.act_one_music_attempted,
            act_one_warden_music_attempted=state.act_one_warden_music_attempted,
            act_one_warden_music_channel=state.act_one_warden_music_channel,
        )
    return state


__all__ = ["MenuActionState", "handle_application_menu_action"]
