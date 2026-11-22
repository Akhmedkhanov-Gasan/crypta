import random

import pygame

from acts.act_three.abilities.phantom_state import ArcherPhantom
from acts.act_three.abilities.phantom_motion import phantom_position, queue_phantom_attack
from acts.act_three.abilities.progression import clear_ability_slot_charge, is_ability_slot_charged
from acts.act_three.combat.archer_aim import cancel_archer_aim
from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType
from logic import can_move_to, get_enemy_occupied_positions, has_line_of_sight
from systems.grid_geometry import can_reach_adjacent_cell
from acts.act_three.rune_master.definitions import MIRROR_ACTIONS, SPECTRAL_ARCHER_COUNT, has_ability_rune


PHANTOM_COUNT = 2
PHANTOM_RANGE = 3
PHANTOM_FOLLOW_DISTANCE = 2


def _positions(game_state, occupied, *, require_visible=True):
    floor = game_state.floor
    px, py = floor.player_column, floor.player_row
    blocked = {
        cell for enemy in floor.enemies if enemy.health > 0
        for cell in get_enemy_occupied_positions(enemy)
    }
    return [
        (x, y)
        for y in range(max(0, py - PHANTOM_FOLLOW_DISTANCE), min(len(floor.map), py + PHANTOM_FOLLOW_DISTANCE + 1))
        for x in range(max(0, px - PHANTOM_FOLLOW_DISTANCE), min(len(floor.map[y]), px + PHANTOM_FOLLOW_DISTANCE + 1))
        if max(abs(x - px), abs(y - py)) == PHANTOM_FOLLOW_DISTANCE
        and (not require_visible or (x, y) in floor.visible_cells)
        and (x, y) not in blocked
        and (x, y) not in occupied
        and can_move_to(floor.map, x, y)
        and has_line_of_sight(floor.map, px, py, x, y, floor.barriers)
    ]


def summon_phantom_retinue(game_state):
    player = game_state.player
    if player.subclass != "archer" or player.health <= 0:
        return False
    if not is_ability_slot_charged(player, "f"):
        add_log_message(game_state.combat_log, "Phantom Retinue is not charged.")
        return False
    cells = _positions(game_state, set())
    if not cells:
        add_log_message(game_state.combat_log, "No room for the Phantom Retinue.")
        return False
    mirror = has_ability_rune(player, "rune_of_phantom_archer")
    count = 1 if mirror else SPECTRAL_ARCHER_COUNT if has_ability_rune(player, "rune_of_spectral_archers") else PHANTOM_COUNT
    now = pygame.time.get_ticks()
    random.shuffle(cells)
    enemies = [enemy for enemy in game_state.floor.enemies if enemy.health > 0]
    cells.sort(key=lambda origin: not any(
        max(abs(cell[0] - origin[0]), abs(cell[1] - origin[1])) <= PHANTOM_RANGE
        and cell in game_state.floor.visible_cells
        and has_line_of_sight(game_state.floor.map, *origin, *cell, game_state.floor.barriers)
        for enemy in enemies for cell in get_enemy_occupied_positions(enemy)
    ))
    cancel_archer_aim(game_state)
    player.archer_empowered_shot_aiming = False
    player.archer_empowered_shot_target = None
    player.archer_leap_aiming = False
    player.archer_leap_target = None
    player.archer_barrage_zone_aiming = False
    player.archer_barrage_zone_cells.clear()
    player.archer_barrage_zones.clear()
    player.archer_barrage_zone_preview_cells.clear()
    player.act_three.archer_phantoms = [
        ArcherPhantom(cell, cell, now, random.randrange(1_000_000), number=index,
                      mirror=mirror, shots_remaining=MIRROR_ACTIONS if mirror else 6)
        for index, cell in enumerate(cells[:count], 1)
    ]
    player.act_three.archer_mirror_actions.clear()
    player.act_three.archer_phantom_travel_started_at = -1
    player.act_three.archer_phantom_travel_ended_at = -1
    player.act_three.archer_phantom_cast = {
        "started_at": now,
        "floor_index": game_state.floor_index,
        "origin": (game_state.floor.player_column, game_state.floor.player_row),
        "positions": tuple(phantom.position for phantom in player.act_three.archer_phantoms),
    }
    clear_ability_slot_charge(player, "f")
    game_state.emit(GameEvent(
        type=GameEventType.ABILITY, actor="hero",
        positions=tuple(cells[:count]),
        data={"ability": "phantom_retinue"},
    ))
    add_log_message(game_state.combat_log, "The Phantom Retinue answers the call.", category="ability")
    return True


def relocate_phantom_retinue(game_state, current_time):
    state = game_state.player.act_three
    state.archer_phantoms[:] = [
        phantom for phantom in state.archer_phantoms
        if phantom.shots_remaining > 0
    ]
    cells = _positions(game_state, set(), require_visible=False)
    random.shuffle(cells)
    origin = (game_state.floor.player_column, game_state.floor.player_row)
    for phantom in state.archer_phantoms:
        position = cells.pop() if cells else origin
        phantom.position = position
        phantom.origin = position
        phantom.moved_at = current_time
        phantom.teleporting = False
        phantom.target = None
        phantom.fired_at = -1
        phantom.expired_at = -1
        phantom.walk_direction = (0, 0)
        phantom.has_acted = False
        phantom.attack_animations.clear()
    state.archer_mirror_actions.clear()
    state.archer_rune_projectiles.clear()


def _target_cell(game_state, phantom, enemy):
    cells = [
        cell for cell in get_enemy_occupied_positions(enemy)
        if cell in game_state.floor.visible_cells
        and max(abs(cell[0] - phantom.position[0]), abs(cell[1] - phantom.position[1])) <= PHANTOM_RANGE
        and has_line_of_sight(game_state.floor.map, *phantom.position, *cell, game_state.floor.barriers)
    ]
    return min(cells, key=lambda cell: abs(cell[0] - phantom.position[0]) + abs(cell[1] - phantom.position[1]), default=None)


def advance_phantom_retinue(game_state, player_previous_position=None):
    state = game_state.player.act_three
    if not state.archer_phantoms or game_state.player.health <= 0:
        return
    now = pygame.time.get_ticks()
    state.archer_phantoms[:] = [
        phantom for phantom in state.archer_phantoms
        if phantom.expired_at < 0 or now < phantom.expired_at + 450
    ]
    occupied = {phantom.position for phantom in state.archer_phantoms if phantom.shots_remaining > 0}
    preferred = set(game_state.player_attack_targets)
    preferred.update(
        cell for event in game_state.events
        if event.type == GameEventType.ATTACK and event.actor == "hero"
        for cell in event.positions
    )
    enemies = [enemy for enemy in game_state.floor.enemies if enemy.health > 0]
    for index, phantom in enumerate(state.archer_phantoms):
        if phantom.shots_remaining <= 0:
            continue
        phantom.target = None
        cells = _positions(game_state, occupied - {phantom.position})
        px, py = game_state.floor.player_column, game_state.floor.player_row
        outside_follow_radius = max(abs(phantom.position[0] - px), abs(phantom.position[1] - py)) != PHANTOM_FOLLOW_DISTANCE
        targets = [(enemy, _target_cell(game_state, phantom, enemy)) for enemy in enemies]
        targets = [(enemy, cell) for enemy, cell in targets if cell is not None]
        mirrored_move = False
        if phantom.mirror and player_previous_position is not None:
            dx, dy = px - player_previous_position[0], py - player_previous_position[1]
            destination = phantom.position[0] + dx, phantom.position[1] + dy
            if (dx or dy) and destination in cells and max(abs(dx), abs(dy)) == 1 and can_reach_adjacent_cell(
                game_state.floor.map, phantom.position, destination, game_state.floor.barriers,
            ):
                occupied.discard(phantom.position)
                phantom.origin = phantom_position(phantom, now)
                phantom.walk_direction = dx, dy
                phantom.position = destination
                phantom.moved_at = now
                phantom.teleporting = False
                occupied.add(destination)
                mirrored_move = True
        if not mirrored_move and cells and phantom.has_acted and (outside_follow_radius or (not targets and not phantom.mirror)):
            occupied.discard(phantom.position)
            nearby = [
                cell for cell in cells
                if max(abs(cell[0] - phantom.position[0]), abs(cell[1] - phantom.position[1])) == 1
                and can_reach_adjacent_cell(game_state.floor.map, phantom.position, cell, game_state.floor.barriers)
            ]
            walk = bool(nearby) and random.random() < 0.8
            straight = (
                phantom.position[0] + phantom.walk_direction[0],
                phantom.position[1] + phantom.walk_direction[1],
            )
            destination = straight if walk and straight in nearby and random.random() < 0.7 else random.choice(nearby if walk else cells)
            phantom.walk_direction = (
                destination[0] - phantom.position[0],
                destination[1] - phantom.position[1],
            )
            phantom.origin = phantom_position(phantom, now)
            phantom.position = destination
            phantom.teleporting = not walk
            phantom.moved_at = now
            occupied.add(destination)
            targets = [(enemy, _target_cell(game_state, phantom, enemy)) for enemy in enemies]
            targets = [(enemy, cell) for enemy, cell in targets if cell is not None]
        if phantom.mirror:
            from acts.act_three.abilities.mirror_actions import advance_mirror_actions

            advance_mirror_actions(game_state, phantom, now)
            phantom.has_acted = True
            continue
        if targets:
            enemy, target = min(targets, key=lambda pair: (
                not bool(set(get_enemy_occupied_positions(pair[0])) & preferred),
                abs(pair[1][0] - phantom.position[0]) + abs(pair[1][1] - phantom.position[1]),
            ))
            phantom.target = target
            animation_ends_at = queue_phantom_attack(phantom, target, now)
            game_state.player.archer_barrage_pending_hits.append((id(enemy), phantom.position, target))
            phantom.shots_remaining -= 1
            if phantom.shots_remaining == 0:
                phantom.expired_at = animation_ends_at
        phantom.has_acted = True
