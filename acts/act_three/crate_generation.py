import random
from collections import defaultdict
from math import ceil

from acts.act_three.enemies.generation import enemy_spawn_cells
from acts.act_three.environment_objects import breakable_environment_gids
from acts.act_three.settings import (
    ACT_THREE_CELLS_PER_CRATE,
    ACT_THREE_MAX_CRATES_PER_ROOM,
)
from acts.act_three.spawn_regions import (
    inside_region,
    reserved_spawn_positions,
    room_entrances,
    spawn_regions,
)
from acts.act_three.world_geometry import reachable_cells


def _room_edges(cells):
    columns_by_row = defaultdict(list)
    rows_by_column = defaultdict(list)
    for column, row in cells:
        columns_by_row[row].append(column)
        rows_by_column[column].append(row)

    return {
        (column, row)
        for row, columns in columns_by_row.items()
        for column in (min(columns), max(columns))
    } | {
        (column, row)
        for column, rows in rows_by_column.items()
        for row in (min(rows), max(rows))
    }


def populate_act_three_crates(floor):
    regions = [region for region in spawn_regions(floor) if region["enabled"]]
    if not regions:
        return

    variants = sorted(breakable_environment_gids())
    if not variants:
        return

    dungeon_map = floor["map"]
    layers = floor["tile_layers"]
    ground = {
        (column, row)
        for row, tiles in enumerate(layers.get("Ground", []))
        for column, gid in enumerate(tiles)
        if gid and dungeon_map[row][column] == "."
    }
    occupied = reserved_spawn_positions(floor)
    occupied.update(floor["torches"])
    for enemy in floor["enemies"]:
        occupied.update(enemy_spawn_cells(enemy["type"], enemy["position"]))
    for name, layer in layers.items():
        if name.split("_", 1)[0] not in ("Ground", "GroundDetails"):
            occupied.update(
                (column, row)
                for row, tiles in enumerate(layer)
                for column, gid in enumerate(tiles)
                if gid
            )
    for column, row in room_entrances(floor):
        occupied.update((
            (column, row), (column - 1, row), (column + 1, row),
            (column, row - 1), (column, row + 1),
        ))

    crates = floor.setdefault("breakable_crates", [])
    blocked = {item["position"] for item in (*crates, *floor["chests"])}
    origin = floor["player_start"]
    barriers = floor["barriers"]
    reachable = reachable_cells(dungeon_map, origin, barriers, blocked=blocked)
    for region in regions:
        room_cells = {cell for cell in ground if inside_region(cell, region)}
        limit = min(
            ACT_THREE_MAX_CRATES_PER_ROOM,
            ceil(len(room_cells) / ACT_THREE_CELLS_PER_CRATE),
        )
        remaining = limit - sum(inside_region(crate["position"], region) for crate in crates)
        if remaining <= 0:
            continue

        candidates = sorted((_room_edges(room_cells) & reachable) - occupied)
        random.shuffle(candidates)
        for cell in candidates:
            blocked.add(cell)
            remaining_reachable = reachable_cells(dungeon_map, origin, barriers, blocked=blocked)
            if len(remaining_reachable) != len(reachable) - 1:
                blocked.remove(cell)
                continue

            crates.append({"position": cell, "variant": random.choice(variants)})
            reachable = remaining_reachable
            remaining -= 1
            if remaining == 0:
                break
