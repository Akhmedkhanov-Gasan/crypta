import math
import random

from enemies import ENEMY_TYPES
from logic import get_enemy_occupied_positions, has_line_of_sight
from systems.grid_geometry import can_reach_adjacent_cell
from acts.act_three.spawn_regions import (
    inside_region,
    reserved_spawn_positions,
    room_entrances,
    spawn_regions,
)
from acts.act_three.settings import ACT_THREE_ENCOUNTER_SETTINGS
from acts.act_three.world_geometry import reachable_cells


def enemy_spawn_cells(enemy_type, position):
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


def _candidates(floor, region, enemy_type, occupied, reachable, settings):
    ground = floor["tile_layers"].get("Ground", [])
    player = floor["player_start"]
    entrances = room_entrances(floor)
    enemy_positions = [enemy["position"] for enemy in floor["enemies"]]
    candidates = []
    for position in reachable:
        if not inside_region(position, region):
            continue
        cells = enemy_spawn_cells(enemy_type, position)
        if not cells <= reachable or not all(inside_region(cell, region) for cell in cells):
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


def _room_enemies(floor, region):
    return [enemy for enemy in floor["enemies"] if inside_region(enemy["position"], region)]


def _place_room_enemy(floor, region, occupied, reachable, settings):
    enemies = _room_enemies(floor, region)
    weights = settings["enemy_weights"]
    enemy_types = [
        name for name in weights
        if not (name == "priest" and any(enemy["type"] == name for enemy in enemies))
        and not (name == "archer" and sum(enemy["type"] == name for enemy in enemies) >= 2)
    ]
    frontline = {"goblin", "brute", "sentinel"}
    if not any(enemy["type"] in frontline for enemy in enemies):
        enemy_types = [name for name in enemy_types if name in frontline]
    while enemy_types:
        enemy_type = random.choices(enemy_types, weights=[weights[name] for name in enemy_types], k=1)[0]
        candidates = _candidates(floor, region, enemy_type, occupied, reachable, settings)
        if candidates:
            nearby = [
                position for position in candidates
                if any(
                    abs(position[0] - enemy["position"][0]) + abs(position[1] - enemy["position"][1]) <= 4
                    and has_line_of_sight(floor["map"], *position, *enemy["position"], floor["barriers"])
                    for enemy in enemies
                )
            ]
            position = random.choice(nearby or candidates)
            floor["enemies"].append({"position": position, "type": enemy_type, "boss_group": False})
            occupied.update(enemy_spawn_cells(enemy_type, position))
            return True
        enemy_types.remove(enemy_type)
    return False


def populate_act_three_enemies(floor, act_floor):
    occupied = reserved_spawn_positions(floor)
    occupied.update(floor.get("trial_safe_cells", ()))
    for enemy in floor["enemies"]:
        cells = enemy_spawn_cells(enemy["type"], enemy["position"])
        if not _fits(floor, cells, occupied):
            raise ValueError(f"Enemy overlaps a blocked or occupied cell: {enemy!r}")
        occupied.update(cells)
    settings = ACT_THREE_ENCOUNTER_SETTINGS.get(act_floor)
    if not settings or not settings["enabled"]:
        return floor
    reachable = reachable_cells(floor["map"], floor["player_start"], floor["barriers"])
    available = []
    for region in spawn_regions(floor):
        if not region["enabled"]:
            continue
        area = sum(inside_region(cell, region) for cell in reachable)
        existing = sum(inside_region(enemy["position"], region) for enemy in floor["enemies"])
        limit = min(settings["maximum_per_room"], math.ceil(area / settings["cells_per_enemy"]))
        if limit > existing:
            available.append([region, limit - existing])
    remaining = max(0, random.randint(settings["min_enemies"], settings["max_enemies"]) - len(floor["enemies"]))
    while remaining and available:
        room_counts = [len(_room_enemies(floor, region)) for region, _ in available]
        minimum = min(room_counts)
        index = random.choice([index for index, count in enumerate(room_counts) if count == minimum])
        region, capacity = available[index]
        group_size = min(remaining, capacity, random.randint(settings["min_group_size"], settings["max_group_size"]))
        placed = False
        for _ in range(group_size):
            placed = _place_room_enemy(floor, region, occupied, reachable, settings)
            if not placed:
                break
            remaining -= 1
            available[index][1] -= 1
        if not placed or available[index][1] == 0:
            available.pop(index)
    return floor
