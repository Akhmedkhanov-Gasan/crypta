from math import ceil

from acts.act_two.settings import (
    MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS,
    MAGE_ARCANE_BURST_WILL_SCALING,
    MAGE_BASIC_ATTACK_WILL_SCALING,
    ROGUE_AMBUSH_INSTINCT_DIVISOR,
    WARRIOR_CLEAVE_DAMAGE_BONUS,
    WARRIOR_CLEAVE_VALOR_SCALING,
)


def mage_basic_attack_damage_bonus(will: int) -> int:
    return ceil(
        max(0, will)
        * MAGE_BASIC_ATTACK_WILL_SCALING
    )


def mage_arcane_burst_damage_bonus(will: int) -> int:
    return (
        MAGE_ARCANE_BURST_BASE_DAMAGE_BONUS
        + ceil(
            max(0, will)
            * MAGE_ARCANE_BURST_WILL_SCALING
        )
    )


def warrior_cleave_damage_bonus(valor: int) -> int:
    return (
        WARRIOR_CLEAVE_DAMAGE_BONUS
        + ceil(
            max(0, valor)
            * WARRIOR_CLEAVE_VALOR_SCALING
        )
    )


def rogue_invisibility_duration(base_duration: int) -> int:
    return max(0, base_duration)


def rogue_ambush_damage_bonus(instinct: int) -> int:
    return (
        max(0, instinct)
        // ROGUE_AMBUSH_INSTINCT_DIVISOR
    )
