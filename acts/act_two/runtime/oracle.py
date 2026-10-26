from game.state import GameState

from acts.act_two.enemies.oracle.combat import update_oracle_combat
from acts.act_two.enemies.oracle.gate import update_oracle_gate
from acts.act_two.presentation.bosses.oracle_death import update_oracle_death
from acts.act_two.presentation.bosses.oracle_intro import update_oracle_intro
from acts.act_two.presentation.bosses.oracle_phase_transition import (
    oracle_phase_transition_active,
    update_oracle_phase_transition,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    update_oracle_phase_two,
)
from acts.act_two.visibility import update_act_two_visibility


def advance_oracle_runtime(
    game_state: GameState,
    camera,
    current_time,
    sounds,
    music_volume,
    input_state,
):
    update_oracle_intro(game_state, camera, current_time)
    update_oracle_phase_transition(
        game_state,
        camera,
        current_time,
        sounds,
        music_volume,
    )
    update_oracle_phase_two(game_state, current_time, sounds)
    update_oracle_death(
        game_state,
        camera,
        current_time,
        sounds,
        music_volume,
    )

    interrupted_player = False
    if not oracle_phase_transition_active(game_state.floor):
        interrupted_player = update_oracle_combat(
            game_state,
            current_time,
            sounds,
        )
    if interrupted_player:
        input_state.cancel_auto_move()

    update_oracle_gate(game_state.floor, current_time)
    update_act_two_visibility(game_state.floor)
    return interrupted_player


__all__ = ["advance_oracle_runtime"]
