from acts.act_two.enemies.oracle.behavior import resolve_oracle_hit_reaction
from acts.act_three.npcs import advance_npc_dialog
from acts.act_three.shadow_step_trial import advance_trial_frame
from acts.act_three.settings import (
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
)
from presentation.layout import ACT_THREE_AWAKENING_END_MS
from systems.player_abilities import resolve_assassin_ultimate


def advance_act_three_frame(game_state, current_act, current_time, sounds):
    if current_act == 3:
        advance_trial_frame(game_state, current_time)
        advance_npc_dialog(game_state, current_time)
        sounds.update(game_state.player, current_time)

    if game_state.player.ultimate_animation_active:
        animation_duration = (
            ASSASSIN_ULTIMATE_PRELUDE_MS
            + len(game_state.player.ultimate_targets) * ASSASSIN_ULTIMATE_STEP_MS
            + ASSASSIN_ULTIMATE_OUTRO_MS
        )
        if (
            current_time - game_state.player.ultimate_animation_started_at
            >= animation_duration
        ):
            resolve_assassin_ultimate(
                game_state,
                resolve_oracle_hit_reaction,
                current_time,
            )
            game_state.player.ultimate_animation_active = False
            game_state.player.ultimate_animation_started_at = 0

    if (
        game_state.act_three_transition_open
        and game_state.act_three_transition_started_at == 0
    ):
        game_state.act_three_transition_started_at = current_time

    if not game_state.act_three_transition_open:
        return

    if game_state.act_three_visual_started_at == 0:
        return

    if (
        current_time - game_state.act_three_visual_started_at
        < ACT_THREE_AWAKENING_END_MS
    ):
        return

    game_state.act_three_transition_open = False
    if game_state.player.player_class in ("warrior", "rogue", "mage"):
        game_state.subclass_selection_open = True
    else:
        game_state.act_three_debug_class_selection_open = True


__all__ = ["advance_act_three_frame"]
