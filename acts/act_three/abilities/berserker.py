from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    can_move_to,
    get_enemy_occupied_positions,
    has_line_of_sight,
)
from settings import (
    BERSERKER_CRUSHING_LEAP_CHARGES,
    BERSERKER_CRUSHING_LEAP_RANGE,
    BERSERKER_LAST_RAGE_CHARGES,
    BERSERKER_LAST_RAGE_TURNS,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

def get_berserker_crushing_leap_cells(
    game_state: GameState,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    dungeon_map = game_state.floor.map
    cells = []
    for row_change in (-1, 0, 1):
        for column_change in (-1, 0, 1):
            if column_change == 0 and row_change == 0:
                continue
            column = target[0] + column_change
            row = target[1] + row_change
            if not (
                0 <= row < len(dungeon_map)
                and 0 <= column < len(dungeon_map[0])
            ):
                continue
            if can_move_to(dungeon_map, column, row):
                cells.append((column, row))
    return cells

def is_valid_berserker_crushing_leap_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    column, row = target
    if (
        player.subclass != "berserker"
        or not player.berserker_crushing_leap_aiming
    ):
        return False
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[0])
    ):
        return False
    if not can_move_to(floor.map, column, row):
        return False

    origin = (floor.player_column, floor.player_row)
    if target == origin:
        return False
    if (
        abs(column - origin[0]) + abs(row - origin[1])
        > BERSERKER_CRUSHING_LEAP_RANGE
    ):
        return False
    if not has_line_of_sight(
        floor.map,
        origin[0],
        origin[1],
        column,
        row,
    ):
        return False
    if any(
        enemy.health > 0
        and target in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    ):
        return False
    if any(
        not chest.is_open
        and target == (chest.column, chest.row)
        for chest in floor.chests
    ):
        return False
    return True

def request_berserker_crushing_leap(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "berserker":
        return False

    if player.berserker_crushing_leap_aiming:
        cancel_berserker_crushing_leap(game_state)
        return True

    if (
        player.berserker_crushing_leap_charge
        < BERSERKER_CRUSHING_LEAP_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Crushing Leap is not charged.",
        )
        return True

    player.berserker_crushing_leap_aiming = True
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a landing cell for Crushing Leap.",
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
        "Crushing Leap aiming cancelled.",
    )

def update_berserker_crushing_leap_preview(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        target is None
        or not is_valid_berserker_crushing_leap_target(
            game_state,
            target,
        )
    ):
        player.berserker_crushing_leap_target = None
        player.berserker_crushing_leap_preview_cells.clear()
        return False

    player.berserker_crushing_leap_target = target
    player.berserker_crushing_leap_preview_cells = (
        get_berserker_crushing_leap_cells(
            game_state,
            target,
        )
    )
    return True

def perform_berserker_crushing_leap(
    game_state: GameState,
    current_time: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target = player.berserker_crushing_leap_target
    if (
        target is None
        or not is_valid_berserker_crushing_leap_target(
            game_state,
            target,
        )
    ):
        return False

    origin = (floor.player_column, floor.player_row)
    impact_cells = get_berserker_crushing_leap_cells(
        game_state,
        target,
    )
    floor.player_column, floor.player_row = target
    player.berserker_crushing_leap_charge = 0
    player.berserker_crushing_leap_aiming = False
    player.berserker_crushing_leap_target = None
    player.berserker_crushing_leap_preview_cells = list(
        impact_cells
    )
    player.berserker_crushing_leap_origin = origin
    player.berserker_crushing_leap_started_at = current_time

    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=origin,
            destination=target,
            data={"kind": "berserker_crushing_leap"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=target,
            positions=tuple(impact_cells),
            data={"kind": "berserker_crushing_leap"},
        )
    )

    enemies_hit = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and any(
                position in impact_cells
                for position in get_enemy_occupied_positions(
                    enemy
                )
            )
        )
    ]
    if not enemies_hit:
        add_log_message(
            game_state.combat_log,
            "Crushing Leap hits nothing.",
        )

    for enemy in enemies_hit:
        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            attacker_position=target,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)

    add_log_message(
        game_state.combat_log,
        "The berserker crashes into the battlefield.",
    )
    return True

def request_berserker_last_rage(
    game_state: GameState,
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
        player.berserker_last_rage_charge
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
