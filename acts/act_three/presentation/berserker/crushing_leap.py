import math

import pygame


CRUSHING_LEAP_FRAME_COUNT = 8


def crushing_leap_direction(origin, destination):
    column_change = destination[0] - origin[0]
    row_change = destination[1] - origin[1]

    if abs(column_change) >= abs(row_change):
        if column_change < 0:
            return "left"
        if column_change > 0:
            return "right"

    if row_change < 0:
        return "up"

    return "down"


def crushing_leap_frame(elapsed, duration):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )

    return min(
        CRUSHING_LEAP_FRAME_COUNT - 1,
        int(progress * CRUSHING_LEAP_FRAME_COUNT),
    )


def crushing_leap_position(
    start_position,
    end_position,
    elapsed,
    duration,
    tile_size,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    eased_progress = (
        progress
        * progress
        * (3 - 2 * progress)
    )
    jump_height = (
        math.sin(math.pi * progress)
        * tile_size
        * 0.55
    )

    ground_position = (
        round(
            start_position[0]
            + (
                end_position[0]
                - start_position[0]
            )
            * eased_progress
        ),
        round(
            start_position[1]
            + (
                end_position[1]
                - start_position[1]
            )
            * eased_progress
        ),
    )

    return (
        ground_position[0],
        round(ground_position[1] - jump_height),
    )


def crushing_leap_camera_offset(
    elapsed,
    travel_duration,
    impact_duration,
):
    impact_elapsed = elapsed - travel_duration
    shake_duration = min(260, impact_duration)

    if not 0 <= impact_elapsed < shake_duration:
        return (0, 0)

    progress = impact_elapsed / shake_duration
    strength = 7 * (1 - progress) ** 2

    return (
        round(math.sin(impact_elapsed * 0.21) * strength),
        round(math.cos(impact_elapsed * 0.29) * strength * 0.65),
    )


def draw_crushing_leap_targeting(
    surface,
    origin,
    target,
    impact_cells,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    if target is None:
        return

    pulse = (
        math.sin(current_time * 0.011) + 1
    ) / 2
    cell_surface = pygame.Surface(
        (tile_size, tile_size),
        pygame.SRCALPHA,
    )
    cell_surface.fill(
        (
            152,
            24,
            12,
            round(36 + pulse * 24),
        )
    )
    pygame.draw.rect(
        cell_surface,
        (
            238,
            67,
            31,
            round(145 + pulse * 70),
        ),
        cell_surface.get_rect().inflate(-4, -4),
        width=2,
    )
    pygame.draw.polygon(
        cell_surface,
        (
            255,
            121,
            48,
            round(80 + pulse * 70),
        ),
        (
            (tile_size // 2, 9),
            (tile_size - 9, tile_size // 2),
            (tile_size // 2, tile_size - 9),
            (9, tile_size // 2),
        ),
        width=2,
    )

    for column, row in impact_cells:
        surface.blit(
            cell_surface,
            (
                column * tile_size - camera_x,
                row * tile_size - camera_y,
            ),
        )

    target_position = (
        target[0] * tile_size - camera_x,
        target[1] * tile_size - camera_y,
    )
    target_surface = pygame.Surface(
        (tile_size, tile_size),
        pygame.SRCALPHA,
    )
    target_surface.fill(
        (
            179,
            27,
            11,
            round(58 + pulse * 38),
        )
    )

    center = (tile_size // 2, tile_size // 2)
    outer_radius = round(
        tile_size * (0.31 + pulse * 0.08)
    )
    inner_radius = round(
        tile_size * (0.16 + pulse * 0.04)
    )

    pygame.draw.circle(
        target_surface,
        (255, 96, 37, 225),
        center,
        outer_radius,
        width=3,
    )
    pygame.draw.circle(
        target_surface,
        (255, 183, 79, 210),
        center,
        inner_radius,
        width=2,
    )
    pygame.draw.line(
        target_surface,
        (255, 213, 123, 230),
        (center[0] - 10, center[1]),
        (center[0] + 10, center[1]),
        width=2,
    )
    pygame.draw.line(
        target_surface,
        (255, 213, 123, 230),
        (center[0], center[1] - 10),
        (center[0], center[1] + 10),
        width=2,
    )

    surface.blit(target_surface, target_position)

    origin_center = (
        origin[0] * tile_size
        - camera_x
        + tile_size // 2,
        origin[1] * tile_size
        - camera_y
        + tile_size // 2,
    )
    target_center = (
        target_position[0] + tile_size // 2,
        target_position[1] + tile_size // 2,
    )

    pygame.draw.line(
        surface,
        (157, 48, 24),
        origin_center,
        target_center,
        width=2,
    )

    path_progress = (
        current_time % 700
    ) / 700
    path_marker = (
        round(
            origin_center[0]
            + (
                target_center[0]
                - origin_center[0]
            )
            * path_progress
        ),
        round(
            origin_center[1]
            + (
                target_center[1]
                - origin_center[1]
            )
            * path_progress
        ),
    )
    pygame.draw.circle(
        surface,
        (255, 154, 66),
        path_marker,
        4,
    )


def draw_crushing_leap_travel_effect(
    surface,
    sprite,
    start_position,
    end_position,
    elapsed,
    duration,
    tile_size,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    eased_progress = (
        progress
        * progress
        * (3 - 2 * progress)
    )
    ground_position = (
        round(
            start_position[0]
            + (
                end_position[0]
                - start_position[0]
            )
            * eased_progress
        ),
        round(
            start_position[1]
            + (
                end_position[1]
                - start_position[1]
            )
            * eased_progress
        ),
    )
    height_ratio = math.sin(math.pi * progress)
    shadow_width = round(
        tile_size * (0.48 - height_ratio * 0.16)
    )
    shadow_height = max(5, round(shadow_width * 0.28))
    shadow_surface = pygame.Surface(
        (tile_size, tile_size),
        pygame.SRCALPHA,
    )
    pygame.draw.ellipse(
        shadow_surface,
        (
            25,
            8,
            5,
            round(145 - height_ratio * 70),
        ),
        (
            tile_size // 2 - shadow_width // 2,
            tile_size - shadow_height - 5,
            shadow_width,
            shadow_height,
        ),
    )
    surface.blit(shadow_surface, ground_position)

    for echo_index in range(3, 0, -1):
        echo_elapsed = max(
            0,
            elapsed - echo_index * 32,
        )
        echo_position = crushing_leap_position(
            start_position,
            end_position,
            echo_elapsed,
            duration,
            tile_size,
        )
        echo = sprite.copy()
        echo.fill(
            (80, 24, 8, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        echo.set_alpha(26 + echo_index * 16)
        surface.blit(echo, echo_position)


def draw_crushing_leap_impact_effect(
    surface,
    target,
    camera_x,
    camera_y,
    impact_elapsed,
    impact_duration,
    tile_size,
):
    if not 0 <= impact_elapsed < impact_duration:
        return

    progress = impact_elapsed / impact_duration
    visibility = (1 - progress) ** 2
    effect_size = tile_size * 3
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center = (effect_size // 2, effect_size // 2)
    target_position = (
        target[0] * tile_size - camera_x,
        target[1] * tile_size - camera_y,
    )

    outer_radius = round(
        tile_size * (0.25 + progress * 1.15)
    )
    inner_radius = round(
        tile_size * (0.12 + progress * 0.72)
    )

    pygame.draw.circle(
        effect_surface,
        (
            255,
            91,
            31,
            round(210 * visibility),
        ),
        center,
        outer_radius,
        width=max(1, round(4 * visibility)),
    )
    pygame.draw.circle(
        effect_surface,
        (
            255,
            185,
            78,
            round(175 * visibility),
        ),
        center,
        inner_radius,
        width=2,
    )

    for crack_index in range(12):
        angle = (
            crack_index * math.tau / 12
            + math.sin(crack_index * 3.17) * 0.18
        )
        start_distance = tile_size * 0.16
        end_distance = (
            tile_size
            * (0.38 + (crack_index % 4) * 0.09)
            * min(1, progress * 4)
        )
        start = (
            round(
                center[0]
                + math.cos(angle) * start_distance
            ),
            round(
                center[1]
                + math.sin(angle) * start_distance
            ),
        )
        end = (
            round(
                center[0]
                + math.cos(angle) * end_distance
            ),
            round(
                center[1]
                + math.sin(angle) * end_distance
            ),
        )
        pygame.draw.line(
            effect_surface,
            (
                112,
                35,
                19,
                round(220 * visibility),
            ),
            start,
            end,
            width=2,
        )

    for dust_index in range(18):
        phase = (
            progress + dust_index * 0.071
        ) % 1
        angle = dust_index * 2.399
        distance = (
            tile_size
            * (0.18 + phase * 0.88)
        )
        dust_position = (
            round(
                center[0]
                + math.cos(angle) * distance
            ),
            round(
                center[1]
                + math.sin(angle) * distance * 0.48
                - math.sin(math.pi * phase) * 15
            ),
        )
        dust_visibility = (
            math.sin(math.pi * phase)
            * visibility
        )
        pygame.draw.circle(
            effect_surface,
            (
                191,
                91,
                43,
                round(190 * dust_visibility),
            ),
            dust_position,
            2 if dust_index % 4 == 0 else 1,
        )

    surface.blit(
        effect_surface,
        (
            target_position[0] - tile_size,
            target_position[1] - tile_size,
        ),
    )
