from dataclasses import dataclass

import pygame

from acts.act_three.runtime import (
    advance_act_three_transition,
    choose_subclass,
    create_act_three_debug_transition,
)
from acts.act_two.class_selection import apply_act_two_class_selection
from game.factories import create_game_state


@dataclass(frozen=True)
class ActThreeFlowInputResult:
    handled: bool
    game_state: object


def handle_act_three_flow_key(
    event,
    game_state,
    loading,
    audio_runtime,
    app_runtime,
    barrage_resume,
):
    if game_state.act_three_debug_class_selection_open:
        player_class = {
            pygame.K_1: "warrior",
            pygame.K_KP1: "warrior",
            pygame.K_2: "rogue",
            pygame.K_KP2: "rogue",
            pygame.K_3: "mage",
            pygame.K_KP3: "mage",
        }.get(event.key)
        if player_class is not None:
            if game_state.act_three_test_mode:
                apply_act_two_class_selection(game_state.player, player_class)
                game_state.act_three_debug_class_selection_open = False
                game_state.subclass_selection_open = True
            else:
                game_state = create_act_three_debug_transition(
                    player_class,
                    pygame.time.get_ticks(),
                )
        return ActThreeFlowInputResult(True, game_state)

    if game_state.act_three_transition_open:
        if event.key in (
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            advance_act_three_transition(game_state, pygame.time.get_ticks())
        return ActThreeFlowInputResult(True, game_state)

    if game_state.subclass_selection_open:
        subclass_keys = _subclass_keys(game_state.player.player_class)
        subclass = subclass_keys.get(event.key)
        if game_state.player.subclass is None and subclass is not None:
            loading.run(choose_subclass, game_state, subclass)
        return ActThreeFlowInputResult(True, game_state)

    if (
        game_state.player.health <= 0 or game_state.game_won
    ) and not barrage_resume:
        if event.key == pygame.K_r:
            audio_runtime.reset()
            game_state = loading.run(create_game_state)
            app_runtime.progress_tracking_enabled = True
        return ActThreeFlowInputResult(True, game_state)

    return ActThreeFlowInputResult(False, game_state)


def _subclass_keys(player_class):
    if player_class == "rogue":
        return {
            pygame.K_1: "assassin",
            pygame.K_KP1: "assassin",
            pygame.K_2: "archer",
            pygame.K_KP2: "archer",
        }
    if player_class == "mage":
        return {
            pygame.K_1: "warlock",
            pygame.K_KP1: "warlock",
            pygame.K_2: "summoner",
            pygame.K_KP2: "summoner",
        }
    return {
        pygame.K_1: "berserker",
        pygame.K_KP1: "berserker",
        pygame.K_2: "paladin",
        pygame.K_KP2: "paladin",
    }


__all__ = ["ActThreeFlowInputResult", "handle_act_three_flow_key"]
