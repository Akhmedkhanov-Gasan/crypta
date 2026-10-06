import math

import pygame

from acts.act_three.presentation.animation import (
    _ATTACK_FRAME_DURATION_MS,
)
from acts.act_three.presentation.combat_effects import (
    _draw_attack_impact_flash,
)
from acts.act_three.presentation.player_motion import (
    assassin_attack_direction,
)
from acts.act_three.presentation.view import (
    _view_position,
)
from acts.act_three.presentation.paladin.block import (
    paladin_block_frame,
)
from presentation.layout import ACT_THREE_TILE_SIZE


_SWING_ANGLES = {
    "right": (-0.95, 0.95),
    "left": (math.pi + 0.95, math.pi - 0.95),
    "up": (-math.pi / 2 - 0.95, -math.pi / 2 + 0.95),
    "down": (math.pi / 2 - 0.9, math.pi / 2 + 0.9),
}


def draw_paladin_attack_effects(
    surface,
    player,
    player_position,
    attack_targets,
    camera_x,
    camera_y,
    current_time,
):
    if player.subclass != "paladin" or player.health <= 0:
        return

    if paladin_block_frame(player, current_time) is not None:
        return

    started_at = player.attack_animation_started_at
    elapsed = current_time - started_at

    if started_at <= 0 or not 0 <= elapsed < _ATTACK_FRAME_DURATION_MS:
        return

    progress = elapsed / _ATTACK_FRAME_DURATION_MS
    swing = max(0.0, min(1.0, (progress - 0.5) / 0.375))
    visibility = (
        math.sin(math.pi * swing)
        if 0.0 < swing < 1.0
        else 0.0
    )

    if visibility > 0:
        tile_size = ACT_THREE_TILE_SIZE
        effect_size = tile_size * 3
        center = effect_size // 2
        radius = tile_size * 0.66
        direction = assassin_attack_direction(
            player.facing_direction
        )
        start_angle, end_angle = _SWING_ANGLES[direction]
        angle_delta = end_angle - start_angle
        swing_direction = 1.0 if angle_delta > 0 else -1.0
        leading_angle = start_angle + angle_delta * swing
        trail_length = min(
            abs(angle_delta) * swing,
            0.25 + visibility * 0.7,
        )

        effect = pygame.Surface(
            (effect_size, effect_size),
            pygame.SRCALPHA,
        )
        points = []

        for index in range(21):
            point_angle = (
                leading_angle
                - swing_direction
                * trail_length
                * (1.0 - index / 20)
            )
            points.append(
                (
                    round(center + math.cos(point_angle) * radius),
                    round(center + math.sin(point_angle) * radius),
                )
            )

        for color, opacity, width_ratio in (
            ((24, 15, 33), 175, 0.20),
            ((69, 48, 78), 145, 0.12),
            ((145, 126, 88), 195, 0.055),
            ((235, 222, 180), 235, 0.018),
        ):
            pygame.draw.lines(
                effect,
                (*color, round(opacity * visibility)),
                False,
                points,
                max(1, round(tile_size * width_ratio)),
            )

        tip_x, tip_y = points[-1]
        spark_length = max(2, round(tile_size * 0.065))
        spark_color = (
            245,
            233,
            199,
            round(230 * visibility),
        )

        pygame.draw.line(
            effect,
            spark_color,
            (tip_x - spark_length, tip_y),
            (tip_x + spark_length, tip_y),
            1,
        )
        pygame.draw.line(
            effect,
            spark_color,
            (tip_x, tip_y - spark_length),
            (tip_x, tip_y + spark_length),
            1,
        )

        surface.blit(
            effect,
            (
                round(player_position[0] + tile_size / 2 - center),
                round(player_position[1] + tile_size / 2 - center),
            ),
        )

    for column, row in attack_targets:
        _draw_attack_impact_flash(
            surface,
            _view_position(
                column,
                row,
                camera_x,
                camera_y,
            ),
            current_time,
            started_at,
            (165, 145, 105),
        )
