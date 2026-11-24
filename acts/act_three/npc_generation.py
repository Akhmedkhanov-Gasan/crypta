import random
from pathlib import Path

from acts.act_three.enemies.generation import enemy_spawn_cells
from acts.act_three.npcs import get_npc_cells
from acts.act_three.spawn_regions import (
    inside_region,
    reserved_spawn_positions,
    room_entrances,
    spawn_regions,
)
from acts.act_three.world_geometry import reachable_cells
from systems.grid_geometry import can_reach_adjacent_cell


def place_random_trader(floor):
    place_random_npc(floor, "trader")


def place_random_npc(floor, npc_type):
    regions = [
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
        npc = {"type": npc_type, "position": position}
        cells = get_npc_cells(npc)
        if not cells <= available or not any(
            all(inside_region(cell, region) for cell in cells) for region in regions
        ):
            continue
        x, y = position
        if not can_reach_adjacent_cell(dungeon_map, position, (x + 1, y), barriers):
            continue
        candidates.append(npc)
    random.shuffle(candidates)
    for npc in candidates:
        cells = get_npc_cells(npc)
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
        if npc_type == "rune_master":
            npc["room_entrance"] = random.choice(sorted(approaches))
        floor.setdefault("npcs", []).append(npc)
        for x, y in cells:
            row = dungeon_map[y]
            dungeon_map[y] = row[:x] + "#" + row[x + 1:]
        return
    raise ValueError(f"No reachable position for the Act Three {npc_type}.")
