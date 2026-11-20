import random
from collections import Counter
from math import ceil
from pathlib import Path

from acts.act_three.crate_generation import _room_edges
from acts.act_three.enemies.generation import enemy_spawn_cells
from acts.act_three.mining.catalog import ORE_TYPES
from acts.act_three.mining.settings import ORE_CELLS_PER_VEIN, ORE_MAXIMUM_PER_ROOM, ORE_MINIMUM_SPACING, ORE_SPAWN_SETTINGS
from acts.act_three.npcs import get_npc_cells
from acts.act_three.spawn_regions import inside_region, reserved_spawn_positions, room_entrances, spawn_regions
from acts.act_three.world_geometry import reachable_cells
from systems.grid_geometry import can_reach_adjacent_cell


def _mining_access(floor, cell, reachable):
    x, y = cell
    return any(
        neighbor in reachable and can_reach_adjacent_cell(floor["map"], neighbor, cell, floor["barriers"], target_must_be_walkable=False)
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    )


def _room_space(floor, cell, open_cells):
    x, y = cell
    for left in range(x - 2, x + 1):
        for top in range(y - 2, y + 1):
            patch = {(column, row) for column in range(left, left + 3) for row in range(top, top + 3)}
            if not patch <= open_cells:
                continue
            if all(
                can_reach_adjacent_cell(floor["map"], origin, target, floor["barriers"])
                for origin in patch
                for target in ((origin[0] + 1, origin[1]), (origin[0], origin[1] + 1))
                if target in patch
            ):
                return True
    return False


def populate_act_three_ores(floor, act_floor):
    settings = ORE_SPAWN_SETTINGS.get(act_floor)
    if settings is None:
        return
    regions = [region for region in spawn_regions(floor) if region.get("ore_spawn_mode", region["enabled"]) and not Path(region.get("source_path", "")).name.startswith("corridor_")]
    if not regions:
        return
    ground = {
        (x, y)
        for y, row in enumerate(floor["tile_layers"].get("Ground", []))
        for x, gid in enumerate(row)
        if gid and floor["map"][y][x] == "."
    }
    occupied = reserved_spawn_positions(floor) | set(floor.get("trial_safe_cells", ())) | set(floor["torches"])
    for enemy in floor["enemies"]:
        occupied.update(enemy_spawn_cells(enemy["type"], enemy["position"]))
    for npc in floor.get("npcs", []):
        for x, y in get_npc_cells(npc):
            occupied.update(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    for x, y in room_entrances(floor):
        occupied.update((x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3))
    for name, layer in floor["tile_layers"].items():
        if name.split("_", 1)[0] not in ("Ground", "GroundDetails"):
            occupied.update((x, y) for y, row in enumerate(layer) for x, gid in enumerate(row) if gid)

    ores = floor.setdefault("ores", [])
    blocked = {item["position"] for item in (*floor["breakable_crates"], *floor["chests"])}
    reachable = reachable_cells(floor["map"], floor["player_start"], floor["barriers"], blocked=blocked)
    protected_veins = [ore["position"] for ore in ores if ore["stage"] < 3 and _mining_access(floor, ore["position"], reachable)]
    counts = Counter(ore["type"] for ore in ores if ore["stage"] < 3)
    remaining = max(0, random.randint(settings["min_veins"], settings["max_veins"]) - sum(counts.values()))
    available = []
    for region in regions:
        allowed = region.get("ore_types") or tuple(settings["weights"])
        unknown = set(allowed) - ORE_TYPES.keys()
        if unknown:
            raise ValueError(f"Unknown ore types in {region.get('source_path', 'map')}: {sorted(unknown)}")
        allowed = tuple(name for name in allowed if settings["weights"].get(name, 0) > 0)
        if not allowed:
            continue
        cells = {cell for cell in ground if inside_region(cell, region)}
        limit = region.get("ore_count")
        if limit is None:
            limit = min(ORE_MAXIMUM_PER_ROOM, ceil(len(cells) / ORE_CELLS_PER_VEIN))
        if limit < 0:
            raise ValueError("ore_count cannot be negative")
        capacity = limit - sum(inside_region(ore["position"], region) and ore["stage"] < 3 for ore in ores)
        candidates = sorted((_room_edges(cells) & reachable) - occupied)
        random.shuffle(candidates)
        if capacity > 0 and candidates:
            available.append([region, allowed, capacity, candidates])

    while remaining and available:
        index = random.randrange(len(available))
        region, allowed, capacity, candidates = available[index]
        placed = False
        while candidates:
            cell = candidates.pop()
            if not _room_space(floor, cell, reachable & ground):
                continue
            if any(abs(cell[0] - ore["position"][0]) + abs(cell[1] - ore["position"][1]) < ORE_MINIMUM_SPACING for ore in ores):
                continue
            blocked.add(cell)
            after = reachable_cells(floor["map"], floor["player_start"], floor["barriers"], blocked=blocked)
            if len(after) != len(reachable) - 1 or not _mining_access(floor, cell, after) or any(
                not _mining_access(floor, position, after) for position in protected_veins
            ):
                blocked.remove(cell)
                continue
            deficits = {ore_type: max(0, settings["minimum_by_type"].get(ore_type, 0) - counts[ore_type]) for ore_type in allowed}
            if "iron_ore" in allowed and counts["iron_ore"] < 4:
                ore_type = "iron_ore"
            elif any(deficits.values()):
                ore_type = max(allowed, key=lambda name: deficits[name])
            else:
                ore_type = random.choices(allowed, weights=[settings["weights"].get(name, 1) for name in allowed], k=1)[0]
            ores.append({"type": ore_type, "position": cell, "stage": 0})
            protected_veins.append(cell)
            x, y = cell
            row = floor["map"][y]
            floor["map"][y] = row[:x] + "#" + row[x + 1:]
            counts[ore_type] += 1
            reachable = after
            available[index][2] -= 1
            remaining -= 1
            placed = True
            break
        if not placed or capacity == 1:
            available.pop(index)
