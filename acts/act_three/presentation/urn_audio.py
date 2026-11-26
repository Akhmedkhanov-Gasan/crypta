import math
import random
from array import array
from functools import lru_cache

import pygame


@lru_cache(maxsize=2)
def _urn_cry(mixer_format):
    frequency, sample_format, channels = mixer_format
    if sample_format != -16:
        return None
    duration = 3.8
    samples = array("h")
    rng = random.Random(719)
    phase = 0.0
    breath = 0.0
    for index in range(round(frequency * duration)):
        time = index / frequency
        progress = time / duration
        attack = min(1.0, time / 0.4)
        release = max(0.0, 1 - progress) ** 0.8
        envelope = attack * release
        pitch = 85 + 190 * math.sin(math.pi * progress) ** 0.7
        pitch *= 1 + 0.045 * math.sin(math.tau * 6.2 * time)
        phase += math.tau * pitch / frequency
        breath = breath * 0.72 + rng.uniform(-1, 1) * 0.28
        voice = (
            math.sin(phase) * 0.24
            + math.sin(phase * 2 + 0.7) * 0.14
            + math.sin(phase * 3 + 1.3) * 0.09
            + math.sin(phase * 5) * 0.04
        )
        throat = voice * (0.7 + 0.3 * math.sin(math.tau * 31 * time))
        rasp = breath * (0.15 + 0.15 * math.sin(phase) ** 2)
        resonance = math.sin(math.tau * 1130 * time + math.sin(phase) * 2) * 0.035
        rumble = math.sin(math.tau * 43 * time) * math.exp(-time * 1.3) * 0.2
        signal = math.tanh((throat + rasp + resonance) * 1.8) * envelope * 0.65 + rumble
        value = round(max(-1.0, min(1.0, signal)) * 32767)
        samples.extend([value] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def play_urn_cry():
    mixer_format = pygame.mixer.get_init()
    if mixer_format is None:
        return
    sound = _urn_cry(mixer_format)
    if sound is not None:
        sound.set_volume(0.52)
        sound.play()
