from acts.act_three.abilities.archer import (
    resolve_archer_barrage_zone_entry,
)
from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, GameState
from logic import (
    distance_between,
    get_enemy_attack_mode,
    get_enemy_attack_targets,
    move_enemy_toward_position,
)
from systems.enemy_ai.common import movement_is_ready


def _summoner_target(game_state, enemy):
    player = game_state.player
    candidates = []
    if player.summoner_familiar_active and player.summoner_familiar_position is not None and player.summoner_familiar_health > 0:
        candidates.append(("familiar", player.summoner_familiar_position))
    spirit = player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and spirit["floor"] == game_state.floor_index:
        candidates.append(("greater_manifestation", spirit["position"]))
    return min(candidates, key=lambda item: distance_between(enemy.column, enemy.row, *item[1]), default=(None, None))


def _familiar_is_preferred_target(
    game_state: GameState,
    enemy,
) -> bool:
    _, familiar_position = _summoner_target(game_state, enemy)
    if (
        enemy.type == "oracle"
        or familiar_position is None
    ):
        return False

    familiar_distance = distance_between(
        enemy.column,
        enemy.row,
        familiar_position[0],
        familiar_position[1],
    )
    player_distance = distance_between(
        enemy.column,
        enemy.row,
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    return familiar_distance <= max(1, enemy.attack_range) or (
        familiar_distance < player_distance
    )

def _prepare_attack_against_familiar(
    game_state: GameState,
    enemy,
    attack_blocking_positions: set[tuple[int, int]],
) -> bool:
    target_kind, familiar_position = _summoner_target(game_state, enemy)
    if familiar_position is None:
        return False

    attack_targets = get_enemy_attack_targets(
        game_state.floor.map,
        enemy,
        familiar_position[0],
        familiar_position[1],
        attack_blocking_positions,
    )
    if not attack_targets:
        return False

    enemy.attack_targets = attack_targets
    enemy.prepared_attack_mode = get_enemy_attack_mode(
        enemy,
        familiar_position[0],
        familiar_position[1],
    )
    enemy.prepared_attack_target = target_kind
    enemy.behavior_state = EnemyBehaviorState.PREPARING_ATTACK
    add_log_message(
        game_state.combat_log,
        (
            f"{enemy.name} prepares "
            f"{enemy.prepared_attack_mode.replace('_', ' ')} "
            f"attack on the {target_kind.replace('_', ' ')}."
        ),
    )
    return True

def _take_familiar_target_turn(
    game_state: GameState,
    enemy,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
) -> None:
    if _prepare_attack_against_familiar(
        game_state,
        enemy,
        attack_blocking_positions,
    ):
        return

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    _, familiar_position = _summoner_target(game_state, enemy)
    if familiar_position is None:
        return
    previous_position = (enemy.column, enemy.row)
    enemy.column, enemy.row = move_enemy_toward_position(
        game_state.floor.map,
        enemy,
        familiar_position[0],
        familiar_position[1],
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
                data={"kind": "pursue_familiar"},
            )
        )
        resolve_archer_barrage_zone_entry(
            game_state,
            enemy,
            previous_position,
        )
        if enemy.health <= 0:
            return

    _prepare_attack_against_familiar(
        game_state,
        enemy,
        attack_blocking_positions,
    )
