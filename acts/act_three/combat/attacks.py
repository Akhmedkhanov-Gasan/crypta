from collections.abc import Callable
from math import ceil

import pygame

from acts.crates import break_crate
from acts.act_three.events import GameEvent, GameEventType
from game.state import (
    EnemyState,
    FloorState,
    GameState,
)
from logic import (
    direction_toward,
    get_enemy_occupied_positions,
    has_line_of_sight,
)
from acts.act_three.settings import (
    ARCHER_BASIC_ATTACK_RANGE,
    ARCHER_BASIC_DAMAGE_MAX,
    ARCHER_BASIC_DAMAGE_MIN,
    WARLOCK_BASIC_ATTACK_RANGE,
    WARLOCK_BASIC_DAMAGE_MAX,
    WARLOCK_BASIC_DAMAGE_MIN,
    SUMMONER_ATTACK_RANGE,
    SUMMONER_ATTACK_RANGE_WITH_FAMILIAR,
)


OracleHitReaction = Callable[
    [EnemyState, FloorState, list[str]],
    None,
]


def attack_breakable_environment_object(game_state, crate, started_at):
    if crate is None or not break_crate(game_state, crate):
        return False
    player = game_state.player
    floor = game_state.floor
    origin = (floor.player_column, floor.player_row)
    target = (crate.column, crate.row)
    player.attack_animation_started_at = started_at
    player.act_three.environment_attack = (started_at, game_state.floor_index, origin, target)
    game_state.player_attack_targets = [target]
    return True


def _enemy_at(floor, target):
    return next(
        (enemy for enemy in floor.enemies
         if enemy.health > 0 and not enemy.possessed_by_summoner and target in get_enemy_occupied_positions(enemy)),
        None,
    )


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

    if _enemy_at(floor, target_cell) is None:
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

    if _enemy_at(floor, target_cell) is None:
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

    from acts.act_three.abilities.warlock_runes import prepare_demon_attack

    if not prepare_demon_attack(game_state):
        return False
    player = game_state.player
    floor = game_state.floor
    player.facing_direction = direction_toward(
        floor.player_column,
        floor.player_row,
        target_cell[0],
        target_cell[1],
    )
    hit_enemy = _enemy_at(floor, target_cell)
    started_at = pygame.time.get_ticks()
    if floor.presentation_act == 3:
        player.act_three.environment_attack = None
        player.attack_animation_started_at = started_at
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
        game_state, hit_enemy, WARLOCK_BASIC_DAMAGE_MIN, WARLOCK_BASIC_DAMAGE_MAX,
        player.crit_chance, attacker_position=(floor.player_column, floor.player_row),
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
    hit_enemy = _enemy_at(floor, target_cell)
    started_at = pygame.time.get_ticks()
    from acts.act_three.abilities.mirror_actions import queue_mirror_action

    queue_mirror_action(game_state, "basic", target_cell, started_at)
    player.act_three.environment_attack = None
    player.attack_animation_started_at = started_at
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

    if _enemy_at(floor, target_cell) is None:
        return False

    if origin is None:
        origin = (floor.player_column, floor.player_row)

    from acts.act_three.abilities.summoner_runes import absorption_active
    from acts.act_three.rune_master.definitions import ABSORPTION_ATTACK_RANGE

    attack_range = (
        SUMMONER_ATTACK_RANGE_WITH_FAMILIAR
        if player.summoner_familiar_active
        else SUMMONER_ATTACK_RANGE
    )
    if absorption_active(player):
        attack_range = ABSORPTION_ATTACK_RANGE
    distance = max(
        abs(target_cell[0] - origin[0]),
        abs(target_cell[1] - origin[1]),
    )
    return (
        0 < distance <= attack_range
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

    from acts.act_three.abilities.summoner_runes import begin_summoner_attack, finish_summoner_attack

    begin_summoner_attack(game_state)
    player = game_state.player
    floor = game_state.floor
    player.facing_direction = direction_toward(
        floor.player_column,
        floor.player_row,
        target_cell[0],
        target_cell[1],
    )
    hit_enemy = _enemy_at(floor, target_cell)
    started_at = pygame.time.get_ticks()
    player.act_three.environment_attack = None
    player.attack_animation_started_at = started_at
    game_state.player_attack_targets = [target_cell]
    game_state.emit(
        GameEvent(
            type=GameEventType.ATTACK,
            actor="hero",
            origin=(floor.player_column, floor.player_row),
            positions=(target_cell,),
            data={
                "kind": (
                    "summoner_magic"
                    if player.summoner_familiar_active or player.act_three.summoner_absorption_attack_active
                    else "summoner_bird"
                )
            },
        )
    )
    enemy_was_defeated = attack_enemy(
        game_state,
        hit_enemy,
        player.damage_min,
        player.damage_max,
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
    finish_summoner_attack(game_state)
    return True
