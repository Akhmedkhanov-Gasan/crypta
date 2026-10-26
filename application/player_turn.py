from dataclasses import dataclass

import pygame

from acts.act_one.player_actions import resolve_act_one_player_action
from acts.act_three.player_actions import resolve_act_three_player_action
from acts.act_three.turns import resume_barrage_turn
from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction
from acts.act_two.player_actions import resolve_act_two_action_request
from acts.act_two.traps import advance_spike_traps
from acts.act_two.treasury import update_treasury_trial
from acts.act_two.turns import complete_act_two_player_turn
from acts.turns import resolve_enemy_turn
from application.directional_input import WAIT_KEYS
from application.turn_feedback import present_turn_feedback
from game.combat_log import add_log_message
from systems.player_abilities import (
    advance_berserker_last_rage,
    advance_paladin_sacred_ground,
    advance_warlock_curses,
    advance_warlock_demon_form,
    resolve_paladin_sacred_ground,
)


@dataclass(frozen=True)
class PlayerTurnResult:
    player_acted: bool
    movement_blocked: bool = False


def _resolve_act_action(
    game_state,
    current_act,
    event,
    direction,
    act_two_action_request,
    mage_ability_target,
    directional_ability_cast,
    rogue_ability_activated,
    stunned_action,
    barrage_resume,
    final_act_one_floor,
    movement_state,
    act_two_sounds,
):
    if barrage_resume:
        return PlayerTurnResult(player_acted=True)
    if stunned_action:
        game_state.player.stun_turns -= 1
        add_log_message(
            game_state.combat_log,
            "The hero loses a turn recovering from the stun.",
            category="debuff",
        )
        return PlayerTurnResult(player_acted=True)

    if current_act == 1:
        action = resolve_act_one_player_action(
            game_state,
            event.key,
            direction,
            pygame.time.get_ticks(),
            final_act_one_floor,
            resolve_oracle_hit_reaction,
        )
    elif current_act == 2:
        action = resolve_act_two_action_request(
            game_state,
            event,
            direction,
            act_two_action_request,
            directional_ability_cast,
            rogue_ability_activated,
            final_act_one_floor,
            resolve_oracle_hit_reaction,
        )
        if action.reset_held_movement:
            movement_state.reset_held_movement()
        if action.trader_sound is not None:
            act_two_sounds.play_ui_sound(action.trader_sound)
    else:
        action = resolve_act_three_player_action(
            game_state,
            event,
            direction,
            mage_ability_target,
            directional_ability_cast,
            rogue_ability_activated,
            final_act_one_floor,
            resolve_oracle_hit_reaction,
        )

    if action.movement_blocked:
        movement_state.cancel_auto_move()
        return PlayerTurnResult(
            player_acted=False,
            movement_blocked=True,
        )
    return PlayerTurnResult(player_acted=action.player_acted)


def _complete_non_act_two_turn(
    game_state,
    current_act,
    event,
    player_position_before_action,
    rogue_ability_activated,
    barrage_resume,
    movement_state,
    movement_profile,
    act_one_sounds,
    act_two_sounds,
    act_three_sounds,
):
    if not barrage_resume:
        game_state.player.familiar_turn_started_at = pygame.time.get_ticks()
        advance_spike_traps(game_state)
        update_treasury_trial(game_state)

    if game_state.player.health > 0:
        if barrage_resume:
            resume_barrage_turn(game_state)
        else:
            resolve_enemy_turn(
                game_state,
                player_position_before_action,
                rogue_ability_activated,
            )

    if game_state.act_three.barrage_turn is None:
        if current_act == 3 and not getattr(
            event,
            "paladin_sacred_ground_turn",
            False,
        ):
            resolve_paladin_sacred_ground(game_state)
        update_treasury_trial(game_state)
        advance_berserker_last_rage(game_state)
        advance_paladin_sacred_ground(game_state)
        advance_warlock_curses(game_state)
        advance_warlock_demon_form(game_state)

    if game_state.act_three.barrage_turn is not None:
        movement_state.cancel_auto_move()
        movement_state.reset_held_movement()

    present_turn_feedback(
        game_state,
        current_act,
        pygame.time.get_ticks(),
        movement_state,
        movement_profile,
        act_one_sounds,
        act_two_sounds,
        act_three_sounds,
    )


def resolve_player_turn(
    game_state,
    current_act,
    event,
    direction,
    act_two_action_request,
    mage_ability_target,
    directional_ability_cast,
    rogue_ability_activated,
    stunned_action,
    barrage_resume,
    automatic_movement,
    final_act_one_floor,
    movement_state,
    movement_profile,
    act_one_sounds,
    act_two_sounds,
    act_three_sounds,
) -> PlayerTurnResult:
    player_position_before_action = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    player_waited = event.key in WAIT_KEYS
    if current_act == 1 and not player_waited:
        game_state.player.act_one_wait_effect_started_at = -1
    if current_act == 2 and not player_waited:
        game_state.player.act_two.wait_effect_started_at = -1
    game_state.player_attack_targets = []

    result = _resolve_act_action(
        game_state,
        current_act,
        event,
        direction,
        act_two_action_request,
        mage_ability_target,
        directional_ability_cast,
        rogue_ability_activated,
        stunned_action,
        barrage_resume,
        final_act_one_floor,
        movement_state,
        act_two_sounds,
    )
    if result.movement_blocked:
        return result

    if result.player_acted and not barrage_resume:
        game_state.run_stats.turns_taken += 1
    elif automatic_movement:
        movement_state.cancel_auto_move()

    if result.player_acted and current_act == 2:
        complete_act_two_player_turn(
            game_state,
            player_position_before_action,
            rogue_ability_activated,
            movement_state,
            act_two_sounds,
            pygame.time.get_ticks(),
        )
    elif result.player_acted:
        _complete_non_act_two_turn(
            game_state,
            current_act,
            event,
            player_position_before_action,
            rogue_ability_activated,
            barrage_resume,
            movement_state,
            movement_profile,
            act_one_sounds,
            act_two_sounds,
            act_three_sounds,
        )
    return result


__all__ = ["PlayerTurnResult", "resolve_player_turn"]
