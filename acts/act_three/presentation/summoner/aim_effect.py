import math

import pygame

from acts.act_three.combat.summoner_aim import (
    summoner_aim_targets,
)
from acts.act_three.presentation.view import _view_position


def draw_summoner_aim_effect(
    surface,
    game_state,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    player = game_state.player
    if not player.summoner_aiming:
        return

    target = player.summoner_aim_target
    if target not in summoner_aim_targets(game_state):
        return

    target_position = _view_position(
        target[0],
        target[1],
        camera_x,
        camera_y,
    )
    center = (
        target_position[0] + tile_size // 2,
        target_position[1] + tile_size // 2,
    )
    size = round(tile_size * 1.7)
    layer = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    middle = (
        size // 2,
        size // 2,
    )
    pulse = (
        math.sin(current_time * 0.009)
        + 1
    ) / 2
    rotation = current_time * 0.0011
    radius = round(
        tile_size * (0.34 + pulse * 0.025)
    )

    for aura_index in range(4):
        aura_radius = radius + 7 + aura_index * 4
        aura_alpha = max(
            5,
            round((31 - aura_index * 7) * pulse),
        )
        pygame.draw.circle(
            layer,
            (
                4,
                31,
                34,
                aura_alpha,
            ),
            middle,
            aura_radius,
        )

    shadow_ring = pygame.Rect(
        0,
        0,
        radius * 2 + 14,
        radius * 2 + 10,
    )
    shadow_ring.center = middle
    pygame.draw.ellipse(
        layer,
        (2, 10, 14, 155),
        shadow_ring,
        width=6,
    )

    outer_ring = pygame.Rect(
        0,
        0,
        radius * 2,
        radius * 2,
    )
    outer_ring.center = middle

    for arc_index in range(6):
        start = (
            rotation
            + arc_index * math.tau / 6
            + math.sin(
                current_time * 0.002
                + arc_index * 1.7
            ) * 0.08
        )
        arc_length = 0.48 + (arc_index % 2) * 0.18

        pygame.draw.arc(
            layer,
            (2, 18, 21, 235),
            outer_ring,
            start - 0.05,
            start + arc_length + 0.05,
            5,
        )
        pygame.draw.arc(
            layer,
            (
                22,
                145 + arc_index % 3 * 13,
                148 + arc_index % 2 * 17,
                225,
            ),
            outer_ring,
            start,
            start + arc_length,
            2,
        )

    feather_distance = radius - 5
    for feather_index in range(7):
        angle = (
            -rotation * 1.35
            + feather_index * math.tau / 7
        )
        feather_center = (
            round(
                middle[0]
                + math.cos(angle) * feather_distance
            ),
            round(
                middle[1]
                + math.sin(angle) * feather_distance * 0.78
            ),
        )
        feather_width = 10 + feather_index % 3 * 2
        feather_height = 17 + feather_index % 2 * 3
        feather_rect = pygame.Rect(
            0,
            0,
            feather_width,
            feather_height,
        )
        feather_rect.center = feather_center

        pygame.draw.arc(
            layer,
            (3, 21, 24, 230),
            feather_rect,
            angle - 1.8,
            angle + 1.2,
            4,
        )
        pygame.draw.arc(
            layer,
            (
                31,
                170,
                168,
                185 + feather_index % 2 * 35,
            ),
            feather_rect,
            angle - 1.72,
            angle + 1.08,
            2,
        )

    for mote_index in range(9):
        mote_angle = (
            rotation * 1.8
            + mote_index * math.tau / 9
        )
        mote_distance = (
            radius
            + 3
            + math.sin(
                current_time * 0.004
                + mote_index * 1.9
            ) * 5
        )
        mote_position = (
            round(
                middle[0]
                + math.cos(mote_angle) * mote_distance
            ),
            round(
                middle[1]
                + math.sin(mote_angle)
                * mote_distance
                * 0.82
            ),
        )
        mote_alpha = round(
            85
            + 90
            * (
                math.sin(
                    current_time * 0.007
                    + mote_index
                )
                + 1
            )
            / 2
        )
        pygame.draw.circle(
            layer,
            (
                48,
                199,
                192,
                mote_alpha,
            ),
            mote_position,
            1 + mote_index % 2,
        )

    eye_glow_radius = round(11 + pulse * 3)
    pygame.draw.circle(
        layer,
        (
            18,
            137,
            139,
            round(30 + pulse * 30),
        ),
        middle,
        eye_glow_radius,
    )

    eye = pygame.Rect(0, 0, 15, 23)
    eye.center = middle
    pygame.draw.ellipse(
        layer,
        (2, 12, 16, 245),
        eye,
    )
    pygame.draw.ellipse(
        layer,
        (
            37,
            183,
            180,
            235,
        ),
        eye,
        width=2,
    )

    pupil = pygame.Rect(
        0,
        0,
        5,
        round(10 + pulse * 3),
    )
    pupil.center = middle
    pygame.draw.ellipse(
        layer,
        (
            137,
            255,
            241,
            250,
        ),
        pupil,
    )
    pygame.draw.circle(
        layer,
        (223, 255, 250, 255),
        (
            middle[0],
            middle[1] - 2,
        ),
        2,
    )

    entry_elapsed = (
        current_time
        - player.summoner_aim_started_at
    )
    if 0 <= entry_elapsed < 260:
        entry_progress = entry_elapsed / 260
        entry_radius = round(
            radius
            + (1 - entry_progress) * tile_size * 0.42
        )
        entry_alpha = round(
            190 * (1 - entry_progress)
        )
        entry_ring = pygame.Rect(
            0,
            0,
            entry_radius * 2,
            entry_radius * 2,
        )
        entry_ring.center = middle

        for entry_index in range(4):
            start = (
                -rotation
                + entry_index * math.pi / 2
            )
            pygame.draw.arc(
                layer,
                (
                    57,
                    218,
                    209,
                    entry_alpha,
                ),
                entry_ring,
                start,
                start + 0.74,
                2,
            )

    surface.blit(
        layer,
        (
            round(center[0] - middle[0]),
            round(center[1] - middle[1]),
        ),
    )
