from math import ceil, floor

from acts.act_two.ability_scaling import mage_basic_attack_damage_bonus
from game.attributes import attribute_stat_changes_for_rank


ARCHER_SHOT_DAMAGE_BONUS = 1
SUMMONER_BOUND_ATTACK_MULTIPLIER = 0.65
SUMMONER_FAMILIAR_DAMAGE_MULTIPLIER = 0.5
PALADIN_GROUND_WILL_SCALING = 0.5


def magical_attack_damage_range(player):
    valor = attribute_stat_changes_for_rank(
        "valor", player.attribute_ranks.get("valor", 0),
        rank_limit=None,
    )
    bonus = mage_basic_attack_damage_bonus(
        player.attribute_ranks.get("will", 0),
    )
    minimum = max(1, player.damage_min - valor.damage_min + bonus)
    maximum = max(minimum, player.damage_max - valor.damage_max + bonus)
    return minimum, maximum


def basic_attack_damage_range(player):
    if player.player_class == "mage":
        return magical_attack_damage_range(player)
    return player.damage_min, player.damage_max


def archer_shot_damage_range(player):
    minimum, maximum = basic_attack_damage_range(player)
    return (
        minimum + ARCHER_SHOT_DAMAGE_BONUS,
        maximum + ARCHER_SHOT_DAMAGE_BONUS,
    )


def summoner_attack_multiplier(player):
    return (
        SUMMONER_BOUND_ATTACK_MULTIPLIER
        if player.summoner_familiar_active
        else 1.0
    )


def familiar_damage_range(player):
    minimum, maximum = magical_attack_damage_range(player)
    return (
        max(1, floor(minimum * SUMMONER_FAMILIAR_DAMAGE_MULTIPLIER)),
        max(1, ceil(maximum * SUMMONER_FAMILIAR_DAMAGE_MULTIPLIER)),
    )


def paladin_ground_damage_bonus(player):
    return ceil(
        max(0, player.attribute_ranks.get("will", 0))
        * PALADIN_GROUND_WILL_SCALING
    )
