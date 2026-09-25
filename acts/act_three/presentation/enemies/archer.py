import math

import pygame

from game.state import EnemyBehaviorState


ARCHER_FRAME_COUNT = 8
ARCHER_IDLE_FRAME_MS = 140
ARCHER_MOVE_DURATION_MS = 220
ARCHER_BACKHOP_DURATION_MS = 360
ARCHER_BACKHOP_HEIGHT = 12
ARCHER_ATTACK_DURATION_MS = 320
ARCHER_DEATH_FRAME_MS = 90
ARCHER_DEATH_DURATION_MS = (
    ARCHER_FRAME_COUNT * ARCHER_DEATH_FRAME_MS
)


def _direction_from_delta(
    column_change,
    row_change,
):
    if abs(column_change) > abs(row_change):
        return (
            "right"
            if column_change > 0
            else "left"
        )

    if row_change:
        return (
            "down"
            if row_change > 0
            else "up"
        )

    return "down"


def _archer_movement_direction(enemy):
    origin = enemy.movement_origin

    if origin is None:
        return "down"

    return _direction_from_delta(
        enemy.column - origin[0],
        enemy.row - origin[1],
    )


def _archer_attack_direction(enemy):
    if not enemy.attack_effect_positions:
        return _archer_movement_direction(enemy)

    target = enemy.attack_effect_positions[0]

    return _direction_from_delta(
        target[0] - enemy.column,
        target[1] - enemy.row,
    )


def _archer_direction(enemy):
    if (
        enemy.attack_effect_positions
        and enemy.attack_animation_started_at
        >= enemy.movement_animation_started_at
    ):
        return _archer_attack_direction(enemy)

    return _archer_movement_direction(enemy)


def _archer_is_backhop(enemy):
    origin = enemy.movement_origin

    if (
        origin is None
        or enemy.movement_animation_kind != "retreat"
    ):
        return False

    distance = (
        abs(enemy.column - origin[0])
        + abs(enemy.row - origin[1])
    )

    return distance == 2


def _archer_movement_state(
    enemy,
    current_time,
):
    if (
        enemy.movement_origin is None
        or enemy.movement_animation_started_at <= 0
    ):
        return None

    backhop = _archer_is_backhop(enemy)
    duration = (
        ARCHER_BACKHOP_DURATION_MS
        if backhop
        else ARCHER_MOVE_DURATION_MS
    )
    elapsed = (
        current_time
        - enemy.movement_animation_started_at
    )

    if not 0 <= elapsed < duration:
        return None

    return elapsed, duration, backhop


def _archer_idle_frame(
    enemy,
    current_time,
    visual_seed,
):
    identity_offset = sum(
        (index + 1) * ord(character)
        for index, character in enumerate(enemy.name)
    )

    return (
        current_time // ARCHER_IDLE_FRAME_MS
        + visual_seed
        + identity_offset
    ) % ARCHER_FRAME_COUNT


def _archer_action_frame(
    elapsed,
    duration,
):
    return min(
        ARCHER_FRAME_COUNT - 1,
        elapsed
        * ARCHER_FRAME_COUNT
        // duration,
    )


def _movement_progress(
    elapsed,
    duration,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    smooth_progress = (
        progress
        * progress
        * (3.0 - 2.0 * progress)
    )

    return (
        progress * 0.85
        + smooth_progress * 0.15
    )


def _archer_movement_position(
    enemy,
    elapsed,
    duration,
    backhop,
    tile_size,
):
    origin = enemy.movement_origin
    progress = _movement_progress(
        elapsed,
        duration,
    )
    raw_progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    lift = (
        math.sin(math.pi * raw_progress)
        * ARCHER_BACKHOP_HEIGHT
        if backhop
        else 0
    )

    return (
        round(
            (
                origin[0]
                + (
                    enemy.column - origin[0]
                )
                * progress
            )
            * tile_size
        ),
        round(
            (
                origin[1]
                + (
                    enemy.row - origin[1]
                )
                * progress
            )
            * tile_size
            - lift
        ),
    )


def archer_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    direction = _archer_direction(enemy)

    if enemy.behavior_state is EnemyBehaviorState.DEAD:
        if enemy.death_animation_started_at < 0:
            frame_index = ARCHER_FRAME_COUNT - 1
        else:
            death_elapsed = max(
                0,
                current_time
                - enemy.death_animation_started_at,
            )
            frame_index = min(
                ARCHER_FRAME_COUNT - 1,
                death_elapsed // ARCHER_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_archer_death_"
                f"{direction}_{frame_index}"
            )
        ]

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if 0 <= attack_elapsed < ARCHER_ATTACK_DURATION_MS:
        attack_direction = _archer_attack_direction(
            enemy,
        )
        frame_index = _archer_action_frame(
            attack_elapsed,
            ARCHER_ATTACK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_archer_attack_"
                f"{attack_direction}_{frame_index}"
            )
        ]

    movement_state = _archer_movement_state(
        enemy,
        current_time,
    )

    if movement_state is not None:
        elapsed, duration, backhop = movement_state
        action = (
            "backhop"
            if backhop
            else "walk"
        )
        frame_index = _archer_action_frame(
            elapsed,
            duration,
        )

        return assets[
            (
                f"enemy_archer_{action}_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = _archer_idle_frame(
        enemy,
        current_time,
        visual_seed,
    )

    return assets[
        (
            f"enemy_archer_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def archer_world_position(
    enemy,
    current_time,
    tile_size,
):
    movement_state = _archer_movement_state(
        enemy,
        current_time,
    )

    if movement_state is None:
        return (
            enemy.column * tile_size,
            enemy.row * tile_size,
        )

    elapsed, duration, backhop = movement_state

    return _archer_movement_position(
        enemy,
        elapsed,
        duration,
        backhop,
        tile_size,
    )


def draw_archer_backhop_afterimages(
    surface,
    assets,
    enemy,
    current_time,
    tile_size,
    camera_x,
    camera_y,
):
    movement_state = _archer_movement_state(
        enemy,
        current_time,
    )

    if movement_state is None:
        return

    elapsed, duration, backhop = movement_state

    if not backhop:
        return

    direction = _archer_direction(enemy)

    for delay, alpha in (
        (120, 42),
        (80, 72),
        (40, 112),
    ):
        sampled_elapsed = elapsed - delay

        if sampled_elapsed < 0:
            continue

        frame_index = _archer_action_frame(
            sampled_elapsed,
            duration,
        )
        sprite = assets[
            (
                f"enemy_archer_backhop_"
                f"{direction}_{frame_index}"
            )
        ]
        position = _archer_movement_position(
            enemy,
            sampled_elapsed,
            duration,
            True,
            tile_size,
        )
        afterimage = sprite.copy()
        afterimage.fill(
            (38, 62, 78, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        afterimage.set_alpha(alpha)

        surface.blit(
            afterimage,
            (
                position[0] - camera_x,
                position[1] - camera_y,
            ),
        )
