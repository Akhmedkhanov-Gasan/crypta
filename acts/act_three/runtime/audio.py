import pygame

from acts.act_three.audio.ambience import DungeonAmbience
from acts.act_three.audio.playlist import ExplorationPlaylist
from acts.act_three.audio.torch import TorchAmbience
from game.combat_log import add_log_message


class ActThreeAudioRuntime:
    def __init__(self):
        self.music_attempted = False
        self._playlist = None
        self._ambience = None
        self._torch = None
        self._last_update = None
        self._paused = False
        self._player = None

    def reset(self):
        if self._playlist is not None:
            self._playlist.stop()
        if self._ambience is not None:
            self._ambience.stop()
        if self._torch is not None:
            self._torch.stop()
        self.__init__()

    def set_music_volume(self, volume):
        if self._playlist is not None:
            self._playlist.set_volume(volume)

    def set_paused(self, paused, current_time):
        if self._paused != paused:
            if self._playlist is not None:
                self._playlist.pause(paused)
            if self._ambience is not None:
                self._ambience.pause(paused)
            if self._torch is not None:
                self._torch.pause(paused)
            self._paused = paused
            self._last_update = current_time

    def ensure_music(
        self,
        game_state,
        current_act,
        music_volume,
        act_one_music_attempted,
        act_two_audio_runtime,
        sounds,
    ):
        if current_act != 3:
            if self.music_attempted:
                self.reset()
            return act_one_music_attempted

        if self._player is not None and self._player is not game_state.player:
            self.reset()
        if not self.music_attempted:
            self.music_attempted = True
            self._player = game_state.player
            act_one_music_attempted = False
            act_two_audio_runtime.music_attempted = False
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init()
                pygame.mixer.music.stop()
                self._playlist = ExplorationPlaylist()
                self._ambience = DungeonAmbience(game_state.combat_log)
                self._torch = TorchAmbience()
                if not self._playlist.paths:
                    add_log_message(game_state.combat_log, "Act III music playlist is empty.", category="system")
                if not self._ambience.sounds:
                    add_log_message(game_state.combat_log, "Act III dungeon ambience is empty.", category="system")
            except (OSError, pygame.error) as error:
                add_log_message(game_state.combat_log, f"Act III atmosphere unavailable: {error}", category="system")

        now = pygame.time.get_ticks()
        elapsed = 0 if self._last_update is None else max(0, min(250, now - self._last_update))
        self._last_update = now
        if self._paused or pygame.mixer.get_init() is None:
            return act_one_music_attempted
        if self._playlist is not None:
            self._playlist.update(elapsed, music_volume, game_state.combat_log)
        if self._ambience is not None:
            self._ambience.update(
                elapsed,
                self._playlist is not None and self._playlist.playing and music_volume > 0,
                sounds.master_volume,
            )
        if self._torch is not None:
            self._torch.update(game_state, elapsed, sounds.master_volume)
        return act_one_music_attempted


__all__ = ["ActThreeAudioRuntime"]
