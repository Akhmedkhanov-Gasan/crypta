from copy import deepcopy

from acts.act_three.world_geometry import reachable_cells


def build_trial(markers, width, height, dungeon_map, connectors):
    if not markers.get("ritual_start"):
        return None

    def one(name):
        values = markers.get(name, [])
        if len(values) != 1:
            raise ValueError(f"Rune trial requires one {name}")
        return values[0][0]

    start = one("ritual_start")
    altars = (one("altar_01"), one("altar_02"))
    exits = [item for item in connectors if item["name"] == "exit_west"]
    if len(exits) != 1:
        raise ValueError("Rune trial requires one exit_west")
    door = exits[0]["position"]
    if not (0 <= start[0] < width and 0 <= start[1] < height and dungeon_map[start[1]][start[0]] == "."):
        raise ValueError("Rune trial ritual_start must be on free floor")
    cells = reachable_cells(dungeon_map, start, set()) - {door}
    if (door[0] + 1, door[1]) not in cells:
        raise ValueError("Rune trial entrance must connect to the ritual")
    return {
        "start": start,
        "altars": altars,
        "door": door,
        "entrance": (door[0] + 1, door[1]),
        "bounds": (0, 0, width, height),
        "cells": cells,
        "phase": "idle",
        "wave": 0,
        "enemies": [],
        "started_at": -1,
        "discovered": False,
    }


def shift_trial(trial, offset):
    result = deepcopy(trial)

    def shift(cell):
        return cell[0] + offset[0], cell[1] + offset[1]

    for name in ("start", "door", "entrance"):
        result[name] = shift(result[name])
    result["altars"] = tuple(shift(cell) for cell in result["altars"])
    result["cells"] = {shift(cell) for cell in result["cells"]}
    left, top, right, bottom = result["bounds"]
    result["bounds"] = left + offset[0], top + offset[1], right + offset[0], bottom + offset[1]
    return result
