import random

from acts.act_three.crate_generation import _room_edges
from acts.act_three.enemies.generation import enemy_spawn_cells
from acts.act_three.spawn_regions import inside_region, reserved_spawn_positions, room_entrances, spawn_regions
from acts.act_three.world_geometry import reachable_cells


CHEST_LOOT = (
    ("healing_scroll", 14),
    ("scroll_of_stoneflesh", 14),
    ("scroll_of_binding", 14),
    ("scroll_of_arcane_impulse", 14),
    ("ironblood_tonic", 10),
    ("burial_relic", 10),
    ("blast_charge", 8),
    ("flash_bomb", 8),
    ("spring_trap", 6),
    ("gemstone", 6),
    ("fire_bomb", 6),
)


def populate_act_three_chests(floor, act_floor):
    if act_floor < 2:
        return
    regions = [region for region in spawn_regions(floor) if region["enabled"]]
    if not regions:
        return
    occupied = reserved_spawn_positions(floor) | set(floor.get("trial_safe_cells", ()))
    occupied.update(floor.get("torches", ()))
    for enemy in floor["enemies"]:
        occupied.update(enemy_spawn_cells(enemy["type"], enemy["position"]))
    layers = floor.get("tile_layers", {})
    for name, layer in layers.items():
        if name.split("_", 1)[0] not in ("Ground", "GroundDetails"):
            occupied.update((x, y) for y, row in enumerate(layer) for x, gid in enumerate(row) if gid)
    entrances = room_entrances(floor)
    occupied.update((x + dx, y + dy) for x, y in entrances for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    blocked = {item["position"] for item in (*floor["chests"], *floor.get("breakable_crates", []))}
    origin = floor["player_start"]
    reachable = reachable_cells(floor["map"], origin, floor.get("barriers", ()), blocked=blocked)
    ground = {(x, y) for y, row in enumerate(layers.get("Ground", [])) for x, gid in enumerate(row) if gid and (x, y) in reachable}
    carriers = [enemy for enemy in floor["enemies"] if not enemy.get("boss_group") and enemy["position"] in reachable and enemy["position"] not in floor.get("trial_safe_cells", ())]
    for enemy in floor["enemies"]:
        enemy["has_key"] = False
    for chest in floor["chests"]:
        if chest.get("requires_key", True):
            if not _assign_carrier(chest, carriers, floor, reachable, blocked):
                raise ValueError("A locked Act Three chest requires a reachable key carrier.")
    random.shuffle(regions)
    limit = 4 if act_floor == 2 else 5
    for region in regions * 2:
        if len(floor["chests"]) >= limit or not carriers:
            break
        if sum(inside_region(chest["position"], region) for chest in floor["chests"]) >= 2:
            continue
        cells = {cell for cell in ground if inside_region(cell, region)}
        edges = _room_edges(cells)
        candidates = sorted((cells & reachable) - occupied)
        random.shuffle(candidates)
        candidates.sort(key=lambda cell: cell not in edges)
        for cell in candidates:
            if not any(inside_region(enemy["position"], region) for enemy in carriers):
                break
            remaining = reachable_cells(floor["map"], origin, floor.get("barriers", ()), blocked=blocked | {cell})
            if remaining != reachable - {cell}:
                continue
            chest = {
                "position": cell,
                "contains": random.choices(
                    [item for item, _ in CHEST_LOOT],
                    weights=[weight for _, weight in CHEST_LOOT],
                    k=1,
                )[0],
                "requires_key": True,
            }
            if not _assign_carrier(chest, carriers, floor, remaining, blocked | {cell}, region):
                continue
            floor["chests"].append(chest)
            occupied.add(cell)
            blocked.add(cell)
            reachable = remaining
            break


def _assign_carrier(chest, carriers, floor, reachable, blocked, region=None):
    from collections import deque

    origin = chest["position"]
    distances = {origin: 0}
    pending = deque([origin])
    from systems.grid_geometry import can_reach_adjacent_cell

    while pending:
        cell = pending.popleft()
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            target = cell[0] + dx, cell[1] + dy
            if target in distances or target not in reachable or target in blocked:
                continue
            if can_reach_adjacent_cell(floor["map"], cell, target, floor.get("barriers", ())):
                distances[target] = distances[cell] + 1
                pending.append(target)
    options = [enemy for enemy in carriers if enemy["position"] in distances and (region is None or inside_region(enemy["position"], region))]
    if not options:
        return False
    enemy = min(options, key=lambda item: distances[item["position"]])
    enemy["has_key"] = True
    carriers.remove(enemy)
    return True
