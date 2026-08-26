import random

from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    GameState,
)


def _next_enemy_name(
    game_state: GameState,
    enemy_type: str,
) -> str:
    config = ENEMY_TYPES[enemy_type]

    if config.get("is_unique", False):
        return config["display_name"]

    existing_count = sum(
        enemy.type == enemy_type
        for enemy in game_state.floor.enemies
    )
    return f"{config['display_name']} {existing_count + 1}"


def try_spawn_enemy_after_death(
    game_state: GameState,
    defeated_enemy: EnemyState,
) -> EnemyState | None:
    defeated_config = ENEMY_TYPES.get(defeated_enemy.type)
    if defeated_config is None:
        return None

    spawn_rule = defeated_config.get("death_spawn")
    if spawn_rule is None:
        return None

    if random.random() >= spawn_rule["chance"]:
        return None

    spawned_type = spawn_rule["enemy_type"]
    spawned_config = ENEMY_TYPES[spawned_type]

    spawned_enemy = EnemyState.from_config(
        enemy_type=spawned_type,
        column=defeated_enemy.column,
        row=defeated_enemy.row,
        name=_next_enemy_name(game_state, spawned_type),
        config=spawned_config,
        belongs_to_boss_group=defeated_enemy.boss_group,
    )

    starts_aggro = spawn_rule.get(
        "starts_aggro",
        defeated_enemy.is_aggro,
    )
    spawned_enemy.is_active = defeated_enemy.is_active
    spawned_enemy.is_aggro = starts_aggro
    spawned_enemy.behavior_state = (
        EnemyBehaviorState.CHASING
        if starts_aggro
        else EnemyBehaviorState.IDLE
    )

    spawned_enemy.movement_bounds = defeated_enemy.movement_bounds
    spawned_enemy.treasury_trial_enemy = (
        defeated_enemy.treasury_trial_enemy
    )

    game_state.floor.enemies.append(spawned_enemy)

    message = spawn_rule.get("message")
    if message is not None:
        add_log_message(game_state.combat_log, message)

    return spawned_enemy
