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
from game.state import EnemyBehaviorState


GOBLIN_IDLE_FRAME_MS = 290
GOBLIN_MOVE_DURATION_MS = 260
GOBLIN_ATTACK_DURATION_MS = 420
GOBLIN_HURT_DURATION_MS = 360
GOBLIN_DEATH_FRAME_MS = 105


def goblin_sprite(
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
                death_elapsed // GOBLIN_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_goblin_death_"
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
        and 0 <= hurt_elapsed < GOBLIN_HURT_DURATION_MS
    ):
        direction = hurt_direction(enemy)
        frame_index = action_frame(
            hurt_elapsed,
            GOBLIN_HURT_DURATION_MS,
        )

        return assets[
            (
                f"enemy_goblin_hurt_"
                f"{direction}_{frame_index}"
            )
        ]

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if 0 <= attack_elapsed < GOBLIN_ATTACK_DURATION_MS:
        direction = attack_direction(enemy)
        frame_index = action_frame(
            attack_elapsed,
            GOBLIN_ATTACK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_goblin_attack_"
                f"{direction}_{frame_index}"
            )
        ]

    move_elapsed = movement_elapsed(
        enemy,
        current_time,
        GOBLIN_MOVE_DURATION_MS,
    )

    if move_elapsed is not None:
        frame_index = action_frame(
            move_elapsed,
            GOBLIN_MOVE_DURATION_MS,
        )

        return assets[
            (
                f"enemy_goblin_walk_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = idle_frame(
        enemy,
        current_time,
        visual_seed,
        GOBLIN_IDLE_FRAME_MS,
    )

    return assets[
        (
            f"enemy_goblin_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def goblin_world_position(
    enemy,
    current_time,
    tile_size,
):
    return world_position(
        enemy,
        current_time,
        GOBLIN_MOVE_DURATION_MS,
        tile_size,
    )
