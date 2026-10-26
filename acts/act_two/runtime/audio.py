from dataclasses import dataclass

import pygame
import resource_store as resources

from game.state import GameState

from game.combat_log import add_log_message
from presentation.layout import (
    ACT_TWO_MUSIC_PATH,
    AWAKENING_HOLD_END_MS,
    AWAKENING_SECOND_OPEN_START_MS,
)


@dataclass
class ActTwoAudioRuntime:
    transition_started: bool = False
    eyes_close_played: bool = False
    eyes_open_played: bool = False
    music_attempted: bool = False

    def reset(self):
        self.transition_started = False
        self.eyes_close_played = False
        self.eyes_open_played = False
        self.music_attempted = False

    @staticmethod
    def _play_music(game_state, music_volume, fade_ms):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            resources.load_music(str(ACT_TWO_MUSIC_PATH))
            pygame.mixer.music.set_volume(music_volume)
            pygame.mixer.music.play(-1, fade_ms=fade_ms)
        except pygame.error as audio_error:
            add_log_message(
                game_state.combat_log,
                f"Act II music unavailable: {audio_error}",
                category="system",
            )

    def update_class_transition(
        self,
        game_state: GameState,
        current_time,
        transition_sounds,
        music_volume,
        warden_music_channel,
    ):
        if not game_state.class_selection_open:
            return warden_music_channel, False

        awakening_elapsed = current_time - game_state.class_transition_started_at
        music_started = False
        if not self.transition_started:
            self.transition_started = True
            if warden_music_channel is not None:
                warden_music_channel.fadeout(1400)
                warden_music_channel = None
            if awakening_elapsed >= AWAKENING_SECOND_OPEN_START_MS:
                self.eyes_close_played = True
            if not self.music_attempted:
                self.music_attempted = True
                music_started = True
                self._play_music(game_state, music_volume, fade_ms=1400)

        if (
            awakening_elapsed >= AWAKENING_HOLD_END_MS
            and not self.eyes_close_played
        ):
            self.eyes_close_played = True
            transition_sounds.play("eyes_close")
        if (
            awakening_elapsed >= AWAKENING_SECOND_OPEN_START_MS
            and not self.eyes_open_played
        ):
            self.eyes_open_played = True
            transition_sounds.play("eyes_open")
        return warden_music_channel, music_started

    def ensure_gameplay_music(
        self,
        game_state: GameState,
        current_act,
        music_volume,
    ):
        if (
            current_act != 2
            or game_state.class_selection_open
            or (
                game_state.floor.has_oracle_gate
                and game_state.floor.oracle_intro is not None
            )
        ):
            return
        if (
            self.music_attempted
            and pygame.mixer.get_init() is not None
            and pygame.mixer.music.get_busy()
        ):
            return
        self.music_attempted = True
        self._play_music(game_state, music_volume, fade_ms=700)


__all__ = ["ActTwoAudioRuntime"]
