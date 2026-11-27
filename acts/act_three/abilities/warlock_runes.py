import pygame

from acts.act_three.rune_master.definitions import (
    BLOOD_PACT_COST_INTERVAL, BLOOD_PACT_DAMAGE_CAP, BLOOD_PACT_DAMAGE_STEP,
    BLOOD_PACT_KILL_HEAL_RATIO, DEMON_KILL_HEAL_RATIO, ETERNAL_FORM_DAMAGE_MULTIPLIER,
    MADNESS_ELITE_TURNS, MADNESS_TURNS, SPREADING_CURSE_RANGE, has_ability_rune,
)
from acts.act_three.settings import WARLOCK_CURSE_TURNS, WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER, WARLOCK_DEMON_FORM_HEALTH_DRAIN
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from game.healing import heal_player
from game.state import EnemyBehaviorState
from logic import get_enemy_occupied_positions, has_line_of_sight


def demon_attack_cost(player):
    if player.subclass != "warlock" or not player.warlock_demon_form_active or player.act_three.warlock_eternal_bound:
        return 0
    if player.act_three.warlock_demon_rune == "rune_of_blood_pact":
        return 1 + player.act_three.warlock_blood_attacks // BLOOD_PACT_COST_INTERVAL
    return WARLOCK_DEMON_FORM_HEALTH_DRAIN


def demon_damage_multiplier(player, next_attack=False):
    if player.subclass != "warlock" or not player.warlock_demon_form_active:
        return 1.0
    if player.act_three.warlock_eternal_bound:
        return ETERNAL_FORM_DAMAGE_MULTIPLIER
    if player.act_three.warlock_demon_rune == "rune_of_blood_pact":
        return min(BLOOD_PACT_DAMAGE_CAP, WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER
                   + max(0, player.act_three.warlock_blood_attacks - (0 if next_attack else 1)) * BLOOD_PACT_DAMAGE_STEP)
    return WARLOCK_DEMON_FORM_DAMAGE_MULTIPLIER


def prepare_demon_attack(game_state):
    player = game_state.player
    cost = demon_attack_cost(player)
    if cost and player.health <= cost:
        add_log_message(game_state.combat_log, f"Demon attack needs {cost} HP. Revert with F or heal first.", category="warning")
        return False
    if cost:
        player.health -= cost
        game_state.emit(GameEvent(type=GameEventType.ABILITY, actor="hero", target="hero", amount=cost,
                                  data={"kind": "warlock_demon_hp_cost"}))
    if player.subclass == "warlock" and player.warlock_demon_form_active:
        player.act_three.warlock_blood_attacks += 1
        player.act_three.warlock_last_demon_attack_at = pygame.time.get_ticks()
    return True


def apply_curse_rune(game_state, enemy):
    player = game_state.player
    enemy.spreading_curse = False
    enemy.madness_turns = 0
    if has_ability_rune(player, "rune_of_madness"):
        elite = enemy.is_elite or enemy.type in ("warden", "oracle", "lantern_warden")
        enemy.madness_turns = MADNESS_ELITE_TURNS if elite else MADNESS_TURNS
        enemy.curse_turns = 0
        enemy.attack_targets.clear()
        enemy.prepared_attack_mode = None
        enemy.attack_windup_turns_remaining = 0
        enemy.heal_target = None
        enemy.summon_windup_turns_remaining = 0
        enemy.behavior_state = EnemyBehaviorState.CHASING
        enemy.is_aggro = True
    else:
        enemy.curse_turns = WARLOCK_CURSE_TURNS
        enemy.spreading_curse = has_ability_rune(player, "rune_of_spreading_curse")
        player.act_three.warlock_newly_cursed_enemies.add(enemy.name)


def _spread_curse(game_state, defeated):
    if not defeated.spreading_curse or defeated.curse_turns <= 0:
        return
    floor = game_state.floor
    origin = defeated.column, defeated.row
    candidates = []
    for enemy in floor.enemies:
        if enemy.health <= 0 or enemy.curse_turns > 0 or enemy.madness_turns > 0:
            continue
        for cell in get_enemy_occupied_positions(enemy):
            distance = max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1]))
            if distance <= SPREADING_CURSE_RANGE and has_line_of_sight(floor.map, *origin, *cell, floor.barriers):
                candidates.append((distance, enemy.name, enemy))
    if not candidates:
        return
    target = min(candidates, key=lambda item: item[:2])[2]
    target.curse_turns = defeated.curse_turns
    target.spreading_curse = True
    game_state.player.act_three.warlock_newly_cursed_enemies.add(target.name)
    transfers = game_state.player.act_three.warlock_curse_transfers
    now = pygame.time.get_ticks()
    transfers[:] = [entry for entry in transfers if now - entry[-1] < 900]
    transfers.append((*origin, target.column, target.row, now))
    add_log_message(game_state.combat_log, f"The curse passes to {target.name} for {target.curse_turns} turns.", category="rune")


def resolve_warlock_defeat(game_state, enemy):
    player = game_state.player
    if player.subclass != "warlock":
        return
    _spread_curse(game_state, enemy)
    if enemy.is_summoned or not player.warlock_demon_form_active or player.act_three.warlock_eternal_bound or player.health <= 0:
        return
    ratio = BLOOD_PACT_KILL_HEAL_RATIO if player.act_three.warlock_demon_rune == "rune_of_blood_pact" else DEMON_KILL_HEAL_RATIO
    player.act_three.warlock_demon_healing_progress += player.max_health * ratio
    amount = int(player.act_three.warlock_demon_healing_progress + 1e-9)
    player.act_three.warlock_demon_healing_progress -= amount
    healed = heal_player(player, amount)
    if healed:
        game_state.emit(GameEvent(type=GameEventType.HEAL, actor="hero", target="hero", amount=healed,
                                  data={"kind": "warlock_demon_kill"}))
        add_log_message(game_state.combat_log, f"Demon Form consumes a soul and restores {healed} HP.", category="healing")


def bind_eternal_form(game_state, current_time=None):
    player = game_state.player
    if player.act_three.warlock_eternal_bound:
        return
    was_active = player.warlock_demon_form_active
    player.act_three.warlock_eternal_bound = True
    restore_eternal_form(player)
    if not was_active:
        player.warlock_demon_form_target_active = True
        player.warlock_demon_form_started_at = pygame.time.get_ticks() if current_time is None else current_time
    player.act_three.warlock_blood_attacks = 0
    player.act_three.warlock_demon_healing_progress = 0.0
    player.ability_slot_charges["f"] = 0.0
    player.warlock_curse_aiming = False
    player.warlock_curse_target = None
    game_state.player_attack_targets.clear()


def restore_eternal_form(player):
    if (player.act_three.warlock_eternal_bound or (player.subclass == "warlock"
            and player.act_three.ability_runes.get("f") == "rune_of_eternal_form")):
        player.act_three.warlock_eternal_bound = True
        player.warlock_demon_form_active = True
        player.act_three.warlock_demon_rune = "rune_of_eternal_form"
        player.act_three.ability_runes["f"] = "rune_of_eternal_form"
        if player.warlock_demon_form_target_active is False:
            player.warlock_demon_form_target_active = None
