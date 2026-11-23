PALADIN_BLOCK_CHANCE = 0.25
PALADIN_BLOCK_CHANCE_CAP = 0.40


def add_paladin_block_chance(player, rune_chance):
    if player.subclass != "paladin":
        return rune_chance

    from acts.act_three.abilities.paladin_runes import crusade_active, tower_shield_active
    from acts.act_three.rune_master.definitions import TOWER_SHIELD_BLOCK_BONUS, TOWER_SHIELD_BLOCK_CAP

    if crusade_active(player):
        return 0.0
    tower = tower_shield_active(player)
    return min(TOWER_SHIELD_BLOCK_CAP if tower else PALADIN_BLOCK_CHANCE_CAP,
               PALADIN_BLOCK_CHANCE + rune_chance + (TOWER_SHIELD_BLOCK_BONUS if tower else 0))
