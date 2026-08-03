DEFAULT_ENEMY_EXPERIENCE = 1
ENEMY_EXPERIENCE_REWARDS = {
    "brute": 3,
    "warden": 5,
    "oracle": 8,
}
MAX_ATTRIBUTE_RANK = 5


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
    return (
        attribute in player.attribute_ranks
        and player.attribute_points > 0
        and player.attribute_ranks[attribute] < MAX_ATTRIBUTE_RANK
    )


def upgrade_attribute(player, attribute: str) -> bool:
    if not can_upgrade_attribute(player, attribute):
        return False

    if attribute == "vitality":
        player.max_health += 2
        player.health += 2
    elif attribute == "power":
        player.damage_min += 1
        player.damage_max += 1
    elif attribute == "precision":
        player.crit_chance += 0.05
    elif attribute == "evasion":
        player.dodge_chance += 0.05

    player.attribute_ranks[attribute] += 1
    player.attribute_points -= 1
    return True
