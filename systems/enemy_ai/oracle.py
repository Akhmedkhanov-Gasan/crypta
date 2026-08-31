from acts.act_two.presentation.bosses.oracle_combat import (
    take_oracle_combat_turn,
)
from game.state import EnemyState, GameState


def take_oracle_turn(
    game_state: GameState,
    oracle: EnemyState,
    attack_blocking_positions: set[tuple[int, int]],
) -> None:
    take_oracle_combat_turn(game_state, oracle)
