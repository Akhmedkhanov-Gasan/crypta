from acts.act_three.abilities.summoner_runes import summon_cell_is_free
from acts.act_three.rune_master.definitions import POSSESSION_LEASH_RANGE, POSSESSION_FOLLOW_DISTANCE
from game.events import GameEvent, GameEventType
from logic import can_player_move_between, get_enemy_occupied_positions, move_enemy_toward_position


def companion_distance(host, position):
    return min(max(abs(cell[0] - position[0]), abs(cell[1] - position[1]))
               for cell in get_enemy_occupied_positions(host))


def _within_leash(host, cell, hero):
    return min(max(abs(cell[0] + dx - hero[0]), abs(cell[1] + dy - hero[1]))
               for dy in range(host.footprint_height) for dx in range(host.footprint_width)) <= POSSESSION_LEASH_RANGE


def _place_host(game_state, host, destination, now):
    origin = host.column, host.row
    host.column, host.row = destination
    host.movement_origin = origin
    host.movement_animation_started_at = now
    host.attack_targets.clear()
    host.prepared_attack_mode = None
    game_state.player.summoner_familiar_position = destination
    game_state.emit(GameEvent(type=GameEventType.MOVE, actor=host.name, origin=origin,
                              destination=destination, data={"kind": "summoner_possession"}))


def move_companion(game_state, host, target, now, returning=False):
    if host.is_immobile:
        return False
    floor = game_state.floor
    hero = floor.player_column, floor.player_row
    occupied = {hero}
    occupied.update(cell for enemy in floor.enemies if enemy is not host and enemy.health > 0 for cell in get_enemy_occupied_positions(enemy))
    occupied.update((chest.column, chest.row) for chest in floor.chests if not chest.is_open)
    occupied.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    spirit = game_state.player.act_three.summoner_manifestation
    if spirit is not None and spirit["health"] > 0 and spirit["floor"] == game_state.floor_index:
        occupied.add(tuple(spirit["position"]))
    origin = host.column, host.row
    destination = move_enemy_toward_position(floor.map, host, *target, occupied)
    if destination == origin or not can_player_move_between(floor.map, *origin, *destination, floor.barriers):
        return False
    if not returning and not _within_leash(host, destination, hero):
        return False
    if not returning and min(max(abs(destination[0] + dx - hero[0]), abs(destination[1] + dy - hero[1]))
                             for dy in range(host.footprint_height) for dx in range(host.footprint_width)) < POSSESSION_FOLLOW_DISTANCE:
        return False
    _place_host(game_state, host, destination, now)
    return True


def give_owner_space(game_state, host, now):
    if host.is_immobile:
        return False
    floor = game_state.floor
    hero = floor.player_column, floor.player_row
    origin = host.column, host.row
    facing = game_state.player.facing_direction
    candidates = []
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if not (dx or dy):
                continue
            destination = origin[0] + dx, origin[1] + dy
            cells = {(destination[0] + x, destination[1] + y)
                     for y in range(host.footprint_height) for x in range(host.footprint_width)}
            distance = min(max(abs(cell[0] - hero[0]), abs(cell[1] - hero[1])) for cell in cells)
            if not POSSESSION_FOLLOW_DISTANCE <= distance <= POSSESSION_LEASH_RANGE:
                continue
            if not all(summon_cell_is_free(game_state, cell, ignore_enemy=host) for cell in cells):
                continue
            if not can_player_move_between(floor.map, *origin, *destination, floor.barriers):
                continue
            behind = (destination[0] - hero[0]) * facing[0] + (destination[1] - hero[1]) * facing[1]
            candidates.append((abs(distance - POSSESSION_FOLLOW_DISTANCE), behind, destination))
    if not candidates:
        return False
    _place_host(game_state, host, min(candidates)[2], now)
    return True


def yield_companion(game_state, host, player_target, now):
    from acts.act_three.abilities.summoner_follow import CHASE_DISTANCE, companion_step_is_free

    floor = game_state.floor
    hero = floor.player_column, floor.player_row
    direction = player_target[0] - hero[0], player_target[1] - hero[1]
    origin = host.column, host.row
    candidates = [(origin[0] + dx, origin[1] + dy) for dy in range(-1, 2) for dx in range(-1, 2) if dx or dy]
    candidates.sort(key=lambda cell: (-(cell[0] - origin[0]) * direction[0] - (cell[1] - origin[1]) * direction[1],
                                     max(abs(cell[0] - hero[0]), abs(cell[1] - hero[1]))))
    for destination in candidates:
        cells = {(destination[0] + dx, destination[1] + dy)
                 for dy in range(host.footprint_height) for dx in range(host.footprint_width)}
        if player_target in cells or min(max(abs(cell[0] - hero[0]), abs(cell[1] - hero[1])) for cell in cells) > CHASE_DISTANCE:
            continue
        if not companion_step_is_free(game_state, origin, destination, host, avoid=(player_target,)):
            continue
        _place_host(game_state, host, destination, now)
        game_state.player.summoner_familiar_skip_turn = True
        return True
    if host.footprint_width == host.footprint_height == 1 and can_player_move_between(floor.map, *origin, *hero, floor.barriers):
        _place_host(game_state, host, hero, now)
        game_state.player.summoner_familiar_skip_turn = True
        return True
    return False
