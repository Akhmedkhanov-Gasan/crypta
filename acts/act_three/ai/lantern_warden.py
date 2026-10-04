from acts.act_three.ai.pursuit import (
    _move_toward_player_with_footprint,
)
from game.state import EnemyBehaviorState
from logic import can_move_between
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


def _try_prepare_melee(game_state, enemy, blocking_positions):
    targets = _attack_targets(
        game_state.floor,
        enemy,
        (enemy.column, enemy.row),
        blocking_positions,
    )

    if not targets:
        return False

    enemy.prepared_attack_target = "hero"
    enemy.attack_effect_positions = ()
    prepare_enemy_attack(
        game_state,
        enemy,
        targets,
        "melee",
    )
    return True


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

    if _try_prepare_melee(
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
        _try_prepare_melee(
            game_state,
            enemy,
            attack_blocking_positions,
        )
