from collections import deque

from acts.act_three.ai.pursuit import (
    _move_toward_player_with_footprint,
)
from game.state import EnemyBehaviorState
from game.combat_log import add_log_message
from acts.act_three.enemies.lantern_warden.soul_procession import procession_targets
from logic import can_move_between, get_enemy_occupied_positions
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
    prepare_enemy_attack,
)


def _attack_targets(floor, enemy, position, blocking_positions):
    left = position[0] - (enemy.footprint_width - 1) // 2
    top = position[1] - (enemy.footprint_height - 1) // 2
    right = left + enemy.footprint_width - 1
    bottom = top + enemy.footprint_height - 1
    player = (floor.player_column, floor.player_row)

    if left <= player[0] <= right and player[1] == top - 1:
        pairs = [
            ((column, top), (column, top - 1))
            for column in range(left, right + 1)
        ]
    elif left <= player[0] <= right and player[1] == bottom + 1:
        pairs = [
            ((column, bottom), (column, bottom + 1))
            for column in range(left, right + 1)
        ]
    elif top <= player[1] <= bottom and player[0] == left - 1:
        pairs = [
            ((left, row), (left - 1, row))
            for row in range(top, bottom + 1)
        ]
    elif top <= player[1] <= bottom and player[0] == right + 1:
        pairs = [
            ((right, row), (right + 1, row))
            for row in range(top, bottom + 1)
        ]
    else:
        return []

    targets = [
        target
        for origin, target in pairs
        if (
            target not in blocking_positions
            and can_move_between(
                floor.map,
                origin[0],
                origin[1],
                target[0],
                target[1],
                floor.barriers,
            )
        )
    ]

    return targets if player in targets else []


def _ability_targets(floor, enemy, blocking_positions):
    footprint = get_enemy_occupied_positions(enemy)
    distances = {position: 0 for position in footprint}
    frontier = deque(footprint)
    while frontier:
        origin = frontier.popleft()
        if distances[origin] >= 5:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            target = (origin[0] + dx, origin[1] + dy)
            if target in distances or target in blocking_positions:
                continue
            if not can_move_between(floor.map, *origin, *target, floor.barriers):
                continue
            distances[target] = distances[origin] + 1
            frontier.append(target)
    px, py = floor.player_column, floor.player_row
    cx = enemy.column + (enemy.footprint_width - 1) / 2
    cy = enemy.row + (enemy.footprint_height - 1) / 2
    horizontal = abs(px - cx) > abs(py - cy)
    sign = 1 if (px - cx if horizontal else py - cy) >= 0 else -1
    patterns = {"lantern_sweep": [], "soul_lance": [], "cinder_nova": []}
    for (x, y), distance in sorted(distances.items()):
        if distance == 0:
            continue
        forward = ((x - cx) if horizontal else (y - cy)) * sign
        sideways = abs((y - cy) if horizontal else (x - cx))
        if forward > 0 and distance <= 1 and sideways <= 1.5:
            patterns["lantern_sweep"].append((x, y))
        if distance <= 1:
            patterns["cinder_nova"].append((x, y))
    dx, dy = (sign, 0) if horizontal else (0, sign)
    for origin in sorted(footprint):
        next_cell = (origin[0] + dx, origin[1] + dy)
        if next_cell in footprint:
            continue
        for step in range(1, 6):
            target = (origin[0] + dx * step, origin[1] + dy * step)
            previous = (target[0] - dx, target[1] - dy)
            if target in blocking_positions or not can_move_between(floor.map, *previous, *target, floor.barriers):
                break
            patterns["soul_lance"].append(target)
    return patterns


def _try_prepare_ability(game_state, enemy, blocking_positions):
    patterns = _ability_targets(game_state.floor, enemy, blocking_positions)
    patterns["soul_procession"] = procession_targets(game_state.floor, enemy, blocking_positions)
    player = (game_state.floor.player_column, game_state.floor.player_row)
    order = ("lantern_sweep", "soul_lance", "soul_procession", "cinder_nova")
    if enemy.last_attack_mode in order:
        index = order.index(enemy.last_attack_mode) + 1
        order = order[index:] + order[:index]
    for mode in order:
        targets = patterns[mode]
        if player not in targets or mode == enemy.last_attack_mode:
            continue
        enemy.prepared_attack_target = "hero"
        enemy.attack_effect_positions = ()
        enemy.last_attack_mode = mode
        prepare_enemy_attack(game_state, enemy, targets, mode)
        if mode == "soul_procession":
            add_log_message(game_state.combat_log, "Ghost lanterns converge on the crossing. Step aside!", category="warning")
        return True
    return False


def take_lantern_warden_turn(
    game_state,
    enemy,
    occupied_positions,
    attack_blocking_positions,
    hazard_costs,
):
    if not enemy.is_aggro:
        enemy.behavior_state = EnemyBehaviorState.IDLE
        return

    enemy.behavior_state = EnemyBehaviorState.CHASING

    if _try_prepare_ability(
        game_state,
        enemy,
        attack_blocking_positions,
    ):
        return

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    def destination_test(position):
        return bool(
            _attack_targets(
                game_state.floor,
                enemy,
                position,
                attack_blocking_positions,
            )
        )

    def movement_resolver(*args, **kwargs):
        return _move_toward_player_with_footprint(
            *args,
            **kwargs,
            destination_test=destination_test,
        )

    move_toward_player(
        game_state,
        enemy,
        occupied_positions,
        hazard_costs,
        movement_resolver=movement_resolver,
    )

    if enemy.health > 0:
        _try_prepare_ability(
            game_state,
            enemy,
            attack_blocking_positions,
        )
