from acts.act_two.settings import (
    WARRIOR_CLEAVE_MAX_RANK,
    WARRIOR_RHYTHM_MAX_RANK,
    CLASS_BASE_ATTRIBUTE_RANKS,
)
from acts.player_stats import (
    attribute_stat_changes_for_rank,
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
    "strength",
    "dexterity",
    "intelligence",
    "vitality",
)

ACT_TWO_UPGRADE_ORDER = {
    player_class: COMMON_ACT_TWO_UPGRADES
    for player_class in ("warrior", "rogue", "mage")
}


def get_act_two_upgrade_order(player_class: str | None) -> tuple[str, ...]:
    return ACT_TWO_UPGRADE_ORDER.get(player_class, ())


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

    if not can_upgrade_act_two(player, attribute):
        return f"{attribute.title()} is capped."

    if player.attribute_points <= 0:
        return "No attribute points available."

    change = player_stat_changes_for_attribute_upgrade(
        attribute,
        player.attribute_ranks[attribute],
    )

    if not upgrade_attribute(player, attribute):
        return "Attribute upgrade failed."

    details = {
        "strength": "physical damage increased",
        "dexterity": "critical power and dodge increased",
        "intelligence": "spell power increased",
        "vitality": f"maximum HP increased by {change.max_health}",
    }
    profile_effects = {
        (
            "warrior",
            "strength",
        ): "physical damage and Power Cleave increased",
        (
            "rogue",
            "dexterity",
        ): "critical power, dodge, and ambush increased",
        (
            "mage",
            "intelligence",
        ): "spell power and Arcane Burst increased",
    }
    detail = profile_effects.get(
        (player.player_class, attribute),
        details[attribute],
    )
    return f"{attribute.title()}: {detail}."


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
                f"{attribute.title()} +{amount}"
            )

    player.attribute_points -= selected_points

    for attribute in COMMON_ACT_TWO_UPGRADES:
        pending[attribute] = 0

    summary = ", ".join(applied_upgrades)
    return True, f"Attributes confirmed: {summary}."


def transfer_mage_strength_upgrades(player, previous_ranks):
    if player.player_class != "mage":
        return

    starting_strength = PLAYER_STARTING_ATTRIBUTE_RANKS["strength"]
    invested = max(
        0,
        previous_ranks.get("strength", starting_strength)
        - starting_strength,
    )
    if invested == 0:
        return

    before = attribute_stat_changes_for_rank(
        "strength", starting_strength + invested,
    )
    baseline = attribute_stat_changes_for_rank(
        "strength", starting_strength,
    )

    player.attribute_ranks["strength"] = (
        CLASS_BASE_ATTRIBUTE_RANKS["mage"]["strength"]
    )
    player.damage_min -= before.damage_min - baseline.damage_min
    player.damage_max -= before.damage_max - baseline.damage_max

    transferred = min(
        invested,
        max(0, MAX_ATTRIBUTE_RANK - player.attribute_ranks["intelligence"]),
    )
    player.attribute_ranks["intelligence"] += transferred
    player.spell_power += attribute_stat_changes_for_rank(
        "intelligence", transferred,
    ).spell_power

    player.attribute_points += invested - transferred
