from application.movement_input import MovementInputProfile
from acts.act_three.movement_timing import PLAYER_STEP_MS


ACT_THREE_MOVEMENT_PROFILE = MovementInputProfile(
    start_delay_ms=PLAYER_STEP_MS,
    repeat_interval_ms=PLAYER_STEP_MS,
    step_duration_ms=PLAYER_STEP_MS,
)
