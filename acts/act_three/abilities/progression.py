ABILITY_SLOTS = frozenset({
    "q",
    "e",
    "f",
})

DEFAULT_UNLOCKED_ABILITY_SLOTS = frozenset({
    "q",
    "e",
    "f",
})

MASTERY_CHARGE_RATES = (
    1.0,
    1.1,
    1.2,
    1.3,
    1.4,
    1.5,
)


def initialize_act_three_progression(
    player,
    unlock_all=False,
):
    player.mastery_rank = 0
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


def is_ability_slot_unlocked(
    player,
    slot,
):
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

    player.unlocked_ability_slots.add(slot)


def get_mastery_charge_rate(player):
    rank = max(
        0,
        min(
            len(MASTERY_CHARGE_RATES) - 1,
            player.mastery_rank,
        ),
    )

    return MASTERY_CHARGE_RATES[rank]


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
