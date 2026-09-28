import math

import pygame

from acts.act_three.settings import (
    WARLOCK_DEMON_FORM_TRANSFORM_MS,
)
from presentation.layout import ACT_THREE_TILE_SIZE


_DEMON_FORM_FRAME_COUNT = 8
_DEMON_FORM_IDLE_FRAME_MS = 210


def load_warlock_demon_form_assets(
    assets,
    warlock_directory,
    tile_size,
    image_loader,
):
    demon_form_directory = (
        warlock_directory / "demon_form"
    )
    idle_directory = (
        demon_form_directory
        / "idle"
        / "demon_idle_down"
    )
    transform_directory = (
        demon_form_directory / "transform_down"
    )

    for frame_index in range(_DEMON_FORM_FRAME_COUNT):
        source_index = frame_index + 1
        idle_sprite = image_loader(
            idle_directory
            / f"idle_down_{source_index:02d}.png",
            (tile_size, tile_size),
        )

        assets[
            f"player_warlock_demon_idle_{frame_index}"
        ] = idle_sprite
        assets[
            f"player_warlock_demon_walk_{frame_index}"
        ] = idle_sprite
        assets[
            f"player_warlock_demon_transform_{frame_index}"
        ] = image_loader(
            transform_directory
            / f"transform_down_{source_index:02d}.png",
            (tile_size, tile_size),
        )

    assets["player_warlock_demon_attack"] = assets[
        "player_warlock_demon_idle_0"
    ]
    assets["player_warlock_demon_hurt"] = assets[
        "player_warlock_demon_idle_0"
    ]


def _warlock_demon_transition_state(
    player,
    current_time,
):
    target_active = (
        player.warlock_demon_form_target_active
    )
    started_at = player.warlock_demon_form_started_at
    if target_active is None or started_at < 0:
        return None

    elapsed = current_time - started_at
    if (
        elapsed < 0
        or elapsed >= WARLOCK_DEMON_FORM_TRANSFORM_MS
    ):
        return None

    return (
        elapsed / WARLOCK_DEMON_FORM_TRANSFORM_MS,
        target_active,
    )


def warlock_demon_transition_sprite(
    player,
    assets,
    current_time,
):
    transition = _warlock_demon_transition_state(
        player,
        current_time,
    )
    if transition is None:
        return None

    progress, target_active = transition
    frame = min(
        _DEMON_FORM_FRAME_COUNT - 1,
        int(progress * _DEMON_FORM_FRAME_COUNT),
    )
    if not target_active:
        frame = _DEMON_FORM_FRAME_COUNT - 1 - frame

    return assets[
        f"player_warlock_demon_transform_{frame}"
    ]


def warlock_demon_idle_sprite(
    player,
    assets,
    current_time,
):
    idle_started_at = (
        player.warlock_demon_form_started_at
        + WARLOCK_DEMON_FORM_TRANSFORM_MS
    )
    elapsed = max(
        0,
        current_time - idle_started_at,
    )
    frame = (
        elapsed // _DEMON_FORM_IDLE_FRAME_MS
    ) % _DEMON_FORM_FRAME_COUNT
    return assets[
        f"player_warlock_demon_idle_{frame}"
    ]


def draw_warlock_demon_transformation(
    surface,
    player,
    position,
    current_time,
):
    transition = _warlock_demon_transition_state(
        player,
        current_time,
    )
    if transition is None:
        return

    progress, target_active = transition
    intensity = math.sin(math.pi * progress)
    margin = 28
    size = ACT_THREE_TILE_SIZE + margin * 2
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )
    effect_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    primary_color = (
        (205, 69, 255)
        if target_active
        else (111, 69, 163)
    )
    ring_radius = round(9 + progress * 45)
    ring_alpha = round(220 * intensity)

    pygame.draw.circle(
        effect_surface,
        (*primary_color, ring_alpha // 4),
        center,
        ring_radius + 7,
        width=5,
    )
    pygame.draw.circle(
        effect_surface,
        (*primary_color, ring_alpha),
        center,
        ring_radius,
        width=2,
    )

    for particle_index in range(12):
        angle = (
            particle_index * math.tau / 12
            + current_time / 360
        )
        travel = (
            34 * (1 - progress)
            if target_active
            else 34 * progress
        )
        particle_position = (
            center[0] + round(math.cos(angle) * travel),
            center[1] + round(math.sin(angle) * travel),
        )
        particle_radius = 1 + particle_index % 2
        pygame.draw.circle(
            effect_surface,
            (
                primary_color[0],
                primary_color[1],
                primary_color[2],
                round(235 * intensity),
            ),
            particle_position,
            particle_radius,
        )

    core_radius = round(7 + intensity * 14)
    pygame.draw.circle(
        effect_surface,
        (223, 104, 255, round(55 * intensity)),
        center,
        core_radius,
    )
    pygame.draw.circle(
        effect_surface,
        (255, 213, 255, round(190 * intensity)),
        center,
        max(2, core_radius // 3),
        width=2,
    )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )

    flash_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    flash_surface.fill(
        (48, 5, 72, round(34 * intensity))
    )
    surface.blit(flash_surface, (0, 0))
