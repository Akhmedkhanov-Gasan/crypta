from acts.act_three.abilities.catalog import (
    get_ability_definition,
)
from acts.act_two.abilities import (
    ability_charge_required,
)
from acts.act_three.settings import (
    ASSASSIN_TELEPORT_CHARGES,
    ASSASSIN_ULTIMATE_CHARGES,
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


def get_act_three_ability_charge_state(
    player,
    slot,
):
    if slot == "e":
        return (
            float(player.ability_kill_charge),
            float(ability_charge_required(player)),
        )

    if player.subclass == "assassin":
        charge_definition = _ASSASSIN_CHARGES.get(
            slot
        )
        if charge_definition is not None:
            field_name, required_charge = (
                charge_definition
            )
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
