from acts.act_three.combat.attacks import (
    is_valid_summoner_attack_target,
)
from game.combat_log import add_log_message
from logic import get_enemy_occupied_positions


def summoner_aim_targets(game_state):
    floor = game_state.floor
    origin = (
        floor.player_column,
        floor.player_row,
    )
    targets = []

    for enemy in floor.enemies:
        if enemy.health <= 0:
            continue

        cells = [
            cell
            for cell in get_enemy_occupied_positions(enemy)
            if (
                cell in floor.visible_cells
                and is_valid_summoner_attack_target(
                    game_state,
                    cell,
                )
            )
        ]
        if not cells:
            continue

        target = min(
            cells,
            key=lambda cell: (
                abs(cell[0] - origin[0])
                + abs(cell[1] - origin[1]),
                cell[1],
                cell[0],
            ),
        )
        targets.append(target)

    return sorted(
        targets,
        key=lambda cell: (
            abs(cell[0] - origin[0])
            + abs(cell[1] - origin[1]),
            cell[1],
            cell[0],
        ),
    )


def begin_summoner_aim(game_state, current_time):
    player = game_state.player
    if player.subclass != "summoner" or player.health <= 0:
        return False

    targets = summoner_aim_targets(game_state)
    if not targets:
        add_log_message(
            game_state.combat_log,
            "No enemies in range.",
        )
        return False

    player.summoner_aiming = True
    player.summoner_aim_target = targets[0]
    player.summoner_aim_started_at = current_time
    return True


def cancel_summoner_aim(game_state):
    player = game_state.player
    player.summoner_aiming = False
    player.summoner_aim_target = None
    player.summoner_aim_started_at = 0


def select_summoner_aim_target(
    game_state,
    direction,
):
    targets = summoner_aim_targets(game_state)
    origin = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    direction_x, direction_y = direction

    directed_targets = [
        target
        for target in targets
        if (
            (target[0] - origin[0]) * direction_x
            + (target[1] - origin[1]) * direction_y
        ) > 0
    ]
    if not directed_targets:
        return False

    directed_targets.sort(
        key=lambda target: (
            abs(
                (target[0] - origin[0]) * direction_y
                - (target[1] - origin[1]) * direction_x
            ),
            abs(target[0] - origin[0])
            + abs(target[1] - origin[1]),
            target[1],
            target[0],
        )
    )

    current = game_state.player.summoner_aim_target
    if current in directed_targets:
        index = (
            directed_targets.index(current) + 1
        ) % len(directed_targets)
    else:
        index = 0

    game_state.player.summoner_aim_target = (
        directed_targets[index]
    )
    return True


def confirm_summoner_aim(game_state):
    player = game_state.player
    targets = summoner_aim_targets(game_state)
    target = player.summoner_aim_target

    if target not in targets:
        player.summoner_aim_target = (
            targets[0] if targets else None
        )
        return False

    player.summoner_attack_target = target
    cancel_summoner_aim(game_state)
    return True
