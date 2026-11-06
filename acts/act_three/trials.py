TRIAL_MAPS = {
    "assassin": "assets/maps/act_3/trials/assassin_shadow_step/assassin_shadow_step.tmx",
    "archer": "assets/maps/act_3/trials/archer_piercing_trial/archer_piercing_trial.tmx",
}


def trial_map_path(subclass):
    return TRIAL_MAPS.get(subclass, TRIAL_MAPS["assassin"])


def teleport_to_trial(game_state):
    from game.factories import create_floor_state
    from levels import FLOOR_CONFIGS

    if game_state.floor.presentation_act != 3:
        return "This command is only available in Act III."
    if game_state.floor_transition_started_at >= 0:
        return "Wait for the floor transition to finish."
    scene = game_state.act_three.awakening
    if game_state.subclass_selection_open or (
        scene is not None and scene.phase != "complete"
    ):
        return "Finish awakening and choose a subclass first."
    trial = game_state.floor.shadow_step_trial
    piercing_trial = game_state.floor.piercing_trial
    if piercing_trial is not None and (
        piercing_trial["phase"] == "opening" or piercing_trial["stage"] is not None
    ):
        return "Wait for the trial animation to finish."
    if trial is not None and (
        trial["phase"] == "opening" or trial.get("action_stage") is not None
    ):
        return "Wait for the trial animation to finish."

    target_index = next(
        (index for index, config in enumerate(FLOOR_CONFIGS)
         if config["act"] == 3 and config.get("tmx_room_sequence")),
        None,
    )
    if target_index is None:
        return "No trial floor is configured."
    floor = (
        game_state.floor if game_state.floor_index == target_index
        else game_state.visited_floors.get(target_index)
    )
    expected_archer = game_state.player.subclass == "archer"
    if floor is None or (floor.piercing_trial is not None) != expected_archer:
        floor = create_floor_state(
            target_index,
            trial_subclass=game_state.player.subclass,
        )
    if floor.trial_entrance is None:
        return "No trial entrance found on this floor."
    column, row = floor.trial_entrance
    destination = (column, row + 1)
    if not (
        0 <= destination[1] < len(floor.map)
        and 0 <= destination[0] < len(floor.map[destination[1]])
        and floor.map[destination[1]][destination[0]] == "."
    ):
        return "The cell outside the trial entrance is blocked."

    game_state.visited_floors[game_state.floor_index] = game_state.floor
    game_state.visited_floors[target_index] = floor
    game_state.floor_index = target_index
    game_state.floor = floor
    floor.player_column, floor.player_row = destination
    floor.visible_cells.clear()
    game_state.player.movement_origin = None
    game_state.player.movement_animation_started_at = 0
    game_state.player.teleport_camera_origin = None
    game_state.player.teleport_transition_started_at = 0
    game_state.player_attack_targets = []
    game_state.clear_events()
    return "Teleported to the trial entrance."
