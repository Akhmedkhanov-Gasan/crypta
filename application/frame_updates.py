from dataclasses import dataclass

from acts.act_one.music import update_act_one_music
from acts.act_one.runtime import advance_act_one_scenes, refresh_act_one_visibility
from acts.act_three.runtime import advance_act_three_frame
from acts.act_two.class_selection import (
    advance_act_two_awakening,
    begin_act_two_awakening,
)
from acts.act_two.presentation.bosses.oracle_audio import update_oracle_fire_audio
from acts.act_two.runtime import advance_oracle_runtime
from application.transitions import advance_floor_transition, complete_class_selection
from game.progress_store import record_act_reached
from levels import FLOOR_CONFIGS
from presentation.layout import CLASS_SELECTION_CHOICE_END_MS


@dataclass(frozen=True)
class GameplayFrameState:
    current_act: int
    current_act_floor: int
    menu_progress: object
    act_one_music_attempted: bool
    act_one_warden_music_attempted: bool
    act_one_warden_music_channel: object | None
    skip_frame: bool = False


class ApplicationFrameUpdater:
    def __init__(
        self,
        loading,
        cutscene_skip,
        act_two_audio_runtime,
        act_three_audio_runtime,
        act_two_input_state,
        act_one_sounds,
        act_two_transition_sounds,
        act_two_sounds,
        act_three_sounds,
    ):
        self.loading = loading
        self.cutscene_skip = cutscene_skip
        self.act_two_audio_runtime = act_two_audio_runtime
        self.act_three_audio_runtime = act_three_audio_runtime
        self.act_two_input_state = act_two_input_state
        self.act_one_sounds = act_one_sounds
        self.act_two_transition_sounds = act_two_transition_sounds
        self.act_two_sounds = act_two_sounds
        self.act_three_sounds = act_three_sounds

    def advance_shared(
        self,
        game_state,
        app_runtime,
        game_surface,
        current_time,
        music_volume,
        act_one_music_attempted,
        act_one_warden_music_channel,
    ):
        scenes_enabled = (
            app_runtime.game_started
            and not app_runtime.menu_open
            and not self.loading.completed
        )
        advance_act_one_scenes(
            game_state,
            current_time,
            enabled=scenes_enabled,
        )
        advance_floor_transition(game_state, current_time)
        self.cutscene_skip.update(
            game_state,
            current_time,
            game_surface,
            enabled=scenes_enabled,
        )
        update_oracle_fire_audio(
            game_state,
            self.act_two_sounds,
            enabled=(
                app_runtime.running
                and app_runtime.game_started
                and not app_runtime.menu_open
                and not game_state.class_selection_open
                and game_state.floor_transition_started_at < 0
            ),
        )
        (
            act_one_warden_music_channel,
            act_two_music_started,
        ) = self.act_two_audio_runtime.update_class_transition(
            game_state,
            current_time,
            self.act_two_transition_sounds,
            music_volume,
            act_one_warden_music_channel,
        )
        if act_two_music_started:
            act_one_music_attempted = False
        return act_one_music_attempted, act_one_warden_music_channel

    def advance_gameplay(
        self,
        game_state,
        app_runtime,
        menu_state,
        menu_progress,
        current_act,
        current_time,
        act_one_music_attempted,
        act_one_warden_music_attempted,
        act_one_warden_music_channel,
        act_two_camera,
    ):
        advance_act_three_frame(
            game_state,
            current_act,
            current_time,
            self.act_three_sounds,
        )
        begin_act_two_awakening(
            game_state,
            current_time,
        )
        advance_act_two_awakening(
            game_state,
            current_time,
        )
        act_one_music_attempted = self.act_three_audio_runtime.ensure_music(
            game_state,
            current_act,
            menu_state.music_volume,
            act_one_music_attempted,
            self.act_two_audio_runtime,
            self.act_three_sounds,
        )
        if (
            game_state.class_selection_open
            and game_state.class_selection_choice_started_at > 0
            and current_time - game_state.class_selection_choice_started_at
            >= CLASS_SELECTION_CHOICE_END_MS
        ):
            self.loading.run(complete_class_selection, game_state)
            return GameplayFrameState(
                current_act,
                FLOOR_CONFIGS[game_state.floor_index]["act_floor"],
                menu_progress,
                act_one_music_attempted,
                act_one_warden_music_attempted,
                act_one_warden_music_channel,
                skip_frame=True,
            )

        current_act = game_state.floor.presentation_act
        current_act_floor = FLOOR_CONFIGS[game_state.floor_index]["act_floor"]
        self.act_two_sounds.update_fire_bomb_audio(
            game_state.floor if current_act == 2 else None,
            current_time,
        )
        (
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
        ) = update_act_one_music(
            current_act,
            game_state.floor,
            menu_state.music_volume,
            game_state.combat_log,
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
            self.act_three_audio_runtime.music_attempted,
        )
        self.act_two_audio_runtime.ensure_gameplay_music(
            game_state,
            current_act,
            menu_state.music_volume,
        )
        refresh_act_one_visibility(game_state)
        if current_act == 2:
            advance_oracle_runtime(
                game_state,
                act_two_camera,
                current_time,
                self.act_two_sounds,
                menu_state.music_volume,
                self.act_two_input_state,
            )
        if (
            app_runtime.progress_tracking_enabled
            and current_act > menu_progress.highest_act_reached
        ):
            menu_progress = record_act_reached(menu_progress, current_act)
            menu_state.menu_theme = menu_progress.menu_theme

        return GameplayFrameState(
            current_act,
            current_act_floor,
            menu_progress,
            act_one_music_attempted,
            act_one_warden_music_attempted,
            act_one_warden_music_channel,
        )


__all__ = ["ApplicationFrameUpdater", "GameplayFrameState"]
