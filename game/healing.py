from acts.act_two.bloody_altar import adjusted_received_healing


def heal_player(player, amount: int) -> int:
    if player.health <= 0:
        return 0

    healing = adjusted_received_healing(player, amount)
    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + healing,
    )

    if player.health >= player.max_health:
        player.act_two.open_wound_healing_progress = 0.0

    if player.summoner_bond_active:
        player.summoner_familiar_health = player.health

    return player.health - previous_health
