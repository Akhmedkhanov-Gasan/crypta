import pygame

from acts.act_three.abilities.catalog import get_subclass_definition
from acts.act_three.abilities.progression import unlock_ability_slot
from acts.act_three.piercing_trial import set_cell
from acts.act_three.trials import teleport_to_trial


def complete_trial(game_state):
    subclass = game_state.player.subclass
    fields = {"assassin": "shadow_step_trial", "archer": "piercing_trial", "berserker": "crushing_trial", "paladin": "shield_trial", "warlock": "curse_trial", "summoner": "summoner_trial"}
    if subclass not in fields:
        return "No trial is available for this subclass."
    result = teleport_to_trial(game_state)
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
        from acts.act_three.summoner_trial import reset_scene, finish, sync_occupancy, detach_familiar

        reset_scene(trial)
        trial.update(side=1, parts=[1, 1, 1], active=True)
        detach_familiar(game_state, trial)
        sync_occupancy(floor)
        floor.player_column, floor.player_row = trial["starts"][1]
        finish(game_state, now)
        destination = trial["starts"][1]
    else:
        from acts.act_three.curse_trial import return_to_body

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
