


from game.state import EnemyBehaviorState


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
_ENEMY_DEATH_IMPACT_HOLD_MS = 190
_ENEMY_DEATH_COLLAPSE_END_MS = {
    "archer": 720,
    "brute": 850,
    "priest": 780,
    "sentinel": 900,
}

from acts.act_three.presentation.animation import (
    _idle_frame,
    _movement_frame,
    _stable_text_seed,
)

def _enemy_sprite(
    assets,
    enemy,
    current_time,
    visual_seed,
):
    if (
        enemy.type in _ENEMY_DEATH_COLLAPSE_END_MS
        and enemy.behavior_state is EnemyBehaviorState.DEAD
    ):
        if enemy.death_animation_started_at < 0:
            return assets[f"enemy_{enemy.type}_death_1"]

        death_elapsed = (
            current_time - enemy.death_animation_started_at
        )
        if death_elapsed < _ENEMY_DEATH_IMPACT_HOLD_MS:
            return assets[f"enemy_{enemy.type}_idle_0"]
        if (
            death_elapsed
            < _ENEMY_DEATH_COLLAPSE_END_MS[enemy.type]
        ):
            return assets[f"enemy_{enemy.type}_death_0"]
        return assets[f"enemy_{enemy.type}_death_1"]

    if (
        enemy.type in (
            "archer",
            "brute",
            "sentinel",
        )
        and 0 <= current_time - enemy.attack_animation_started_at
        < _ATTACK_FRAME_DURATION_MS
    ):
        return assets[f"enemy_{enemy.type}_attack"]

    if (
        enemy.type == "priest"
        and 0 <= current_time - enemy.attack_animation_started_at
        < _ATTACK_FRAME_DURATION_MS
    ):
        return assets["priest_heal_cast"]

    if (
        enemy.type in (
            "archer",
            "brute",
            "priest",
            "sentinel",
        )
        and 0 <= current_time - enemy.movement_animation_started_at
        < _MOVE_FRAME_COUNT * _MOVE_FRAME_DURATION_MS
    ):
        return assets[
            f"enemy_{enemy.type}_walk_{_movement_frame(
                current_time,
                enemy.movement_animation_started_at,
            )}"
        ]

    if (
        enemy.type == "sentinel"
        and enemy.shield_turns > 0
    ):
        return assets["sentinel_guard"]

    if (
        enemy.type == "priest"
        and enemy.behavior_state
        is EnemyBehaviorState.PREPARING_HEAL
        and enemy.heal_target is not None
        and enemy.heal_target.health > 0
    ):
        return assets["priest_heal_cast"]

    if enemy.type in (
        "archer",
        "brute",
        "sentinel",
        "priest",
    ):
        identity_seed = (
            visual_seed
            ^ _stable_text_seed(
                f"{enemy.type}:{enemy.name}"
            )
        )
        frame_index = _idle_frame(
            current_time,
            identity_seed,
        )
        return assets[
            f"enemy_{enemy.type}_idle_{frame_index}"
        ]

    return assets.get(
        f"enemy_{enemy.type}",
        assets["enemy_brute"],
    )
