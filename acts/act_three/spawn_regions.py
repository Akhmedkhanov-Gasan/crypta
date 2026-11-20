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
    altar = floor.get("upgrade_altar")
    if altar is not None:
        positions.update((altar[0] + x, altar[1] + y) for x in range(2) for y in range(2))
    for passage in floor.get("passages", []):
        positions.update((passage["wall_position"], passage["trigger_position"]))
    return positions - {None}
