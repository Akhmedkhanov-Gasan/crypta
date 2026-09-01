import random
from functools import lru_cache

import pygame

from game.events import GameEventType
from presentation.layout import PROJECT_ROOT


SOUND_PREFIXES = {
    ("sphere", "prepare"): "projectiles_prepare",
    ("sphere", "shot"): "projectiles_exploded",
    ("line", "prepare"): "blackfire_prepare",
    ("line", "shot"): "blackfire_volley",
    ("line", "blast"): "blackfire_exploded",
    ("radial", "prepare"): "blackfire_prepare",
    ("radial", "blast"): "blackfire_exploded",
}

SOUND_VOLUMES = {
    "prepare": 0.65,
    "shot": 0.80,
    "blast": 0.85,
}

FIRE_LOOP_VOLUME = 0.45
PAIN_VOLUME = 0.80
LAUGH_VOLUME = 0.85
LAUGH_COOLDOWN_MS = 700

_burning_channel = None
_burning_sound = None
_burning_active = False
_pain_channel = None
_last_pain_sound = None
_laugh_channel = None
_last_laugh_sound = None
_last_laugh_at = -1


@lru_cache(maxsize=7)
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
    phase_two = floor.oracle_phase_two

    first_phase_fire = (
        state is not None
        and state.caster.health > 0
        and bool(state.ground_fire.cells)
    )
    second_phase_fire = (
        phase_two is not None
        and phase_two.caster.health > 0
        and bool(phase_two.hazards)
        and not phase_two.defeated_pending
    )

    should_play = (
        enabled
        and floor.has_oracle_gate
        and game_state.player.health > 0
        and (
            first_phase_fire
            or second_phase_fire
        )
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

@lru_cache(maxsize=1)
def _load_pain_variants():
    root = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/pain"
    )
    variants = []

    for index in range(4):
        path = root / f"oracle_pain_{index:02d}.mp3"

        try:
            variants.append(pygame.mixer.Sound(str(path)))
        except (OSError, pygame.error):
            continue

    return tuple(variants)


def play_oracle_pain_from_events(events, sounds):
    global _pain_channel, _last_pain_sound

    oracle_was_hit = any(
        event.type is GameEventType.HIT
        and (event.amount or 0) > 0
        and (
            event.target == "Oracle"
            or event.data.get("enemy_type") == "oracle_pillar"
        )
        for event in events
    )

    if not oracle_was_hit:
        return

    if pygame.mixer.get_init() is None:
        _pain_channel = None
        return

    variants = _load_pain_variants()

    if not variants:
        return

    choices = tuple(
        sound
        for sound in variants
        if sound is not _last_pain_sound
    )
    sound = random.choice(choices or variants)

    if _pain_channel is None:
        channel_index = pygame.mixer.get_num_channels()
        pygame.mixer.set_num_channels(channel_index + 1)
        _pain_channel = pygame.mixer.Channel(channel_index)

    if _pain_channel.get_busy():
        _pain_channel.stop()

    _pain_channel.play(
        sound,
        fade_ms=45,
    )
    _pain_channel.set_volume(
        max(
            0.0,
            min(1.0, sounds.master_volume * PAIN_VOLUME),
        )
    )

    _last_pain_sound = sound


@lru_cache(maxsize=1)
def _load_laugh_variants():
    root = (
        PROJECT_ROOT
        / "assets/audio/sounds_act_2/oracle/laugh"
    )
    variants = []

    for index in (1, 2):
        path = root / f"oracle_laughter_{index}.mp3"

        try:
            variants.append(
                pygame.mixer.Sound(str(path))
            )
        except (OSError, pygame.error):
            continue

    return tuple(variants)


def play_oracle_laugh_from_events(events, sounds):
    global _laugh_channel
    global _last_laugh_sound
    global _last_laugh_at

    rejected_hit = any(
        event.type is GameEventType.HIT
        and event.data.get("mode") == "phase_two_immune"
        for event in events
    )

    if not rejected_hit or pygame.mixer.get_init() is None:
        return

    current_time = pygame.time.get_ticks()

    if (
        _last_laugh_at >= 0
        and current_time - _last_laugh_at
        < LAUGH_COOLDOWN_MS
    ):
        return

    variants = _load_laugh_variants()

    if not variants:
        return

    choices = tuple(
        sound
        for sound in variants
        if sound is not _last_laugh_sound
    )
    sound = random.choice(choices or variants)

    if _laugh_channel is None:
        channel_index = pygame.mixer.get_num_channels()
        pygame.mixer.set_num_channels(channel_index + 1)
        _laugh_channel = pygame.mixer.Channel(channel_index)

    if _laugh_channel.get_busy():
        _laugh_channel.stop()

    _laugh_channel.play(
        sound,
        fade_ms=35,
    )
    _laugh_channel.set_volume(
        max(
            0.0,
            min(
                1.0,
                sounds.master_volume * LAUGH_VOLUME,
            ),
        )
    )

    _last_laugh_sound = sound
    _last_laugh_at = current_time
