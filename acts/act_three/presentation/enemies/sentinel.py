from acts.act_three.presentation.enemies.directional import (
    DIRECTIONAL_FRAME_COUNT,
    action_frame,
    attack_direction,
    direction_from_delta,
    facing_direction,
    hurt_direction,
    idle_frame,
    movement_elapsed,
    world_position,
)
from game.state import EnemyBehaviorState


SENTINEL_IDLE_FRAME_MS = 290
SENTINEL_MOVE_DURATION_MS = 280
SENTINEL_ATTACK_DURATION_MS = 520
SENTINEL_BLOCK_DURATION_MS = 520
SENTINEL_BLOCK_FRAME_MS = 150
SENTINEL_HURT_DURATION_MS = 400
SENTINEL_DEATH_FRAME_MS = 120


def _sentinel_attack_direction(enemy):
    if enemy.attack_effect_positions:
        return attack_direction(enemy)

    column_change, row_change = (
        enemy.sentinel.bash_direction
    )

    if column_change or row_change:
        return direction_from_delta(
            column_change,
            row_change,
        )

    return facing_direction(enemy)


def _sentinel_block_direction(enemy):
    if (
        enemy.hit_blocked
        and enemy.hit_origin is not None
    ):
        return hurt_direction(enemy)

    if enemy.prepared_attack_mode == "shield_bash":
        column_change, row_change = (
            enemy.sentinel.bash_direction
        )

        if column_change or row_change:
            return direction_from_delta(
                column_change,
                row_change,
            )

    return facing_direction(enemy)


def sentinel_sprite(
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
                death_elapsed // SENTINEL_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_sentinel_death_"
                f"{direction}_{frame_index}"
            )
        ]

    hit_elapsed = (
        current_time
        - enemy.hit_animation_started_at
    )

    if (
        enemy.hit_blocked
        and not enemy.hit_dodged
        and 0 <= hit_elapsed < SENTINEL_BLOCK_DURATION_MS
    ):
        direction = _sentinel_block_direction(enemy)
        frame_index = action_frame(
            hit_elapsed,
            SENTINEL_BLOCK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_sentinel_block_"
                f"{direction}_{frame_index}"
            )
        ]

    if (
        enemy.hit_damage > 0
        and not enemy.hit_dodged
        and 0 <= hit_elapsed < SENTINEL_HURT_DURATION_MS
    ):
        direction = hurt_direction(enemy)
        frame_index = action_frame(
            hit_elapsed,
            SENTINEL_HURT_DURATION_MS,
        )

        return assets[
            (
                f"enemy_sentinel_hurt_"
                f"{direction}_{frame_index}"
            )
        ]

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if 0 <= attack_elapsed < SENTINEL_ATTACK_DURATION_MS:
        direction = _sentinel_attack_direction(enemy)
        frame_index = action_frame(
            attack_elapsed,
            SENTINEL_ATTACK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_sentinel_attack_"
                f"{direction}_{frame_index}"
            )
        ]

    move_elapsed = movement_elapsed(
        enemy,
        current_time,
        SENTINEL_MOVE_DURATION_MS,
    )

    if move_elapsed is not None:
        frame_index = action_frame(
            move_elapsed,
            SENTINEL_MOVE_DURATION_MS,
        )

        return assets[
            (
                f"enemy_sentinel_walk_"
                f"{direction}_{frame_index}"
            )
        ]

    if (
        enemy.prepared_attack_mode == "shield_bash"
        or (
            enemy.shield_blocks_remaining > 0
            and enemy.sentinel.recovery_turns == 0
        )
    ):
        direction = _sentinel_block_direction(enemy)
        frame_index = (
            current_time // SENTINEL_BLOCK_FRAME_MS
        ) % DIRECTIONAL_FRAME_COUNT

        return assets[
            (
                f"enemy_sentinel_block_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = idle_frame(
        enemy,
        current_time,
        visual_seed,
        SENTINEL_IDLE_FRAME_MS,
    )

    return assets[
        (
            f"enemy_sentinel_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def sentinel_world_position(
    enemy,
    current_time,
    tile_size,
):
    return world_position(
        enemy,
        current_time,
        SENTINEL_MOVE_DURATION_MS,
        tile_size,
    )
