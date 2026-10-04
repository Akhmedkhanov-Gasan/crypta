WARDEN_ATTACK_FRAME_DURATIONS = (
    65, 80, 60, 70, 85, 130, 180, 230,
)
WARDEN_ATTACK_DURATION_MS = sum(WARDEN_ATTACK_FRAME_DURATIONS)
WARDEN_ATTACK_IMPACT_MS = sum(WARDEN_ATTACK_FRAME_DURATIONS[:4])
WARDEN_HURT_DURATION_MS = 480
WARDEN_DEATH_FRAME_DURATIONS = (
    140, 160, 180, 140, 110, 220, 260, 350,
)
WARDEN_DEATH_DURATION_MS = sum(WARDEN_DEATH_FRAME_DURATIONS)
WARDEN_DEATH_IMPACT_MS = sum(WARDEN_DEATH_FRAME_DURATIONS[:5])
WARDEN_DEATH_EFFECT_DURATION_MS = 2400


def warden_death_frame(enemy, current_time):
    if enemy.death_animation_started_at < 0:
        return len(WARDEN_DEATH_FRAME_DURATIONS) - 1

    remaining = max(
        0,
        current_time - enemy.death_animation_started_at,
    )

    for index, duration in enumerate(WARDEN_DEATH_FRAME_DURATIONS):
        if remaining < duration:
            return index
        remaining -= duration

    return len(WARDEN_DEATH_FRAME_DURATIONS) - 1


def _attack_frame(elapsed):
    remaining = max(0, elapsed)

    for index, duration in enumerate(WARDEN_ATTACK_FRAME_DURATIONS):
        if remaining < duration:
            return index
        remaining -= duration

    return len(WARDEN_ATTACK_FRAME_DURATIONS) - 1

def _direction_from_delta(dx, dy):
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"

    if dy:
        return "down" if dy > 0 else "up"

    return "down"


def warden_target_direction(enemy, target):
    center_column = (
        enemy.column
        + (enemy.footprint_width - 1) / 2
    )
    center_row = (
        enemy.row
        + (enemy.footprint_height - 1) / 2
    )
    return _direction_from_delta(
        target[0] - center_column,
        target[1] - center_row,
    )


def warden_direction(enemy):
    if enemy.attack_targets:
        return warden_target_direction(
            enemy,
            enemy.attack_targets[0],
        )

    if (
        enemy.attack_effect_positions
        and enemy.attack_animation_started_at
        >= enemy.movement_animation_started_at
    ):
        return warden_target_direction(
            enemy,
            enemy.attack_effect_positions[0],
        )

    if enemy.movement_origin is not None:
        return _direction_from_delta(
            enemy.column - enemy.movement_origin[0],
            enemy.row - enemy.movement_origin[1],
        )

    return "down"


def _action_frame(elapsed, duration, frame_count):
    return min(
        frame_count - 1,
        max(0, int(elapsed * frame_count / duration)),
    )


def warden_action(
    enemy,
    current_time,
    move_duration,
    frame_count,
):
    direction = warden_direction(enemy)
    hurt_elapsed = current_time - enemy.hit_animation_started_at
    attack_elapsed = current_time - enemy.attack_animation_started_at
    move_elapsed = current_time - enemy.movement_animation_started_at

    if (
        enemy.hit_damage > 0
        and not enemy.hit_dodged
        and enemy.hit_animation_started_at >= 0
        and 0 <= hurt_elapsed < WARDEN_HURT_DURATION_MS
        and enemy.hit_animation_started_at
        >= max(
            enemy.attack_animation_started_at,
            enemy.movement_animation_started_at,
        )
    ):
        if enemy.hit_origin is not None:
            direction = warden_target_direction(
                enemy,
                enemy.hit_origin,
            )

        return (
            "hurt",
            direction,
            _action_frame(
                hurt_elapsed,
                WARDEN_HURT_DURATION_MS,
                frame_count,
            ),
        )

    if (
        enemy.attack_effect_positions
        and 0 <= attack_elapsed < WARDEN_ATTACK_DURATION_MS
        and enemy.attack_animation_started_at
        >= enemy.movement_animation_started_at
    ):
        return (
            "attack",
            warden_target_direction(
                enemy,
                enemy.attack_effect_positions[0],
            ),
            _attack_frame(attack_elapsed),
        )
    if enemy.attack_targets:
        return "attack", direction, 1
    if (
        enemy.movement_origin is not None
        and enemy.movement_animation_started_at > 0
        and 0 <= move_elapsed < move_duration
    ):
        direction = _direction_from_delta(
            enemy.column - enemy.movement_origin[0],
            enemy.row - enemy.movement_origin[1],
        )
        return (
            "walk",
            direction,
            _action_frame(
                move_elapsed,
                move_duration,
                frame_count,
            ),
        )

    return "idle", direction, 0
