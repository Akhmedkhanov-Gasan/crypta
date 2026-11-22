from acts.act_three.rune_master.definitions import SPLITFANG_DAMAGE_MULTIPLIER, SPLITFANG_RANGE
from logic import get_enemy_occupied_positions, has_line_of_sight
from systems.player_combat import attack_enemy, resolve_enemy_defeat


def splitfang_hits(game_state, impact, excluded, current_time, oracle_hit_reaction,
                   attacker_name, damage_multiplier, critical):
    from acts.act_three.abilities.archer_piercing_shot import PIERCING_DAMAGE_MIN, PIERCING_DAMAGE_MAX

    floor, player = game_state.floor, game_state.player
    candidates = []
    for enemy in floor.enemies:
        if enemy.health <= 0 or id(enemy) in excluded:
            continue
        cells = [
            cell for cell in get_enemy_occupied_positions(enemy)
            if cell in floor.visible_cells
            and max(abs(cell[0] - impact[0]), abs(cell[1] - impact[1])) <= SPLITFANG_RANGE
            and has_line_of_sight(floor.map, *impact, *cell, floor.barriers)
        ]
        target = min(cells, key=lambda cell: (abs(cell[0] - impact[0]) + abs(cell[1] - impact[1]), cell), default=None)
        if target is not None:
            candidates.append((abs(target[0] - impact[0]) + abs(target[1] - impact[1]), enemy.name, enemy, target))
    for _, _, enemy, target in sorted(candidates, key=lambda item: item[:2])[:2]:
        player.act_three.archer_rune_projectiles.append({
            "origin": impact, "target": target, "started_at": current_time + 400,
            "phantom": attacker_name == "phantom",
        })
        defeated = attack_enemy(
            game_state, enemy, PIERCING_DAMAGE_MIN, PIERCING_DAMAGE_MAX, player.crit_chance,
            force_critical=critical, attacker_position=impact, attacker_name=attacker_name,
            grant_ability_charge=False, suppress_veil_retrigger=critical,
            damage_multiplier=damage_multiplier * SPLITFANG_DAMAGE_MULTIPLIER,
        )
        if enemy.type == "oracle":
            oracle_hit_reaction(enemy, floor, game_state.combat_log)
        if defeated:
            resolve_enemy_defeat(game_state, enemy)
