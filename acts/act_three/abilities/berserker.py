import math
from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    get_enemy_occupied_positions,
)
from acts.act_three.settings import (
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_CRUSHING_LEAP_RANGE,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_LAST_RAGE_TURNS,
)
from systems.grid_geometry import can_reach_adjacent_cell
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


def get_berserker_crushing_leap_direction(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> str:
    column_change = target[0] - origin[0]
    row_change = target[1] - origin[1]

    if abs(column_change) >= abs(row_change):
        if column_change < 0:
            return "left"

        return "right"

    if row_change < 0:
        return "left"

    return "right"


def get_berserker_crushing_leap_cells(
    game_state: GameState,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    if dx == dy == 0:
        return []

    sector = round(math.atan2(dy, dx) / (math.pi / 4)) % 8
    step_x, step_y = (
        (1, 0), (1, 1), (0, 1), (-1, 1),
        (-1, 0), (-1, -1), (0, -1), (1, -1),
    )[sector]
    cells = []
    previous = origin
    for distance in range(1, BERSERKER_CRUSHING_LEAP_RANGE + 1):
        cell = (origin[0] + step_x * distance, origin[1] + step_y * distance)
        if not can_reach_adjacent_cell(floor.map, previous, cell, floor.barriers):
            break
        cells.append(cell)
        previous = cell
    return cells


def request_berserker_crushing_leap(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "berserker":
        return False

    if (
        not player.debug_unlimited_abilities
        and player.berserker_crushing_leap_charge
        < BERSERKER_CRUSHING_LEAP_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Rending Spin is not charged.",
        )
        return True

    player.berserker_crushing_leap_aiming = True
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a direction, then press it again or click to dash.",
    )
    return True

def cancel_berserker_crushing_leap(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Rending Spin aiming cancelled.",
    )

def update_berserker_crushing_leap_preview(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    cells = (
        get_berserker_crushing_leap_cells(game_state, target)
        if player.berserker_crushing_leap_aiming and target is not None
        else []
    )
    player.berserker_crushing_leap_target = cells[-1] if cells else None
    player.berserker_crushing_leap_preview_cells = cells
    return bool(cells)


def perform_berserker_crushing_leap(
    game_state: GameState,
    current_time: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target = player.berserker_crushing_leap_target
    if (
        player.subclass != "berserker"
        or not player.berserker_crushing_leap_aiming
        or target is None
    ):
        return False

    origin = (floor.player_column, floor.player_row)
    impact_cells = get_berserker_crushing_leap_cells(game_state, target)
    if not impact_cells:
        return False

    direction = get_berserker_crushing_leap_direction(origin, impact_cells[-1])
    player.facing_direction = (-1, 0) if direction == "left" else (1, 0)
    player.movement_origin = None
    player.movement_animation_started_at = 0
    player.berserker_crushing_leap_charge = 0
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_origin = origin
    player.berserker_crushing_leap_started_at = current_time

    def living_enemy_at(cell):
        return next(
            (
                enemy
                for enemy in floor.enemies
                if enemy.health > 0
                and cell in get_enemy_occupied_positions(enemy)
            ),
            None,
        )

    struck_enemies = set()
    attacked_cells = []
    traveled_count = 0

    for index, cell in enumerate(impact_cells):
        attacked_cells.append(cell)
        enemy = living_enemy_at(cell)
        if enemy is not None and id(enemy) not in struck_enemies:
            struck_enemies.add(id(enemy))
            enemy_was_defeated = attack_enemy(
                game_state,
                enemy,
                player.damage_min,
                player.damage_max,
                player.crit_chance,
                attacker_position=origin,
            )
            if enemy.type == "oracle":
                oracle_hit_reaction(
                    enemy,
                    floor,
                    game_state.combat_log,
                )
            if enemy_was_defeated:
                resolve_enemy_defeat(game_state, enemy)

        if living_enemy_at(cell) is None:
            traveled_count = index + 1
            continue

        next_index = index + 1
        if (
            next_index >= len(impact_cells)
            or living_enemy_at(impact_cells[next_index]) is not None
        ):
            break

    traveled_cells = impact_cells[:traveled_count]
    player.berserker_crushing_leap_preview_cells = traveled_cells
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=tuple(attacked_cells),
            data={"kind": "berserker_rending_spin"},
        )
    )

    if not struck_enemies:
        add_log_message(
            game_state.combat_log,
            "Rending Spin hits nothing.",
        )

    if traveled_cells:
        destination = traveled_cells[-1]
        floor.player_column, floor.player_row = destination
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor="hero",
                origin=origin,
                destination=destination,
                positions=tuple(traveled_cells),
                data={"kind": "berserker_rending_spin"},
            )
        )

    add_log_message(
        game_state.combat_log,
        "The berserker unleashes Rending Spin.",
    )
    return True

def request_berserker_last_rage(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "berserker":
        return False

    if player.berserker_last_rage_turns > 0:
        add_log_message(
            game_state.combat_log,
            "Last Rage is already active.",
        )
        return True
    if (
        not player.debug_unlimited_abilities
        and player.berserker_last_rage_charge
        < BERSERKER_LAST_RAGE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Last Rage is not charged.",
        )
        return True

    player.berserker_last_rage_charge = 0
    player.berserker_last_rage_turns = (
        BERSERKER_LAST_RAGE_TURNS
    )
    player.berserker_last_rage_started_at = current_time
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Last Rage ignites. The berserker cannot die.",
    )
    return True

def advance_berserker_last_rage(
    game_state: GameState,
) -> None:
    player = game_state.player
    if (
        player.subclass != "berserker"
        or player.berserker_last_rage_turns <= 0
    ):
        return

    player.berserker_last_rage_turns -= 1
    if player.berserker_last_rage_turns == 0:
        add_log_message(
            game_state.combat_log,
            "Last Rage fades. Death can claim the berserker again.",
        )
