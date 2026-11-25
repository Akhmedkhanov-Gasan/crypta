PLAYER_STEP_MS = 220
PLAYER_FOOT_PLANT_HOLD_MS = 25
PLAYER_POSE_HOLD_MS = 60
PLAYER_WALK_PHASE_PER_STEP = 0.5
PLAYER_WALK_START_PHASE = 0.75


def player_footfall_delay(step_ms):
    travel_fraction = (PLAYER_STEP_MS - PLAYER_FOOT_PLANT_HOLD_MS) / PLAYER_STEP_MS
    return round(step_ms * travel_fraction)
