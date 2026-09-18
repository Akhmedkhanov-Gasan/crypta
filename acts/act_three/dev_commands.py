from acts.act_three.abilities import (
    get_subclass_definition,
    unlock_ability_slot,
)
from acts.act_two.abilities import ability_charge_required
from acts.act_three.settings import (
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_LEAP_CHARGES,
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_LAST_RAGE_CHARGES,
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_SHIELD_CHARGE_CHARGES,
    SUMMONER_BOND_CHARGES,
    SUMMONER_FAMILIAR_CHARGES,
    SUMMONER_TRUE_FORM_CHARGES,
    WARLOCK_CURSE_CHARGES,
    WARLOCK_SOUL_EXCHANGE_CHARGES,
)


ACT_THREE_CONSOLE_HELP = (
    "unlockabilities - unlock all class abilities (Act III)",
    "chargeabilities - charge all active abilities (Act III)",
)

_PASSIVE_RUNES = frozenset({
    "rune_of_the_veil",
    "rune_of_resonance",
    "rune_of_impact",
})

_CLASS_CHARGE_FIELDS = {
    "assassin": (
        (
            "teleport_charge",
            ASSASSIN_TELEPORT_CHARGES,
        ),
        (
            "ultimate_charge",
            ASSASSIN_ULTIMATE_CHARGES,
        ),
    ),
    "archer": (
        (
            "archer_empowered_shot_charge",
            ARCHER_EMPOWERED_SHOT_CHARGES,
        ),
        (
            "archer_leap_charge",
            ARCHER_LEAP_CHARGES,
        ),
        (
            "archer_barrage_zone_charge",
            ARCHER_BARRAGE_ZONE_CHARGES,
        ),
    ),
    "berserker": (
        (
            "berserker_crushing_leap_charge",
            BERSERKER_CRUSHING_LEAP_CHARGES,
        ),
        (
            "berserker_last_rage_charge",
            BERSERKER_LAST_RAGE_CHARGES,
        ),
    ),
    "paladin": (
        (
            "paladin_holy_hand_charge",
            PALADIN_HOLY_HAND_CHARGES,
        ),
        (
            "paladin_shield_charge_charge",
            PALADIN_SHIELD_CHARGE_CHARGES,
        ),
        (
            "paladin_holy_shield_charge",
            PALADIN_HOLY_SHIELD_CHARGES,
        ),
    ),
    "warlock": (
        (
            "warlock_curse_charge",
            WARLOCK_CURSE_CHARGES,
        ),
        (
            "warlock_soul_exchange_charge",
            WARLOCK_SOUL_EXCHANGE_CHARGES,
        ),
    ),
    "summoner": (
        (
            "summoner_familiar_charge",
            SUMMONER_FAMILIAR_CHARGES,
        ),
        (
            "summoner_bond_charge",
            SUMMONER_BOND_CHARGES,
        ),
        (
            "summoner_true_form_charge",
            SUMMONER_TRUE_FORM_CHARGES,
        ),
    ),
}


def execute_act_three_console_command(
    game_state,
    parts,
):
    name = parts[0]

    if name not in (
        "unlockabilities",
        "chargeabilities",
    ):
        return None

    if len(parts) != 1:
        return f"Usage: {name}"

    if game_state.floor.presentation_act != 3:
        return "This command is only available in Act III."

    definition = get_subclass_definition(
        game_state.player.subclass
    )
    if definition is None:
        return "Choose an Act III subclass first."

    if name == "unlockabilities":
        return _unlock_all_abilities(
            game_state.player,
            definition,
        )

    return _charge_all_abilities(
        game_state.player,
        definition,
    )


def _unlock_all_abilities(
    player,
    definition,
):
    for slot in definition.abilities:
        unlock_ability_slot(player, slot)

    return f"All {definition.id} abilities unlocked."


def _charge_all_abilities(
    player,
    definition,
):
    inherited_ability_is_passive = (
        player.selected_rune_id in _PASSIVE_RUNES
    )

    for slot, ability in definition.abilities.items():
        if slot == "e" and inherited_ability_is_passive:
            continue

        player.ability_slot_charges[slot] = (
            ability.charge_required
        )

    if not inherited_ability_is_passive:
        player.ability_kill_charge = (
            ability_charge_required(player)
        )

    for field_name, required_charge in (
        _CLASS_CHARGE_FIELDS.get(
            player.subclass,
            (),
        )
    ):
        setattr(
            player,
            field_name,
            required_charge,
        )

    return (
        f"All chargeable {definition.id} abilities charged."
    )
