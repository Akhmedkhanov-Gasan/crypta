from game.combat_log import add_log_message
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import direction_toward, has_line_of_sight


def try_raise_shield(
    game_state: GameState,
    enemy: EnemyState,
    shield_is_ready: bool,
    distance_to_player: int,
) -> bool:
    floor = game_state.floor

    if (
        not shield_is_ready
        or distance_to_player > 3
        or not has_line_of_sight(
            floor.map,
            enemy.column,
            enemy.row,
            floor.player_column,
            floor.player_row,
        )
    ):
        return False

    enemy.shield_direction = direction_toward(
        enemy.column,
        enemy.row,
        floor.player_column,
        floor.player_row,
    )
    enemy.shield_turns = enemy.shield_duration
    enemy.behavior_state = EnemyBehaviorState.GUARDING
    add_log_message(
        game_state.combat_log,
        f"{enemy.name} raises its shield.",
    )

    return True
