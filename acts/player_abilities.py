import pygame

from game.combat_log import add_log_message
from game.events import GameEvent, GameEventType

from acts.act_three.abilities.archer_barrage_zone import (
    place_archer_barrage_zone,
)
from acts.act_three.abilities.archer_piercing_shot import (
    perform_archer_piercing_shot,
)
from acts.act_three.abilities.mage import (
    is_valid_act_three_arcane_burst_target,
)
from acts.act_three.combat.archer_aim import archer_shot_direction
from presentation.cursors import (
    set_archer_attack_cursor,
    set_archer_barrage_zone_cursor,
    set_archer_empowered_cursor,
    set_archer_leap_cursor,
    set_assassin_target_cursor,
    set_berserker_crushing_leap_cursor,
    set_paladin_shield_charge_cursor,
    set_summoner_staff_cursor,
    set_warlock_curse_cursor,
    set_warlock_staff_cursor,
)
from systems.player_abilities import (
    assassin_teleport_facing_direction,
    cast_directional_ability,
    cast_mage_arcane_burst,
    perform_archer_empowered_shot,
    perform_berserker_crushing_leap,
    perform_paladin_shield_charge,
    perform_warlock_curse,
)
from systems.player_combat import (
    perform_archer_attack,
    perform_mage_resonance_attack,
    perform_summoner_attack,
    perform_warlock_attack,
)


def resolve_targeted_player_ability(
    game_state,
    event,
    current_act,
    direction,
    mage_ability_target,
    resonance_target,
    directional_ability_cast,
    rogue_ability_activated,
    hit_reaction,
):
    """Resolve an already selected class/subclass action.

    ``None`` means no targeted ability was pending. A boolean means an
    ability was handled and reports whether it consumed the player's turn.
    """
    player = game_state.player

    if player.warlock_curse_target is not None:
        acted = perform_warlock_curse(
            game_state,
            player.warlock_curse_target,
            pygame.time.get_ticks(),
        )
        set_warlock_curse_cursor()
        return acted

    if player.warlock_attack_target is not None:
        target = player.warlock_attack_target
        player.warlock_attack_target = None
        acted = perform_warlock_attack(game_state, target, hit_reaction)
        if acted:
            player.attack_animation_started_at = pygame.time.get_ticks()
        set_warlock_staff_cursor()
        return acted

    if player.summoner_attack_target is not None:
        target = player.summoner_attack_target
        player.summoner_attack_target = None
        acted = perform_summoner_attack(game_state, target, hit_reaction)
        if acted:
            player.attack_animation_started_at = pygame.time.get_ticks()
        set_summoner_staff_cursor()
        return acted

    if player.paladin_shield_charge_target is not None:
        acted = perform_paladin_shield_charge(
            game_state,
            pygame.time.get_ticks(),
            hit_reaction,
        )
        if acted:
            set_paladin_shield_charge_cursor()
        return acted

    if player.berserker_crushing_leap_target is not None:
        acted = perform_berserker_crushing_leap(
            game_state,
            pygame.time.get_ticks(),
            hit_reaction,
        )
        if acted:
            set_berserker_crushing_leap_cursor()
        return acted

    if player.archer_leap_target is not None:
        target = player.archer_leap_target
        origin = (game_state.floor.player_column, game_state.floor.player_row)
        started_at = pygame.time.get_ticks()
        game_state.floor.player_column, game_state.floor.player_row = target
        player.archer_leap_target = None
        player.archer_leap_aiming = False
        player.archer_leap_charge = 0
        player.archer_leap_origin = origin
        player.archer_leap_started_at = started_at
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor="hero",
                origin=origin,
                destination=target,
                data={"kind": "archer_leap"},
            )
        )
        add_log_message(
            game_state.combat_log,
            "The archer leaps backward.",
            category="ability",
        )
        set_archer_leap_cursor()
        return True

    if player.archer_empowered_shot_target is not None:
        target = player.archer_empowered_shot_target
        player.archer_empowered_shot_target = None
        acted = perform_archer_empowered_shot(
            game_state,
            target,
            hit_reaction,
        )
        if acted:
            player.attack_animation_started_at = pygame.time.get_ticks()
            player.archer_empowered_shot_started_at = pygame.time.get_ticks()
        set_archer_empowered_cursor()
        return acted

    if getattr(event, "archer_barrage_commit", False):
        acted = place_archer_barrage_zone(game_state)
        if acted:
            set_archer_barrage_zone_cursor()
        return acted

    if player.archer_piercing_target is not None:
        target = player.archer_piercing_target
        player.archer_piercing_target = None
        player.facing_direction = archer_shot_direction(
            (game_state.floor.player_column, game_state.floor.player_row),
            target,
        )
        started_at = pygame.time.get_ticks()
        acted = perform_archer_piercing_shot(
            game_state,
            target,
            started_at,
            hit_reaction,
        )
        if acted:
            player.attack_animation_started_at = started_at
        return acted

    if player.archer_attack_target is not None:
        target = player.archer_attack_target
        player.archer_attack_target = None
        player.facing_direction = archer_shot_direction(
            (game_state.floor.player_column, game_state.floor.player_row),
            target,
        )
        acted = perform_archer_attack(game_state, target, hit_reaction)
        if acted:
            player.attack_animation_started_at = pygame.time.get_ticks()
        set_archer_attack_cursor()
        return acted

    if rogue_ability_activated:
        return True

    if player.teleport_target is not None:
        target = player.teleport_target
        origin = (game_state.floor.player_column, game_state.floor.player_row)
        player.facing_direction = assassin_teleport_facing_direction(
            origin,
            target,
        )
        game_state.floor.player_column, game_state.floor.player_row = target
        player.teleport_target = None
        player.teleport_aiming = False
        set_assassin_target_cursor()
        player.teleport_charge = 0
        player.teleport_camera_origin = origin
        player.teleport_transition_started_at = pygame.time.get_ticks()
        game_state.emit(
            GameEvent(
                type=GameEventType.MOVE,
                actor="hero",
                origin=origin,
                destination=target,
                data={"kind": "teleport"},
            )
        )
        add_log_message(
            game_state.combat_log,
            "The assassin teleports through the shadows.",
            category="ability",
        )
        return True

    if resonance_target is not None:
        acted = perform_mage_resonance_attack(
            game_state,
            resonance_target,
            hit_reaction,
        )
        if acted:
            started_at = pygame.time.get_ticks()
            player.attack_animation_started_at = started_at
            player.act_two.ability_effect_started_at = started_at
        return acted

    if mage_ability_target is not None:
        effect_state = (
            player.act_three.mage_arcane_burst
            if current_act == 3
            else player.act_two
        )
        acted = cast_mage_arcane_burst(
            game_state,
            mage_ability_target,
            hit_reaction,
            effect_state=effect_state,
            target_validator=(
                is_valid_act_three_arcane_burst_target
                if current_act == 3
                else None
            ),
        )
        if acted:
            started_at = pygame.time.get_ticks()
            player.attack_animation_started_at = started_at
            effect_state.ability_effect_started_at = started_at
            if current_act == 3:
                player.act_three.mage_arcane_burst.preview_target = None
        return acted

    if directional_ability_cast:
        acted = cast_directional_ability(
            game_state,
            direction[0],
            direction[1],
            hit_reaction,
        )
        if acted:
            started_at = pygame.time.get_ticks()
            player.attack_animation_started_at = started_at
            if current_act == 2:
                player.act_two.ability_effect_started_at = started_at
                player.act_two.ability_effect_direction = direction
        return acted

    return None


__all__ = ["resolve_targeted_player_ability"]
