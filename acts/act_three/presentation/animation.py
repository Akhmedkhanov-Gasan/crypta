from functools import lru_cache





_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

def _stable_text_seed(text):
    seed = 2166136261

    for character in text:
        seed ^= ord(character)
        seed = (seed * 16777619) & 0xFFFFFFFF

    return seed


def _next_idle_random(state):
    state = (
        state * 1664525 + 1013904223
    ) & 0xFFFFFFFF
    return state, state


@lru_cache(maxsize=None)
def _idle_timeline(identity_seed):
    state = identity_seed & 0xFFFFFFFF
    timeline = []

    for _ in range(_IDLE_TIMELINE_CYCLE_COUNT):
        state, neutral_roll = _next_idle_random(state)
        state, inhale_roll = _next_idle_random(state)
        state, full_breath_roll = _next_idle_random(state)
        state, exhale_roll = _next_idle_random(state)
        durations = (
            2800 + neutral_roll % 2001,
            650 + inhale_roll % 301,
            1200 + full_breath_roll % 1201,
            650 + exhale_roll % 301,
        )
        timeline.extend(
            zip(_IDLE_FRAME_SEQUENCE, durations)
        )

    total_duration = sum(
        duration for _, duration in timeline
    )
    return tuple(timeline), total_duration


def _idle_frame(current_time, identity_seed):
    timeline, total_duration = _idle_timeline(
        identity_seed
    )
    phase_offset = (
        identity_seed * 2654435761
    ) % total_duration
    elapsed = (
        current_time + phase_offset
    ) % total_duration

    for frame_index, duration in timeline:
        if elapsed < duration:
            return frame_index

        elapsed -= duration

    return 0


def _movement_frame(current_time, started_at):
    return (
        (current_time - started_at) // _MOVE_FRAME_DURATION_MS
    ) % _MOVE_FRAME_COUNT
