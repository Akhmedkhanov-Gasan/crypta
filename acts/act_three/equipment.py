from acts.act_three.balance import ARMOR_BONUS_PER_RANK


MAX_EQUIPMENT_RANK = 5
EQUIPMENT_BONUS_PER_RANK = 10


def equipment_rank_bonus(rank, *, armor=False):
    step = ARMOR_BONUS_PER_RANK if armor else EQUIPMENT_BONUS_PER_RANK
    return max(0, min(MAX_EQUIPMENT_RANK, rank)) * step


def apply_weapon_bonus(player, damage):
    bonus = equipment_rank_bonus(player.act_three.weapon_rank)
    return (damage * (100 + bonus) + 50) // 100


def apply_armor_bonus(player, damage):
    if damage <= 0:
        return damage

    reduction = equipment_rank_bonus(player.act_three.armor_rank, armor=True)
    return max(1, (damage * (100 - reduction) + 50) // 100)
