import math
import random

from enemies import ENEMY_TYPES
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell
from acts.act_three.npcs import get_npc_cells
from acts.act_three.settings import ACT_THREE_ENCOUNTER_SETTINGS
from acts.act_three.world_geometry import reachable_cells


def _enemy_cells(enemy_type, position):
    config = ENEMY_TYPES[enemy_type]
    return set(get_enemy_occupied_positions({
        "column": position[0],
        "row": position[1],
        "footprint_width": config.get("footprint_width", 1),
        "footprint_height": config.get("footprint_height", 1),
    }))


def _fits(floor, cells, occupied):
    dungeon_map = floor["map"]
    for x, y in cells:
        if not (0 <= y < len(dungeon_map) and 0 <= x < len(dungeon_map[y])):
            return False
        if dungeon_map[y][x] != "." or (x, y) in occupied:
            return False
        for neighbor in ((x + 1, y), (x, y + 1)):
            if neighbor in cells and not can_reach_adjacent_cell(dungeon_map, (x, y), neighbor, floor["barriers"]):
                return False
    return True


def _reserved_positions(floor):
    positions = {floor["player_start"], floor["stairs"]}
    positions.update(chest["position"] for chest in floor["chests"])
    positions.update(floor["potions"])
    positions.update(ore["position"] for ore in floor.get("ores", []))
    for npc in floor.get("npcs", []):
        positions.update(get_npc_cells(npc))
    altar = floor.get("upgrade_altar")
    if altar is not None:
        positions.update((altar[0] + x, altar[1] + y) for x in range(2) for y in range(2))
    for passage in floor.get("passages", []):
        positions.update((passage["wall_position"], passage["trigger_position"]))
    return positions - {None}


def _inside(position, region):
    return region["left"] <= position[0] < region["right"] and region["top"] <= position[1] < region["bottom"]


def _candidates(floor, region, enemy_type, occupied, reachable, settings):
    ground = floor["tile_layers"].get("Ground", [])
    player = floor["player_start"]
    entrances = [connector["position"] for connector in floor.get("connectors", [])]
    entrances.extend(position for edge in floor.get("room_connections", []) for position in edge)
    enemy_positions = [enemy["position"] for enemy in floor["enemies"]]
    candidates = []
    for position in reachable:
        if not _inside(position, region):
            continue
        cells = _enemy_cells(enemy_type, position)
        if not cells <= reachable or not all(_inside(cell, region) for cell in cells):
            continue
        if not _fits(floor, cells, occupied):
            continue
        if any(y >= len(ground) or x >= len(ground[y]) or not ground[y][x] for x, y in cells):
            continue
        if min(abs(x - player[0]) + abs(y - player[1]) for x, y in cells) < settings["minimum_player_distance"]:
            continue
        if any(abs(x - door[0]) + abs(y - door[1]) < 2 for x, y in cells for door in entrances):
            continue
        if any(abs(position[0] - other[0]) + abs(position[1] - other[1]) < settings["minimum_spacing"] for other in enemy_positions):
            continue
        candidates.append(position)
    return candidates


def populate_act_three_enemies(floor, act_floor):
    occupied = _reserved_positions(floor)
    for enemy in floor["enemies"]:
        cells = _enemy_cells(enemy["type"], enemy["position"])
        if not _fits(floor, cells, occupied):
            raise ValueError(f"Enemy overlaps a blocked or occupied cell: {enemy!r}")
        occupied.update(cells)
    settings = ACT_THREE_ENCOUNTER_SETTINGS.get(act_floor)
    if not settings or not settings["enabled"]:
        return floor
    reachable = reachable_cells(floor["map"], floor["player_start"], floor["barriers"])
    regions = floor.get("spawn_regions", [{
        "left": 0,
        "top": 0,
        "right": len(floor["map"][0]),
        "bottom": len(floor["map"]),
        "enabled": floor.get("enemy_spawn_mode", False),
    }])
    available = []
    for region in regions:
        if not region["enabled"]:
            continue
        area = sum(_inside(cell, region) for cell in reachable)
        existing = sum(_inside(enemy["position"], region) for enemy in floor["enemies"])
        limit = min(settings["maximum_per_room"], math.ceil(area / settings["cells_per_enemy"]))
        if limit > existing:
            available.append([region, limit - existing])
    remaining = max(0, random.randint(settings["min_enemies"], settings["max_enemies"]) - len(floor["enemies"]))
    weights = settings["enemy_weights"]
    while remaining and available:
        index = random.randrange(len(available))
        region, capacity = available[index]
        enemy_types = list(weights)
        placed = False
        while enemy_types:
            enemy_type = random.choices(enemy_types, weights=[weights[name] for name in enemy_types], k=1)[0]
            candidates = _candidates(floor, region, enemy_type, occupied, reachable, settings)
            if candidates:
                position = random.choice(candidates)
                floor["enemies"].append({"position": position, "type": enemy_type, "boss_group": False})
                occupied.update(_enemy_cells(enemy_type, position))
                remaining -= 1
                available[index][1] -= 1
                placed = True
                break
            enemy_types.remove(enemy_type)
        if not placed or capacity == 1:
            available.pop(index)
    return floor
