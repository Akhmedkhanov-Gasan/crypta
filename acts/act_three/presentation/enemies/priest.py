from acts.act_three.presentation.enemies.directional import (
    DIRECTIONAL_FRAME_COUNT,
    action_frame,
    attack_direction,
    direction_to_position,
    facing_direction,
    hurt_direction,
    idle_frame,
    movement_elapsed,
    world_position,
)
from game.state import EnemyBehaviorState


PRIEST_IDLE_FRAME_MS = 280
PRIEST_MOVE_DURATION_MS = 280
PRIEST_CAST_DURATION_MS = 560
PRIEST_PREPARE_FRAME_MS = 100
PRIEST_HURT_DURATION_MS = 400
PRIEST_DEATH_FRAME_MS = 115


def _priest_cast_direction(enemy):
    heal_target = enemy.heal_target

    if (
        heal_target is not None
        and heal_target.health > 0
    ):
        return direction_to_position(
            enemy,
            (
                heal_target.column,
                heal_target.row,
            ),
        )

    return attack_direction(enemy)


def _priest_direction(enemy):
    if (
        enemy.behavior_state
        is EnemyBehaviorState.PREPARING_HEAL
        and enemy.heal_target is not None
        and enemy.heal_target.health > 0
    ):
        return _priest_cast_direction(enemy)

    return facing_direction(enemy)


def priest_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    direction = _priest_direction(enemy)

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
                death_elapsed // PRIEST_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_priest_death_"
                f"{direction}_{frame_index}"
            )
        ]

    hurt_elapsed = (
        current_time
        - enemy.hit_animation_started_at
    )

    if (
        enemy.hit_damage > 0
        and not enemy.hit_dodged
        and 0 <= hurt_elapsed < PRIEST_HURT_DURATION_MS
    ):
        direction = hurt_direction(enemy)
        frame_index = action_frame(
            hurt_elapsed,
            PRIEST_HURT_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_hurt_"
                f"{direction}_{frame_index}"
            )
        ]

    cast_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if 0 <= cast_elapsed < PRIEST_CAST_DURATION_MS:
        direction = _priest_cast_direction(enemy)
        frame_index = action_frame(
            cast_elapsed,
            PRIEST_CAST_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_cast_"
                f"{direction}_{frame_index}"
            )
        ]

    if (
        enemy.behavior_state
        is EnemyBehaviorState.PREPARING_HEAL
        and enemy.heal_target is not None
        and enemy.heal_target.health > 0
    ):
        direction = _priest_cast_direction(enemy)
        frame_index = (
            current_time // PRIEST_PREPARE_FRAME_MS
        ) % DIRECTIONAL_FRAME_COUNT

        return assets[
            (
                f"enemy_priest_cast_"
                f"{direction}_{frame_index}"
            )
        ]

    move_elapsed = movement_elapsed(
        enemy,
        current_time,
        PRIEST_MOVE_DURATION_MS,
    )

    if move_elapsed is not None:
        frame_index = action_frame(
            move_elapsed,
            PRIEST_MOVE_DURATION_MS,
        )

        return assets[
            (
                f"enemy_priest_walk_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = idle_frame(
        enemy,
        current_time,
        visual_seed,
        PRIEST_IDLE_FRAME_MS,
    )

    return assets[
        (
            f"enemy_priest_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def priest_world_position(
    enemy,
    current_time,
    tile_size,
):
    return world_position(
        enemy,
        current_time,
        PRIEST_MOVE_DURATION_MS,
        tile_size,
    )
