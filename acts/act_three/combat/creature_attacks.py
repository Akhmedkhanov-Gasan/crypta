from math import ceil
import random

from acts.act_three.settings import WARLOCK_CURSE_DAMAGE_MULTIPLIER
from acts.act_two.enemies.oracle.health import limit_oracle_phase_one_damage
from game.events import GameEvent, GameEventType
from game.state import EnemyBehaviorState


def damage_enemy_from_creature(game_state, attacker, victim, damage, mode):
    from systems.player_combat import resolve_enemy_defeat

    origin = attacker.column, attacker.row
    if victim.type == "sentinel" and victim.shield_blocks_remaining > 0 and victim.sentinel.recovery_turns == 0:
        victim.shield_blocks_remaining -= 1
        if victim.shield_blocks_remaining == 0:
            from systems.enemy_ai.sentinel import break_sentinel_shield

            break_sentinel_shield(game_state, victim)
        damage = 0
    elif random.random() < victim.dodge_chance:
        damage = 0
    else:
        if victim.curse_turns > 0:
            damage = ceil(damage * WARLOCK_CURSE_DAMAGE_MULTIPLIER)
        damage = min(victim.health, limit_oracle_phase_one_damage(victim, damage))
        victim.health -= damage
    game_state.emit(GameEvent(type=GameEventType.HIT, actor=attacker.name, target=victim.name,
                              origin=origin, destination=(victim.column, victim.row), amount=damage,
                              data={"kind": mode, "enemy_type": victim.type, "critical": False}))
    if victim.type == "oracle" and damage > 0:
        from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

        resolve_oracle_hit_reaction(victim, game_state.floor, game_state.combat_log)
    if victim.health <= 0:
        victim.behavior_state = EnemyBehaviorState.DEAD
        game_state.emit(GameEvent(type=GameEventType.DEATH, actor=victim.name,
                                  destination=(victim.column, victim.row), data={"enemy_type": victim.type, "cause": mode}))
        resolve_enemy_defeat(game_state, victim)
    return damage
