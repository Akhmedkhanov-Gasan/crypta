from acts.act_three.items.inventory import ORE_ITEM_NAMES
from acts.act_three.mining.catalog import ORE_TYPES


def build_ores(by_name, dungeon_map):
    ores = []
    occupied = set()

    markers = (
        (ore_type, definition, position, properties)
        for ore_type, definition in ORE_TYPES.items()
        for marker in definition["markers"]
        for position, properties in by_name.get(marker, [])
    )
    for ore_type, definition, position, properties in markers:
        column, row = position
        stage = int(properties.get("state", "1")) - 1

        if not (
            0 <= row < len(dungeon_map)
            and 0 <= column < len(dungeon_map[row])
            and 0 <= stage <= 3
            and position not in occupied
        ):
            raise ValueError(f"Invalid {ORE_ITEM_NAMES[definition['item']]} marker: {position!r}")

        occupied.add(position)
        dungeon_map[row][column] = "." if stage == 3 else "#"
        ores.append(
            {
                "type": ore_type,
                "position": position,
                "stage": stage,
            }
        )

    return ores


def clear_ore_collision(floor, position):
    column, row = position
    map_row = floor.map[row]
    if map_row[column] == "#":
        floor.map[row] = map_row[:column] + "." + map_row[column + 1:]


def get_ore_at(floor, position):
    return next(
        (
            ore
            for ore in floor.act_three_ores
            if ore["position"] == position
        ),
        None,
    )
