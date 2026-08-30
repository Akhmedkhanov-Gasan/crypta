import random
from collections.abc import Iterable
from pathlib import Path

import pygame

from acts.act_two.settings import FIRE_BOMB_FLIGHT_MS
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


ACT_TWO_ENEMY_SOUND_FILES = {
    "goblin_attack": ("goblin_attack_1.mp3", "goblin_attack_2.mp3"),
    "goblin_hurt": ("goblin_hurt_1.mp3", "goblin_hurt_2.mp3"),
    "goblin_death": ("goblin_death_1.mp3", "goblin_death_2.mp3"),
    "brute_prepare": ("brute_prepare_1.mp3", "brute_prepare_2.mp3"),
    "brute_attack": ("brute_attack_1.mp3", "brute_attack_2.mp3"),
    "brute_hurt": ("brute_hurt_1.mp3", "brute_hurt_2.mp3"),
    "brute_death": ("brute_death_1.mp3", "brute_death_2.mp3"),
    "archer_prepare": ("archer_prepare_1.mp3", "archer_prepare_2.mp3"),
    "archer_attack": ("archer_attack_1.mp3", "archer_attack_2.mp3"),
    "archer_hurt": ("archer_hurt_1.mp3", "archer_hurt_2.mp3"),
    "archer_death": ("archer_death_1.mp3", "archer_death_2.mp3"),
    "sentinel_prepare": (
        "sentinel_prepare_1.mp3",
        "sentinel_prepare_2.mp3",
    ),
    "sentinel_attack": (
        "sentinel_attack_1.mp3",
        "sentinel_attack_2.mp3",
    ),
    "sentinel_block": ("sentinel_block_1.mp3", "sentinel_block_2.mp3"),
    "sentinel_hurt": ("sentinel_hurt_1.mp3", "sentinel_hurt_2.mp3"),
    "sentinel_death": ("sentinel_death_1.mp3", "sentinel_death_2.mp3"),
    "priest_prepare": ("priest_prepare_1.mp3", "priest_prepare_2.mp3"),
    "priest_attack": ("priest_attack_1.mp3", "priest_attack_2.mp3"),
    "priest_heal_prepare": (
        "priest_heal_prepare_1.mp3",
        "priest_heal_prepare_2.mp3",
    ),
    "priest_heal": ("priest_heal_1.mp3", "priest_heal_2.mp3"),
    "priest_hurt": ("priest_hurt_1.mp3", "priest_hurt_2.mp3"),
    "priest_death": ("priest_death_1.mp3", "priest_death_2.mp3"),
    "mimic_attack": (
        "mimic_attack_1.mp3",
        "mimic_attack_2.mp3",
    ),
    "mimic_hurt": (
        "mimic_hurt_1.mp3",
        "mimic_hurt_2.mp3",
    ),
    "mimic_death": (
        "mimic_death_1.mp3",
        "mimic_death_2.mp3",
    ),
}


ACT_TWO_PLAYER_SOUND_FILES = {
    "player_heal": ("player_heal_1.mp3", "player_heal_2.mp3"),
}


ACT_TWO_LEVEL_UP_SOUND_FILES = {
    "level_up": ("lvl_up_1.mp3", "lvl_up_2.mp3"),
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
    "treasury_trap_activate": (
        "treasury_trap_activate_1.mp3",
        "treasury_trap_activate_2.mp3",
    ),
    "portcullis_lock": ("portcullis_lock_1.mp3", "portcullis_lock_2.mp3"),
    "portcullis_unlock": (
        "portcullis_unlock_1.mp3",
        "portcullis_unlock_2.mp3",
    ),
    "room_reward": ("room_reward_1.mp3", "room_reward_2.mp3"),
    "secret_wall_break": (
        "secret_wall_break_1.mp3",
        "secret_wall_break_2.mp3",
    ),
}


ACT_TWO_TRADER_SOUND_FILES = {
    "trader_meeting": (
        "trader_meeting_1.mp3",
        "trader_meeting_2.mp3",
    ),
    "trader_normal": (
        "trader_normal_1.mp3",
        "trader_normal_2.mp3",
    ),
}


ACT_TWO_FIRE_BOMB_SOUND_FILES = {
    "fire_bomb_break": (
        "fire_bomb_break_1.mp3",
        "fire_bomb_break_2.mp3",
    ),
    "fire_bomb_ignite": (
        "fire_bomb_ignite_1.mp3",
        "fire_bomb_ignite_2.mp3",
    ),
    "fire_bomb_burning": ("fire_bomb_burning_loop.mp3",),
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
    "player_heal": 0.82,
    "level_up": 0.72,
    "goblin_attack": 0.68,
    "goblin_hurt": 0.66,
    "goblin_death": 0.70,
    "mimic_attack": 0.78,
    "mimic_hurt": 0.70,
    "mimic_death": 0.80,
    "brute_prepare": 0.68,
    "brute_attack": 0.82,
    "brute_hurt": 0.72,
    "brute_death": 0.82,
    "archer_prepare": 0.60,
    "archer_attack": 0.72,
    "archer_hurt": 0.64,
    "archer_death": 0.70,
    "sentinel_prepare": 0.66,
    "sentinel_attack": 0.80,
    "sentinel_block": 0.86,
    "sentinel_hurt": 0.72,
    "sentinel_death": 0.82,
    "priest_prepare": 0.64,
    "priest_attack": 0.74,
    "priest_heal_prepare": 0.64,
    "priest_heal": 0.76,
    "priest_hurt": 0.66,
    "priest_death": 0.74,
    "footstep": 0.48,
    "rune_activate": 0.68,
    "chest_open": 0.62,
    "chest_break": 0.74,
    "gold_pickup": 0.72,
    "item_pickup": 0.72,
    "key_pickup": 1.00,
    "treasury_trap_activate": 0.82,
    "portcullis_lock": 0.78,
    "portcullis_unlock": 0.74,
    "room_reward": 0.84,
    "secret_wall_break": 0.82,
    "fire_bomb_break": 0.68,
    "fire_bomb_ignite": 0.50,
    "fire_bomb_burning": 0.22,
    "trader_meeting": 0.82,
    "trader_normal": 0.82,
}


_LEVEL_UP_CHANNEL = 2

_FIRE_BOMB_IGNITE_DELAY_MS = 90
_FIRE_BOMB_LOOP_DELAY_MS = 220
_FIRE_BOMB_BREAK_CHANNEL = 5
_FIRE_BOMB_IGNITE_CHANNEL = 6
_FIRE_BOMB_LOOP_CHANNEL = 7


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
        self._fire_bomb_floor_identity = None
        self._fire_bomb_breaks_played = set()
        self._fire_bomb_ignitions_played = set()
        self._fire_bomb_loop_active = False

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

        for sound_key, filenames in ACT_TWO_ENEMY_SOUND_FILES.items():
            enemy_path = sounds_path / sound_key.split("_", 1)[0]
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(enemy_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        player_path = sounds_path / "player"
        for sound_key, filenames in ACT_TWO_PLAYER_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(player_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        level_up_path = sounds_path / "lvl_up"
        for sound_key, filenames in ACT_TWO_LEVEL_UP_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(level_up_path / filename))
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
        trader_path = sounds_path / "trader"

        for (
            sound_key,
            filenames,
        ) in ACT_TWO_TRADER_SOUND_FILES.items():
            variants = []

            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(
                            str(
                                trader_path
                                / filename
                            )
                        )
                    )
                except (
                    FileNotFoundError,
                    pygame.error,
                ):
                    continue

            if variants:
                loaded_sounds[
                    sound_key
                ] = variants
        fire_bomb_path = sounds_path / "items" / "fire_bomb"
        for sound_key, filenames in ACT_TWO_FIRE_BOMB_SOUND_FILES.items():
            variants = []
            for filename in filenames:
                try:
                    variants.append(
                        pygame.mixer.Sound(str(fire_bomb_path / filename))
                    )
                except (FileNotFoundError, pygame.error):
                    continue
            if variants:
                loaded_sounds[sound_key] = variants

        return cls(loaded_sounds)

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def play_ui_sound(self, sound_key):
        self._play(sound_key)

    @staticmethod
    def _fire_channel(channel_index: int):
        if pygame.mixer.get_init() is None:
            return None
        if pygame.mixer.get_num_channels() <= channel_index:
            pygame.mixer.set_num_channels(channel_index + 1)
        return pygame.mixer.Channel(channel_index)

    def _play_fire_sound(
        self,
        sound_key: str,
        channel_index: int,
        distance_gain: float,
        loops: int = 0,
        fade_ms: int = 0,
    ) -> bool:
        variants = self.sounds.get(sound_key)
        channel = self._fire_channel(channel_index)
        if not variants or channel is None:
            return False
        channel.play(
            random.choice(variants),
            loops=loops,
            fade_ms=fade_ms,
        )
        channel.set_volume(
            min(
                1.0,
                ACT_TWO_SOUND_VOLUMES[sound_key]
                * self.master_volume
                * max(0.0, min(1.0, distance_gain)),
            )
        )
        return True

    def _stop_fire_bomb_audio(self) -> None:
        for channel_index in (
            _FIRE_BOMB_BREAK_CHANNEL,
            _FIRE_BOMB_IGNITE_CHANNEL,
        ):
            channel = self._fire_channel(channel_index)
            if channel is not None:
                channel.fadeout(120)
        loop_channel = self._fire_channel(_FIRE_BOMB_LOOP_CHANNEL)
        if loop_channel is not None:
            loop_channel.fadeout(280)
        self._fire_bomb_loop_active = False

    def update_fire_bomb_audio(self, floor, current_time: int) -> None:
        floor_identity = id(floor) if floor is not None else None
        if floor_identity != self._fire_bomb_floor_identity:
            self._stop_fire_bomb_audio()
            self._fire_bomb_floor_identity = floor_identity
            self._fire_bomb_breaks_played.clear()
            self._fire_bomb_ignitions_played.clear()

        zones = tuple(getattr(floor, "fire_zones", ()))
        if not zones:
            if (
                self._fire_bomb_loop_active
                or self._fire_bomb_breaks_played
                or self._fire_bomb_ignitions_played
            ):
                self._stop_fire_bomb_audio()
            self._fire_bomb_breaks_played.clear()
            self._fire_bomb_ignitions_played.clear()
            return

        player_position = (
            (floor.player_column, floor.player_row)
            if floor is not None
            else None
        )
        burning_distance_gain = 0.0
        for zone in zones:
            elapsed = current_time - zone.created_at
            zone_key = (zone.created_at, zone.origin, zone.center)
            distance_gain = _act_two_distance_gain(
                zone.center,
                player_position,
            )
            if (
                elapsed >= FIRE_BOMB_FLIGHT_MS
                and zone_key not in self._fire_bomb_breaks_played
            ):
                self._fire_bomb_breaks_played.add(zone_key)
                self._play_fire_sound(
                    "fire_bomb_break",
                    _FIRE_BOMB_BREAK_CHANNEL,
                    distance_gain,
                )
            if (
                elapsed
                >= FIRE_BOMB_FLIGHT_MS + _FIRE_BOMB_IGNITE_DELAY_MS
                and zone_key not in self._fire_bomb_ignitions_played
            ):
                self._fire_bomb_ignitions_played.add(zone_key)
                self._play_fire_sound(
                    "fire_bomb_ignite",
                    _FIRE_BOMB_IGNITE_CHANNEL,
                    distance_gain,
                )
            if elapsed >= FIRE_BOMB_FLIGHT_MS + _FIRE_BOMB_LOOP_DELAY_MS:
                burning_distance_gain = max(
                    burning_distance_gain,
                    distance_gain,
                )

        if burning_distance_gain <= 0:
            return
        loop_channel = self._fire_channel(_FIRE_BOMB_LOOP_CHANNEL)
        if not self._fire_bomb_loop_active:
            self._fire_bomb_loop_active = self._play_fire_sound(
                "fire_bomb_burning",
                _FIRE_BOMB_LOOP_CHANNEL,
                burning_distance_gain,
                loops=-1,
                fade_ms=180,
            )
        elif loop_channel is not None:
            loop_channel.set_volume(
                min(
                    1.0,
                    ACT_TWO_SOUND_VOLUMES["fire_bomb_burning"]
                    * self.master_volume
                    * burning_distance_gain,
                )
            )

    def _play_level_up(self) -> None:
        variants = self.sounds.get("level_up")
        if not variants or pygame.mixer.get_init() is None:
            return

        if pygame.mixer.get_num_channels() <= _LEVEL_UP_CHANNEL:
            pygame.mixer.set_num_channels(
                _LEVEL_UP_CHANNEL + 1
            )

        sound = random.choice(variants)
        channel = pygame.mixer.Channel(_LEVEL_UP_CHANNEL)

        channel.stop()
        channel.play(sound)
        channel.set_volume(
            min(
                1.0,
                ACT_TWO_SOUND_VOLUMES["level_up"]
                * self.master_volume,
            )
        )


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
        floor=None,
    ) -> None:
        events = tuple(events)
        hero_died = any(
            event.type is GameEventType.DEATH and event.actor == "hero"
            for event in events
        )
        if hero_died:
            self._stop_effect_channels()
            death_sound_key = {
                "warrior": "warrior_death",
                "rogue": "rogue_death",
                "mage": "mage_death",
            }.get(player_class)
            if death_sound_key is not None:
                self._play(death_sound_key, volume_multiplier=1.12)
            return

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

        if any(
            event.type is GameEventType.HEAL
            and event.actor == "hero"
            and event.target == "hero"
            and event.data.get("kind") in ("potion", "healing_scroll")
            for event in events
        ):
            self._play("player_heal")

        if any(
                event.type is GameEventType.LEVEL_UP
                and event.actor == "hero"
                for event in events
        ):
            self._play_level_up()

        if any(
            event.type is GameEventType.HIT
            and event.actor == "hero"
            and event.data.get("kind") == "scroll_of_arcane_impulse"
            for event in events
        ):
            self._play("mage_hit")

        self._play_enemy_events(events, floor)

        environment_sound_gains = {}
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
                if event.data.get("kind") in (
                    "gold",
                    "gold_pile",
                ):
                    sound_key = "gold_pickup"
                elif event.data.get("kind") == "key":
                    sound_key = "key_pickup"
                elif event.data.get("kind") in (
                        "potion",
                        "guild_seal",
                    ):
                    sound_key = "item_pickup"
                elif event.data.get("kind") in (
                    "fire_bomb",
                    "scroll_of_stoneflesh",
                    "scroll_of_binding",
                    "healing_scroll",
                    "scroll_of_arcane_impulse",
                ):
                    sound_key = "item_pickup"
            elif event.type is GameEventType.ENVIRONMENT:
                candidate_key = event.data.get("kind")
                if candidate_key in ACT_TWO_ENVIRONMENT_SOUND_FILES:
                    sound_key = candidate_key
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
                layered_sound_keys = tuple(
                    sound_key
                    for sound_key in (class_attack_sound, "chest_break")
                    if sound_key is not None
                )
                source_position = (
                    event.positions[0] if event.positions else event.origin
                )
                distance_gain = _act_two_distance_gain(
                    source_position,
                    (
                        (floor.player_column, floor.player_row)
                        if floor is not None
                        else None
                    ),
                )
                for layered_sound_key in layered_sound_keys:
                    environment_sound_gains[layered_sound_key] = max(
                        distance_gain,
                        environment_sound_gains.get(layered_sound_key, 0.0),
                    )
                continue
            elif (
                event.type is GameEventType.ATTACK
                and event.actor == "hero"
                and event.data.get("kind") == "secret_wall"
            ):
                class_attack_sound = {
                    "warrior": "warrior_hit",
                    "rogue": "rogue_hit",
                    "mage": "mage_hit",
                }.get(player_class)
                layered_sound_keys = tuple(
                    key
                    for key in (class_attack_sound, "secret_wall_break")
                    if key is not None
                )
                source_position = (
                    event.positions[0] if event.positions else event.origin
                )
                distance_gain = _act_two_distance_gain(
                    source_position,
                    (
                        (floor.player_column, floor.player_row)
                        if floor is not None
                        else None
                    ),
                )
                for layered_sound_key in layered_sound_keys:
                    environment_sound_gains[layered_sound_key] = max(
                        distance_gain,
                        environment_sound_gains.get(layered_sound_key, 0.0),
                    )
                continue

            if sound_key is not None:
                source_position = (
                    event.positions[0]
                    if event.positions
                    else event.destination or event.origin
                )
                distance_gain = _act_two_distance_gain(
                    source_position,
                    (
                        (floor.player_column, floor.player_row)
                        if floor is not None
                        else None
                    ),
                )
                environment_sound_gains[sound_key] = max(
                    distance_gain,
                    environment_sound_gains.get(sound_key, 0.0),
                )

        for sound_key, distance_gain in environment_sound_gains.items():
            if distance_gain > 0:
                self._play(sound_key, distance_gain=distance_gain)

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

    @staticmethod
    def _stop_effect_channels() -> None:
        if pygame.mixer.get_init() is None:
            return
        for channel_index in range(2, pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(channel_index).stop()

    def _play_enemy_events(self, events, floor) -> None:
        if any(
            event.type is GameEventType.ENVIRONMENT
            and event.data.get("kind") == "treasury_trap_activate"
            for event in events
        ):
            return
        enemies = tuple(getattr(floor, "enemies", ()))
        enemies_by_name = {enemy.name: enemy for enemy in enemies}
        player_position = None
        if floor is not None:
            player_position = (floor.player_column, floor.player_row)

        defeated_enemies = {
            event.actor
            for event in events
            if event.type is GameEventType.DEATH and event.actor != "hero"
        }
        candidates = []

        for event_index, event in enumerate(events):
            enemy = enemies_by_name.get(event.actor)
            if enemy is None and event.target is not None:
                enemy = enemies_by_name.get(event.target)
            enemy_type = event.data.get("enemy_type")
            if enemy_type is None and enemy is not None:
                enemy_type = enemy.type
            if enemy_type not in (
                "goblin",
                "mimic",
                "brute",
                "archer",
                "sentinel",
                "priest",
                "priest_ghost",
            ):
                continue

            audio_enemy_type = (
                "priest"
                if enemy_type == "priest_ghost"
                else enemy_type
            )

            sound_key = None
            priority = 0
            if event.type is GameEventType.PREPARE_ATTACK:
                candidate_key = f"{audio_enemy_type}_prepare"
                if candidate_key in ACT_TWO_ENEMY_SOUND_FILES:
                    sound_key = candidate_key
                    priority = 1
            elif event.type is GameEventType.PREPARE_HEAL:
                sound_key = "priest_heal_prepare"
                priority = 2
            elif event.type is GameEventType.ATTACK and event.actor != "hero":
                sound_key = f"{audio_enemy_type}_attack"
                priority = 3
            elif (
                event.type is GameEventType.HEAL
                and event.actor != "hero"
                and enemy_type == "priest"
            ):
                sound_key = "priest_heal"
                priority = 4
            elif (
                event.type is GameEventType.HIT
                and (
                    event.actor in ("hero", "familiar")
                    or event.data.get("kind") == "fire_bomb"
                )
                and event.target not in (None, "hero", "familiar")
            ):
                if event.data.get("blocked", False) and enemy_type == "sentinel":
                    sound_key = "sentinel_block"
                    priority = 5
                elif event.target not in defeated_enemies:
                    sound_key = f"{audio_enemy_type}_hurt"
                    priority = 3
                elif event.type is GameEventType.DEATH and event.actor != "hero":
                    sound_key = f"{audio_enemy_type}_death"
                    priority = 5

            if sound_key is None:
                continue
            source_position = event.origin or event.destination
            if source_position is None and enemy is not None:
                source_position = (enemy.column, enemy.row)
            distance_gain = _act_two_distance_gain(
                source_position,
                player_position,
            )
            if distance_gain <= 0:
                continue
            candidates.append(
                (priority, distance_gain, event_index, sound_key)
            )

        nearest_by_sound = {}
        for candidate in candidates:
            sound_key = candidate[3]
            previous = nearest_by_sound.get(sound_key)
            if previous is None or candidate[:2] > previous[:2]:
                nearest_by_sound[sound_key] = candidate

        selected = sorted(
            nearest_by_sound.values(),
            key=lambda candidate: (-candidate[0], -candidate[1], candidate[2]),
        )[:3]
        for _priority, distance_gain, _event_index, sound_key in selected:
            self._play(sound_key, distance_gain=distance_gain)


def _act_two_distance_gain(source_position, player_position) -> float:
    if source_position is None or player_position is None:
        return 1.0
    distance = max(
        abs(source_position[0] - player_position[0]),
        abs(source_position[1] - player_position[1]),
    )
    if distance <= 1:
        return 1.0
    if distance > 8:
        return 0.0
    return max(0.10, 1.0 - (distance - 1) * 0.13)


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
