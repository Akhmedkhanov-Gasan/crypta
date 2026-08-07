from settings import (
    CRIT_UPGRADE_AMOUNT,
    DAMAGE_UPGRADE_AMOUNT,
    DODGE_UPGRADE_AMOUNT,
    HEALTH_UPGRADE_AMOUNT,
    MAX_ATTRIBUTE_RANK,
    MAX_CRIT_CHANCE,
    MAX_DODGE_CHANCE,
)


DEFAULT_ENEMY_EXPERIENCE = 1
ENEMY_EXPERIENCE_REWARDS = {
    "brute": 3,
    "warden": 5,
    "oracle": 8,
}
def experience_required_for_level(level: int) -> int:
    return 5 + max(0, level - 1) * 2


def experience_reward_for_enemy(enemy_type: str) -> int:
    return ENEMY_EXPERIENCE_REWARDS.get(
        enemy_type,
        DEFAULT_ENEMY_EXPERIENCE,
    )


def grant_experience(player, amount: int) -> int:
    player.experience += max(0, amount)
    levels_gained = 0

    while player.experience >= experience_required_for_level(
        player.level
    ):
        player.experience -= experience_required_for_level(
            player.level
        )
        player.level += 1
        player.attribute_points += 1
        levels_gained += 1

    return levels_gained


def can_upgrade_attribute(player, attribute: str) -> bool:
    if attribute == "precision" and player.crit_chance >= MAX_CRIT_CHANCE:
        return False
    if attribute == "evasion" and player.dodge_chance >= MAX_DODGE_CHANCE:
        return False
    return (
        attribute in player.attribute_ranks
        and player.attribute_points > 0
        and player.attribute_ranks[attribute] < MAX_ATTRIBUTE_RANK
    )


def apply_attribute_upgrade(player, attribute: str) -> bool:
    if attribute == "vitality":
        player.max_health += HEALTH_UPGRADE_AMOUNT
        player.health += HEALTH_UPGRADE_AMOUNT
    elif attribute == "power":
        player.damage_min += DAMAGE_UPGRADE_AMOUNT
        player.damage_max += DAMAGE_UPGRADE_AMOUNT
    elif attribute == "precision":
        player.crit_chance = min(
            MAX_CRIT_CHANCE,
            player.crit_chance + CRIT_UPGRADE_AMOUNT,
        )
    elif attribute == "evasion":
        player.dodge_chance = min(
            MAX_DODGE_CHANCE,
            player.dodge_chance + DODGE_UPGRADE_AMOUNT,
        )
    else:
        return False

    return True


def upgrade_attribute(player, attribute: str) -> bool:
    if not can_upgrade_attribute(player, attribute):
        return False

    apply_attribute_upgrade(player, attribute)

    player.attribute_ranks[attribute] += 1
    player.attribute_points -= 1
    return True
