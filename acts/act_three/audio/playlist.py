import random

import pygame
import resource_store as resources

from acts.act_three.audio.atmosphere_settings import (
    FADE_MS,
    MUSIC_DIRECTORY,
    MUSIC_GAIN,
    MUSIC_PATTERN,
    MUSIC_SECTION_MS,
    MUSIC_SILENCE_MS,
)
from game.combat_log import add_log_message


class ExplorationPlaylist:
    def __init__(self):
        self.paths = list(resources.glob_resources(MUSIC_DIRECTORY, MUSIC_PATTERN))
        self._bag = []
        self._last_path = None
        self._playing = False
        self._elapsed = 0
        self._duration = 0
        self._wait = 0
        self._volume = 0.0

    @property
    def playing(self):
        return self._playing

    def set_volume(self, volume):
        self._volume = max(0.0, min(1.0, volume))
        if self._playing and pygame.mixer.get_init() is not None:
            envelope = min(
                1.0,
                self._elapsed / FADE_MS,
                max(0, self._duration - self._elapsed) / FADE_MS,
            )
            pygame.mixer.music.set_volume(self._volume * MUSIC_GAIN * envelope)

    def update(self, elapsed_ms, volume, combat_log):
        self.set_volume(volume)
        if self._playing:
            self._elapsed += elapsed_ms
            if self._elapsed >= self._duration or not pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self._playing = False
                self._wait = random.randint(*MUSIC_SILENCE_MS)
            else:
                self.set_volume(volume)
            return

        self._wait = max(0, self._wait - elapsed_ms)
        if self._wait or not self.paths:
            return
        if not self._bag:
            self._bag = list(self.paths)
            random.shuffle(self._bag)
            if len(self._bag) > 1 and self._bag[-1] == self._last_path:
                self._bag[0], self._bag[-1] = self._bag[-1], self._bag[0]
        path = self._bag.pop()
        try:
            resources.load_music(str(path))
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play()
            self._playing = True
            self._elapsed = 0
            self._duration = random.randint(*MUSIC_SECTION_MS)
            self._last_path = path
        except (OSError, pygame.error) as error:
            add_log_message(combat_log, f"Act III music unavailable: {path.name}: {error}", category="system")
            self.paths.remove(path)
            self._wait = 3000

    def pause(self, paused):
        if self._playing and pygame.mixer.get_init() is not None:
            if paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def stop(self):
        if self._playing and pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        self._playing = False
