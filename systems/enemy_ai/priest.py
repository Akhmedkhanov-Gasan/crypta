from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import distance_between, move_enemy_toward_position
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


def get_heal_candidate(
    priest: EnemyState,
    enemies: list[EnemyState],
) -> EnemyState | None:
    reserved_targets = {
        id(other_priest.heal_target)
        for other_priest in enemies
        if (
            other_priest is not priest
            and other_priest.type == "priest"
            and other_priest.health > 0
            and other_priest.heal_target is not None
        )
    }
    candidates = [
        enemy
        for enemy in enemies
        if (
            enemy is not priest
            and enemy.health > 0
            and enemy.health < enemy.max_health
            and enemy.curse_turns <= 0
            and enemy.is_active
            and id(enemy) not in reserved_targets
            and distance_between(
                priest.column,
                priest.row,
                enemy.column,
                enemy.row,
            )
            <= priest.heal_range
        )
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda enemy: (
            enemy.health / enemy.max_health,
            distance_between(
                priest.column,
                priest.row,
                enemy.column,
                enemy.row,
            ),
        ),
    )


def try_start_healing(
    game_state: GameState,
    priest: EnemyState,
    occupied_positions: set[tuple[int, int]],
    heal_is_ready: bool,
) -> bool:
    if not heal_is_ready:
        return False

    heal_candidate = get_heal_candidate(
        priest,
        game_state.floor.enemies,
    )

    if heal_candidate is None:
        return False

    distance_to_ally = distance_between(
        priest.column,
        priest.row,
        heal_candidate.column,
        heal_candidate.row,
    )

    if distance_to_ally == 1:
        priest.heal_target = heal_candidate
        priest.behavior_state = (
            EnemyBehaviorState.PREPARING_HEAL
        )
        game_state.emit(
            GameEvent(
                type=GameEventType.PREPARE_HEAL,
                actor=priest.name,
                target=heal_candidate.name,
                origin=(priest.column, priest.row),
                destination=(
                    heal_candidate.column,
                    heal_candidate.row,
                ),
                data={"enemy_type": priest.type},
            )
        )
        add_log_message(
            game_state.combat_log,
            (
                f"{priest.name} prepares to heal "
                f"{heal_candidate.name}."
            ),
        )
        return True

    priest.move_counter += 1

    if priest.move_counter < priest.move_every:
        return False

    priest.move_counter = 0
    previous_position = (priest.column, priest.row)
    priest.column, priest.row = move_enemy_toward_position(
        game_state.floor.map,
        priest,
        heal_candidate.column,
        heal_candidate.row,
        occupied_positions,
    )
    new_position = (priest.column, priest.row)

    if new_position == previous_position:
        return False

    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor=priest.name,
            target=heal_candidate.name,
            origin=previous_position,
            destination=new_position,
            data={"kind": "move_to_heal"},
        )
    )
    resolve_archer_barrage_zone_entry(
        game_state,
        priest,
        previous_position,
    )
    return True
