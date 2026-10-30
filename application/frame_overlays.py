from acts.act_one.presentation.death_scene import draw_act_one_death_overlay
from acts.act_one.settings import FLOOR_INTRO_SUBTITLES
from acts.act_two.presentation.cutscene_skip import draw_cutscene_skip
from levels import FLOOR_CONFIGS
from presentation.floor_progress import roman_number, tower_floor_number
from acts.act_three.awakening.presentation import draw_awakening_scene
from acts.act_three.awakening.selection import draw_selection
from presentation.screens import (
    draw_act_three_awakening,
    draw_act_three_debug_class_selection,
    draw_class_selection_screen,
    draw_floor_transition,
)


def draw_frame_overlays(
    screen,
    game_state,
    current_act,
    current_time,
    act_one_fonts,
    act_two_fonts,
    act_three_fonts,
    act_two_sprites,
    act_three_transition_assets,
    cutscene_skip,
    dev_console,
    mouse_position,
    act_two_camera=None,
):
    if game_state.class_selection_open:
        draw_class_selection_screen(
            screen,
            act_two_fonts["title"],
            act_two_fonts["heading"],
            act_two_fonts["heading"],
            act_two_fonts["text"],
            act_two_sprites,
            current_time - game_state.class_transition_started_at,
            mouse_position,
            game_state.class_selection_choice,
            (
                None
                if game_state.class_selection_choice_started_at == 0
                else (
                    current_time
                    - game_state.class_selection_choice_started_at
                )
            ),
            attribute_ranks=(
                game_state.class_selection_preview_ranks
                if game_state.class_selection_choice is not None
                else game_state.player.attribute_ranks
            ),
        )

    if game_state.act_three_debug_class_selection_open:
        draw_act_three_debug_class_selection(
            screen,
            act_three_fonts["title"],
            act_three_fonts["heading"],
            act_three_fonts["text"],
            mouse_position,
        )
    elif game_state.act_three_transition_open:
        if game_state.act_three.awakening is not None:
            draw_awakening_scene(screen, game_state, act_three_fonts, act_two_fonts, act_two_camera)
        else:
            draw_act_three_awakening(
                screen,
                act_three_transition_assets,
                act_three_fonts["narrative"],
                current_time - game_state.act_three_transition_started_at,
                (
                    None
                    if game_state.act_three_visual_started_at == 0
                    else current_time - game_state.act_three_visual_started_at
                ),
                game_state.player.player_class,
            )
    elif game_state.subclass_selection_open:
        draw_selection(
            screen,
            act_three_fonts["title"],
            act_three_fonts["heading"],
            act_three_fonts["text"],
            act_three_transition_assets,
            mouse_position,
            game_state.player.subclass,
            game_state.player.player_class,
        )

    if (
        game_state.floor_transition_started_at >= 0
        and game_state.floor_transition_target_index is not None
    ):
        target_floor_config = FLOOR_CONFIGS[
            game_state.floor_transition_target_index
        ]
        target_act = target_floor_config["act"]
        target_act_floor = target_floor_config["act_floor"]
        transition_title_font = (
            act_one_fonts["title"]
            if target_act == 1
            else act_two_fonts["title"]
            if target_act == 2
            else act_three_fonts["title"]
        )
        transition_text_font = (
            act_one_fonts["interface"]
            if target_act == 1
            else act_two_fonts["text"]
            if target_act == 2
            else act_three_fonts["text"]
        )
        draw_floor_transition(
            screen,
            transition_title_font,
            transition_text_font,
            current_time - game_state.floor_transition_started_at,
            roman_number(
                tower_floor_number(
                    game_state.floor_transition_target_index
                )
            ),
            (
                FLOOR_INTRO_SUBTITLES.get(target_act_floor, "")
                if target_act == 1
                else "THE DESCENT CONTINUES"
            ),
        )

    draw_cutscene_skip(screen, cutscene_skip, current_time)
    dev_console.draw(screen)

    if current_act == 1 and game_state.player.health <= 0:
        draw_act_one_death_overlay(
            screen,
            game_state,
            current_time,
            mouse_position,
        )


__all__ = ["draw_frame_overlays"]
