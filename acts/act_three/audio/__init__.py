from collections.abc import Iterable

import pygame

from acts.act_three.audio.assassin import AssassinSoundBank
from game.events import GameEvent


class ActThreeSoundBank:
    def __init__(self, assassin: AssassinSoundBank):
        self.assassin = assassin

    @classmethod
    def load(cls) -> "ActThreeSoundBank":
        return cls(
            assassin=AssassinSoundBank.load(),
        )

    def set_master_volume(self, volume: float) -> None:
        self.assassin.set_master_volume(volume)

    def set_music_volume(self, volume: float) -> None:
        if pygame.mixer.get_init() is None:
            return

        pygame.mixer.music.set_volume(
            max(0.0, min(1.0, volume)) * 0.35
        )

    def play_events(
        self,
        events: Iterable[GameEvent],
        player,
    ) -> None:
        self.assassin.play_events(events, player)

    def update(
        self,
        player,
        current_time: int,
    ) -> None:
        self.assassin.update_invisibility(player)
        self.assassin.update_killing_spree_targeting(player)
        self.assassin.update_killing_spree(
            player,
            current_time,
        )
