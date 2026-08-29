import random

from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.state import (
    ChestState,
    EnemyBehaviorState,
    EnemyState,
    GameState,
)


def mark_mimic_chests(
    chests: list[dict],
    count: int = 1,
) -> None:
    if count <= 0:
        return

    eligible_chests = [
        chest
        for chest in chests
        if chest.get("appearance", "standard") == "standard"
    ]
    mimic_count = min(count, len(eligible_chests))

    for mimic_chest in random.sample(
        eligible_chests,
        mimic_count,
    ):
        mimic_chest["appearance"] = "mimic"


def _next_mimic_name(game_state: GameState) -> str:
    existing_count = sum(
        enemy.type == "mimic"
        for enemy in game_state.floor.enemies
    )
    return f"Mimic {existing_count + 1}"


def awaken_mimic(
    game_state: GameState,
    chest: ChestState,
) -> bool:
    if chest.appearance != "mimic":
        return False

    enemy = EnemyState.from_config(
        enemy_type="mimic",
        column=chest.column,
        row=chest.row,
        name=_next_mimic_name(game_state),
        config=ENEMY_TYPES["mimic"],
        belongs_to_boss_group=False,
    )
    enemy.is_aggro = True
    enemy.behavior_state = EnemyBehaviorState.CHASING

    chest.appearance = f"mimic:{enemy.name}"
    game_state.floor.enemies.append(enemy)

    add_log_message(
        game_state.combat_log,
        "The chest reveals itself as a Mimic!",
        category="warning",
    )
    return True


def release_mimic_loot(
    game_state: GameState,
    enemy: EnemyState,
) -> bool:
    if enemy.type != "mimic":
        return False

    active_appearance = f"mimic:{enemy.name}"
    chest = next(
        (
            candidate
            for candidate in game_state.floor.chests
            if candidate.appearance == active_appearance
        ),
        None,
    )
    if chest is None:
        return False

    chest.column = enemy.column
    chest.row = enemy.row
    chest.appearance = "mimic_defeated"
    chest.loot_available = True

    add_log_message(
        game_state.combat_log,
        "The Mimic releases the treasure it swallowed.",
        category="loot",
    )
    return True
