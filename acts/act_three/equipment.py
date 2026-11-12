MAX_EQUIPMENT_RANK = 5
EQUIPMENT_BONUS_PER_RANK = 10


def equipment_rank_bonus(rank):
    return max(0, min(MAX_EQUIPMENT_RANK, rank)) * EQUIPMENT_BONUS_PER_RANK


def apply_weapon_bonus(player, damage):
    bonus = equipment_rank_bonus(player.act_three.weapon_rank)
    return (damage * (100 + bonus) + 50) // 100


def apply_armor_bonus(player, damage):
    if damage <= 0:
        return damage

    reduction = equipment_rank_bonus(player.act_three.armor_rank)
    return max(1, (damage * (100 - reduction) + 50) // 100)
