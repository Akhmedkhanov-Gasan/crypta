ACT_TWO_ENEMY_MOVE_MS = 180
ACT_TWO_ENEMY_KNOCKBACK_MS = 260

_KNOCKBACK_MOVEMENT_KINDS = {
    "power_cleave_knockback",
    "arcane_burst_knockback",
}


def enemy_movement_duration(enemy) -> int:
    return (
        ACT_TWO_ENEMY_KNOCKBACK_MS
        if enemy.get("movement_animation_kind")
        in _KNOCKBACK_MOVEMENT_KINDS
        else ACT_TWO_ENEMY_MOVE_MS
    )


def attack_telegraph_is_visible(
    enemy,
    current_time: int,
) -> bool:
    return (
        bool(enemy["attack_targets"])
        and current_time
        >= enemy.get("attack_telegraph_visible_at", 0)
    )