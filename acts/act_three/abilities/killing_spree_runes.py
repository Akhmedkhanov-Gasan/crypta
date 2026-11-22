import random

from acts.act_three.rune_master.definitions import (
    CARNAGE_EXTRA_ATTACKS, CARNAGE_TRANSFER_RANGE, EXECUTIONER_DAMAGE_MULTIPLIER,
    has_ability_rune,
)
from acts.act_three.settings import ASSASSIN_ULTIMATE_PRELUDE_MS, ASSASSIN_ULTIMATE_STEP_MS
from logic import get_enemy_occupied_positions, has_line_of_sight
from systems.player_combat import attack_enemy, resolve_enemy_defeat


def _carnage_neighbor(game_state, origin):
    candidates = [
        (max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])), enemy.name, enemy)
        for enemy in game_state.floor.enemies if enemy.health > 0
        for cell in get_enemy_occupied_positions(enemy)
        if cell in game_state.floor.visible_cells
        and max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= CARNAGE_TRANSFER_RANGE
        and has_line_of_sight(game_state.floor.map, *origin, *cell, game_state.floor.barriers)
    ]
    return min(candidates, key=lambda item: item[:2])[2] if candidates else None


def _redirect_remaining(game_state, index, origin, extra=0):
    player = game_state.player
    remaining = len(player.ultimate_targets) - index + extra
    neighbor = _carnage_neighbor(game_state, origin) if remaining else None
    del player.ultimate_targets[index:]
    del player.ultimate_visual_variants[index:]
    if neighbor is None:
        return False
    previous = player.ultimate_visual_variants[-1] if player.ultimate_visual_variants else None
    for _ in range(remaining):
        previous = random.choice([value for value in range(4) if value != previous])
        player.ultimate_targets.append(neighbor.name)
        player.ultimate_visual_variants.append(previous)
    return True


def advance_killing_spree(game_state, oracle_hit_reaction, current_time, *, finish=False):
    player = game_state.player
    carnage = has_ability_rune(player, "rune_of_carnage")
    executioner = has_ability_rune(player, "rune_of_the_executioner")
    elapsed = current_time - player.ultimate_animation_started_at - ASSASSIN_ULTIMATE_PRELUDE_MS
    while player.ultimate_resolved_strikes < len(player.ultimate_targets):
        index = player.ultimate_resolved_strikes
        name = player.ultimate_targets[index]
        enemy = next((enemy for enemy in game_state.floor.enemies if enemy.name == name and enemy.health > 0), None)
        if enemy is None:
            if carnage:
                previous = next((enemy for enemy in game_state.floor.enemies if enemy.name == name), None)
                origin = ((previous.column, previous.row) if previous is not None else
                          player.ultimate_impact_positions[-1] if player.ultimate_impact_positions else player.ultimate_origin)
                if not _redirect_remaining(game_state, index, origin):
                    break
                continue
            if executioner:
                del player.ultimate_targets[index:]
                del player.ultimate_visual_variants[index:]
                break
            if not finish and elapsed < (index + 0.72) * ASSASSIN_ULTIMATE_STEP_MS:
                break
            player.ultimate_resolved_strikes += 1
            continue
        if not finish and elapsed < (index + 0.72) * ASSASSIN_ULTIMATE_STEP_MS:
            break
        player.ultimate_resolved_strikes += 1
        multiplier = EXECUTIONER_DAMAGE_MULTIPLIER if executioner else 1.0
        defeated = attack_enemy(
            game_state, enemy, player.damage_min, player.damage_max, player.crit_chance,
            attacker_position=player.ultimate_origin,
            damage_multiplier=multiplier, grant_ability_charge=False,
        )
        player.ultimate_impact_positions.append((enemy.column, enemy.row))
        player.ultimate_impact_started_at = current_time
        if enemy.type == "oracle":
            oracle_hit_reaction(enemy, game_state.floor, game_state.combat_log)
        if not defeated:
            continue
        resolve_enemy_defeat(game_state, enemy)
        if executioner:
            del player.ultimate_targets[index + 1:]
            del player.ultimate_visual_variants[index + 1:]
        if not carnage:
            continue
        extra = 0 if player.ultimate_bonus_strikes_awarded else CARNAGE_EXTRA_ATTACKS
        player.ultimate_bonus_strikes_awarded = True
        _redirect_remaining(game_state, index + 1, (enemy.column, enemy.row), extra)
