import random

import pygame
import resource_store as resources

from acts.act_three.audio.atmosphere_settings import (
    AMBIENCE_DIRECTORY,
    AMBIENCE_GAIN_WITH_MUSIC,
    AMBIENCE_GAIN_WITHOUT_MUSIC,
    AMBIENCE_GAP_WITH_MUSIC_MS,
    AMBIENCE_GAP_WITHOUT_MUSIC_MS,
    AMBIENCE_PATTERN,
    AMBIENCE_SECTION_MS,
    FADE_MS,
)
from game.combat_log import add_log_message


class DungeonAmbience:
    def __init__(self, combat_log):
        self.sounds = []
        for path in resources.glob_resources(AMBIENCE_DIRECTORY, AMBIENCE_PATTERN):
            try:
                self.sounds.append(resources.load_sound(str(path)))
            except (OSError, pygame.error) as error:
                add_log_message(combat_log, f"Act III ambience unavailable: {path.name}: {error}", category="system")
        self._bag = []
        self._last_index = None
        self._sound = None
        self._channel = None
        self._elapsed = 0
        self._duration = 0
        self._wait = 5000
        self._music_playing = False
        self._gain = AMBIENCE_GAIN_WITH_MUSIC

    def _owns_channel(self):
        return (
            self._channel is not None
            and self._channel.get_busy()
            and self._channel.get_sound() is self._sound
        )

    def update(self, elapsed_ms, music_playing, volume):
        if not self.sounds:
            return
        if self._music_playing and not music_playing:
            self._wait = min(self._wait, random.randint(*AMBIENCE_GAP_WITHOUT_MUSIC_MS))
        self._music_playing = music_playing
        target = AMBIENCE_GAIN_WITH_MUSIC if music_playing else AMBIENCE_GAIN_WITHOUT_MUSIC
        change = elapsed_ms / FADE_MS * max(AMBIENCE_GAIN_WITH_MUSIC, AMBIENCE_GAIN_WITHOUT_MUSIC)
        self._gain += max(-change, min(change, target - self._gain))

        if self._sound is not None:
            self._elapsed += elapsed_ms
            if self._elapsed >= self._duration or not self._owns_channel():
                self.stop()
                gap = AMBIENCE_GAP_WITH_MUSIC_MS if music_playing else AMBIENCE_GAP_WITHOUT_MUSIC_MS
                self._wait = random.randint(*gap)
            else:
                envelope = min(1.0, self._elapsed / FADE_MS, max(0, self._duration - self._elapsed) / FADE_MS)
                self._channel.set_volume(max(0.0, min(1.0, volume)) * self._gain * envelope)
            return

        self._wait = max(0, self._wait - elapsed_ms)
        if self._wait:
            return
        if not self._bag:
            self._bag = list(range(len(self.sounds)))
            random.shuffle(self._bag)
            if len(self._bag) > 1 and self._bag[-1] == self._last_index:
                self._bag[0], self._bag[-1] = self._bag[-1], self._bag[0]
        self._last_index = self._bag.pop()
        self._sound = self.sounds[self._last_index]
        self._duration = min(round(self._sound.get_length() * 1000), random.randint(*AMBIENCE_SECTION_MS))
        self._elapsed = 0
        self._channel = pygame.mixer.Channel(0)
        self._channel.play(self._sound, fade_ms=FADE_MS)
        self._channel.set_volume(0.0)

    def pause(self, paused):
        if self._owns_channel():
            if paused:
                self._channel.pause()
            else:
                self._channel.unpause()

    def stop(self):
        if self._owns_channel():
            self._channel.stop()
        self._sound = None
        self._channel = None
