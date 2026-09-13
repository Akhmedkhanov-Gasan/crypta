"""Compose small Act III floors from hand-authored TMX templates."""

from __future__ import annotations

import random
from pathlib import Path

import resource_store as resources

from acts.act_three.tmx_loader import load_tmx_floor


OPPOSITE_DIRECTION = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}

DIRECTION_STEP = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


def _template_paths(directory, spawn_path):
    directory = Path(directory)
    paths = {
        *resources.glob_resources(directory, "room_*.tmx"),
        *resources.glob_resources(directory, "corridor_*.tmx"),
        *resources.glob_resources(directory, "test_room_*.tmx"),
    }
    return sorted(path for path in paths if path != Path(spawn_path))


def _translated(position, offset):
    return position[0] + offset[0], position[1] + offset[1]


def _placement_offset(open_connector, template_connector):
    step = DIRECTION_STEP[open_connector["direction"]]
    target_position = (
        open_connector["position"][0] + step[0],
        open_connector["position"][1] + step[1],
    )
    return (
        target_position[0] - template_connector["position"][0],
        target_position[1] - template_connector["position"][1],
    )


def _bounds(template, offset):
    return (
        offset[0],
        offset[1],
        offset[0] + template["width"],
        offset[1] + template["height"],
    )


def _bounds_overlap(first, second):
    return (
        first[0] < second[2]
        and first[2] > second[0]
        and first[1] < second[3]
        and first[3] > second[1]
    )


def _shift_edge(edge, offset):
    return tuple(sorted((_translated(edge[0], offset), _translated(edge[1], offset))))


def _shift_entities(items, offset):
    shifted = []
    for item in items:
        shifted_item = dict(item)
        shifted_item["position"] = _translated(item["position"], offset)
        shifted.append(shifted_item)
    return shifted


def _compose(placements, connections):
    min_column = min(offset[0] for _, offset in placements)
    min_row = min(offset[1] for _, offset in placements)
    max_column = max(
        offset[0] + template["width"]
        for template, offset in placements
    )
    max_row = max(
        offset[1] + template["height"]
        for template, offset in placements
    )
    normalization = (-min_column, -min_row)
    width = max_column - min_column
    height = max_row - min_row

    dungeon_map = [["#" for _ in range(width)] for _ in range(height)]
    layer_names = tuple(
        dict.fromkeys(
            name
            for template, _ in placements
            for name in template["tile_layers"]
        )
    )
    layers = {
        name: [[0 for _ in range(width)] for _ in range(height)]
        for name in layer_names
    }
    barriers = set()
    torches = []
    enemies = []
    chests = []
    potions = []
    upgrade_altar = None
    open_connectors = []

    for template, original_offset in placements:
        offset = (
            original_offset[0] + normalization[0],
            original_offset[1] + normalization[1],
        )
        for row, map_row in enumerate(template["map"]):
            for column, value in enumerate(map_row):
                dungeon_map[row + offset[1]][column + offset[0]] = value

        for layer_name, layer in template["tile_layers"].items():
            for row, layer_row in enumerate(layer):
                for column, gid in enumerate(layer_row):
                    if gid:
                        layers[layer_name][row + offset[1]][column + offset[0]] = gid

        barriers.update(
            _shift_edge(edge, offset)
            for edge in template["barriers"]
        )
        torches.extend(
            _translated(position, offset)
            for position in template["torches"]
        )
        enemies.extend(_shift_entities(template["enemies"], offset))
        chests.extend(_shift_entities(template["chests"], offset))
        potions.extend(
            _translated(position, offset)
            for position in template["potions"]
        )
        if (
            upgrade_altar is None
            and template.get("upgrade_altar") is not None
        ):
            upgrade_altar = _translated(
                template["upgrade_altar"],
                offset,
            )
        open_connectors.extend(
            {
                **connector,
                "position": _translated(connector["position"], offset),
            }
            for connector in template["connectors"]
        )

    shifted_connections = {
        tuple(
            sorted(
                (
                    _translated(first, normalization),
                    _translated(second, normalization),
                )
            )
        )
        for first, second in connections
    }
    barriers.difference_update(shifted_connections)
    connected_positions = {
        position
        for edge in shifted_connections
        for position in edge
    }
    open_connectors = [
        connector
        for connector in open_connectors
        if connector["position"] not in connected_positions
    ]

    spawn_template, spawn_offset = placements[0]

    if spawn_template["player_start"] is None:
        raise ValueError(
            "The first TMX template must contain a Spawn entity"
        )

    player_start = _translated(
        spawn_template["player_start"],
        (
            spawn_offset[0] + normalization[0],
            spawn_offset[1] + normalization[1],
        ),
    )
    fallback_stairs = next(
        (
            (column, row)
            for row in range(height - 1, -1, -1)
            for column in range(width - 1, -1, -1)
            if dungeon_map[row][column] == "."
        ),
        player_start,
    )

    return {
        "map": ["".join(row) for row in dungeon_map],
        "player_start": player_start,
        "enemies": enemies,
        "chests": chests,
        "potions": potions,
        "torches": torches,
        "upgrade_altar": upgrade_altar,
        "tile_layers": layers,
        "barriers": barriers,
        "connectors": open_connectors,
        "stairs": fallback_stairs,
        "boss_door": None,
        "boss_room": None,
        "boss_columns": [],
        "boss_emitters": [],
        "seal_boss_door_during_fight": False,
        "visual_seed": random.randrange(1_000_000),
        "generated_pieces": [
            Path(template["source_path"]).name
            for template, _ in placements
        ],
    }


def generate_tmx_room_floor(spawn_path, template_directory, piece_count=2):
    project_root = Path(__file__).resolve().parents[2]
    spawn_path = Path(spawn_path)
    template_directory = Path(template_directory)

    if not spawn_path.is_absolute():
        spawn_path = project_root / spawn_path
    if not template_directory.is_absolute():
        template_directory = project_root / template_directory

    spawn = load_tmx_floor(spawn_path)
    templates = [
        load_tmx_floor(path)
        for path in _template_paths(template_directory, spawn_path)
    ]
    placements = [(spawn, (0, 0))]
    open_connectors = [dict(connector) for connector in spawn["connectors"]]
    connections = []

    while len(placements) < piece_count and open_connectors and templates:
        options = []
        for open_index, open_connector in enumerate(open_connectors):
            direction = open_connector.get("direction", "")
            expected_direction = OPPOSITE_DIRECTION.get(direction)
            if expected_direction is None:
                continue
            for template_index, template in enumerate(templates):
                for connector_index, connector in enumerate(template["connectors"]):
                    if (
                        connector.get("direction") != expected_direction
                        or connector.get("width", 1)
                        != open_connector.get("width", 1)
                    ):
                        continue
                    offset = _placement_offset(open_connector, connector)
                    candidate_bounds = _bounds(template, offset)
                    if any(
                        _bounds_overlap(candidate_bounds, _bounds(placed, placed_offset))
                        for placed, placed_offset in placements
                    ):
                        continue
                    options.append(
                        (
                            open_index,
                            template_index,
                            connector_index,
                            offset,
                        )
                    )

        if not options:
            break

        open_index, template_index, connector_index, offset = random.choice(options)
        open_connector = open_connectors.pop(open_index)
        template = templates[template_index]
        used_connector = template["connectors"][connector_index]
        used_world_position = _translated(used_connector["position"], offset)
        connections.append((open_connector["position"], used_world_position))
        placements.append((template, offset))
        open_connectors.extend(
            {
                **connector,
                "position": _translated(connector["position"], offset),
            }
            for index, connector in enumerate(template["connectors"])
            if index != connector_index
        )

    return _compose(placements, connections)


def _structural_connectors(template):
    structural_names = {
        "exit_north",
        "exit_south",
        "exit_east",
        "exit_west",
    }
    return [
        connector
        for connector in template["connectors"]
        if connector.get("name") in structural_names
    ]


def generate_tmx_sequence_floor(template_paths):
    project_root = Path(__file__).resolve().parents[2]
    resolved_paths = []

    for template_path in template_paths:
        resolved_path = Path(template_path)
        if not resolved_path.is_absolute():
            resolved_path = project_root / resolved_path
        resolved_paths.append(resolved_path)

    templates = [
        load_tmx_floor(path)
        for path in resolved_paths
    ]

    if not templates:
        raise ValueError("TMX room sequence cannot be empty")

    placements = [(templates[0], (0, 0))]
    connections = []
    first_connectors = _structural_connectors(templates[0])

    if not first_connectors and len(templates) > 1:
        raise ValueError(
            f"No structural connector in {resolved_paths[0].name}"
        )

    open_connector = (
        random.choice(first_connectors)
        if first_connectors
        else None
    )

    for sequence_index, template in enumerate(
        templates[1:],
        start=1,
    ):
        expected_direction = OPPOSITE_DIRECTION.get(
            open_connector.get("direction", "")
        )
        options = []

        for connector in _structural_connectors(template):
            if (
                connector.get("direction") != expected_direction
                or connector.get("width", 1)
                != open_connector.get("width", 1)
            ):
                continue

            offset = _placement_offset(
                open_connector,
                connector,
            )
            candidate_bounds = _bounds(template, offset)

            if any(
                _bounds_overlap(
                    candidate_bounds,
                    _bounds(placed_template, placed_offset),
                )
                for placed_template, placed_offset in placements
            ):
                continue

            options.append((connector, offset))

        if not options:
            raise ValueError(
                "Cannot connect "
                f"{resolved_paths[sequence_index - 1].name} "
                f"to {resolved_paths[sequence_index].name}"
            )

        used_connector, offset = random.choice(options)
        used_world_position = _translated(
            used_connector["position"],
            offset,
        )

        connections.append(
            (
                open_connector["position"],
                used_world_position,
            )
        )
        placements.append((template, offset))

        if sequence_index >= len(templates) - 1:
            continue

        outgoing_connectors = [
            {
                **connector,
                "position": _translated(
                    connector["position"],
                    offset,
                ),
            }
            for connector in _structural_connectors(template)
            if connector is not used_connector
        ]

        if not outgoing_connectors:
            raise ValueError(
                f"No outgoing connector in "
                f"{resolved_paths[sequence_index].name}"
            )

        open_connector = random.choice(outgoing_connectors)

    return _compose(placements, connections)


def _passage_positions(connector):
    name = connector.get("name", "")
    direction = connector.get("direction", "")

    if name in ("exit_up", "exit_next_floor"):
        direction = "north"

    step = DIRECTION_STEP.get(direction)
    if step is None:
        return None

    wall_position = connector["position"]
    trigger_position = (
        wall_position[0] - step[0],
        wall_position[1] - step[1],
    )
    return wall_position, trigger_position


def attach_act_three_passages(
    floor,
    floor_index,
    floor_count,
):
    passages = []

    for connector in floor.get("connectors", []):
        name = connector.get("name", "")

        if name in ("exit_up", "exit_next_floor"):
            target_floor_index = (
                floor_index + 1
                if floor_index + 1 < floor_count
                else None
            )
        elif name == "exit_back":
            target_floor_index = (
                floor_index - 1
                if floor_index > 0
                else None
            )
        else:
            continue

        positions = _passage_positions(connector)
        if positions is None:
            continue

        wall_position, trigger_position = positions

        passages.append(
            {
                "passage_id": name,
                "wall_position": wall_position,
                "trigger_position": trigger_position,
                "target_floor_index": target_floor_index,
                "target_passage_id": None,
                "requires_clear": False,
            }
        )

    floor["passages"] = passages
    return floor
