from game.events import GameEvent, GameEventType
from game.state import EnemyState, GameState
from logic import (
    can_move_between,
    distance_between,
    get_enemy_attack_targets,
)
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


def _brute_can_cleave_from(
    game_state: GameState,
    brute: EnemyState,
    position: tuple[int, int],
    attack_blocking_positions: set[tuple[int, int]],
) -> bool:
    hypothetical_brute = {
        "column": position[0],
        "row": position[1],
        "attack_kind": brute.attack_kind,
        "attack_range": brute.attack_range,
    }

    return bool(
        get_enemy_attack_targets(
            game_state.floor.map,
            hypothetical_brute,
            game_state.floor.player_column,
            game_state.floor.player_row,
            attack_blocking_positions,
        )
    )


def _brute_position_score(
    game_state: GameState,
    brute: EnemyState,
    position: tuple[int, int],
    current_position: tuple[int, int],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, bool, int, int, bool]:
    floor = game_state.floor
    column_difference = abs(
        floor.player_column - position[0]
    )
    row_difference = abs(
        floor.player_row - position[1]
    )
    player_distance = distance_between(
        position[0],
        position[1],
        floor.player_column,
        floor.player_row,
    )

    alignment_gap = (
        0
        if column_difference == 0 or row_difference == 0
        else min(column_difference, row_difference)
    )
    distance_from_cleave_range = abs(player_distance - 2)
    can_cleave = _brute_can_cleave_from(
        game_state,
        brute,
        position,
        attack_blocking_positions,
    )

    return (
        hazard_costs.get(position, 0),
        not can_cleave,
        alignment_gap,
        distance_from_cleave_range,
        position != current_position,
    )


def _choose_brute_position(
    game_state: GameState,
    brute: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, int]:
    floor = game_state.floor
    current_position = (brute.column, brute.row)
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
            brute.column + column_change,
            brute.row + row_change,
        )

        if (
            position == player_position
            or position in occupied_positions
            or not can_move_between(
                floor.map,
                brute.column,
                brute.row,
                position[0],
                position[1],
                floor.barriers,
            )
        ):
            continue

        if brute.movement_bounds is not None:
            left, top, right, bottom = brute.movement_bounds
            if not (
                left <= position[0] <= right
                and top <= position[1] <= bottom
            ):
                continue

        candidates.append(position)

    return min(
        candidates,
        key=lambda position: _brute_position_score(
            game_state,
            brute,
            position,
            current_position,
            attack_blocking_positions,
            hazard_costs,
        ),
    )


def take_brute_turn(
    game_state: GameState,
    brute: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> None:
    if try_prepare_attack(
        game_state,
        brute,
        attack_blocking_positions,
    ):
        return

    if brute.is_immobile or not movement_is_ready(brute):
        return

    previous_position = (brute.column, brute.row)
    tactical_position = _choose_brute_position(
        game_state,
        brute,
        occupied_positions,
        attack_blocking_positions,
        hazard_costs,
    )

    if tactical_position == previous_position:
        move_toward_player(
            game_state,
            brute,
            occupied_positions,
            hazard_costs,
        )

        if brute.health <= 0:
            return

        try_prepare_attack(
            game_state,
            brute,
            attack_blocking_positions,
        )
        return

    brute.column, brute.row = tactical_position

    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor=brute.name,
            origin=previous_position,
            destination=tactical_position,
            data={"kind": "brute_pressure"},
        )
    )
    resolve_archer_barrage_zone_entry(
        game_state,
        brute,
        previous_position,
    )

    if brute.health <= 0:
        return

    try_prepare_attack(
        game_state,
        brute,
        attack_blocking_positions,
    )
