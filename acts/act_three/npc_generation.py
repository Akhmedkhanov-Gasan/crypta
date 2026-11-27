import random
from collections import deque
from pathlib import Path

from acts.act_three.enemies.generation import enemy_spawn_cells
from acts.act_three.npcs import NPC_FOOTPRINTS
from acts.act_three.spawn_regions import (
    inside_region,
    reserved_spawn_positions,
    room_entrances,
    spawn_regions,
)
from acts.act_three.world_geometry import reachable_cells
from systems.grid_geometry import can_reach_adjacent_cell


def _early_trader_regions(floor):
    regions = spawn_regions(floor)
    origin = next(index for index, region in enumerate(regions) if inside_region(floor["player_start"], region))
    links = {index: set() for index in range(len(regions))}
    for first, second in floor.get("room_connections", ()):
        left = next(index for index, region in enumerate(regions) if inside_region(first, region))
        right = next(index for index, region in enumerate(regions) if inside_region(second, region))
        links[left].add(right)
        links[right].add(left)
    distances = {origin: 0}
    pending = deque([origin])
    while pending:
        index = pending.popleft()
        for neighbor in links[index]:
            corridor = Path(regions[neighbor].get("source_path", "")).name.startswith("corridor_")
            distance = distances[index] + (0 if corridor else 1)
            if distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = distance
                pending.append(neighbor)
    return [
        region for index, region in enumerate(regions)
        if index != origin and distances.get(index, float("inf")) <= 2
        and region["enabled"]
        and Path(region.get("source_path", "")).name != "room_corner_se_01.tmx"
        and not Path(region.get("source_path", "")).name.startswith("corridor_")
    ]


def place_random_trader(floor):
    place_random_npc(floor, "trader", regions=_early_trader_regions(floor))


def find_fixture_position(floor, footprint, *, regions=None):
    regions = regions if regions is not None else [
        region for region in spawn_regions(floor)
        if region["enabled"]
        and not inside_region(floor["player_start"], region)
        and not Path(region.get("source_path", "")).name.startswith("corridor_")
    ]
    dungeon_map = floor["map"]
    barriers = floor["barriers"]
    occupied = reserved_spawn_positions(floor) | set(floor.get("trial_safe_cells", ()))
    occupied.update(floor.get("torches", ()))
    for enemy in floor["enemies"]:
        occupied.update(enemy_spawn_cells(enemy["type"], enemy["position"]))
    for x, y in room_entrances(floor):
        occupied.update(
            (x + dx, y + dy) for dx in range(-1, 2) for dy in range(-1, 2)
        )
    for name, layer in floor["tile_layers"].items():
        if name.split("_", 1)[0] not in ("Ground", "GroundDetails"):
            occupied.update(
                (x, y) for y, row in enumerate(layer) for x, gid in enumerate(row) if gid
            )
    ground = {
        (x, y)
        for y, row in enumerate(floor["tile_layers"].get("Ground", []))
        for x, gid in enumerate(row) if gid
    }
    blocked = {
        item["position"] for item in (*floor["breakable_crates"], *floor["chests"])
    }
    reachable = reachable_cells(dungeon_map, floor["player_start"], barriers, blocked=blocked)
    available = (reachable & ground) - occupied
    candidates = []
    for position in sorted(available):
        width, height = footprint
        cells = {(position[0] + dx, position[1] + dy) for dy in range(height) for dx in range(width)}
        if not cells <= available or not any(
            all(inside_region(cell, region) for cell in cells) for region in regions
        ):
            continue
        if any(not can_reach_adjacent_cell(dungeon_map, cell, neighbor, barriers)
               for cell in cells for neighbor in ((cell[0] + 1, cell[1]), (cell[0], cell[1] + 1))
               if neighbor in cells):
            continue
        candidates.append((position, cells))
    random.shuffle(candidates)
    for position, cells in candidates:
        after = reachable_cells(
            dungeon_map, floor["player_start"], barriers, blocked=blocked | cells,
        )
        if after != reachable - cells:
            continue
        approaches = [
            ((x, y), neighbor)
            for x, y in cells
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if neighbor in after
        ]
        approaches = [neighbor for cell, neighbor in approaches if
            can_reach_adjacent_cell(
                dungeon_map, neighbor, cell, barriers, target_must_be_walkable=False,
            )
        ]
        if not approaches:
            continue
        return position, approaches
    raise ValueError(f"No reachable position for an Act Three fixture of size {footprint}.")


def occupy_fixture(floor, position, footprint):
    width, height = footprint
    for y in range(position[1], position[1] + height):
        row = floor["map"][y]
        floor["map"][y] = row[:position[0]] + "#" * width + row[position[0] + width:]


def place_random_npc(floor, npc_type, *, regions=None):
    footprint = NPC_FOOTPRINTS[npc_type]
    position, approaches = find_fixture_position(floor, footprint, regions=regions)
    npc = {"type": npc_type, "position": position}
    if npc_type == "rune_master":
        npc["room_entrance"] = random.choice(sorted(approaches))
    floor.setdefault("npcs", []).append(npc)
    occupy_fixture(floor, position, footprint)
