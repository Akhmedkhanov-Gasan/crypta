from acts.act_two.bloody_altar import adjusted_received_healing


def healing_is_blocked(player):
    from acts.act_three.abilities.berserker_runes import rage_blocks_healing

    return rage_blocks_healing(player)


def heal_player(player, amount: int) -> int:
    if player.health <= 0 or healing_is_blocked(player):
        return 0

    healing = adjusted_received_healing(player, amount)
    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + healing,
    )

    if player.health >= player.max_health:
        player.act_two.open_wound_healing_progress = 0.0

    return player.health - previous_health
