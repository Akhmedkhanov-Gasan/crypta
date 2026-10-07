from collections.abc import Callable

from game.combat_log import add_log_message
from game.healing import heal_player
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
from acts.act_three.settings import (
    PALADIN_HOLY_HAND_CHARGES,
    PALADIN_HOLY_HAND_HEALING,
    PALADIN_HOLY_SHIELD_CHARGES,
    PALADIN_HOLY_SHIELD_TURNS,
    PALADIN_SHIELD_CHARGE_CHARGES,
    PALADIN_SHIELD_CHARGE_RANGE,
    PALADIN_SHIELD_CHARGE_STUN_TURNS,
)
from systems.player_combat import (
    attack_enemy,
    resolve_enemy_defeat,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]

def request_paladin_holy_hand(
    game_state: GameState,
    current_time: int,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.health >= player.max_health:
        add_log_message(
            game_state.combat_log,
            "Holy Hand is not needed at full health.",
        )
        return True
    if (
        not player.debug_unlimited_abilities
        and player.paladin_holy_hand_charge
        < PALADIN_HOLY_HAND_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Holy Hand is not charged.",
        )
        return True

    healing = heal_player(
        player,
        PALADIN_HOLY_HAND_HEALING,
    )
    player.paladin_holy_hand_charge = 0
    player.paladin_holy_hand_started_at = current_time
    game_state.emit(
        GameEvent(
            type=GameEventType.HEAL,
            actor="hero",
            target="hero",
            destination=(
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
            amount=healing,
            data={"kind": "paladin_holy_hand"},
        )
    )
    add_log_message(
        game_state.combat_log,
        f"Holy Hand restores {healing} health.",
    )
    return True

def request_paladin_holy_shield(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.paladin_holy_shield_turns > 0:
        add_log_message(
            game_state.combat_log,
            "Holy Shield is already active.",
        )
        return True
    if (
        not player.debug_unlimited_abilities
        and player.paladin_holy_shield_charge
        < PALADIN_HOLY_SHIELD_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Holy Shield is not charged.",
        )
        return True

    player.paladin_holy_shield_charge = 0
    player.paladin_holy_shield_turns = (
        PALADIN_HOLY_SHIELD_TURNS
    )
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Holy Shield surrounds the paladin.",
    )
    return True

def advance_paladin_holy_shield(
    game_state: GameState,
) -> None:
    player = game_state.player
    if (
        player.subclass != "paladin"
        or player.paladin_holy_shield_turns <= 0
    ):
        return

    player.paladin_holy_shield_turns -= 1
    if player.paladin_holy_shield_turns == 0:
        add_log_message(
            game_state.combat_log,
            "Holy Shield fades.",
        )

def get_paladin_shield_charge_path(
    game_state: GameState,
    target: tuple[int, int],
) -> list[tuple[int, int]]:
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    target_column, target_row = target
    current_column, current_row = origin
    column_distance = abs(target_column - current_column)
    row_distance = abs(target_row - current_row)
    column_step = 1 if current_column < target_column else -1
    row_step = 1 if current_row < target_row else -1
    error = column_distance - row_distance
    path = []

    while (current_column, current_row) != target:
        doubled_error = error * 2
        if doubled_error > -row_distance:
            error -= row_distance
            current_column += column_step
        if doubled_error < column_distance:
            error += column_distance
            current_row += row_step
        path.append((current_column, current_row))

    return path

def _get_paladin_shield_charge_destination(
    game_state: GameState,
    path: list[tuple[int, int]],
) -> tuple[int, int]:
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    occupied_positions = {
        position
        for enemy in floor.enemies
        if enemy.health > 0
        for position in get_enemy_occupied_positions(enemy)
    }
    if path and path[-1] not in occupied_positions:
        return path[-1]
    for position in reversed(path[:-1]):
        if position not in occupied_positions:
            return position
    return origin

def is_valid_paladin_shield_charge_target(
    game_state: GameState,
    target: tuple[int, int],
) -> bool:
    player = game_state.player
    floor = game_state.floor
    column, row = target
    origin = (floor.player_column, floor.player_row)
    if (
        player.subclass != "paladin"
        or not player.paladin_shield_charge_aiming
        or target == origin
    ):
        return False
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[0])
        and can_move_to(floor.map, column, row)
    ):
        return False
    if (
        max(
            abs(column - origin[0]),
            abs(row - origin[1]),
        )
        > PALADIN_SHIELD_CHARGE_RANGE
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

    path = get_paladin_shield_charge_path(
        game_state,
        target,
    )
    blocked_by_chest = any(
        not chest.is_open
        and (chest.column, chest.row) in path
        for chest in floor.chests
    )
    return bool(path) and not blocked_by_chest

def request_paladin_shield_charge(
    game_state: GameState,
) -> bool:
    player = game_state.player
    if player.subclass != "paladin":
        return False

    if player.paladin_shield_charge_aiming:
        cancel_paladin_shield_charge(game_state)
        return True
    if (
        not player.debug_unlimited_abilities
        and player.paladin_shield_charge_charge
        < PALADIN_SHIELD_CHARGE_CHARGES
    ):
        add_log_message(
            game_state.combat_log,
            "Shield Charge is not charged.",
        )
        return True

    player.paladin_shield_charge_aiming = True
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Choose a cell or enemy for Shield Charge.",
    )
    return True

def cancel_paladin_shield_charge(
    game_state: GameState,
) -> None:
    player = game_state.player
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    add_log_message(
        game_state.combat_log,
        "Shield Charge aiming cancelled.",
    )

def _paladin_shield_charge_target_in_direction(
    game_state: GameState,
    direction: tuple[int, int],
    maximum_distance: int,
) -> tuple[int, int] | None:
    floor = game_state.floor
    origin = (
        floor.player_column,
        floor.player_row,
    )
    target = None

    for distance in range(
        1,
        min(
            maximum_distance,
            PALADIN_SHIELD_CHARGE_RANGE,
        ) + 1,
    ):
        candidate = (
            origin[0] + direction[0] * distance,
            origin[1] + direction[1] * distance,
        )

        if not is_valid_paladin_shield_charge_target(
            game_state,
            candidate,
        ):
            break

        target = candidate

        if any(
            enemy.health > 0
            and candidate in get_enemy_occupied_positions(enemy)
            for enemy in floor.enemies
        ):
            break

    return target


def _paladin_shield_charge_direction_to_target(
    origin: tuple[int, int],
    target: tuple[int, int],
) -> tuple[int, int]:
    column_difference = target[0] - origin[0]
    row_difference = target[1] - origin[1]

    if column_difference == 0:
        return (
            0,
            1 if row_difference > 0 else -1,
        )

    if row_difference == 0:
        return (
            1 if column_difference > 0 else -1,
            0,
        )

    horizontal_distance = abs(column_difference)
    vertical_distance = abs(row_difference)

    if horizontal_distance > vertical_distance * 2:
        return (
            1 if column_difference > 0 else -1,
            0,
        )

    if vertical_distance > horizontal_distance * 2:
        return (
            0,
            1 if row_difference > 0 else -1,
        )

    return (
        1 if column_difference > 0 else -1,
        1 if row_difference > 0 else -1,
    )


def update_paladin_shield_charge_preview(
    game_state: GameState,
    target: tuple[int, int] | None,
) -> bool:
    player = game_state.player
    floor = game_state.floor

    if target is None:
        player.paladin_shield_charge_target = None
        player.paladin_shield_charge_preview_cells.clear()
        return False

    origin = (
        floor.player_column,
        floor.player_row,
    )
    direction = (
        _paladin_shield_charge_direction_to_target(
            origin,
            target,
        )
    )
    requested_distance = min(
        PALADIN_SHIELD_CHARGE_RANGE,
        max(
            abs(target[0] - origin[0]),
            abs(target[1] - origin[1]),
        ),
    )
    snapped_target = (
        _paladin_shield_charge_target_in_direction(
            game_state,
            direction,
            requested_distance,
        )
    )

    if snapped_target is None:
        player.paladin_shield_charge_target = None
        player.paladin_shield_charge_preview_cells.clear()
        return False

    player.paladin_shield_charge_target = snapped_target
    player.paladin_shield_charge_preview_cells = (
        get_paladin_shield_charge_path(
            game_state,
            snapped_target,
        )
    )
    return True


def select_paladin_shield_charge_direction(
    game_state: GameState,
    direction: tuple[int, int],
) -> bool:
    player = game_state.player

    if (
        not player.paladin_shield_charge_aiming
        or direction == (0, 0)
    ):
        return False

    target = _paladin_shield_charge_target_in_direction(
        game_state,
        direction,
        PALADIN_SHIELD_CHARGE_RANGE,
    )

    if target is None:
        player.paladin_shield_charge_target = None
        player.paladin_shield_charge_preview_cells.clear()
        return False

    player.paladin_shield_charge_target = target
    player.paladin_shield_charge_preview_cells = (
        get_paladin_shield_charge_path(
            game_state,
            target,
        )
    )
    return True


def perform_paladin_shield_charge(
    game_state: GameState,
    current_time: int,
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    target = player.paladin_shield_charge_target
    if (
        target is None
        or not is_valid_paladin_shield_charge_target(
            game_state,
            target,
        )
    ):
        return False

    origin = (floor.player_column, floor.player_row)
    path = get_paladin_shield_charge_path(
        game_state,
        target,
    )
    destination = _get_paladin_shield_charge_destination(
        game_state,
        path,
    )
    movement = (
        target[0] - origin[0],
        target[1] - origin[1],
    )
    player.facing_direction = (
        (
            1 if movement[0] > 0 else -1,
            0,
        )
        if abs(movement[0]) >= abs(movement[1])
        else (
            0,
            1 if movement[1] > 0 else -1,
        )
    )
    enemies_hit = [
        enemy
        for enemy in floor.enemies
        if (
            enemy.health > 0
            and any(
                position in path
                for position in get_enemy_occupied_positions(
                    enemy
                )
            )
        )
    ]

    floor.player_column, floor.player_row = destination
    player.paladin_shield_charge_charge = 0
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    player.paladin_shield_charge_origin = origin
    player.paladin_shield_charge_started_at = current_time
    game_state.emit(
        GameEvent(
            type=GameEventType.MOVE,
            actor="hero",
            origin=origin,
            destination=destination,
            positions=tuple(path),
            data={"kind": "paladin_shield_charge"},
        )
    )
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=origin,
            destination=target,
            positions=tuple(path),
            data={"kind": "paladin_shield_charge"},
        )
    )

    for enemy in enemies_hit:
        enemy_was_defeated = attack_enemy(
            game_state,
            enemy,
            player.damage_min,
            player.damage_max,
            player.crit_chance,
            attacker_position=destination,
            grant_ability_charge=False,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(
                enemy,
                floor,
                game_state.combat_log,
            )
        if enemy_was_defeated:
            resolve_enemy_defeat(game_state, enemy)
            continue

        enemy.stun_turns = max(
            enemy.stun_turns,
            PALADIN_SHIELD_CHARGE_STUN_TURNS,
        )
        enemy.attack_targets = []
        enemy.prepared_attack_mode = None
        enemy.attack_windup_turns_remaining = 0
        enemy.heal_target = None

        game_state.emit(
            GameEvent(
                type=GameEventType.ABILITY,
                actor="hero",
                target=enemy.name,
                origin=origin,
                destination=(
                    enemy.column,
                    enemy.row,
                ),
                data={
                    "kind": "paladin_shield_charge_stun",
                    "turns": (
                        PALADIN_SHIELD_CHARGE_STUN_TURNS
                    ),
                },
            )
        )
        add_log_message(
            game_state.combat_log,
            f"{enemy.name} is stunned by Shield Charge.",
            category="debuff",
        )

    add_log_message(
        game_state.combat_log,
        (
            f"Shield Charge strikes {len(enemies_hit)} target(s)."
            if enemies_hit
            else "The paladin charges across the battlefield."
        ),
    )
    return True
