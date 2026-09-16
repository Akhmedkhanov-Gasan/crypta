"""Act Three subclass abilities."""

from acts.act_three.abilities.progression import (
    ABILITY_SLOTS,
    DEFAULT_UNLOCKED_ABILITY_SLOTS,
    MASTERY_CHARGE_RATES,
    clear_ability_slot_charge,
    get_ability_slot_charge,
    get_mastery_charge_rate,
    initialize_act_three_progression,
    is_ability_slot_unlocked,
    unlock_ability_slot,
)
from acts.act_three.abilities.catalog import (
    AbilityDefinition,
    PassiveDefinition,
    SubclassDefinition,
    SUBCLASS_DEFINITIONS,
    get_ability_definition,
    get_passive_definition,
    get_subclass_definition,
)

__all__ = [
    "ABILITY_SLOTS",
    "DEFAULT_UNLOCKED_ABILITY_SLOTS",
    "MASTERY_CHARGE_RATES",
    "clear_ability_slot_charge",
    "get_ability_slot_charge",
    "get_mastery_charge_rate",
    "initialize_act_three_progression",
    "is_ability_slot_unlocked",
    "unlock_ability_slot",
    "AbilityDefinition",
    "PassiveDefinition",
    "SubclassDefinition",
    "SUBCLASS_DEFINITIONS",
    "get_ability_definition",
    "get_passive_definition",
    "get_subclass_definition",
]
