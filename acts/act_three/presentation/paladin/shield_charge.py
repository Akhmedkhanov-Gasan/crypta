import math

import pygame

from acts.act_three.presentation.player_motion import (
    assassin_hurt_direction,
)
from acts.act_three.settings import (
    PALADIN_SHIELD_CHARGE_IMPACT_MS,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
    PALADIN_SHIELD_CHARGE_WINDUP_MS,
)


def shield_charge_direction(origin, destination):
    return assassin_hurt_direction(
        (
            destination[0] - origin[0],
            destination[1] - origin[1],
        )
    )


def shield_charge_motion_progress(elapsed):
    travel_elapsed = (
        elapsed - PALADIN_SHIELD_CHARGE_WINDUP_MS
    )
    progress = max(
        0.0,
        min(
            1.0,
            travel_elapsed
            / PALADIN_SHIELD_CHARGE_TRAVEL_MS,
        ),
    )
    return 1 - (1 - progress) ** 2.15


def shield_charge_sprite(
    player_state,
    floor,
    assets,
):
    direction = shield_charge_direction(
        player_state.shield_charge_origin,
        (
            floor.player_column,
            floor.player_row,
        ),
    )
    elapsed = player_state.shield_charge_elapsed

    if elapsed < PALADIN_SHIELD_CHARGE_WINDUP_MS:
        progress = max(
            0.0,
            elapsed / PALADIN_SHIELD_CHARGE_WINDUP_MS,
        )
        frame = min(1, int(progress * 2))
    elif elapsed < (
        PALADIN_SHIELD_CHARGE_WINDUP_MS
        + PALADIN_SHIELD_CHARGE_TRAVEL_MS
    ):
        progress = (
            elapsed - PALADIN_SHIELD_CHARGE_WINDUP_MS
        ) / PALADIN_SHIELD_CHARGE_TRAVEL_MS
        frame = 2 + min(4, int(progress * 5))
    else:
        frame = 7

    return assets[
        f"player_paladin_shield_charge_{direction}_{frame}"
    ]


def shield_charge_camera_offset(elapsed):
    impact_elapsed = (
        elapsed
        - PALADIN_SHIELD_CHARGE_WINDUP_MS
        - PALADIN_SHIELD_CHARGE_TRAVEL_MS
    )

    if not (
        0
        <= impact_elapsed
        < PALADIN_SHIELD_CHARGE_IMPACT_MS
    ):
        return (0, 0)

    progress = (
        impact_elapsed
        / PALADIN_SHIELD_CHARGE_IMPACT_MS
    )
    strength = 9 * (1 - progress) ** 2

    return (
        round(
            math.sin(impact_elapsed * 0.31)
            * strength
        ),
        round(
            math.cos(impact_elapsed * 0.43)
            * strength
            * 0.72
        ),
    )


def _jagged_ring(
    surface,
    center,
    radius,
    color,
    width,
    phase,
):
    points = []

    for index in range(12):
        angle = math.tau * index / 12
        variation = (
            1
            + math.sin(index * 4.7 + phase) * 0.14
        )
        distance = radius * variation
        points.append(
            (
                round(
                    center[0]
                    + math.cos(angle) * distance
                ),
                round(
                    center[1]
                    + math.sin(angle) * distance
                ),
            )
        )

    pygame.draw.polygon(
        surface,
        color,
        points,
        width,
    )


def draw_shield_charge_effect(
    surface,
    start_position,
    end_position,
    player_position,
    elapsed,
    size,
):
    if start_position is None:
        return

    start = (
        start_position[0] + size // 2,
        start_position[1] + size // 2,
    )
    end = (
        end_position[0] + size // 2,
        end_position[1] + size // 2,
    )
    current = (
        player_position[0] + size // 2,
        player_position[1] + size // 2,
    )

    travel_x = end[0] - start[0]
    travel_y = end[1] - start[1]
    travel_length = max(
        1.0,
        math.hypot(travel_x, travel_y),
    )
    direction_x = travel_x / travel_length
    direction_y = travel_y / travel_length
    normal_x = -direction_y
    normal_y = direction_x

    windup_progress = max(
        0.0,
        min(
            1.0,
            elapsed / PALADIN_SHIELD_CHARGE_WINDUP_MS,
        ),
    )
    travel_elapsed = (
        elapsed - PALADIN_SHIELD_CHARGE_WINDUP_MS
    )
    travel_progress = max(
        0.0,
        min(
            1.0,
            travel_elapsed
            / PALADIN_SHIELD_CHARGE_TRAVEL_MS,
        ),
    )
    impact_elapsed = (
        travel_elapsed
        - PALADIN_SHIELD_CHARGE_TRAVEL_MS
    )
    impact_progress = max(
        0.0,
        min(
            1.0,
            impact_elapsed
            / PALADIN_SHIELD_CHARGE_IMPACT_MS,
        ),
    )

    effect = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    if elapsed < PALADIN_SHIELD_CHARGE_WINDUP_MS:
        pulse = 0.65 + math.sin(elapsed * 0.06) * 0.18
        shield_center = (
            round(
                current[0] + direction_x * size * 0.27
            ),
            round(
                current[1] + direction_y * size * 0.27
            ),
        )

        for index in range(3):
            radius = round(
                size
                * (
                    0.54
                    - windup_progress * 0.24
                    + index * 0.08
                )
            )
            alpha = round(
                (75 - index * 18)
                * windup_progress
            )
            _jagged_ring(
                effect,
                shield_center,
                radius,
                (74, 45, 91, alpha),
                max(1, size // 28),
                elapsed * 0.025 + index,
            )

        for index in range(8):
            angle = math.tau * index / 8
            distance = (
                size
                * (
                    0.48
                    - windup_progress * 0.25
                )
            )
            particle_position = (
                round(
                    shield_center[0]
                    + math.cos(angle) * distance
                ),
                round(
                    shield_center[1]
                    + math.sin(angle) * distance
                ),
            )
            pygame.draw.circle(
                effect,
                (
                    188,
                    148,
                    91,
                    round(150 * windup_progress),
                ),
                particle_position,
                max(1, size // 30),
            )

        pygame.draw.circle(
            effect,
            (
                38,
                20,
                50,
                round(130 * windup_progress),
            ),
            shield_center,
            round(size * 0.31 * pulse),
        )
        pygame.draw.circle(
            effect,
            (
                229,
                197,
                126,
                round(210 * windup_progress),
            ),
            shield_center,
            round(size * 0.31 * pulse),
            max(2, size // 24),
        )

    if 0 < travel_progress < 1:
        trail_length = size * (
            0.85 + travel_progress * 1.15
        )

        for index in range(7):
            segment_start_distance = (
                trail_length * index / 7
            )
            segment_end_distance = (
                trail_length * (index + 0.62) / 7
            )
            side = -1 if index % 2 else 1
            offset = (
                size
                * (0.04 + index % 3 * 0.035)
                * side
            )

            segment_start = (
                round(
                    current[0]
                    - direction_x
                    * segment_start_distance
                    + normal_x * offset
                ),
                round(
                    current[1]
                    - direction_y
                    * segment_start_distance
                    + normal_y * offset
                ),
            )
            segment_end = (
                round(
                    current[0]
                    - direction_x
                    * segment_end_distance
                    - normal_x * offset * 0.55
                ),
                round(
                    current[1]
                    - direction_y
                    * segment_end_distance
                    - normal_y * offset * 0.55
                ),
            )
            fade = 1 - index / 7

            pygame.draw.line(
                effect,
                (
                    48,
                    27,
                    59,
                    round(155 * fade),
                ),
                segment_start,
                segment_end,
                max(3, round(size * 0.20 * fade)),
            )
            pygame.draw.line(
                effect,
                (
                    207,
                    168,
                    102,
                    round(220 * fade),
                ),
                segment_start,
                segment_end,
                max(1, round(size * 0.055 * fade)),
            )

        shield_center = (
            round(
                current[0] + direction_x * size * 0.34
            ),
            round(
                current[1] + direction_y * size * 0.34
            ),
        )
        shield_points = []

        for index in range(6):
            angle = math.tau * index / 6
            radius = size * (
                0.27
                + (0.04 if index % 2 else 0)
            )
            shield_points.append(
                (
                    round(
                        shield_center[0]
                        + math.cos(angle) * radius
                    ),
                    round(
                        shield_center[1]
                        + math.sin(angle) * radius
                    ),
                )
            )

        pygame.draw.polygon(
            effect,
            (32, 17, 43, 190),
            shield_points,
        )
        pygame.draw.polygon(
            effect,
            (226, 194, 126, 235),
            shield_points,
            max(2, size // 18),
        )

    if impact_progress > 0:
        visibility = (1 - impact_progress) ** 1.4
        impact_center = (
            round(
                end[0] + direction_x * size * 0.26
            ),
            round(
                end[1] + direction_y * size * 0.26
            ),
        )

        for index in range(3):
            radius = size * (
                0.25
                + impact_progress * (0.65 + index * 0.16)
            )
            _jagged_ring(
                effect,
                impact_center,
                radius,
                (
                    232,
                    202,
                    134,
                    round(
                        visibility
                        * (220 - index * 48)
                    ),
                ),
                max(2, size // (20 + index * 5)),
                impact_elapsed * 0.04 + index,
            )

        for index in range(16):
            angle = (
                math.tau * index / 16
                + math.sin(index * 3.1) * 0.11
            )
            distance = size * (
                0.20 + impact_progress * 0.74
            )
            length = size * (
                0.10 + index % 4 * 0.045
            )
            spark_start = (
                round(
                    impact_center[0]
                    + math.cos(angle) * distance
                ),
                round(
                    impact_center[1]
                    + math.sin(angle) * distance
                ),
            )
            spark_end = (
                round(
                    spark_start[0]
                    + math.cos(angle) * length
                ),
                round(
                    spark_start[1]
                    + math.sin(angle) * length
                ),
            )

            pygame.draw.line(
                effect,
                (
                    245,
                    218,
                    155,
                    round(235 * visibility),
                ),
                spark_start,
                spark_end,
                max(1, size // 25),
            )

        for index in range(9):
            side = -1 if index % 2 else 1
            distance = size * (
                0.22 + impact_progress * 0.55
            )
            debris_position = (
                round(
                    impact_center[0]
                    - direction_x * distance
                    + normal_x
                    * side
                    * size
                    * (0.10 + index * 0.025)
                ),
                round(
                    impact_center[1]
                    - direction_y * distance
                    + normal_y
                    * side
                    * size
                    * (0.10 + index * 0.025)
                ),
            )
            pygame.draw.circle(
                effect,
                (
                    82,
                    58,
                    65,
                    round(170 * visibility),
                ),
                debris_position,
                max(1, size // 24),
            )

    surface.blit(effect, (0, 0))
