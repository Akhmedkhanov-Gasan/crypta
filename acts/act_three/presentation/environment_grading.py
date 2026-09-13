from functools import lru_cache

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


_BARRIER_SHADOW_ALPHA = 56
_GRIME_ALPHA = 18
_GRIME_FREQUENCY = 18


@lru_cache(maxsize=4)
def _barrier_shadow_surfaces(tile_size):
    depth = max(10, round(tile_size * 0.24))

    horizontal = pygame.Surface(
        (tile_size, depth * 2 + 1),
        pygame.SRCALPHA,
    )
    vertical = pygame.Surface(
        (depth * 2 + 1, tile_size),
        pygame.SRCALPHA,
    )

    for offset in range(depth + 1):
        progress = 1 - offset / depth
        alpha = round(
            _BARRIER_SHADOW_ALPHA
            * progress**2
        )
        color = (0, 0, 3, alpha)

        pygame.draw.line(
            horizontal,
            color,
            (0, depth - offset),
            (tile_size, depth - offset),
        )
        pygame.draw.line(
            horizontal,
            color,
            (0, depth + offset),
            (tile_size, depth + offset),
        )
        pygame.draw.line(
            vertical,
            color,
            (depth - offset, 0),
            (depth - offset, tile_size),
        )
        pygame.draw.line(
            vertical,
            color,
            (depth + offset, 0),
            (depth + offset, tile_size),
        )

    return horizontal, vertical, depth


@lru_cache(maxsize=4)
def _grime_surface(tile_size):
    radius = round(tile_size * 1.6)
    grime = pygame.Surface(
        (radius * 2, radius * 2),
        pygame.SRCALPHA,
    )

    for current_radius in range(radius, 0, -3):
        proximity = 1 - current_radius / radius
        alpha = round(
            _GRIME_ALPHA * proximity**1.5
        )

        pygame.draw.circle(
            grime,
            (0, 2, 5, alpha),
            (radius, radius),
            current_radius,
        )

    return grime


def _position_seed(column, row, visual_seed):
    return (
        column * 73856093
        ^ row * 19349663
        ^ visual_seed * 83492791
    ) & 0xFFFFFFFF


def _draw_floor_grading(
    surface,
    floor,
    camera_x,
    camera_y,
    first_column,
    first_row,
    last_column,
    last_row,
):
    grime = _grime_surface(ACT_THREE_TILE_SIZE)
    grime_radius = grime.get_width() // 2

    for row in range(
        max(0, first_row - 2),
        min(len(floor.map), last_row + 2),
    ):
        for column in range(
            max(0, first_column - 2),
            min(len(floor.map[0]), last_column + 2),
        ):
            if floor.map[row][column] == "#":
                continue

            seed = _position_seed(
                column,
                row,
                floor.visual_seed,
            )

            if seed % 100 >= _GRIME_FREQUENCY:
                continue

            offset_x = (
                (seed >> 8) % ACT_THREE_TILE_SIZE
                - ACT_THREE_TILE_SIZE // 2
            )
            offset_y = (
                (seed >> 16) % ACT_THREE_TILE_SIZE
                - ACT_THREE_TILE_SIZE // 2
            )

            center_x = (
                column * ACT_THREE_TILE_SIZE
                - camera_x
                + ACT_THREE_TILE_SIZE // 2
                + offset_x
            )
            center_y = (
                row * ACT_THREE_TILE_SIZE
                - camera_y
                + ACT_THREE_TILE_SIZE // 2
                + offset_y
            )

            surface.blit(
                grime,
                (
                    center_x - grime_radius,
                    center_y - grime_radius,
                ),
            )


def _draw_barrier_shadows(
    surface,
    barriers,
    camera_x,
    camera_y,
):
    horizontal, vertical, depth = (
        _barrier_shadow_surfaces(
            ACT_THREE_TILE_SIZE
        )
    )

    for first, second in barriers:
        first_column, first_row = first
        second_column, second_row = second

        if (
            first_row == second_row
            and abs(first_column - second_column) == 1
        ):
            boundary_x = max(
                first_column,
                second_column,
            ) * ACT_THREE_TILE_SIZE
            top = first_row * ACT_THREE_TILE_SIZE

            surface.blit(
                vertical,
                (
                    boundary_x - camera_x - depth,
                    top - camera_y,
                ),
            )

        elif (
            first_column == second_column
            and abs(first_row - second_row) == 1
        ):
            boundary_y = max(
                first_row,
                second_row,
            ) * ACT_THREE_TILE_SIZE
            left = first_column * ACT_THREE_TILE_SIZE

            surface.blit(
                horizontal,
                (
                    left - camera_x,
                    boundary_y - camera_y - depth,
                ),
            )


def draw_environment_grading(
    surface,
    floor,
    camera_x,
    camera_y,
    first_column,
    first_row,
    last_column,
    last_row,
):
    _draw_floor_grading(
        surface,
        floor,
        camera_x,
        camera_y,
        first_column,
        first_row,
        last_column,
        last_row,
    )
    _draw_barrier_shadows(
        surface,
        floor.barriers,
        camera_x,
        camera_y,
    )
