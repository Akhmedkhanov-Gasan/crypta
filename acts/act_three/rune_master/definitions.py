from dataclasses import dataclass


DISPLACEMENT_STUN_TURNS = 1
DOPPELGANGER_INVISIBILITY_TURNS = 2
CARNAGE_EXTRA_ATTACKS = 2
CARNAGE_TRANSFER_RANGE = 4
EXECUTIONER_DAMAGE_MULTIPLIER = 1.5
EMERALD_DAMAGE_MULTIPLIER = 1.5
EMERALD_STUN_TURNS = 1
SPLITFANG_DAMAGE_MULTIPLIER = 0.5
SPLITFANG_RANGE = 3
SPECTRAL_ARCHER_COUNT = 3
MIRROR_ACTIONS = 12
MIRROR_DAMAGE_MULTIPLIER = 0.5


@dataclass(frozen=True)
class AbilityRune:
    id: str
    subclass: str
    slot: str
    name: str
    description: str


ABILITY_RUNES = (
    AbilityRune("rune_of_displacement", "assassin", "q", "Rune of Displacement",
                f"Shadow Step can exchange places with a single-cell enemy. Stuns it for {DISPLACEMENT_STUN_TURNS} turn."),
    AbilityRune("rune_of_the_doppelganger", "assassin", "q", "Rune of the Doppelganger",
                f"Gain {DOPPELGANGER_INVISIBILITY_TURNS} turns of invisibility after Shadow Step."),
    AbilityRune("rune_of_carnage", "assassin", "f", "Rune of Carnage",
                f"The first kill adds {CARNAGE_EXTRA_ATTACKS} strikes once per Killing Spree. Remaining strikes jump to the nearest living enemy within {CARNAGE_TRANSFER_RANGE} cells."),
    AbilityRune("rune_of_the_executioner", "assassin", "f", "Rune of the Executioner",
                f"Killing Spree strikes one chosen enemy five times for {EXECUTIONER_DAMAGE_MULTIPLIER - 1:.0%} more damage."),
    AbilityRune("rune_of_emerald_piercing_shot", "archer", "q", "Rune of Emerald Piercing Shot",
                f"Piercing Shot deals {EMERALD_DAMAGE_MULTIPLIER - 1:.0%} more damage and stuns each enemy hit for {EMERALD_STUN_TURNS} turn."),
    AbilityRune("rune_of_splitfang_arrow", "archer", "q", "Rune of Splitfang Arrow",
                f"After the first impact, two arrows seek different nearby enemies for {SPLITFANG_DAMAGE_MULTIPLIER:.0%} damage each."),
    AbilityRune("rune_of_spectral_archers", "archer", "f", "Rune of Spectral Archers",
                "Summon three phantom archers instead of two. Each has six shots."),
    AbilityRune("rune_of_phantom_archer", "archer", "f", "Rune of Phantom Archer",
                f"Summon one double with {MIRROR_ACTIONS} actions. It echoes your attacks, invisibility and Piercing Shot at {MIRROR_DAMAGE_MULTIPLIER:.0%} damage. Never attacks independently."),
)
ABILITY_RUNES_BY_ID = {rune.id: rune for rune in ABILITY_RUNES}


def equipped_rune(player, slot):
    rune = ABILITY_RUNES_BY_ID.get(player.act_three.ability_runes.get(slot))
    if rune is None or rune.subclass != player.subclass or rune.slot != slot:
        return None
    return rune


def has_ability_rune(player, identifier):
    rune = ABILITY_RUNES_BY_ID[identifier]
    return equipped_rune(player, rune.slot) == rune
