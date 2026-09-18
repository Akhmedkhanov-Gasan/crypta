import random
from collections.abc import Iterable
from pathlib import Path

import pygame
import resource_store as resources

from acts.act_three.settings import (
    ASSASSIN_ULTIMATE_CAMERA_TRAVEL_RATIO,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
)
from game.events import GameEvent, GameEventType


_ASSASSIN_SOUNDS_PATH = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "audio"
    / "sounds_act_3"
    / "player"
    / "assassin"
)


ASSASSIN_SOUND_FILES = {
    "attack": tuple(
        f"assassin_attack_{index:02d}.mp3"
        for index in range(1, 9)
    ),
    "death": tuple(
        f"assassin_death_{index}.mp3"
        for index in range(1, 5)
    ),
    "footstep": tuple(
        f"footstep_{index:02d}.mp3"
        for index in range(1, 11)
    ),
    "hurt": tuple(
        f"assassin_hurt_{index}.mp3"
        for index in range(1, 7)
    ),
    "invisibility": tuple(
        f"invisibility_{index:02d}.mp3"
        for index in range(1, 5)
    ),
    "killing_spree": tuple(
        f"killing_spree_{index:02d}.mp3"
        for index in range(1, 7)
    ),
    "killing_spree_target": tuple(
        f"target_{index:02d}.mp3"
        for index in range(1, 7)
    ),
    "shadow_step": tuple(
        f"shadow_step_{index:02d}.mp3"
        for index in range(1, 5)
    ),
}


ASSASSIN_SOUND_DIRECTORIES = {
    "attack": _ASSASSIN_SOUNDS_PATH / "attack",
    "death": _ASSASSIN_SOUNDS_PATH / "death",
    "footstep": _ASSASSIN_SOUNDS_PATH / "footstep",
    "hurt": _ASSASSIN_SOUNDS_PATH / "hurt",
    "invisibility": (
        _ASSASSIN_SOUNDS_PATH
        / "skills"
        / "invisibility"
    ),
    "killing_spree": (
        _ASSASSIN_SOUNDS_PATH
        / "skills"
        / "killing_spree"
    ),
    "killing_spree_target": (
        _ASSASSIN_SOUNDS_PATH
        / "skills"
        / "killing_spree"
        / "target"
    ),
    "shadow_step": (
        _ASSASSIN_SOUNDS_PATH
        / "skills"
        / "shadow_step"
    ),
}


ASSASSIN_SOUND_VOLUMES = {
    "attack": 0.72,
    "death": 0.78,
    "footstep": 1.0,
    "hurt": 0.70,
    "invisibility": 0.72,
    "killing_spree": 0.78,
    "killing_spree_target": 0.72,
    "shadow_step": 0.76,
}


class AssassinSoundBank:
    def __init__(
        self,
        sounds: dict[str, list[pygame.mixer.Sound]],
    ):
        self.sounds = sounds
        self.master_volume = 1.0
        self._last_footstep = None
        self._invisibility_was_active = False
        self._ultimate_target_count = 0
        self._ultimate_started_at = None
        self._ultimate_strikes_played = 0
        self._ultimate_outro_played = False

    @classmethod
    def load(cls) -> "AssassinSoundBank":
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})

        loaded_sounds = {}

        for sound_key, filenames in ASSASSIN_SOUND_FILES.items():
            variants = []
            sound_directory = ASSASSIN_SOUND_DIRECTORIES[sound_key]

            for filename in filenames:
                try:
                    variants.append(
                        resources.load_sound(
                            str(sound_directory / filename)
                        )
                    )
                except (FileNotFoundError, pygame.error):
                    continue

            if variants:
                loaded_sounds[sound_key] = variants

        return cls(loaded_sounds)

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def _play(self, sound_key: str) -> None:
        variants = self.sounds.get(sound_key)
        if not variants:
            return

        choices = variants

        if sound_key == "footstep" and len(variants) > 1:
            choices = [
                sound
                for sound in variants
                if sound is not self._last_footstep
            ]

        sound = random.choice(choices)

        if sound_key == "footstep":
            self._last_footstep = sound

        channel = sound.play()
        if channel is not None:
            channel.set_volume(
                ASSASSIN_SOUND_VOLUMES[sound_key]
                * self.master_volume
            )

    def play_events(
        self,
        events: Iterable[GameEvent],
        player,
    ) -> None:
        if player.subclass != "assassin":
            return

        events = tuple(events)

        if any(
            event.type is GameEventType.DEATH
            and event.actor == "hero"
            for event in events
        ):
            self._play("death")
            return

        hero_moves = [
            event
            for event in events
            if event.type is GameEventType.MOVE
            and event.actor == "hero"
        ]

        if any(
            event.data.get("kind") == "teleport"
            for event in hero_moves
        ):
            self._play("shadow_step")
        elif hero_moves:
            self._play("footstep")

        if any(
            event.type is GameEventType.HIT
            and event.actor == "hero"
            and event.target not in (None, "hero", "familiar")
            and event.amount is not None
            and event.amount > 0
            and not event.data.get("blocked", False)
            for event in events
        ):
            self._play("attack")

        if any(
            event.type is GameEventType.ABILITY
            and event.actor == "hero"
            and event.data.get("ability") == "invisibility"
            for event in events
        ):
            self._play("invisibility")

        if any(
            event.type is GameEventType.HIT
            and event.target == "hero"
            and event.amount is not None
            and event.amount > 0
            and not event.data.get("blocked", False)
            for event in events
        ):
            self._play("hurt")
    def update_invisibility(self, player) -> None:
        is_assassin = player.subclass == "assassin"
        invisibility_active = (
            is_assassin
            and player.invisibility_turns > 0
        )

        if (
            is_assassin
            and player.health > 0
            and self._invisibility_was_active
            and not invisibility_active
        ):
            self._play("invisibility")

        self._invisibility_was_active = invisibility_active

    def update_killing_spree_targeting(self, player) -> None:
        selection_active = (
            player.subclass == "assassin"
            and (
                player.ultimate_aiming
                or player.ultimate_animation_active
            )
        )

        if not selection_active:
            self._ultimate_target_count = 0
            return

        target_count = len(player.ultimate_targets)

        while self._ultimate_target_count < target_count:
            self._play("killing_spree_target")
            self._ultimate_target_count += 1

        if target_count < self._ultimate_target_count:
            self._ultimate_target_count = target_count

    def update_killing_spree(
        self,
        player,
        current_time: int,
    ) -> None:
        if (
            player.subclass != "assassin"
            or not player.ultimate_animation_active
        ):
            self._ultimate_started_at = None
            self._ultimate_strikes_played = 0
            self._ultimate_outro_played = False
            return

        started_at = player.ultimate_animation_started_at
        if started_at <= 0:
            return

        if self._ultimate_started_at != started_at:
            self._ultimate_started_at = started_at
            self._ultimate_strikes_played = 0
            self._ultimate_outro_played = False
            self._play("shadow_step")

        target_count = len(player.ultimate_targets)
        if target_count <= 0:
            return

        elapsed = current_time - started_at
        travel_duration = (
            ASSASSIN_ULTIMATE_STEP_MS
            * ASSASSIN_ULTIMATE_CAMERA_TRAVEL_RATIO
        )
        action_duration = (
            ASSASSIN_ULTIMATE_STEP_MS
            - travel_duration
        )
        impact_offset = round(
            travel_duration
            + action_duration / 2
        )

        while self._ultimate_strikes_played < target_count:
            strike_started_at = (
                ASSASSIN_ULTIMATE_PRELUDE_MS
                + self._ultimate_strikes_played
                * ASSASSIN_ULTIMATE_STEP_MS
                + impact_offset
            )

            if elapsed < strike_started_at:
                break

            self._play("killing_spree")
            self._ultimate_strikes_played += 1

        outro_started_at = (
            ASSASSIN_ULTIMATE_PRELUDE_MS
            + target_count
            * ASSASSIN_ULTIMATE_STEP_MS
        )

        if (
            elapsed >= outro_started_at
            and not self._ultimate_outro_played
        ):
            self._play("shadow_step")
            self._ultimate_outro_played = True
