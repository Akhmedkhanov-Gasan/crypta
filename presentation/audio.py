import random
from collections.abc import Iterable
from pathlib import Path

import pygame

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


ACT_TWO_TRANSITION_SOUND_FILES = {
    "eyes_close": "act_2_eyes_close.mp3",
    "eyes_open": "act_2_eyes_open.mp3",
    "class_select": "act_2_class_select.mp3",
}


ACT_TWO_WARRIOR_SOUND_FILES = {
    "warrior_hit": (
        "Isolated_warrior_sword_hit_1.mp3",
        "Isolated_warrior_sword_hit_2.mp3",
    ),
    "warrior_cleave_impact": (
        "warrior_sword_hit_1.mp3",
        "warrior_sword_hit_2.mp3",
    ),
    "warrior_cleave_voice": (
        "warrior_power_cleave_voice_1.mp3",
        "warrior_power_cleave_voice_2.mp3",
    ),
    "warrior_hurt": (
        "warrior_hurt_1.mp3",
        "warrior_hurt_2.mp3",
    ),
    "warrior_death": (
        "warrior_death_1.mp3",
        "warrior_death_2.mp3",
    ),
}


ACT_TWO_ROGUE_SOUND_FILES = {
    "rogue_hit": ("rogue_dagger_hit_1.mp3", "rogue_dagger_hit_2.mp3"),
    "rogue_invisibility": (
        "rogue_invisibility_1.mp3",
        "rogue_invisibility_2.mp3",
    ),
    "rogue_hurt": ("rogue_hurt_1.mp3", "rogue_hurt_2.mp3"),
    "rogue_death": ("rogue_death_1.mp3", "rogue_death_2.mp3"),
}


ACT_TWO_MAGE_SOUND_FILES = {
    "mage_hit": ("mage_arcane_hit_1.mp3", "mage_arcane_hit_2.mp3"),
    "mage_arcane_burst": (
        "mage_arcane_burst_1.mp3",
        "mage_arcane_burst_2.mp3",
    ),
    "mage_hurt": ("mage_hurt_1.mp3", "mage_hurt_2.mp3"),
    "mage_death": ("mage_death_1.mp3", "mage_death_2.mp3"),
}


ACT_TWO_FOOTSTEP_FILES = tuple(
    f"act_2_footstep_{index}.mp3" for index in range(1, 6)
)


ACT_TWO_ENVIRONMENT_SOUND_FILES = {
    "rune_activate": ("rune_activate_1.mp3", "rune_activate_2.mp3"),
    "chest_open": ("chest_open_1.mp3", "chest_open_2.mp3"),
    "chest_break": ("chest_break_1.mp3", "chest_break_2.mp3"),
    "gold_pickup": ("gold_pickup_1.mp3", "gold_pickup_2.mp3"),
    "item_pickup": ("item_pickup_1.mp3", "item_pickup_2.mp3"),
    "key_pickup": ("item_pickup_1.mp3", "item_pickup_2.mp3"),
}


ACT_TWO_SOUND_VOLUMES = {
    "warrior_hit": 0.78,
    "warrior_cleave_impact": 0.82,
    "warrior_cleave_voice": 0.62,
    "warrior_hurt": 0.68,
    "warrior_death": 0.72,
    "rogue_hit": 0.78,
    "rogue_invisibility": 0.68,
    "rogue_hurt": 0.68,
    "rogue_death": 0.72,
    "mage_hit": 0.78,
    "mage_arcane_burst": 0.84,
    "mage_hurt": 0.68,
    "mage_death": 0.72,
    "footstep": 0.48,
    "rune_activate": 0.68,
    "chest_open": 0.62,
    "chest_break": 0.74,
    "gold_pickup": 0.72,
    "item_pickup": 0.72,
    "key_pickup": 1.00,
}


class ActTwoTransitionSoundBank:
    def __init__(self, sounds: dict[str, pygame.mixer.Sound]):
        self.sounds = sounds
        self.master_volume = 1.0

    @classmethod
    def load(cls, sounds_path: Path) -> "ActTwoTransitionSoundBank":
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})

        sounds = {}
        for sound_key, filename in ACT_TWO_TRANSITION_SOUND_FILES.items():
            try:
                sounds[sound_key] = pygame.mixer.Sound(
                    str(sounds_path / filename)
                )
            except (FileNotFoundError, pygame.error):
                continue
        return cls(sounds)

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        for sound_key, sound in self.sounds.items():
            gain = 1.35 if sound_key in ("eyes_close", "eyes_open") else 1.0
            sound.set_volume(min(1.0, self.master_volume * gain))

    def play(self, sound_key: str) -> None:
        sound = self.sounds.get(sound_key)
        if sound is not None:
            pygame.mixer.Channel(1).play(sound)


class ActTwoSoundBank:
    def __init__(self, sounds: dict[str, list[pygame.mixer.Sound]]):
        self.sounds = sounds
        self.master_volume = 1.0
        self._last_footstep = None

    @classmethod
    def load(cls, sounds_path: Path) -> "ActTwoSoundBank":
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except pygame.error:
            return cls({})

        loaded_sounds = {}
        warrior_path = sounds_path / "warrior"
        for sound_key, filenames in ACT_TWO_WARRIOR_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(warrior_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        rogue_path = sounds_path / "rogue"
        for sound_key, filenames in ACT_TWO_ROGUE_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(rogue_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        mage_path = sounds_path / "mage"
        for sound_key, filenames in ACT_TWO_MAGE_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(mage_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        footstep_path = sounds_path / "footstep"
        footsteps = []
        for filename in ACT_TWO_FOOTSTEP_FILES:
            try:
                footsteps.append(
                    pygame.mixer.Sound(str(footstep_path / filename))
                )
            except (FileNotFoundError, pygame.error):
                continue
        if footsteps:
            loaded_sounds["footstep"] = footsteps

        environment_path = sounds_path / "environment"
        for sound_key, filenames in ACT_TWO_ENVIRONMENT_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(environment_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        return cls(loaded_sounds)

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def _play(
        self,
        sound_key: str,
        distance_gain: float = 1.0,
        volume_multiplier: float = 1.0,
    ) -> None:
        variants = self.sounds.get(sound_key)
        if not variants:
            return

        choices = variants
        if sound_key == "footstep" and len(variants) > 1:
            choices = [
                sound for sound in variants if sound is not self._last_footstep
            ]
        sound = random.choice(choices)
        if sound_key == "footstep":
            self._last_footstep = sound

        channel = sound.play()
        if channel is not None:
            channel.set_volume(
                min(
                    1.0,
                    ACT_TWO_SOUND_VOLUMES[sound_key]
                    * self.master_volume
                    * max(0.0, min(1.0, distance_gain))
                    * max(0.0, volume_multiplier),
                )
            )

    def play_events(
        self,
        events: Iterable[GameEvent],
        player_class: str | None,
    ) -> None:
        events = tuple(events)
        hero_died = any(
            event.type is GameEventType.DEATH and event.actor == "hero"
            for event in events
        )

        hero_move = next(
            (
                event
                for event in events
                if event.type is GameEventType.MOVE
                and event.actor == "hero"
                and event.data.get("kind") not in ("teleport", "archer_leap")
            ),
            None,
        )
        if hero_move is not None:
            self._play("footstep")

        played_environment_sounds = set()
        for event in events:
            sound_key = None
            if (
                event.type is GameEventType.ATTACK
                and event.actor == "hero"
                and event.data.get("kind") == "wall_rune"
                and event.data.get("activated", False)
            ):
                sound_key = "rune_activate"
            elif event.type is GameEventType.CHEST_OPEN:
                sound_key = "chest_open"
            elif event.type is GameEventType.PICKUP:
                if event.data.get("kind") == "gold":
                    sound_key = "gold_pickup"
                elif event.data.get("kind") == "key":
                    sound_key = "key_pickup"
                elif event.data.get("kind") == "potion":
                    sound_key = "item_pickup"
            elif (
                event.type is GameEventType.ATTACK
                and event.actor == "hero"
                and event.data.get("kind") == "breakable_crate"
            ):
                class_attack_sound = {
                    "warrior": "warrior_hit",
                    "rogue": "rogue_hit",
                    "mage": "mage_hit",
                }.get(player_class)
                crate_sound_keys = tuple(
                    sound_key
                    for sound_key in (class_attack_sound, "chest_break")
                    if sound_key is not None
                )
                for crate_sound_key in crate_sound_keys:
                    if crate_sound_key not in played_environment_sounds:
                        self._play(crate_sound_key)
                        played_environment_sounds.add(crate_sound_key)
                continue

            if (
                sound_key is not None
                and sound_key not in played_environment_sounds
            ):
                self._play(sound_key)
                played_environment_sounds.add(sound_key)

        if player_class == "rogue":
            rogue_attacked = any(
                event.type is GameEventType.ATTACK
                and event.actor == "hero"
                and event.data.get("kind") == "basic"
                for event in events
            )
            hero_hits = [
                event
                for event in events
                if event.type is GameEventType.HIT
                and event.actor == "hero"
                and event.target not in (None, "hero", "familiar")
                and not event.data.get("blocked", False)
            ]
            if rogue_attacked:
                critical_hit = any(
                    event.data.get("critical", False)
                    for event in hero_hits
                )
                self._play(
                    "rogue_hit",
                    volume_multiplier=1.2 if critical_hit else 1.0,
                )

            if any(
                event.type is GameEventType.ABILITY
                and event.actor == "hero"
                and event.data.get("ability") == "invisibility"
                for event in events
            ):
                self._play("rogue_invisibility")

            if hero_died:
                self._play("rogue_death")
            elif any(
                event.type is GameEventType.HIT and event.target == "hero"
                for event in events
            ):
                self._play("rogue_hurt")
            return

        if player_class == "mage":
            hero_attack = next(
                (
                    event
                    for event in events
                    if event.type is GameEventType.ATTACK
                    and event.actor == "hero"
                ),
                None,
            )
            hero_hit_enemy = any(
                event.type is GameEventType.HIT
                and event.actor == "hero"
                and event.target not in (None, "hero", "familiar")
                and not event.data.get("blocked", False)
                for event in events
            )
            if hero_attack is not None:
                if hero_attack.data.get("ability") == "arcane burst":
                    self._play("mage_arcane_burst")
                elif (
                    hero_attack.data.get("kind") == "basic"
                    and hero_hit_enemy
                ):
                    self._play("mage_hit")

            if hero_died:
                self._play("mage_death")
            elif any(
                event.type is GameEventType.HIT and event.target == "hero"
                for event in events
            ):
                self._play("mage_hurt")
            return

        if player_class != "warrior":
            return

        hero_attack = next(
            (
                event
                for event in events
                if event.type is GameEventType.ATTACK
                and event.actor == "hero"
            ),
            None,
        )
        hero_hit_enemy = any(
            event.type is GameEventType.HIT
            and event.actor == "hero"
            and event.target not in (None, "hero", "familiar")
            and not event.data.get("blocked", False)
            for event in events
        )
        if hero_attack is not None:
            if hero_attack.data.get("ability") == "power cleave":
                self._play("warrior_cleave_impact")
                self._play("warrior_cleave_voice")
            elif hero_attack.data.get("kind") == "basic" and hero_hit_enemy:
                self._play("warrior_hit")

        if hero_died:
            self._play("warrior_death")
        elif any(
            event.type is GameEventType.HIT and event.target == "hero"
            for event in events
        ):
            self._play("warrior_hurt")


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
    """Translate one resolved turn into its Act One sound layers."""
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
                    sound = pygame.mixer.Sound(str(sounds_path / filename))
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
