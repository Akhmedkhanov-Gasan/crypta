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


def attack_damage_factors(player, enemy, critical=False, attacker="hero", multiplier=1.0, *, floor=None, basic=False):
    from acts.act_three.bloody_altar.effects import critical_multiplier, outgoing_multiplier
    from acts.act_three.bloody_altar.catalog import PACTS_BY_ID

    factors = [("Ability", multiplier)]
    if enemy is not None and enemy.curse_turns > 0:
        factors.append(("Curse", WARLOCK_CURSE_DAMAGE_MULTIPLIER))
    if player.subclass == "berserker" and player.health > 0:
        from acts.act_three.abilities.berserker_runes import rage_rune_active
        from acts.act_three.rune_master.definitions import DEATH_WISH_MULTIPLIER

        ratio = player.health / player.max_health
        if player.berserker_last_rage_hits > 0 or ratio <= BERSERKER_RAGE_CRITICAL_HEALTH_RATIO:
            factors.append(("Rage", BERSERKER_RAGE_CRITICAL_DAMAGE_MULTIPLIER))
        elif ratio <= BERSERKER_RAGE_INJURED_HEALTH_RATIO:
            factors.append(("Rage", BERSERKER_RAGE_INJURED_DAMAGE_MULTIPLIER))
        if attacker == "hero" and rage_rune_active(player, "rune_of_death_wish"):
            factors.append(("Rune of Death Wish", DEATH_WISH_MULTIPLIER))
    if critical:
        factors.append(("Critical hit", critical_multiplier(player)))
    if attacker in ("hero", "phantom", "familiar", "greater_manifestation"):
        pact = PACTS_BY_ID.get(player.act_three.altar_pact_id)
        factors.append((pact.name if pact else "Altar", outgoing_multiplier(player, enemy, floor, basic=basic and attacker == "hero")))
        factors.append(("Weapon", 1 + equipment_rank_bonus(player.act_three.weapon_rank) / 100))
        if has_bloody_pact(player, GLASS_HEART):
            factors.append(("Glass Heart", GLASS_HEART_DAMAGE_MULTIPLIER))
    if attacker == "hero" and player.subclass == "warlock":
        from acts.act_three.abilities.warlock_runes import demon_damage_multiplier

        rune_names = {"rune_of_eternal_form": "Rune of Eternal Form", "rune_of_blood_pact": "Rune of Blood Pact"}
        factors.append((rune_names.get(player.act_three.warlock_demon_rune, "Demon Form"), demon_damage_multiplier(player)))
    if attacker == "hero" and player.subclass == "summoner":
        from acts.act_three.abilities.summoner_runes import absorption_damage_multiplier

        absorption = absorption_damage_multiplier(player)
        familiar = summoner_attack_multiplier(player)
        name = "Rune of Absorption + released familiar" if absorption != 1 and familiar != 1 else "Rune of Absorption" if absorption != 1 else "Released familiar"
        factors.append((name, absorption * familiar))
    if attacker == "hero" and player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import crusade_active, tower_shield_active
        from acts.act_three.rune_master.definitions import FERVENT_CRUSADE_DAMAGE_MULTIPLIER, TOWER_SHIELD_DAMAGE_MULTIPLIER

        if tower_shield_active(player):
            factors.append(("Rune of Tower Shield", TOWER_SHIELD_DAMAGE_MULTIPLIER))
        if crusade_active(player):
            factors.append(("Rune of Fervent Crusade", FERVENT_CRUSADE_DAMAGE_MULTIPLIER))
    return tuple((name, value) for name, value in factors if value != 1.0)


def scaled_attack_damage(player, enemy, damage, critical, attacker, multiplier=1.0, *, floor=None, basic=False):
    if player.subclass == "summoner" and player.summoner_true_form_active and attacker == "familiar":
        damage += SUMMONER_TRUE_FORM_DAMAGE_BONUS
    factors = attack_damage_factors(player, enemy, critical, attacker, multiplier, floor=floor, basic=basic)
    multiplier = 1.0
    for _, factor in factors:
        multiplier *= factor
    if attacker == "hero" and player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import round_tower_damage, tower_shield_active

        if tower_shield_active(player):
            return round_tower_damage(player, damage * multiplier)
    return max(1, ceil(damage * multiplier)) if damage > 0 else 0
