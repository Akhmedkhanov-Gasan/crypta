import random
from collections.abc import Iterable
from pathlib import Path

import pygame
import resource_store as resources

from game.events import GameEvent, GameEventType


ACT_ONE_SOUND_FILES = {
    "gold_pickup": ("Ancient gold_1.mp3", "Ancient gold_2.mp3"),
    "chest_open": (
        "Heavy wooden treasure_1.mp3",
        "Heavy wooden treasure_2.mp3",
    ),
    "warden_attack": ("Warden_1.mp3", "Warden_2.mp3"),
    "warden_warning": (
        "Crypt Warden attack_1.mp3",
        "Crypt Warden attack_2.mp3",
    ),
    "healing": ("Dark fantasy healing_1.mp3", "Dark fantasy healing_2.mp3"),
    "dodge": ("Fast evasive_1.mp3", "Fast evasive_2.mp3"),
    "player_hurt": ("Heavy body impact_1.mp3", "Heavy body impact_2.mp3"),
    "common_enemy_attack": (
        "Isolated common enemy attack_1.mp3",
        "Isolated common enemy attack_2.mp3",
    ),
    "enemy_pain": (
        "Very short goblin pain_1.mp3",
        "Very short goblin pain_2.mp3",
    ),
    "potion_pickup": (
        "Small glass potion_1.mp3",
        "Small glass potion_2.mp3",
    ),
    "enemy_death": (
        "Small hostile creature collapsing_1.mp3",
        "Small hostile creature collapsing_2.mp3",
    ),
    "sword_impact": (
        "Isolated sword impact_1.mp3",
        "Isolated sword impact_2.mp3",
    ),
}


ACT_ONE_SOUND_VOLUMES = {
    "gold_pickup": 0.55,
    "chest_open": 0.60,
    "potion_pickup": 0.55,
    "healing": 0.65,
    "sword_impact": 0.70,
    "enemy_pain": 0.55,
    "player_hurt": 0.75,
    "dodge": 0.60,
    "enemy_death": 0.65,
    "common_enemy_attack": 0.55,
    "warden_warning": 0.70,
    "warden_attack": 0.75,
}


def warden_music_should_play(floor) -> bool:
    return (
        floor.boss_fight_started
        and any(enemy.type == "warden" for enemy in floor.enemies)
    )


def warden_has_been_defeated(floor) -> bool:
    wardens = [enemy for enemy in floor.enemies if enemy.type == "warden"]
    return bool(wardens) and all(warden.health <= 0 for warden in wardens)


def sound_keys_for_act_one_events(
    events: Iterable[GameEvent],
) -> list[str]:
    events = tuple(events)
    sound_keys = []
    defeated_enemies = {
        event.actor
        for event in events
        if (
            event.type is GameEventType.DEATH
            and event.actor != "hero"
        )
    }

    def add_sound(sound_key: str) -> None:
        if sound_key not in sound_keys:
            sound_keys.append(sound_key)

    for event in events:
        if event.type is GameEventType.ATTACK:
            if event.actor == "Crypt Warden":
                add_sound("warden_attack")
        elif event.type is GameEventType.PREPARE_ATTACK:
            if event.data.get("enemy_type") == "warden":
                add_sound("warden_warning")
        elif event.type is GameEventType.HIT:
            if event.target == "hero":
                add_sound(
                    "player_hurt"
                    if event.actor == "Crypt Warden"
                    else "common_enemy_attack"
                )
            elif event.actor == "hero":
                add_sound("sword_impact")
                if (
                    event.target not in defeated_enemies
                    and event.target != "Crypt Warden"
                ):
                    add_sound("enemy_pain")
        elif (
            event.type is GameEventType.DODGE
            and event.target == "hero"
        ):
            add_sound("dodge")
        elif (
            event.type is GameEventType.HEAL
            and event.actor == "hero"
        ):
            add_sound("healing")
        elif (
            event.type is GameEventType.DEATH
            and event.actor != "hero"
        ):
            add_sound("enemy_death")
        elif event.type is GameEventType.PICKUP:
            add_sound(
                "potion_pickup"
                if event.data.get("kind") == "potion"
                else "gold_pickup"
            )
        elif event.type is GameEventType.CHEST_OPEN:
            add_sound("chest_open")

    return sound_keys


class ActOneSoundBank:
    def __init__(self, sounds: dict[str, list[pygame.mixer.Sound]]):
        self.sounds = sounds
        self.master_volume = 1.0

    @classmethod
    def load(cls, sounds_path: Path) -> "ActOneSoundBank":
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})

        loaded_sounds = {}
        for sound_key, filenames in ACT_ONE_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    sound = resources.load_sound(str(sounds_path / filename))
                except (FileNotFoundError, pygame.error):
                    continue
                variants.append(sound)
            if variants:
                loaded_sounds[sound_key] = variants

        sound_bank = cls(loaded_sounds)
        sound_bank.set_master_volume(1.0)
        return sound_bank

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        for sound_key, variants in self.sounds.items():
            sound_volume = (
                ACT_ONE_SOUND_VOLUMES[sound_key]
                * self.master_volume
            )
            for sound in variants:
                sound.set_volume(sound_volume)

    def play_events(self, events: Iterable[GameEvent]) -> None:
        for sound_key in sound_keys_for_act_one_events(events):
            variants = self.sounds.get(sound_key)
            if variants:
                random.choice(variants).play()
