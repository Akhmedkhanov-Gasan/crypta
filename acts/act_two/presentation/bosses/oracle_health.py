def limit_oracle_phase_one_damage(enemy, damage):
    if (
        enemy.type != "oracle"
        or enemy.oracle_phase != 1
    ):
        return damage

    threshold = max(1, enemy.max_health // 2)
    available_health = max(
        0,
        enemy.health - threshold,
    )
    damage = min(damage, available_health)

    if enemy.health - damage <= threshold:
        enemy.phase_transition_pending = True

    return damage
