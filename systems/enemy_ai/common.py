from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import (
    get_enemy_attack_mode,
    get_enemy_attack_targets,
    move_enemy,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


def prepare_enemy_attack(
    game_state: GameState,
    enemy: EnemyState,
    attack_targets: list[tuple[int, int]],
    attack_mode: str,
) -> None:
    enemy.attack_targets = attack_targets
    enemy.prepared_attack_mode = attack_mode
    enemy.attack_windup_turns_remaining = (
        1 if enemy.type == "brute" else 0
    )
    enemy.behavior_state = (
        EnemyBehaviorState.PREPARING_ATTACK
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.PREPARE_ATTACK,
            actor=enemy.name,
            origin=(enemy.column, enemy.row),
            positions=tuple(attack_targets),
            data={"mode": attack_mode, "enemy_type": enemy.type},
        )
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
        floor.barriers,
    )
    if enemy.movement_bounds is not None:
        left, top, right, bottom = enemy.movement_bounds
        if not (
            left <= enemy.column <= right
            and top <= enemy.row <= bottom
        ):
            enemy.column, enemy.row = previous_position
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
        resolve_archer_barrage_zone_entry(
            game_state,
            enemy,
            previous_position,
        )
