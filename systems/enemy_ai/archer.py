import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyState, GameState
from logic import distance_between, move_enemy_away
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


def take_archer_turn(
    game_state: GameState,
    enemy: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    distance_to_player: int,
) -> None:
    should_retreat = distance_to_player == 2

    if (
        not should_retreat
        and try_prepare_attack(
            game_state,
            enemy,
            attack_blocking_positions,
        )
    ):
        return

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    if should_retreat:
        previous_position = (enemy.column, enemy.row)
        maximum_steps = (
            2
            if random.random() < enemy.retreat_jump_chance
            else 1
        )
        enemy.column, enemy.row = move_enemy_away(
            game_state.floor.map,
            enemy,
            game_state.floor.player_column,
            game_state.floor.player_row,
            occupied_positions,
            maximum_steps,
            game_state.floor.barriers,
        )
        new_position = (enemy.column, enemy.row)

        if new_position != previous_position:
            game_state.emit(
                GameEvent(
                    type=GameEventType.MOVE,
                    actor=enemy.name,
                    origin=previous_position,
                    destination=new_position,
                    data={"kind": "retreat"},
                )
            )
            resolve_archer_barrage_zone_entry(
                game_state,
                enemy,
                previous_position,
            )

            if enemy.health <= 0:
                return

        if (
            distance_between(
                previous_position[0],
                previous_position[1],
                new_position[0],
                new_position[1],
            )
            == 2
        ):
            add_log_message(
                game_state.combat_log,
                f"{enemy.name} leaps away.",
            )
    else:
        move_toward_player(
            game_state,
            enemy,
            occupied_positions,
        )
        if enemy.health <= 0:
            return

    try_prepare_attack(
        game_state,
        enemy,
        attack_blocking_positions,
    )
