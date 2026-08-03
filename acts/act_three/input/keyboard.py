import pygame

from acts.act_three.input.cursors import (
    set_archer_barrage_zone_cursor,
    set_archer_empowered_cursor,
    set_archer_leap_cursor,
    set_assassin_target_cursor,
    set_berserker_crushing_leap_cursor,
    set_paladin_shield_charge_cursor,
    set_summoner_staff_cursor,
    set_warlock_staff_cursor,
)
from acts.act_three.abilities.archer import (
    cancel_archer_barrage_zone,
    cancel_archer_empowered_shot,
    cancel_archer_leap,
    request_archer_barrage_zone,
    request_archer_empowered_shot,
    request_archer_leap,
)
from acts.act_three.abilities.assassin import (
    begin_assassin_ultimate,
    cancel_assassin_teleport,
    cancel_assassin_ultimate,
    request_assassin_teleport,
    request_assassin_ultimate,
)
from acts.act_three.abilities.berserker import (
    cancel_berserker_crushing_leap,
    request_berserker_crushing_leap,
    request_berserker_last_rage,
)
from acts.act_three.abilities.paladin import (
    cancel_paladin_shield_charge,
    request_paladin_holy_hand,
    request_paladin_holy_shield,
    request_paladin_shield_charge,
)
from acts.act_three.abilities.summoner import (
    release_summoner_familiar,
    request_summoner_bond,
    request_summoner_true_form,
)
from acts.act_three.abilities.warlock import (
    cancel_warlock_curse,
    cancel_warlock_soul_exchange,
    request_warlock_curse,
    request_warlock_soul_exchange,
)
from levels import FLOOR_CONFIGS
from settings import (
    ARCHER_LEAP_DURATION_MS,
    BERSERKER_CRUSHING_LEAP_IMPACT_MS,
    BERSERKER_CRUSHING_LEAP_TRAVEL_MS,
    PALADIN_SHIELD_CHARGE_TRAVEL_MS,
    WARLOCK_SOUL_EXCHANGE_TRAVEL_MS,
)
def handle_act_three_key_event(event, game_state):
    if game_state.upgrade_altar_menu_open:
        if event.key == pygame.K_ESCAPE:
            game_state.upgrade_altar_menu_open = False
            game_state.upgrade_altar_menu_hovered_control = None
        return True

    if (
        game_state.player.archer_leap_origin is not None
        and game_state.player.archer_leap_started_at > 0
        and pygame.time.get_ticks()
        - game_state.player.archer_leap_started_at
        < ARCHER_LEAP_DURATION_MS
    ):
        return True
    if (
        game_state.player.berserker_crushing_leap_origin
        is not None
        and game_state.player.berserker_crushing_leap_started_at
        > 0
        and pygame.time.get_ticks()
        - game_state.player.berserker_crushing_leap_started_at
        < (
            BERSERKER_CRUSHING_LEAP_TRAVEL_MS
            + BERSERKER_CRUSHING_LEAP_IMPACT_MS
        )
    ):
        return True
    
    if (
        game_state.player.paladin_shield_charge_origin
        is not None
        and game_state.player.paladin_shield_charge_started_at
        > 0
        and pygame.time.get_ticks()
        - game_state.player.paladin_shield_charge_started_at
        < PALADIN_SHIELD_CHARGE_TRAVEL_MS
    ):
        return True
    
    if (
        game_state.player.warlock_soul_exchange_player_origin
        is not None
        and game_state.player.warlock_soul_exchange_started_at
        > 0
        and pygame.time.get_ticks()
        - game_state.player.warlock_soul_exchange_started_at
        < WARLOCK_SOUL_EXCHANGE_TRAVEL_MS
    ):
        return True
    
    if event.key == pygame.K_ESCAPE and game_state.player.teleport_aiming:
        cancel_assassin_teleport(game_state)
        set_assassin_target_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.archer_empowered_shot_aiming
    ):
        cancel_archer_empowered_shot(game_state)
        set_archer_empowered_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.archer_leap_aiming
    ):
        cancel_archer_leap(game_state)
        set_archer_leap_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.archer_barrage_zone_aiming
    ):
        cancel_archer_barrage_zone(game_state)
        set_archer_barrage_zone_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.berserker_crushing_leap_aiming
    ):
        cancel_berserker_crushing_leap(game_state)
        set_berserker_crushing_leap_cursor()
        return True
    
    if event.key == pygame.K_ESCAPE and game_state.player.ultimate_aiming:
        cancel_assassin_ultimate(game_state)
        set_assassin_target_cursor()
        return True
    
    if (
        event.key in (pygame.K_1, pygame.K_KP1)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "archer"
    ):
        request_archer_empowered_shot(game_state)
        set_archer_empowered_cursor(
            game_state.player.archer_empowered_shot_aiming
        )
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.paladin_shield_charge_aiming
    ):
        cancel_paladin_shield_charge(game_state)
        set_paladin_shield_charge_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.warlock_curse_aiming
    ):
        cancel_warlock_curse(game_state)
        set_warlock_staff_cursor()
        return True
    
    if (
        event.key == pygame.K_ESCAPE
        and game_state.player.warlock_soul_exchange_aiming
    ):
        cancel_warlock_soul_exchange(game_state)
        set_warlock_staff_cursor()
        return True
    
    if (
        event.key in (pygame.K_2, pygame.K_KP2)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "archer"
    ):
        request_archer_leap(game_state)
        set_archer_leap_cursor(
            game_state.player.archer_leap_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_2, pygame.K_KP2)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "berserker"
    ):
        request_berserker_crushing_leap(game_state)
        set_berserker_crushing_leap_cursor(
            game_state.player.berserker_crushing_leap_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_1, pygame.K_KP1)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "paladin"
    ):
        request_paladin_holy_hand(
            game_state,
            pygame.time.get_ticks(),
        )
        return True
    
    if (
        event.key in (pygame.K_1, pygame.K_KP1)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "warlock"
    ):
        request_warlock_curse(game_state)
        set_warlock_staff_cursor(
            game_state.player.warlock_curse_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_1, pygame.K_KP1)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "summoner"
    ):
        release_summoner_familiar(game_state)
        set_summoner_staff_cursor()
        return True
    
    if (
        event.key in (pygame.K_2, pygame.K_KP2)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "warlock"
    ):
        request_warlock_soul_exchange(game_state)
        set_warlock_staff_cursor(
            game_state.player.warlock_soul_exchange_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_2, pygame.K_KP2)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "summoner"
    ):
        request_summoner_bond(game_state)
        return True
    
    if (
        event.key in (pygame.K_3, pygame.K_KP3)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "warlock"
    ):
        game_state.player.warlock_demon_form_active = not (
            game_state.player.warlock_demon_form_active
        )
        return True
    
    if (
        event.key in (pygame.K_3, pygame.K_KP3)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "summoner"
    ):
        request_summoner_true_form(game_state)
        return True
    
    if (
        event.key in (pygame.K_2, pygame.K_KP2)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "paladin"
    ):
        request_paladin_shield_charge(game_state)
        set_paladin_shield_charge_cursor(
            game_state.player.paladin_shield_charge_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_3, pygame.K_KP3)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "paladin"
    ):
        request_paladin_holy_shield(game_state)
        set_paladin_shield_charge_cursor()
        return True
    
    if (
        event.key in (pygame.K_3, pygame.K_KP3)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "archer"
    ):
        request_archer_barrage_zone(game_state)
        set_archer_barrage_zone_cursor(
            game_state.player.archer_barrage_zone_aiming
        )
        return True
    
    if (
        event.key in (pygame.K_3, pygame.K_KP3)
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "berserker"
    ):
        request_berserker_last_rage(game_state)
        set_berserker_crushing_leap_cursor(
            game_state.player.berserker_crushing_leap_aiming
        )
        return True
    
    if (
        event.key == pygame.K_2
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "assassin"
    ):
        request_assassin_teleport(game_state)
        set_assassin_target_cursor(
            "teleport"
            if game_state.player.teleport_aiming
            else None
        )
        return True
    
    if (
        event.key == pygame.K_3
        and FLOOR_CONFIGS[game_state.floor_index]["act"] == 3
        and game_state.player.subclass == "assassin"
    ):
        request_assassin_ultimate(game_state)
        set_assassin_target_cursor(
            "ultimate"
            if game_state.player.ultimate_aiming
            else None
        )
        return True
    
    if (
        event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        and game_state.player.ultimate_aiming
    ):
        if begin_assassin_ultimate(
            game_state,
            pygame.time.get_ticks(),
        ):
            set_assassin_target_cursor()
        return True
    
    if (
        game_state.player.teleport_aiming
        and game_state.player.teleport_target is None
    ):
        return True
    
    if (
        game_state.player.archer_leap_aiming
        and game_state.player.archer_leap_target is None
    ):
        return True
    
    if (
        game_state.player.berserker_crushing_leap_aiming
        and game_state.player.berserker_crushing_leap_target
        is None
    ):
        return True
    
    if game_state.player.ultimate_aiming:
        return True

    return False
