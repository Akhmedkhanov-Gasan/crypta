import math

import pygame


def draw_shadow_step_targeting(
    surface,
    origin_position,
    target_position,
    current_time,
    tile_size,
):
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    half_tile = tile_size // 2
    origin = (
        origin_position[0] + half_tile,
        origin_position[1] + half_tile,
    )
    target = (
        target_position[0] + half_tile,
        target_position[1] + half_tile,
    )

    target_rect = pygame.Rect(
        target_position[0] + 5,
        target_position[1] + 5,
        tile_size - 10,
        tile_size - 10,
    )
    pulse = (
        math.sin(current_time * 0.009) + 1
    ) / 2

    pygame.draw.rect(
        overlay,
        (43, 35, 61, round(48 + pulse * 24)),
        target_rect,
        border_radius=8,
    )
    pygame.draw.rect(
        overlay,
        (142, 119, 184, round(155 + pulse * 65)),
        target_rect,
        width=2,
        border_radius=8,
    )

    difference_x = target[0] - origin[0]
    difference_y = target[1] - origin[1]
    distance = max(
        1.0,
        math.hypot(difference_x, difference_y),
    )
    perpendicular_x = -difference_y / distance
    perpendicular_y = difference_x / distance
    points = []

    for step in range(33):
        progress = step / 32
        taper = math.sin(math.pi * progress)
        wave = math.sin(
            progress * math.tau * 2
            - current_time * 0.006
        )
        offset = wave * taper * 4
        points.append(
            (
                round(
                    origin[0]
                    + difference_x * progress
                    + perpendicular_x * offset
                ),
                round(
                    origin[1]
                    + difference_y * progress
                    + perpendicular_y * offset
                ),
            )
        )

    pygame.draw.lines(
        overlay,
        (20, 18, 29, 115),
        False,
        points,
        width=6,
    )
    pygame.draw.lines(
        overlay,
        (102, 82, 135, 175),
        False,
        points,
        width=2,
    )
    pygame.draw.lines(
        overlay,
        (184, 162, 211, 125),
        False,
        points,
        width=1,
    )

    for mote_index in range(6):
        progress = (
            current_time / 1150
            + mote_index / 6
        ) % 1
        point_index = min(
            len(points) - 1,
            round(progress * (len(points) - 1)),
        )
        mote_position = points[point_index]
        mote_alpha = round(
            80 + 130 * math.sin(math.pi * progress)
        )
        pygame.draw.circle(
            overlay,
            (193, 174, 218, mote_alpha),
            mote_position,
            2,
        )

    pygame.draw.circle(
        overlay,
        (213, 196, 231, 220),
        target,
        4,
        width=1,
    )
    surface.blit(overlay, (0, 0))
