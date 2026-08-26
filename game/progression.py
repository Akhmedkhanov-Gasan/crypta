from acts.player_stats import (
    ATTRIBUTE_NAMES,
    apply_player_stat_changes,
    player_stat_changes_for_attribute_upgrade,
)
from settings import MAX_ATTRIBUTE_RANK


DEFAULT_ENEMY_EXPERIENCE = 1
ENEMY_EXPERIENCE_REWARDS = {
    "brute": 3,
    "goblin": 2,
    "archer": 2,
    "priest": 2,
    "priest_ghost": 3,
    "sentinel": 3,
    "mimic": 4,
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
    return (
        attribute in ATTRIBUTE_NAMES
        and attribute in player.attribute_ranks
        and player.attribute_points > 0
        and player.attribute_ranks[attribute] < MAX_ATTRIBUTE_RANK
    )


def apply_attribute_upgrade(player, attribute: str) -> bool:
    if attribute not in ATTRIBUTE_NAMES:
        return False
    current_rank = player.attribute_ranks.get(attribute)
    if current_rank is None or current_rank >= MAX_ATTRIBUTE_RANK:
        return False

    apply_player_stat_changes(
        player,
        player_stat_changes_for_attribute_upgrade(
            attribute,
            current_rank,
        ),
    )
    player.attribute_ranks[attribute] = current_rank + 1
    return True


def upgrade_attribute(player, attribute: str) -> bool:
    if not can_upgrade_attribute(player, attribute):
        return False

    if not apply_attribute_upgrade(player, attribute):
        return False
    player.attribute_points -= 1
    return True
