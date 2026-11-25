from application.movement_input import MovementInputProfile
from acts.act_three.movement_timing import PLAYER_STEP_MS


ACT_THREE_MOVEMENT_PROFILE = MovementInputProfile(
    start_delay_ms=PLAYER_STEP_MS,
    repeat_interval_ms=PLAYER_STEP_MS,
    step_duration_ms=PLAYER_STEP_MS,
    continuous_steps=True,
)


def player_special_movement_active(player):
    return (
        player.ultimate_animation_active
        or any(
            getattr(player, name, None) is not None
            for name in (
                "teleport_camera_origin",
                "archer_leap_origin",
                "berserker_crushing_leap_origin",
                "paladin_shield_charge_origin",
            )
        )
    )
