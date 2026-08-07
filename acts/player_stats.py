from dataclasses import dataclass

from settings import MAX_CRIT_CHANCE, MAX_DODGE_CHANCE


@dataclass(frozen=True)
class PlayerBaseStats:
    max_health: int
    damage_min: int
    damage_max: int
    crit_chance: float = 0.0
    dodge_chance: float = 0.0


@dataclass(frozen=True)
class PlayerStatChanges:
    max_health: int = 0
    damage_min: int = 0
    damage_max: int = 0
    crit_chance: float = 0.0
    dodge_chance: float = 0.0


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


def apply_player_stat_transition(
    player,
    previous: PlayerBaseStats,
    next_stats: PlayerBaseStats,
) -> None:
    apply_player_stat_changes(
        player,
        player_stat_changes_between(previous, next_stats),
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

    return tuple(descriptions)
