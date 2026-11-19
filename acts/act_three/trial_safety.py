from collections import deque

from game.state import EnemyBehaviorState
from logic import get_enemy_occupied_positions, move_enemy_randomly
from systems.grid_geometry import can_reach_adjacent_cell


def player_is_safe(floor):
    return floor.presentation_act == 3 and (floor.player_column, floor.player_row) in floor.trial_safe_cells


def clear_aggro(enemy):
    enemy.is_aggro = False
    enemy.attack_targets = []
    enemy.prepared_attack_mode = None
    enemy.prepared_attack_target = "hero"
    enemy.attack_windup_turns_remaining = 0
    enemy.heal_target = None
    enemy.summon_windup_turns_remaining = 0
    enemy.summon_animation_started_at = -1
    enemy.warden_reposition_target = None
    enemy.attack_effect_positions = ()
    enemy.attack_effect_mode = None
    if enemy.health > 0 and enemy.is_active:
        enemy.behavior_state = EnemyBehaviorState.IDLE


def blocked_anchors(floor, enemy):
    if not floor.trial_safe_cells:
        return set()
    return {(x - dx, y - dy) for x, y in floor.trial_safe_cells for dy in range(enemy.footprint_height) for dx in range(enemy.footprint_width)}


def occupied_positions(game_state, enemy):
    floor = game_state.floor
    occupied = set()
    occupied.update(cell for other in floor.enemies if other is not enemy and other.health > 0 for cell in get_enemy_occupied_positions(other))
    occupied.update((chest.column, chest.row) for chest in floor.chests if not chest.is_open)
    occupied.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    occupied.update(((floor.player_column, floor.player_row), (floor.stairs_column, floor.stairs_row)))
    if game_state.player.summoner_familiar_active and game_state.player.summoner_familiar_position is not None:
        occupied.add(game_state.player.summoner_familiar_position)
    return occupied


def fits(floor, enemy, cell, occupied):
    x, y = cell
    cells = {(x + dx, y + dy) for dy in range(enemy.footprint_height) for dx in range(enemy.footprint_width)}
    if cells & (occupied | floor.trial_safe_cells):
        return False
    if any(not (0 <= row < len(floor.map) and 0 <= column < len(floor.map[row]) and floor.map[row][column] == ".") for column, row in cells):
        return False
    for origin in cells:
        for destination in ((origin[0] + 1, origin[1]), (origin[0], origin[1] + 1)):
            if destination in cells and not can_reach_adjacent_cell(floor.map, origin, destination, floor.barriers):
                return False
    return True


def idle_turn(game_state, enemy, hazard_costs):
    clear_aggro(enemy)
    if enemy.is_immobile:
        return
    floor = game_state.floor
    origin = enemy.column, enemy.row
    occupied = occupied_positions(game_state, enemy)
    destination = move_enemy_randomly(floor.map, enemy, floor.player_column, floor.player_row, occupied | blocked_anchors(floor, enemy), floor.barriers, hazard_costs)
    if destination == origin or not fits(floor, enemy, destination, occupied):
        return
    if enemy.movement_bounds is not None:
        left, top, right, bottom = enemy.movement_bounds
        if not (left <= destination[0] and top <= destination[1] and destination[0] + enemy.footprint_width - 1 <= right and destination[1] + enemy.footprint_height - 1 <= bottom):
            return
    if not all(can_reach_adjacent_cell(floor.map, (origin[0] + dx, origin[1] + dy), (destination[0] + dx, destination[1] + dy), floor.barriers) for dy in range(enemy.footprint_height) for dx in range(enemy.footprint_width)):
        return
    enemy.column, enemy.row = destination
    from game.events import GameEvent, GameEventType
    from acts.act_three.abilities.archer import resolve_archer_barrage_zone_entry

    game_state.emit(GameEvent(type=GameEventType.MOVE, actor=enemy.name, origin=origin, destination=destination, data={"kind": "wander"}))
    resolve_archer_barrage_zone_entry(game_state, enemy, origin)


def maintain_safety(game_state):
    floor = game_state.floor
    if floor.presentation_act != 3 or not floor.trial_safe_cells:
        return
    safe = player_is_safe(floor)
    for enemy in floor.enemies:
        if enemy.health <= 0:
            continue
        if safe:
            clear_aggro(enemy)
        if not any(cell in floor.trial_safe_cells for cell in get_enemy_occupied_positions(enemy)):
            continue
        occupied = occupied_positions(game_state, enemy)
        door = floor.trial_entrance
        if door is None:
            continue
        origin = door[0], door[1] + 1
        pending = deque([origin])
        visited = {origin}
        while pending:
            cell = pending.popleft()
            if fits(floor, enemy, cell, occupied):
                enemy.column, enemy.row = cell
                clear_aggro(enemy)
                break
            for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)):
                target = cell[0] + dx, cell[1] + dy
                if target in visited or target in floor.trial_safe_cells:
                    continue
                if can_reach_adjacent_cell(floor.map, cell, target, floor.barriers):
                    visited.add(target)
                    pending.append(target)
