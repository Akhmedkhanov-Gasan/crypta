import pygame

from acts.act_three.abilities.warlock import (
    cancel_warlock_curse,
    request_warlock_curse,
)
from acts.act_three.combat.enemy_aim import enemy_aim_targets, next_enemy_aim_target
from acts.act_three.combat.warlock_aim import valid_warlock_aim_target, warlock_aiming
from application.directional_input import WAIT_KEYS
from game.combat_log import add_log_message
from presentation.cursors import set_warlock_curse_cursor, set_warlock_staff_cursor


def hover_warlock_aim(game_state, target):
    player = game_state.player
    valid = valid_warlock_aim_target(game_state, target)
    if valid:
        player.warlock_aim_target = target
    if player.warlock_curse_aiming:
        set_warlock_curse_cursor(True, valid)
    else:
        set_warlock_staff_cursor(valid)


def cancel_warlock_aim(game_state):
    player = game_state.player
    if player.warlock_curse_aiming:
        cancel_warlock_curse(game_state)
        set_warlock_curse_cursor()
    else:
        set_warlock_staff_cursor()
    player.warlock_basic_aiming = False
    player.warlock_aim_target = None


def confirm_warlock_aim(game_state, target):
    player = game_state.player
    if player.warlock_attack_target is not None or player.warlock_curse_target is not None:
        return
    if not valid_warlock_aim_target(game_state, target):
        return

    if player.warlock_curse_aiming:
        player.warlock_curse_target = target
    else:
        player.warlock_attack_target = target
    player.warlock_aim_target = None
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))


def handle_warlock_aim_key(event, game_state, direction):
    player = game_state.player
    if (
        game_state.floor.presentation_act != 3
        or player.subclass != "warlock"
        or player.health <= 0
        or player.stun_turns > 0
    ):
        return False

    if player.warlock_attack_target is not None or player.warlock_curse_target is not None:
        return event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER)

    if warlock_aiming(player):
        confirm_key = pygame.K_q if player.warlock_curse_aiming else pygame.K_r
        if event.key == pygame.K_ESCAPE:
            cancel_warlock_aim(game_state)
            return True
        if event.key in (confirm_key, pygame.K_RETURN, pygame.K_KP_ENTER):
            if not getattr(event, "repeat", False):
                confirm_warlock_aim(game_state, player.warlock_aim_target)
            return True
        if direction is not None:
            if not getattr(event, "automatic_movement", False):
                target = next_enemy_aim_target(
                    game_state,
                    enemy_aim_targets(game_state, valid_warlock_aim_target),
                    player.warlock_aim_target,
                    direction,
                )
                if target is not None:
                    hover_warlock_aim(game_state, target)
            return True
        if event.key in WAIT_KEYS:
            return True
        cancel_warlock_aim(game_state)

    if event.key not in (pygame.K_r, pygame.K_q):
        return False
    if getattr(event, "repeat", False):
        return True

    if event.key == pygame.K_q:
        request_warlock_curse(game_state)
        if not player.warlock_curse_aiming:
            return True
    else:
        player.warlock_basic_aiming = True

    targets = enemy_aim_targets(game_state, valid_warlock_aim_target)
    if targets:
        hover_warlock_aim(game_state, targets[0])
    else:
        player.warlock_basic_aiming = False
        player.warlock_curse_aiming = False
        message = "No enemies in range." if event.key == pygame.K_q else "No targets in range."
        add_log_message(game_state.combat_log, message)
    return True
