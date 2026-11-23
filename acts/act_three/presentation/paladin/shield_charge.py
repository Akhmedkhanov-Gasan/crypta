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


def draw_shield_charge_targeting(
    surface,
    origin,
    cells,
    camera_x,
    camera_y,
    current_time,
    size,
):
    if not cells:
        return

    start = (
        (origin[0] + 0.5) * size - camera_x,
        (origin[1] + 0.5) * size - camera_y,
    )
    end = (
        (cells[-1][0] + 0.5) * size - camera_x,
        (cells[-1][1] + 0.5) * size - camera_y,
    )
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length < 1:
        return

    dx = (end[0] - start[0]) / length
    dy = (end[1] - start[1]) / length
    nx, ny = -dy, dx
    pulse = 0.5 + 0.5 * math.sin(current_time * 0.004)
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    def point(distance, offset=0):
        return (
            round(start[0] + dx * distance + nx * offset),
            round(start[1] + dy * distance + ny * offset),
        )

    half_width = size * 0.19
    shoulder = max(size * 0.22, length - size * 0.29)
    outline = (
        point(size * 0.24, -half_width),
        point(shoulder, -half_width),
        point(shoulder, -size * 0.32),
        point(length + size * 0.16),
        point(shoulder, size * 0.32),
        point(shoulder, half_width),
        point(size * 0.24, half_width),
    )
    pygame.draw.polygon(layer, (17, 14, 18, 72), outline)
    pygame.draw.lines(
        layer, (107, 44, 53, round(135 + pulse * 35)),
        False, outline, 2,
    )
    pygame.draw.lines(
        layer, (187, 179, 183, round(165 + pulse * 35)),
        False,
        (
            point(shoulder, -size * 0.23),
            point(length + size * 0.09),
            point(shoulder, size * 0.23),
        ),
        2,
    )
    for column, row in cells:
        center = (
            (column + 0.5) * size - camera_x,
            (row + 0.5) * size - camera_y,
        )
        pygame.draw.line(
            layer, (145, 117, 122, 115),
            (round(center[0] - nx * 3), round(center[1] - ny * 3)),
            (round(center[0] + nx * 3), round(center[1] + ny * 3)),
            1,
        )
    surface.blit(layer, (0, 0))


def draw_shield_charge_effect(
    surface,
    start_position,
    end_position,
    player_position,
    elapsed,
    size,
):
    if start_position is None or elapsed < 0:
        return

    start = (
        start_position[0] + size * 0.5,
        start_position[1] + size * 0.5,
    )
    end = (
        end_position[0] + size * 0.5,
        end_position[1] + size * 0.5,
    )
    current = (
        player_position[0] + size * 0.5,
        player_position[1] + size * 0.5,
    )
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length < 1:
        return

    dx = (end[0] - start[0]) / length
    dy = (end[1] - start[1]) / length
    nx, ny = -dy, dx
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    def point(center, forward, side=0):
        return (
            round(center[0] + dx * forward + nx * side),
            round(center[1] + dy * forward + ny * side),
        )

    def shield_edge(center, scale, alpha):
        points = tuple(
            point(center, size * forward * scale, size * side * scale)
            for forward, side in (
                (0.13, -0.25),
                (0.27, -0.14),
                (0.31, 0),
                (0.27, 0.14),
                (0.13, 0.25),
            )
        )
        pygame.draw.lines(layer, (27, 18, 24, alpha), False, points, 7)
        pygame.draw.lines(layer, (114, 44, 57, alpha), False, points, 3)
        pygame.draw.lines(
            layer, (190, 182, 187, round(alpha * 0.72)),
            False, points[1:4], 1,
        )

    travel_elapsed = elapsed - PALADIN_SHIELD_CHARGE_WINDUP_MS
    impact_elapsed = travel_elapsed - PALADIN_SHIELD_CHARGE_TRAVEL_MS

    if travel_elapsed < 0:
        progress = min(1.0, elapsed / PALADIN_SHIELD_CHARGE_WINDUP_MS)
        shield_edge(current, 0.82 + progress * 0.18, round(165 * progress))
        for side in (-1, 1):
            pygame.draw.line(
                layer, (108, 69, 79, round(110 * progress)),
                point(current, -size * (0.34 - progress * 0.16), side * size * 0.2),
                point(current, size * 0.08, side * size * 0.16),
                2,
            )
    elif impact_elapsed < 0:
        progress = travel_elapsed / PALADIN_SHIELD_CHARGE_TRAVEL_MS
        traveled = length * shield_charge_motion_progress(elapsed)
        shield_edge(current, 1.0, 190)
        for index in range(5):
            side = -1 if index % 2 else 1
            distance = min(traveled, size * (0.24 + index * 0.16))
            offset = side * size * (0.12 + index % 3 * 0.035)
            alpha = 120 - index * 17
            pygame.draw.line(
                layer, (65, 31, 42, alpha),
                point(current, -distance, offset),
                point(current, -max(0, distance - size * 0.22), offset * 0.85),
                3 if index < 2 else 2,
            )
        for index in range(6):
            age = (progress * 2.5 + index / 6) % 1.0
            side = -1 if index % 2 else 1
            distance = min(traveled, size * (0.2 + age * 0.65))
            center = point(current, -distance, side * size * (0.18 + age * 0.18))
            pygame.draw.line(
                layer, (156, 145, 149, round(105 * (1 - age))),
                center,
                point(center, -size * 0.055, side * size * 0.025),
                1,
            )
    elif impact_elapsed < PALADIN_SHIELD_CHARGE_IMPACT_MS:
        progress = impact_elapsed / PALADIN_SHIELD_CHARGE_IMPACT_MS
        fade = (1 - progress) ** 1.5
        shield_edge(end, 1.0 + progress * 0.75, round(190 * fade))
        for index in range(7):
            angle = (index - 3) * 0.29
            forward = size * (0.3 + progress * 0.6)
            side = math.sin(angle) * size * (0.25 + progress * 0.55)
            center = point(end, forward * math.cos(angle), side)
            pygame.draw.line(
                layer, (170, 150, 156, round(150 * fade)),
                center,
                point(center, size * 0.075 * math.cos(angle), size * 0.075 * math.sin(angle)),
                2 if index % 3 == 0 else 1,
            )

    surface.blit(layer, (0, 0))
