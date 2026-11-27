from acts.act_three.npcs import get_npc_cells


def spawn_regions(floor):
    return floor.get("spawn_regions", [{
        "left": 0,
        "top": 0,
        "right": len(floor["map"][0]),
        "bottom": len(floor["map"]),
        "enabled": floor.get("enemy_spawn_mode", False),
        "ore_spawn_mode": floor.get("ore_spawn_mode", floor.get("enemy_spawn_mode", False)),
        "ore_types": floor.get("ore_types", ()),
        "ore_count": floor.get("ore_count"),
    }])


def inside_region(position, region):
    x, y = position
    return region["left"] <= x < region["right"] and region["top"] <= y < region["bottom"]


def room_entrances(floor):
    connectors = {connector["position"] for connector in floor.get("connectors", [])}
    return connectors | {position for edge in floor.get("room_connections", []) for position in edge}


def reserved_spawn_positions(floor):
    positions = {floor["player_start"], floor["stairs"]}
    positions.update(chest["position"] for chest in floor["chests"])
    positions.update(crate["position"] for crate in floor.get("breakable_crates", []))
    positions.update(floor["potions"])
    positions.update(ore["position"] for ore in floor.get("ores", []))
    for npc in floor.get("npcs", []):
        positions.update(get_npc_cells(npc))
        if npc["type"] == "rune_master" and npc.get("room_entrance") is not None:
            positions.add(npc["room_entrance"])
    rune_trial = floor.get("rune_trial")
    if rune_trial is not None:
        positions.update((rune_trial["start"], rune_trial["entrance"], rune_trial["door"]))
    trader_altar = floor.get("trader_altar")
    if trader_altar is not None:
        positions.update((trader_altar[0] + dx, trader_altar[1] + dy) for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)))
    for passage in floor.get("passages", []):
        positions.update((passage["wall_position"], passage["trigger_position"]))
    return positions - {None}
