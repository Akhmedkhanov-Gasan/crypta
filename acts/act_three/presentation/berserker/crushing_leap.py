import math

import pygame
from acts.act_three.abilities.berserker_runes import spin_duration

from acts.act_three.settings import (
    BERSERKER_CRUSHING_LEAP_RANGE,
    BERSERKER_RENDING_SPIN_ANIMATION_MS,
)


CRUSHING_LEAP_FRAME_COUNT = 8


def crushing_leap_frame(elapsed, duration):
    return min(
        CRUSHING_LEAP_FRAME_COUNT - 1,
        max(0, elapsed * CRUSHING_LEAP_FRAME_COUNT // duration),
    )


def rending_spin_world_position(player, current_time, tile_size):
    origin = player.berserker_crushing_leap_origin
    cells = player.berserker_crushing_leap_preview_cells
    started_at = player.berserker_crushing_leap_started_at
    elapsed = current_time - started_at
    if (
        player.subclass != "berserker"
        or player.health <= 0
        or origin is None
        or started_at <= 0
        or not 0 <= elapsed < spin_duration(player)
    ):
        return None

    if not cells:
        return origin[0] * tile_size, origin[1] * tile_size

    travel_duration = (
        BERSERKER_RENDING_SPIN_ANIMATION_MS * 0.8
        * len(cells) / BERSERKER_CRUSHING_LEAP_RANGE
    )
    phase = min(1.0, elapsed / travel_duration)
    eased = phase * phase * (3 - 2 * phase)
    return tuple(
        (a + (b - a) * eased) * tile_size
        for a, b in zip(origin, cells[-1])
    )


def draw_crushing_leap_targeting(
    surface, origin, cells, camera_x, camera_y, current_time, tile_size,
):
    if not cells:
        return

    dx, dy = cells[0][0] - origin[0], cells[0][1] - origin[1]
    magnitude = math.hypot(dx, dy)
    forward_x, forward_y = dx / magnitude, dy / magnitude

    def point(center, across, forward):
        return (
            round(center[0] - forward_y * across + forward_x * forward),
            round(center[1] + forward_x * across + forward_y * forward),
        )

    def center(cell):
        return (
            (cell[0] + 0.5) * tile_size - camera_x,
            (cell[1] + 0.5) * tile_size - camera_y,
        )

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    start, end = center(origin), center(cells[-1])
    width = tile_size * 0.21
    front = tile_size * 0.31
    for side in (-1, 1):
        rail = (
            point(start, side * width * 0.8, tile_size * 0.33),
            point(end, side * width, -tile_size * 0.18),
            point(end, side * width, front * 0.3),
            point(end, 0, front),
        )
        pygame.draw.lines(overlay, (28, 11, 15, 200), False, rail, 5)
        pygame.draw.lines(overlay, (142, 47, 38, 178), False, rail, 2)

    for index, cell in enumerate(cells):
        pulse = 0.5 + 0.5 * math.sin(current_time * 0.008 - index * 1.2)
        middle = center(cell)
        mark = (
            point(middle, -width * 0.46, -front * 0.3),
            point(middle, 0, front * 0.4),
            point(middle, width * 0.46, -front * 0.3),
        )
        pygame.draw.lines(
            overlay, (188, 101, 73, round(100 + 83 * pulse)), False, mark, 2,
        )
    surface.blit(overlay, (0, 0))


def draw_rending_spin_effect(surface, player, camera_x, camera_y, now, size):
    position = rending_spin_world_position(player, now, size)
    if position is None:
        return

    elapsed = now - player.berserker_crushing_leap_started_at
    if elapsed >= BERSERKER_RENDING_SPIN_ANIMATION_MS:
        from acts.act_three.presentation.berserker.rune_effects import draw_devastation

        draw_devastation(surface, position, camera_x, camera_y, elapsed - BERSERKER_RENDING_SPIN_ANIMATION_MS, size)
        return
    from acts.act_three.presentation.berserker.rune_effects import draw_spin_sweep

    draw_spin_sweep(surface, position, camera_x, camera_y,
                    elapsed / BERSERKER_RENDING_SPIN_ANIMATION_MS, size)
