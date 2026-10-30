from acts.act_one.presentation.intro import act_one_intro_active
from acts.act_one.warden_intro import warden_intro_active
from acts.act_three.abilities.paladin_sacred_ground import (
    paladin_sacred_ground_cast_active,
)
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_cutscene_active,
)


def console_input_available(app_runtime, game_state):
    if app_runtime.menu_open:
        return True

    return (
        app_runtime.game_started
        and game_state.player.health > 0
        and not game_state.game_won
        and game_state.floor_transition_started_at < 0
        and not game_state.class_selection_open
        and not game_state.upgrade_screen_open
        and not game_state.subclass_selection_open
        and not game_state.act_three_transition_open
        and not game_state.act_three_debug_class_selection_open
        and not oracle_cutscene_active(game_state.floor)
        and not warden_intro_active(game_state.floor)
    )


def gameplay_cutscene_active(game_state):
    return (
        game_state.act_three_transition_open
        or oracle_cutscene_active(game_state.floor)
        or act_one_intro_active(game_state)
        or warden_intro_active(game_state.floor)
    )


def act_one_cutscene_active(game_state):
    return (
        act_one_intro_active(game_state)
        or warden_intro_active(game_state.floor)
    )


def continuous_movement_input_available(
    app_runtime,
    game_state,
    dev_console_open,
    current_time,
):
    player = game_state.player
    return (
        app_runtime.game_started
        and not app_runtime.menu_open
        and not dev_console_open
        and game_state.floor_transition_started_at < 0
        and not game_state.class_selection_open
        and not game_state.upgrade_screen_open
        and not game_state.rune_selection_open
        and not game_state.bloody_altar_open
        and not game_state.subclass_selection_open
        and not game_state.act_three_transition_open
        and not game_state.act_three_debug_class_selection_open
        and not game_state.upgrade_altar_menu_open
        and game_state.act_three.npc_dialog_position is None
        and not player.directional_ability_aiming
        and not player.act_two.fire_bomb_aiming
        and player.act_two.scroll_aiming_kind is None
        and not player.teleport_aiming
        and not player.ultimate_aiming
        and not player.ultimate_animation_active
        and not player.archer_empowered_shot_aiming
        and not player.archer_leap_aiming
        and not player.archer_barrage_zone_aiming
        and not player.berserker_crushing_leap_aiming
        and not player.paladin_shield_charge_aiming
        and not paladin_sacred_ground_cast_active(player, current_time)
        and not player.warlock_curse_aiming
        and player.health > 0
        and not game_state.game_won
        and not game_state.trade_screen_open
        and not gameplay_cutscene_active(game_state)
    )
