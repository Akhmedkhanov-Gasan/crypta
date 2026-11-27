from math import ceil, log

from acts.act_three.ability_scaling import basic_attack_damage_range
from acts.act_three.balance import (
    CRIT_ASYMPTOTE, CRIT_DIMINISHING_THRESHOLD,
    DODGE_ASYMPTOTE, DODGE_DIMINISHING_THRESHOLD,
)
from acts.act_three.bloody_altar.catalog import has_pact
from acts.act_three.bloody_altar.effects import critical_multiplier
from acts.act_three.combat.damage import attack_damage_factors
from acts.act_three.equipment import equipment_rank_bonus
from game.attributes import attribute_stat_changes_for_rank


def damage_range_text(values):
    minimum, maximum = values
    return str(minimum) if minimum == maximum else f"{minimum}-{maximum}"


def current_damage_range(player, values=None, *, critical=False, attacker="hero"):
    minimum, maximum = values or basic_attack_damage_range(player)
    if attacker == "familiar" and player.summoner_true_form_active:
        from acts.act_three.settings import SUMMONER_TRUE_FORM_DAMAGE_BONUS

        minimum += SUMMONER_TRUE_FORM_DAMAGE_BONUS
        maximum += SUMMONER_TRUE_FORM_DAMAGE_BONUS
    factor = 1.0
    for _, value in attack_damage_factors(player, None, critical, attacker):
        factor *= value
    from acts.act_three.abilities.paladin_runes import tower_shield_active

    if attacker == "hero" and tower_shield_active(player):
        remainder = player.act_three.paladin_tower_damage_remainder
        return tuple(max(1, int(value * factor + remainder + 1e-9)) for value in (minimum, maximum))
    return tuple(max(1, ceil(value * factor)) for value in (minimum, maximum))


def conditional_damage_lines(player):
    identifier = player.act_three.altar_pact_id
    lines = {
        "final_word": ("Final Word: x1.60 at half enemy HP or less; x0.70 above half.",),
        "lone_prey": ("Lone Prey: x1.40 against isolated foes; x0.75 with another foe within 5 cells.",),
        "feast_of_many": ("Feast of Many: x1.40 with another foe within 5 cells; x0.75 against isolated foes.",),
        "insatiable_edge": (
            f"Insatiable Edge: next basic hit +{min(4, player.act_three.altar_attack_chain + 1) * 15}%; maximum +60%.",
            "Other actions, blocked attacks and misses reset the chain.",
        ),
    }.get(identifier, ())
    if player.subclass == "warlock":
        from acts.act_three.rune_master.definitions import has_ability_rune
        from acts.act_three.settings import WARLOCK_CURSE_DAMAGE_MULTIPLIER

        if not has_ability_rune(player, "rune_of_madness"):
            lines += (f"Curse: x{WARLOCK_CURSE_DAMAGE_MULTIPLIER:g} against cursed targets.",)
    if player.invisibility_turns > 0:
        lines += ("Invisibility: your next direct attack is a guaranteed critical hit.",)
    return lines


def damage_lines(player):
    from acts.act_two.ability_scaling import mage_basic_attack_damage_bonus

    raw = basic_attack_damage_range(player)
    valor = attribute_stat_changes_for_rank("valor", player.attribute_ranks.get("valor", 0), rank_limit=None)
    if player.player_class == "mage":
        bonus = mage_basic_attack_damage_bonus(player.attribute_ranks.get("will", 0))
        base = (raw[0] - bonus, raw[1] - bonus)
        source = f"Base {damage_range_text(base)} + Will {bonus} = {damage_range_text(raw)} magic damage."
    else:
        base = (raw[0] - valor.damage_min, raw[1] - valor.damage_max)
        source = f"Base {damage_range_text(base)} + Valor {valor.damage_min}-{valor.damage_max} = {damage_range_text(raw)} physical damage."
    factors = tuple(f"{name}: x{value:.2f}." for name, value in attack_damage_factors(player, None))
    normal = damage_range_text(current_damage_range(player))
    critical = damage_range_text(current_damage_range(player, critical=True))
    return (
        source,
        *factors,
        f"Current hit: {normal}; critical: {critical} (x{critical_multiplier(player):.2f}).",
        *conditional_damage_lines(player),
        *hit_effect_lines(player),
        "Target-dependent bonuses are applied separately; final damage is rounded once.",
    )


def hit_effect_lines(player):
    from acts.act_two.bloody_altar import has_bloody_pact

    lines = ()
    if has_bloody_pact(player, "open_wound"):
        lines += ("Open Wound: 25% chance to bleed for 20% of hit damage per turn, for 3 turns.",)
    elif has_bloody_pact(player, "blood_hunger"):
        lines += ("Blood Hunger: direct hero damage heals for 25% of damage dealt, before healing modifiers.",)
    if has_pact(player, "crimson_rupture"):
        lines += ("Crimson Rupture: direct hero hits bleed for 20% of hit damage per turn, for 3 turns.",)
    elif has_pact(player, "endless_hunger"):
        lines += ("Endless Hunger: direct hero damage heals for 40% of damage dealt.",)
    return lines


def chance_lines(player, *, dodge=False):
    stored = player.dodge_chance if dodge else player.crit_chance
    threshold = DODGE_DIMINISHING_THRESHOLD if dodge else CRIT_DIMINISHING_THRESHOLD
    asymptote = DODGE_ASYMPTOTE if dodge else CRIT_ASYMPTOTE
    raw = stored
    if threshold < stored < asymptote:
        raw = threshold - (asymptote - threshold) * log((asymptote - stored) / (asymptote - threshold))
    instinct_stats = attribute_stat_changes_for_rank("instinct", player.attribute_ranks.get("instinct", 0), rank_limit=None)
    instinct = instinct_stats.dodge_chance if dodge else instinct_stats.crit_chance
    other_name = "Fortitude" if dodge else "Will"
    other_key = "fortitude" if dodge else "will"
    other_stats = attribute_stat_changes_for_rank(other_key, player.attribute_ranks.get(other_key, 0), rank_limit=None)
    other = other_stats.dodge_chance if dodge else other_stats.crit_chance
    lines = (
        f"Base / retained adjustments: {(raw - instinct - other) * 100:+.1f} percentage points.",
        f"Instinct: +{instinct * 100:.1f} points; {other_name}: +{other * 100:.1f} points.",
    )
    if stored > threshold:
        lines += (f"Diminishing returns: {(stored - raw) * 100:.1f} points; stored total {stored:.1%}.",)
    else:
        lines += (f"Total: {stored:.1%}.",)
    lines += (f"Gains diminish above {threshold:.0%}, approaching {asymptote:.0%}.",)
    if dodge:
        from acts.act_three.abilities.paladin_runes import crusade_active

        if has_pact(player, "blood_carapace"):
            lines += ("Blood Carapace disables dodge: current chance 0%.",)
        elif crusade_active(player):
            lines += ("Fervent Crusade disables dodge until its empowered hits end.",)
        if player.subclass == "assassin":
            lines += ("Shadow Reflex: dodging a direct attack triggers a counterattack.",)
        lines += ("Does not avoid traps, ground hazards or unavoidable damage.",)
    elif player.invisibility_turns > 0:
        lines += ("Invisibility guarantees the next direct attack's critical hit.",)
    return lines


def critical_lines(player):
    valor = attribute_stat_changes_for_rank("valor", player.attribute_ranks.get("valor", 0), rank_limit=None).critical_damage_multiplier
    will = attribute_stat_changes_for_rank("will", player.attribute_ranks.get("will", 0), rank_limit=None).critical_damage_multiplier
    lines = (
        f"Base / retained bonuses: x{player.critical_damage_multiplier - valor - will:.2f}.",
        f"Valor: +{valor:.2f}; Will: +{will:.2f} to the multiplier.",
    )
    if has_pact(player, "exposed_heart"):
        lines += ("Exposed Heart: +0.75 to the multiplier.",)
    return (*lines, f"Total critical multiplier: x{critical_multiplier(player):.2f}.",
            "Multiplies damage on a critical hit; other damage bonuses still apply.")


def health_lines(player):
    valor = attribute_stat_changes_for_rank("valor", player.attribute_ranks.get("valor", 0), rank_limit=None).max_health
    fortitude = attribute_stat_changes_for_rank("fortitude", player.attribute_ranks.get("fortitude", 0), rank_limit=None).max_health
    glass = player.act_two.bloody_pact_health_penalty
    altar = player.act_three.altar_health_penalty
    base = player.max_health + glass + altar - valor - fortitude
    lines = [f"Maximum HP: base {base} + Valor {valor} + Fortitude {fortitude}."]
    if glass:
        lines.append(f"Glass Heart: -{glass} maximum HP.")
    if altar:
        from acts.act_three.bloody_altar.catalog import PACTS_BY_ID

        pact = PACTS_BY_ID.get(player.act_three.altar_pact_id)
        lines.append(f"{pact.name if pact else 'Altar'}: -{altar} maximum HP.")
    lines.append(f"Current health: {player.health}/{player.max_health}. Increasing maximum HP does not heal you.")
    return tuple(lines)


def block_lines(player):
    from acts.act_three.combat.paladin import add_paladin_block_chance, PALADIN_BLOCK_CHANCE, PALADIN_BLOCK_CHANCE_CAP
    from acts.act_three.abilities.paladin_runes import crusade_active, tower_shield_active
    from acts.act_three.abilities.summoner_runes import absorption_active
    from acts.act_three.rune_master.definitions import ABSORPTION_BLOCK_CHANCE, TOWER_SHIELD_BLOCK_BONUS, TOWER_SHIELD_BLOCK_CAP
    from settings import WARRIOR_IMPACT_BLOCK_CHANCE

    impact = WARRIOR_IMPACT_BLOCK_CHANCE if player.player_class == "warrior" and player.selected_rune_id == "rune_of_impact" else 0
    chance = add_paladin_block_chance(player, impact)
    lines = []
    if player.subclass == "paladin":
        lines.append(f"Dark Aegis: {PALADIN_BLOCK_CHANCE:.0%} base block chance.")
    if impact:
        lines.append(f"Rune of Impact: +{impact:.0%} block chance.")
    if tower_shield_active(player):
        lines.append(f"Rune of Tower Shield: +{TOWER_SHIELD_BLOCK_BONUS:.0%} block chance.")
    if player.subclass == "paladin":
        cap = TOWER_SHIELD_BLOCK_CAP if tower_shield_active(player) else PALADIN_BLOCK_CHANCE_CAP
        lines.append(f"Combined block chance is limited to {cap:.0%}.")
    if absorption_active(player):
        chance += ABSORPTION_BLOCK_CHANCE
        lines.append(f"Rune of Absorption: +{ABSORPTION_BLOCK_CHANCE:.0%} block chance.")
    if has_pact(player, "blood_carapace") or crusade_active(player):
        source = "Blood Carapace" if has_pact(player, "blood_carapace") else "Fervent Crusade"
        lines.append(f"{source}: blocking disabled.")
    lines.append(f"Current total block chance: {chance:.0%}. A block prevents the whole attack.")
    return tuple(lines)


def armor_lines(player):
    reduction = equipment_rank_bonus(player.act_three.armor_rank, armor=True)
    lines = [f"Armor rank {player.act_three.armor_rank}: {reduction}% less physical damage."]
    if has_pact(player, "blood_carapace"):
        lines.append("Blood Carapace: 35% less attack damage; dodge and block disabled.")
    elif has_pact(player, "endless_hunger"):
        lines.append("Endless Hunger: 50% more attack damage received.")
    elif has_pact(player, "exposed_heart"):
        lines.append("Exposed Heart: enemy attacks have a 20% chance to deal double damage.")
    if player.act_two.stoneflesh_hits > 0:
        lines.append(f"Stoneflesh: 60% less physical damage; {player.act_two.stoneflesh_hits} damaging hits left.")
    if player.act_three.ironblood_guard:
        lines.append("Ironblood Tonic: the next damaging hit is halved.")
    lines.append("Reductions multiply; positive physical damage cannot fall below 1 after armor.")
    return tuple(lines)
