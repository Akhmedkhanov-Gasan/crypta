import random

import pygame

from acts.act_three.abilities.summoner_runes import familiar_recharge_requirement
from acts.act_three.combat.creature_attacks import damage_enemy_from_creature
from acts.act_three.rune_master.definitions import POSSESSION_ELITE_TURNS, POSSESSION_RANGE, POSSESSION_TURNS
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState
from logic import (
    can_player_move_between, get_enemy_attack_mode, get_enemy_attack_targets,
    get_enemy_occupied_positions, has_line_of_sight, move_enemy_toward_position,
)


def possession_targets(game_state):
    floor = game_state.floor
    origin = floor.player_column, floor.player_row
    return tuple(cell for enemy in floor.enemies
                 if enemy.health > 0 and not enemy.possessed_by_summoner
                 and enemy.type not in ("warden", "oracle", "oracle_pillar", "lantern_warden")
                 for cell in get_enemy_occupied_positions(enemy)
                 if max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= POSSESSION_RANGE
                 and cell in floor.visible_cells and has_line_of_sight(floor.map, *origin, *cell, floor.barriers))


def possession_host(game_state):
    name = game_state.player.act_three.summoner_possession_host
    return next((enemy for enemy in game_state.floor.enemies if enemy.name == name and enemy.health > 0
                 and enemy.possessed_by_summoner), None)


def sync_host(game_state, host):
    player = game_state.player
    player.summoner_familiar_position = host.column, host.row
    player.summoner_familiar_health = host.health
    player.summoner_familiar_max_health = host.max_health


def possess_enemy(game_state, target, now):
    from acts.act_three.abilities.progression import is_ability_slot_unlocked
    from acts.act_three.settings import SUMMONER_TRUE_FORM_CHARGES

    player = game_state.player
    if target not in possession_targets(game_state):
        return False
    if not player.debug_unlimited_abilities and player.summoner_familiar_charge < familiar_recharge_requirement(player):
        return False
    host = next(enemy for enemy in game_state.floor.enemies if target in get_enemy_occupied_positions(enemy) and enemy.health > 0)
    host.possessed_by_summoner = True
    host.madness_turns = 0
    host.attack_targets.clear()
    host.prepared_attack_mode = None
    host.attack_windup_turns_remaining = 0
    host.heal_target = None
    host.behavior_state = EnemyBehaviorState.IDLE
    player.act_three.summoner_possession_host = host.name
    elite = host.is_elite or host.type in ("brute", "sentinel")
    player.act_three.summoner_possession_turns = POSSESSION_ELITE_TURNS if elite else POSSESSION_TURNS
    player.act_three.summoner_familiar_mode = "possession"
    player.act_three.summoner_entity_floor = game_state.floor_index
    player.act_three.summoner_rune_started_at = now
    player.act_three.summoner_recall_requirement = 0
    player.summoner_familiar_active = True
    player.summoner_familiar_skip_turn = True
    player.summoner_familiar_charge = 0
    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    player.summoner_familiar_summoned_at = now
    player.summoner_true_form_charge = SUMMONER_TRUE_FORM_CHARGES if is_ability_slot_unlocked(player, "f") else 0
    sync_host(game_state, host)
    add_log_message(game_state.combat_log, f"The familiar possesses {host.name} for {player.act_three.summoner_possession_turns} actions.", category="rune")
    return True


def release_host(game_state):
    player = game_state.player
    host = possession_host(game_state)
    if host is not None:
        host.possessed_by_summoner = False
        host.attack_targets.clear()
        host.prepared_attack_mode = None
        host.attack_windup_turns_remaining = 0
        host.behavior_state = EnemyBehaviorState.CHASING
        host.is_aggro = True
        host.stun_turns = max(1, host.stun_turns)
        sync_host(game_state, host)
    player.act_three.summoner_possession_host = None
    player.act_three.summoner_possession_turns = 0


def host_defeated(game_state, enemy):
    player = game_state.player
    if player.act_three.summoner_possession_host != enemy.name:
        return
    from acts.act_three.abilities.summoner import damage_summoner_familiar

    enemy.possessed_by_summoner = False
    player.act_three.summoner_possession_host = None
    player.act_three.summoner_possession_turns = 0
    player.summoner_familiar_position = enemy.column, enemy.row
    player.summoner_familiar_health = 1
    damage_summoner_familiar(game_state, 1)


def damage_host(game_state, damage):
    from systems.player_combat import resolve_enemy_defeat

    host = possession_host(game_state)
    if host is None:
        return 0
    dealt = min(host.health, max(0, damage))
    host.health -= dealt
    sync_host(game_state, host)
    if host.health <= 0:
        host.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(GameEvent(type=GameEventType.DEATH, actor=host.name,
                                  destination=(host.column, host.row), data={"enemy_type": host.type, "cause": "possession"}))
        resolve_enemy_defeat(game_state, host)
    return dealt


def take_possession_turn(game_state):
    from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES

    player, floor = game_state.player, game_state.floor
    host = possession_host(game_state)
    if host is None:
        return
    sync_host(game_state, host)
    player.act_three.summoner_possession_turns -= 1
    candidates = [enemy for enemy in floor.enemies if enemy.health > 0 and not enemy.possessed_by_summoner]
    target = min(candidates, key=lambda enemy: max(abs(enemy.column - host.column), abs(enemy.row - host.row)), default=None)
    now = player.familiar_turn_started_at
    host.heal_cooldown = max(0, host.heal_cooldown - 1)
    if host.stun_turns > 0:
        host.stun_turns -= 1
        target = None
    elif (host.type in ("priest", "priest_ghost") and host.heal_amount > 0 and host.heal_cooldown <= 0
          and player.health < player.max_health
          and abs(host.column - floor.player_column) + abs(host.row - floor.player_row) <= host.heal_range
          and has_line_of_sight(floor.map, host.column, host.row, floor.player_column, floor.player_row, floor.barriers)):
        from game.healing import heal_player

        healed = heal_player(player, host.heal_amount)
        host.heal_cooldown = host.heal_cooldown_duration
        host.attack_animation_started_at = now
        host.attack_effect_mode = "heal"
        game_state.emit(GameEvent(type=GameEventType.HEAL, actor=host.name, target="hero",
                                  origin=(host.column, host.row), destination=(floor.player_column, floor.player_row), amount=healed))
        target = None
    if target is not None and host.stun_turns <= 0:
        blocked = {(chest.column, chest.row) for chest in floor.chests if not chest.is_open}
        cells = get_enemy_attack_targets(floor.map, host, target.column, target.row, blocked)
        cells = tuple(cell for cell in cells if has_line_of_sight(floor.map, host.column, host.row, *cell, floor.barriers))
        if get_enemy_occupied_positions(target).intersection(cells):
            mode = get_enemy_attack_mode(host, target.column, target.row)
            values, weights = host.damage_by_mode.get(mode, next(iter(host.damage_by_mode.values()), ((1,), (1,))))
            host.attack_animation_started_at = now
            host.attack_effect_mode = mode
            host.attack_effect_positions = cells
            for victim in tuple(candidates):
                if victim.health > 0 and get_enemy_occupied_positions(victim).intersection(cells):
                    damage_enemy_from_creature(game_state, host, victim, random.choices(values, weights=weights, k=1)[0], "summoner_possession")
        elif not host.is_immobile:
            occupied = {(floor.player_column, floor.player_row)}
            occupied.update(cell for enemy in floor.enemies if enemy is not host and enemy.health > 0 for cell in get_enemy_occupied_positions(enemy))
            occupied.update(blocked)
            origin = host.column, host.row
            destination = move_enemy_toward_position(floor.map, host, target.column, target.row, occupied)
            if destination != origin and can_player_move_between(floor.map, *origin, *destination, floor.barriers):
                host.column, host.row = destination
                host.movement_origin = origin
                host.movement_animation_started_at = now
                game_state.emit(GameEvent(type=GameEventType.MOVE, actor=host.name, origin=origin,
                                          destination=destination, data={"kind": "summoner_possession"}))
    sync_host(game_state, host)
    if player.act_three.summoner_possession_turns <= 0:
        release_host(game_state)
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
        add_log_message(game_state.combat_log, "The familiar releases its host and returns.", category="rune")
