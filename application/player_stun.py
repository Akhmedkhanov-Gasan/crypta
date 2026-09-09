import pygame


def stunned_wait_event(game_state, wait_key):
    player = game_state.player
    player.directional_ability_aiming = False
    player.act_two.fire_bomb_aiming = False
    player.act_two.fire_bomb_aiming_slot = None
    player.act_two.scroll_aiming_kind = None
    player.act_two.scroll_aiming_slot = None
    player.act_two.selected_ability_direction = None

    for name in (
        "archer_empowered_shot_aiming",
        "archer_leap_aiming",
        "archer_barrage_zone_aiming",
        "berserker_crushing_leap_aiming",
        "paladin_shield_charge_aiming",
        "warlock_curse_aiming",
        "warlock_soul_exchange_aiming",
        "teleport_aiming",
        "ultimate_aiming",
    ):
        setattr(player, name, False)

    for name in (
        "archer_attack_target",
        "archer_empowered_shot_target",
        "archer_leap_target",
        "berserker_crushing_leap_target",
        "paladin_shield_charge_target",
        "warlock_attack_target",
        "warlock_curse_target",
        "warlock_soul_exchange_target",
        "summoner_attack_target",
        "teleport_target",
    ):
        setattr(player, name, None)

    return pygame.event.Event(pygame.KEYDOWN, key=wait_key)
