from dataclasses import dataclass

import pygame

from acts.act_three.movement import ACT_THREE_MOVEMENT_PROFILE
from acts.act_three.movement_timing import PLAYER_STEP_MS
from acts.act_two.turns import act_two_combat_is_active
from application.auto_movement import AUTO_MOVE_INTERVAL_MS, create_auto_move_event
from application.input_policy import (
    console_input_available,
    continuous_movement_input_available,
    gameplay_cutscene_active,
)
from application.movement_input import (
    DEFAULT_MOVEMENT_PROFILE,
    create_held_movement_event,
    sync_movement_scope,
)
from levels import FLOOR_CONFIGS
from presentation.cursors import set_warlock_staff_cursor
from systems.player_abilities import (
    paladin_sacred_ground_impact_ready,
    perform_paladin_sacred_ground,
)


@dataclass(frozen=True)
class FrameInputState:
    current_act: int
    continuous_movement_available: bool
    movement_profile: object
    menu_visual_theme: int
    active_menu_layouts: object
    console_available: bool


def prepare_frame_input(
    game_state,
    app_runtime,
    menu_state,
    menu_layouts,
    dev_console,
    movement_state,
    ground_item_window,
    act_one_sounds,
    act_two_sounds,
):
    current_act = game_state.floor.presentation_act
    console_available = console_input_available(app_runtime, game_state)
    if not console_available:
        dev_console.close()

    if movement_state.resonance_cursor_active and (
        current_act != 2
        or app_runtime.menu_open
        or game_state.player.health <= 0
        or game_state.floor_transition_started_at >= 0
    ):
        set_warlock_staff_cursor(False)
        movement_state.resonance_cursor_active = False

    current_time = pygame.time.get_ticks()
    if gameplay_cutscene_active(game_state):
        movement_state.reset_held_movement()
        movement_state.cancel_auto_move()
        movement_state.cancel_consumable_drag()

    continuous_movement_available = continuous_movement_input_available(
        app_runtime,
        game_state,
        dev_console.is_open,
        current_time,
    )
    ground_item_window.update(
        game_state,
        movement_state,
        continuous_movement_available,
        current_time,
        (
            act_one_sounds
            if current_act == 1
            else act_two_sounds if current_act == 2 else None
        ),
    )
    continuous_movement_available = (
        continuous_movement_available and not ground_item_window.is_open
    )

    if game_state.rune_selection_open or game_state.bloody_altar_open:
        movement_state.cancel_auto_move()
        movement_state.cancel_consumable_drag()

    movement_profile = (
        ACT_THREE_MOVEMENT_PROFILE
        if current_act == 3
        else DEFAULT_MOVEMENT_PROFILE
    )
    sync_movement_scope(
        movement_state,
        game_state.player,
        game_state.floor,
        movement_profile,
    )
    held_event = create_held_movement_event(
        movement_state,
        current_time,
        continuous_movement_available,
        act_two_combat_is_active(game_state),
        profile=movement_profile,
    )
    if held_event is not None:
        pygame.event.post(held_event)

    auto_move_event = create_auto_move_event(
        movement_state,
        game_state,
        current_time,
        continuous_movement_available,
        PLAYER_STEP_MS if current_act == 3 else AUTO_MOVE_INTERVAL_MS,
    )
    if auto_move_event is not None:
        pygame.event.post(auto_move_event)

    menu_visual_theme = (
        FLOOR_CONFIGS[game_state.floor_index]["act"]
        if app_runtime.game_started
        else menu_state.menu_theme
    )

    if (
        app_runtime.game_started
        and not app_runtime.menu_open
        and current_act == 3
        and paladin_sacred_ground_impact_ready(game_state, current_time)
        and perform_paladin_sacred_ground(game_state, current_time)
    ):
        pygame.event.post(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_SPACE,
                paladin_sacred_ground_turn=True,
            )
        )

    barrage_turn = game_state.act_three.barrage_turn
    if (
        current_act == 3
        and app_runtime.game_started
        and not app_runtime.menu_open
        and barrage_turn is not None
        and current_time >= barrage_turn.ready_at
    ):
        pygame.event.post(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_UNKNOWN,
                archer_barrage_resume=True,
            )
        )

    return FrameInputState(
        current_act,
        continuous_movement_available,
        movement_profile,
        menu_visual_theme,
        menu_layouts[menu_visual_theme],
        console_available,
    )


__all__ = ["FrameInputState", "prepare_frame_input"]
