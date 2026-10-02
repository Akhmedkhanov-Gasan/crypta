from game.state import EnemyBehaviorState


BRUTE_FRAME_COUNT = 8
BRUTE_IDLE_FRAME_MS = 160
BRUTE_MOVE_DURATION_MS = 240
BRUTE_ATTACK_DURATION_MS = 480
BRUTE_HURT_DURATION_MS = 400
BRUTE_DIRECTIONS = (
    "down",
    "left",
    "right",
    "up",
)
BRUTE_DEATH_FRAME_MS = 170


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


def _brute_movement_direction(enemy):
    origin = enemy.movement_origin

    if origin is None:
        return "down"

    return _direction_from_delta(
        enemy.column - origin[0],
        enemy.row - origin[1],
    )


def _brute_attack_direction(enemy):
    if not enemy.attack_effect_positions:
        return _brute_movement_direction(enemy)

    target = enemy.attack_effect_positions[0]

    return _direction_from_delta(
        target[0] - enemy.column,
        target[1] - enemy.row,
    )


def _brute_direction(enemy):
    if (
        enemy.attack_effect_positions
        and enemy.attack_animation_started_at
        >= enemy.movement_animation_started_at
    ):
        return _brute_attack_direction(enemy)

    return _brute_movement_direction(enemy)


def _brute_hurt_direction(enemy):
    if enemy.hit_origin is None:
        return _brute_direction(enemy)

    return _direction_from_delta(
        enemy.hit_origin[0] - enemy.column,
        enemy.hit_origin[1] - enemy.row,
    )


def _brute_movement_state(
    enemy,
    current_time,
):
    if (
        enemy.movement_origin is None
        or enemy.movement_animation_started_at <= 0
    ):
        return None

    elapsed = (
        current_time
        - enemy.movement_animation_started_at
    )

    if not 0 <= elapsed < BRUTE_MOVE_DURATION_MS:
        return None

    return elapsed


def _brute_action_frame(
    elapsed,
    duration,
):
    return min(
        BRUTE_FRAME_COUNT - 1,
        elapsed
        * BRUTE_FRAME_COUNT
        // duration,
    )


def _brute_idle_frame(
    enemy,
    current_time,
    visual_seed,
):
    identity_offset = sum(
        (index + 1) * ord(character)
        for index, character in enumerate(enemy.name)
    )

    return (
        current_time // BRUTE_IDLE_FRAME_MS
        + visual_seed
        + identity_offset
    ) % BRUTE_FRAME_COUNT


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


def brute_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    direction = _brute_direction(enemy)

    if enemy.behavior_state is EnemyBehaviorState.DEAD:
        if enemy.death_animation_started_at < 0:
            frame_index = BRUTE_FRAME_COUNT - 1
        else:
            death_elapsed = max(
                0,
                current_time
                - enemy.death_animation_started_at,
            )
            frame_index = min(
                BRUTE_FRAME_COUNT - 1,
                death_elapsed // BRUTE_DEATH_FRAME_MS,
            )

        return assets[
            (
                f"enemy_brute_death_"
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
        and 0 <= hurt_elapsed < BRUTE_HURT_DURATION_MS
    ):
        hurt_direction = _brute_hurt_direction(
            enemy,
        )
        frame_index = _brute_action_frame(
            hurt_elapsed,
            BRUTE_HURT_DURATION_MS,
        )

        return assets[
            (
                f"enemy_brute_hurt_"
                f"{hurt_direction}_{frame_index}"
            )
        ]

    attack_elapsed = (
        current_time
        - enemy.attack_animation_started_at
    )

    if 0 <= attack_elapsed < BRUTE_ATTACK_DURATION_MS:
        attack_direction = _brute_attack_direction(
            enemy,
        )

        if attack_direction not in BRUTE_DIRECTIONS:
            attack_direction = BRUTE_DIRECTIONS[0]

        frame_index = _brute_action_frame(
            attack_elapsed,
            BRUTE_ATTACK_DURATION_MS,
        )

        return assets[
            (
                f"enemy_brute_attack_"
                f"{attack_direction}_{frame_index}"
            )
        ]
    movement_elapsed = _brute_movement_state(
        enemy,
        current_time,
    )

    if movement_elapsed is not None:
        frame_index = _brute_action_frame(
            movement_elapsed,
            BRUTE_MOVE_DURATION_MS,
        )

        return assets[
            (
                f"enemy_brute_walk_"
                f"{direction}_{frame_index}"
            )
        ]

    frame_index = _brute_idle_frame(
        enemy,
        current_time,
        visual_seed,
    )

    return assets[
        (
            f"enemy_brute_idle_"
            f"{direction}_{frame_index}"
        )
    ]


def brute_world_position(
    enemy,
    current_time,
    tile_size,
):
    movement_elapsed = _brute_movement_state(
        enemy,
        current_time,
    )

    if movement_elapsed is None:
        return (
            enemy.column * tile_size,
            enemy.row * tile_size,
        )

    origin = enemy.movement_origin
    progress = _movement_progress(
        movement_elapsed,
        BRUTE_MOVE_DURATION_MS,
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
        ),
    )
