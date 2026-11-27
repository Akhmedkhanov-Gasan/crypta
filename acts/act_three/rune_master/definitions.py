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
TOWER_SHIELD_BLOCK_BONUS = 0.25
TOWER_SHIELD_DAMAGE_MULTIPLIER = 0.75
TOWER_SHIELD_BLOCK_CAP = 0.65
BATTERING_RAM_COLLISION_MULTIPLIER = 0.5
FERVENT_CRUSADE_HITS = 6
FERVENT_CRUSADE_DAMAGE_MULTIPLIER = 1.75
SANCTUARY_HEAL_RATIO = 0.03
SPREADING_CURSE_RANGE = 3
MADNESS_TURNS = 4
MADNESS_ELITE_TURNS = 2
ETERNAL_FORM_DAMAGE_MULTIPLIER = 1.4
BLOOD_PACT_DAMAGE_STEP = 0.15
BLOOD_PACT_DAMAGE_CAP = 3.0
BLOOD_PACT_COST_INTERVAL = 3
BLOOD_PACT_KILL_HEAL_RATIO = 0.3
DEMON_KILL_HEAL_RATIO = 0.1
SPIRIT_TOTEM_RANGE = 3
SPIRIT_TOTEM_PLACEMENT_RANGE = 1
POSSESSION_RANGE = 4
POSSESSION_LEASH_RANGE = 3
POSSESSION_FOLLOW_DISTANCE = 2
POSSESSION_GUARD_RANGE = 3
FAMILIAR_DEATH_TURNS = 6
ABSORPTION_ATTACKS = 6
ABSORPTION_DAMAGE_MULTIPLIER = 1.75
ABSORPTION_BLOCK_CHANCE = 0.25
ABSORPTION_ATTACK_RANGE = 3


@dataclass(frozen=True)
class AbilityRune:
    id: str
    subclass: str
    slot: str
    name: str
    description: str


ABILITY_RUNES = (
    AbilityRune("rune_of_spirit_totem", "summoner", "q", "Rune of Spirit Totem",
                "Replace the familiar with an immobile spiritual totem on a chosen adjacent cell. It attacks enemies within 3 cells."),
    AbilityRune("rune_of_possession", "summoner", "q", "Rune of Possession",
                "Bind a visible enemy within 4 cells until death or transfer. Each binding or transfer costs a fully charged Q. Captured priests heal only while a visible hostile is within 3 cells of you. Bosses are immune."),
    AbilityRune("rune_of_soul_devourer", "summoner", "f", "Rune of Soul Devourer",
                "Each kill grants Greater Manifestation +25% attack damage and restores 90% maximum HP, capped at full health. Each attack costs 1 more HP than the previous one, even when blocked or dodged. The attack cost is paid before healing; a lethal cost cannot be healed."),
    AbilityRune("rune_of_absorption", "summoner", "f", "Rune of Absorption",
                "Absorb the greater spirit instead of summoning it: 6 attacks with +75% damage, +25 percentage points of block chance and attack range 3. Your familiar remains independent."),
    AbilityRune("rune_of_spreading_curse", "warlock", "q", "Rune of Spreading Curse",
                "When a cursed enemy dies, its remaining curse transfers to the nearest uncursed enemy within 3 cells."),
    AbilityRune("rune_of_madness", "warlock", "q", "Rune of Madness",
                "Replace vulnerability with random attacks that can hit allies, walls or empty cells. Lasts 4 enemy actions, or 2 for elites and bosses."),
    AbilityRune("rune_of_eternal_form", "warlock", "f", "Rune of Eternal Form",
                "Choosing this rune immediately transforms you permanently for this run: +40% attack damage, no HP cost and no healing on kills. No activation charge needed. Cannot revert or replace this rune."),
    AbilityRune("rune_of_blood_pact", "warlock", "f", "Rune of Blood Pact",
                "Transform without charges. Start at +75% damage; each attack adds 15 percentage points, capped at +200%. Cost starts at 1 HP and rises every 3 attacks. Kills heal 30% maximum HP. Revert with F."),
    AbilityRune("rune_of_battering_ram", "paladin", "q", "Rune of Battering Ram",
                "Shield Charge damages and pushes enemies out of its path. Failed pushes deal an extra 50% hit on collision."),
    AbilityRune("rune_of_tower_shield", "paladin", "q", "Rune of Tower Shield",
                "Passive: gain 25 percentage points of block chance, stacking with Guard and Impact up to 65%. Deal 25% less damage. Replaces Shield Charge."),
    AbilityRune("rune_of_fervent_crusade", "paladin", "f", "Rune of Fervent Crusade",
                "Empower your next 6 successful hits for 75% more damage instead of creating a zone. Cannot block or dodge while empowered. Recasting replaces the old effect."),
    AbilityRune("rune_of_redeeming_sanctuary", "paladin", "f", "Rune of Redeeming Sanctuary",
                "Sacred Ground has 6 damaging hits. Each enemy damaged is stunned for 1 turn and restores 3% of your maximum HP. Recasting replaces the old zone with 6 new hits."),
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
