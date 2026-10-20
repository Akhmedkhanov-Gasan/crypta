def attack_direction(enemy):
    positions = enemy.get(
        "attack_effect_positions",
        (),
    )
    if not positions:
        return 0, 0

    target_column, target_row = positions[0]
    delta_x = target_column - enemy["column"]
    delta_y = target_row - enemy["row"]

    if abs(delta_x) >= abs(delta_y):
        if delta_x == 0:
            return 0, 0
        return (
            1 if delta_x > 0 else -1,
            0,
        )

    if delta_y == 0:
        return 0, 0

    return (
        0,
        1 if delta_y > 0 else -1,
    )


def stepped_attack_offset(
    enemy,
    current_time,
    enemy_type,
    frame_start,
    frame_end,
    distance,
):
    if enemy["type"] != enemy_type:
        return 0, 0

    started_at = enemy.get(
        "attack_animation_started_at",
        0,
    )
    if started_at <= 0:
        return 0, 0

    elapsed = current_time - started_at
    if not frame_start <= elapsed < frame_end:
        return 0, 0

    direction_x, direction_y = attack_direction(enemy)
    return (
        direction_x * distance,
        direction_y * distance,
    )


__all__ = [
    "attack_direction",
    "stepped_attack_offset",
]
