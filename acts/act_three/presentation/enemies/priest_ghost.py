import math

import pygame

from acts.act_three.presentation.enemies.directional import (
    DIRECTIONAL_FRAME_COUNT,
    action_frame,
    attack_direction,
    facing_direction,
    hurt_direction,
    idle_frame,
    movement_elapsed,
    world_position,
)
from game.events import GameEventType
from game.state import EnemyBehaviorState


PRIEST_GHOST_IDLE_FRAME_MS = 280
PRIEST_GHOST_MOVE_DURATION_MS = 280
PRIEST_GHOST_ATTACK_DURATION_MS = 560
PRIEST_GHOST_HURT_DURATION_MS = 400
PRIEST_GHOST_DEATH_FRAME_MS = 115
PRIEST_GHOST_TRANSFORM_FRAME_MS = 120
PRIEST_GHOST_TRANSFORM_DURATION_MS = (
    DIRECTIONAL_FRAME_COUNT
    * PRIEST_GHOST_TRANSFORM_FRAME_MS
)
PRIEST_GHOST_REBIRTH_EFFECT_MS = 1100
PRIEST_GHOST_ATTACK_EFFECT_DELAY_MS = 140
PRIEST_GHOST_ATTACK_TRACER_STEP_MS = 65
PRIEST_GHOST_ATTACK_TRACER_FLASH_MS = 190
PRIEST_GHOST_ATTACK_IMPACT_DELAY_MS = 90
PRIEST_GHOST_ATTACK_IMPACT_MS = 320


def _is_priest_rebirth_event(event):
    return (
        event.type is GameEventType.ENVIRONMENT
        and event.data.get("kind") == "enemy_death_spawn"
        and event.data.get("source_enemy_type") == "priest"
        and event.data.get("enemy_type") == "priest_ghost"
    )


def record_priest_ghost_rebirth_feedback(
    game_state,
    started_at,
):
    if game_state.floor.presentation_act < 3:
        return

    enemies_by_name = {
        enemy.name: enemy
        for enemy in game_state.floor.enemies
    }

    for event in game_state.events:
        if not _is_priest_rebirth_event(event):
            continue

        priest = enemies_by_name.get(event.target)
        ghost = enemies_by_name.get(event.actor)

        if priest is not None:
            game_state.act_three.priest_rebirth_consumed_corpses.add(
                id(priest)
            )

        if ghost is None:
            continue

        rebirth_started_at = started_at

        if (
            priest is not None
            and priest.death_animation_started_at >= 0
        ):
            rebirth_started_at = (
                priest.death_animation_started_at
            )

        if ghost.summon_spawn_animation_started_at < 0:
            ghost.summon_spawn_animation_started_at = (
                rebirth_started_at
            )


def _priest_ghost_transform_elapsed(
    enemy,
    current_time,
):
    started_at = enemy.summon_spawn_animation_started_at

    if started_at < 0:
        return None

    elapsed = current_time - started_at

    if not 0 <= elapsed < PRIEST_GHOST_TRANSFORM_DURATION_MS:
        return None

    return elapsed


def priest_ghost_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    direction = facing_direction(enemy)

    if enemy.behavior_state is EnemyBehaviorState.DEAD:
        if enemy.death_animation_started_at < 0:
            frame_index = DIRECTIONAL_FRAME_COUNT - 1
        else:
            death_elapsed = max(
                0,
                current_time
                - enemy.death_animation_started_at,
            )
            frame_index = min(
                DIRECTIONAL_FRAME_COUNT - 1,
                death_elapsed
                // PRIEST_GHOST_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_priest_ghost_death_"
                f"{direction}_{frame_index}"
            )
        ]

    transform_elapsed = _priest_ghost_transform_elapsed(
        enemy,
        current_time,
    )

    if transform_elapsed is not None:
        frame_index = min(
            DIRECTIONAL_FRAME_COUNT - 1,
            transform_elapsed
            // PRIEST_GHOST_TRANSFORM_FRAME_MS,
        )

        return assets[
            f"enemy_priest_ghost_transform_down_{frame_index}"
        ]

    hurt_elapsed = (
        current_time
        - enemy.hit_animation_started_at
    )

    if (
        enemy.hit_damage > 0
        and not enemy.hit_dodged
        and 0
        <= hurt_elapsed
        < PRIEST_GHOST_HURT_DURATION_MS
    ):
        direction = hurt_direction(enemy)
        frame_index = action_frame(
            hurt_elapsed,
            PRIEST_GHOST_HURT_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_ghost_hurt_"
                f"{direction}_{frame_index}"
            )
        ]

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if (
        0
        <= attack_elapsed
        < PRIEST_GHOST_ATTACK_DURATION_MS
    ):
        direction = attack_direction(enemy)
        frame_index = action_frame(
            attack_elapsed,
            PRIEST_GHOST_ATTACK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_ghost_attack_"
                f"{direction}_{frame_index}"
            )
        ]

    move_elapsed = movement_elapsed(
        enemy,
        current_time,
        PRIEST_GHOST_MOVE_DURATION_MS,
    )

    if move_elapsed is not None:
        frame_index = action_frame(
            move_elapsed,
            PRIEST_GHOST_MOVE_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_ghost_walk_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = idle_frame(
        enemy,
        current_time,
        visual_seed,
        PRIEST_GHOST_IDLE_FRAME_MS,
    )

    return assets[
        (
            f"enemy_priest_ghost_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def priest_ghost_world_position(
    enemy,
    current_time,
    tile_size,
):
    return world_position(
        enemy,
        current_time,
        PRIEST_GHOST_MOVE_DURATION_MS,
        tile_size,
    )


def draw_priest_ghost_attack_effects(
    surface,
    enemy,
    current_time,
    tile_size,
    camera_x,
    camera_y,
):
    if (
        enemy.health <= 0
        or not enemy.attack_effect_positions
    ):
        return

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )
    target = enemy.attack_effect_positions[0]
    column_distance = (
        target[0] - enemy.column
    )
    row_distance = (
        target[1] - enemy.row
    )

    if column_distance and row_distance:
        return

    path_length = max(
        abs(column_distance),
        abs(row_distance),
    )

    if path_length <= 0:
        return

    column_step = (
        0
        if column_distance == 0
        else 1
        if column_distance > 0
        else -1
    )
    row_step = (
        0
        if row_distance == 0
        else 1
        if row_distance > 0
        else -1
    )
    attack_path = [
        (
            enemy.column
            + column_step * distance,
            enemy.row
            + row_step * distance,
        )
        for distance in range(
            1,
            path_length + 1,
        )
    ]

    for cell_index, position in enumerate(
        attack_path
    ):
        cell_elapsed = (
            attack_elapsed
            - PRIEST_GHOST_ATTACK_EFFECT_DELAY_MS
            - cell_index
            * PRIEST_GHOST_ATTACK_TRACER_STEP_MS
        )

        if not (
            0
            <= cell_elapsed
            < PRIEST_GHOST_ATTACK_TRACER_FLASH_MS
        ):
            continue

        progress = (
            cell_elapsed
            / PRIEST_GHOST_ATTACK_TRACER_FLASH_MS
        )
        visibility = (
            min(
                1.0,
                cell_elapsed / 45,
            )
            * min(
                1.0,
                (
                    PRIEST_GHOST_ATTACK_TRACER_FLASH_MS
                    - cell_elapsed
                )
                / 85,
            )
        )
        effect = pygame.Surface(
            (tile_size, tile_size),
            pygame.SRCALPHA,
        )
        center = (
            tile_size / 2,
            tile_size / 2,
        )
        direction_x = (
            position[0] - enemy.column
        )
        direction_y = (
            position[1] - enemy.row
        )
        direction_length = max(
            1.0,
            math.hypot(
                direction_x,
                direction_y,
            ),
        )
        forward_x = (
            direction_x / direction_length
        )
        forward_y = (
            direction_y / direction_length
        )
        side_x = -forward_y
        side_y = forward_x
        seed = (
            position[0] * 0.73
            + position[1] * 1.19
            + cell_index * 0.53
        )
        travel = (
            progress - 0.42
        ) * tile_size * 0.3
        flame_center = (
            center[0] + forward_x * travel,
            center[1] + forward_y * travel,
        )
        flame_length = tile_size * (
            0.46
            + math.sin(
                progress * math.pi
            )
            * 0.12
        )
        flame_width = tile_size * (
            0.09
            + math.sin(
                progress * math.pi
            )
            * 0.035
        )

        def flame_point(
            distance,
            width,
        ):
            return (
                round(
                    flame_center[0]
                    + forward_x * distance
                    + side_x * width
                ),
                round(
                    flame_center[1]
                    + forward_y * distance
                    + side_y * width
                ),
            )

        outer_flame = [
            flame_point(
                flame_length * 0.52,
                0,
            ),
            flame_point(
                flame_length * 0.25,
                -flame_width * 0.55,
            ),
            flame_point(
                flame_length * 0.08,
                -flame_width,
            ),
            flame_point(
                -flame_length * 0.12,
                -flame_width * 0.45,
            ),
            flame_point(
                -flame_length * 0.42,
                -flame_width * 0.76,
            ),
            flame_point(
                -flame_length * 0.29,
                0,
            ),
            flame_point(
                -flame_length * 0.5,
                flame_width * 0.48,
            ),
            flame_point(
                -flame_length * 0.08,
                flame_width * 0.42,
            ),
            flame_point(
                flame_length * 0.1,
                flame_width,
            ),
            flame_point(
                flame_length * 0.3,
                flame_width * 0.48,
            ),
        ]
        middle_flame = [
            flame_point(
                flame_length * 0.48,
                0,
            ),
            flame_point(
                flame_length * 0.16,
                -flame_width * 0.45,
            ),
            flame_point(
                -flame_length * 0.2,
                -flame_width * 0.25,
            ),
            flame_point(
                -flame_length * 0.36,
                0,
            ),
            flame_point(
                -flame_length * 0.12,
                flame_width * 0.34,
            ),
            flame_point(
                flame_length * 0.2,
                flame_width * 0.42,
            ),
        ]
        inner_flame = [
            flame_point(
                flame_length * 0.44,
                0,
            ),
            flame_point(
                flame_length * 0.05,
                -flame_width * 0.2,
            ),
            flame_point(
                -flame_length * 0.22,
                0,
            ),
            flame_point(
                flame_length * 0.08,
                flame_width * 0.22,
            ),
        ]

        pygame.draw.polygon(
            effect,
            (
                1,
                16,
                8,
                round(225 * visibility),
            ),
            outer_flame,
        )
        pygame.draw.polygon(
            effect,
            (
                13,
                92,
                37,
                round(238 * visibility),
            ),
            middle_flame,
        )
        pygame.draw.polygon(
            effect,
            (
                128,
                255,
                70,
                round(250 * visibility),
            ),
            inner_flame,
        )

        for tongue_index in range(5):
            tongue_distance = (
                -flame_length * 0.08
                - tongue_index
                * flame_length
                * 0.075
            )
            tongue_side = (
                -1
                if tongue_index % 2 == 0
                else 1
            )
            tongue_side *= flame_width * (
                0.28
                + tongue_index * 0.13
            )
            tongue_start = flame_point(
                tongue_distance,
                tongue_side,
            )
            tongue_middle = flame_point(
                tongue_distance
                - flame_length
                * (
                    0.08
                    + tongue_index * 0.018
                ),
                tongue_side
                + math.sin(
                    seed + tongue_index
                )
                * flame_width
                * 0.7,
            )
            tongue_end = flame_point(
                tongue_distance
                - flame_length
                * (
                    0.17
                    + tongue_index * 0.025
                ),
                tongue_side * 0.25,
            )

            pygame.draw.lines(
                effect,
                (
                    1,
                    20,
                    9,
                    round(210 * visibility),
                ),
                False,
                (
                    tongue_start,
                    tongue_middle,
                    tongue_end,
                ),
                7,
            )
            pygame.draw.lines(
                effect,
                (
                    18,
                    117,
                    45,
                    round(225 * visibility),
                ),
                False,
                (
                    tongue_start,
                    tongue_middle,
                    tongue_end,
                ),
                3,
            )
            pygame.draw.lines(
                effect,
                (
                    152,
                    255,
                    75,
                    round(240 * visibility),
                ),
                False,
                (
                    tongue_start,
                    tongue_middle,
                ),
                1,
            )

        for spark_index in range(7):
            spark_distance = flame_length * (
                0.05
                + spark_index * 0.055
            )
            spark_side = (
                -1
                if spark_index % 2 == 0
                else 1
            )
            spark_side *= flame_width * (
                0.9
                + spark_index % 3 * 0.45
            )
            spark_start = flame_point(
                spark_distance,
                spark_side,
            )
            spark_end = flame_point(
                spark_distance
                - flame_length
                * (
                    0.07
                    + spark_index % 2 * 0.03
                ),
                spark_side * 1.3,
            )

            pygame.draw.line(
                effect,
                (
                    90,
                    236,
                    70,
                    round(225 * visibility),
                ),
                spark_start,
                spark_end,
                2 if spark_index % 3 == 0 else 1,
            )
        surface.blit(
            effect,
            (
                position[0] * tile_size - camera_x,
                position[1] * tile_size - camera_y,
            ),
        )

    impact_started_at = (
            PRIEST_GHOST_ATTACK_EFFECT_DELAY_MS
            + (
                    path_length - 1
            )
            * PRIEST_GHOST_ATTACK_TRACER_STEP_MS
            + PRIEST_GHOST_ATTACK_IMPACT_DELAY_MS
    )
    impact_elapsed = (
            attack_elapsed - impact_started_at
    )

    if not (
            0
            <= impact_elapsed
            < PRIEST_GHOST_ATTACK_IMPACT_MS
    ):
        return

    impact_progress = (
            impact_elapsed
            / PRIEST_GHOST_ATTACK_IMPACT_MS
    )
    impact_visibility = (
            min(
                1.0,
                impact_elapsed / 55,
            )
            * min(
        1.0,
        (
                PRIEST_GHOST_ATTACK_IMPACT_MS
                - impact_elapsed
        )
        / 130,
    )
    )
    impact = pygame.Surface(
        (tile_size, tile_size),
        pygame.SRCALPHA,
    )
    impact_center = (
        tile_size // 2,
        tile_size // 2,
    )
    burst = math.sin(
        math.pi * impact_progress
    )
    outer_radius = tile_size * (
            0.11 + burst * 0.18
    )
    middle_radius = outer_radius * 0.7
    inner_radius = outer_radius * 0.38
    rotation = (
            impact_progress * 1.7
            + target[0] * 0.31
            + target[1] * 0.23
    )

    outer_points = []
    middle_points = []
    inner_points = []

    for point_index in range(16):
        angle = (
                rotation
                + point_index * math.tau / 16
        )
        radius_scale = (
            1.0
            if point_index % 2 == 0
            else 0.42
        )
        outer_points.append(
            (
                round(
                    impact_center[0]
                    + math.cos(angle)
                    * outer_radius
                    * radius_scale
                ),
                round(
                    impact_center[1]
                    + math.sin(angle)
                    * outer_radius
                    * radius_scale
                ),
            )
        )
        middle_points.append(
            (
                round(
                    impact_center[0]
                    + math.cos(angle)
                    * middle_radius
                    * radius_scale
                ),
                round(
                    impact_center[1]
                    + math.sin(angle)
                    * middle_radius
                    * radius_scale
                ),
            )
        )
        inner_points.append(
            (
                round(
                    impact_center[0]
                    + math.cos(angle)
                    * inner_radius
                    * radius_scale
                ),
                round(
                    impact_center[1]
                    + math.sin(angle)
                    * inner_radius
                    * radius_scale
                ),
            )
        )

    pygame.draw.polygon(
        impact,
        (
            1,
            15,
            7,
            round(230 * impact_visibility),
        ),
        outer_points,
    )
    pygame.draw.polygon(
        impact,
        (
            13,
            103,
            39,
            round(240 * impact_visibility),
        ),
        middle_points,
    )
    pygame.draw.polygon(
        impact,
        (
            141,
            255,
            70,
            round(250 * impact_visibility),
        ),
        inner_points,
    )

    for flame_index in range(9):
        flame_angle = (
                rotation
                + flame_index * math.tau / 9
        )
        flame_length = tile_size * (
                0.18
                + burst
                * (
                        0.12
                        + flame_index % 3 * 0.025
                )
        )
        flame_start = (
            round(
                impact_center[0]
                + math.cos(flame_angle)
                * outer_radius
                * 0.35
            ),
            round(
                impact_center[1]
                + math.sin(flame_angle)
                * outer_radius
                * 0.35
            ),
        )
        flame_middle = (
            round(
                impact_center[0]
                + math.cos(
                    flame_angle + 0.12
                )
                * flame_length
                * 0.72
            ),
            round(
                impact_center[1]
                + math.sin(
                    flame_angle + 0.12
                )
                * flame_length
                * 0.72
            ),
        )
        flame_end = (
            round(
                impact_center[0]
                + math.cos(
                    flame_angle - 0.08
                )
                * flame_length
            ),
            round(
                impact_center[1]
                + math.sin(
                    flame_angle - 0.08
                )
                * flame_length
            ),
        )

        pygame.draw.lines(
            impact,
            (
                2,
                25,
                10,
                round(215 * impact_visibility),
            ),
            False,
            (
                flame_start,
                flame_middle,
                flame_end,
            ),
            6,
        )
        pygame.draw.lines(
            impact,
            (
                23,
                137,
                49,
                round(230 * impact_visibility),
            ),
            False,
            (
                flame_start,
                flame_middle,
                flame_end,
            ),
            3,
        )
        pygame.draw.line(
            impact,
            (
                149,
                255,
                72,
                round(245 * impact_visibility),
            ),
            flame_start,
            flame_middle,
            1,
        )

    for spark_index in range(8):
        spark_angle = (
                rotation
                + spark_index * math.tau / 8
                + 0.24
        )
        spark_distance = tile_size * (
                0.16
                + impact_progress
                * (
                        0.17
                        + spark_index % 3 * 0.025
                )
        )
        spark_start = (
            round(
                impact_center[0]
                + math.cos(spark_angle)
                * spark_distance
            ),
            round(
                impact_center[1]
                + math.sin(spark_angle)
                * spark_distance
            ),
        )
        spark_end = (
            round(
                spark_start[0]
                + math.cos(spark_angle)
                * tile_size
                * 0.055
            ),
            round(
                spark_start[1]
                + math.sin(spark_angle)
                * tile_size
                * 0.055
            ),
        )

        pygame.draw.line(
            impact,
            (
                100,
                238,
                73,
                round(220 * impact_visibility),
            ),
            spark_start,
            spark_end,
            2 if spark_index % 3 == 0 else 1,
        )

    surface.blit(
        impact,
        (
            target[0] * tile_size - camera_x,
            target[1] * tile_size - camera_y,
        ),
    )

def draw_priest_ghost_rebirth_effect(
    surface,
    enemy,
    position,
    current_time,
    tile_size,
):
    started_at = enemy.summon_spawn_animation_started_at

    if started_at < 0:
        return

    elapsed = current_time - started_at

    if not 0 <= elapsed < PRIEST_GHOST_REBIRTH_EFFECT_MS:
        return

    progress = elapsed / PRIEST_GHOST_REBIRTH_EFFECT_MS
    eruption = min(
        1.0,
        elapsed / PRIEST_GHOST_TRANSFORM_DURATION_MS,
    )
    visibility = min(
        1.0,
        (
            PRIEST_GHOST_REBIRTH_EFFECT_MS - elapsed
        )
        / 260,
    )
    effect_size = tile_size * 4
    effect_center = effect_size // 2
    effect = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    radius = round(
        tile_size
        * (
            0.32
            + eruption * 0.74
        )
    )

    pygame.draw.circle(
        effect,
        (
            2,
            12,
            7,
            round(185 * visibility),
        ),
        (effect_center, effect_center),
        radius,
    )
    pygame.draw.circle(
        effect,
        (
            16,
            74,
            35,
            round(170 * visibility),
        ),
        (effect_center, effect_center),
        max(1, radius - 5),
        width=5,
    )
    pygame.draw.circle(
        effect,
        (
            80,
            205,
            91,
            round(215 * visibility),
        ),
        (effect_center, effect_center),
        radius,
        width=2,
    )

    seal_radius = tile_size * (
        0.4 + eruption * 0.18
    )
    rotation = (
        -math.pi / 2
        + progress * 1.9
    )
    vertices = [
        (
            round(
                effect_center
                + math.cos(
                    rotation
                    + index * math.tau / 5
                )
                * seal_radius
            ),
            round(
                effect_center
                + math.sin(
                    rotation
                    + index * math.tau / 5
                )
                * seal_radius
            ),
        )
        for index in range(5)
    ]

    pygame.draw.lines(
        effect,
        (
            54,
            171,
            69,
            round(190 * visibility),
        ),
        True,
        [
            vertices[index]
            for index in (
                0,
                2,
                4,
                1,
                3,
            )
        ],
        2,
    )

    for particle_index in range(14):
        angle = (
            particle_index * math.tau / 14
            + progress * 3.6
            + enemy.column * 0.17
        )
        distance = tile_size * (
            0.18
            + eruption * 0.46
            + particle_index % 3 * 0.07
        )
        lift = progress * tile_size * (
            0.55
            + particle_index % 4 * 0.14
        )
        particle_x = (
            effect_center
            + math.cos(angle) * distance
        )
        particle_y = (
            effect_center
            + math.sin(angle) * distance * 0.48
            - lift
        )
        points = [
            (
                round(
                    particle_x
                    + math.sin(
                        angle + segment * 0.7
                    )
                    * (2 + segment)
                ),
                round(
                    particle_y
                    + segment * tile_size * 0.07
                ),
            )
            for segment in range(5)
        ]

        pygame.draw.lines(
            effect,
            (
                5,
                35,
                17,
                round(215 * visibility),
            ),
            False,
            points,
            6,
        )
        pygame.draw.lines(
            effect,
            (
                42,
                148,
                62,
                round(205 * visibility),
            ),
            False,
            points,
            2,
        )
        pygame.draw.circle(
            effect,
            (
                139,
                239,
                117,
                round(230 * visibility),
            ),
            points[0],
            2,
        )

    surface.blit(
        effect,
        (
            round(
                position[0]
                + tile_size / 2
                - effect_center
            ),
            round(
                position[1]
                + tile_size / 2
                - effect_center
            ),
        ),
    )
