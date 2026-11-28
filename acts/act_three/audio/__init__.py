from collections.abc import Iterable

from acts.act_three.audio.assassin import AssassinSoundBank
from acts.act_three.audio.footsteps import FootstepSoundBank
from acts.act_three.audio.environment import EnvironmentSoundBank
from acts.act_three.audio.melee import MeleeAttackSoundBank
from acts.act_three.audio.warlock import WarlockSoundBank
from game.events import GameEvent


class ActThreeSoundBank:
    def __init__(
        self,
        assassin: AssassinSoundBank,
        footsteps: FootstepSoundBank,
        warlock: WarlockSoundBank,
        melee: MeleeAttackSoundBank,
        environment: EnvironmentSoundBank,
    ):
        self.assassin = assassin
        self.footsteps = footsteps
        self.warlock = warlock
        self.melee = melee
        self.environment = environment
        self.master_volume = 1.0

    @classmethod
    def load(cls) -> "ActThreeSoundBank":
        return cls(
            assassin=AssassinSoundBank.load(),
            footsteps=FootstepSoundBank.load(),
            warlock=WarlockSoundBank.load(),
            melee=MeleeAttackSoundBank.load(),
            environment=EnvironmentSoundBank.load(),
        )

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self.assassin.set_master_volume(volume)
        self.footsteps.set_master_volume(volume)
        self.warlock.set_master_volume(volume)
        self.melee.set_master_volume(volume)
        self.environment.set_master_volume(volume)

    def play_events(
        self,
        events: Iterable[GameEvent],
        player,
    ) -> None:
        events = tuple(events)
        self.footsteps.play_events(events, player)
        self.assassin.play_events(events, player)
        self.warlock.play_events(events, player)
        self.melee.play_events(events, player)
        self.environment.play_events(events)

    def update(
        self,
        player,
        current_time: int,
    ) -> None:
        self.footsteps.update(player, current_time)
        self.melee.update(player, current_time)
        self.assassin.update_invisibility(player)
        self.assassin.update_killing_spree_targeting(player)
        self.assassin.update_killing_spree(
            player,
            current_time,
        )
