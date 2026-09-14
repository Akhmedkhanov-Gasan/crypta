PLAYER_MOVE_DURATION_MS = 200
ASSASSIN_IDLE_FRAME_COUNT = 8
ASSASSIN_WALK_FRAME_COUNT = 8
ASSASSIN_IDLE_FRAME_DURATION_MS = 270


def player_movement_progress(
    current_time,
    started_at,
):
    if started_at <= 0:
        return None

    elapsed = current_time - started_at

    if not 0 <= elapsed < PLAYER_MOVE_DURATION_MS:
        return None

    return elapsed / PLAYER_MOVE_DURATION_MS


def movement_frame_for_progress(
    progress,
    frame_count,
):
    return min(
        frame_count - 1,
        int(progress * frame_count),
    )


def assassin_idle_frame(current_time):
    return (
        current_time // ASSASSIN_IDLE_FRAME_DURATION_MS
    ) % ASSASSIN_IDLE_FRAME_COUNT


def interpolate_player_position(
    origin,
    destination,
    progress,
):
    eased_progress = progress * progress * (3 - 2 * progress)

    return (
        round(
            origin[0]
            + (destination[0] - origin[0]) * eased_progress
        ),
        round(
            origin[1]
            + (destination[1] - origin[1]) * eased_progress
        ),
    )


def assassin_walk_direction(facing_direction):
    column_change, row_change = facing_direction

    if column_change < 0:
        return "left"

    if column_change > 0:
        return "right"

    if row_change < 0:
        return "up"

    return "down"
