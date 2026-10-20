from functools import lru_cache
import math

import pygame

from acts.act_one.presentation.player import (
    act_one_player_movement_offset,
)
from acts.act_one.settings import (
    FOG_EXPLORED_ALPHA,
    FOG_UNEXPLORED_ALPHA,
    VISION_RADIUS_TILES,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


FLOOR_BASE = (24, 24, 27)
FLOOR_LIGHT = (39, 38, 40)
FLOOR_SHADOW = (13, 14, 17)
WALL_BASE = (44, 43, 46)
WALL_LIGHT = (66, 63, 64)
WALL_SHADOW = (15, 16, 19)
MORTAR_COLOR = (24, 24, 27)
DAMP_COLOR = (21, 31, 30)
IRON_COLOR = (48, 47, 49)


def _noise(column, row, seed, salt=0):
    value = (
        column * 374761393
        + row * 668265263
        + seed * 69069
        + salt * 362437
    )
    value = (value ^ (value >> 13)) * 1274126177
    return value ^ (value >> 16)


def _draw_crack(screen, x, y, value, color):
    start_x = x + 6 + value % 17
    start_y = y + 5 + value // 7 % 14
    middle_x = start_x + value // 13 % 7 - 3
    middle_y = start_y + 5
    end_x = middle_x + value // 19 % 7 - 3
    end_y = min(y + TILE_SIZE - 4, middle_y + 6)

    pygame.draw.aaline(
        screen,
        color,
        (start_x, start_y),
        (middle_x, middle_y),
    )
    pygame.draw.aaline(
        screen,
        color,
        (middle_x, middle_y),
        (end_x, end_y),
    )


def _draw_floor_tile(screen, rectangle, column, row, value):
    variation = value % 11
    base_shift = variation % 4
    base_color = tuple(
        channel + base_shift
        for channel in FLOOR_BASE
    )
    pygame.draw.rect(screen, base_color, rectangle)

    x = rectangle.x
    y = rectangle.y
    seam_offset = 1 + value // 17 % 4

    pygame.draw.line(
        screen,
        FLOOR_LIGHT,
        (x + 2, y + seam_offset),
        (x + TILE_SIZE - 3, y + seam_offset),
    )
    pygame.draw.line(
        screen,
        FLOOR_SHADOW,
        (x + 2, y + TILE_SIZE - 2),
        (x + TILE_SIZE - 3, y + TILE_SIZE - 2),
        2,
    )

    if (column + row) % 2:
        pygame.draw.line(
            screen,
            (31, 30, 33),
            (x + TILE_SIZE // 2, y + 3),
            (x + TILE_SIZE // 2, y + TILE_SIZE - 4),
        )

    if value % 7 == 0:
        _draw_crack(
            screen,
            x,
            y,
            value,
            (10, 11, 13),
        )

    if value % 13 == 0:
        stain = pygame.Surface(
            (TILE_SIZE, TILE_SIZE),
            pygame.SRCALPHA,
        )
        pygame.draw.ellipse(
            stain,
            (16, 24, 23, 74),
            (
                5 + value % 6,
                13 + value // 11 % 5,
                18,
                8,
            ),
        )
        screen.blit(stain, rectangle)


def _draw_wall_tile(
    screen,
    rectangle,
    dungeon_map,
    column,
    row,
    value,
):
    x = rectangle.x
    y = rectangle.y
    base_shift = value % 5
    base_color = tuple(
        channel + base_shift
        for channel in WALL_BASE
    )

    pygame.draw.rect(screen, base_color, rectangle)
    pygame.draw.line(
        screen,
        WALL_LIGHT,
        (x + 1, y + 1),
        (x + TILE_SIZE - 2, y + 1),
        2,
    )
    pygame.draw.line(
        screen,
        WALL_SHADOW,
        (x + 1, y + TILE_SIZE - 2),
        (x + TILE_SIZE - 2, y + TILE_SIZE - 2),
        3,
    )

    horizontal_seam = y + 10 + value % 8
    pygame.draw.line(
        screen,
        MORTAR_COLOR,
        (x + 2, horizontal_seam),
        (x + TILE_SIZE - 3, horizontal_seam),
        2,
    )

    upper_seam = x + 8 + value // 7 % 14
    lower_seam = x + 7 + value // 17 % 16
    pygame.draw.line(
        screen,
        MORTAR_COLOR,
        (upper_seam, y + 2),
        (upper_seam, horizontal_seam),
    )
    pygame.draw.line(
        screen,
        MORTAR_COLOR,
        (lower_seam, horizontal_seam),
        (lower_seam, y + TILE_SIZE - 3),
    )

    exposed = any(
        0 <= row + row_change < len(dungeon_map)
        and 0 <= column + column_change < len(
            dungeon_map[row + row_change]
        )
        and dungeon_map[row + row_change][
            column + column_change
        ] != "#"
        for column_change, row_change in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        )
    )

    if value % 9 == 0:
        _draw_crack(
            screen,
            x,
            y,
            value,
            (17, 17, 20),
        )

    if exposed and value % 17 == 0:
        pygame.draw.line(
            screen,
            IRON_COLOR,
            (x + 10, y + 4),
            (x + 10, y + 25),
            2,
        )
        pygame.draw.circle(
            screen,
            (75, 71, 69),
            (x + 10, y + 8),
            3,
            1,
        )
        pygame.draw.circle(
            screen,
            (30, 29, 31),
            (x + 10, y + 24),
            3,
            1,
        )

    if value % 19 == 0:
        damp = pygame.Surface(
            (TILE_SIZE, TILE_SIZE),
            pygame.SRCALPHA,
        )
        pygame.draw.polygon(
            damp,
            (*DAMP_COLOR, 105),
            (
                (3, 2),
                (TILE_SIZE - 4, 2),
                (TILE_SIZE - 8, 12),
                (18, 16),
                (7, 11),
            ),
        )
        screen.blit(damp, rectangle)


def draw_act_one_dungeon(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
):
    depth = max(0, floor_number - 1)

    for row, map_row in enumerate(dungeon_map):
        for column, tile in enumerate(map_row):
            rectangle = pygame.Rect(
                MAP_OFFSET_X + column * TILE_SIZE,
                MAP_OFFSET_Y + row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            )
            value = _noise(
                column,
                row,
                visual_seed,
                floor_number,
            )

            if tile in ("#", "S"):
                _draw_wall_tile(
                    screen,
                    rectangle,
                    dungeon_map,
                    column,
                    row,
                    value,
                )
            else:
                _draw_floor_tile(
                    screen,
                    rectangle,
                    column,
                    row,
                    value,
                )

            border_color = (
                max(6, 15 - depth),
                max(7, 16 - depth),
                max(9, 18 - depth),
            )
            pygame.draw.rect(
                screen,
                border_color,
                rectangle,
                1,
            )


def draw_act_one_ambient(
    screen,
    player_column,
    player_row,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return

    map_width = len(dungeon_map[0]) * TILE_SIZE
    map_height = len(dungeon_map) * TILE_SIZE
    depth = max(0, floor_number - 1)
    veil = pygame.Surface(
        (map_width, map_height),
        pygame.SRCALPHA,
    )
    veil.fill((2, 4, 7, 30 + depth * 8))

    for inset, alpha, width in (
        (0, 72, 22),
        (20, 42, 18),
        (38, 22, 14),
    ):
        pygame.draw.rect(
            veil,
            (1, 2, 4, alpha + depth * 4),
            (
                inset,
                inset,
                map_width - inset * 2,
                map_height - inset * 2,
            ),
            width=width,
        )

    screen.blit(veil, (MAP_OFFSET_X, MAP_OFFSET_Y))

    particles = pygame.Surface(
        (map_width, map_height),
        pygame.SRCALPHA,
    )
    particle_count = 24 + floor_number * 4

    for index in range(particle_count):
        value = _noise(index, floor_number, visual_seed, 41)
        column = value % len(dungeon_map[0])
        row = value // len(dungeon_map[0]) % len(dungeon_map)

        if dungeon_map[row][column] in ("#", "S"):
            continue

        cycle = (
            current_time * 0.000035
            + (value % 1000) / 1000
        ) % 1.0
        x = (
            column * TILE_SIZE
            + 4
            + value // 13 % (TILE_SIZE - 8)
            + round(math.sin(current_time / 850 + index) * 2)
        )
        y = (
            row * TILE_SIZE
            + TILE_SIZE
            - round(cycle * (TILE_SIZE + 12))
        )
        alpha = round(30 * math.sin(math.pi * cycle))

        pygame.draw.circle(
            particles,
            (151, 139, 120, alpha),
            (x, y),
            1,
        )

    screen.blit(
        particles,
        (MAP_OFFSET_X, MAP_OFFSET_Y),
    )

    return


def _light_polygon(center, radius, roughness):
    points = []

    for index in range(40):
        angle = math.tau * index / 40
        ripple = (
            math.sin(angle * 3 + 0.45) * roughness
            + math.sin(angle * 7 - 1.20) * roughness * 0.38
            + math.sin(angle * 11 + 2.10) * roughness * 0.16
        )
        current_radius = max(1, radius + ripple)
        points.append(
            (
                round(
                    center[0]
                    + math.cos(angle) * current_radius
                ),
                round(
                    center[1]
                    + math.sin(angle) * current_radius
                ),
            )
        )

    return points


@lru_cache(maxsize=1)
def _soft_light_texture():
    outer_radius = round(
        VISION_RADIUS_TILES * TILE_SIZE * 0.76
    )
    margin = 18
    size = (outer_radius + margin) * 2
    center = (size // 2, size // 2)
    light = pygame.Surface((size, size))
    layer_count = 30

    for layer_index in range(layer_count):
        progress = layer_index / (layer_count - 1)
        radius = round(
            outer_radius
            + (22 - outer_radius) * progress
        )
        intensity = round(
            1 + 13 * progress ** 1.7
        )
        pygame.draw.polygon(
            light,
            (
                round(intensity * 0.48),
                round(intensity * 0.68),
                intensity,
            ),
            _light_polygon(
                center,
                radius,
                2.0 + radius * 0.022,
            ),
        )

    return pygame.transform.gaussian_blur(
        light,
        10,
    )


@lru_cache(maxsize=1)
def _visibility_reveal_texture():
    outer_radius = round(
        VISION_RADIUS_TILES * TILE_SIZE
    )
    margin = 18
    size = (outer_radius + margin) * 2
    center = (size // 2, size // 2)
    reveal = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    layer_count = 48

    for layer_index in range(layer_count):
        progress = layer_index / (layer_count - 1)
        radius = round(
            outer_radius
            + (28 - outer_radius) * progress
        )
        strength = round(
            6 + 249 * progress ** 1.16
        )
        pygame.draw.polygon(
            reveal,
            (0, 0, 0, strength),
            _light_polygon(
                center,
                radius,
                2.6 + radius * 0.023,
            ),
        )

    return pygame.transform.gaussian_blur(
        reveal,
        10,
    )


def _draw_soft_light(
    screen,
    center,
    current_time,
):
    light = _soft_light_texture()
    pulse = 238 + round(
        math.sin(current_time / 310) * 8
    )
    light.set_alpha(pulse)
    screen.blit(
        light,
        (
            MAP_OFFSET_X
            + center[0]
            - light.get_width() // 2,
            MAP_OFFSET_Y
            + center[1]
            - light.get_height() // 2,
        ),
        special_flags=pygame.BLEND_RGB_ADD,
    )


def _draw_visibility_gradient(
    fog,
    center,
):
    reveal = _visibility_reveal_texture()
    fog.blit(
        reveal,
        (
            center[0] - reveal.get_width() // 2,
            center[1] - reveal.get_height() // 2,
        ),
        special_flags=pygame.BLEND_RGBA_SUB,
    )


def draw_act_one_fog_of_war(
    screen,
    act_number,
    floor,
    current_time,
    movement_started_at=0,
    movement_origin=None,
):
    if act_number != 1:
        return

    map_width = len(floor.map[0]) * TILE_SIZE
    map_height = len(floor.map) * TILE_SIZE
    movement_offset = act_one_player_movement_offset(
        floor.player_column,
        floor.player_row,
        movement_origin,
        current_time,
        movement_started_at,
    )
    player_center = (
        floor.player_column * TILE_SIZE
        + TILE_SIZE // 2
        + movement_offset[0],
        floor.player_row * TILE_SIZE
        + TILE_SIZE // 2
        + movement_offset[1],
    )

    _draw_soft_light(
        screen,
        player_center,
        current_time,
    )

    fog = pygame.Surface(
        (map_width, map_height),
        pygame.SRCALPHA,
    )
    fog.fill((2, 4, 7, FOG_UNEXPLORED_ALPHA))

    for column, row in floor.explored_cells:
        pygame.draw.rect(
            fog,
            (2, 4, 7, FOG_EXPLORED_ALPHA),
            (
                column * TILE_SIZE,
                row * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
            ),
        )

    _draw_visibility_gradient(
        fog,
        player_center,
    )

    for row in range(len(floor.map)):
        for column in range(len(floor.map[row])):
            position = (column, row)

            if position in floor.visible_cells:
                continue

            pygame.draw.rect(
                fog,
                (
                    2,
                    4,
                    7,
                    (
                        FOG_EXPLORED_ALPHA
                        if position in floor.explored_cells
                        else FOG_UNEXPLORED_ALPHA
                    ),
                ),
                (
                    column * TILE_SIZE,
                    row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                ),
            )

    screen.blit(
        fog,
        (MAP_OFFSET_X, MAP_OFFSET_Y),
    )
