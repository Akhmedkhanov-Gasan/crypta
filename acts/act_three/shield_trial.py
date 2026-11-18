from copy import deepcopy
import random

import pygame

from acts.act_three.events import GameEvent, GameEventType
from systems.grid_geometry import can_reach_adjacent_cell
from acts.act_three.piercing_trial import set_cell


def neighbors(index):
    x, y = index % 4, index // 4
    return [ny * 4 + nx for nx, ny in ((x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if 0 <= nx < 4 and 0 <= ny < 4]


def build_trial(markers, width, height, dungeon_map):
    if not markers.get("start_trial"):
        return None
    start = markers["start_trial"][0][0]
    left, top = (width - 4) // 2, start[1] - 4
    cells = [(left + x, top + y) for y in range(4) for x in range(4)]
    for x, y in [start, *cells]:
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Shield trial requires free floor at {(x, y)}")
    rng = random.Random()
    while True:
        lights = [False] * 16
        for index in rng.sample(range(16), rng.randint(7, 12)):
            for neighbor in neighbors(index):
                lights[neighbor] = not lights[neighbor]
        if 5 <= sum(lights) <= 11:
            break
    doors = markers.get("trial_door", [])
    if len(doors) != 1:
        raise ValueError("Shield trial requires one trial_door marker")
    door = doors[0][0]
    x, y = door
    if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
        raise ValueError(f"Shield trial door requires free floor at {door}")
    dungeon_map[y][x] = "#"
    return {"start": start, "door": door, "cells": cells, "bounds": (1, 2, width - 1, start[1]),
            "lights": lights, "levels": [float(value) for value in lights],
            "initial": list(lights), "phase": "closed", "started": 0, "last_frame": 0, "pressed": -1000, "pulse": {}, "moves": 0}


def shift_trial(trial, offset):
    result = deepcopy(trial)
    def shift(cell):
        return cell[0] + offset[0], cell[1] + offset[1]
    result["start"] = shift(result["start"])
    result["door"] = shift(result["door"])
    result["cells"] = [shift(cell) for cell in result["cells"]]
    left, top, right, bottom = result["bounds"]
    result["bounds"] = left + offset[0], top + offset[1], right + offset[0], bottom + offset[1]
    return result


def inside(trial, cell):
    left, top, right, bottom = trial["bounds"]
    return left <= cell[0] < right and top <= cell[1] <= bottom


def synchronize(game_state, trial):
    if trial["phase"] != "active":
        return
    floor = game_state.floor
    active = inside(trial, (floor.player_column, floor.player_row))
    if not active:
        deactivate(trial, pygame.time.get_ticks())


def deactivate(trial, now):
    trial.update(phase="extinguishing", started=now, pulse={}, moves=0)
    trial["lights"] = list(trial["initial"])


def handle_key(event, game_state):
    trial = game_state.floor.shield_trial
    if trial is None or game_state.player.subclass != "paladin":
        return False
    synchronize(game_state, trial)
    if trial["phase"] in ("completion", "opening", "awakening", "extinguishing"):
        return event.key != pygame.K_ESCAPE
    if trial["phase"] != "active" or event.key != pygame.K_q:
        return False
    floor = game_state.floor
    cell = floor.player_column, floor.player_row
    now = pygame.time.get_ticks()
    if cell not in trial["cells"] or getattr(event, "repeat", False) or now - trial["pressed"] < 250:
        return True
    changed = neighbors(trial["cells"].index(cell))
    for index in changed:
        trial["lights"][index] = not trial["lights"][index]
        trial["pulse"][index] = now
    trial.update(pressed=now, moves=trial["moves"] + 1)
    if len(set(trial["lights"])) == 1:
        from acts.act_three.abilities.progression import unlock_ability_slot
        from acts.act_three.abilities.catalog import get_subclass_definition
        from game.combat_log import add_log_message
        unlock_ability_slot(game_state.player, "q")
        game_state.player.ability_slot_charges["q"] = get_subclass_definition("paladin").abilities["q"].charge_required
        trial.update(phase="completion", completed=now, completion_origin=cell)
        game_state.clear_events()
        add_log_message(game_state.combat_log, "Trial complete. SHIELD CHARGE unlocked.", category="progress")
    return True


def handle_action(game_state, event, direction):
    floor = game_state.floor
    trial = floor.shield_trial
    if trial is None:
        return None
    if trial["phase"] in ("completion", "opening", "awakening", "extinguishing"):
        return False
    if game_state.player.subclass != "paladin" or trial["phase"] == "complete":
        return None
    origin = floor.player_column, floor.player_row
    target = origin[0] + direction[0], origin[1] + direction[1]
    if trial["phase"] == "closed":
        if target != trial["door"]:
            return None
        if abs(direction[0]) + abs(direction[1]) == 1 and can_reach_adjacent_cell(floor.map, origin, target, floor.barriers, target_must_be_walkable=False):
            trial.update(phase="opening", started=pygame.time.get_ticks())
        return False
    if not inside(trial, origin) and not inside(trial, target):
        return None
    if direction == (0, 0) or not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
        return False
    floor.player_column, floor.player_row = target
    game_state.player.movement_animation_started_at = pygame.time.get_ticks()
    game_state.emit(GameEvent(type=GameEventType.MOVE, actor="hero", origin=origin, destination=target))
    event.piercing_trial_turn = True
    if target == trial["start"] or (origin == trial["start"] and inside(trial, target)):
        if trial["phase"] == "ready":
            trial.update(phase="awakening", started=pygame.time.get_ticks(), pulse={})
            game_state.player.paladin_shield_charge_aiming = False
            game_state.player.paladin_shield_charge_target = None
        elif trial["phase"] == "active" and target == trial["start"]:
            deactivate(trial, pygame.time.get_ticks())
    synchronize(game_state, trial)
    return True


def advance_frame(game_state, now):
    trial = game_state.floor.shield_trial
    if trial is None:
        return
    dt = min(100, max(0, now - trial["last_frame"]))
    trial["last_frame"] = now
    elapsed = now - trial["started"]
    if trial["phase"] == "opening" and elapsed >= 640:
        set_cell(game_state.floor, trial["door"], ".")
        trial["phase"] = "ready"
    elif trial["phase"] == "awakening" and elapsed >= 1050:
        trial["phase"] = "active"
    elif trial["phase"] == "extinguishing" and elapsed >= 650:
        trial["phase"] = "ready"
    for index, value in enumerate(trial["levels"]):
        target = float(trial["lights"][index])
        trial["levels"][index] = min(target, value + dt / 240) if target > value else max(target, value - dt / 240)
    if trial["phase"] == "completion" and now - trial["completed"] >= 4200:
        trial["phase"] = "complete"
    synchronize(game_state, trial)
