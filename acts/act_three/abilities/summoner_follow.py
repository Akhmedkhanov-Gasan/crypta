from collections import deque
from copy import copy

from acts.act_three.abilities.summoner_runes import summon_cell_is_free
from logic import can_player_move_between, get_enemy_attack_targets, get_enemy_occupied_positions, has_line_of_sight


FOLLOW_DISTANCE = 2
CHASE_DISTANCE = 4
THREAT_DISTANCE = 5


def cell_distance(first, second):
    return max(abs(first[0] - second[0]), abs(first[1] - second[1]))


def body_cells(position, host=None):
    width = host.footprint_width if host is not None else 1
    height = host.footprint_height if host is not None else 1
    return {(position[0] + dx, position[1] + dy) for dy in range(height) for dx in range(width)}


def companion_step_is_free(game_state, origin, destination, host=None, spirit=False, avoid=()):
    player, floor = game_state.player, game_state.floor
    cells = body_cells(destination, host)
    blocked = set(avoid)
    manifestation = player.act_three.summoner_manifestation
    if spirit:
        if player.summoner_familiar_active and player.summoner_familiar_position is not None:
            blocked.add(tuple(player.summoner_familiar_position))
    elif manifestation is not None and manifestation["health"] > 0:
        blocked.add(tuple(manifestation["position"]))
    if cells.intersection(blocked):
        return False
    for cell in cells:
        if spirit and manifestation is not None and cell == tuple(manifestation["position"]):
            continue
        if not summon_cell_is_free(game_state, cell, ignore_enemy=host):
            return False
    dx, dy = destination[0] - origin[0], destination[1] - origin[1]
    return all(can_player_move_between(floor.map, *cell, cell[0] + dx, cell[1] + dy, floor.barriers)
               for cell in body_cells(origin, host))


def companion_attack_cells(game_state, position, enemy, host=None):
    floor = game_state.floor
    blocked = {(chest.column, chest.row) for chest in floor.chests if not chest.is_open}
    blocked.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    if host is None:
        return tuple(cell for cell in get_enemy_occupied_positions(enemy)
                     if cell_distance(position, cell) == 1
                     and can_player_move_between(floor.map, *position, *cell, floor.barriers))
    proxy = copy(host)
    proxy.column, proxy.row = position
    cells = get_enemy_attack_targets(floor.map, proxy, enemy.column, enemy.row, blocked)
    cells = tuple(cell for cell in cells if has_line_of_sight(floor.map, *position, *cell, floor.barriers))
    return cells if get_enemy_occupied_positions(enemy).intersection(cells) else ()


def plan_companion_turn(game_state, origin, host=None, spirit=False, avoid=()):
    floor, player = game_state.floor, game_state.player
    hero = floor.player_column, floor.player_row
    origin = tuple(origin)
    owner_distance = lambda position: min(cell_distance(cell, hero) for cell in body_cells(position, host))
    chase_distance = CHASE_DISTANCE
    follow_distance = 1 if spirit else FOLLOW_DISTANCE
    threat_distance = 2 if spirit else THREAT_DISTANCE
    retaliation = player.act_three.summoner_manifestation.get("retaliation_enemy") if spirit else None
    if retaliation is not None and not any(enemy.name == retaliation and enemy.health > 0
                                          and min(cell_distance(cell, hero) for cell in get_enemy_occupied_positions(enemy)) <= CHASE_DISTANCE + 1
                                          for enemy in floor.enemies):
        player.act_three.summoner_manifestation["retaliation_enemy"] = None
        retaliation = None
    attackers = lambda enemy: enemy.name == retaliation or bool(set(enemy.attack_targets).intersection(body_cells(origin, host)))
    enemies = [enemy for enemy in floor.enemies if enemy.health > 0 and not enemy.possessed_by_summoner
               and (min(cell_distance(cell, hero) for cell in get_enemy_occupied_positions(enemy)) <= threat_distance
                    or attackers(enemy))]
    focus = player.act_three.summoner_manifestation.get("focus_enemy") if spirit else None
    enemies.sort(key=lambda enemy: (not attackers(enemy), enemy.name != focus, not enemy.is_aggro,
                                   min(cell_distance(cell, origin) for cell in get_enemy_occupied_positions(enemy))))
    if owner_distance(origin) <= chase_distance:
        for enemy in enemies:
            cells = companion_attack_cells(game_state, origin, enemy, host)
            if cells:
                if spirit:
                    player.act_three.summoner_manifestation["focus_enemy"] = enemy.name
                return enemy, cells, origin
    if spirit and not enemies and owner_distance(origin) == follow_distance and not avoid:
        return None, (), origin
    paths = {origin: (origin, 0)}
    queue = deque((origin,))
    while queue:
        current = queue.popleft()
        first, steps = paths[current]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == dy == 0:
                    continue
                candidate = current[0] + dx, current[1] + dy
                if candidate in paths or owner_distance(candidate) > max(chase_distance, owner_distance(origin)):
                    continue
                if not companion_step_is_free(game_state, current, candidate, host, spirit, avoid):
                    continue
                paths[candidate] = (candidate if current == origin else first, steps + 1)
                queue.append(candidate)
    if owner_distance(origin) <= chase_distance:
        options = []
        for priority, enemy in enumerate(enemies):
            for position, (first, steps) in paths.items():
                if position == origin or owner_distance(position) > chase_distance:
                    continue
                if companion_attack_cells(game_state, position, enemy, host):
                    options.append(((priority, steps, abs(owner_distance(position) - follow_distance)), first))
        if options:
            return None, (), min(options, key=lambda option: option[0])[1]
    if spirit and owner_distance(origin) == follow_distance and not avoid:
        return None, (), origin
    facing = player.facing_direction
    candidates = [(position, first, steps) for position, (first, steps) in paths.items() if not body_cells(position, host).intersection(avoid)]
    def idle_score(item):
        position, _, steps = item
        distance = owner_distance(position)
        ahead = max(0, (position[0] - hero[0]) * facing[0] + (position[1] - hero[1]) * facing[1])
        return abs(distance - follow_distance), ahead, steps
    best = min(candidates, key=idle_score, default=(origin, origin, 0))
    return None, (), best[1]


def yield_mobile_summon(game_state, player_target, now):
    player, floor = game_state.player, game_state.floor
    state = player.act_three
    manifestation = state.summoner_manifestation
    spirit = (manifestation is not None and manifestation["health"] > 0
              and manifestation["floor"] == game_state.floor_index and tuple(manifestation["position"]) == player_target)
    familiar = (player.summoner_familiar_active and state.summoner_familiar_mode == "familiar"
                and player.summoner_familiar_position == player_target)
    if not spirit and not familiar:
        return True
    hero = floor.player_column, floor.player_row
    if not can_player_move_between(floor.map, *hero, *player_target, floor.barriers):
        return False
    candidates = [(player_target[0] + dx, player_target[1] + dy)
                  for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
    follow_distance = 1 if spirit else FOLLOW_DISTANCE
    candidates.sort(key=lambda cell: (abs(cell_distance(cell, hero) - follow_distance), cell))
    destination = next((cell for cell in candidates if cell_distance(cell, hero) <= CHASE_DISTANCE
                        and companion_step_is_free(game_state, player_target, cell, spirit=spirit, avoid=(player_target,))), hero)
    if spirit:
        manifestation.update(origin=player_target, position=destination, move_at=now, target=None, skip_turn=True)
    else:
        player.summoner_familiar_movement_origin = player_target
        player.summoner_familiar_position = destination
        player.summoner_familiar_movement_started_at = now
        player.summoner_familiar_attack_target = None
        player.summoner_familiar_skip_turn = True
    return True
