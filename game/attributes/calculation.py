from game.attributes.balance import (
    FORTITUDE_DODGE_CHANCE_PER_RANK,
    FORTITUDE_HEALTH_PER_RANK,
    INSTINCT_CRIT_CHANCE_PER_RANK,
    INSTINCT_DODGE_CHANCE_PER_RANK,
    MAX_ATTRIBUTE_RANK,
    MAX_CRITICAL_DAMAGE_MULTIPLIER,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
    VALOR_CRITICAL_DAMAGE_PER_RANK,
    VALOR_DAMAGE_PER_STEP,
    VALOR_HEALTH_PER_TWO_RANKS,
    WILL_CRITICAL_DAMAGE_PER_RANK,
    WILL_CRIT_CHANCE_PER_RANK,
)
from game.attributes.definitions import (
    ATTRIBUTE_ORDER,
    FORTITUDE,
    INSTINCT,
    VALOR,
    WILL,
)
from game.attributes.models import (
    PlayerBaseStats,
    PlayerStatChanges,
)


def normalized_attribute_rank(rank: int) -> int:
    return max(
        0,
        min(MAX_ATTRIBUTE_RANK, rank),
    )


def attribute_stat_changes_for_rank(
    attribute: str,
    rank: int,
) -> PlayerStatChanges:
    rank = normalized_attribute_rank(rank)

    if attribute == VALOR:
        return PlayerStatChanges(
            max_health=(
                rank // 2
            ) * VALOR_HEALTH_PER_TWO_RANKS,
            damage_min=(
                rank // 2
            ) * VALOR_DAMAGE_PER_STEP,
            damage_max=(
                (rank + 1) // 2
            ) * VALOR_DAMAGE_PER_STEP,
            critical_damage_multiplier=(
                rank * VALOR_CRITICAL_DAMAGE_PER_RANK
            ),
        )

    if attribute == INSTINCT:
        return PlayerStatChanges(
            crit_chance=(
                rank * INSTINCT_CRIT_CHANCE_PER_RANK
            ),
            dodge_chance=(
                rank * INSTINCT_DODGE_CHANCE_PER_RANK
            ),
        )

    if attribute == WILL:
        return PlayerStatChanges(
            crit_chance=(
                rank * WILL_CRIT_CHANCE_PER_RANK
            ),
            critical_damage_multiplier=(
                rank * WILL_CRITICAL_DAMAGE_PER_RANK
            ),
        )

    if attribute == FORTITUDE:
        return PlayerStatChanges(
            max_health=(
                rank * FORTITUDE_HEALTH_PER_RANK
            ),
            dodge_chance=(
                rank * FORTITUDE_DODGE_CHANCE_PER_RANK
            ),
        )

    raise ValueError(
        f"Unknown player attribute: {attribute}"
    )


def player_stat_changes_for_attribute_upgrade(
    attribute: str,
    current_rank: int,
) -> PlayerStatChanges:
    current = attribute_stat_changes_for_rank(
        attribute,
        current_rank,
    )
    upgraded = attribute_stat_changes_for_rank(
        attribute,
        current_rank + 1,
    )

    return PlayerStatChanges(
        max_health=(
            upgraded.max_health
            - current.max_health
        ),
        damage_min=(
            upgraded.damage_min
            - current.damage_min
        ),
        damage_max=(
            upgraded.damage_max
            - current.damage_max
        ),
        crit_chance=(
            upgraded.crit_chance
            - current.crit_chance
        ),
        dodge_chance=(
            upgraded.dodge_chance
            - current.dodge_chance
        ),
        critical_damage_multiplier=(
            upgraded.critical_damage_multiplier
            - current.critical_damage_multiplier
        ),
    )


def combined_attribute_stat_changes(
    attribute_ranks: dict[str, int],
) -> PlayerStatChanges:
    values = {
        "max_health": 0,
        "damage_min": 0,
        "damage_max": 0,
        "crit_chance": 0.0,
        "dodge_chance": 0.0,
        "critical_damage_multiplier": 0.0,
    }

    for attribute in ATTRIBUTE_ORDER:
        changes = attribute_stat_changes_for_rank(
            attribute,
            attribute_ranks.get(attribute, 0),
        )

        for field_name in values:
            values[field_name] += getattr(
                changes,
                field_name,
            )

    return PlayerStatChanges(**values)


def player_stats_with_attributes(
    base_stats: PlayerBaseStats,
    attribute_ranks: dict[str, int],
) -> PlayerBaseStats:
    changes = combined_attribute_stat_changes(
        attribute_ranks,
    )

    return PlayerBaseStats(
        max_health=max(
            1,
            base_stats.max_health
            + changes.max_health,
        ),
        damage_min=max(
            0,
            base_stats.damage_min
            + changes.damage_min,
        ),
        damage_max=max(
            base_stats.damage_min
            + changes.damage_min,
            base_stats.damage_max
            + changes.damage_max,
        ),
        crit_chance=max(
            0.0,
            min(
                MAX_CRIT_CHANCE,
                base_stats.crit_chance
                + changes.crit_chance,
            ),
        ),
        dodge_chance=max(
            0.0,
            min(
                MAX_DODGE_CHANCE,
                base_stats.dodge_chance
                + changes.dodge_chance,
            ),
        ),
        critical_damage_multiplier=max(
            1.0,
            min(
                MAX_CRITICAL_DAMAGE_MULTIPLIER,
                base_stats.critical_damage_multiplier
                + changes.critical_damage_multiplier,
            ),
        ),
    )


def player_stat_changes_between(
    previous: PlayerBaseStats,
    current: PlayerBaseStats,
) -> PlayerStatChanges:
    return PlayerStatChanges(
        max_health=(
            current.max_health
            - previous.max_health
        ),
        damage_min=(
            current.damage_min
            - previous.damage_min
        ),
        damage_max=(
            current.damage_max
            - previous.damage_max
        ),
        crit_chance=(
            current.crit_chance
            - previous.crit_chance
        ),
        dodge_chance=(
            current.dodge_chance
            - previous.dodge_chance
        ),
        critical_damage_multiplier=(
            current.critical_damage_multiplier
            - previous.critical_damage_multiplier
        ),
    )
