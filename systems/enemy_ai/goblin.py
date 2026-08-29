import random

from enemies import ENEMY_TYPES
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import (
    EnemyBehaviorState,
    EnemyState,
    GameState,
)
from logic import (
    can_move_to,
    distance_between,
    move_enemy_toward_cell,
    positions_are_adjacent,
    has_line_of_sight,
    get_enemy_occupied_positions,
)
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    try_prepare_attack,
)
from systems.player_abilities import (
    resolve_archer_barrage_zone_entry,
)


FRONTLINE_ENEMY_TYPES = {
    "goblin",
    "brute",
    "sentinel",
}

GOBLIN_SUMMON_COUNT = 2
GOBLIN_PACK_ALERT_RADIUS = 7
GOBLIN_SUMMON_CHANCE = 0.20

def _engaged_frontline_directions(
    game_state: GameState,
    goblin: EnemyState,
) -> list[tuple[int, int]]:
    floor = game_state.floor
    directions = []

    for ally in floor.enemies:
        if (
            ally is goblin
            or ally.health <= 0
            or not ally.is_active
            or ally.type not in FRONTLINE_ENEMY_TYPES
            or not positions_are_adjacent(
                ally.column,
                ally.row,
                floor.player_column,
                floor.player_row,
            )
        ):
            continue

        directions.append(
            (
                ally.column - floor.player_column,
                ally.row - floor.player_row,
            )
        )

    return directions


def _engagement_position_score(
    game_state: GameState,
    goblin: EnemyState,
    position: tuple[int, int],
    frontline_directions: list[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, int, bool, int]:
    floor = game_state.floor
    candidate_direction = (
        position[0] - floor.player_column,
        position[1] - floor.player_row,
    )

    same_side_count = 0
    has_opposite_ally = False

    for ally_direction in frontline_directions:
        direction_dot_product = (
            candidate_direction[0] * ally_direction[0]
            + candidate_direction[1] * ally_direction[1]
        )

        if direction_dot_product > 0:
            same_side_count += 1
        elif direction_dot_product < 0:
            has_opposite_ally = True

    distance_to_position = distance_between(
        goblin.column,
        goblin.row,
        position[0],
        position[1],
    )

    return (
        hazard_costs.get(position, 0),
        same_side_count,
        (
            not has_opposite_ally
            if frontline_directions
            else False
        ),
        distance_to_position,
    )


def _choose_engagement_position(
    game_state: GameState,
    goblin: EnemyState,
    occupied_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
) -> tuple[int, int] | None:
    floor = game_state.floor
    current_position = (
        goblin.column,
        goblin.row,
    )
    frontline_directions = _engaged_frontline_directions(
        game_state,
        goblin,
    )
    candidates = []

    for row_change in (-1, 0, 1):
        for column_change in (-1, 0, 1):
            if column_change == 0 and row_change == 0:
                continue

            position = (
                floor.player_column + column_change,
                floor.player_row + row_change,
            )

            if (
                not can_move_to(
                    floor.map,
                    position[0],
                    position[1],
                )
                or (
                    position != current_position
                    and position in occupied_positions
                )
            ):
                continue

            candidates.append(position)

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda position: _engagement_position_score(
            game_state,
            goblin,
            position,
            frontline_directions,
            hazard_costs,
        ),
    )

def goblin_should_join_combat(
    game_state: GameState,
    goblin: EnemyState,
) -> bool:
    floor = game_state.floor

    return any(
        ally is not goblin
        and ally.health > 0
        and ally.is_active
        and ally.is_aggro
        and distance_between(
            goblin.column,
            goblin.row,
            ally.column,
            ally.row,
        )
        <= GOBLIN_PACK_ALERT_RADIUS
        and has_line_of_sight(
            floor.map,
            goblin.column,
            goblin.row,
            ally.column,
            ally.row,
        )
        for ally in floor.enemies
    )


def try_start_goblin_summon(
    game_state: GameState,
    goblin: EnemyState,
) -> bool:
    if (
        goblin.is_summoned
        or goblin.goblin_summon_used
        or not goblin.is_aggro
        or (
            goblin.column,
            goblin.row,
        ) not in game_state.floor.visible_cells
    ):
        return False

    if random.random() >= GOBLIN_SUMMON_CHANCE:
        return False

    goblin.goblin_summon_used = True
    goblin.summon_windup_turns_remaining = 4
    goblin.attack_targets = []
    goblin.prepared_attack_mode = None
    goblin.behavior_state = (
        EnemyBehaviorState.PREPARING_SUMMON
    )

    game_state.emit(
        GameEvent(
            type=GameEventType.PREPARE_SUMMON,
            actor=goblin.name,
            origin=(goblin.column, goblin.row),
            data={"enemy_type": goblin.type},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"{goblin.name} begins calling for reinforcements.",
        category="warning",
    )
    return True


def take_goblin_turn(
    game_state: GameState,
    goblin: EnemyState,
    occupied_positions: set[tuple[int, int]],
    attack_blocking_positions: set[tuple[int, int]],
    hazard_costs: dict[tuple[int, int], int],
    summoning_enabled: bool = False,
) -> None:
    if (
            summoning_enabled
            and try_start_goblin_summon(
        game_state,
        goblin,
    )
    ):
        return
    if try_prepare_attack(
        game_state,
        goblin,
        attack_blocking_positions,
    ):
        return

    if goblin.is_immobile or not movement_is_ready(goblin):
        return

    engagement_position = _choose_engagement_position(
        game_state,
        goblin,
        occupied_positions,
        hazard_costs,
    )

    if engagement_position is None:
        move_toward_player(
            game_state,
            goblin,
            occupied_positions,
            hazard_costs,
        )
    else:
        previous_position = (
            goblin.column,
            goblin.row,
        )
        goblin.column, goblin.row = move_enemy_toward_cell(
            game_state.floor.map,
            goblin,
            engagement_position[0],
            engagement_position[1],
            occupied_positions,
            game_state.floor.barriers,
            hazard_costs,
        )
        new_position = (
            goblin.column,
            goblin.row,
        )

        if new_position == previous_position:
            move_toward_player(
                game_state,
                goblin,
                occupied_positions,
                hazard_costs,
            )
        else:
            game_state.emit(
                GameEvent(
                    type=GameEventType.MOVE,
                    actor=goblin.name,
                    origin=previous_position,
                    destination=new_position,
                    data={"kind": "flank"},
                )
            )
            resolve_archer_barrage_zone_entry(
                game_state,
                goblin,
                previous_position,
            )

    if goblin.health <= 0:
        return

    try_prepare_attack(
        game_state,
        goblin,
        attack_blocking_positions,
    )


def _goblin_summon_positions(
    game_state: GameState,
    summoner: EnemyState,
    hazard_costs: dict[tuple[int, int], int],
) -> list[tuple[int, int]]:
    floor = game_state.floor
    occupied_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    occupied_positions.update(
        (chest.column, chest.row)
        for chest in floor.chests
        if not chest.is_open
    )
    occupied_positions.update(
        (crate.column, crate.row)
        for crate in floor.breakable_crates
        if not crate.is_broken
    )
    occupied_positions.add(
        (floor.player_column, floor.player_row)
    )
    occupied_positions.add(
        (floor.stairs_column, floor.stairs_row)
    )

    if (
        game_state.player.summoner_familiar_active
        and game_state.player.summoner_familiar_position
        is not None
    ):
        occupied_positions.add(
            game_state.player.summoner_familiar_position
        )

    candidates = []

    for row_change in (-1, 0, 1):
        for column_change in (-1, 0, 1):
            if column_change == 0 and row_change == 0:
                continue

            position = (
                summoner.column + column_change,
                summoner.row + row_change,
            )

            if (
                position in occupied_positions
                or not can_move_to(
                    floor.map,
                    position[0],
                    position[1],
                )
            ):
                continue

            candidates.append(position)

    random.shuffle(candidates)
    candidates.sort(
        key=lambda position: hazard_costs.get(position, 0)
    )
    return candidates[:GOBLIN_SUMMON_COUNT]


def _next_summoned_goblin_name(
    game_state: GameState,
) -> str:
    existing_names = {
        enemy.name
        for enemy in game_state.floor.enemies
    }
    number = 1

    while True:
        name = f"Goblin Reinforcement {number}"

        if name not in existing_names:
            return name

        number += 1


def resolve_goblin_summon(
    game_state: GameState,
    summoner: EnemyState,
    hazard_costs: dict[tuple[int, int], int],
) -> None:
    spawn_positions = _goblin_summon_positions(
        game_state,
        summoner,
        hazard_costs,
    )
    summoner.behavior_state = EnemyBehaviorState.CHASING
    summoner.summon_windup_turns_remaining = 0
    summoner.summon_animation_started_at = -1

    summoned_names = []

    for position in spawn_positions:
        reinforcement = EnemyState.from_config(
            enemy_type="goblin",
            column=position[0],
            row=position[1],
            name=_next_summoned_goblin_name(game_state),
            config=ENEMY_TYPES["goblin"],
            belongs_to_boss_group=False,
        )
        reinforcement.is_summoned = True
        reinforcement.is_aggro = True
        reinforcement.behavior_state = (
            EnemyBehaviorState.CHASING
        )

        game_state.floor.enemies.append(reinforcement)
        summoned_names.append(reinforcement.name)

    game_state.emit(
        GameEvent(
            type=GameEventType.SUMMON,
            actor=summoner.name,
            origin=(summoner.column, summoner.row),
            positions=tuple(spawn_positions),
            data={
                "enemy_type": summoner.type,
                "summoned_names": tuple(summoned_names),
            },
        )
    )

    if summoned_names:
        add_log_message(
            game_state.combat_log,
            (
                f"{summoner.name} calls "
                f"{len(summoned_names)} reinforcements."
            ),
            category="enemy_attack",
        )
    else:
        add_log_message(
            game_state.combat_log,
            f"{summoner.name}'s call goes unanswered.",
            category="system",
        )
