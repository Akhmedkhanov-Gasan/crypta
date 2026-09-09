def apply_bleed(enemy, damage: int, turns: int) -> None:
    if enemy.health <= 0 or damage <= 0 or turns <= 0:
        return

    previous_damage = (
        enemy.bleed_damage
        if enemy.bleed_turns > 0
        else 0
    )
    enemy.bleed_damage = max(previous_damage, damage)
    enemy.bleed_turns = turns
