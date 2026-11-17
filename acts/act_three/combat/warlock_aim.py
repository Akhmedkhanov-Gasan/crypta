from acts.act_three.abilities.warlock import is_valid_warlock_curse_target
from acts.act_three.combat.attacks import is_valid_warlock_attack_target


def warlock_aiming(player):
    return player.warlock_basic_aiming or player.warlock_curse_aiming


def valid_warlock_aim_target(game_state, target):
    player = game_state.player
    if (
        target is None
        or not warlock_aiming(player)
        or target not in game_state.floor.visible_cells
    ):
        return False

    validator = (
        is_valid_warlock_curse_target
        if player.warlock_curse_aiming
        else is_valid_warlock_attack_target
    )
    return validator(game_state, target)
