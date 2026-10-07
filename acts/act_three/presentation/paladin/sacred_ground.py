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


def _sacred_ground_patch(
    layer,
    left,
    top,
    tile_size,
    seed,
    pulse,
):
    generator = random.Random(seed)
    inset = tile_size * 0.08

    points = [
        (
            left + inset + generator.randint(0, tile_size // 7),
            top + inset + generator.randint(0, tile_size // 7),
        ),
        (
            left + tile_size * 0.48,
            top + generator.randint(0, tile_size // 9),
        ),
        (
            left + tile_size - inset,
            top + inset + generator.randint(0, tile_size // 6),
        ),
        (
            left + tile_size - generator.randint(0, tile_size // 8),
            top + tile_size * 0.52,
        ),
        (
            left + tile_size - inset - generator.randint(
                0,
                tile_size // 8,
            ),
            top + tile_size - inset,
        ),
        (
            left + tile_size * 0.48,
            top + tile_size - generator.randint(0, tile_size // 8),
        ),
        (
            left + inset + generator.randint(0, tile_size // 7),
            top + tile_size - inset,
        ),
        (
            left + generator.randint(0, tile_size // 8),
            top + tile_size * 0.48,
        ),
    ]

    pygame.draw.polygon(
        layer,
        (
            9,
            7,
            8,
            round(118 + pulse * 24),
        ),
        points,
    )
    pygame.draw.polygon(
        layer,
        (
            54,
            12,
            14,
            round(88 + pulse * 35),
        ),
        points,
        width=3,
    )

    center = (
        round(left + tile_size * 0.5),
        round(top + tile_size * 0.52),
    )

    for crack_index in range(4):
        angle = (
            generator.random() * math.tau
            + crack_index * 1.2
        )
        length = generator.uniform(
            tile_size * 0.22,
            tile_size * 0.52,
        )
        middle = (
            round(
                center[0]
                + math.cos(angle) * length * 0.48
            ),
            round(
                center[1]
                + math.sin(angle) * length * 0.48
            ),
        )
        end = (
            round(
                center[0]
                + math.cos(angle + generator.uniform(-0.22, 0.22))
                * length
            ),
            round(
                center[1]
                + math.sin(angle + generator.uniform(-0.22, 0.22))
                * length
            ),
        )

        pygame.draw.lines(
            layer,
            (
                17,
                15,
                16,
                230,
            ),
            False,
            (
                center,
                middle,
                end,
            ),
            width=5,
        )
        pygame.draw.lines(
            layer,
            (
                131,
                27,
                31,
                round(145 + pulse * 65),
            ),
            False,
            (
                center,
                middle,
                end,
            ),
            width=2,
        )


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

        impact_progress = min(1.0, progress * 3.0)
        impact_radius = round(
            tile_size * (
                0.18 + impact_progress * 0.55
            )
        )

        pygame.draw.circle(
            bolt_layer,
            (22, 4, 31, round(210 * fade)),
            target,
            impact_radius + 8,
        )
        pygame.draw.circle(
            bolt_layer,
            (125, 51, 154, round(245 * fade)),
            target,
            impact_radius,
            width=4,
        )
        pygame.draw.circle(
            bolt_layer,
            (231, 184, 91, round(230 * fade)),
            target,
            max(4, impact_radius - 7),
            width=2,
        )

        for angle_index in range(8):
            angle = (
                math.tau * angle_index / 8
                + progress * 0.6
            )
            inner = tile_size * 0.18
            outer = tile_size * (
                0.38 + impact_progress * 0.28
            )
            pygame.draw.line(
                bolt_layer,
                (97, 38, 127, round(220 * fade)),
                (
                    round(target[0] + math.cos(angle) * inner),
                    round(target[1] + math.sin(angle) * inner),
                ),
                (
                    round(target[0] + math.cos(angle) * outer),
                    round(target[1] + math.sin(angle) * outer),
                ),
                width=3,
            )

        surface.blit(bolt_layer, (0, 0))

    player.paladin_sacred_ground_lightnings = active_lightnings
