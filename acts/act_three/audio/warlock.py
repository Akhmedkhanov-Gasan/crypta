import pygame
import resource_store as resources

from game.events import GameEventType


WARLOCK_PULSE_PATH = (
    resources.PROJECT_ROOT
    / "assets/audio/sounds_act_3/player/magic/warlock_orb/cast/warlock_pulse_01.wav"
)
WARLOCK_PULSE_VOLUME = 0.42


class WarlockSoundBank:
    def __init__(self, pulse):
        self.pulse = pulse
        self.master_volume = 1.0

    @classmethod
    def load(cls):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            return cls(resources.load_sound(str(WARLOCK_PULSE_PATH)))
        except (OSError, pygame.error):
            return cls(None)

    def set_master_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, volume))

    def play_events(self, events, player):
        if player.subclass != "warlock" or self.pulse is None:
            return
        if not any(
            event.type is GameEventType.ATTACK
            and event.actor == "hero"
            and event.data.get("kind") == "warlock_orb"
            for event in events
        ):
            return
        channel = self.pulse.play()
        if channel is not None:
            channel.set_volume(WARLOCK_PULSE_VOLUME * self.master_volume)
