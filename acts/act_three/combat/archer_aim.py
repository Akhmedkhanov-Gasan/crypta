from acts.act_three.combat.attacks import (
    is_valid_archer_attack_target,
)
from acts.act_three.combat.enemy_aim import enemy_aim_targets
from game.combat_log import add_log_message


def archer_aim_targets(game_state):
    return enemy_aim_targets(game_state, is_valid_archer_attack_target)


def begin_archer_aim(game_state, current_time, piercing=False):
    player = game_state.player
    if player.subclass != "archer" or player.health <= 0:
        return False

    targets = archer_aim_targets(game_state)
    if not targets:
        add_log_message(
            game_state.combat_log,
            "No enemies in range." if piercing else "No targets in range.",
        )
        return False

    player.archer_basic_aiming = not piercing
    player.archer_piercing_aiming = piercing
    player.archer_basic_aim_started_at = current_time
    player.archer_basic_aim_target = targets[0]
    return True


def cancel_archer_aim(game_state):
    player = game_state.player
    player.archer_basic_aiming = False
    player.archer_basic_aim_target = None
    player.archer_basic_aim_started_at = 0
    player.archer_piercing_aiming = False


def select_archer_aim_target(game_state, direction):
    targets = archer_aim_targets(game_state)
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    dx, dy = direction

    directed_targets = [
        target
        for target in targets
        if (
            (target[0] - origin[0]) * dx
            + (target[1] - origin[1]) * dy
        ) > 0
    ]
    if not directed_targets:
        return False

    directed_targets.sort(
        key=lambda target: (
            abs(
                (target[0] - origin[0]) * dy
                - (target[1] - origin[1]) * dx
            ),
            abs(target[0] - origin[0])
            + abs(target[1] - origin[1]),
            target[1],
            target[0],
        )
    )

    current = game_state.player.archer_basic_aim_target
    if current in directed_targets:
        index = (directed_targets.index(current) + 1) % len(
            directed_targets
        )
    else:
        index = 0

    game_state.player.archer_basic_aim_target = directed_targets[index]
    return True


def confirm_archer_aim(game_state):
    player = game_state.player
    target = player.archer_basic_aim_target
    targets = archer_aim_targets(game_state)

    if target not in targets:
        player.archer_basic_aim_target = targets[0] if targets else None
        return False

    if player.archer_piercing_aiming:
        player.archer_piercing_target = target
    else:
        player.archer_attack_target = target

    cancel_archer_aim(game_state)
    return True


def archer_shot_direction(origin, target):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]

    if abs(dx) >= abs(dy):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)
