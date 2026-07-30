from collections.abc import Callable

from game.combat_log import add_log_message
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    ArcherBarrageShotState,
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
    ARCHER_EMPOWERED_SHOT_CHARGES,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
    ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
    ARCHER_BARRAGE_ZONE_CHARGES,
    ARCHER_BARRAGE_ZONE_SIZE,
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

    if player.archer_empowered_shot_charge < ARCHER_EMPOWERED_SHOT_CHARGES:
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

    if player.archer_leap_charge < ARCHER_LEAP_CHARGES:
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

def get_archer_barrage_zone_cells(
    game_state: GameState,
    anchor: tuple[int, int],
) -> list[tuple[int, int]]:
    dungeon_map = game_state.floor.map
    start_column = anchor[0] - 2
    start_row = anchor[1] - 2
    cells = []

    for row in range(
        start_row,
        start_row + ARCHER_BARRAGE_ZONE_SIZE,
    ):
        for column in range(
            start_column,
            start_column + ARCHER_BARRAGE_ZONE_SIZE,
        ):
            if not (
                0 <= row < len(dungeon_map)
                and 0 <= column < len(dungeon_map[0])
            ):
                continue
            if can_move_to(dungeon_map, column, row):
                cells.append((column, row))

    return cells

def is_valid_archer_barrage_zone_anchor(
    game_state: GameState,
    anchor: tuple[int, int],
) -> bool:
    player = game_state.player
    dungeon_map = game_state.floor.map
    column, row = anchor
    return (
        player.subclass == "archer"
        and player.archer_barrage_zone_aiming
        and 0 <= row < len(dungeon_map)
        and 0 <= column < len(dungeon_map[0])
        and can_move_to(dungeon_map, column, row)
    )

def request_archer_barrage_zone(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "archer":
        return False

    if player.archer_barrage_zone_aiming:
        cancel_archer_barrage_zone(game_state)
        return True

    if (
        player.archer_barrage_zone_charge
        < ARCHER_BARRAGE_ZONE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Barrage Zone is not charged.",
        )
        return True

    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = True
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose an area for Barrage Zone.",
    )
    return True

def cancel_archer_barrage_zone(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Barrage Zone aiming cancelled.",
    )

def update_archer_barrage_zone_preview(
    game_state: GameState,
    anchor: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    if (
        anchor is None
        or not is_valid_archer_barrage_zone_anchor(
            game_state,
            anchor,
        )
    ):
        player.archer_barrage_zone_anchor = None
        player.archer_barrage_zone_preview_cells.clear()
        return False

    player.archer_barrage_zone_anchor = anchor
    player.archer_barrage_zone_preview_cells = (
        get_archer_barrage_zone_cells(
            game_state,
            anchor,
        )
    )
    return bool(player.archer_barrage_zone_preview_cells)

def place_archer_barrage_zone(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if (
        not player.archer_barrage_zone_aiming
        or player.archer_barrage_zone_anchor is None
        or not player.archer_barrage_zone_preview_cells
    ):
        return False

    player.archer_barrage_zone_cells = list(
        dict.fromkeys(
            (
                *player.archer_barrage_zone_cells,
                *player.archer_barrage_zone_preview_cells,
            )
        )
    )
    player.archer_barrage_zone_charge = 0
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Barrage Zone is deployed.",
    )
    return True

def _archer_barrage_visual_origin(
    game_state: GameState,
    enemy: EnemyState,
) -> tuple[int, int]:
    floor = game_state.floor
    blocked_positions = {
        position
        for living_enemy in floor.enemies
        if living_enemy.health > 0
        for position in get_enemy_occupied_positions(
            living_enemy
        )
    }
    candidates = []
    for column_change, row_change in (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ):
        column = enemy.column + column_change
        row = enemy.row + row_change
        if not (
            0 <= row < len(floor.map)
            and 0 <= column < len(floor.map[0])
            and can_move_to(floor.map, column, row)
            and (column, row) not in blocked_positions
        ):
            continue
        candidates.append((column, row))

    if not candidates:
        return (
            floor.player_column,
            floor.player_row,
        )

    return min(
        candidates,
        key=lambda position: (
            abs(position[0] - floor.player_column)
            + abs(position[1] - floor.player_row)
        ),
    )

def resolve_archer_barrage_zone_entry(
    game_state: GameState,
    enemy: EnemyState,
    previous_position: tuple[int, int],
) -> bool:
    player = game_state.player
    zone_cells = set(player.archer_barrage_zone_cells)
    if (
        player.subclass != "archer"
        or not zone_cells
        or enemy.health <= 0
    ):
        return False

    current_cells = get_enemy_occupied_positions(enemy)
    if (
        previous_position == (enemy.column, enemy.row)
        or not current_cells & zone_cells
    ):
        return False

    triggered_cells = current_cells & zone_cells
    player.archer_barrage_zone_cells = [
        cell
        for cell in player.archer_barrage_zone_cells
        if cell not in triggered_cells
    ]

    shot_origin = _archer_barrage_visual_origin(
        game_state,
        enemy,
    )
    shot_target = (
        enemy.column,
        enemy.row,
    )
    player.archer_barrage_shots.append(
        ArcherBarrageShotState(
            origin=shot_origin,
            target=shot_target,
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            target=enemy.name,
            origin=shot_origin,
            positions=(shot_target,),
            data={"kind": "archer_barrage_zone"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Barrage Zone fires at {enemy.name}.",
    )
    previous_health = enemy.health
    enemy_was_defeated = attack_enemy(
        game_state,
        enemy,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MIN,
        ARCHER_EMPOWERED_SHOT_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=shot_origin,
        grant_ability_charge=False,
    )
    dealt_damage = enemy.health < previous_health

    if enemy.type == "oracle":
        from bosses.oracle import resolve_oracle_hit_reaction

        resolve_oracle_hit_reaction(
            enemy,
            game_state.floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, enemy)

    return dealt_damage
