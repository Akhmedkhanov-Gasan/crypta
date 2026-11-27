from math import ceil

from acts.act_three.ability_scaling import summoner_attack_multiplier
from acts.act_three.equipment import equipment_rank_bonus
from acts.act_three.settings import (
    BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_CRITICAL_HEALTH_RATIO,
    BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER,
    BERSERKER_RAGE_INJURED_HEALTH_RATIO,
    SUMMONER_TRUE_FORM_DAMAGE_BONUS,
    WARLOCK_CURSE_DAMAGE_MULTIPLIER,
)
from acts.act_two.bloody_altar import GLASS_HEART, GLASS_HEART_DAMAGE_MULTIPLIER, has_bloody_pact


def scaled_attack_damage(player, enemy, damage, critical, attacker, multiplier=1.0):
    if player.subclass == "summoner" and player.summoner_true_form_active and attacker == "familiar":
        damage += SUMMONER_TRUE_FORM_DAMAGE_BONUS
    if enemy.curse_turns > 0:
        multiplier *= WARLOCK_CURSE_DAMAGE_MULTIPLIER
    if player.subclass == "berserker" and player.health > 0:
        from acts.act_three.abilities.berserker_runes import rage_rune_active
        from acts.act_three.rune_master.definitions import DEATH_WISH_MULTIPLIER

        ratio = player.health / player.max_health
        if player.berserker_last_rage_hits > 0 or ratio <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO:
            multiplier *= BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER
        elif ratio <= BERSERKER_RAGE_INJURED_HEALTH_RATIO:
            multiplier *= BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER
        if attacker == "hero" and rage_rune_active(player, "rune_of_death_wish"):
            multiplier *= DEATH_WISH_MULTIPLIER
    if critical:
        multiplier *= player.critical_damage_multiplier
    if attacker in ("hero", "phantom", "familiar", "greater_manifestation"):
        multiplier *= 1 + equipment_rank_bonus(player.act_three.weapon_rank) / 100
        if has_bloody_pact(player, GLASS_HEART):
            multiplier *= GLASS_HEART_DAMAGE_MULTIPLIER
    if attacker == "hero" and player.subclass == "warlock":
        from acts.act_three.abilities.warlock_runes import demon_damage_multiplier

        multiplier *= demon_damage_multiplier(player)
    if attacker == "hero" and player.subclass == "summoner":
        from acts.act_three.abilities.summoner_runes import absorption_damage_multiplier

        multiplier *= absorption_damage_multiplier(player) * summoner_attack_multiplier(player)
    if attacker == "hero" and player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import (
            paladin_attack_multiplier,
            round_tower_damage,
            tower_shield_active,
        )

        multiplier *= paladin_attack_multiplier(player)
        if tower_shield_active(player):
            return round_tower_damage(player, damage * multiplier)
    return max(1, ceil(damage * multiplier)) if damage > 0 else 0
