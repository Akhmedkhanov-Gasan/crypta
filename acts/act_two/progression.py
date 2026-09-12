from copy import copy

from acts.act_two.settings import (
    WARRIOR_CLEAVE_MAX_RANK,
    WARRIOR_RHYTHM_MAX_RANK,
    CLASS_BASE_ATTRIBUTE_RANKS,
)
from game.attributes import (
    apply_player_stat_changes,
    attribute_stat_changes_for_rank,
    get_attribute_definition,
    player_stat_changes_between,
    player_stat_changes_for_attribute_upgrade,
)
from acts.act_one.settings import PLAYER_STARTING_ATTRIBUTE_RANKS
from game.progression import (
    apply_attribute_upgrade,
    upgrade_attribute,
)
from settings import MAX_ATTRIBUTE_RANK


ACT_TWO_CLASS_UPGRADE_MAX_RANKS = {
    "warrior_cleave": WARRIOR_CLEAVE_MAX_RANK,
    "warrior_rhythm": WARRIOR_RHYTHM_MAX_RANK,
}

COMMON_ACT_TWO_UPGRADES = (
    "valor",
    "instinct",
    "will",
    "fortitude",
)

ACT_TWO_UPGRADE_ORDER = {
    player_class: COMMON_ACT_TWO_UPGRADES
    for player_class in ("warrior", "rogue", "mage")
}


def get_act_two_upgrade_order(player_class: str | None) -> tuple[str, ...]:
    return ACT_TWO_UPGRADE_ORDER.get(player_class, ())


def get_act_two_attribute_preview(player):
    pending = player.act_two.pending_attribute_upgrades

    if not any(pending.values()):
        return player

    preview = copy(player)
    preview.attribute_ranks = dict(player.attribute_ranks)

    for attribute in COMMON_ACT_TWO_UPGRADES:
        for _ in range(pending.get(attribute, 0)):
            apply_attribute_upgrade(preview, attribute)

    return preview


def get_class_upgrade_rank(player, upgrade: str) -> int:
    return player.act_two.class_upgrade_ranks.get(upgrade, 0)


def get_warrior_upgrade_rank(player, upgrade: str) -> int:
    return get_class_upgrade_rank(player, upgrade)


def can_upgrade_act_two(player, upgrade: str) -> bool:
    if upgrade in player.attribute_ranks:
        return player.attribute_ranks[upgrade] < MAX_ATTRIBUTE_RANK
    maximum_rank = ACT_TWO_CLASS_UPGRADE_MAX_RANKS.get(upgrade)
    return (
        maximum_rank is not None
        and get_class_upgrade_rank(player, upgrade) < maximum_rank
    )


def _apply_class_upgrade(player, upgrade: str) -> bool:
    if not can_upgrade_act_two(player, upgrade):
        return False
    player.act_two.class_upgrade_ranks[upgrade] = (
        get_class_upgrade_rank(player, upgrade) + 1
    )
    return True


def upgrade_act_two_attribute(player, attribute: str) -> str:
    if attribute not in get_act_two_upgrade_order(player.player_class):
        return "This attribute is unavailable to the class."

    definition = get_attribute_definition(
        attribute
    )

    if not can_upgrade_act_two(player, attribute):
        return f"{definition.title} is capped."

    if player.attribute_points <= 0:
        return "No attribute points available."

    if not upgrade_attribute(player, attribute):
        return "Attribute upgrade failed."

    details = {
        "valor": (
            "physical damage, critical damage, "
            "and resilience increased"
        ),
        "instinct": (
            "critical chance and dodge increased"
        ),
        "will": (
            "critical chance and critical damage increased"
        ),
        "fortitude": (
            "maximum HP and dodge increased"
        ),
    }
    profile_effects = {
        (
            "warrior",
            "valor",
        ): (
            "physical damage, critical damage, "
            "and Power Cleave increased"
        ),
        (
            "rogue",
            "instinct",
        ): (
            "critical chance, dodge, "
            "and ambush increased"
        ),
        (
            "mage",
            "will",
        ): (
            "magical attacks and critical potential increased"
        ),
    }
    detail = profile_effects.get(
        (player.player_class, attribute),
        details[attribute],
    )
    return f"{definition.title}: {detail}."


def queue_act_two_attribute_upgrade(
    player,
    attribute: str,
) -> bool:
    if attribute not in COMMON_ACT_TWO_UPGRADES:
        return False

    pending = player.act_two.pending_attribute_upgrades
    pending_points = sum(pending.values())

    if pending_points >= player.attribute_points:
        return False

    future_rank = (
        player.attribute_ranks[attribute]
        + pending[attribute]
    )
    if future_rank >= MAX_ATTRIBUTE_RANK:
        return False

    pending[attribute] += 1
    return True


def cancel_queued_act_two_attribute_upgrade(
    player,
    attribute: str,
) -> bool:
    if attribute not in COMMON_ACT_TWO_UPGRADES:
        return False

    pending = player.act_two.pending_attribute_upgrades

    if pending[attribute] <= 0:
        return False

    pending[attribute] -= 1
    return True


def confirm_queued_act_two_attribute_upgrades(
    player,
) -> tuple[bool, str]:
    pending = player.act_two.pending_attribute_upgrades
    selected_points = sum(pending.values())

    if selected_points <= 0:
        return False, "No attribute upgrades selected."

    if selected_points > player.attribute_points:
        return False, "Not enough attribute points."

    for attribute in COMMON_ACT_TWO_UPGRADES:
        amount = pending.get(attribute, 0)
        future_rank = (
            player.attribute_ranks[attribute] + amount
        )

        if amount < 0 or future_rank > MAX_ATTRIBUTE_RANK:
            return False, "Invalid attribute allocation."

    applied_upgrades = []

    for attribute in COMMON_ACT_TWO_UPGRADES:
        amount = pending.get(attribute, 0)

        for _ in range(amount):
            if not apply_attribute_upgrade(player, attribute):
                return False, "Attribute upgrade failed."

        if amount > 0:
            applied_upgrades.append(
                (
                    f"{get_attribute_definition(attribute).title} "
                    f"+{amount}"
                )
            )

    player.attribute_points -= selected_points

    for attribute in COMMON_ACT_TWO_UPGRADES:
        pending[attribute] = 0

    summary = ", ".join(applied_upgrades)
    return True, f"Attributes confirmed: {summary}."


def transfer_mage_valor_investment(
    player,
    previous_ranks,
):
    if player.player_class != "mage":
        return

    starting_valor = (
        PLAYER_STARTING_ATTRIBUTE_RANKS["valor"]
    )
    invested = max(
        0,
        previous_ranks.get(
            "valor",
            starting_valor,
        )
        - starting_valor,
    )

    if invested == 0:
        return

    previous_valor_stats = (
        attribute_stat_changes_for_rank(
            "valor",
            starting_valor + invested,
        )
    )
    starting_valor_stats = (
        attribute_stat_changes_for_rank(
            "valor",
            starting_valor,
        )
    )

    player.attribute_ranks["valor"] = (
        CLASS_BASE_ATTRIBUTE_RANKS[
            "mage"
        ]["valor"]
    )

    apply_player_stat_changes(
        player,
        player_stat_changes_between(
            previous_valor_stats,
            starting_valor_stats,
        ),
    )

    current_will = player.attribute_ranks["will"]
    transferred = min(
        invested,
        max(
            0,
            MAX_ATTRIBUTE_RANK - current_will,
        ),
    )
    upgraded_will = current_will + transferred

    previous_will_stats = (
        attribute_stat_changes_for_rank(
            "will",
            current_will,
        )
    )
    upgraded_will_stats = (
        attribute_stat_changes_for_rank(
            "will",
            upgraded_will,
        )
    )

    apply_player_stat_changes(
        player,
        player_stat_changes_between(
            previous_will_stats,
            upgraded_will_stats,
        ),
    )

    player.attribute_ranks["will"] = upgraded_will
    player.attribute_points += invested - transferred
