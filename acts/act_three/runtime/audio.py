from dataclasses import dataclass

import pygame
import resource_store as resources

from game.combat_log import add_log_message
from presentation.layout import ACT_THREE_MUSIC_PATH


@dataclass
class ActThreeAudioRuntime:
    music_attempted: bool = False

    def reset(self):
        if self.music_attempted and pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        self.music_attempted = False

    def ensure_music(
        self,
        game_state,
        current_act,
        music_volume,
        act_one_music_attempted,
        act_two_audio_runtime,
        sounds,
    ):
        if current_act != 3 or self.music_attempted:
            return act_one_music_attempted

        act_one_music_attempted = False
        act_two_audio_runtime.music_attempted = False
        self.music_attempted = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            resources.load_music(str(ACT_THREE_MUSIC_PATH))
            sounds.set_music_volume(music_volume)
            pygame.mixer.music.play(-1, fade_ms=1800)
        except pygame.error as audio_error:
            add_log_message(
                game_state.combat_log,
                f"Act III music unavailable: {audio_error}",
                category="system",
            )
        return act_one_music_attempted


__all__ = ["ActThreeAudioRuntime"]
