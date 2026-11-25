import pygame

from acts.act_three.abilities.phantom_retinue import summon_phantom_retinue
from acts.act_three.ability_scaling import basic_attack_damage_range
from game.events import GameEvent, GameEventType
from systems.player_combat import attack_enemy, resolve_enemy_defeat


class ArcherBarrageTurnInterrupt(Exception):
    pass


def request_archer_barrage_zone(game_state):
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_UNKNOWN, archer_barrage_commit=True,
    ))
    return True


def place_archer_barrage_zone(game_state):
    return summon_phantom_retinue(game_state)


def cancel_archer_barrage_zone(game_state):
    player = game_state.player
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_anchor = None
    player.archer_barrage_zone_preview_cells.clear()


def get_archer_barrage_zone_cells(game_state, anchor):
    return []


def is_valid_archer_barrage_zone_anchor(game_state, anchor):
    return False


def update_archer_barrage_zone_preview(game_state, anchor):
    return False


def select_archer_barrage_zone_direction(game_state, direction):
    return False


def resolve_archer_barrage_zone_entry(game_state, enemy, previous_position):
    return False


def resolve_archer_barrage_hits(game_state):
    damage_minimum, damage_maximum = basic_attack_damage_range(game_state.player)
    pending = tuple(game_state.player.archer_barrage_pending_hits)
    game_state.player.archer_barrage_pending_hits.clear()
    for enemy_id, origin, target in pending:
        enemy = next((enemy for enemy in game_state.floor.enemies if id(enemy) == enemy_id and enemy.health > 0), None)
        if enemy is None:
            continue
        game_state.emit(GameEvent(
            type=GameEventType.ATTACK, actor="phantom", target=enemy.name,
            origin=origin, positions=(target,), data={"kind": "phantom_retinue"},
        ))
        defeated = attack_enemy(
            game_state, enemy, damage_minimum, damage_maximum, game_state.player.crit_chance,
            attacker_position=origin, attacker_name="phantom",
            grant_ability_charge=False, suppress_veil_retrigger=True,
            damage_multiplier=0.25,
        )
        if enemy.type == "oracle":
            from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

            resolve_oracle_hit_reaction(enemy, game_state.floor, game_state.combat_log)
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
