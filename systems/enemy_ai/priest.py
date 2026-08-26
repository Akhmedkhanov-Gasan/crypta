from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState, EnemyState, GameState
from logic import (
    distance_between,
    has_line_of_sight,
    move_enemy_away,
    move_enemy_toward_position,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)

PRIEST_RETREAT_INTERVAL = 2
PRIEST_RETREAT_TRIGGER_DISTANCE = 3


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


def priest_should_join_combat(
    priest: EnemyState,
    enemies: list[EnemyState],
) -> bool:
    return any(
        enemy is not priest
        and enemy.health > 0
        and enemy.is_active
        and distance_between(
            priest.column,
            priest.row,
            enemy.column,
            enemy.row,
        )
        <= priest.heal_range
        and (
            enemy.is_aggro
            or enemy.health < enemy.max_health
        )
        for enemy in enemies
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

    can_heal_from_current_position = (
        distance_to_ally <= priest.heal_range
        and has_line_of_sight(
            game_state.floor.map,
            priest.column,
            priest.row,
            heal_candidate.column,
            heal_candidate.row,
        )
    )

    if can_heal_from_current_position:
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


def _priest_retreat_is_due(
    priest: EnemyState,
) -> bool:
    priest.priest_retreat_counter += 1

    if (
        priest.priest_retreat_counter
        < PRIEST_RETREAT_INTERVAL
    ):
        return False

    priest.priest_retreat_counter = 0
    return True


def take_priest_turn(
    game_state: GameState,
    priest: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> None:
    floor = game_state.floor
    priest_position = (
        priest.column,
        priest.row,
    )
    distance_to_player = distance_between(
        priest.column,
        priest.row,
        floor.player_column,
        floor.player_row,
    )
    standing_in_danger = (
        hazard_costs.get(priest_position, 0) > 0
    )
    scheduled_retreat = (
        _priest_retreat_is_due(priest)
        and distance_to_player
        <= PRIEST_RETREAT_TRIGGER_DISTANCE
    )
    should_retreat = (
        standing_in_danger
        or scheduled_retreat
    )

    if should_retreat:
        if priest.is_immobile:
            try_prepare_attack(
                game_state,
                priest,
                attack_blocking_positions,
            )
            return

        if not movement_is_ready(priest):
            try_prepare_attack(
                game_state,
                priest,
                attack_blocking_positions,
            )
            return

        previous_position = (
            priest.column,
            priest.row,
        )
        priest.column, priest.row = move_enemy_away(
            floor.map,
            priest,
            floor.player_column,
            floor.player_row,
            occupied_positions,
            1,
            floor.barriers,
            hazard_costs,
        )
        new_position = (
            priest.column,
            priest.row,
        )

        if new_position != previous_position:
            game_state.emit(
                GameEvent(
                    type=GameEventType.MOVE,
                    actor=priest.name,
                    origin=previous_position,
                    destination=new_position,
                    data={"kind": "support_retreat"},
                )
            )
            resolve_archer_barrage_zone_entry(
                game_state,
                priest,
                previous_position,
            )

            if priest.health <= 0:
                return

            try_prepare_attack(
                game_state,
                priest,
                attack_blocking_positions,
            )
            return

        # Отступить некуда. Не заставляем жреца вместо этого
        # приближаться к игроку в тот же ход.
        try_prepare_attack(
            game_state,
            priest,
            attack_blocking_positions,
        )
        return

    if try_prepare_attack(
        game_state,
        priest,
        attack_blocking_positions,
    ):
        return

    if priest.is_immobile or not movement_is_ready(priest):
        return

    move_toward_player(
        game_state,
        priest,
        occupied_positions,
        hazard_costs,
    )

    if priest.health <= 0:
        return

    try_prepare_attack(
        game_state,
        priest,
        attack_blocking_positions,
    )
