import random

from acts.act_one.settings import (
    WARDEN_REPOSITION_AFTER_ATTACKS,
    WARDEN_REPOSITION_COOLDOWN_ATTACKS,
    WARDEN_REPOSITION_MAX_TRAVEL,
    WARDEN_REPOSITION_MIN_TRAVEL,
    WARDEN_REPOSITION_PREFERRED_PLAYER_DISTANCE,
    WARDEN_REPOSITION_TRIGGER_PLAYER_DISTANCE,
)
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import can_move_to, distance_between, get_enemy_occupied_positions
from systems.enemy_ai.common import try_prepare_attack


def _warden_occupied_positions(
    game_state: GameState,
    warden: EnemyState,
) -> set[tuple[int, int]]:
    occupied = {
        position
        for enemy in game_state.floor.enemies
        if enemy is not warden and enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    occupied.update(
        (chest.column, chest.row)
        for chest in game_state.floor.chests
        if not chest.is_open
    )
    occupied.add(
        (
            game_state.floor.player_column,
            game_state.floor.player_row,
        )
    )
    occupied.add(
        (
            game_state.floor.stairs_column,
            game_state.floor.stairs_row,
        )
    )
    return occupied


def _choose_warden_reposition_target(
    game_state: GameState,
    warden: EnemyState,
) -> tuple[int, int] | None:
    floor = game_state.floor
    player_position = (floor.player_column, floor.player_row)
    current_position = (warden.column, warden.row)
    current_player_distance = distance_between(
        *current_position,
        *player_position,
    )
    if (
        current_player_distance
        > WARDEN_REPOSITION_TRIGGER_PLAYER_DISTANCE
    ):
        return None

    if warden.movement_bounds is None:
        left, top = 0, 0
        right = len(floor.map[0]) - 1
        bottom = len(floor.map) - 1
    else:
        left, top, right, bottom = warden.movement_bounds

    occupied = _warden_occupied_positions(game_state, warden)
    candidates = []
    for row in range(top, bottom + 1):
        for column in range(left, right + 1):
            position = (column, row)
            travel_distance = distance_between(
                *current_position,
                column,
                row,
            )
            if not (
                WARDEN_REPOSITION_MIN_TRAVEL
                <= travel_distance
                <= WARDEN_REPOSITION_MAX_TRAVEL
            ):
                continue
            if position in occupied or not can_move_to(
                floor.map,
                column,
                row,
            ):
                continue

            player_distance = distance_between(
                column,
                row,
                *player_position,
            )
            if (
                player_distance <= current_player_distance
            ):
                continue

            same_axis_penalty = int(
                column == floor.player_column
                or row == floor.player_row
            )
            preferred_distance_delta = abs(
                player_distance
                - WARDEN_REPOSITION_PREFERRED_PLAYER_DISTANCE
            )
            candidates.append(
                (
                    preferred_distance_delta,
                    -player_distance,
                    same_axis_penalty,
                    -travel_distance,
                    position,
                )
            )

    if not candidates:
        return None

    candidates.sort(key=lambda candidate: candidate[:-1])
    best_score = candidates[0][:-1]
    best_positions = [
        candidate[-1]
        for candidate in candidates
        if candidate[:-1] == best_score
    ]
    return random.choice(best_positions)


def note_warden_attack_completed(
    game_state: GameState,
    warden: EnemyState,
) -> bool:
    warden.warden_attacks_since_reposition += 1
    if warden.warden_reposition_cooldown > 0:
        warden.warden_reposition_cooldown -= 1

    if (
        warden.warden_attacks_since_reposition
        < WARDEN_REPOSITION_AFTER_ATTACKS
        or warden.warden_reposition_cooldown > 0
    ):
        return False

    target = _choose_warden_reposition_target(game_state, warden)
    if target is None:
        return False

    warden.warden_reposition_target = target
    add_log_message(
        game_state.combat_log,
        "The Crypt Warden marks a path through the chamber.",
        category="warning",
    )
    return True


def resolve_warden_reposition(
    game_state: GameState,
    warden: EnemyState,
) -> bool:
    target = warden.warden_reposition_target
    if target is None:
        return False

    occupied = _warden_occupied_positions(game_state, warden)
    if target in occupied or not can_move_to(
        game_state.floor.map,
        target[0],
        target[1],
    ):
        warden.warden_reposition_target = None
        warden.warden_attacks_since_reposition = 0
        return True

    origin = (warden.column, warden.row)
    warden.column, warden.row = target
    warden.warden_reposition_target = None
    warden.warden_attacks_since_reposition = 0
    warden.warden_reposition_cooldown = (
        WARDEN_REPOSITION_COOLDOWN_ATTACKS
    )
    warden.behavior_state = EnemyBehaviorState.CHASING
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor=warden.name,
            origin=origin,
            destination=target,
            data={"kind": "warden_reposition"},
        )
    )
    add_log_message(
        game_state.combat_log,
        "The Crypt Warden surges across the chamber.",
        category="enemy_attack",
    )
    return True


def take_warden_turn(
    game_state: GameState,
    warden: EnemyState,
    _occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
) -> None:
    try_prepare_attack(
        game_state,
        warden,
        attack_blocking_positions,
    )


__all__ = [
    "note_warden_attack_completed",
    "resolve_warden_reposition",
    "take_warden_turn",
]
