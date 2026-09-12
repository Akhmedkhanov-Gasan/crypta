from game.attributes.models import PlayerStatChanges


def describe_player_stat_changes(
    changes: PlayerStatChanges,
) -> tuple[str, ...]:
    descriptions = []

    if changes.max_health:
        descriptions.append(
            f"{changes.max_health:+d} maximum HP"
        )

    if (
        changes.damage_min == changes.damage_max
        and changes.damage_min
    ):
        descriptions.append(
            f"{changes.damage_min:+d} damage"
        )
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
            f"{changes.critical_damage_multiplier:+.2f} "
            "critical damage"
        )

    return tuple(descriptions)
