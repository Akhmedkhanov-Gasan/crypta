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

from acts.act_two.presentation.bosses.oracle_balance import (
    PHASE_TWO_PILLAR_BREAK_MS,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    oracle_phase_two_pillar_at,
    oracle_phase_two_pillar_flash,
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

    names = (
        "pillar",
        "pillar_cracked",
        "pillar_broken",
        "fire_01",
        "fire_02",
        "fire_03",
        "blackfire_01",
        "blackfire_02",
        "blackfire_03",
        "blackfire_04",
    )

    for name in names:
        source = pygame.image.load(
            str(root / f"{name}.png")
        ).convert_alpha()
        sprites[name] = pygame.transform.scale(
            source,
            (TILE_SIZE, TILE_SIZE),
        )

    return sprites



def _pillar_hit_state(pillar, current_time):
    started_at = pillar.hit_animation_started_at

    if started_at < 0:
        return 0, 0.0

    age = current_time - started_at

    if age < 0 or age >= 360:
        return 0, 0.0

    progress = age / 360
    strength = 1.0 - progress
    shake = round(
        math.sin(age / 12) * 4 * strength
    )

    return shake, strength


def _draw_pillar_hit_effect(
    screen,
    position,
    pillar,
    current_time,
):
    shake, strength = _pillar_hit_state(
        pillar,
        current_time,
    )

    if strength <= 0:
        return

    effect = pygame.Surface(
        (TILE_SIZE * 2, TILE_SIZE * 2),
        pygame.SRCALPHA,
    )
    center = (TILE_SIZE, TILE_SIZE)
    radius = round(
        TILE_SIZE * (0.25 + (1.0 - strength) * 0.65)
    )
    alpha = round(190 * strength)

    pygame.draw.circle(
        effect,
        (151, 38, 45, alpha),
        center,
        radius,
        3,
    )
    pygame.draw.line(
        effect,
        (
            235,
            198,
            181,
            round(230 * strength),
        ),
        (
            center[0] - 15,
            center[1] - 22,
        ),
        (
            center[0] + 12,
            center[1] + 16,
        ),
        4,
    )
    pygame.draw.line(
        effect,
        (
            125,
            24,
            34,
            round(210 * strength),
        ),
        (
            center[0] - 7,
            center[1] - 13,
        ),
        (
            center[0] + 18,
            center[1] + 7,
        ),
        3,
    )

    flash = pygame.Surface(
        (TILE_SIZE, TILE_SIZE),
        pygame.SRCALPHA,
    )
    flash.fill(
        (
            125,
            25,
            32,
            round(80 * strength),
        )
    )

    screen.blit(
        flash,
        (
            position[0] + shake,
            position[1],
        ),
        special_flags=pygame.BLEND_RGBA_ADD,
    )
    screen.blit(
        effect,
        (
            position[0] - TILE_SIZE // 2 + shake,
            position[1] - TILE_SIZE // 2,
        ),
    )


def draw_oracle_pillars(screen, floor, current_time):
    if not floor.has_oracle_gate:
        return

    sprites = _load_arena_sprites()
    phase_two = floor.oracle_phase_two
    global_flash = oracle_phase_two_pillar_flash(
        floor,
        current_time,
    )

    for column, row in floor.boss_columns:
        position_key = (column, row)

        if position_key not in floor.visible_cells:
            continue

        position = (
            MAP_OFFSET_X + column * TILE_SIZE,
            MAP_OFFSET_Y + row * TILE_SIZE,
        )
        pillar = oracle_phase_two_pillar_at(
            floor,
            position_key,
        )
        shake = 0

        if pillar is not None:
            shake, _strength = _pillar_hit_state(
                pillar,
                current_time,
            )

        render_position = (
            position[0] + shake,
            position[1],
        )

        if phase_two is None or pillar is None:
            screen.blit(
                sprites["pillar"],
                render_position,
            )

            level, flash = oracle_pillar_light(
                floor,
                column,
                row,
            )

            if level <= 0:
                continue

            phase = column * 71 + row * 43
            frame = (
                (current_time + phase)
                // FIRE_FRAME_MS
            ) % 3 + 1

            fire = sprites[f"fire_{frame:02d}"].copy()
            fire.set_alpha(round(255 * level))
            screen.blit(
                fire,
                render_position,
            )
        else:
            if pillar.health > 0:
                pillar_sprite = sprites["pillar"]
            else:
                broken_at = (
                    phase_two.pillar_break_started_at.get(
                        position_key,
                        -1,
                    )
                )
                age = (
                    current_time - broken_at
                    if broken_at >= 0
                    else PHASE_TWO_PILLAR_BREAK_MS
                )
                pillar_sprite = (
                    sprites["pillar_cracked"]
                    if age < PHASE_TWO_PILLAR_BREAK_MS
                    else sprites["pillar_broken"]
                )

            screen.blit(
                pillar_sprite,
                render_position,
            )

            _draw_pillar_hit_effect(
                screen,
                position,
                pillar,
                current_time,
            )

            if pillar.health <= 0:
                continue

            phase = column * 71 + row * 43
            frame = (
                (current_time + phase)
                // FIRE_FRAME_MS
            ) % 4 + 1

            screen.blit(
                sprites[f"blackfire_{frame:02d}"],
                render_position,
            )
            flash = global_flash

        if flash <= 0:
            continue

        effect = pygame.Surface(
            (TILE_SIZE * 2, TILE_SIZE * 2),
            pygame.SRCALPHA,
        )
        center = (TILE_SIZE, TILE_SIZE)

        for radius, alpha in (
            (22, 16),
            (15, 30),
            (8, 48),
        ):
            pygame.draw.circle(
                effect,
                (
                    132,
                    31,
                    42,
                    round(alpha * flash),
                ),
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
        position = (column, row)

        if position not in floor.visible_cells:
            continue

        phase_two_pillar = oracle_phase_two_pillar_at(
            floor,
            position,
        )

        if (
            phase_two_pillar is not None
            and phase_two_pillar.health <= 0
        ):
            continue

        if phase_two_pillar is not None:
            level = 1.0
            flash = oracle_phase_two_pillar_flash(
                floor,
                current_time,
            )
        else:
            level, flash = oracle_pillar_light(
                floor,
                column,
                row,
            )

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
