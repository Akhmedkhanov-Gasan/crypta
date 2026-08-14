import math

import pygame

from acts.act_two.state import RunePuzzlePhase
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


RUNE_SPRITE_NAMES = (
    "rune_trident",
    "rune_eye",
    "rune_spiral",
)
RUNE_ACTIVATION_EFFECT_DURATION_MS = 900


def _cell_top_left(position):
    return (
        MAP_OFFSET_X + position[0] * TILE_SIZE,
        MAP_OFFSET_Y + position[1] * TILE_SIZE,
    )


def _blit_with_alpha(screen, sprite, position, alpha):
    tinted = sprite.copy()
    tinted.set_alpha(alpha)
    screen.blit(tinted, _cell_top_left(position))


def _draw_rune_effects(
    screen,
    sprite,
    position,
    rune_index,
    current_time,
    intensity,
    particles,
):
    if intensity <= 0:
        return

    left, top = _cell_top_left(position)
    pulse = (math.sin(current_time / 280 + rune_index * 1.7) + 1) / 2
    effect = pygame.Surface((64, 64), pygame.SRCALPHA)
    for radius, alpha in ((21, 5), (16, 9), (12, 13)):
        pygame.draw.circle(
            effect,
            (
                105,
                20,
                16,
                round(alpha * intensity * (0.82 + pulse * 0.18)),
            ),
            (32, 32),
            radius,
        )

    if particles:
        for particle_index in range(3):
            lifetime = (
                current_time / 1050
                + rune_index * 0.23
                + particle_index / 3
                + position[0] * 0.07
                + position[1] * 0.11
            ) % 1
            angle = (
                rune_index * 1.9
                + particle_index * math.tau / 3
                + current_time / 1700
            )
            distance = 15 + lifetime * 7
            particle_x = round(32 + math.cos(angle) * distance)
            particle_y = round(
                32 + math.sin(angle) * distance - lifetime * 4
            )
            particle_alpha = round(
                (1 - lifetime) * 90 * intensity
            )
            particle_color = (
                (126, 33, 23, particle_alpha)
                if particle_index != 1
                else (128, 111, 93, particle_alpha // 2)
            )
            pygame.draw.rect(
                effect,
                particle_color,
                (particle_x, particle_y, 1, 1),
            )
    screen.blit(effect, (left - 16, top - 16))

    outline_alpha = round((24 + pulse * 12) * intensity)
    outline = pygame.mask.from_surface(sprite, 18).to_surface(
        setcolor=(112, 22, 17, outline_alpha),
        unsetcolor=(0, 0, 0, 0),
    )
    for offset_x, offset_y in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ):
        screen.blit(outline, (left + offset_x, top + offset_y))


def _draw_rune_activation_burst(
    screen,
    position,
    rune_index,
    current_time,
    started_at,
):
    if started_at is None:
        return
    elapsed = current_time - started_at
    if elapsed < 0 or elapsed >= RUNE_ACTIVATION_EFFECT_DURATION_MS:
        return

    progress = elapsed / RUNE_ACTIVATION_EFFECT_DURATION_MS
    visibility = (1 - progress) ** 1.35
    left, top = _cell_top_left(position)
    effect = pygame.Surface((96, 96), pygame.SRCALPHA)
    center = (48, 48)

    flash_visibility = max(0.0, 1 - progress * 3.2)
    for radius, alpha in ((24, 25), (17, 42), (10, 75)):
        pygame.draw.circle(
            effect,
            (190, 62, 32, round(alpha * flash_visibility)),
            center,
            radius,
        )

    ring_radius = round(7 + progress * 30)
    pygame.draw.circle(
        effect,
        (231, 145, 76, round(220 * visibility)),
        center,
        ring_radius,
        width=2 if progress < 0.45 else 1,
    )

    for particle_index in range(12):
        angle = (
            particle_index * math.tau / 12
            + rune_index * 0.71
            + progress * 0.45
        )
        distance = 7 + progress * (24 + particle_index % 4 * 3)
        particle_x = round(center[0] + math.cos(angle) * distance)
        particle_y = round(
            center[1]
            + math.sin(angle) * distance
            - progress * (4 + particle_index % 3 * 2)
        )
        color = (
            (238, 163, 87, round(235 * visibility))
            if particle_index % 3 == 0
            else (156, 47, 30, round(205 * visibility))
        )
        pygame.draw.circle(
            effect,
            color,
            (particle_x, particle_y),
            2 if particle_index % 4 == 0 else 1,
        )

    screen.blit(effect, (left - 32, top - 32))


def draw_act_two_rune_room(
    screen,
    room,
    sprites,
    visible_cells,
    current_time,
) -> None:
    if room is None:
        return

    pulse = (math.sin(current_time / 230) + 1) / 2
    for rune_index, (position, sprite_name) in enumerate(
        zip(room.wall_rune_positions, RUNE_SPRITE_NAMES)
    ):
        if position not in visible_cells:
            continue
        activated = rune_index in room.activated_runes
        _draw_rune_effects(
            screen,
            sprites[sprite_name],
            position,
            rune_index,
            current_time,
            0.16 if activated else 0.9,
            not activated,
        )
        alpha = 58 if activated else round(210 + pulse * 45)
        _blit_with_alpha(
            screen,
            sprites[sprite_name],
            position,
            alpha,
        )
        _draw_rune_activation_burst(
            screen,
            position,
            rune_index,
            current_time,
            room.activation_effect_started_at.get(rune_index),
        )

    for rune_index, (position, sprite_name) in enumerate(
        zip(room.floor_rune_positions, RUNE_SPRITE_NAMES)
    ):
        if position not in visible_cells:
            continue
        activated = rune_index in room.activated_runes
        _draw_rune_effects(
            screen,
            sprites[sprite_name],
            position,
            rune_index,
            current_time,
            0.82 if activated else 0.12,
            activated,
        )
        alpha = round(220 + pulse * 35) if activated else 68
        _blit_with_alpha(
            screen,
            sprites[sprite_name],
            position,
            alpha,
        )
        _draw_rune_activation_burst(
            screen,
            position,
            rune_index,
            current_time,
            room.activation_effect_started_at.get(rune_index),
        )

    if room.pedestal_position not in visible_cells:
        return
    sprite_name = (
        "rune_pedestal_reward"
        if room.phase is RunePuzzlePhase.REWARD_AVAILABLE
        else "rune_pedestal"
    )
    screen.blit(
        sprites[sprite_name],
        _cell_top_left(room.pedestal_position),
    )


__all__ = ["draw_act_two_rune_room"]
