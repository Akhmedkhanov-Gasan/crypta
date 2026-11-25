from collections.abc import Iterable

from acts.act_three.audio.assassin import AssassinSoundBank
from acts.act_three.audio.footsteps import FootstepSoundBank
from game.events import GameEvent


class ActThreeSoundBank:
    def __init__(
        self,
        assassin: AssassinSoundBank,
        footsteps: FootstepSoundBank,
    ):
        self.assassin = assassin
        self.footsteps = footsteps
        self.master_volume = 1.0

    @classmethod
    def load(cls) -> "ActThreeSoundBank":
        return cls(
            assassin=AssassinSoundBank.load(),
            footsteps=FootstepSoundBank.load(),
        )

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self.assassin.set_master_volume(volume)
        self.footsteps.set_master_volume(volume)

    def play_events(
        self,
        events: Iterable[GameEvent],
        player,
    ) -> None:
        events = tuple(events)
        self.footsteps.play_events(events, player)
        self.assassin.play_events(events, player)

    def update(
        self,
        player,
        current_time: int,
    ) -> None:
        self.footsteps.update(player, current_time)
        self.assassin.update_invisibility(player)
        self.assassin.update_killing_spree_targeting(player)
        self.assassin.update_killing_spree(
            player,
            current_time,
        )
