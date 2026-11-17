from acts.act_three.combat.attacks import (
    is_valid_summoner_attack_target,
)
from game.combat_log import add_log_message
from acts.act_three.combat.enemy_aim import enemy_aim_targets, next_enemy_aim_target


def summoner_aim_targets(game_state):
    return enemy_aim_targets(game_state, is_valid_summoner_attack_target)


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


def select_summoner_aim_target(game_state, direction):
    player = game_state.player
    target = next_enemy_aim_target(
        game_state, summoner_aim_targets(game_state), player.summoner_aim_target, direction
    )
    if target is None:
        return False

    player.summoner_aim_target = target
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
