def minimap_visible(game_state):
    state = game_state.act_three
    return (
        game_state.floor.presentation_act == 3
        and game_state.player.health > 0
        and not game_state.game_won
        and game_state.floor_transition_started_at < 0
        and not game_state.act_three_transition_open
        and (state.awakening is None or state.awakening.phase == "complete")
    )


def map_visible(game_state):
    from acts.act_three.trials.summoner import busy
    from acts.act_three.trials.warlock import is_spirit

    state = game_state.act_three
    return (
        minimap_visible(game_state)
        and not game_state.subclass_selection_open
        and not game_state.act_three_debug_class_selection_open
        and not state.altar_menu_open
        and not game_state.dialogue.active
        and not is_spirit(game_state.floor.curse_trial)
        and not busy(game_state.floor.summoner_trial)
        and not (game_state.floor.curse_trial is not None and game_state.floor.curse_trial["phase"] == "body_rite")
        and state.sidebar_tab == "closed"
        and state.npc_dialog_position is None
        and state.npc_menu_from_console is None
        and state.rune_menu is None
    )


def advance_map(game_state, current_time, blocked=False):
    state = game_state.act_three
    if blocked or not map_visible(game_state):
        state.map_open = False
        state.map_closing_at = -1
        state.map_drag_anchor = None
    elif state.map_closing_at >= 0 and current_time - state.map_closing_at >= 180:
        state.map_open = False
        state.map_closing_at = -1
