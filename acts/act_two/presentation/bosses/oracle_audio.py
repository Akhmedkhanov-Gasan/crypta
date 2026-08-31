import random
from functools import lru_cache

import pygame

from presentation.layout import PROJECT_ROOT


SOUND_PREFIXES = {
    ("sphere", "prepare"): "projectiles_prepare",
    ("sphere", "shot"): "projectiles_exploded",
    ("line", "prepare"): "blackfire_prepare",
    ("line", "shot"): "blackfire_volley",
    ("line", "blast"): "blackfire_exploded",
}

SOUND_VOLUMES = {
    "prepare": 0.65,
    "shot": 0.80,
    "blast": 0.85,
}

FIRE_LOOP_VOLUME = 0.45

_burning_channel = None
_burning_sound = None
_burning_active = False


@lru_cache(maxsize=5)
def _load_variants(prefix):
    root = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/attack"
    )
    variants = []

    for index in (1, 2):
        path = root / f"{prefix}_{index}.mp3"

        try:
            variants.append(pygame.mixer.Sound(str(path)))
        except (OSError, pygame.error):
            continue

    return tuple(variants)


def play_oracle_attack_sound(sounds, kind, stage):
    if pygame.mixer.get_init() is None:
        return

    volume = max(
        0.0,
        min(1.0, sounds.master_volume * SOUND_VOLUMES[stage]),
    )

    if volume <= 0:
        return

    variants = _load_variants(SOUND_PREFIXES[(kind, stage)])

    if not variants:
        return

    channel = random.choice(variants).play()

    if channel is not None:
        channel.set_volume(volume)


def stop_oracle_fire_audio():
    global _burning_channel, _burning_active

    if pygame.mixer.get_init() is None:
        _burning_channel = None
        _burning_active = False
        return

    if (
        _burning_active
        and _burning_channel is not None
        and _burning_channel.get_sound() is _burning_sound
    ):
        _burning_channel.fadeout(120)

    _burning_active = False


def update_oracle_fire_audio(game_state, sounds, enabled=True):
    global _burning_channel, _burning_sound, _burning_active

    floor = game_state.floor
    state = floor.oracle_combat

    should_play = (
        enabled
        and floor.has_oracle_gate
        and game_state.player.health > 0
        and state is not None
        and state.caster.health > 0
        and state.phase in ("embers", "blast")
    )

    if not should_play or pygame.mixer.get_init() is None:
        stop_oracle_fire_audio()
        return

    variants = sounds.sounds.get("fire_bomb_burning")
    volume = max(
        0.0,
        min(1.0, sounds.master_volume * FIRE_LOOP_VOLUME),
    )

    if not variants or volume <= 0:
        stop_oracle_fire_audio()
        return

    sound = variants[0]

    if _burning_channel is None:
        channel_index = pygame.mixer.get_num_channels()
        pygame.mixer.set_num_channels(channel_index + 1)
        _burning_channel = pygame.mixer.Channel(channel_index)

    if (
        _burning_channel.get_busy()
        and _burning_channel.get_sound() is not sound
    ):
        _burning_active = False
        return

    _burning_sound = sound

    if not _burning_active or not _burning_channel.get_busy():
        _burning_channel.play(
            sound,
            loops=-1,
            fade_ms=180,
        )
        _burning_active = True

    _burning_channel.set_volume(volume)
