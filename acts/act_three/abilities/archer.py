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
    has_line_of_sight,
)
from acts.act_three.settings import (
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
    ARCHER_LEAP_CHARGES,
    ARCHER_LEAP_RANGE,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

def request_archer_empowered_shot(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_empowered_shot_aiming:
        player.archer_empowered_shot_aiming = False
        player.archer_empowered_shot_target = None
        add_log_message(
            game_state.combat_log,
            "Empowered Shot aiming cancelled.",
        )
        return True

    if (
        not player.debug_unlimited_abilities
        and player.archer_empowered_shot_charge
        < ARCHER_EMPOWERED_SHOT_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Empowered Shot is not charged.",
        )
        return True

    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_empowered_shot_aiming = True
    player.archer_empowered_shot_target = None
    add_log_message(
        game_state.combat_log,
        "Choose a visible enemy for Empowered Shot.",
    )
    return True

def cancel_archer_empowered_shot(game_state: GameState) -> None:
    game_state.player.archer_empowered_shot_aiming = False
    game_state.player.archer_empowered_shot_target = None
    add_log_message(
        game_state.combat_log,
        "Empowered Shot aiming cancelled.",
    )

def is_valid_archer_empowered_shot_target(
    game_state: GameState,
    target_cell: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer" or not player.archer_empowered_shot_aiming:
        return False
    if not (0 <= target_cell[1] < len(floor.map)):
        return False
    if not (0 <= target_cell[0] < len(floor.map[0])):
        return False

    target_enemy = next(
        (
            enemy
            for enemy in floor.enemies
            if enemy.health > 0
            and target_cell in get_enemy_occupied_positions(enemy)
        ),
        None,
    )
    if target_enemy is None:
        return False

    return has_line_of_sight(
        floor.map,
        floor.player_column,
        floor.player_row,
        target_cell[0],
        target_cell[1],
    )

def perform_archer_empowered_shot(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_archer_empowered_shot_target(game_state, target_cell):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    origin = (floor.player_column, floor.player_row)
    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = target_cell
    player.archer_empowered_shot_started_at = 0
    player.archer_empowered_shot_charge = 0
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            positions=(target_cell,),
            data={"kind": "archer_empowered_shot"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=origin,
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(hit_enemy, floor, game_state.combat_log)
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True

def request_archer_leap(game_state: GameState) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_leap_aiming:
        player.archer_leap_aiming = False
        player.archer_leap_target = None
        add_log_message(
            game_state.combat_log,
            "Leap aiming cancelled.",
        )
        return True

    if (
        not player.debug_unlimited_abilities
        and player.archer_leap_charge < ARCHER_LEAP_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Leap is not charged.",
        )
        return True

    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    player.archer_leap_aiming = True
    player.archer_leap_target = None
    add_log_message(
        game_state.combat_log,
        "Choose a visible cell for Leap.",
    )
    return True

def cancel_archer_leap(game_state: GameState) -> None:
    game_state.player.archer_leap_aiming = False
    game_state.player.archer_leap_target = None
    add_log_message(
        game_state.combat_log,
        "Leap aiming cancelled.",
    )

def is_valid_archer_leap_target(
    game_state: GameState,
    column: int,
    row: int,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer" or not player.archer_leap_aiming:
        return False
    if not (0 <= row < len(floor.map)):
        return False
    if not (0 <= column < len(floor.map[0])):
        return False
    if floor.map[row][column] in ("#", "C"):
        return False

    origin = (floor.player_column, floor.player_row)
    if (column, row) == origin:
        return False
    if (
        abs(column - origin[0]) + abs(row - origin[1])
        > ARCHER_LEAP_RANGE
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
        and (column, row) in get_enemy_occupied_positions(enemy)
        for enemy in floor.enemies
    ):
        return False
    if any(
        not chest.is_open
        and (column, row) == (chest.column, chest.row)
        for chest in floor.chests
    ):
        return False
    return True


from acts.act_three.abilities.archer_barrage_zone import (
    cancel_archer_barrage_zone,
    get_archer_barrage_zone_cells,
    is_valid_archer_barrage_zone_anchor,
    place_archer_barrage_zone,
    request_archer_barrage_zone,
    resolve_archer_barrage_zone_entry,
    select_archer_barrage_zone_direction,
    update_archer_barrage_zone_preview,
)
