from copy import deepcopy

import pygame

from acts.act_three.trials.archer import set_cell
from systems.grid_geometry import can_reach_adjacent_cell


PARTS = ("curse_shackle_left", "curse_prisoner_mask", "curse_shackle_right")
SPIRIT_PHASES = ("entering", "active", "sliding", "reset", "completion", "leaving")


def build_trial(markers, width, height, dungeon_map):
    if not markers.get(PARTS[0]):
        return None
    def one(name):
        values = markers.get(name, [])
        if len(values) != 1:
            raise ValueError(f"Curse trial requires one {name}")
        return values[0][0]
    start, door = one("start_trial"), one("trial_door")
    parts = [one(name) for name in PARTS]
    if len(set(parts)) != 3:
        raise ValueError("Curse trial parts overlap")
    for x, y in [start, door, *parts]:
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Curse trial requires free floor at {(x, y)}")
    dungeon_map[door[1]][door[0]] = "#"
    return {"start": start, "door": door, "parts": parts, "initial": list(parts),
            "bounds": (0, 0, width, start[1]), "phase": "closed", "started": 0,
            "selected": 0, "moves": 0, "drag": None, "last_slide": -1000}


def shift_trial(trial, offset):
    result = deepcopy(trial)
    def shift(cell):
        return cell[0] + offset[0], cell[1] + offset[1]
    for name in ("start", "door"):
        result[name] = shift(result[name])
    for name in ("parts", "initial"):
        result[name] = [shift(cell) for cell in result[name]]
    left, top, right, bottom = result["bounds"]
    result["bounds"] = left + offset[0], top + offset[1], right + offset[0], bottom + offset[1]
    return result


def is_spirit(trial):
    return trial is not None and trial["phase"] in SPIRIT_PHASES


def slide(game_state, direction):
    trial = game_state.floor.curse_trial
    if trial["phase"] != "active" or pygame.time.get_ticks() - trial["last_slide"] < 120:
        return
    cell = trial["parts"][trial["selected"]]
    origin = cell
    occupied = set(trial["parts"])
    left, top, right, bottom = trial["bounds"]
    while True:
        target = cell[0] + direction[0], cell[1] + direction[1]
        if not (left <= target[0] < right and top <= target[1] < bottom) or target in occupied:
            break
        if not can_reach_adjacent_cell(game_state.floor.map, cell, target, game_state.floor.barriers):
            break
        cell = target
    if cell != origin:
        distance = abs(cell[0] - origin[0]) + abs(cell[1] - origin[1])
        trial.update(phase="sliding", started=pygame.time.get_ticks(), slide_origin=origin,
                     slide_target=cell, duration=min(850, 180 + distance * 80), moves=trial["moves"] + 1)


def handle_key(event, game_state):
    trial = game_state.floor.curse_trial
    if trial is None:
        return False
    if trial["phase"] == "body_rite":
        return True
    if trial["phase"] == "opening":
        return event.key != pygame.K_ESCAPE
    if not is_spirit(trial):
        return False
    if getattr(event, "repeat", False):
        return True
    if event.key == pygame.K_ESCAPE and trial["phase"] == "active":
        trial.update(phase="leaving", started=pygame.time.get_ticks(), drag=None)
    elif trial["phase"] == "active":
        if event.key == pygame.K_TAB:
            trial["selected"] = (trial["selected"] + 1) % 3
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            trial["selected"] = event.key - pygame.K_1
        elif event.key == pygame.K_t:
            trial.update(phase="reset", started=pygame.time.get_ticks(), drag=None)
        else:
            direction = {pygame.K_w: (0, -1), pygame.K_UP: (0, -1), pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
                         pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0), pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0)}.get(event.key)
            if direction:
                slide(game_state, direction)
    return True


def handle_action(game_state, event, direction):
    floor = game_state.floor
    trial = floor.curse_trial
    if trial is None:
        return None
    if is_spirit(trial) or trial["phase"] in ("opening", "body_rite"):
        return False
    origin = floor.player_column, floor.player_row
    target = origin[0] + direction[0], origin[1] + direction[1]
    if target == trial["door"] and trial["phase"] == "closed":
        if game_state.player.subclass == "warlock" and abs(direction[0]) + abs(direction[1]) == 1 and can_reach_adjacent_cell(floor.map, origin, target, floor.barriers, target_must_be_walkable=False):
            trial.update(phase="opening", started=pygame.time.get_ticks())
        return False
    if target == trial["start"] and trial["phase"] == "ready" and game_state.player.subclass == "warlock":
        if can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
            floor.player_column, floor.player_row = target
            game_state.player.movement_origin = None
            game_state.player.movement_animation_started_at = 0
            trial.update(phase="entering", started=pygame.time.get_ticks(), return_cell=origin, drag=None)
            game_state.clear_events()
        return False
    return None


def return_to_body(game_state, trial):
    floor = game_state.floor
    if trial.get("completed") is not None:
        trial["return_cell"] = trial["start"]
    floor.player_column, floor.player_row = trial["return_cell"]
    game_state.player.movement_origin = None
    game_state.player.movement_animation_started_at = 0
    game_state.player.teleport_camera_origin = None
    game_state.player.teleport_transition_started_at = 0
    trial.update(phase="body_rite" if trial.get("completed") is not None else "ready", started=pygame.time.get_ticks(), drag=None)
    game_state.clear_events()


def advance_frame(game_state, now):
    trial = game_state.floor.curse_trial
    if trial is None:
        return
    elapsed = now - trial["started"]
    if trial["phase"] == "opening" and elapsed >= 640:
        set_cell(game_state.floor, trial["door"], ".")
        trial["phase"] = "ready"
    elif trial["phase"] == "entering" and elapsed >= 700:
        trial["phase"] = "active"
    elif trial["phase"] == "reset" and elapsed >= 600:
        trial.update(parts=list(trial["initial"]), phase="active", moves=0)
    elif trial["phase"] == "leaving" and elapsed >= 600:
        return_to_body(game_state, trial)
    elif trial["phase"] == "sliding" and elapsed >= trial["duration"]:
        trial["parts"][trial["selected"]] = trial["slide_target"]
        trial.update(phase="active", last_slide=now)
        left, mask, right = trial["parts"]
        if mask == (left[0] + 1, left[1]) and right == (mask[0] + 1, mask[1]):
            trial.update(phase="completion", completed=now, started=now)
    elif trial["phase"] == "completion" and elapsed >= 900:
        trial.update(phase="leaving", started=now)
    elif trial["phase"] == "body_rite":
        if elapsed >= 1400 and not trial.get("reward_granted"):
            from acts.act_three.abilities.progression import unlock_ability_slot
            from acts.act_three.abilities.catalog import get_subclass_definition
            from game.combat_log import add_log_message
            unlock_ability_slot(game_state.player, "q")
            game_state.player.ability_slot_charges["q"] = get_subclass_definition("warlock").abilities["q"].charge_required
            trial["reward_granted"] = True
            add_log_message(game_state.combat_log, "Trial complete. CURSE unlocked.", category="progress")
        if elapsed >= 4900:
            trial["phase"] = "complete"
