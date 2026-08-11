from dataclasses import dataclass

from settings import (
    DEXTERITY_CRITICAL_DAMAGE_PER_RANK,
    DEXTERITY_CRIT_CHANCE_PER_RANK,
    DEXTERITY_DODGE_CHANCE_PER_RANK,
    INTELLIGENCE_SPELL_POWER_PER_RANK,
    MAX_ATTRIBUTE_RANK,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
    STRENGTH_DAMAGE_PER_RANK,
    VITALITY_HEALTH_PER_RANK,
)


@dataclass(frozen=True)
class PlayerBaseStats:
    max_health: int
    damage_min: int
    damage_max: int
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    critical_damage_multiplier: float = 2.0
    spell_power: int = 0


@dataclass(frozen=True)
class PlayerStatChanges:
    max_health: int = 0
    damage_min: int = 0
    damage_max: int = 0
    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    critical_damage_multiplier: float = 0.0
    spell_power: int = 0


ATTRIBUTE_NAMES = (
    "strength",
    "dexterity",
    "intelligence",
    "vitality",
)


def attribute_stat_changes_for_rank(
    attribute: str,
    rank: int,
) -> PlayerStatChanges:
    """Return the total contribution of an attribute at the given rank."""
    rank = max(0, rank)
    if attribute == "strength":
        # Odd ranks raise the upper roll, even ranks raise the lower roll.
        return PlayerStatChanges(
            damage_min=(rank // 2) * STRENGTH_DAMAGE_PER_RANK,
            damage_max=((rank + 1) // 2) * STRENGTH_DAMAGE_PER_RANK,
        )
    if attribute == "dexterity":
        return PlayerStatChanges(
            crit_chance=rank * DEXTERITY_CRIT_CHANCE_PER_RANK,
            dodge_chance=rank * DEXTERITY_DODGE_CHANCE_PER_RANK,
            critical_damage_multiplier=(
                rank * DEXTERITY_CRITICAL_DAMAGE_PER_RANK
            ),
        )
    if attribute == "intelligence":
        return PlayerStatChanges(
            spell_power=rank * INTELLIGENCE_SPELL_POWER_PER_RANK,
        )
    if attribute == "vitality":
        return PlayerStatChanges(
            max_health=rank * VITALITY_HEALTH_PER_RANK,
        )
    raise ValueError(f"Unknown player attribute: {attribute}")


def player_stat_changes_for_attribute_upgrade(
    attribute: str,
    current_rank: int,
) -> PlayerStatChanges:
    current = attribute_stat_changes_for_rank(attribute, current_rank)
    next_rank = attribute_stat_changes_for_rank(attribute, current_rank + 1)
    return PlayerStatChanges(
        **{
            field_name: (
                getattr(next_rank, field_name)
                - getattr(current, field_name)
            )
            for field_name in current.__dataclass_fields__
        }
    )


def player_stats_with_attributes(
    base_stats: PlayerBaseStats,
    attribute_ranks: dict[str, int],
) -> PlayerBaseStats:
    values = {
        "max_health": base_stats.max_health,
        "damage_min": base_stats.damage_min,
        "damage_max": base_stats.damage_max,
        "crit_chance": base_stats.crit_chance,
        "dodge_chance": base_stats.dodge_chance,
        "critical_damage_multiplier": (
            base_stats.critical_damage_multiplier
        ),
        "spell_power": base_stats.spell_power,
    }
    for attribute in ATTRIBUTE_NAMES:
        changes = attribute_stat_changes_for_rank(
            attribute,
            attribute_ranks.get(attribute, 0),
        )
        for field_name in values:
            values[field_name] += getattr(changes, field_name)

    values["crit_chance"] = min(MAX_CRIT_CHANCE, values["crit_chance"])
    values["dodge_chance"] = min(
        MAX_DODGE_CHANCE,
        values["dodge_chance"],
    )
    return PlayerBaseStats(**values)


def player_stat_changes_between(
    previous: PlayerBaseStats,
    next_stats: PlayerBaseStats,
) -> PlayerStatChanges:
    return PlayerStatChanges(
        max_health=next_stats.max_health - previous.max_health,
        damage_min=next_stats.damage_min - previous.damage_min,
        damage_max=next_stats.damage_max - previous.damage_max,
        crit_chance=next_stats.crit_chance - previous.crit_chance,
        dodge_chance=next_stats.dodge_chance - previous.dodge_chance,
        critical_damage_multiplier=(
            next_stats.critical_damage_multiplier
            - previous.critical_damage_multiplier
        ),
        spell_power=next_stats.spell_power - previous.spell_power,
    )


def apply_player_stat_changes(player, changes: PlayerStatChanges) -> None:
    player.max_health = max(1, player.max_health + changes.max_health)
    player.health = max(
        1,
        min(player.max_health, player.health + changes.max_health),
    )
    player.damage_min = max(0, player.damage_min + changes.damage_min)
    player.damage_max = max(
        player.damage_min,
        player.damage_max + changes.damage_max,
    )
    player.crit_chance = max(
        0.0,
        min(MAX_CRIT_CHANCE, player.crit_chance + changes.crit_chance),
    )
    player.dodge_chance = max(
        0.0,
        min(MAX_DODGE_CHANCE, player.dodge_chance + changes.dodge_chance),
    )
    player.critical_damage_multiplier = max(
        1.0,
        player.critical_damage_multiplier
        + changes.critical_damage_multiplier,
    )
    player.spell_power = max(0, player.spell_power + changes.spell_power)


def apply_player_stat_transition(
    player,
    previous: PlayerBaseStats,
    next_stats: PlayerBaseStats,
) -> None:
    apply_player_stat_changes(
        player,
        player_stat_changes_between(previous, next_stats),
    )


def apply_attribute_rank_transition(
    player,
    previous_ranks: dict[str, int],
    next_ranks: dict[str, int],
) -> None:
    """Move act baselines while preserving ranks bought during the run."""
    for attribute in ATTRIBUTE_NAMES:
        invested_ranks = max(
            0,
            player.attribute_ranks.get(attribute, 0)
            - previous_ranks.get(attribute, 0),
        )
        player.attribute_ranks[attribute] = min(
            MAX_ATTRIBUTE_RANK,
            next_ranks.get(attribute, 0) + invested_ranks,
        )


def describe_player_stat_changes(
    changes: PlayerStatChanges,
) -> tuple[str, ...]:
    descriptions = []

    if changes.max_health:
        descriptions.append(f"{changes.max_health:+d} maximum HP")

    if changes.damage_min == changes.damage_max and changes.damage_min:
        descriptions.append(f"{changes.damage_min:+d} damage")
    else:
        if changes.damage_min:
            descriptions.append(
                f"{changes.damage_min:+d} minimum damage"
            )
        if changes.damage_max:
            descriptions.append(
                f"{changes.damage_max:+d} maximum damage"
            )

    crit_percent = round(changes.crit_chance * 100)
    dodge_percent = round(changes.dodge_chance * 100)
    if crit_percent and crit_percent == dodge_percent:
        descriptions.append(
            f"{crit_percent:+d}% critical and dodge chance"
        )
    else:
        if crit_percent:
            descriptions.append(
                f"{crit_percent:+d}% critical chance"
            )
        if dodge_percent:
            descriptions.append(
                f"{dodge_percent:+d}% dodge chance"
            )

    if changes.critical_damage_multiplier:
        descriptions.append(
            f"{changes.critical_damage_multiplier:+.1f} critical damage"
        )
    if changes.spell_power:
        descriptions.append(f"{changes.spell_power:+d} spell power")

    return tuple(descriptions)
