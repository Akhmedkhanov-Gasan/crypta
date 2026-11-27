from acts.act_three.abilities.catalog import (
    get_ability_definition,
)
from acts.act_three.abilities.progression import (
    charge_ability_slots,
    is_ability_slot_unlocked,
)
from acts.act_two.abilities import (
    ability_charge_required,
)
from acts.act_three.settings import (
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    PALADIN_SACRED_GROUND_CHARGES,
    PALADIN_SHIELD_CHARGE_CHARGES,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
)


_ASSASSIN_CHARGES = {
    "q": (
        "teleport_charge",
        ASSASSIN_TELEPORT_CHARGES,
    ),
    "f": (
        "ultimate_charge",
        ASSASSIN_ULTIMATE_CHARGES,
    ),
}
_PALADIN_CHARGES = {
    "q": (
        "paladin_shield_charge_charge",
        PALADIN_SHIELD_CHARGE_CHARGES,
    ),
    "f": (
        "paladin_sacred_ground_charge",
        PALADIN_SACRED_GROUND_CHARGES,
    ),
}
_BERSERKER_CHARGES = {
    "q": (
        "berserker_crushing_leap_charge",
        BERSERKER_CRUSHING_LEAP_CHARGES,
    ),
    "f": (
        "berserker_last_rage_charge",
        BERSERKER_LAST_RAGE_CHARGES,
    ),
}

_SUBCLASS_CHARGES = {
    "assassin": _ASSASSIN_CHARGES,
    "berserker": _BERSERKER_CHARGES,
    "paladin": _PALADIN_CHARGES,
    "summoner": {
        "q": ("summoner_familiar_charge", SUMMONER_FAMILIAR_CHARGES),
        "f": ("summoner_true_form_charge", SUMMONER_TRUE_FORM_CHARGES),
    },
}


PASSIVE_RUNES = frozenset({"rune_of_the_veil", "rune_of_resonance", "rune_of_impact"})


def ability_is_passive(player, slot):
    if slot == "f" and player.subclass == "warlock" and player.act_three.warlock_eternal_bound:
        return True
    if slot == "q" and player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import tower_shield_active

        return tower_shield_active(player)
    return slot == "e" and player.selected_rune_id in PASSIVE_RUNES


def charge_subclass_abilities(player):
    if player.subclass == "assassin" and player.ultimate_animation_active:
        return
    if player.subclass in ("archer", "warlock"):
        charge_ability_slots(player, ("q", "f"))
        return
    for slot, (field, required) in _SUBCLASS_CHARGES.get(player.subclass, {}).items():
        if not is_ability_slot_unlocked(player, slot) or ability_is_passive(player, slot):
            continue
        if slot == "f" and ability_active(player, slot):
            continue
        if player.subclass == "summoner" and slot == "q":
            if player.act_three.summoner_loss_turns > 0:
                continue
            from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement

            required = familiar_recharge_requirement(player)
        setattr(player, field, min(required, getattr(player, field) + 1.0))


def fill_ability_slot(player, slot):
    if slot == "e":
        player.ability_kill_charge = ability_charge_required(player)
        return
    definition = _SUBCLASS_CHARGES.get(player.subclass, {}).get(slot)
    if definition is not None:
        field, required = definition
        setattr(player, field, required)
        return
    ability = get_ability_definition(player.subclass, slot)
    if ability is not None:
        player.ability_slot_charges[slot] = ability.charge_required


def ability_charge_hint(player, slot):
    if player.subclass == "warlock":
        from acts.act_three.abilities.blood_magic import skill_health_cost

        cost = skill_health_cost(player, slot)
        return f"Blood Magic: {cost} HP; no charges. Casting must leave at least 1 HP."
    if player.subclass == "summoner" and slot == "q":
        from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement

        if player.act_three.summoner_loss_turns > 0:
            return f"Familiar recovery: {player.act_three.summoner_loss_turns} turns remaining."
        return f"Requires {familiar_recharge_requirement(player)} successful attack charges. Q is disabled during the ultimate."
    if player.debug_unlimited_abilities:
        return "Free use."
    if ability_is_passive(player, slot):
        return "Passive effect. No charge required."
    if player.subclass == "summoner" and slot == "f":
        return "Gains one charge per successful hit or damaging hit received while inactive."
    if player.subclass == "berserker" and slot == "f":
        return "Gains one charge per successful hit or damaging hit received while Last Rage is inactive."
    if slot == "e":
        return f"Requires {ability_charge_required(player)} successful hits."
    if slot in ("q", "f"):
        return "Gains one charge per successful hit."
    return "Charges through successful attacks."


def ability_active(player, slot):
    if slot == "e":
        return not ability_is_passive(player, slot) and player.invisibility_turns > 0
    if slot == "q" and player.subclass == "summoner":
        return player.summoner_familiar_active
    if slot == "f":
        from acts.act_three.abilities.paladin_runes import paladin_ultimate_active

        return {
            "berserker": player.berserker_last_rage_hits > 0,
            "paladin": paladin_ultimate_active(player),
            "warlock": player.warlock_demon_form_active,
            "summoner": bool(player.act_three.summoner_manifestation and player.act_three.summoner_manifestation["health"] > 0) or player.act_three.summoner_absorption_attacks > 0 or player.act_three.summoner_manifestation_aiming,
            "archer": bool(player.archer_phantoms),
        }.get(player.subclass, False)
    return False

def get_act_three_ability_charge_state(
    player,
    slot,
):
    if not is_ability_slot_unlocked(player, slot):
        return 0.0, 1.0
    if player.subclass == "warlock":
        from acts.act_three.abilities.blood_magic import can_pay_skill
        from acts.act_three.abilities.warlock_runes import demon_attack_cost

        extra = demon_attack_cost(player) if slot == "e" and not ability_is_passive(player, slot) else 0
        return (1.0 if can_pay_skill(player, slot, extra) else 0.0), 1.0
    if slot == "q" and player.subclass == "summoner" and player.act_three.summoner_loss_turns > 0:
        return 0.0, 1.0
    if slot == "f" and player.subclass == "warlock":
        from acts.act_three.rune_master.definitions import has_ability_rune

        if player.warlock_demon_form_active or has_ability_rune(player, "rune_of_blood_pact"):
            return 1.0, 1.0
    if player.debug_unlimited_abilities or ability_is_passive(player, slot):
        return 1.0, 1.0

    if slot == "e":
        return (
            float(player.ability_kill_charge),
            float(ability_charge_required(player)),
        )
    if player.subclass == "summoner":
        spirit = player.act_three.summoner_manifestation
        if slot == "f" and spirit is not None and spirit["health"] > 0:
            return float(spirit["health"]), float(spirit["max_health"])
        if slot == "q":
            from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement

            return float(player.summoner_familiar_charge), float(familiar_recharge_requirement(player))
        if slot == "f" and player.summoner_true_form_active:
            return float(player.summoner_familiar_health), float(max(1, player.summoner_familiar_max_health))
        if slot == "f" and player.act_three.summoner_absorption_attacks > 0:
            from acts.act_three.rune_master.definitions import ABSORPTION_ATTACKS

            return float(player.act_three.summoner_absorption_attacks), float(ABSORPTION_ATTACKS)

    charge_definition = _SUBCLASS_CHARGES.get(
        player.subclass,
        {},
    ).get(slot)

    if charge_definition is not None:
        field_name, required_charge = charge_definition
        return (
            float(getattr(player, field_name)),
            float(required_charge),
        )

    ability = get_ability_definition(
        player.subclass,
        slot,
    )
    if ability is None:
        return 0.0, 1.0

    return (
        float(
            player.ability_slot_charges.get(
                slot,
                0.0,
            )
        ),
        float(ability.charge_required),
    )
