from bosses.oracle import (
    choose_oracle_action,
    spawn_oracle_projectiles,
)
from game.state import EnemyState, GameState
from systems.enemy_ai.common import try_prepare_attack


def take_oracle_turn(
    game_state: GameState,
    oracle: EnemyState,
    attack_blocking_positions: set[tuple[int, int]],
) -> None:
    if oracle.projectile_cooldown > 0:
        oracle.projectile_cooldown -= 1
        return

    oracle_action = choose_oracle_action(oracle)

    if oracle_action in ("straight", "homing"):
        spawn_oracle_projectiles(
            oracle,
            game_state.floor,
            game_state.combat_log,
            oracle_action,
        )
        return

    try_prepare_attack(
        game_state,
        oracle,
        attack_blocking_positions,
    )
