from acts.act_one.camera import update_act_one_camera
from acts.act_one.presentation.death_scene import begin_act_one_death
from acts.act_one.presentation.intro import (
    act_one_intro_camera_offset,
    update_act_one_intro,
)
from acts.act_one.visibility import update_act_one_visibility
from acts.act_one.warden_intro import (
    update_warden_intro,
    warden_intro_camera_focus,
)


def advance_act_one_scenes(game_state, current_time, enabled):
    update_act_one_intro(
        game_state,
        current_time,
        enabled=enabled,
    )
    update_warden_intro(
        game_state,
        current_time,
        enabled=enabled,
    )

    if enabled:
        begin_act_one_death(game_state, current_time)


def refresh_act_one_visibility(game_state):
    if game_state.floor.presentation_act == 1:
        update_act_one_visibility(game_state.floor)


def update_act_one_view(camera, game_state, current_time):
    if game_state.floor.presentation_act != 1:
        return

    update_act_one_camera(
        camera,
        game_state.floor.map,
        game_state.floor.player_column,
        game_state.floor.player_row,
        game_state.floor_index,
        current_time,
        focus_offset_y=act_one_intro_camera_offset(
            getattr(game_state, "act_one_intro", None)
        ),
        focus_position=warden_intro_camera_focus(
            game_state.floor
        ),
    )
