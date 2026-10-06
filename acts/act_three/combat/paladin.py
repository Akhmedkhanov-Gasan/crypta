PALADIN_BLOCK_CHANCE = 0.25
PALADIN_BLOCK_CHANCE_CAP = 0.40


def add_paladin_block_chance(player, rune_chance):
    if player.subclass != "paladin":
        return rune_chance

    return min(
        PALADIN_BLOCK_CHANCE_CAP,
        PALADIN_BLOCK_CHANCE + rune_chance,
    )
