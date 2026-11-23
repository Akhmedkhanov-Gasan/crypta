import pygame

from acts.act_three.abilities.progression import is_ability_slot_unlocked
from acts.act_three.combat.stun import apply_act_three_enemy_stun
from acts.act_three.rune_master.definitions import FERVENT_CRUSADE_HITS, SANCTUARY_HEAL_RATIO, equipped_rune
from acts.act_three.settings import (
    PALADIN_SACRED_GROUND_CHARGES, PALADIN_SACRED_GROUND_DAMAGE_MAX,
    PALADIN_SACRED_GROUND_DAMAGE_MIN, PALADIN_SACRED_GROUND_IMPACT_MS,
    PALADIN_SACRED_GROUND_RADIUS, PALADIN_SACRED_GROUND_HITS, PALADIN_SACRED_GROUND_CAST_MS,
)
from acts.act_three.state import PaladinSacredLightningState
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.healing import heal_player
from logic import can_move_to, get_enemy_occupied_positions
from systems.player_combat import attack_enemy, resolve_enemy_defeat


def get_paladin_sacred_ground_cells(game_state, anchor):
    floor = game_state.floor
    return [(column, row)
            for row in range(anchor[1] - PALADIN_SACRED_GROUND_RADIUS, anchor[1] + PALADIN_SACRED_GROUND_RADIUS + 1)
            for column in range(anchor[0] - PALADIN_SACRED_GROUND_RADIUS, anchor[0] + PALADIN_SACRED_GROUND_RADIUS + 1)
            if 0 <= row < len(floor.map) and 0 <= column < len(floor.map[0])
            and can_move_to(floor.map, column, row)]


def request_paladin_sacred_ground(game_state, current_time):
    player = game_state.player
    if (player.subclass != "paladin" or not is_ability_slot_unlocked(player, "f")
            or player.paladin_sacred_ground_cast_requested
            or paladin_sacred_ground_cast_active(player, current_time)):
        return False
    if not player.debug_unlimited_abilities and player.paladin_sacred_ground_charge < PALADIN_SACRED_GROUND_CHARGES:
        add_log_message(game_state.combat_log, "Sacred Ground is not charged.")
        return False
    rune = equipped_rune(player, "f")
    player.act_three.paladin_ultimate_rune = rune.id if rune else None
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    player.paladin_sacred_ground_cast_requested = True
    player.paladin_sacred_ground_started_at = current_time
    add_log_message(game_state.combat_log, "The paladin raises his blade.")
    return True


def paladin_sacred_ground_cast_active(player, current_time):
    started_at = player.paladin_sacred_ground_started_at
    return (player.subclass == "paladin" and started_at > 0
            and 0 <= current_time - started_at < PALADIN_SACRED_GROUND_CAST_MS)


def paladin_sacred_ground_impact_ready(game_state, current_time):
    player = game_state.player
    return (player.subclass == "paladin" and player.paladin_sacred_ground_cast_requested
            and player.paladin_sacred_ground_started_at > 0
            and current_time - player.paladin_sacred_ground_started_at >= PALADIN_SACRED_GROUND_IMPACT_MS)


def perform_paladin_sacred_ground(game_state, current_time):
    if not paladin_sacred_ground_impact_ready(game_state, current_time):
        return False
    player, floor = game_state.player, game_state.floor
    player.paladin_sacred_ground_charge = 0
    player.paladin_sacred_ground_cast_requested = False
    player.paladin_sacred_ground_turns = 0
    player.paladin_sacred_ground_lightnings.clear()
    player.act_three.paladin_sanctuary_healing_progress = 0.0
    player.paladin_sacred_ground_cells.clear()
    player.paladin_sacred_ground_anchor = None
    player.act_three.paladin_sacred_ground_floor = game_state.floor_index
    if player.act_three.paladin_ultimate_rune == "rune_of_fervent_crusade":
        player.act_three.paladin_crusade_hits = FERVENT_CRUSADE_HITS
        player.paladin_sacred_ground_hits = 0
        add_log_message(game_state.combat_log, f"Fervent Crusade empowers {FERVENT_CRUSADE_HITS} hits. Guard and evasion are forsaken.", category="rune")
        return True
    player.act_three.paladin_crusade_hits = 0
    anchor = floor.player_column, floor.player_row
    player.paladin_sacred_ground_anchor = anchor
    player.paladin_sacred_ground_cells = get_paladin_sacred_ground_cells(game_state, anchor)
    player.paladin_sacred_ground_hits = PALADIN_SACRED_GROUND_HITS
    add_log_message(game_state.combat_log, f"Sacred Ground has {player.paladin_sacred_ground_hits} damaging hits remaining.", category="ability")
    resolve_paladin_sacred_ground(game_state)
    return True


def resolve_paladin_sacred_ground(game_state):
    player = game_state.player
    zone_cells = set(player.paladin_sacred_ground_cells)
    if (player.subclass != "paladin" or player.paladin_sacred_ground_hits <= 0 or not zone_cells
            or player.act_three.paladin_sacred_ground_floor not in (None, game_state.floor_index)):
        return 0
    enemies_hit = 0
    now = pygame.time.get_ticks()
    sanctuary = player.act_three.paladin_ultimate_rune == "rune_of_redeeming_sanctuary"
    for enemy in tuple(game_state.floor.enemies):
        if player.paladin_sacred_ground_hits <= 0:
            break
        if enemy.health <= 0 or not get_enemy_occupied_positions(enemy).intersection(zone_cells):
            continue
        health = enemy.health
        target = enemy.column, enemy.row
        game_state.emit(GameEvent(type=GameEventType.ATTACK, actor="hero", target=enemy.name,
                                  origin=player.paladin_sacred_ground_anchor, destination=target,
                                  positions=(target,), data={"kind": "paladin_sacred_ground"}))
        defeated = attack_enemy(game_state, enemy, PALADIN_SACRED_GROUND_DAMAGE_MIN,
                                PALADIN_SACRED_GROUND_DAMAGE_MAX, player.crit_chance,
                                attacker_position=player.paladin_sacred_ground_anchor, grant_ability_charge=False)
        if enemy.health < health:
            enemies_hit += 1
            player.paladin_sacred_ground_hits -= 1
            player.paladin_sacred_ground_lightnings.append(PaladinSacredLightningState(target=target))
            if sanctuary:
                if not defeated:
                    apply_act_three_enemy_stun(game_state, enemy, 1, now)
                player.act_three.paladin_sanctuary_healing_progress += player.max_health * SANCTUARY_HEAL_RATIO
                healing = int(player.act_three.paladin_sanctuary_healing_progress + 1e-9)
                player.act_three.paladin_sanctuary_healing_progress -= healing
                healed = heal_player(player, healing)
                if healed:
                    game_state.emit(GameEvent(type=GameEventType.HEAL, actor="hero", target="hero", amount=healed,
                                              destination=(game_state.floor.player_column, game_state.floor.player_row),
                                              data={"kind": "rune_of_redeeming_sanctuary"}))
        if enemy.type == "oracle":
            from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

            resolve_oracle_hit_reaction(enemy, game_state.floor, game_state.combat_log)
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
    if player.paladin_sacred_ground_hits == 0:
        player.paladin_sacred_ground_cells.clear()
        player.paladin_sacred_ground_anchor = None
        add_log_message(game_state.combat_log, "The corrupted ground is exhausted.", category="ability")
    return enemies_hit
