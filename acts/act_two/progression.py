from acts.act_two.settings import (
    WARRIOR_CLEAVE_MAX_RANK,
    WARRIOR_RHYTHM_MAX_RANK,
)
from acts.player_stats import player_stat_changes_for_attribute_upgrade
from game.progression import apply_attribute_upgrade
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


def purchase_act_two_upgrade(player, upgrade: str) -> str:
    if player.gold_count <= 0:
        return "Not enough gold."
    if upgrade not in get_act_two_upgrade_order(player.player_class):
        return "This upgrade is unavailable to the class."
    if not can_upgrade_act_two(player, upgrade):
        return f"{upgrade.replace('_', ' ').title()} is capped."

    if upgrade in player.attribute_ranks:
        change = player_stat_changes_for_attribute_upgrade(
            upgrade,
            player.attribute_ranks[upgrade],
        )
        if not apply_attribute_upgrade(player, upgrade):
            return f"{upgrade.title()} is capped."
        details = {
            "strength": "physical damage increased",
            "dexterity": "critical power and dodge increased",
            "intelligence": "spell power increased",
            "vitality": f"maximum HP increased by {change.max_health}",
        }
        profile_effects = {
            ("warrior", "strength"): "physical damage and Power Cleave increased",
            ("rogue", "dexterity"): "critical power, dodge, and ambush increased",
            ("mage", "intelligence"): "spell power and Arcane Burst increased",
        }
        detail = profile_effects.get(
            (player.player_class, upgrade),
            details[upgrade],
        )
        message = f"{upgrade.title()}: {detail}."
    else:
        return "Unknown attribute."

    player.gold_count -= 1
    return message


# Compatibility for older callers while the Act Two interface is migrated.
WARRIOR_UPGRADE_MAX_RANKS = ACT_TWO_CLASS_UPGRADE_MAX_RANKS


def purchase_warrior_upgrade(player, upgrade: str) -> str:
    aliases = {"power": "strength"}
    return purchase_act_two_upgrade(player, aliases.get(upgrade, upgrade))
