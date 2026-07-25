from game.state import EnemyState, GameState
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)


def take_standard_turn(
    game_state: GameState,
    enemy: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
) -> None:
    if try_prepare_attack(
        game_state,
        enemy,
        attack_blocking_positions,
    ):
        return

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    move_toward_player(
        game_state,
        enemy,
        occupied_positions,
    )
    try_prepare_attack(
        game_state,
        enemy,
        attack_blocking_positions,
    )
