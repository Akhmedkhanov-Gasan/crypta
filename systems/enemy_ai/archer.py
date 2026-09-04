import random

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyState, GameState
from logic import (
    can_move_between,
    distance_between,
    has_clear_line,
    move_enemy_away,
)
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


ARCHER_PREFERRED_MIN_DISTANCE = 3
ARCHER_PREFERRED_MAX_DISTANCE = 5

ARCHER_SCREEN_TYPES = {
    "goblin",
    "brute",
    "sentinel",
    "warden",
}

def _position_has_melee_screen(
    game_state: GameState,
    archer: EnemyState,
    position: tuple[int, int],
) -> bool:
    player_position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    player_to_archer = distance_between(
        *player_position,
        *position,
    )

    for ally in game_state.floor.enemies:
        if (
            ally is archer
            or ally.health <= 0
            or not ally.is_active
            or ally.type not in ARCHER_SCREEN_TYPES
        ):
            continue

        ally_position = (ally.column, ally.row)
        player_to_ally = distance_between(
            *player_position,
            *ally_position,
        )
        ally_to_archer = distance_between(
            *ally_position,
            *position,
        )

        if (
            player_to_ally < player_to_archer
            and player_to_ally + ally_to_archer
            == player_to_archer
        ):
            return True

    return False

def _archer_position_score(
    game_state: GameState,
    archer: EnemyState,
    position: tuple[int, int],
    current_position: tuple[int, int],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, bool, int, bool, bool]:
    floor = game_state.floor
    player_position = (
        floor.player_column,
        floor.player_row,
    )
    player_distance = distance_between(
        *position,
        *player_position,
    )

    has_firing_line = (
        2 <= player_distance <= archer.attack_range
        and has_clear_line(
            floor.map,
            position[0],
            position[1],
            player_position[0],
            player_position[1],
            attack_blocking_positions,
        )
    )

    if player_distance < ARCHER_PREFERRED_MIN_DISTANCE:
        distance_penalty = (
            ARCHER_PREFERRED_MIN_DISTANCE - player_distance
        )
    elif player_distance > ARCHER_PREFERRED_MAX_DISTANCE:
        distance_penalty = (
            player_distance - ARCHER_PREFERRED_MAX_DISTANCE
        )
    else:
        distance_penalty = 0

    has_melee_screen = _position_has_melee_screen(
        game_state,
        archer,
        position,
    )

    return (
        hazard_costs.get(position, 0),
        not has_firing_line,
        distance_penalty,
        not has_melee_screen,
        position != current_position,
    )

def _choose_archer_position(
    game_state: GameState,
    archer: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, int]:
    floor = game_state.floor
    current_position = (archer.column, archer.row)
    player_position = (
        floor.player_column,
        floor.player_row,
    )

    candidates = [current_position]

    for column_change, row_change in (
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
    ):
        position = (
            archer.column + column_change,
            archer.row + row_change,
        )

        if (
            position == player_position
            or position in occupied_positions
            or not can_move_between(
                floor.map,
                archer.column,
                archer.row,
                position[0],
                position[1],
                floor.barriers,
            )
        ):
            continue

        if archer.movement_bounds is not None:
            left, top, right, bottom = archer.movement_bounds
            if not (
                left <= position[0] <= right
                and top <= position[1] <= bottom
            ):
                continue

        candidates.append(position)

    return min(
        candidates,
        key=lambda position: _archer_position_score(
            game_state,
            archer,
            position,
            current_position,
            attack_blocking_positions,
            hazard_costs,
        ),
    )


def take_archer_turn(
    game_state: GameState,
    enemy: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    distance_to_player: int,
    hazard_costs: dict[tuple[int, int], int],
) -> None:
    should_retreat = distance_to_player <= 2

    if enemy.is_immobile:
        try_prepare_attack(
            game_state,
            enemy,
            attack_blocking_positions,
        )
        return

    if not movement_is_ready(enemy):
        try_prepare_attack(
            game_state,
            enemy,
            attack_blocking_positions,
        )
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
            hazard_costs,
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
                category="defense",
            )

    else:
        tactical_position = _choose_archer_position(
            game_state,
            enemy,
            occupied_positions,
            attack_blocking_positions,
            hazard_costs,
        )
        previous_position = (enemy.column, enemy.row)

        if tactical_position != previous_position:
            enemy.column, enemy.row = tactical_position

            game_state.emit(
                GameEvent(
                    type=GameEventType.MOVE,
                    actor=enemy.name,
                    origin=previous_position,
                    destination=tactical_position,
                    data={"kind": "reposition"},
                )
            )
            resolve_archer_barrage_zone_entry(
                game_state,
                enemy,
                previous_position,
            )

            if enemy.health <= 0:
                return

        elif try_prepare_attack(
            game_state,
            enemy,
            attack_blocking_positions,
        ):
            return

        else:
            move_toward_player(
                game_state,
                enemy,
                occupied_positions,
                hazard_costs,
            )

            if enemy.health <= 0:
                return

    try_prepare_attack(
        game_state,
        enemy,
        attack_blocking_positions,
    )
