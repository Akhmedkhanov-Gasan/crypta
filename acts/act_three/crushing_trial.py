from copy import deepcopy

import pygame

from acts.act_three.events import GameEvent, GameEventType
from acts.act_three.piercing_trial import set_cell
from systems.grid_geometry import can_reach_adjacent_cell


PUSH_MS = 420
HOLD_MS = 900


def build_trial(markers, width, height, dungeon_map):
    if not markers.get("enter_zone") or not markers.get("crushing_trial_pressure_plate"):
        return None
    trial = {name: markers[name][0][0] for name in ("enter_zone", "player_start", "player_exit")}
    trial["rocks"] = [
        {"cell": cell, "variant": int(name.rsplit("_", 1)[1])}
        for name, values in markers.items() if name.startswith("crushing_trial_boulder_")
        for cell, _ in values
    ]
    trial["plates"] = [cell for cell, _ in markers["crushing_trial_pressure_plate"]]
    if len(trial["rocks"]) != len(trial["plates"]):
        raise ValueError("Crushing trial requires one boulder per plate")
    cells = [rock["cell"] for rock in trial["rocks"]]
    if len(set(cells)) != len(cells) or len(set(trial["plates"])) != len(trial["plates"]):
        raise ValueError("Crushing trial contains duplicate objects")
    for x, y in set(cells + trial["plates"] + list(trial[name] for name in ("enter_zone", "player_start"))):
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Crushing trial object requires free floor: {(x, y)}")
    x, y = trial["player_exit"]
    dungeon_map[y][x] = "."
    trial.update(initial=deepcopy(trial["rocks"]), active=False, complete=False,
                 stage=None, started=0, hold=None, plate_levels={cell: float(cell in cells) for cell in trial["plates"]}, last_frame=0)
    for x, y in cells:
        dungeon_map[y][x] = "#"
    return trial


def shift_trial(trial, offset):
    trial = deepcopy(trial)
    def shift(cell):
        return cell[0] + offset[0], cell[1] + offset[1]
    for key in ("enter_zone", "player_start", "player_exit"):
        trial[key] = shift(trial[key])
    for key in ("rocks", "initial"):
        for rock in trial[key]:
            rock["cell"] = shift(rock["cell"])
    trial["plates"] = [shift(cell) for cell in trial["plates"]]
    trial["plate_levels"] = {shift(cell): value for cell, value in trial["plate_levels"].items()}
    return trial


def teleport(game_state, cell):
    floor = game_state.floor
    floor.player_column, floor.player_row = cell
    game_state.player.movement_origin = None
    game_state.player.movement_animation_started_at = 0
    game_state.player.teleport_camera_origin = None
    game_state.player.teleport_transition_started_at = 0
    game_state.clear_events()


def handle_key(event, game_state):
    trial = game_state.floor.crushing_trial
    if trial is None:
        return False
    if trial["stage"] is not None:
        return event.key != pygame.K_ESCAPE
    return trial["active"] and not trial["complete"] and event.key in (pygame.K_t, pygame.K_q, pygame.K_e, pygame.K_f)


def handle_action(game_state, event, direction):
    floor = game_state.floor
    trial = floor.crushing_trial
    if trial is None:
        return None
    if trial["stage"] is not None:
        return False
    origin = (floor.player_column, floor.player_row)
    target = origin[0] + direction[0], origin[1] + direction[1]
    if not trial["active"]:
        if target != trial["enter_zone"]:
            return None
        if trial["complete"]:
            return False
        if game_state.player.subclass != "berserker" or not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
            return False
        trial.update(stage="transition", started=pygame.time.get_ticks(), destination=trial["player_start"], entering=True, transferred=False, hold=None)
        return False
    if target == trial["player_exit"]:
        if not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
            return False
        trial.update(stage="transition", started=pygame.time.get_ticks(), destination=(trial["enter_zone"][0], trial["enter_zone"][1] + 1), entering=False, transferred=False, hold=None)
        return False
    rock = next((rock for rock in trial["rocks"] if rock["cell"] == target), None)
    if rock is not None:
        if abs(direction[0]) + abs(direction[1]) != 1:
            return False
        destination = target[0] + direction[0], target[1] + direction[1]
        if destination in (trial["player_exit"], trial["enter_zone"]) or not can_reach_adjacent_cell(floor.map, target, destination, floor.barriers):
            return False
        if not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers, target_must_be_walkable=False):
            return False
        set_cell(floor, target, ".")
        set_cell(floor, destination, "#")
        rock["cell"] = destination
        trial.update(stage="push", started=pygame.time.get_ticks(), push_origin=target, push_target=destination)
    elif direction == (0, 0) or not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
        return False
    floor.player_column, floor.player_row = target
    game_state.player.movement_animation_started_at = pygame.time.get_ticks()
    game_state.emit(GameEvent(type=GameEventType.MOVE, actor="hero", origin=origin, destination=target))
    event.piercing_trial_turn = True
    return True


def advance_frame(game_state, now):
    floor = game_state.floor
    trial = floor.crushing_trial
    if trial is None:
        return
    dt = min(100, max(0, now - trial["last_frame"]))
    trial["last_frame"] = now
    if trial["stage"] == "completion":
        if now - trial["completed"] >= 4400:
            trial.update(
                stage="transition", started=now,
                destination=(trial["enter_zone"][0], trial["enter_zone"][1] + 1),
                entering=False, transferred=False, hold=None,
            )
        return
    if trial["stage"] == "transition":
        elapsed = now - trial["started"]
        if elapsed >= 300 and not trial["transferred"]:
            teleport(game_state, trial["destination"])
            trial.update(active=trial["entering"], transferred=True)
            if trial["complete"] and not trial["entering"]:
                set_cell(floor, trial["enter_zone"], "#")
        if elapsed >= 650:
            trial["stage"] = None
        return
    occupied = {rock["cell"] for rock in trial["rocks"]}
    for cell, level in trial["plate_levels"].items():
        target = float(cell in occupied)
        trial["plate_levels"][cell] = min(target, level + dt / 280) if target > level else max(target, level - dt / 280)
    if trial["stage"] == "push" and now - trial["started"] >= PUSH_MS:
        trial["stage"] = None
        if not trial["complete"] and set(trial["plates"]) == occupied:
            from acts.act_three.abilities.progression import unlock_ability_slot
            from acts.act_three.abilities.catalog import get_subclass_definition
            unlock_ability_slot(game_state.player, "q")
            game_state.player.ability_slot_charges["q"] = get_subclass_definition("berserker").abilities["q"].charge_required
            trial.update(complete=True, completed=now, completion_origin=(floor.player_column, floor.player_row), stage="completion", hold=None)
    if trial["stage"] == "reset":
        elapsed = now - trial["started"]
        if elapsed >= 500 and not trial.get("restored"):
            for rock in trial["rocks"]:
                set_cell(floor, rock["cell"], ".")
            trial["rocks"] = deepcopy(trial["initial"])
            for rock in trial["rocks"]:
                set_cell(floor, rock["cell"], "#")
            teleport(game_state, trial["player_start"])
            trial["restored"] = True
        if elapsed >= 1100:
            trial["stage"] = None
        return
    if trial["active"] and not trial["complete"] and trial["stage"] is None and pygame.key.get_pressed()[pygame.K_t]:
        if trial["hold"] is None:
            trial["hold"] = now
        elif now - trial["hold"] >= HOLD_MS:
            trial.update(stage="reset", started=now, restored=False, hold=None)
    else:
        trial["hold"] = None
