import math
import random
from functools import lru_cache

import pygame


WARDEN_FOG_COLOR = (9, 11, 12)
WARDEN_FOG_EDGE_COLOR = (86, 91, 82)
WARDEN_RED_COLOR = (65, 13, 19)
WARDEN_FOG_OPACITY = 175
WARDEN_FOG_FRONT_FACTOR = 0.68
WARDEN_FOG_PERIOD_MS = 14500

WARDEN_FIREFLY_COLOR = (183, 195, 72)
WARDEN_FIREFLY_CORE_COLOR = (240, 239, 145)
WARDEN_FIREFLY_COUNT = 12
WARDEN_FIREFLY_PERIOD_MS = 7800
WARDEN_FIREFLY_BRIGHTNESS = 1.0
WARDEN_FIREFLY_SPEED = 1.15


def _unit(seed, salt):
    value = (seed + salt * 374761393) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    value ^= value >> 16
    return value / 4294967295


@lru_cache(maxsize=48)
def _fog_puff(radius, color):
    diameter = radius * 2 + 2
    puff = pygame.Surface(
        (diameter, diameter),
        pygame.SRCALPHA,
    )
    center = (radius + 1, radius + 1)

    for current_radius in range(radius, 0, -1):
        proximity = 1.0 - current_radius / (radius + 1)
        alpha = round(190 * proximity ** 0.85)

        pygame.draw.circle(
            puff,
            (*color, alpha),
            center,
            current_radius,
        )

    return puff


@lru_cache(maxsize=16)
def _fog_cluster(sprite_size, variant):
    width = max(32, round(sprite_size * 0.61))
    height = max(32, round(sprite_size * 0.52))
    cluster = pygame.Surface(
        (width, height),
        pygame.SRCALPHA,
    )
    generator = random.Random(variant * 7919 + 173)
    lobes = []

    for index in range(7):
        radius = max(
            3,
            round(
                min(width, height)
                * generator.uniform(0.16, 0.25)
            ),
        )
        center = (
            round(width * generator.uniform(0.28, 0.72)),
            round(height * generator.uniform(0.28, 0.72)),
        )
        lobes.append((radius, center))

    for radius, center in lobes:
        edge_radius = max(3, round(radius * 1.18))
        edge = _fog_puff(
            edge_radius,
            WARDEN_FOG_EDGE_COLOR,
        ).copy()
        edge.set_alpha(155)
        edge_center = (
            center[0] - round(radius * 0.19),
            center[1] - round(radius * 0.25),
        )

        cluster.blit(
            edge,
            edge.get_rect(center=edge_center),
        )

    for radius, center in lobes:
        core = _fog_puff(
            radius,
            WARDEN_FOG_COLOR,
        ).copy()
        core.set_alpha(205)
        core_center = (
            center[0] + round(radius * 0.16),
            center[1] + round(radius * 0.14),
        )

        cluster.blit(
            core,
            core.get_rect(center=core_center),
        )

    if variant % 3 != 1:
        for index in range(2):
            radius = max(
                3,
                round(min(width, height) * 0.11),
            )
            center = (
                round(width * generator.uniform(0.35, 0.65)),
                round(height * generator.uniform(0.35, 0.65)),
            )
            stain = _fog_puff(
                radius,
                WARDEN_RED_COLOR,
            ).copy()
            stain.set_alpha(105)

            cluster.blit(
                stain,
                stain.get_rect(center=center),
            )

    return pygame.transform.gaussian_blur(
        cluster,
        max(1, round(sprite_size * 0.012)),
    )


@lru_cache(maxsize=8)
def _firefly_texture(radius):
    diameter = radius * 2 + 3
    glow = pygame.Surface((diameter, diameter))
    glow.fill((0, 0, 0))
    center = (diameter // 2, diameter // 2)

    for current_radius in range(radius, 0, -1):
        proximity = 1.0 - current_radius / (radius + 1)
        strength = proximity ** 2 * 0.65
        color = tuple(
            round(channel * strength)
            for channel in WARDEN_FIREFLY_COLOR
        )

        pygame.draw.circle(
            glow,
            color,
            center,
            current_radius,
        )

    pygame.draw.circle(
        glow,
        WARDEN_FIREFLY_CORE_COLOR,
        center,
        1,
    )
    return glow


def _draw_fog(
    surface,
    position,
    sprite_size,
    current_time,
    identity_seed,
    foreground,
):
    if foreground:
        return

    phase = (
        current_time / 6500
        + _unit(identity_seed, 91) * math.tau
    )
    radius = max(8, round(sprite_size * 0.22))
    source = _fog_puff(
        radius,
        (45, 48, 45),
    )
    size = (
        max(1, round(sprite_size * 0.48)),
        max(1, round(sprite_size * 0.14)),
    )
    mist = pygame.transform.smoothscale(source, size)
    mist.set_alpha(28)

    for side in (-1, 1):
        center = (
            position[0]
            + sprite_size * (
                0.5
                + side * 0.20
                + math.sin(phase + side) * 0.025
            ),
            position[1]
            + sprite_size * 0.88
            + math.cos(phase + side) * sprite_size * 0.008,
        )

        surface.blit(
            mist,
            mist.get_rect(
                center=(
                    round(center[0]),
                    round(center[1]),
                )
            ),
        )


def _draw_fireflies(
    surface,
    position,
    sprite_size,
    current_time,
    identity_seed,
    foreground,
    strength=1.0,
):
    current_time = round(current_time * WARDEN_FIREFLY_SPEED)
    center_x = position[0] + sprite_size * 0.5

    for index in range(WARDEN_FIREFLY_COUNT):
        if (index % 3 == 0) != foreground:
            continue

        period = max(
            1,
            WARDEN_FIREFLY_PERIOD_MS + index * 379,
        )
        elapsed = (
            current_time
            + round(_unit(identity_seed, index + 31) * period)
        )
        cycle, cycle_elapsed = divmod(elapsed, period)
        progress = cycle_elapsed / period
        active_fraction = 0.76

        if progress >= active_fraction:
            continue

        life_progress = progress / active_fraction
        brightness = (
            math.sin(math.pi * life_progress) ** 2
            * WARDEN_FIREFLY_BRIGHTNESS
            * strength
        )
        weight = max(
            0,
            min(255, round(brightness * 255)),
        )

        if weight == 0:
            continue

        particle_seed = (
            identity_seed
            + index * 104729
            + cycle * 13007
        )
        side = -1 if index % 2 == 0 else 1
        spread = (
            (0.22 if foreground else 0.37)
            + _unit(particle_seed, 1) * 0.20
        )
        height_level = (
            0.12 + _unit(particle_seed, 2) * 0.78
        )
        drift_phase = (
            current_time / 6500
            + _unit(particle_seed, 3) * math.tau
        )
        center = (
            center_x
            + side * sprite_size * spread
            + math.sin(drift_phase) * sprite_size * 0.022,
            position[1]
            + sprite_size * height_level
            + math.cos(drift_phase * 0.79) * sprite_size * 0.018,
        )
        radius = max(
            3,
            round(sprite_size * 0.03) + index % 2,
        )
        glow = _firefly_texture(radius).copy()
        glow.fill(
            (weight, weight, weight),
            special_flags=pygame.BLEND_RGB_MULT,
        )

        surface.blit(
            glow,
            glow.get_rect(
                center=(
                    round(center[0]),
                    round(center[1]),
                )
            ),
            special_flags=pygame.BLEND_RGB_ADD,
        )


def draw_warden_presence(
    surface,
    position,
    sprite_size,
    current_time,
    identity_seed,
    *,
    foreground=False,
):
    _draw_fog(
        surface,
        position,
        sprite_size,
        current_time,
        identity_seed,
        foreground,
    )
    _draw_fireflies(
        surface,
        position,
        sprite_size,
        current_time,
        identity_seed,
        foreground,
    )
