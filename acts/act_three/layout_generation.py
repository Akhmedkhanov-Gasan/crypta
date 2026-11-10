import random
from collections import Counter
from pathlib import Path

from acts.act_three.room_generation import (
    DIRECTION_STEP,
    OPPOSITE_DIRECTION,
    _bounds,
    _bounds_overlap,
    _compose,
    _placement_offset,
    _structural_connectors,
    _template_paths,
    _translated,
)
from acts.act_three.tmx_loader import load_tmx_floor
from acts.act_three.world_geometry import reachable_cells


def _validate_template(template):
    connectors = _structural_connectors(template)
    name = Path(template["source_path"]).name
    if not connectors:
        raise ValueError(f"Room needs structural connectors: {name}")
    origin = template["player_start"] or connectors[0]["position"]
    reachable = reachable_cells(template["map"], origin, template["barriers"])
    for connector in connectors:
        x, y = connector["position"]
        direction = connector["direction"]
        boundary = {
            "north": y == 0,
            "south": y == template["height"] - 1,
            "west": x == 0,
            "east": x == template["width"] - 1,
        }
        dx, dy = DIRECTION_STEP[direction]
        if connector["width"] != 1 or not boundary[direction]:
            raise ValueError(f"Connector must be one cell wide on the map boundary: {name}: {connector['name']}")
        if (x, y) not in reachable or (x - dx, y - dy) not in reachable:
            raise ValueError(f"Connector is blocked or unreachable: {name}: {connector['name']}")


def _options(placements, frontier, templates):
    options = []
    for frontier_index, opening in enumerate(frontier):
        for template in templates:
            for connector in _structural_connectors(template):
                if connector["direction"] != OPPOSITE_DIRECTION[opening["direction"]]:
                    continue
                if connector["width"] != opening["width"] or connector["width"] != 1:
                    continue
                offset = _placement_offset(opening, connector)
                if any(_bounds_overlap(_bounds(template, offset), _bounds(placed, position)) for placed, position in placements):
                    continue
                options.append((frontier_index, template, connector, offset))
    random.shuffle(options)
    return options


def _extend(placements, frontier, connections, option):
    index, template, connector, offset = option
    opening = frontier[index]
    remaining = frontier[:index] + frontier[index + 1:]
    remaining.extend(
        {**item, "position": _translated(item["position"], offset)}
        for item in _structural_connectors(template)
        if item is not connector
    )
    return (
        placements + [(template, offset)],
        remaining,
        connections + [(opening["position"], _translated(connector["position"], offset))],
    )


def _seal_boundaries(floor, placements, connections):
    min_x = min(offset[0] for _, offset in placements)
    min_y = min(offset[1] for _, offset in placements)
    connected = {tuple(sorted(edge)) for edge in connections}
    for template, offset in placements:
        left, top, right, bottom = _bounds(template, offset)
        edges = []
        for x in range(left, right):
            edges.extend([((x, top - 1), (x, top)), ((x, bottom - 1), (x, bottom))])
        for y in range(top, bottom):
            edges.extend([((left - 1, y), (left, y)), ((right - 1, y), (right, y))])
        for edge in edges:
            if tuple(sorted(edge)) not in connected:
                floor["barriers"].add(tuple(sorted((
                    (edge[0][0] - min_x, edge[0][1] - min_y),
                    (edge[1][0] - min_x, edge[1][1] - min_y),
                ))))
    for connector in floor["connectors"]:
        if connector["name"] not in {"exit_north", "exit_south", "exit_east", "exit_west"}:
            continue
        position = connector["position"]
        dx, dy = DIRECTION_STEP[connector["direction"]]
        inside = position[0] - dx, position[1] - dy
        floor["barriers"].add(tuple(sorted((position, inside))))


def _valid_floor(floor):
    reachable = reachable_cells(floor["map"], floor["player_start"], floor["barriers"])
    exits = [item for item in floor["connectors"] if item["name"] in ("exit_up", "exit_next_floor")]
    if not exits:
        return False
    trial_door = floor.get("trial_entrance")
    for edge in floor["room_connections"]:
        if any(position not in reachable and position != trial_door for position in edge):
            return False
    for connector in exits:
        x, y = connector["position"]
        if (x, y + 1) not in reachable:
            return False
    entrance = floor.get("trial_entrance")
    return entrance is None or (entrance[0], entrance[1] + 1) in reachable


def generate_room_layout(config, trial_path=None):
    project_root = Path(__file__).resolve().parents[2]
    entry_path = project_root / config["map_path"]
    exit_path = project_root / config["exit_map_path"]
    entry = load_tmx_floor(entry_path)
    exit_room = load_tmx_floor(exit_path)
    templates = [
        load_tmx_floor(path)
        for path in _template_paths(project_root / config["room_template_directory"], entry_path)
        if path != exit_path
    ]
    trial = load_tmx_floor(project_root / trial_path) if trial_path else None
    if not templates:
        raise ValueError("Act Three needs at least one room template")
    for template in [entry, exit_room, *templates]:
        _validate_template(template)
    target_count = config["generated_piece_count"] - 2 - (trial is not None)
    target_count = max(len(templates), target_count)
    remaining_attempts = [4000]

    def search(placements, frontier, connections, count):
        remaining_attempts[0] -= 1
        if remaining_attempts[0] <= 0:
            return None
        if count == target_count:
            states = [(placements, frontier, connections)]
            if trial is not None:
                states = [_extend(*states[0], option) for option in _options(placements, frontier, [trial])]
            for state in states:
                for option in _options(state[0], state[1], [exit_room]):
                    final_placements, _, final_connections = _extend(*state, option)
                    floor = _compose(final_placements, final_connections)
                    _seal_boundaries(floor, final_placements, final_connections)
                    if _valid_floor(floor):
                        return floor
            return None
        usage = Counter(template["source_path"] for template, _ in placements)
        candidates = [template for template in templates if not usage[template["source_path"]]]
        options = _options(placements, frontier, candidates or templates)
        options.sort(key=lambda option: usage[option[1]["source_path"]])
        for option in options:
            if remaining_attempts[0] <= 0:
                break
            result = search(*_extend(placements, frontier, connections, option), count + 1)
            if result is not None:
                return result
        return None

    result = search([(entry, (0, 0))], [dict(item) for item in _structural_connectors(entry)], [], 0)
    if result is None:
        raise ValueError("Cannot assemble a reachable Act Three floor; check room connectors, Blocked and Barriers in Tiled")
    return result
