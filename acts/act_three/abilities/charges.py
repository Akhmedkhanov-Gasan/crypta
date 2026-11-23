from acts.act_three.abilities.catalog import (
    get_ability_definition,
)
from acts.act_three.abilities.progression import is_ability_slot_unlocked
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
    if slot == "q" and player.subclass == "paladin":
        from acts.act_three.abilities.paladin_runes import tower_shield_active

        return tower_shield_active(player)
    return slot == "e" and player.selected_rune_id in PASSIVE_RUNES


def ability_charge_hint(player, slot):
    if player.subclass == "summoner" and slot == "q":
        from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement

        return f"Recall requires {familiar_recharge_requirement(player)} successful attack charges. Q is disabled during the ultimate."
    if player.subclass == "warlock" and slot == "f":
        from acts.act_three.rune_master.definitions import has_ability_rune

        if player.act_three.warlock_eternal_bound:
            return "Eternal Form is permanent for this run."
        if has_ability_rune(player, "rune_of_blood_pact"):
            return "No activation charge required. F reverts; re-entering resets attack escalation."
    if player.debug_unlimited_abilities:
        return "Unlimited uses enabled by the console."
    if ability_is_passive(player, slot):
        return "Passive effect. No charge required."
    if player.subclass == "summoner" and slot == "f":
        return "Charges through successful attacks and incoming damage."
    if player.subclass == "archer" and slot in ("q", "f"):
        return "Charges through successful attacks; Mastery increases charge gained."
    if player.subclass == "warlock" and slot in ("q", "f"):
        return "Charges through successful attacks; Mastery increases charge gained."
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
            "summoner": player.summoner_true_form_active or player.act_three.summoner_absorption_attacks > 0,
            "archer": bool(player.archer_phantoms),
        }.get(player.subclass, False)
    return False

def get_act_three_ability_charge_state(
    player,
    slot,
):
    if not is_ability_slot_unlocked(player, slot):
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
