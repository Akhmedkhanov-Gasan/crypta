from acts.act_three.enemies.balance import LANTERN_WARDEN_EXPERIENCE
from game.attributes import (
    ATTRIBUTE_ORDER,
    MAX_ATTRIBUTE_RANK,
    apply_player_stat_changes,
    player_stat_changes_for_attribute_upgrade,
)


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
    "lantern_warden": LANTERN_WARDEN_EXPERIENCE,

}


def attribute_rank_limit(player) -> int | None:
    return None if getattr(player, "subclass", None) is not None else MAX_ATTRIBUTE_RANK


def attribute_points_per_level(player) -> int:
    if getattr(player, "subclass", None) is not None:
        from acts.act_three.balance import ATTRIBUTE_POINTS_PER_LEVEL

        return ATTRIBUTE_POINTS_PER_LEVEL
    return 1


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
        player.attribute_points += attribute_points_per_level(player)
        levels_gained += 1

    return levels_gained


def can_upgrade_attribute(player, attribute: str) -> bool:
    rank_limit = attribute_rank_limit(player)
    return (
        attribute in ATTRIBUTE_ORDER
        and attribute in player.attribute_ranks
        and player.attribute_points > 0
        and (rank_limit is None or player.attribute_ranks[attribute] < rank_limit)
    )


def apply_attribute_upgrade(player, attribute: str) -> bool:
    if attribute not in ATTRIBUTE_ORDER:
        return False
    if getattr(player, "subclass", None) is not None and player.health <= 0:
        return False
    current_rank = player.attribute_ranks.get(attribute)
    rank_limit = attribute_rank_limit(player)
    if current_rank is None or (rank_limit is not None and current_rank >= rank_limit):
        return False

    apply_player_stat_changes(
        player,
        player_stat_changes_for_attribute_upgrade(
            attribute,
            current_rank,
            rank_limit=rank_limit,
        ),
        heal_max_health=rank_limit is not None,
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
