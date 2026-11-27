from acts.act_three.abilities.catalog import (
    get_subclass_definition,
)


ABILITY_SLOTS = frozenset({
    "q",
    "e",
    "f",
})

DEFAULT_UNLOCKED_ABILITY_SLOTS = frozenset({
    "e",
})

def initialize_act_three_progression(
    player,
    unlock_all=False,
):
    player.weapon_rank = 0
    player.armor_rank = 0
    player.unlocked_ability_slots = set(
        ABILITY_SLOTS
        if unlock_all
        else DEFAULT_UNLOCKED_ABILITY_SLOTS
    )
    player.ability_slot_charges = {
        slot: 0.0
        for slot in ABILITY_SLOTS
    }
    player.debug_unlimited_abilities = False


def is_ability_slot_unlocked(
    player,
    slot,
):
    if slot not in ABILITY_SLOTS:
        return False
    if player.debug_unlimited_abilities or slot == "e":
        return True
    return (
        slot in ABILITY_SLOTS
        and slot in player.unlocked_ability_slots
    )


def unlock_ability_slot(
    player,
    slot,
):
    if slot not in ABILITY_SLOTS:
        raise ValueError(
            f"Unknown ability slot: {slot}"
        )

    if slot in player.unlocked_ability_slots:
        return
    player.unlocked_ability_slots.add(slot)
    from acts.act_three.abilities.charges import fill_ability_slot

    fill_ability_slot(player, slot)


def get_ability_slot_charge(
    player,
    slot,
):
    if slot not in ABILITY_SLOTS:
        raise ValueError(
            f"Unknown ability slot: {slot}"
        )

    return player.ability_slot_charges.get(
        slot,
        0.0,
    )


def clear_ability_slot_charge(
    player,
    slot,
):
    if slot not in ABILITY_SLOTS:
        raise ValueError(
            f"Unknown ability slot: {slot}"
        )

    player.ability_slot_charges[slot] = 0.0


def is_ability_slot_charged(
    player,
    slot,
):
    if not is_ability_slot_unlocked(player, slot):
        return False

    if player.debug_unlimited_abilities:
        return True

    definition = get_subclass_definition(player.subclass)
    if definition is None:
        return False

    ability = definition.abilities.get(slot)
    if ability is None:
        return False

    return (
        get_ability_slot_charge(player, slot)
        >= ability.charge_required
    )


def charge_ability_slots(
    player,
    slots,
):
    definition = get_subclass_definition(player.subclass)
    if definition is None:
        return

    for slot in slots:
        if not is_ability_slot_unlocked(player, slot):
            continue

        ability = definition.abilities.get(slot)
        if ability is None:
            continue

        current_charge = get_ability_slot_charge(
            player,
            slot,
        )
        player.ability_slot_charges[slot] = min(
            ability.charge_required,
            current_charge + 1.0,
        )
