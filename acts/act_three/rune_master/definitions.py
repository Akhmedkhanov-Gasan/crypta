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
BLOOD_WHEEL_RATIO = 0.2
BLOOD_WHEEL_TURNS = 3
DEVASTATION_RATIO = 0.5
DEVASTATION_ANIMATION_MS = 360
SECOND_WIND_RATIO = 0.1
SECOND_WIND_CAP = 0.4
DEATH_WISH_MULTIPLIER = 1.35
DEATH_WISH_EXTRA_HITS = 2


@dataclass(frozen=True)
class AbilityRune:
    id: str
    subclass: str
    slot: str
    name: str
    description: str


ABILITY_RUNES = (
    AbilityRune("rune_of_blood_wheel", "berserker", "q", "Rune of Blood Wheel",
                "Rending Spin causes bleeding for 3 turns, dealing 20% of the hit's damage each turn."),
    AbilityRune("rune_of_devastation", "berserker", "q", "Rune of Devastation",
                "Finish Rending Spin with another rotation, striking all eight neighboring cells for 50% damage."),
    AbilityRune("rune_of_second_wind", "berserker", "f", "Rune of Second Wind",
                "Store 10% of damage dealt as healing, up to 40% of maximum HP. Release it after Last Rage absorbs its final hit. No turn limit."),
    AbilityRune("rune_of_death_wish", "berserker", "f", "Rune of Death Wish",
                "Enter Last Rage at 1 HP and deal 35% more attack damage. The first two kills restore one protected hit each, up to 10 hits per activation. Cannot heal; finish at 1 HP."),
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
