from copy import deepcopy

import pygame

from acts.act_three.events import GameEvent, GameEventType
from game.combat_log import add_log_message
from systems.grid_geometry import can_reach_adjacent_cell


STEPS = ((0, -1), (1, 0), (0, 1), (-1, 0))
DIRECTIONS = {"north": 0, "east": 1, "south": 2, "west": 3}
TURN_MS = 560
PUSH_MS = 720
SHOT_MS = 800
RESET_MS = 1100


def build_trial(markers, width, height, dungeon_map):
    if not markers.get("piercing_trial_launcher_01"):
        return None

    def one(name):
        values = markers.get(name, [])
        if len(values) != 1:
            raise ValueError(f"Piercing trial requires one {name}")
        return values[0]

    launchers = []
    targets = []
    for number in range(1, 4):
        position, properties = one(f"piercing_trial_launcher_{number:02d}")
        direction = DIRECTIONS[properties.get("direction", "south" if number == 1 else "east")]
        launchers.append({"id": number, "position": position, "direction": direction})
        targets.append({"id": number, "position": one(f"piercing_trial_target_{number:02d}")[0]})
    levers = {
        "a": one("swivel_assembly_a")[0],
        "b": one("swivel_assembly_b")[0],
        "fire": one("lever")[0],
    }
    trial = {
        "door": one("trial_door")[0],
        "bounds": (0, 0, width, height - 1),
        "launchers": launchers,
        "targets": targets,
        "levers": levers,
        "movable": [position for position, _ in markers.get("piercing_trial_movable_column", [])],
        "fragile": [position for position, _ in markers.get("piercing_trial_fragile_column", [])],
        "broken": set(),
        "activated": set(),
        "phase": "closed",
        "stage": None,
        "started": 0,
        "paths": [],
    }
    trial["return"] = (levers["fire"][0], levers["fire"][1] + 1)
    for cell in [trial["return"], *[item["position"] for item in targets]]:
        x, y = cell
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Piercing trial requires free floor at {cell}")
    trial["initial_movable"] = list(trial["movable"])
    trial["initial_directions"] = [item["direction"] for item in launchers]
    occupied = [trial["door"], *trial["movable"], *trial["fragile"], *levers.values(), *[item["position"] for item in launchers]]
    if len(occupied) != len(set(occupied)):
        raise ValueError("Piercing trial objects overlap")
    for x, y in occupied:
        if not (0 <= x < width and 0 <= y < height and dungeon_map[y][x] == "."):
            raise ValueError(f"Invalid piercing trial object cell: {(x, y)}")
        dungeon_map[y][x] = "#"
    return trial


def shift_trial(trial, offset):
    result = deepcopy(trial)

    def shifted(cell):
        return cell[0] + offset[0], cell[1] + offset[1]

    for name in ("door", "return"):
        result[name] = shifted(result[name])
    for name in ("movable", "initial_movable", "fragile"):
        result[name] = [shifted(cell) for cell in result[name]]
    result["levers"] = {key: shifted(cell) for key, cell in result["levers"].items()}
    for name in ("launchers", "targets"):
        for item in result[name]:
            item["position"] = shifted(item["position"])
    left, top, right, bottom = result["bounds"]
    result["bounds"] = (left + offset[0], top + offset[1], right + offset[0], bottom + offset[1])
    return result


def inside(trial, cell):
    left, top, right, bottom = trial["bounds"]
    return left <= cell[0] < right and top <= cell[1] < bottom


def set_cell(floor, cell, value):
    x, y = cell
    row = list(floor.map[y])
    row[x] = value
    floor.map[y] = "".join(row)


def interaction_cells(trial):
    if trial["phase"] == "closed":
        return {trial["door"]}
    if trial["phase"] == "active":
        return set(trial["levers"].values()) | set(trial["movable"])
    return set()


def nearby(floor, cell):
    origin = (floor.player_column, floor.player_row)
    return abs(cell[0] - origin[0]) + abs(cell[1] - origin[1]) == 1 and can_reach_adjacent_cell(
        floor.map, origin, cell, floor.barriers, target_must_be_walkable=False,
    )


def interact(game_state, cell):
    floor = game_state.floor
    trial = floor.piercing_trial
    if trial is None or cell not in interaction_cells(trial) or not nearby(floor, cell):
        return False
    if trial["stage"] is not None:
        return True
    now = pygame.time.get_ticks()
    if trial["phase"] == "closed":
        if game_state.player.subclass != "archer":
            add_log_message(game_state.combat_log, "Only an archer may enter this sanctuary.")
            return True
        trial.update(phase="opening", started=now)
        game_state.player.archer_basic_aiming = False
        game_state.player.archer_piercing_aiming = False
        return True
    key = next((key for key, position in trial["levers"].items() if position == cell), None)
    if key is not None:
        trial.update(stage="lever", started=now, lever=key)
        trial["previous_directions"] = [item["direction"] for item in trial["launchers"]]
        return True
    origin = (floor.player_column, floor.player_row)
    step = (cell[0] - origin[0], cell[1] - origin[1])
    target = (cell[0] + step[0], cell[1] + step[1])
    protected = {trial["return"], trial["door"], *[item["position"] for item in trial["targets"]]}
    if target in protected or not inside(trial, target) or not can_reach_adjacent_cell(floor.map, cell, target, floor.barriers):
        add_log_message(game_state.combat_log, "The column cannot move there.")
        return True
    trial["movable"][trial["movable"].index(cell)] = target
    set_cell(floor, cell, ".")
    set_cell(floor, target, "#")
    trial.update(stage="push", started=now, push_origin=cell, push_target=target)
    return True


def handle_key(event, game_state):
    floor = game_state.floor
    trial = floor.piercing_trial
    if trial is None or trial["phase"] == "complete":
        return False
    origin = (floor.player_column, floor.player_row)
    if trial["phase"] == "opening" or trial["stage"] is not None:
        return event.key != pygame.K_ESCAPE
    if event.key == pygame.K_t:
        if getattr(event, "mod", 0) & pygame.KMOD_SHIFT and nearby(floor, trial["levers"]["fire"]):
            reset_attempt(game_state, trial, penalize=False)
            add_log_message(game_state.combat_log, "The trial mechanisms return to their initial positions.")
            return True
        candidates = [cell for cell in interaction_cells(trial) if nearby(floor, cell)]
        if candidates:
            facing = getattr(game_state.player, "facing_direction", (0, 1))
            candidates.sort(key=lambda cell: (cell != (origin[0] + facing[0], origin[1] + facing[1]), cell))
            return interact(game_state, candidates[0])
    return inside(trial, origin) and event.key in (
        pygame.K_q, pygame.K_e, pygame.K_f, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
    )


def handle_action(game_state, event, direction):
    floor = game_state.floor
    trial = floor.piercing_trial
    if trial is None or trial["phase"] == "complete":
        return None
    origin = (floor.player_column, floor.player_row)
    target = (origin[0] + direction[0], origin[1] + direction[1])
    if trial["phase"] == "opening" or trial["stage"] is not None:
        return False
    if target in interaction_cells(trial) and interact(game_state, target):
        return False
    if not inside(trial, origin) and not inside(trial, target):
        return None
    if trial["phase"] != "active":
        return False
    if direction == (0, 0):
        return False
    if not can_reach_adjacent_cell(floor.map, origin, target, floor.barriers):
        return False
    floor.player_column, floor.player_row = target
    game_state.player.movement_animation_started_at = pygame.time.get_ticks()
    game_state.emit(GameEvent(type=GameEventType.MOVE, actor="hero", origin=origin, destination=target))
    event.piercing_trial_turn = True
    return True


def shoot(floor, trial, now):
    paths = []
    for launcher in trial["launchers"]:
        origin = launcher["position"]
        step = STEPS[launcher["direction"]]
        cell = origin
        path = {"id": launcher["id"], "cells": [origin], "hits": [], "break": None}
        for _ in range(max(len(floor.map), len(floor.map[0]))):
            target = (cell[0] + step[0], cell[1] + step[1])
            if not inside(trial, target):
                break
            fragile = target in trial["fragile"] and target not in trial["broken"]
            if not can_reach_adjacent_cell(floor.map, cell, target, floor.barriers, target_must_be_walkable=False):
                break
            if floor.map[target[1]][target[0]] != "." and not fragile and target not in trial["levers"].values():
                break
            path["cells"].append(target)
            if fragile:
                path["break"] = target
                break
            path["hits"].extend(
                item["id"] for item in trial["targets"]
                if item["position"] == target and item["id"] not in trial.get("destroyed_targets", set())
            )
            if path["hits"]:
                break
            cell = target
        paths.append(path)
    trial.update(stage="shot", started=now, paths=paths)


def reset_attempt(game_state, trial, penalize=True):
    floor = game_state.floor
    for cell in trial["movable"]:
        set_cell(floor, cell, ".")
    trial["movable"] = list(trial["initial_movable"])
    for cell in trial["movable"] + trial["fragile"]:
        set_cell(floor, cell, "#")
    for item, direction in zip(trial["launchers"], trial["initial_directions"]):
        item["direction"] = direction
    trial["broken"].clear()
    trial["broken_at"] = {}
    trial["activated"].clear()
    trial["destroyed_targets"] = set()
    trial["target_impacts"] = []
    trial.update(stage=None, paths=[])
    floor.player_column, floor.player_row = trial["return"]
    player = game_state.player
    if penalize:
        player.health = max(1, (player.health + 1) // 2)
    player.movement_origin = None
    player.movement_animation_started_at = 0
    game_state.clear_events()


def advance_frame(game_state, now):
    floor = game_state.floor
    trial = floor.piercing_trial
    if trial is None:
        return
    elapsed = now - trial["started"]
    if trial["phase"] == "opening" and elapsed >= 640:
        trial["phase"] = "active"
        set_cell(floor, trial["door"], ".")
    stage = trial["stage"]
    if stage == "push" and elapsed >= PUSH_MS:
        trial["stage"] = None
    elif stage == "lever" and elapsed >= TURN_MS:
        key = trial["lever"]
        if key == "fire":
            shoot(floor, trial, now)
        else:
            changes = {"a": (-1, 1, 0), "b": (1, 0, -1)}[key]
            for item, change in zip(trial["launchers"], changes):
                item["direction"] = (item["direction"] + change) % 4
            trial.update(stage="return", started=now)
    elif stage == "return" and elapsed >= 220:
        trial["stage"] = None
    elif stage == "shot" and elapsed >= SHOT_MS:
        wrong = any(hit != path["id"] for path in trial["paths"] for hit in path["hits"])
        for path in trial["paths"]:
            if path["break"] is not None and path["break"] not in trial["broken"]:
                trial["broken"].add(path["break"])
                trial.setdefault("broken_at", {})[path["break"]] = now
                set_cell(floor, path["break"], ".")
        impacts = trial.setdefault("target_impacts", [])
        impacts[:] = [impact for impact in impacts if now - impact["started"] < 1100]
        for path in trial["paths"]:
            for hit in path["hits"]:
                if hit in trial.setdefault("destroyed_targets", set()):
                    continue
                trial["destroyed_targets"].add(hit)
                impacts.append({
                    "position": path["cells"][-1],
                    "started": now,
                    "wrong": hit != path["id"],
                    "direction": (
                        path["cells"][1][0] - path["cells"][0][0],
                        path["cells"][1][1] - path["cells"][0][1],
                    ),
                })
                if hit == path["id"]:
                    trial["activated"].add(hit)
        if wrong:
            trial.update(stage="reset", started=now)
            add_log_message(game_state.combat_log, "A foreign seal rejects the arrow. The mechanisms recoil.")
        elif len(trial["activated"]) == len(trial["targets"]):
            from acts.act_three.abilities.progression import unlock_ability_slot
            from acts.act_three.abilities.catalog import get_subclass_definition
            unlock_ability_slot(game_state.player, "q")
            definition = get_subclass_definition(game_state.player.subclass)
            game_state.player.ability_slot_charges["q"] = definition.abilities["q"].charge_required
            trial.update(phase="complete", stage=None, completed=now)
            add_log_message(game_state.combat_log, "Trial complete. PIERCING SHOT unlocked.", category="progress")
        else:
            trial.update(stage="return", started=now)
    elif stage == "reset" and elapsed >= RESET_MS:
        reset_attempt(game_state, trial)
        trial.update(stage="recover", started=now)
    elif stage == "recover" and elapsed >= 350:
        trial["stage"] = None
