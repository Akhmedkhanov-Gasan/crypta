import pygame


def handle_dialogue_event(game_state, event, current_time):
    state = game_state.dialogue
    if not state.active:
        return False
    pressed = (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_SPACE
        and not getattr(event, "repeat", False)
    ) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
    if not pressed:
        return False
    if not state.revealed and state.elapsed < state.typing_end:
        state.revealed = True
        state.ready_at = max(state.ready_at, current_time + 2200)
        return True
    target = state.end
    track = state.track
    if track == "act_two_awakening":
        game_state.class_transition_started_at = current_time - target
    elif track == "act_two_choice":
        game_state.class_selection_choice_started_at = current_time - target
    elif track.startswith("act_three_awakening:"):
        scene = game_state.act_three.awakening
        scene.elapsed = target
        scene.updated_at = current_time
    elif track == "act_one_intro":
        game_state.act_one_intro.elapsed = target
        game_state.act_one_intro.updated_at = current_time
    elif track == "warden_intro":
        game_state.floor.act_one_warden_intro.elapsed = target
        game_state.floor.act_one_warden_intro.updated_at = current_time
    elif track == "oracle_intro":
        game_state.floor.oracle_intro.elapsed = target
        game_state.floor.oracle_intro.updated_at = current_time
    elif track == "oracle_phase":
        game_state.floor.oracle_phase_transition.elapsed = target
        game_state.floor.oracle_phase_transition.updated_at = current_time
    elif track == "act_one_death":
        scene = game_state.act_one_death_scene
        delta = target - (current_time - scene.started_at)
        scene.started_at -= delta
        game_state.player.death_animation_started_at -= delta
    elif track == "act_three_death":
        game_state.player.death_animation_started_at = current_time - target
    else:
        return False
    state.completed_until = target
    state.ready_at = -1
    state.start = -1
    state.end = -1
    return True

