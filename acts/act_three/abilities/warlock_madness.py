from math import ceil
import random

import pygame

from acts.act_three.abilities.paladin_runes import effective_dodge_chance
from acts.act_three.settings import WARLOCK_CURSE_DAMAGE_MULTIPLIER
from acts.act_two.enemies.oracle.health import limit_oracle_phase_one_damage
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState
from logic import can_move_to, get_enemy_occupied_positions, has_line_of_sight


DIRECTIONS = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


def take_madness_turn(game_state, enemy):
    from systems.player_combat import damage_player, resolve_enemy_defeat, try_block_enemy_attack

    floor, player = game_state.floor, game_state.player
    direction = random.choice(DIRECTIONS)
    occupied = get_enemy_occupied_positions(enemy)
    origin = max(occupied, key=lambda cell: cell[0] * direction[0] + cell[1] * direction[1])
    values, weights = enemy.damage_by_mode.get("melee", next(iter(enemy.damage_by_mode.values()), ((1,), (1,))))
    damage = random.choices(values, weights=weights, k=1)[0]
    target = origin
    cells = []
    victim = None
    hero_hit = False
    for distance in range(1, max(1, enemy.attack_range) + 1):
        cell = origin[0] + direction[0] * distance, origin[1] + direction[1] * distance
        target = cell
        cells.append(cell)
        if not can_move_to(floor.map, *cell) or not has_line_of_sight(floor.map, *origin, *cell, floor.barriers):
            break
        victim = next((other for other in floor.enemies if other is not enemy and other.health > 0
                       and cell in get_enemy_occupied_positions(other)), None)
        hero_hit = cell == (floor.player_column, floor.player_row)
        if victim is not None or hero_hit:
            break
    enemy.madness_turns -= 1
    enemy.attack_targets.clear()
    enemy.prepared_attack_mode = None
    enemy.attack_windup_turns_remaining = 0
    enemy.heal_target = None
    enemy.behavior_state = EnemyBehaviorState.CHASING if enemy.is_aggro else EnemyBehaviorState.IDLE
    game_state.emit(GameEvent(type=GameEventType.ATTACK, actor=enemy.name, origin=origin,
                              destination=target, positions=tuple(cells), data={"kind": "warlock_madness"}))
    now = pygame.time.get_ticks()
    enemy.attack_animation_started_at = now
    enemy.attack_effect_mode = "madness"
    enemy.attack_effect_positions = tuple(cells)
    flashes = player.act_three.warlock_madness_attacks
    flashes[:] = [entry for entry in flashes if now - entry[-1] < 600]
    flashes.append((*origin, *target, now))
    dealt = 0
    if hero_hit:
        if not try_block_enemy_attack(game_state, enemy.name, origin) and random.random() >= effective_dodge_chance(player):
            dealt = damage_player(game_state, damage)
        if player.health <= 0:
            game_state.emit(GameEvent(type=GameEventType.DEATH, actor="hero", destination=target,
                                      data={"cause": "warlock_madness"}))
    elif victim is not None:
        if victim.type == "sentinel" and victim.shield_blocks_remaining > 0 and victim.sentinel.recovery_turns == 0:
            victim.shield_blocks_remaining -= 1
            if victim.shield_blocks_remaining == 0:
                from systems.enemy_ai.sentinel import break_sentinel_shield

                break_sentinel_shield(game_state, victim)
        elif random.random() >= victim.dodge_chance:
            if victim.curse_turns > 0:
                damage = ceil(damage * WARLOCK_CURSE_DAMAGE_MULTIPLIER)
            dealt = min(victim.health, limit_oracle_phase_one_damage(victim, damage))
            victim.health -= dealt
            if victim.health <= 0:
                victim.behavior_state = EnemyBehaviorState.DEAD
                game_state.emit(GameEvent(type=GameEventType.DEATH, actor=victim.name, destination=target,
                                          data={"cause": "warlock_madness", "enemy_type": victim.type}))
                resolve_enemy_defeat(game_state, victim)
    if hero_hit or victim is not None:
        game_state.emit(GameEvent(type=GameEventType.HIT, actor=enemy.name,
                                  target="hero" if hero_hit else victim.name, origin=origin,
                                  destination=target, amount=dealt, data={"kind": "warlock_madness"}))
