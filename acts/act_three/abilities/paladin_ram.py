from acts.act_three.combat.stun import apply_act_three_enemy_stun
from acts.act_three.rune_master.definitions import BATTERING_RAM_COLLISION_MULTIPLIER
from acts.act_three.settings import PALADIN_SHIELD_CHARGE_TRAVEL_MS, PALADIN_SHIELD_CHARGE_WINDUP_MS
from game.events import GameEvent, GameEventType
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell


def _push_destination(floor, enemy, step, hero_position):
    from acts.act_three.npcs import get_npc_at

    origin = enemy.column, enemy.row
    for dx, dy in ((-step[1], step[0]), (step[1], -step[0]), step):
        target = origin[0] + dx, origin[1] + dy
        if target == hero_position or not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
            continue
        if any(other is not enemy and other.health > 0 and target in get_enemy_occupied_positions(other)
               for other in floor.enemies):
            continue
        if any(not chest.is_open and target == (chest.column, chest.row) for chest in floor.chests):
            continue
        if any(not crate.is_broken and target == (crate.column, crate.row) for crate in getattr(floor, "breakable_crates", [])):
            continue
        if any(ore.get("stage", 0) < 3 and target == ore.get("position") for ore in getattr(floor, "act_three_ores", [])):
            continue
        if get_npc_at(floor, target) is not None:
            continue
        return target
    return None


def perform_battering_ram(game_state, current_time, oracle_hit_reaction):
    from acts.act_three.abilities.paladin import get_paladin_shield_charge_path
    from systems.player_combat import attack_enemy, resolve_enemy_defeat

    player, floor = game_state.player, game_state.floor
    origin = floor.player_column, floor.player_row
    path = get_paladin_shield_charge_path(game_state, player.paladin_shield_charge_target)
    destination = origin
    traversed, struck = [], set()
    player.act_three.paladin_ram_impacts.clear()
    for index, cell in enumerate(path):
        step = cell[0] - destination[0], cell[1] - destination[1]
        for enemy in tuple(floor.enemies):
            if enemy.health <= 0 or id(enemy) in struck or cell not in get_enemy_occupied_positions(enemy):
                continue
            struck.add(id(enemy))
            health = enemy.health
            defeated = attack_enemy(game_state, enemy, player.damage_min, player.damage_max,
                                    player.crit_chance, attacker_position=destination, grant_ability_charge=False)
            if enemy.type == "oracle":
                oracle_hit_reaction(enemy, floor, game_state.combat_log)
            collision = False
            if not defeated:
                movable = (not enemy.is_immobile and len(get_enemy_occupied_positions(enemy)) == 1
                           and enemy.type not in ("warden", "oracle", "oracle_pillar", "lantern_warden"))
                pushed = _push_destination(floor, enemy, step, destination) if movable else None
                if pushed is not None:
                    previous = enemy.column, enemy.row
                    enemy.column, enemy.row = pushed
                    game_state.emit(GameEvent(type=GameEventType.MOVE, actor=enemy.name, origin=previous,
                                              destination=pushed, data={"kind": "paladin_battering_ram", "enemy_type": enemy.type}))
                elif movable:
                    collision = True
                    defeated = attack_enemy(game_state, enemy, player.damage_min, player.damage_max,
                                            player.crit_chance, attacker_position=destination,
                                            damage_multiplier=BATTERING_RAM_COLLISION_MULTIPLIER, grant_ability_charge=False)
                if enemy.health < health and not defeated:
                    apply_act_three_enemy_stun(game_state, enemy, 1, current_time)
            if defeated:
                resolve_enemy_defeat(game_state, enemy)
            impact_time = current_time + PALADIN_SHIELD_CHARGE_WINDUP_MS + round(
                PALADIN_SHIELD_CHARGE_TRAVEL_MS * (1 - (1 - (index + 1) / len(path)) ** (1 / 2.15)))
            player.act_three.paladin_ram_impacts.append((*cell, collision, impact_time))
        if any(enemy.health > 0 and cell in get_enemy_occupied_positions(enemy) for enemy in floor.enemies):
            break
        destination = cell
        traversed.append(cell)
    floor.player_column, floor.player_row = destination
    player.facing_direction = (path[0][0] - origin[0], path[0][1] - origin[1])
    player.paladin_shield_charge_charge = 0
    player.paladin_shield_charge_aiming = False
    player.paladin_shield_charge_target = None
    player.paladin_shield_charge_preview_cells.clear()
    player.paladin_shield_charge_origin = origin
    player.paladin_shield_charge_started_at = current_time
    game_state.emit(GameEvent(type=GameEventType.MOVE, actor="hero", origin=origin,
                              destination=destination, positions=tuple(traversed), data={"kind": "paladin_shield_charge"}))
    game_state.emit(GameEvent(type=GameEventType.ATTACK, actor="hero", origin=origin,
                              destination=destination, positions=tuple(path), data={"kind": "paladin_battering_ram"}))
    return True
