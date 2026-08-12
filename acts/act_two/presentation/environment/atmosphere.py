import math

import pygame

from acts.act_two.presentation.environment.tiles import (
    _tile_noise,
    _wall_is_exposed,
    wall_sprite_name,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def _draw_glow(screen, center, color, radius=18):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for current_radius in range(radius, 2, -3):
        progress = 1 - current_radius / radius
        alpha = round(5 + 21 * progress * progress)
        pygame.draw.circle(
            glow,
            (*color, alpha),
            (radius, radius),
            current_radius,
        )
    screen.blit(glow, (center[0] - radius, center[1] - radius))


def _draw_motes(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return
    column_count = len(dungeon_map[0])
    row_count = len(dungeon_map)
    map_width = column_count * TILE_SIZE
    map_height = row_count * TILE_SIZE
    motes = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    area_scale = (column_count * row_count) / (25 * 15)
    mote_count = round((24 + floor_number * 7) * area_scale)
    for mote_index in range(mote_count):
        noise = _tile_noise(
            mote_index,
            floor_number,
            visual_seed,
            211,
        )
        column = noise % column_count
        row = (noise // column_count) % row_count
        if dungeon_map[row][column] == "#":
            continue
        cycle = ((current_time / 13) + noise % 1201) % 1201 / 1201
        mote_x = (
            column * TILE_SIZE
            + 4
            + (noise // 19) % (TILE_SIZE - 8)
            + round(math.sin(current_time / 1150 + mote_index) * 4)
        )
        mote_y = (
            row * TILE_SIZE
            + TILE_SIZE
            - round(cycle * (TILE_SIZE + 12))
        )
        alpha = round(34 * math.sin(math.pi * cycle))
        color = (
            (91, 139, 144, alpha)
            if mote_index % 4
            else (152, 137, 119, alpha)
        )
        pygame.draw.circle(motes, color, (mote_x, mote_y), 1)
    screen.blit(motes, (MAP_OFFSET_X, MAP_OFFSET_Y))


def _draw_rune_glows(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return
    pulse = (math.sin(current_time / 480) + 1) / 2
    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "#" or not _wall_is_exposed(
                dungeon_map,
                column,
                row,
            ):
                continue
            noise = _tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 101,
            )
            if noise % 37 != 4:
                continue
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + 10 + noise % 12,
                MAP_OFFSET_Y + row * TILE_SIZE + 16,
            )
            _draw_glow(
                screen,
                center,
                (49, 119, 126),
                round(21 + pulse * 5),
            )
            pygame.draw.circle(
                screen,
                (93, 153, 155),
                center,
                1,
            )


def _draw_torch_lights(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return

    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "#":
                continue
            if wall_sprite_name(
                dungeon_map,
                column,
                row,
                visual_seed,
                floor_number,
            ) != "wall_torch":
                continue

            noise = _tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 613,
            )
            flicker = (
                math.sin(current_time / 92 + noise % 17)
                + math.sin(current_time / 157 + noise % 29) * 0.45
            )
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
                MAP_OFFSET_Y + row * TILE_SIZE + 12,
            )
            _draw_glow(
                screen,
                center,
                (196, 82, 24),
                round(50 + flicker * 3),
            )
            _draw_glow(
                screen,
                center,
                (244, 151, 47),
                round(27 + flicker * 2),
            )
            pygame.draw.circle(
                screen,
                (255, 201, 91),
                center,
                1,
            )


def _draw_brazier_lights(
    screen,
    dungeon_map,
    floor_number,
    visual_seed,
    current_time,
):
    if not dungeon_map:
        return

    for row, tiles in enumerate(dungeon_map):
        for column, tile in enumerate(tiles):
            if tile != "B":
                continue

            noise = _tile_noise(
                column,
                row,
                visual_seed,
                floor_number + 1181,
            )
            flicker = (
                math.sin(current_time / 106 + noise % 19)
                + math.sin(current_time / 181 + noise % 31) * 0.4
            )
            center = (
                MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
                MAP_OFFSET_Y + row * TILE_SIZE + 12,
            )
            _draw_glow(
                screen,
                center,
                (175, 61, 19),
                round(62 + flicker * 4),
            )
            _draw_glow(
                screen,
                center,
                (242, 131, 37),
                round(34 + flicker * 2),
            )
            pygame.draw.circle(screen, (255, 215, 109), center, 2)


def draw_atmosphere(
    screen,
    player_column,
    player_row,
    dungeon_map=None,
    floor_number=1,
    visual_seed=0,
    current_time=0,
):
    map_width = len(dungeon_map[0]) * TILE_SIZE
    map_height = len(dungeon_map) * TILE_SIZE

    player_center = (
        player_column * TILE_SIZE + TILE_SIZE // 2,
        player_row * TILE_SIZE + TILE_SIZE // 2,
    )
    darkness = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    darkness.fill((3, 6, 11, 76 + (floor_number - 1) * 10))
    for radius, alpha in ((146, 54), (112, 38), (78, 21), (46, 8)):
        pygame.draw.circle(
            darkness,
            (8, 13, 18, alpha),
            player_center,
            radius,
        )
    screen.blit(darkness, (MAP_OFFSET_X, MAP_OFFSET_Y))

    _draw_torch_lights(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )
    _draw_brazier_lights(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )

    _draw_rune_glows(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )

    world_player_center = (
        MAP_OFFSET_X + player_center[0],
        MAP_OFFSET_Y + player_center[1],
    )
    _draw_glow(screen, world_player_center, (55, 102, 111), 62)

    fog = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
    for band_index in range(5):
        noise = _tile_noise(
            band_index,
            floor_number,
            visual_seed,
            307,
        )
        drift = round(
            math.sin(current_time / 2200 + band_index * 1.7) * 34
        )
        fog_y = 52 + (noise % max(1, map_height - 104))
        fog_x = -90 + (noise % 130) + drift
        pygame.draw.ellipse(
            fog,
            (53, 69, 72, 8 + floor_number * 2),
            (fog_x, fog_y, 360 + noise % 150, 34 + noise % 24),
        )
        pygame.draw.ellipse(
            fog,
            (73, 78, 80, 5 + floor_number),
            (fog_x + 230, fog_y + 11, 390, 28),
        )
    screen.blit(fog, (MAP_OFFSET_X, MAP_OFFSET_Y))

    _draw_motes(
        screen,
        dungeon_map,
        floor_number,
        visual_seed,
        current_time,
    )
