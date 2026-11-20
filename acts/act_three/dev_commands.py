from acts.act_three.abilities import (
    get_subclass_definition,
    unlock_ability_slot,
)


ACT_THREE_CONSOLE_HELP = (
    "lantern - teleport to the Lantern Warden room entrance (Act III)",
    "blacksmith - teleport to the blacksmith room entrance (Act III, floor 9)",
    "trialwin - complete your trial and preview the unlock effect (repeatable)",
    "trial - teleport to your class trial entrance (Act III)",
    "wake3[_warrior|_rogue|_mage] - jump to the post-Oracle awakening scene",
    "skills - unlock all abilities and disable charges (Act III)",
)


def execute_act_three_console_command(
    game_state,
    parts,
    close_console=None,
    request_debug_jump=None,
):
    name = parts[0]
    if name in ("lantern", "blacksmith"):
        if len(parts) != 1:
            return f"Usage: {name}"
        room_name, label = (
            ("lantern_warden_room.tmx", "Lantern Warden")
            if name == "lantern" else ("blacksmith_room.tmx", "Blacksmith")
        )
        result = _teleport_to_room(game_state, room_name, label)
        if result == f"Teleported to the {label} room entrance." and close_console is not None:
            close_console()
        return result
    if name == "trialwin":
        if len(parts) != 1:
            return "Usage: trialwin"
        result = _complete_trial(game_state)
        if result == "Trial completion effect started." and close_console is not None:
            close_console()
        return result

    if name == "trial":
        if len(parts) != 1:
            return "Usage: trial"
        result = _teleport_to_trial(game_state)
        if result == "Teleported to the trial entrance." and close_console is not None:
            close_console()
        return result

    if name == "wake3":
        if len(parts) > 2 or (len(parts) == 2 and parts[1] not in ("warrior", "rogue", "mage")):
            return "Usage: wake3, wake3_warrior, wake3_rogue or wake3_mage"
        parent = parts[1] if len(parts) == 2 else game_state.player.player_class
        if parent not in ("warrior", "rogue", "mage"):
            parent = "rogue"
        request_debug_jump(f"act_three_awakening:{parent}")
        close_console()
        return f"Jumping to the post-Oracle awakening as {parent}."

    if name != "skills":
        return None

    if len(parts) != 1:
        return "Usage: skills"

    if game_state.floor.presentation_act != 3:
        return "This command is only available in Act III."

    player = game_state.player
    definition = get_subclass_definition(player.subclass)

    if definition is None:
        return "Choose an Act III subclass first."

    for slot in definition.abilities:
        unlock_ability_slot(player, slot)

    player.debug_unlimited_abilities = True

    return (
        f"All {definition.id} abilities unlocked "
        "with unlimited charges."
    )


def _teleport_to_room(game_state, room_name, label):
    from application.input_policy import gameplay_cutscene_active
    from game.factories import create_floor_state
    from levels import FLOOR_CONFIGS

    if game_state.floor.presentation_act != 3:
        return "This command is only available in Act III."
    if game_state.floor_transition_started_at >= 0 or gameplay_cutscene_active(game_state):
        return "Wait for the current scene to finish."
    if game_state.subclass_selection_open or not game_state.player.subclass:
        return "Choose an Act III subclass first."
    if game_state.player.act_three.mining is not None or game_state.act_three.npc_dialog_position is not None:
        return "Finish the current interaction first."
    if game_state.floor.trial_safe_cells and (game_state.floor.player_column, game_state.floor.player_row) in game_state.floor.trial_safe_cells:
        return "Leave the class trial before teleporting."
    target_index = next((index for index, config in enumerate(FLOOR_CONFIGS)
                         if config.get("act") == 3 and any(
                             path.endswith(room_name)
                             for path in config.get("required_room_paths", ()))), None)
    if target_index is None:
        return f"No {label} room is configured."
    floor = game_state.floor if game_state.floor_index == target_index else game_state.visited_floors.get(target_index)
    if floor is None:
        try:
            floor = create_floor_state(target_index, trial_subclass=game_state.player.subclass)
        except ValueError as error:
            return f"Could not generate the {label} floor: {error}"
    if room_name == "lantern_warden_room.tmx":
        destination = floor.lantern_encounter["entrance"] if floor.lantern_encounter is not None else None
    else:
        npc = next((npc for npc in floor.act_three_npcs if npc["type"] == "blacksmith"), None)
        destination = npc.get("room_entrance") if npc is not None else None
    if destination is None:
        return f"The {label} room is missing from this saved floor. Start a new run to regenerate it."
    if floor.map[destination[1]][destination[0]] != ".":
        return f"The {label} entrance is blocked."
    from logic import get_enemy_occupied_positions

    if any(enemy.health > 0 and destination in get_enemy_occupied_positions(enemy) for enemy in floor.enemies):
        return f"An enemy is blocking the {label} entrance."
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
    return f"Teleported to the {label} room entrance."


def _teleport_to_trial(game_state):
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
    crushing_trial = game_state.floor.crushing_trial
    shield_trial = game_state.floor.shield_trial
    from acts.act_three.trials.warlock import is_spirit

    from acts.act_three.trials.summoner import in_scene
    if in_scene(game_state.floor.summoner_trial) or (game_state.floor.summoner_trial is not None and game_state.floor.summoner_trial["phase"] == "opening"):
        return "Wait for the trial scene to finish."

    if is_spirit(game_state.floor.curse_trial) or (game_state.floor.curse_trial is not None and game_state.floor.curse_trial["phase"] == "body_rite"):
        return "Return to your body first."
    if shield_trial is not None and shield_trial["phase"] in ("completion", "opening", "awakening", "extinguishing"):
        return "Wait for the trial animation to finish."
    if crushing_trial is not None and crushing_trial["stage"] is not None:
        return "Wait for the trial animation to finish."
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
         if config["act"] == 3 and (config.get("trial_room") or config.get("tmx_room_sequence"))),
        None,
    )
    if target_index is None:
        return "No trial floor is configured."
    floor = (
        game_state.floor if game_state.floor_index == target_index
        else game_state.visited_floors.get(target_index)
    )
    expected_archer = game_state.player.subclass == "archer"
    expected_berserker = game_state.player.subclass == "berserker"
    expected_paladin = game_state.player.subclass == "paladin"
    expected_warlock = game_state.player.subclass == "warlock"
    expected_summoner = game_state.player.subclass == "summoner"
    if floor is None or (floor.piercing_trial is not None) != expected_archer or (floor.crushing_trial is not None) != expected_berserker or (floor.shield_trial is not None) != expected_paladin or (floor.curse_trial is not None) != expected_warlock or (floor.summoner_trial is not None) != expected_summoner:
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


def _complete_trial(game_state):
    import pygame

    from acts.act_three.trials.archer import set_cell

    subclass = game_state.player.subclass
    fields = {"assassin": "shadow_step_trial", "archer": "piercing_trial", "berserker": "crushing_trial", "paladin": "shield_trial", "warlock": "curse_trial", "summoner": "summoner_trial"}
    if subclass not in fields:
        return "No trial is available for this subclass."
    result = _teleport_to_trial(game_state)
    if result != "Teleported to the trial entrance.":
        return result
    floor = game_state.floor
    trial = getattr(floor, fields[subclass])
    if trial is None:
        return "No class trial was found."
    now = pygame.time.get_ticks()
    set_cell(floor, trial["door"], ".")
    if subclass == "assassin":
        from acts.act_three.settings import ASSASSIN_TELEPORT_CHARGES

        trial.update(phase="complete", action_stage=None, completion_fx_ms=trial["animation_ms"], activated={1, 2, 3}, seal_fx=[])
        game_state.player.teleport_charge = ASSASSIN_TELEPORT_CHARGES
        destination = trial["final"]
    elif subclass == "archer":
        trial.update(phase="complete", stage=None, completed=now, paths=[], activated={1, 2, 3}, destroyed_targets={1, 2, 3}, target_impacts=[])
        destination = trial["return"]
    elif subclass == "berserker":
        for rock in trial["rocks"]:
            set_cell(floor, rock["cell"], ".")
        for rock, cell in zip(trial["rocks"], trial["plates"]):
            rock["cell"] = cell
            set_cell(floor, cell, "#")
        trial["plate_levels"] = {cell: 1.0 for cell in trial["plates"]}
        destination = trial["player_start"]
        if floor.map[destination[1]][destination[0]] != ".":
            destination = trial["enter_zone"]
            set_cell(floor, destination, ".")
        trial.update(door_open=True, complete=True, active=True, stage="completion", completed=now, started=now, completion_origin=destination, hold=None)
    elif subclass == "paladin":
        destination = trial["cells"][10]
        trial.update(phase="completion", completed=now, completion_origin=destination, lights=[True] * 16, levels=[1.0] * 16, pulse={})
    elif subclass == "summoner":
        from acts.act_three.trials.summoner import reset_scene, finish, sync_occupancy, detach_familiar

        reset_scene(trial)
        trial.update(side=1, parts=[1, 1, 1], active=True)
        detach_familiar(game_state, trial)
        sync_occupancy(floor)
        floor.player_column, floor.player_row = trial["starts"][1]
        finish(game_state, now)
        destination = trial["starts"][1]
    else:
        from acts.act_three.trials.warlock import return_to_body

        trial.update(completed=now, reward_granted=False)
        return_to_body(game_state, trial)
        destination = trial["start"]
    floor.player_column, floor.player_row = destination
    if subclass != "warlock":
        unlock_ability_slot(game_state.player, "q")
        game_state.player.ability_slot_charges["q"] = get_subclass_definition(subclass).abilities["q"].charge_required
    player = game_state.player
    player.movement_origin = None
    player.movement_animation_started_at = 0
    player.teleport_camera_origin = None
    player.teleport_transition_started_at = 0
    player.archer_basic_aiming = False
    player.archer_piercing_aiming = False
    player.paladin_shield_charge_aiming = False
    player.berserker_crushing_leap_aiming = False
    floor.visible_cells.clear()
    game_state.player_attack_targets = []
    game_state.clear_events()
    from acts.act_three.presentation.camera import snap_act_three_camera

    snap_act_three_camera(floor, now)
    return "Trial completion effect started."
