from acts.act_three.abilities.phantom_motion import queue_phantom_attack
from acts.act_three.rune_master.definitions import MIRROR_DAMAGE_MULTIPLIER
from acts.act_three.ability_scaling import basic_attack_damage_range
from acts.act_three.settings import ARCHER_BASIC_ATTACK_RANGE
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions, has_line_of_sight
from systems.player_combat import attack_enemy, resolve_enemy_defeat


def queue_mirror_action(game_state, kind, target, current_time):
    player = game_state.player
    phantom = next((phantom for phantom in player.act_three.archer_phantoms
                    if phantom.mirror and phantom.shots_remaining > 0), None)
    if phantom is None:
        return
    player.act_three.archer_mirror_actions.append({
        "seed": phantom.seed, "kind": kind, "target": target,
        "duration": player.invisibility_turns, "started_at": current_time,
    })


def _oracle_reaction(enemy, floor, log):
    if enemy.type == "oracle":
        from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction

        resolve_oracle_hit_reaction(enemy, floor, log)


def advance_mirror_actions(game_state, phantom, current_time):
    state, floor, player = game_state.player.act_three, game_state.floor, game_state.player
    if phantom.invisibility_turns > 0:
        phantom.invisibility_turns -= 1
    actions = [action for action in state.archer_mirror_actions if action["seed"] == phantom.seed]
    state.archer_mirror_actions[:] = [action for action in state.archer_mirror_actions if action["seed"] != phantom.seed]
    for action in actions:
        if phantom.shots_remaining <= 0:
            break
        if action["kind"] == "invisibility":
            phantom.invisibility_turns = max(phantom.invisibility_turns, action["duration"])
            phantom.shots_remaining -= 1
            if phantom.shots_remaining == 0:
                phantom.expired_at = current_time
            continue
        target = action["target"]
        if target is None:
            continue
        distance = max(abs(target[0] - phantom.position[0]), abs(target[1] - phantom.position[1]))
        if distance > ARCHER_BASIC_ATTACK_RANGE + 2 or not has_line_of_sight(
            floor.map, *phantom.position, *target, floor.barriers,
        ):
            continue
        critical = phantom.invisibility_turns > 0
        phantom.invisibility_turns = 0
        ends_at = queue_phantom_attack(phantom, target, current_time)
        phantom.attack_animations[-1]["kind"] = action["kind"]
        phantom.shots_remaining -= 1
        if phantom.shots_remaining == 0:
            phantom.expired_at = ends_at
        game_state.emit(GameEvent(
            type=GameEventType.ATTACK, actor="phantom", origin=phantom.position,
            positions=(target,), data={"kind": f"mirror_{action['kind']}"},
        ))
        if action["kind"] == "piercing":
            from acts.act_three.abilities.archer_piercing_shot import piercing_shot_cells, resolve_piercing_hits

            cells = piercing_shot_cells(game_state, target, origin=phantom.position)
            enemies = []
            for cell in cells:
                for enemy in floor.enemies:
                    if enemy.health > 0 and enemy not in enemies and cell in get_enemy_occupied_positions(enemy):
                        enemies.append(enemy)
            resolve_piercing_hits(game_state, enemies, phantom.position, current_time, _oracle_reaction,
                                  attacker_name="phantom", damage_multiplier=MIRROR_DAMAGE_MULTIPLIER,
                                  shot_from_invisibility=critical)
            if cells:
                from acts.act_three.rune_master.definitions import has_ability_rune

                phantom.attack_animations[-1]["target"] = (
                    (enemies[0].column, enemies[0].row)
                    if enemies and has_ability_rune(player, "rune_of_splitfang_arrow") else cells[-1]
                )
        else:
            enemy = next((enemy for enemy in floor.enemies
                          if enemy.health > 0 and target in get_enemy_occupied_positions(enemy)), None)
            if enemy is None:
                continue
            damage_minimum, damage_maximum = basic_attack_damage_range(player)
            defeated = attack_enemy(
                game_state, enemy, damage_minimum, damage_maximum, player.crit_chance,
                attacker_position=phantom.position, attacker_name="phantom",
                force_critical=critical, damage_multiplier=MIRROR_DAMAGE_MULTIPLIER,
                grant_ability_charge=False, suppress_veil_retrigger=True,
            )
            _oracle_reaction(enemy, floor, game_state.combat_log)
            if defeated:
                resolve_enemy_defeat(game_state, enemy)
