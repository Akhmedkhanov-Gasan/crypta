from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import (
    get_enemy_attack_mode,
    get_enemy_attack_targets,
    move_enemy,
)


def prepare_enemy_attack(
    game_state: GameState,
    enemy: EnemyState,
    attack_targets: list[tuple[int, int]],
    attack_mode: str,
) -> None:
    enemy.attack_targets = attack_targets
    enemy.prepared_attack_mode = attack_mode
    enemy.behavior_state = (
        EnemyBehaviorState.PREPARING_ATTACK
    )
    add_log_message(
        game_state.combat_log,
        (
            f"{enemy.name} prepares "
            f"{attack_mode.replace('_', ' ')} attack."
        ),
    )


def try_prepare_attack(
    game_state: GameState,
    enemy: EnemyState,
    attack_blocking_positions: set[tuple[int, int]],
) -> bool:
    floor = game_state.floor
    attack_targets = get_enemy_attack_targets(
        floor.map,
        enemy,
        floor.player_column,
        floor.player_row,
        attack_blocking_positions,
    )

    if not attack_targets:
        return False

    attack_mode = get_enemy_attack_mode(
        enemy,
        floor.player_column,
        floor.player_row,
    )
    prepare_enemy_attack(
        game_state,
        enemy,
        attack_targets,
        attack_mode,
    )

    return True


def movement_is_ready(enemy: EnemyState) -> bool:
    enemy.move_counter += 1

    if enemy.move_counter < enemy.move_every:
        return False

    enemy.move_counter = 0
    return True


def move_toward_player(
    game_state: GameState,
    enemy: EnemyState,
    occupied_positions: set[tuple[int, int]],
) -> None:
    floor = game_state.floor
    previous_position = (enemy.column, enemy.row)
    enemy.column, enemy.row = move_enemy(
        floor.map,
        enemy,
        floor.player_column,
        floor.player_row,
        occupied_positions,
    )
    new_position = (enemy.column, enemy.row)

    if new_position != previous_position:
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor=enemy.name,
                origin=previous_position,
                destination=new_position,
            )
        )
