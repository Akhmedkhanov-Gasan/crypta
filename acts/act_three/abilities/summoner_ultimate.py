from math import ceil

import pygame

from acts.act_three.abilities.summoner_runes import nearest_summon_cell, summon_cell_is_free
from acts.act_three.rune_master.definitions import ABSORPTION_ATTACKS, CATACLYSM_DAMAGE_MULTIPLIER, CATACLYSM_RADIUS, equipped_rune
from acts.act_three.settings import SUMMONER_FAMILIAR_CHARGES, SUMMONER_TRUE_FORM_CHARGES, SUMMONER_TRUE_FORM_DAMAGE_BONUS, SUMMONER_TRUE_FORM_HEALTH_BONUS
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions, has_line_of_sight


def _snapshot(player, floor_index):
    return {"mode": player.act_three.summoner_familiar_mode,
            "position": player.summoner_familiar_position,
            "health": player.summoner_familiar_health,
            "max_health": player.summoner_familiar_max_health,
            "anchor": player.act_three.summoner_totem_anchor, "floor": floor_index}


def restore_familiar(game_state):
    player = game_state.player
    saved = player.act_three.summoner_suspended_familiar
    if saved is None:
        return
    player.act_three.summoner_suspended_familiar = None
    player.act_three.summoner_absorption_attack_active = False
    player.act_three.summoner_absorption_attacks = 0
    player.summoner_true_form_active = False
    player.summoner_true_form_charge = 0
    player.summoner_true_form_started_at = -1
    player.summoner_true_form_ending_started_at = pygame.time.get_ticks()
    player.summoner_true_form_base_max_health = 0
    player.act_three.summoner_entity_floor = game_state.floor_index
    mode = saved["mode"]
    player.act_three.summoner_familiar_mode = mode
    player.summoner_familiar_max_health = saved["max_health"]
    player.summoner_familiar_health = max(1, min(saved["max_health"], saved["health"]))
    if mode == "possession":
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
    else:
        origin = (saved["anchor"] or saved["position"]) if mode == "totem" else (game_state.floor.player_column, game_state.floor.player_row)
        if saved.get("floor", game_state.floor_index) != game_state.floor_index:
            origin = game_state.floor.player_column, game_state.floor.player_row
        position = origin if summon_cell_is_free(game_state, origin) else nearest_summon_cell(game_state, origin)
        player.summoner_familiar_position = position
        player.summoner_familiar_active = position is not None
        player.summoner_familiar_skip_turn = True
        player.summoner_familiar_movement_origin = None
        player.summoner_familiar_summoned_at = pygame.time.get_ticks()
        if mode == "totem":
            player.act_three.summoner_totem_anchor = position
        if position is None:
            player.summoner_familiar_charge = SUMMONER_FAMILIAR_CHARGES
    add_log_message(game_state.combat_log, "The familiar returns from its unleashed power.", category="ability")


def end_true_form(game_state):
    player = game_state.player
    saved = player.act_three.summoner_suspended_familiar
    if saved is not None:
        saved["health"] = min(saved["max_health"], player.summoner_familiar_health)
    restore_familiar(game_state)


def activate_summoner_ultimate(game_state, now):
    from acts.act_three.abilities.summoner_possession import release_host

    player = game_state.player
    if player.act_three.summoner_absorption_attacks > 0:
        return False
    if not player.summoner_familiar_active or player.summoner_familiar_health <= 0:
        add_log_message(game_state.combat_log, "The familiar must be present to unleash its power.")
        return False
    if player.summoner_true_form_active:
        if player.act_three.summoner_ultimate_rune == "rune_of_cataclysm":
            return detonate_familiar(game_state, now)
        end_true_form(game_state)
        return True
    if not player.debug_unlimited_abilities and player.summoner_true_form_charge < SUMMONER_TRUE_FORM_CHARGES:
        add_log_message(game_state.combat_log, "True Form is not fully charged.")
        return False
    rune = equipped_rune(player, "f")
    absorption = rune is not None and rune.id == "rune_of_absorption"
    saved = _snapshot(player, game_state.floor_index)
    position = player.summoner_familiar_position
    if saved["mode"] == "possession" and not absorption:
        position = nearest_summon_cell(game_state, position)
        if position is None:
            add_log_message(game_state.combat_log, "There is no free cell for True Form.", category="warning")
            return False
    player.act_three.summoner_suspended_familiar = saved
    player.act_three.summoner_ultimate_rune = rune.id if rune else None
    player.act_three.summoner_rune_started_at = now
    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    player.summoner_true_form_charge = 0
    if saved["mode"] == "possession":
        release_host(game_state)
    if absorption:
        player.act_three.summoner_absorption_attacks = ABSORPTION_ATTACKS
        player.act_three.summoner_absorption_attack_active = False
        player.summoner_familiar_active = False
        player.summoner_familiar_position = None
        add_log_message(game_state.combat_log, "The familiar merges with its master for six empowered attacks.", category="rune")
        return True
    if saved["mode"] == "possession":
        base = max(1, player.max_health // 2)
        player.summoner_familiar_health = max(1, round(base * saved["health"] / saved["max_health"]))
        player.summoner_familiar_max_health = base
    player.summoner_familiar_position = position
    player.summoner_familiar_active = True
    player.summoner_true_form_active = True
    player.summoner_true_form_started_at = now
    player.summoner_true_form_ending_started_at = -1
    player.summoner_familiar_skip_turn = True
    player.summoner_familiar_movement_origin = None
    player.summoner_true_form_base_max_health = player.summoner_familiar_max_health
    player.summoner_familiar_max_health += SUMMONER_TRUE_FORM_HEALTH_BONUS
    player.summoner_familiar_health += SUMMONER_TRUE_FORM_HEALTH_BONUS
    add_log_message(game_state.combat_log, "True Form awakens. Each attack consumes its own health.", category="ability")
    return True


def detonate_familiar(game_state, now):
    from acts.act_three.abilities.summoner import damage_summoner_familiar
    from systems.player_combat import attack_enemy, damage_player, resolve_enemy_defeat

    player, floor = game_state.player, game_state.floor
    origin = player.summoner_familiar_position
    if not player.summoner_true_form_active or origin is None:
        return False
    own_damage = ceil(((player.damage_min + player.damage_max) / 2 + SUMMONER_TRUE_FORM_DAMAGE_BONUS) * CATACLYSM_DAMAGE_MULTIPLIER)
    for enemy in tuple(floor.enemies):
        if enemy.health <= 0:
            continue
        in_blast = any(max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= CATACLYSM_RADIUS
                       and has_line_of_sight(floor.map, *origin, *cell, floor.barriers)
                       for cell in get_enemy_occupied_positions(enemy))
        if not in_blast:
            continue
        defeated = attack_enemy(game_state, enemy, player.damage_min, player.damage_max, 0,
                                attacker_name="familiar", attacker_position=origin,
                                damage_multiplier=CATACLYSM_DAMAGE_MULTIPLIER, grant_ability_charge=False)
        if enemy.type == "oracle":
            from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

            resolve_oracle_hit_reaction(enemy, floor, game_state.combat_log)
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
    hero = floor.player_column, floor.player_row
    if (max(abs(hero[0] - origin[0]), abs(hero[1] - origin[1])) <= CATACLYSM_RADIUS
            and has_line_of_sight(floor.map, *origin, *hero, floor.barriers)):
        amount = damage_player(game_state, own_damage, "arcane")
        game_state.emit(GameEvent(type=GameEventType.HIT, actor="familiar", target="hero", origin=origin,
                                  destination=hero, amount=amount, data={"kind": "summoner_cataclysm"}))
        if player.health <= 0:
            game_state.emit(GameEvent(type=GameEventType.DEATH, actor="hero", destination=hero,
                                      data={"cause": "summoner_cataclysm"}))
    player.act_three.summoner_cataclysm_position = origin
    player.act_three.summoner_cataclysm_started_at = now
    damage_summoner_familiar(game_state, player.summoner_familiar_health, penalty_multiplier=2)
    add_log_message(game_state.combat_log, "Cataclysm consumes the familiar. Recalling it now requires twelve charges.", category="rune")
    return True
