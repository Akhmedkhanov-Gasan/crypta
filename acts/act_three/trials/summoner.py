from copy import deepcopy

import pygame

from acts.act_three.trials.archer import set_cell
from systems.grid_geometry import can_reach_adjacent_cell


PARTS = ("familiar", "caterpillar", "moon_root")
EATING_ARRIVAL_HOLD_MS = 1100
EATING_CAMERA_MOVE_MS = 1300
EATING_SETTLE_MS = 500
EATING_LEAD_MS = EATING_ARRIVAL_HOLD_MS + EATING_CAMERA_MOVE_MS + EATING_SETTLE_MS
EATING_FRAME_MS = 180
EATING_HOLD_MS = 1300
TRIAL_PHASES = ("entering", "active", "boarding", "sailing", "landing", "eating", "reset", "leaving", "completion")
DURATIONS = {"opening": 640, "entering": 900, "boarding": 600, "sailing": 2200, "landing": 600, "eating": EATING_LEAD_MS + 8 * EATING_FRAME_MS + EATING_HOLD_MS, "reset": 1000, "leaving": 900, "completion": 4400}


def build_trial(markers, width, height, dungeon_map, water):
    if not markers.get("summoner_start_01"):
        return None
    def one(name):
        values = markers.get(name, [])
        if len(values) != 1:
            raise ValueError(f"Summoner trial requires one {name}")
        return values[0][0]
    door, enter = one("trial_door"), one("enter_zone")
    starts = [one(f"summoner_start_{index:02d}") for index in (1, 2)]
    docks = [one(f"boat_{index:02d}") for index in (1, 2)]
    positions = [[one(f"{name}_{index:02d}") for name in PARTS] for index in (1, 2)]
    for x, y in water:
        dungeon_map[y][x] = "#"
    for x, y in [enter, *starts, *positions[0], *positions[1]]:
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Summoner trial requires free shore at {(x, y)}")
    dungeon_map[door[1]][door[0]] = "#"
    return {"door": door, "enter_zone": enter, "starts": starts, "docks": docks,
            "positions": positions, "bounds": (0, 0, width, height), "water": set(water),
            "phase": "closed", "started": 0, "side": 0, "parts": [0, 0, 0],
            "passenger": None, "occupied": set(), "active": False}


def shift_trial(trial, offset):
    result = deepcopy(trial)
    def shift(cell):
        return cell[0] + offset[0], cell[1] + offset[1]
    for key in ("door", "enter_zone"):
        result[key] = shift(result[key])
    for key in ("starts", "docks"):
        result[key] = [shift(cell) for cell in result[key]]
    result["water"] = {shift(cell) for cell in result["water"]}
    result["positions"] = [[shift(cell) for cell in bank] for bank in result["positions"]]
    left, top, right, bottom = result["bounds"]
    result["bounds"] = left + offset[0], top + offset[1], right + offset[0], bottom + offset[1]
    return result


def in_scene(trial):
    return trial is not None and trial["phase"] in TRIAL_PHASES


def busy(trial):
    return trial is not None and trial["phase"] in ("opening", "entering", "boarding", "sailing", "landing", "eating", "reset", "leaving", "completion")


def change_phase(trial, phase, now=None):
    trial.update(phase=phase, started=pygame.time.get_ticks() if now is None else now, transferred=False)


def reset_scene(trial):
    trial.update(side=0, parts=[0, 0, 0], passenger=None)
    trial.pop("eating_pair", None)
    trial.pop("eating_side", None)
    trial.pop("eating_origin", None)


def sync_occupancy(floor):
    trial = floor.summoner_trial
    for cell in trial["occupied"]:
        set_cell(floor, cell, ".")
    trial["occupied"] = {trial["positions"][side][index] for index, side in enumerate(trial["parts"])} if trial["active"] else set()
    for cell in trial["occupied"]:
        set_cell(floor, cell, "#")


def place_player(game_state, cell):
    floor = game_state.floor
    floor.player_column, floor.player_row = cell
    game_state.player.movement_origin = None
    game_state.player.movement_animation_started_at = 0
    game_state.player.teleport_camera_origin = None
    game_state.player.teleport_transition_started_at = 0
    game_state.clear_events()


def detach_familiar(game_state, trial):
    player = game_state.player
    names = ("summoner_familiar_active", "summoner_familiar_position", "summoner_familiar_summoned_at", "summoner_familiar_movement_origin", "summoner_familiar_attack_target")
    trial["saved_familiar"] = {name: getattr(player, name) for name in names}
    player.summoner_familiar_active = False
    player.summoner_familiar_position = None
    player.summoner_familiar_summoned_at = -1
    player.summoner_familiar_movement_origin = None
    player.summoner_familiar_attack_target = None
    player.summoner_familiar_summon_aiming = False
    player.summoner_familiar_summon_target = None
    player.summoner_aiming = False
    player.summoner_aim_target = None


def restore_familiar(game_state, trial):
    for name, value in trial.pop("saved_familiar", {}).items():
        setattr(game_state.player, name, value)


def handle_action(game_state, event, direction):
    floor = game_state.floor
    trial = floor.summoner_trial
    if trial is None:
        return None
    if busy(trial):
        return False
    origin = floor.player_column, floor.player_row
    target = origin[0] + direction[0], origin[1] + direction[1]
    if target == trial["door"] and trial["phase"] == "closed":
        if game_state.player.subclass == "summoner" and can_reach_adjacent_cell(floor.map, origin, target, floor.barriers, target_must_be_walkable=False):
            change_phase(trial, "opening")
        return False
    if target == trial["enter_zone"] and can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
        if trial["phase"] == "ready" and game_state.player.subclass == "summoner":
            reset_scene(trial)
            change_phase(trial, "entering")
        elif trial["phase"] == "active":
            change_phase(trial, "leaving")
    return None


def interaction(game_state):
    floor = game_state.floor
    trial = floor.summoner_trial
    if trial is None or trial["phase"] != "active":
        return None
    side = trial["side"]
    cell = floor.player_column, floor.player_row
    candidates = [i for i in range(3) if trial["parts"][i] == side and abs(cell[0] - trial["positions"][side][i][0]) + abs(cell[1] - trial["positions"][side][i][1]) == 1]
    if candidates:
        facing = game_state.player.facing_direction
        index = max(candidates, key=lambda i: (trial["positions"][side][i][0] - cell[0]) * facing[0] + (trial["positions"][side][i][1] - cell[1]) * facing[1])
        return "part", index
    if max(abs(cell[0] - trial["starts"][side][0]), abs(cell[1] - trial["starts"][side][1])) <= 1:
        return "boat", None
    return None


def interact(game_state, choice=None):
    trial = game_state.floor.summoner_trial
    if trial is None or trial["phase"] != "active":
        return
    choice = interaction(game_state) if choice is None else choice
    if choice is None:
        return
    trial["passenger"] = choice[1]
    change_phase(trial, "boarding")
    game_state.clear_events()


def handle_key(event, game_state):
    trial = game_state.floor.summoner_trial
    if busy(trial):
        return event.key != pygame.K_ESCAPE
    if trial is None or trial["phase"] != "active":
        return False
    if event.key == pygame.K_t:
        if not getattr(event, "repeat", False):
            interact(game_state)
        return True
    return event.key in (pygame.K_q, pygame.K_e, pygame.K_f)


def boat_position(trial, now):
    side = trial["side"]
    if trial["phase"] == "landing":
        return trial["docks"][side]
    origin = trial["docks"][side]
    if trial["phase"] != "sailing":
        return origin
    target = trial["docks"][1 - side]
    t = max(0, min(1, (now - trial["started"]) / DURATIONS["sailing"]))
    t = t * t * (3 - 2 * t)
    return origin[0] + (target[0] - origin[0]) * t, origin[1] + (target[1] - origin[1]) * t


def aboard(trial, now):
    if trial is None:
        return False
    elapsed = now - trial["started"]
    return trial["phase"] == "sailing" or (trial["phase"] == "boarding" and elapsed >= 300) or (trial["phase"] == "landing" and elapsed < 300)


def focus_cell(trial, now):
    if trial is None:
        return None
    if aboard(trial, now):
        return boat_position(trial, now)
    if trial["phase"] == "eating":
        origin = trial["eating_origin"]
        target = trial["positions"][trial["eating_side"]][trial["eating_pair"][1]]
        t = max(0, min(1, (now - trial["started"] - EATING_ARRIVAL_HOLD_MS) / EATING_CAMERA_MOVE_MS))
        t = t * t * (3 - 2 * t)
        return origin[0] + (target[0] - origin[0]) * t, origin[1] + (target[1] - origin[1]) * t
    if trial["phase"] == "reset" and not trial["transferred"] and "eating_pair" in trial:
        return trial["positions"][trial["eating_side"]][trial["eating_pair"][1]]
    return None


def finish(game_state, now):
    from acts.act_three.abilities.progression import unlock_ability_slot
    from acts.act_three.abilities.catalog import get_subclass_definition
    from game.combat_log import add_log_message
    unlock_ability_slot(game_state.player, "q")
    game_state.player.ability_slot_charges["q"] = get_subclass_definition("summoner").abilities["q"].charge_required
    trial = game_state.floor.summoner_trial
    trial["completion_origin"] = game_state.floor.player_column, game_state.floor.player_row
    change_phase(trial, "completion", now)
    add_log_message(game_state.combat_log, "Trial complete. RELEASE FAMILIAR unlocked.", category="progress")


def advance_frame(game_state, now):
    floor = game_state.floor
    trial = floor.summoner_trial
    if trial is None:
        return
    phase = trial["phase"]
    elapsed = now - trial["started"]
    if phase == "sailing":
        x, y = boat_position(trial, now)
        floor.player_column, floor.player_row = round(x), round(y)
    halfway = {"entering": 450, "boarding": 300, "landing": 300, "reset": 500, "leaving": 450, "completion": 3950}.get(phase)
    if halfway is not None and elapsed >= halfway and not trial["transferred"]:
        if phase == "entering":
            trial["active"] = True
            detach_familiar(game_state, trial)
            sync_occupancy(floor)
        elif phase == "boarding":
            place_player(game_state, trial["docks"][trial["side"]])
        elif phase == "landing":
            sync_occupancy(floor)
            place_player(game_state, trial["starts"][trial["side"]])
        elif phase == "reset":
            reset_scene(trial)
            sync_occupancy(floor)
            place_player(game_state, trial["starts"][0])
        elif phase in ("leaving", "completion"):
            trial["active"] = False
            sync_occupancy(floor)
            reset_scene(trial)
            restore_familiar(game_state, trial)
            place_player(game_state, trial["enter_zone"])
        trial["transferred"] = True
    if phase not in DURATIONS or elapsed < DURATIONS[phase]:
        return
    if phase == "opening":
        set_cell(floor, trial["door"], ".")
        change_phase(trial, "ready", now)
    elif phase in ("entering", "reset"):
        change_phase(trial, "active", now)
    elif phase == "boarding":
        change_phase(trial, "sailing", now)
    elif phase == "sailing":
        trial["side"] = 1 - trial["side"]
        if trial["passenger"] is not None:
            trial["parts"][trial["passenger"]] = trial["side"]
        change_phase(trial, "landing", now)
    elif phase == "landing":
        unattended = 1 - trial["side"]
        pair = next((pair for pair in ((0, 1), (1, 2)) if all(trial["parts"][i] == unattended for i in pair)), None)
        if pair is not None:
            trial.update(eating_pair=pair, eating_side=unattended, eating_origin=(floor.player_column, floor.player_row), passenger=None)
            change_phase(trial, "eating", now)
        elif trial["parts"] == [1, 1, 1]:
            trial["passenger"] = None
            finish(game_state, now)
        else:
            trial["passenger"] = None
            change_phase(trial, "active", now)
    elif phase == "eating":
        change_phase(trial, "reset", now)
    elif phase in ("leaving", "completion"):
        change_phase(trial, "complete" if phase == "completion" else "ready", now)
