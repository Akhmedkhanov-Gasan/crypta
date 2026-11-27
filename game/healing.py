from acts.act_two.bloody_altar import adjusted_received_healing


def healing_is_blocked(player, *, source=None):
    from acts.act_three.abilities.berserker_runes import rage_blocks_healing

    from acts.act_three.bloody_altar.catalog import has_pact

    return rage_blocks_healing(player) or (has_pact(player, "endless_hunger") and source != "lifesteal")


def heal_player(player, amount: int, *, source=None) -> int:
    if player.health <= 0 or healing_is_blocked(player, source=source):
        return 0

    healing = adjusted_received_healing(player, amount)
    from acts.act_three.bloody_altar.effects import adjusted_healing

    healing = adjusted_healing(player, healing, source)
    previous_health = player.health
    player.health = min(
        player.max_health,
        player.health + healing,
    )

    if player.health >= player.max_health:
        player.act_two.open_wound_healing_progress = 0.0
        player.act_three.altar_healing_progress = 0.0

    return player.health - previous_health
