import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.summoner.true_form import (
    SUMMONER_TRUE_FORM_ATTACK_DURATION_MS,
    summoner_true_form_direction,
    summoner_true_form_transition_progress,
    summoner_true_form_visual_active,
)


def _draw_smoke_blob(
    surface,
    center,
    radius,
    color,
    alpha,
    phase,
):
    for layer in range(4):
        layer_radius = max(
            1,
            round(radius * (1 - layer * 0.14)),
        )
        offset_x = round(
            math.sin(phase + layer * 1.7)
            * radius
            * 0.28
        )
        offset_y = round(
            math.cos(phase * 0.7 + layer * 1.3)
            * radius
            * 0.19
        )
        width = layer_radius * 2 + layer % 2 * 3
        height = max(
            2,
            round(layer_radius * (1.15 + layer % 3 * 0.17)),
        )
        pygame.draw.ellipse(
            surface,
            (
                color[0],
                color[1],
                color[2],
                max(0, round(alpha * (1 - layer * 0.19))),
            ),
            (
                center[0] + offset_x - width // 2,
                center[1] + offset_y - height // 2,
                width,
                height,
            ),
        )


def _draw_astral_halo(
    surface,
    center,
    current_time,
    pulse,
):
    phase = current_time / 1250

    for glow_index in range(4, 0, -1):
        radius_x = 19 + glow_index * 5
        radius_y = 23 + glow_index * 6
        pygame.draw.ellipse(
            surface,
            (
                13 + glow_index * 6,
                82 + glow_index * 10,
                91 + glow_index * 12,
                round(
                    10
                    + glow_index * 5
                    + pulse * 8
                ),
            ),
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
        )

    for arc_index in range(4):
        radius_x = 25 + arc_index * 5
        radius_y = 29 + arc_index * 6
        start = (
            phase
            * (
                0.65
                if arc_index % 2 == 0
                else -0.48
            )
            + arc_index * 1.63
        )
        color = (
            (
                73,
                221,
                207,
                round(90 + pulse * 45),
            )
            if arc_index % 2 == 0
            else (
                129,
                74,
                173,
                round(68 + pulse * 38),
            )
        )
        pygame.draw.arc(
            surface,
            color,
            (
                center[0] - radius_x,
                center[1] - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
            start,
            start + 1.1 + arc_index * 0.11,
            2,
        )


def _quadratic_point(start, control, end, progress):
    inverse = 1 - progress
    return (
        inverse * inverse * start[0]
        + 2 * inverse * progress * control[0]
        + progress * progress * end[0],
        inverse * inverse * start[1]
        + 2 * inverse * progress * control[1]
        + progress * progress * end[1],
    )


def draw_summoner_true_form_aura(
    surface,
    position,
    player,
    current_time,
    moving,
):
    if not summoner_true_form_visual_active(
        player,
        current_time,
    ):
        return

    margin = 54
    size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2 + 6,
    )
    time_phase = current_time / 900
    pulse = 0.5 + 0.5 * math.sin(current_time / 620)

    _draw_astral_halo(
        effect_surface,
        (
            center[0],
            center[1] - 4,
        ),
        current_time,
        pulse,
    )

    if not moving:
        for mote_index in range(7):
            angle = (
                time_phase * 0.62
                + mote_index * math.tau / 7
            )
            orbit_x = 29 + mote_index % 2 * 6
            orbit_y = 31 + mote_index % 3 * 4
            mote_position = (
                center[0]
                + round(math.cos(angle) * orbit_x),
                center[1]
                - 4
                + round(math.sin(angle) * orbit_y),
            )
            mote_alpha = round(
                105
                + pulse * 70
                + math.sin(
                    current_time / 310
                    + mote_index
                )
                * 28
            )
            mote_color = (
                (99, 235, 219)
                if mote_index % 2
                else (164, 105, 207)
            )

            pygame.draw.circle(
                effect_surface,
                (
                    mote_color[0],
                    mote_color[1],
                    mote_color[2],
                    max(30, mote_alpha // 3),
                ),
                mote_position,
                4,
            )
            pygame.draw.circle(
                effect_surface,
                (
                    mote_color[0],
                    mote_color[1],
                    mote_color[2],
                    max(70, mote_alpha),
                ),
                mote_position,
                1 if mote_index % 3 else 2,
            )

    if moving:
        direction = summoner_true_form_direction(player)
        direction_vector = {
            "left": (-1, 0),
            "right": (1, 0),
            "up": (0, -1),
            "down": (0, 1),
        }[direction]

        for trail_index in range(13):
            distance = 10 + trail_index * 4
            drift = math.sin(
                current_time / 75 + trail_index * 1.4
            ) * (3 + trail_index * 0.3)
            trail_center = (
                center[0]
                - direction_vector[0] * distance
                + round(direction_vector[1] * drift),
                center[1]
                - direction_vector[1] * distance
                - round(direction_vector[0] * drift),
            )
            _draw_smoke_blob(
                effect_surface,
                trail_center,
                max(2, 7 - trail_index // 3),
                (
                    18 + trail_index * 2,
                    127 + trail_index * 4,
                    133 + trail_index * 5,
                ),
                max(12, 85 - trail_index * 6),
                time_phase + trail_index,
            )

    transition_progress = (
        summoner_true_form_transition_progress(
            player,
            current_time,
        )
    )
    if transition_progress is not None:
        progress = transition_progress
        visibility = math.sin(math.pi * progress)

        for burst_index in range(28):
            angle = (
                burst_index * 2.399
                + progress * 2.8
            )
            distance = (
                6
                + progress
                * (
                    24
                    + burst_index % 7 * 4
                )
            )
            burst_center = (
                center[0]
                + round(math.cos(angle) * distance),
                center[1]
                + round(math.sin(angle) * distance),
            )
            color = (
                (41, 195, 187)
                if burst_index % 2 == 0
                else (93, 48, 139)
            )
            _draw_smoke_blob(
                effect_surface,
                burst_center,
                4 + burst_index % 5,
                color,
                round(115 * visibility),
                time_phase + burst_index,
            )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )


def draw_summoner_true_form_foreground(
    surface,
    position,
    player,
    current_time,
):
    if not summoner_true_form_visual_active(
        player,
        current_time,
    ):
        return

    margin = 38
    size = ACT_THREE_TILE_SIZE + margin * 2
    effect_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )
    phase = current_time / 740
    transition_progress = (
        summoner_true_form_transition_progress(
            player,
            current_time,
        )
    )

    if transition_progress is None:
        pulse = 0.5 + 0.5 * math.sin(
            current_time / 540
        )

        for crescent_index in range(3):
            radius_x = 20 + crescent_index * 7
            radius_y = 25 + crescent_index * 6
            start = (
                phase
                * (
                    0.38
                    if crescent_index % 2 == 0
                    else -0.31
                )
                + crescent_index * 2.05
            )
            pygame.draw.arc(
                effect_surface,
                (
                    116 + crescent_index * 18,
                    235,
                    220,
                    round(
                        72
                        + pulse * 48
                        - crescent_index * 10
                    ),
                ),
                (
                    center[0] - radius_x,
                    center[1] - 4 - radius_y,
                    radius_x * 2,
                    radius_y * 2,
                ),
                start,
                start + 0.72 + crescent_index * 0.16,
                2,
            )

        for star_index in range(6):
            angle = (
                phase * 0.55
                + star_index * math.tau / 6
            )
            star_position = (
                center[0]
                + round(
                    math.cos(angle)
                    * (24 + star_index % 2 * 7)
                ),
                center[1]
                - 4
                + round(
                    math.sin(angle)
                    * (28 + star_index % 3 * 4)
                ),
            )
            star_color = (
                (126, 245, 226)
                if star_index % 2
                else (184, 119, 218)
            )
            star_alpha = round(
                115
                + pulse * 90
                + math.sin(
                    current_time / 260
                    + star_index * 1.7
                )
                * 25
            )

            pygame.draw.circle(
                effect_surface,
                (
                    star_color[0],
                    star_color[1],
                    star_color[2],
                    max(35, star_alpha // 4),
                ),
                star_position,
                4,
            )
            pygame.draw.circle(
                effect_surface,
                (
                    star_color[0],
                    star_color[1],
                    star_color[2],
                    max(80, star_alpha),
                ),
                star_position,
                1 if star_index % 3 else 2,
            )
    else:
        progress = transition_progress
        visibility = math.sin(math.pi * progress)

        for veil_index in range(9):
            veil_center = (
                center[0]
                + round(
                    math.sin(
                        phase * 1.4 + veil_index * 1.8
                    )
                    * (9 + veil_index * 2)
                ),
                center[1]
                + 22
                - round(progress * 48)
                + veil_index % 3 * 4,
            )
            _draw_smoke_blob(
                effect_surface,
                veil_center,
                5 + veil_index % 4,
                (
                    72 + veil_index * 7,
                    216,
                    205,
                ),
                round(105 * visibility),
                phase + veil_index * 0.8,
            )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )


def draw_summoner_true_form_attack_effect(
    surface,
    origin_position,
    target_position,
    current_time,
    started_at,
):
    elapsed = current_time - started_at
    if not (
        0
        <= elapsed
        < SUMMONER_TRUE_FORM_ATTACK_DURATION_MS
    ):
        return

    progress = (
        elapsed / SUMMONER_TRUE_FORM_ATTACK_DURATION_MS
    )
    margin = 54
    left = min(origin_position[0], target_position[0]) - margin
    top = min(origin_position[1], target_position[1]) - margin
    right = (
        max(origin_position[0], target_position[0])
        + ACT_THREE_TILE_SIZE
        + margin
    )
    bottom = (
        max(origin_position[1], target_position[1])
        + ACT_THREE_TILE_SIZE
        + margin
    )
    effect_surface = pygame.Surface(
        (right - left, bottom - top),
        pygame.SRCALPHA,
    )
    origin_center = (
        origin_position[0]
        + ACT_THREE_TILE_SIZE // 2
        - left,
        origin_position[1]
        + ACT_THREE_TILE_SIZE // 2
        - top,
    )
    target_center = (
        target_position[0]
        + ACT_THREE_TILE_SIZE // 2
        - left,
        target_position[1]
        + ACT_THREE_TILE_SIZE // 2
        - top,
    )

    direction_x = target_center[0] - origin_center[0]
    direction_y = target_center[1] - origin_center[1]
    distance = max(
        1.0,
        math.hypot(direction_x, direction_y),
    )
    normal_x = -direction_y / distance
    normal_y = direction_x / distance
    travel = max(
        0.0,
        min(1.0, (progress - 0.10) / 0.42),
    )
    fade = max(
        0.0,
        min(1.0, (1 - progress) / 0.45),
    )

    for tendril_index in range(5):
        bend = (
            tendril_index - 2
        ) * 10 + math.sin(
            current_time / 70 + tendril_index
        ) * 7
        control = (
            (
                origin_center[0] + target_center[0]
            ) / 2
            + normal_x * bend,
            (
                origin_center[1] + target_center[1]
            ) / 2
            + normal_y * bend,
        )
        tendril_end = (
            origin_center[0] + direction_x * travel,
            origin_center[1] + direction_y * travel,
        )

        for segment_index in range(18):
            segment_progress = segment_index / 17
            if segment_progress > travel:
                continue

            local_progress = min(
                1.0,
                segment_progress / max(0.01, travel),
            )
            point = _quadratic_point(
                origin_center,
                control,
                tendril_end,
                local_progress,
            )
            wobble = math.sin(
                current_time / 55
                + segment_index * 1.3
                + tendril_index
            ) * 3
            smoke_center = (
                round(point[0] + normal_x * wobble),
                round(point[1] + normal_y * wobble),
            )
            color = (
                (33, 198, 190)
                if tendril_index % 2 == 0
                else (109, 56, 155)
            )
            _draw_smoke_blob(
                effect_surface,
                smoke_center,
                3 + (segment_index + tendril_index) % 4,
                color,
                round(
                    fade
                    * (
                        115
                        + segment_index % 5 * 12
                    )
                ),
                progress * 9
                + segment_index
                + tendril_index,
            )

    impact_progress = max(
        0.0,
        min(1.0, (progress - 0.28) / 0.72),
    )
    if impact_progress > 0:
        visibility = math.sin(
            math.pi * impact_progress
        )

        for impact_index in range(30):
            angle = (
                impact_index * 2.399
                + impact_progress * 3.6
            )
            distance_from_target = (
                3
                + impact_progress
                * (
                    13
                    + impact_index % 8 * 3
                )
            )
            impact_center = (
                target_center[0]
                + round(
                    math.cos(angle)
                    * distance_from_target
                ),
                target_center[1]
                + round(
                    math.sin(angle)
                    * distance_from_target
                ),
            )
            color = (
                (43, 211, 199)
                if impact_index % 3
                else (132, 63, 176)
            )
            _draw_smoke_blob(
                effect_surface,
                impact_center,
                4 + impact_index % 6,
                color,
                round(150 * visibility),
                progress * 12 + impact_index,
            )

        for core_index in range(7):
            core_center = (
                target_center[0]
                + round(
                    math.sin(
                        current_time / 45 + core_index
                    )
                    * 6
                ),
                target_center[1]
                + round(
                    math.cos(
                        current_time / 58 + core_index
                    )
                    * 5
                ),
            )
            _draw_smoke_blob(
                effect_surface,
                core_center,
                6 + core_index % 3,
                (
                    104,
                    232,
                    218,
                ),
                round(175 * visibility),
                progress * 15 + core_index,
            )

    surface.blit(
        effect_surface,
        (left, top),
    )
