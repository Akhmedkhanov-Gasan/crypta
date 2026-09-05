from collections.abc import Callable
from math import ceil

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
from settings import (
    ARCHER_BASIC_ATTACK_RANGE,
    ARCHER_BASIC_DAMAGE_MAX,
    ARCHER_BASIC_DAMAGE_MIN,
    WARLOCK_BASIC_ATTACK_RANGE,
    WARLOCK_BASIC_DAMAGE_MAX,
    WARLOCK_BASIC_DAMAGE_MIN,
    WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER,
    SUMMONER_ATTACK_RANGE,
    SUMMONER_ATTACK_RANGE_WITH_FAMILIAR,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


def navigation_attack(game_state, target, *, origin=None):
    attacks = {
        "archer": (
            "archer_attack_target",
            is_valid_archer_attack_target,
        ),
        "warlock": (
            "warlock_attack_target",
            is_valid_warlock_attack_target,
        ),
        "summoner": (
            "summoner_attack_target",
            is_valid_summoner_attack_target,
        ),
    }
    attack = attacks.get(game_state.player.subclass)
    if attack is None:
        return None

    field, validator = attack
    return field, validator(game_state, target, origin=origin)

def attack_enemy(*args, **kwargs):
    from systems.player_combat import attack_enemy as service

    return service(*args, **kwargs)


def resolve_enemy_defeat(*args, **kwargs):
    from systems.player_combat import (
        resolve_enemy_defeat as service,
    )

    return service(*args, **kwargs)

def is_valid_archer_attack_target(
    game_state: GameState,
    target_cell: tuple[int, int],
    *,
    origin=None,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "archer":
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

    if origin is None:
        origin = (floor.player_column, floor.player_row)

    distance = abs(target_cell[0] - origin[0]) + abs(
        target_cell[1] - origin[1]
    )
    return (
        distance <= ARCHER_BASIC_ATTACK_RANGE
        and has_line_of_sight(
            floor.map,
            *origin,
            *target_cell,
        )
    )

def is_valid_warlock_attack_target(
    game_state: GameState,
    target_cell: tuple[int, int],
    *,
    origin=None,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "warlock":
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

    if origin is None:
        origin = (floor.player_column, floor.player_row)

    distance = abs(target_cell[0] - origin[0]) + abs(
        target_cell[1] - origin[1]
    )
    return (
        distance <= WARLOCK_BASIC_ATTACK_RANGE
        and has_line_of_sight(
            floor.map,
            *origin,
            *target_cell,
        )
    )

def perform_warlock_attack(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_warlock_attack_target(
        game_state,
        target_cell,
    ):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(
                floor.player_column,
                floor.player_row,
            ),
            positions=(target_cell,),
            data={"kind": "warlock_orb"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ceil(
            WARLOCK_BASIC_DAMAGE_MIN
            * (
                WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER
                if player.warlock_demon_form_active
                else 1
            )
        ),
        ceil(
            WARLOCK_BASIC_DAMAGE_MAX
            * (
                WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER
                if player.warlock_demon_form_active
                else 1
            )
        ),
        player.crit_chance,
        attacker_position=(
            floor.player_column,
            floor.player_row,
        ),
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(
            hit_enemy,
            floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True

def perform_archer_attack(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_archer_attack_target(game_state, target_cell):
        return False

    player = game_state.player
    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=(target_cell,),
            data={"kind": "archer_basic"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        ARCHER_BASIC_DAMAGE_MIN,
        ARCHER_BASIC_DAMAGE_MAX,
        player.crit_chance,
        attacker_position=(floor.player_column, floor.player_row),
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(
            hit_enemy,
            floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True

def is_valid_summoner_attack_target(
    game_state: GameState,
    target_cell: tuple[int, int],
    *,
    origin=None,
) -> bool:
    player = game_state.player
    floor = game_state.floor
    if player.subclass != "summoner":
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

    attack_range = (
        SUMMONER_ATTACK_RANGE_WITH_FAMILIAR
        if player.summoner_familiar_active
        else SUMMONER_ATTACK_RANGE
    )
    if origin is None:
        origin = (floor.player_column, floor.player_row)

    distance = max(
        abs(target_cell[0] - origin[0]),
        abs(target_cell[1] - origin[1]),
    )
    return (
        distance <= attack_range
        and has_line_of_sight(
            floor.map,
            *origin,
            *target_cell,
        )
    )

def perform_summoner_attack(
    game_state: GameState,
    target_cell: tuple[int, int],
    oracle_hit_reaction: OracleHitReaction,
) -> bool:
    if not is_valid_summoner_attack_target(game_state, target_cell):
        return False

    floor = game_state.floor
    hit_enemy = next(
        enemy
        for enemy in floor.enemies
        if enemy.health > 0
        and target_cell in get_enemy_occupied_positions(enemy)
    )
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=(target_cell,),
            data={"kind": "summoner_magic"},
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        game_state.player.damage_min,
        game_state.player.damage_max,
        game_state.player.crit_chance,
        attacker_position=(floor.player_column, floor.player_row),
    )
    if hit_enemy.type == "oracle":
        oracle_hit_reaction(
            hit_enemy,
            floor,
            game_state.combat_log,
        )
    if enemy_was_defeated:
        resolve_enemy_defeat(game_state, hit_enemy)
    return True
