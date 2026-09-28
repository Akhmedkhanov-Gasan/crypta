import math

import pygame

from acts.act_three.settings import (
    MAGE_ARCANE_BURST_EFFECT_MS,
)
from acts.act_three.presentation.view import _view_position
from logic import get_mage_arcane_burst_cells


def _effect_colors(effect_kind):
    if effect_kind == "concentration_release":
        return (
            (181, 78, 255),
            (244, 203, 255),
        )
    if effect_kind == "fracture":
        return (
            (46, 188, 255),
            (194, 245, 255),
        )
    return (
        (73, 118, 255),
        (205, 229, 255),
    )


def _cell_center(
    position,
    camera_x,
    camera_y,
    tile_size,
):
    left, top = _view_position(
        position[0],
        position[1],
        camera_x,
        camera_y,
    )
    return (
        left + tile_size // 2,
        top + tile_size // 2,
    )


def draw_act_three_arcane_burst_targeting(
    surface,
    game_state,
    camera_x,
    camera_y,
    tile_size,
    current_time,
):
    player = game_state.player
    state = player.act_three.mage_arcane_burst
    target = state.preview_target
    if (
        player.player_class != "mage"
        or not player.directional_ability_aiming
        or target is None
    ):
        return

    cells = get_mage_arcane_burst_cells(
        game_state.floor,
        target,
        player.selected_rune_id,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 115)
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    for cell in cells:
        left, top = _view_position(
            cell[0],
            cell[1],
            camera_x,
            camera_y,
        )
        inset = 7 if cell == target else 11
        rectangle = pygame.Rect(
            left + inset,
            top + inset,
            tile_size - inset * 2,
            tile_size - inset * 2,
        )
        color = (
            134,
            87,
            255,
            round(65 + pulse * 45),
        )
        pygame.draw.rect(
            overlay,
            color,
            rectangle,
            width=2,
            border_radius=7,
        )

    target_center = _cell_center(
        target,
        camera_x,
        camera_y,
        tile_size,
    )
    pygame.draw.circle(
        overlay,
        (219, 184, 255, round(155 + pulse * 70)),
        target_center,
        round(10 + pulse * 3),
        width=2,
    )
    surface.blit(overlay, (0, 0))


def draw_act_three_arcane_burst_effect(
    surface,
    game_state,
    player_position,
    camera_x,
    camera_y,
    tile_size,
    current_time,
):
    player = game_state.player
    state = player.act_three.mage_arcane_burst
    started_at = state.ability_effect_started_at
    target = state.ability_effect_target
    if (
        player.player_class != "mage"
        or started_at <= 0
        or target is None
    ):
        return

    elapsed = current_time - started_at
    if not 0 <= elapsed < MAGE_ARCANE_BURST_EFFECT_MS:
        return

    progress = elapsed / MAGE_ARCANE_BURST_EFFECT_MS
    primary, highlight = _effect_colors(
        state.ability_effect_kind
    )
    origin = (
        player_position[0] + tile_size // 2,
        player_position[1] + tile_size // 2 - 8,
    )
    target_center = _cell_center(
        target,
        camera_x,
        camera_y,
        tile_size,
    )
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    charge_progress = min(1.0, progress / 0.22)
    charge_visibility = max(
        0.0,
        1.0 - max(0.0, progress - 0.18) / 0.20,
    )
    for ring_index in range(3):
        radius = round(
            20
            - charge_progress * 13
            + ring_index * 4
        )
        pygame.draw.circle(
            overlay,
            (
                primary[0],
                primary[1],
                primary[2],
                round(
                    (145 - ring_index * 28)
                    * charge_visibility
                ),
            ),
            origin,
            max(2, radius),
            width=2,
        )

    travel = max(
        0.0,
        min(1.0, (progress - 0.12) / 0.31),
    )
    if travel > 0:
        eased_travel = 1 - (1 - travel) ** 3
        head = (
            round(
                origin[0]
                + (target_center[0] - origin[0])
                * eased_travel
            ),
            round(
                origin[1]
                + (target_center[1] - origin[1])
                * eased_travel
            ),
        )
        trail_progress = max(0.0, eased_travel - 0.24)
        trail = (
            round(
                origin[0]
                + (target_center[0] - origin[0])
                * trail_progress
            ),
            round(
                origin[1]
                + (target_center[1] - origin[1])
                * trail_progress
            ),
        )
        pygame.draw.line(
            overlay,
            (*primary, 85),
            trail,
            head,
            width=13,
        )
        pygame.draw.line(
            overlay,
            (*primary, 220),
            trail,
            head,
            width=6,
        )
        pygame.draw.line(
            overlay,
            (*highlight, 255),
            trail,
            head,
            width=2,
        )
        pygame.draw.circle(
            overlay,
            (*highlight, 255),
            head,
            5,
        )

    impact_progress = max(
        0.0,
        min(1.0, (progress - 0.38) / 0.62),
    )
    if impact_progress > 0:
        visibility = 1.0 - impact_progress
        radius = round(
            7 + impact_progress * tile_size * 0.95
        )
        pygame.draw.circle(
            overlay,
            (*primary, round(225 * visibility)),
            target_center,
            radius,
            width=4,
        )
        pygame.draw.circle(
            overlay,
            (*highlight, round(245 * visibility)),
            target_center,
            max(3, round(radius * 0.55)),
            width=2,
        )

        for cell in state.ability_effect_cells:
            if cell == target:
                continue
            cell_center = _cell_center(
                cell,
                camera_x,
                camera_y,
                tile_size,
            )
            pygame.draw.line(
                overlay,
                (*primary, round(175 * visibility)),
                target_center,
                cell_center,
                width=8,
            )
            pygame.draw.line(
                overlay,
                (*highlight, round(235 * visibility)),
                target_center,
                cell_center,
                width=2,
            )

        for spark_index in range(14):
            angle = spark_index * math.tau / 14
            distance = round(
                tile_size
                * (0.18 + impact_progress * 0.85)
            )
            spark = (
                target_center[0]
                + round(math.cos(angle) * distance),
                target_center[1]
                + round(math.sin(angle) * distance),
            )
            pygame.draw.circle(
                overlay,
                (*highlight, round(230 * visibility)),
                spark,
                1 + spark_index % 2,
            )

        for hit_position in state.ability_effect_hit_positions:
            hit_center = _cell_center(
                hit_position,
                camera_x,
                camera_y,
                tile_size,
            )
            pygame.draw.circle(
                overlay,
                (*highlight, round(215 * visibility)),
                hit_center,
                round(5 + impact_progress * 11),
                width=2,
            )

    surface.blit(overlay, (0, 0))
