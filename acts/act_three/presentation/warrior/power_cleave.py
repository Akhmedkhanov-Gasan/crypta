import math

import pygame

from acts.act_three.presentation.animation import _ATTACK_FRAME_DURATION_MS
from acts.act_two.abilities import (
    get_warrior_aftershock_cells,
    get_warrior_cleave_cells,
)


_SUBCLASSES = ("berserker", "paladin")
_SWING_DELAY_MS = _ATTACK_FRAME_DURATION_MS // 2
_SWING_LIFETIME_MS = 460
_SHADOW = (37, 22, 29)
_SCAR = (123, 57, 51)
_EDGE = (210, 172, 135)


def _cell_center(cell, camera_x, camera_y, tile_size):
    return (
        (cell[0] + 0.5) * tile_size - camera_x,
        (cell[1] + 0.5) * tile_size - camera_y,
    )


def _point(center, direction, across, forward):
    dx, dy = direction
    return (
        round(center[0] - dy * across + dx * forward),
        round(center[1] + dx * across + dy * forward),
    )


def _draw_scars(overlay, cells, direction, camera_x, camera_y, size, alpha):
    for cell in cells:
        center = _cell_center(cell, camera_x, camera_y, size)
        points = [
            _point(center, direction, across * size, forward * size)
            for across, forward in (
                (-0.28, -0.23), (-0.09, -0.08), (-0.13, 0.04),
                (0.09, 0.11), (0.24, 0.28),
            )
        ]
        pygame.draw.lines(overlay, (*_SHADOW, alpha), False, points, 4)
        pygame.draw.lines(overlay, (*_SCAR, alpha), False, points)
        pygame.draw.line(
            overlay, (*_SCAR, alpha), points[2],
            _point(center, direction, -0.27 * size, 0.21 * size),
        )


def _draw_sweep(
    overlay, cells, direction, camera_x, camera_y, size, opacity,
    progress=None,
):
    ordered_cells = sorted(
        cells, key=lambda cell: cell[1] * direction[0] - cell[0] * direction[1]
    )
    first = ordered_cells[0]
    dx, dy = direction
    offsets = [
        (cell[1] - first[1]) * dx - (cell[0] - first[0]) * dy
        for cell in ordered_cells
    ]
    span = offsets[-1] + 1
    preview = progress is None

    for cell, offset in zip(ordered_cells, offsets):
        center = _cell_center(cell, camera_x, camera_y, size)
        for layer in range(3):
            half_width = size * (0.49 - layer * 0.045)
            depth = size * (0.43 - layer * 0.075)
            shape = [
                _point(center, direction, across * half_width, forward * depth)
                for across, forward in (
                    (-1, -0.65), (-0.62, -1), (0.68, -1),
                    (1, -0.6), (1, 0.5), (0.55, 0.92),
                    (-0.64, 1), (-1, 0.54),
                )
            ]
            color = _SHADOW if layer < 2 else _SCAR
            pygame.draw.polygon(
                overlay, (*color, round((37 + layer * 11) * opacity)), shape
            )

        for index in range(16):
            start = (offset + index / 16) / span
            end = (offset + (index + 1) / 16) / span
            if not preview:
                front = progress * 1.75
                trail = front - (start + end) * 0.5
                if not 0 <= trail < 0.85:
                    continue
                intensity = opacity * (1 - trail / 0.85)
            else:
                intensity = opacity * (0.55 + 0.45 * math.sin(math.pi * start))

            points = [
                _point(
                    center,
                    direction,
                    (t * span - offset - 0.5) * size * 0.96,
                    size * (0.20 - 0.35 * (2 * t - 1) ** 2),
                )
                for t in (start, end)
            ]
            for color, width, alpha in (
                (_SHADOW, 0.14, 155),
                (_SCAR, 0.065, 177),
                (_EDGE, 0.018, 125 if preview else 238),
            ):
                pygame.draw.line(
                    overlay, (*color, round(alpha * intensity)),
                    *points, max(1, round(size * width)),
                )


def draw_power_cleave_targeting(
    surface, game_state, camera_x, camera_y, current_time, tile_size,
):
    player = game_state.player
    direction = player.act_two.selected_ability_direction
    if (
        player.player_class != "warrior"
        or player.subclass not in _SUBCLASSES
        or not player.directional_ability_aiming
        or direction is None
    ):
        return

    cells = get_warrior_cleave_cells(game_state.floor, *direction)
    if not cells:
        return

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    opacity = 0.78 + 0.10 * math.sin(current_time / 280)
    _draw_sweep(overlay, cells, direction, camera_x, camera_y, tile_size, opacity)
    if player.selected_rune_id == "rune_of_aftershock":
        _draw_scars(
            overlay, get_warrior_aftershock_cells(game_state.floor, *direction),
            direction, camera_x, camera_y, tile_size, round(140 * opacity),
        )
    surface.blit(overlay, (0, 0))


def draw_power_cleave_effect(
    surface, player, camera_x, camera_y, current_time, tile_size,
):
    state = player.act_two
    started_at = state.ability_effect_started_at
    elapsed = current_time - started_at
    if (
        player.subclass not in _SUBCLASSES
        or state.ability_effect_kind != "power_cleave"
        or not state.ability_effect_cells
        or started_at <= 0
        or not 0 <= elapsed < _SWING_DELAY_MS + _SWING_LIFETIME_MS
    ):
        return False

    progress = (elapsed - _SWING_DELAY_MS) / _SWING_LIFETIME_MS
    if progress >= 0:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        opacity = (1 - progress) ** 1.2
        direction = state.ability_effect_direction
        _draw_sweep(
            overlay, state.ability_effect_cells, direction,
            camera_x, camera_y, tile_size, opacity, progress,
        )
        if progress > 0.22:
            aftershock = (progress - 0.22) / 0.78
            _draw_scars(
                overlay, state.ability_effect_aftershock_positions, direction,
                camera_x, camera_y, tile_size,
                round(194 * math.sin(math.pi * aftershock) * (1 - aftershock)),
            )
        surface.blit(overlay, (0, 0))

    return started_at == player.attack_animation_started_at
