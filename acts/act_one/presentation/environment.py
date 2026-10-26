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
    branch_direction = (
        -1
        if value % 2
        else 1
    )
    branch_end = (
        middle_x + branch_direction * (
            2 + value // 23 % 3
        ),
        min(
            y + TILE_SIZE - 4,
            middle_y + 2 + value // 29 % 3,
        ),
    )

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
    pygame.draw.aaline(
        screen,
        color,
        (middle_x, middle_y),
        branch_end,
    )


def _draw_floor_decor(screen, rectangle, value):
    x = rectangle.x
    y = rectangle.y
    detail = value % 113

    if detail in (7, 71):
        puddle = pygame.Surface(
            (TILE_SIZE, TILE_SIZE),
            pygame.SRCALPHA,
        )
        puddle_x = 4 + value // 17 % 6
        puddle_y = 17 + value // 31 % 4
        puddle_width = 14 + value // 43 % 5

        pygame.draw.ellipse(
            puddle,
            (10, 20, 21, 88),
            (
                puddle_x,
                puddle_y,
                puddle_width,
                6,
            ),
        )
        pygame.draw.ellipse(
            puddle,
            (24, 36, 36, 56),
            (
                puddle_x + 3,
                puddle_y + 1,
                max(5, puddle_width - 7),
                3,
            ),
        )
        pygame.draw.aaline(
            puddle,
            (69, 76, 75, 52),
            (
                puddle_x + 4,
                puddle_y + 2,
            ),
            (
                puddle_x
                + puddle_width
                - 5,
                puddle_y + 2,
            ),
        )
        screen.blit(
            puddle,
            rectangle,
        )
    elif detail in (19, 83):
        debris_x = x + 7 + value // 17 % 8
        debris_y = y + 18 + value // 29 % 5

        pygame.draw.polygon(
            screen,
            (43, 40, 38),
            (
                (
                    debris_x,
                    debris_y + 2,
                ),
                (
                    debris_x + 4,
                    debris_y,
                ),
                (
                    debris_x + 6,
                    debris_y + 3,
                ),
                (
                    debris_x + 2,
                    debris_y + 5,
                ),
            ),
        )
        pygame.draw.line(
            screen,
            (60, 52, 43),
            (
                debris_x + 8,
                debris_y + 4,
            ),
            (
                debris_x + 13,
                debris_y + 1,
            ),
        )
        pygame.draw.line(
            screen,
            (27, 25, 24),
            (
                debris_x + 10,
                debris_y + 5,
            ),
            (
                debris_x + 14,
                debris_y + 6,
            ),
        )
    elif detail in (43, 101):
        bone_start = (
            x + 7 + value // 19 % 6,
            y + 22 + value // 37 % 3,
        )
        bone_end = (
            bone_start[0] + 8,
            bone_start[1] - 3,
        )
        bone_color = (91, 87, 76)
        bone_shadow = (48, 47, 43)

        pygame.draw.line(
            screen,
            bone_shadow,
            (
                bone_start[0] + 1,
                bone_start[1] + 1,
            ),
            (
                bone_end[0] + 1,
                bone_end[1] + 1,
            ),
            2,
        )
        pygame.draw.line(
            screen,
            bone_color,
            bone_start,
            bone_end,
            2,
        )
        pygame.draw.circle(
            screen,
            bone_color,
            bone_start,
            2,
        )
        pygame.draw.circle(
            screen,
            bone_color,
            bone_end,
            2,
        )
        pygame.draw.line(
            screen,
            (69, 66, 59),
            (
                bone_start[0] + 11,
                bone_start[1] + 2,
            ),
            (
                bone_start[0] + 15,
                bone_start[1] + 4,
            ),
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

    _draw_floor_decor(
        screen,
        rectangle,
        value,
    )


def _wall_is_exposed(
    dungeon_map,
    column,
    row,
):
    return any(
        0 <= row + row_change < len(dungeon_map)
        and 0 <= column + column_change < len(
            dungeon_map[row + row_change]
        )
        and dungeon_map[
            row + row_change
        ][
            column + column_change
        ] not in ("#", "S")
        for column_change, row_change in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        )
    )


def _wall_has_torch(value):
    return value % 53 == 11


def _draw_wall_torch(
    screen,
    rectangle,
    value,
):
    x = rectangle.x + 16
    y = rectangle.y + 16
    lean = value // 19 % 3 - 1

    pygame.draw.line(
        screen,
        (24, 23, 25),
        (
            x,
            y + 2,
        ),
        (
            x + lean,
            y + 10,
        ),
        3,
    )
    pygame.draw.line(
        screen,
        (77, 55, 35),
        (
            x,
            y,
        ),
        (
            x + lean,
            y + 8,
        ),
        2,
    )
    pygame.draw.line(
        screen,
        (64, 63, 65),
        (
            x - 4,
            y + 7,
        ),
        (
            x + 4,
            y + 7,
        ),
        2,
    )
    pygame.draw.polygon(
        screen,
        (111, 43, 20),
        (
            (
                x - 3,
                y,
            ),
            (
                x - 1,
                y - 7,
            ),
            (
                x + 1,
                y - 4,
            ),
            (
                x + 3,
                y - 1,
            ),
            (
                x + 1,
                y + 3,
            ),
            (
                x - 2,
                y + 2,
            ),
        ),
    )
    pygame.draw.polygon(
        screen,
        (181, 101, 39),
        (
            (
                x - 1,
                y,
            ),
            (
                x,
                y - 4,
            ),
            (
                x + 2,
                y,
            ),
            (
                x,
                y + 2,
            ),
        ),
    )


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

    exposed = _wall_is_exposed(
        dungeon_map,
        column,
        row,
    )
    has_torch = (
        exposed
        and _wall_has_torch(value)
    )

    if value % 9 == 0:
        _draw_crack(
            screen,
            x,
            y,
            value,
            (17, 17, 20),
        )

    if (
        exposed
        and value % 17 == 0
        and not has_torch
    ):
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

    if has_torch:
        _draw_wall_torch(
            screen,
            rectangle,
            value,
        )

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


def _draw_wall_torch_light(
    screen,
    dungeon_map,
    column,
    row,
    value,
    current_time,
):
    flicker = (
        math.sin(
            current_time / 170
            + value % 19
        )
        + math.sin(
            current_time / 73
            + value % 7
        )
        * 0.35
    )
    radius = 23 + round(flicker)
    size = radius * 2
    light = pygame.Surface(
        (size, size),
    )
    center = (
        radius,
        radius,
    )

    pygame.draw.circle(
        light,
        (7, 4, 2),
        center,
        radius,
    )
    pygame.draw.circle(
        light,
        (13, 7, 3),
        center,
        max(1, radius - 7),
    )
    pygame.draw.circle(
        light,
        (19, 10, 4),
        center,
        max(1, radius - 14),
    )

    source_center = (
        MAP_OFFSET_X
        + column * TILE_SIZE
        + TILE_SIZE // 2,
        MAP_OFFSET_Y
        + row * TILE_SIZE
        + TILE_SIZE // 2,
    )
    light_rectangle = light.get_rect(
        center=source_center,
    )
    allowed_positions = [
        (
            column,
            row,
        )
    ]

    for column_change, row_change in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ):
        target_column = (
            column + column_change
        )
        target_row = (
            row + row_change
        )

        if not (
            0 <= target_row < len(dungeon_map)
            and 0 <= target_column < len(
                dungeon_map[target_row]
            )
        ):
            continue

        if dungeon_map[
            target_row
        ][
            target_column
        ] in ("#", "S"):
            continue

        allowed_positions.append(
            (
                target_column,
                target_row,
            )
        )

    for target_column, target_row in allowed_positions:
        tile_rectangle = pygame.Rect(
            MAP_OFFSET_X
            + target_column * TILE_SIZE,
            MAP_OFFSET_Y
            + target_row * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        clipped = light_rectangle.clip(
            tile_rectangle
        )

        if clipped.width <= 0 or clipped.height <= 0:
            continue

        source_rectangle = pygame.Rect(
            clipped.x - light_rectangle.x,
            clipped.y - light_rectangle.y,
            clipped.width,
            clipped.height,
        )
        screen.blit(
            light,
            clipped.topleft,
            source_rectangle,
            special_flags=pygame.BLEND_RGB_ADD,
        )


def _draw_wall_torch_lights(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    for row, map_row in enumerate(dungeon_map):
        for column, tile in enumerate(map_row):
            if tile not in ("#", "S"):
                continue

            value = _noise(
                column,
                row,
                visual_seed,
                floor_number,
            )

            if (
                not _wall_has_torch(value)
                or not _wall_is_exposed(
                    dungeon_map,
                    column,
                    row,
                )
            ):
                continue

            _draw_wall_torch_light(
                screen,
                dungeon_map,
                column,
                row,
                value,
                current_time,
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

    _draw_wall_torch_lights(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )

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


@lru_cache(maxsize=1)
def _warden_light_texture():
    radius = round(TILE_SIZE * 1.35)
    size = radius * 2
    center = (radius, radius)
    light = pygame.Surface((size, size))

    for layer_index in range(24):
        progress = layer_index / 23
        current_radius = round(
            radius
            + (12 - radius) * progress
        )
        intensity = round(
            1 + 15 * progress ** 1.7
        )
        pygame.draw.circle(
            light,
            (
                intensity,
                round(intensity * 0.28),
                round(intensity * 0.48),
            ),
            center,
            current_radius,
        )

    return pygame.transform.gaussian_blur(
        light,
        9,
    )


@lru_cache(maxsize=1)
def _warden_reveal_texture():
    radius = round(TILE_SIZE * 1.45)
    size = radius * 2
    center = (radius, radius)
    reveal = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    for layer_index in range(32):
        progress = layer_index / 31
        current_radius = round(
            radius
            + (14 - radius) * progress
        )
        strength = round(
            4 + 186 * progress ** 1.35
        )
        pygame.draw.circle(
            reveal,
            (0, 0, 0, strength),
            center,
            current_radius,
        )

    return pygame.transform.gaussian_blur(
        reveal,
        9,
    )


def _warden_light_data(floor):
    if not floor.boss_fight_started:
        return None

    warden = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.type == "warden"
            and enemy.health > 0
        ),
        None,
    )

    if warden is None:
        return None

    state = getattr(
        floor,
        "act_one_warden_intro",
        None,
    )
    strength = 1.0

    if (
        state is not None
        and state.started
        and not state.finished
    ):
        strength = max(
            0.0,
            min(
                1.0,
                state.elapsed / 1600,
            ),
        )

    center = (
        warden.column * TILE_SIZE
        + TILE_SIZE // 2,
        warden.row * TILE_SIZE
        + TILE_SIZE // 2,
    )
    return center, strength


def _draw_warden_light(
    screen,
    floor,
    current_time,
):
    light_data = _warden_light_data(floor)

    if light_data is None:
        return None

    center, strength = light_data
    light = _warden_light_texture()
    pulse = (
        0.92
        + math.sin(current_time / 260) * 0.08
    )
    light.set_alpha(
        round(255 * strength * pulse)
    )
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
    return center, strength


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


def _draw_warden_visibility_gradient(
    fog,
    center,
    strength,
):
    reveal = _warden_reveal_texture()
    reveal.set_alpha(
        round(255 * strength)
    )
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
    warden_light = _draw_warden_light(
        screen,
        floor,
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

    if warden_light is not None:
        (
            warden_light_center,
            warden_light_strength,
        ) = warden_light
        _draw_warden_visibility_gradient(
            fog,
            warden_light_center,
            warden_light_strength,
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
