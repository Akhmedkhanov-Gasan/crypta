from game.attributes.balance import (
    MAX_ATTRIBUTE_RANK,
    MAX_CRITICAL_DAMAGE_MULTIPLIER,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
)
from game.attributes.calculation import (
    player_stat_changes_between,
)
from game.attributes.definitions import (
    ATTRIBUTE_ORDER,
)
from game.attributes.models import (
    PlayerBaseStats,
    PlayerStatChanges,
)


def apply_player_stat_changes(
    player,
    changes: PlayerStatChanges,
) -> None:
    player.max_health = max(
        1,
        player.max_health + changes.max_health,
    )
    player.health = max(
        1,
        min(
            player.max_health,
            player.health + changes.max_health,
        ),
    )
    player.damage_min = max(
        0,
        player.damage_min + changes.damage_min,
    )
    player.damage_max = max(
        player.damage_min,
        player.damage_max + changes.damage_max,
    )
    player.crit_chance = max(
        0.0,
        min(
            MAX_CRIT_CHANCE,
            player.crit_chance + changes.crit_chance,
        ),
    )
    player.dodge_chance = max(
        0.0,
        min(
            MAX_DODGE_CHANCE,
            player.dodge_chance + changes.dodge_chance,
        ),
    )
    player.critical_damage_multiplier = max(
        1.0,
        min(
            MAX_CRITICAL_DAMAGE_MULTIPLIER,
            player.critical_damage_multiplier
            + changes.critical_damage_multiplier,
        ),
    )


def apply_player_stat_transition(
    player,
    previous: PlayerBaseStats,
    current: PlayerBaseStats,
) -> None:
    apply_player_stat_changes(
        player,
        player_stat_changes_between(
            previous,
            current,
        ),
    )


def apply_attribute_rank_transition(
    player,
    previous_ranks: dict[str, int],
    current_ranks: dict[str, int],
) -> None:
    for attribute in ATTRIBUTE_ORDER:
        invested_ranks = max(
            0,
            player.attribute_ranks.get(attribute, 0)
            - previous_ranks.get(attribute, 0),
        )
        player.attribute_ranks[attribute] = min(
            MAX_ATTRIBUTE_RANK,
            current_ranks.get(attribute, 0)
            + invested_ranks,
        )
