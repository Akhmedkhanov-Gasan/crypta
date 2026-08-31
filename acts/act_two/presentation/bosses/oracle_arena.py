import math
from functools import lru_cache

import pygame

from acts.act_two.presentation.bosses.oracle_combat_fx import (
    oracle_attack_lights,
)

from acts.act_two.presentation.bosses.oracle_intro import (
    oracle_boss_light,
    oracle_pillar_light,
    oracle_player_position,
)

from presentation.layout import (
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    PROJECT_ROOT,
)
from settings import TILE_SIZE


AMBIENT_DARKNESS = 242
PILLAR_LIGHT_RADIUS = 3.5
PLAYER_LIGHT_RADIUS = 2.6
BOSS_LIGHT_RADIUS = 3.8
BRAZIER_LIGHT_RADIUS = 3.0

PILLAR_LIGHT_STRENGTH = 240
PLAYER_LIGHT_STRENGTH = 210
BOSS_LIGHT_STRENGTH = 120
BRAZIER_LIGHT_STRENGTH = 230

FIRE_FRAME_MS = 140


@lru_cache(maxsize=1)
def _load_arena_sprites():
    root = (
        PROJECT_ROOT
        / "assets/sprites/act_2/bosses/oracle/arena"
    )
    sprites = {}

    for name in ("pillar", "fire_01", "fire_02", "fire_03"):
        source = pygame.image.load(
            str(root / f"{name}.png")
        ).convert_alpha()
        sprites[name] = pygame.transform.scale(
            source,
            (TILE_SIZE, TILE_SIZE),
        )

    return sprites


def draw_oracle_pillars(screen, floor, current_time):
    if not floor.has_oracle_gate:
        return

    sprites = _load_arena_sprites()

    for column, row in floor.boss_columns:
        if (column, row) not in floor.visible_cells:
            continue

        position = (
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
        )
        screen.blit(sprites["pillar"], position)

        level, flash = oracle_pillar_light(floor, column, row)
        if level <= 0:
            continue

        phase = column * 71 + row * 43
        frame = ((current_time + phase) // FIRE_FRAME_MS) % 3 + 1

        fire = sprites[f"fire_{frame:02d}"].copy()
        fire.set_alpha(round(255 * level))
        screen.blit(fire, position)

        if flash > 0:
            effect = pygame.Surface(
                (TILE_SIZE * 2, TILE_SIZE * 2),
                pygame.SRCALPHA,
            )
            center = (TILE_SIZE, TILE_SIZE)

            for radius, alpha in ((18, 12), (12, 22), (6, 35)):
                pygame.draw.circle(
                    effect,
                    (154, 97, 52, round(alpha * flash)),
                    center,
                    radius,
                )

            screen.blit(
                effect,
                (
                    position[0] - TILE_SIZE // 2,
                    position[1] - round(TILE_SIZE * 0.72),
                ),
            )


@lru_cache(maxsize=96)
def _light_surfaces(radius, strength, color):
    size = radius * 2 + 1
    center = (radius, radius)

    light = pygame.Surface((size, size), pygame.SRCALPHA)
    light.fill((0, 0, 0, 255))

    glow = pygame.Surface((size, size))
    glow.fill((0, 0, 0))

    for current_radius in range(radius, -1, -1):
        progress = min(
            1.0,
            (1.0 - current_radius / radius) / 0.75,
        )
        progress = progress * progress * (3.0 - 2.0 * progress)
        alpha = 255 - round(strength * progress)

        pygame.draw.circle(
            light,
            (0, 0, 0, alpha),
            center,
            current_radius,
        )
        pygame.draw.circle(
            glow,
            tuple(round(channel * progress) for channel in color),
            center,
            current_radius,
        )

    return light, glow


def draw_oracle_lighting(screen, floor, current_time):
    if not floor.has_oracle_gate:
        return

    map_size = (
        len(floor.map[0]) * TILE_SIZE,
        len(floor.map) * TILE_SIZE,
    )
    darkness = pygame.Surface(map_size, pygame.SRCALPHA)

    scene = floor.oracle_intro
    ambient = (
        AMBIENT_DARKNESS
        if scene is not None and scene.finished
        else 255
    )
    darkness.fill((0, 0, 0, ambient))

    player_column, player_row = oracle_player_position(floor)
    sources = [
        (
            player_column + 0.5,
            player_row + 0.5,
            PLAYER_LIGHT_RADIUS,
            PLAYER_LIGHT_STRENGTH,
            (0, 0, 0),
        ),
    ]

    for column, row in floor.boss_columns:
        if (column, row) not in floor.visible_cells:
            continue

        level, flash = oracle_pillar_light(floor, column, row)
        if level <= 0:
            continue

        phase = column * 0.7 + row * 1.3
        flicker = round(
            math.sin(current_time / 135 + phase) * 3
            + math.sin(current_time / 217 + phase) * 2
        )
        strength = round(
            (PILLAR_LIGHT_STRENGTH + flicker) * level
        )

        sources.append(
            (
                column + 0.5,
                row + 0.28,
                PILLAR_LIGHT_RADIUS,
                strength,
                (30, 13, 3),
            ),
        )

    for row, tiles in enumerate(floor.map):
        for column, tile in enumerate(tiles):
            if (
                tile != "B"
                or (column, row) not in floor.visible_cells
            ):
                continue

            sources.append(
                (
                    column + 0.5,
                    row + 0.35,
                    BRAZIER_LIGHT_RADIUS,
                    BRAZIER_LIGHT_STRENGTH,
                    (30, 13, 3),
                ),
            )

    boss_light = oracle_boss_light(floor)

    for enemy in floor.enemies:
        if (
            boss_light <= 0
            or enemy["type"] != "oracle"
            or enemy["health"] <= 0
            or (
                enemy["column"],
                enemy["row"],
            ) not in floor.visible_cells
        ):
            continue

        sources.append(
            (
                enemy["column"] + 0.5,
                enemy["row"] + 0.5,
                BOSS_LIGHT_RADIUS,
                round(BOSS_LIGHT_STRENGTH * boss_light),
                (8, 9, 15),
            ),
        )

    sources.extend(oracle_attack_lights(floor, current_time))

    for column, row, radius_tiles, strength, color in sources:
        radius = max(1, round(radius_tiles * TILE_SIZE))
        strength = max(0, min(255, strength))
        light, glow = _light_surfaces(radius, strength, color)

        position = (
            round(column * TILE_SIZE) - radius,
            round(row * TILE_SIZE) - radius,
        )

        darkness.blit(
            light,
            position,
            special_flags=pygame.BLEND_RGBA_MIN,
        )

        if color != (0, 0, 0):
            screen.blit(
                glow,
                (
                    MAP_OFFSET_X + position[0],
                    MAP_OFFSET_Y + position[1],
                ),
                special_flags=pygame.BLEND_RGB_ADD,
            )

    screen.blit(darkness, (MAP_OFFSET_X, MAP_OFFSET_Y))
