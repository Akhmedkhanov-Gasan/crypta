DIRECTIONAL_FRAME_COUNT = 8
DIRECTIONAL_DIRECTIONS = (
    "down",
    "left",
    "right",
    "up",
)


def direction_from_delta(
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


def direction_to_position(
    enemy,
    position,
):
    return direction_from_delta(
        position[0] - enemy.column,
        position[1] - enemy.row,
    )


def movement_direction(enemy):
    origin = enemy.movement_origin

    if origin is None:
        return "down"

    return direction_from_delta(
        enemy.column - origin[0],
        enemy.row - origin[1],
    )


def attack_direction(enemy):
    if not enemy.attack_effect_positions:
        return movement_direction(enemy)

    return direction_to_position(
        enemy,
        enemy.attack_effect_positions[0],
    )


def facing_direction(enemy):
    if (
        enemy.attack_effect_positions
        and enemy.attack_animation_started_at
        >= enemy.movement_animation_started_at
    ):
        return attack_direction(enemy)

    return movement_direction(enemy)


def hurt_direction(enemy):
    if enemy.hit_origin is None:
        return facing_direction(enemy)

    return direction_to_position(
        enemy,
        enemy.hit_origin,
    )


def movement_elapsed(
    enemy,
    current_time,
    duration,
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

    if not 0 <= elapsed < duration:
        return None

    return elapsed


def action_frame(
    elapsed,
    duration,
):
    return min(
        DIRECTIONAL_FRAME_COUNT - 1,
        elapsed
        * DIRECTIONAL_FRAME_COUNT
        // duration,
    )


def idle_frame(
    enemy,
    current_time,
    visual_seed,
    frame_duration,
):
    identity_offset = sum(
        (index + 1) * ord(character)
        for index, character in enumerate(enemy.name)
    )

    return (
        current_time // frame_duration
        + visual_seed
        + identity_offset
    ) % DIRECTIONAL_FRAME_COUNT


def world_position(
    enemy,
    current_time,
    duration,
    tile_size,
):
    elapsed = movement_elapsed(
        enemy,
        current_time,
        duration,
    )

    if elapsed is None:
        return (
            enemy.column * tile_size,
            enemy.row * tile_size,
        )

    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    smooth_progress = (
        progress
        * progress
        * (3.0 - 2.0 * progress)
    )
    progress = (
        progress * 0.85
        + smooth_progress * 0.15
    )
    origin = enemy.movement_origin

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
