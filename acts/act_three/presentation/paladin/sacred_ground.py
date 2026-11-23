import math
import random

import pygame

from acts.act_three.presentation.player_motion import (
    assassin_walk_direction,
)
from acts.act_three.presentation.view import _view_position
from acts.act_three.settings import (
    PALADIN_SACRED_GROUND_CAST_MS,
    PALADIN_SACRED_GROUND_IMPACT_MS,
    PALADIN_SACRED_GROUND_LIGHTNING_MS,
)


def paladin_sacred_ground_sprite(
    player,
    assets,
    current_time,
):
    started_at = player.paladin_sacred_ground_started_at
    elapsed = current_time - started_at

    if (
        player.subclass != "paladin"
        or started_at <= 0
        or not 0 <= elapsed < PALADIN_SACRED_GROUND_CAST_MS
    ):
        return None

    direction = assassin_walk_direction(
        player.facing_direction
    )
    frame_boundaries = (
        0.10,
        0.21,
        0.33,
        0.46,
        0.60,
        0.76,
        0.90,
    )
    progress = elapsed / PALADIN_SACRED_GROUND_CAST_MS
    if player.act_three.paladin_ultimate_rune == "rune_of_fervent_crusade":
        if elapsed >= PALADIN_SACRED_GROUND_IMPACT_MS:
            return None
        frame = min(2, int(progress * 5))
        return assets[f"player_paladin_sacred_ground_{direction}_{frame}"]
    frame = sum(
        progress >= boundary
        for boundary in frame_boundaries
    )

    return assets[
        f"player_paladin_sacred_ground_{direction}_{frame}"
    ]


def _sacred_ground_local_position(
    position,
    minimum_column,
    minimum_row,
    tile_size,
):
    return (
        (position[0] - minimum_column) * tile_size,
        (position[1] - minimum_row) * tile_size,
    )


def _sacred_ground_patch(layer, left, top, tile_size, seed, pulse):
    from acts.act_three.presentation.berserker.effect_brushes import mist

    generator = random.Random(seed)
    center = left + tile_size * 0.5, top + tile_size * 0.5
    for index in range(4):
        point = (center[0] + generator.uniform(-0.25, 0.25) * tile_size,
                 center[1] + generator.uniform(-0.25, 0.25) * tile_size)
        mist(layer, point, tile_size * 0.4, (22, 15, 28), 0.85)
        mist(layer, point, tile_size * 0.23, (69, 47, 79), 0.3 + pulse * 0.12)
    for index in range(5):
        angle = generator.random() * math.tau
        length = generator.uniform(0.22, 0.46) * tile_size
        origin = (center[0] + generator.uniform(-0.15, 0.15) * tile_size,
                  center[1] + generator.uniform(-0.15, 0.15) * tile_size)
        middle = (origin[0] + math.cos(angle) * length * 0.5,
                  origin[1] + math.sin(angle) * length * 0.5)
        end = (origin[0] + math.cos(angle + 0.3) * length,
               origin[1] + math.sin(angle + 0.3) * length)
        points = [(round(x), round(y)) for x, y in (origin, middle, end)]
        pygame.draw.lines(layer, (15, 11, 19, 165), False, points, 4)
        pygame.draw.aalines(layer, (132, 94, 128, round(95 + pulse * 35)), False, points)
        branch = (middle[0] + math.cos(angle - 0.8) * length * 0.4,
                  middle[1] + math.sin(angle - 0.8) * length * 0.4)
        pygame.draw.aaline(layer, (110, 82, 111, round(85 + pulse * 25)), middle, branch)


def draw_paladin_sacred_ground_cells(
    surface,
    positions,
    anchor,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    if not positions or anchor is None:
        return

    minimum_column = min(
        position[0]
        for position in positions
    )
    maximum_column = max(
        position[0]
        for position in positions
    )
    minimum_row = min(
        position[1]
        for position in positions
    )
    maximum_row = max(
        position[1]
        for position in positions
    )

    width = (
        maximum_column - minimum_column + 1
    ) * tile_size
    height = (
        maximum_row - minimum_row + 1
    ) * tile_size
    layer = pygame.Surface(
        (width, height),
        pygame.SRCALPHA,
    )
    pulse = (
        math.sin(current_time * 0.0042) + 1
    ) / 2

    for column, row in positions:
        local_left, local_top = (
            _sacred_ground_local_position(
                (column, row),
                minimum_column,
                minimum_row,
                tile_size,
            )
        )
        seed = (
            column * 92821
            + row * 68917
        )
        _sacred_ground_patch(
            layer,
            local_left,
            local_top,
            tile_size,
            seed,
            pulse,
        )

    world_position = _view_position(
        minimum_column,
        minimum_row,
        camera_x,
        camera_y,
    )
    surface.blit(
        layer,
        world_position,
    )


def draw_paladin_sacred_ground_cast_effect(
    surface,
    player,
    player_position,
    current_time,
    tile_size,
):
    started_at = player.paladin_sacred_ground_started_at
    elapsed = current_time - started_at

    if (
        player.subclass != "paladin"
        or started_at <= 0
        or not 0 <= elapsed < PALADIN_SACRED_GROUND_CAST_MS
    ):
        return

    if player.act_three.paladin_ultimate_rune == "rune_of_fervent_crusade":
        from acts.act_three.presentation.paladin.rune_effects import draw_crusade_activation

        draw_crusade_activation(surface, player_position, elapsed, PALADIN_SACRED_GROUND_CAST_MS, tile_size)
        return
    layer = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    sword_point = (
        round(player_position[0] + tile_size * 0.5),
        round(player_position[1] + tile_size * 0.78),
    )

    if elapsed < PALADIN_SACRED_GROUND_IMPACT_MS:
        progress = (
            elapsed / PALADIN_SACRED_GROUND_IMPACT_MS
        )
        pull = progress * progress
        intensity = round(
            55 + progress * 160
        )
        source_offsets = (
            (-1.30, -0.72),
            (-1.05, 0.12),
            (-0.62, -1.18),
            (0.62, -1.18),
            (1.05, 0.12),
            (1.30, -0.72),
        )

        pygame.draw.polygon(
            layer,
            (
                10,
                8,
                9,
                round(45 + progress * 75),
            ),
            (
                (
                    sword_point[0] - round(tile_size * 0.52),
                    sword_point[1] + round(tile_size * 0.18),
                ),
                (
                    sword_point[0],
                    sword_point[1] - round(tile_size * 0.16),
                ),
                (
                    sword_point[0] + round(tile_size * 0.52),
                    sword_point[1] + round(tile_size * 0.18),
                ),
                (
                    sword_point[0],
                    sword_point[1] + round(tile_size * 0.34),
                ),
            ),
        )

        for index, offset in enumerate(source_offsets):
            source = (
                sword_point[0] + round(offset[0] * tile_size),
                sword_point[1] + round(offset[1] * tile_size),
            )
            current = (
                round(
                    source[0]
                    + (sword_point[0] - source[0]) * pull
                ),
                round(
                    source[1]
                    + (sword_point[1] - source[1]) * pull
                ),
            )
            direction_x = sword_point[0] - current[0]
            direction_y = sword_point[1] - current[1]
            length = max(
                1.0,
                math.hypot(direction_x, direction_y),
            )
            normal_x = -direction_y / length
            normal_y = direction_x / length
            width = 5 if index % 2 == 0 else 3
            tail_ratio = max(
                0.0,
                pull - 0.18,
            )
            tail = (
                round(
                    source[0]
                    + (sword_point[0] - source[0])
                    * tail_ratio
                ),
                round(
                    source[1]
                    + (sword_point[1] - source[1])
                    * tail_ratio
                ),
            )

            pygame.draw.polygon(
                layer,
                (
                    18,
                    14,
                    15,
                    intensity,
                ),
                (
                    (
                        round(tail[0] + normal_x * width),
                        round(tail[1] + normal_y * width),
                    ),
                    (
                        round(current[0] + normal_x * 2),
                        round(current[1] + normal_y * 2),
                    ),
                    sword_point,
                    (
                        round(current[0] - normal_x * 2),
                        round(current[1] - normal_y * 2),
                    ),
                    (
                        round(tail[0] - normal_x * width),
                        round(tail[1] - normal_y * width),
                    ),
                ),
            )
            pygame.draw.line(
                layer,
                (
                    132,
                    26,
                    30,
                    intensity,
                ),
                current,
                sword_point,
                width=2,
            )

        for shard_index in range(7):
            shard_progress = (
                progress + shard_index * 0.13
            ) % 1.0
            horizontal_offset = (
                shard_index - 3
            ) * tile_size * 0.16
            shard_position = (
                round(
                    sword_point[0]
                    + horizontal_offset
                    * (1.0 - shard_progress)
                ),
                round(
                    sword_point[1]
                    - tile_size
                    * (
                        0.08
                        + shard_progress * 0.72
                    )
                ),
            )
            shard_size = 2 + shard_index % 3

            pygame.draw.polygon(
                layer,
                (
                    91,
                    84,
                    81,
                    round(45 + progress * 100),
                ),
                (
                    (
                        shard_position[0],
                        shard_position[1] - shard_size,
                    ),
                    (
                        shard_position[0] + shard_size,
                        shard_position[1] + shard_size,
                    ),
                    (
                        shard_position[0] - shard_size,
                        shard_position[1] + shard_size,
                    ),
                ),
            )
    else:
        release_progress = (
            elapsed - PALADIN_SACRED_GROUND_IMPACT_MS
        ) / (
            PALADIN_SACRED_GROUND_CAST_MS
            - PALADIN_SACRED_GROUND_IMPACT_MS
        )
        fade = max(
            0.0,
            1.0 - release_progress,
        )
        fracture_directions = (
            (-1.00, -0.18),
            (-0.82, 0.42),
            (-0.42, 0.78),
            (0.42, 0.78),
            (0.82, 0.42),
            (1.00, -0.18),
        )

        for index, direction in enumerate(
            fracture_directions
        ):
            middle = (
                round(
                    sword_point[0]
                    + direction[0] * tile_size * 0.48
                ),
                round(
                    sword_point[1]
                    + direction[1] * tile_size * 0.48
                    + (-5 if index % 2 == 0 else 5)
                ),
            )
            end = (
                round(
                    sword_point[0]
                    + direction[0]
                    * tile_size
                    * (
                        0.95 + release_progress * 0.42
                    )
                ),
                round(
                    sword_point[1]
                    + direction[1]
                    * tile_size
                    * (
                        0.95 + release_progress * 0.42
                    )
                ),
            )

            pygame.draw.lines(
                layer,
                (
                    12,
                    9,
                    10,
                    round(235 * fade),
                ),
                False,
                (
                    sword_point,
                    middle,
                    end,
                ),
                width=8,
            )
            pygame.draw.lines(
                layer,
                (
                    147,
                    25,
                    29,
                    round(225 * fade),
                ),
                False,
                (
                    sword_point,
                    middle,
                    end,
                ),
                width=3,
            )

        flash_width = round(
            tile_size * 0.52 * fade
        )
        pygame.draw.polygon(
            layer,
            (
                176,
                142,
                73,
                round(90 * fade),
            ),
            (
                (
                    sword_point[0] - flash_width,
                    sword_point[1] - 3,
                ),
                (
                    sword_point[0],
                    sword_point[1] - 10,
                ),
                (
                    sword_point[0] + flash_width,
                    sword_point[1] - 3,
                ),
                (
                    sword_point[0],
                    sword_point[1] + 7,
                ),
            ),
        )

    surface.blit(layer, (0, 0))


def draw_paladin_sacred_ground_lightnings(
    surface,
    player,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    active_lightnings = []

    for lightning in player.paladin_sacred_ground_lightnings:
        if lightning.started_at == 0:
            lightning.started_at = current_time

        elapsed = current_time - lightning.started_at
        if not 0 <= elapsed < PALADIN_SACRED_GROUND_LIGHTNING_MS:
            continue

        active_lightnings.append(lightning)
        progress = (
            elapsed / PALADIN_SACRED_GROUND_LIGHTNING_MS
        )
        target_position = _view_position(
            lightning.target[0],
            lightning.target[1],
            camera_x,
            camera_y,
        )
        target = (
            target_position[0] + tile_size // 2,
            target_position[1] + tile_size // 2,
        )
        source = (
            target[0],
            target[1] - tile_size * 4,
        )

        seed = (
            lightning.target[0] * 92821
            + lightning.target[1] * 68917
            + elapsed // 42
        )
        generator = random.Random(seed)
        points = [source]

        for index in range(1, 7):
            ratio = index / 7
            points.append(
                (
                    round(
                        source[0]
                        + (target[0] - source[0]) * ratio
                        + generator.randint(
                            -tile_size // 4,
                            tile_size // 4,
                        )
                    ),
                    round(
                        source[1]
                        + (target[1] - source[1]) * ratio
                    ),
                )
            )

        points.append(target)
        fade = max(0.0, 1.0 - progress)
        bolt_layer = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA,
        )

        pygame.draw.lines(
            bolt_layer,
            (8, 2, 14, round(235 * fade)),
            False,
            points,
            width=12,
        )
        pygame.draw.lines(
            bolt_layer,
            (76, 25, 105, round(255 * fade)),
            False,
            points,
            width=7,
        )
        pygame.draw.lines(
            bolt_layer,
            (180, 117, 202, round(255 * fade)),
            False,
            points,
            width=3,
        )
        pygame.draw.lines(
            bolt_layer,
            (255, 224, 154, round(230 * fade)),
            False,
            points,
            width=1,
        )

        from acts.act_three.presentation.berserker.effect_brushes import mist, spark

        mist(bolt_layer, target, tile_size * 0.42, (96, 58, 119), fade * 0.85)
        mist(bolt_layer, target, tile_size * 0.17, (208, 178, 151), fade * 0.65)
        for index in range(11):
            angle = index * 2.399
            distance = tile_size * (0.12 + progress * 0.43)
            point = (target[0] + math.cos(angle) * distance,
                     target[1] + math.sin(angle) * distance * 0.5 - math.sin(progress * math.pi) * 8)
            spark(bolt_layer, point, (math.cos(angle), math.sin(angle) * 0.6),
                  (209, 181, 153), fade * 0.7, 2)

        surface.blit(bolt_layer, (0, 0))

    player.paladin_sacred_ground_lightnings = active_lightnings
