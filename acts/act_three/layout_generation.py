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


def _required_openings(rooms):
    required = Counter()
    for room in rooms:
        connectors = _structural_connectors(room)
        if len(connectors) != 1:
            return Counter()
        required[OPPOSITE_DIRECTION[connectors[0]["direction"]]] += 1
    return required


def _opening_deficits(frontier, required):
    available = Counter(opening["direction"] for opening in frontier)
    return {direction: max(0, count - available[direction]) for direction, count in required.items()}


def _frontier_after_option(frontier, option):
    index, template, connector, _ = option
    return frontier[:index] + frontier[index + 1:] + [
        item for item in _structural_connectors(template) if item is not connector
    ]


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


def _valid_floor(floor):
    if _structural_connectors(floor):
        return False
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
    required_templates = [
        load_tmx_floor(project_root / path)
        for path in config.get("required_room_paths", ())
    ]
    required_sources = {template["source_path"] for template in required_templates}
    templates = [template for template in templates if template["source_path"] not in required_sources]
    for template in [entry, exit_room, *templates, *required_templates]:
        _validate_template(template)
    dead_ends = [template for template in templates if len(_structural_connectors(template)) == 1]
    connecting_rooms = [template for template in templates if len(_structural_connectors(template)) > 1]
    if not connecting_rooms or not dead_ends:
        raise ValueError("Act Three needs connecting rooms and dead ends")

    required_rooms = [exit_room, *required_templates]
    if trial is not None:
        required_rooms.append(trial)
    required_openings = _required_openings(required_rooms)
    maximum_openings = {
        direction: max(
            sum(connector["direction"] == direction for connector in _structural_connectors(room))
            for room in connecting_rooms
        )
        for direction in required_openings
    }
    target_count = config["generated_piece_count"] - 1 - len(required_rooms)
    remaining_attempts = 0

    def finish(placements, frontier, connections, required):
        nonlocal remaining_attempts
        if remaining_attempts <= 0 or len(frontier) < len(required):
            return None
        remaining_attempts -= 1

        if not frontier:
            floor = _compose(placements, connections)
            _seal_boundaries(floor, placements, connections)
            return floor if _valid_floor(floor) else None

        if required:
            demands = _required_openings(required)
            if any(_opening_deficits(frontier, demands).values()):
                return None
            if demands:
                choices = [
                    (index, _options(placements, frontier, [room]))
                    for index, room in enumerate(required)
                ]
                required_index, options = min(choices, key=lambda choice: len(choice[1]))
            else:
                required_index = 0
                options = _options(placements, frontier, required[:1])
            next_required = required[:required_index] + required[required_index + 1:]
        else:
            options_by_opening = [[] for _ in frontier]
            for option in _options(placements, frontier, dead_ends):
                options_by_opening[option[0]].append(option)
            options = min(options_by_opening, key=len)
            next_required = required

        for option in options:
            if remaining_attempts <= 0:
                break
            result = finish(*_extend(placements, frontier, connections, option), next_required)
            if result is not None:
                return result
        return None

    def search(placements, frontier, connections, count):
        nonlocal remaining_attempts
        if remaining_attempts <= 0:
            return None
        deficits = _opening_deficits(frontier, required_openings)
        if any(deficit > count * maximum_openings[direction] for direction, deficit in deficits.items()):
            return None
        if count == 0:
            return finish(placements, frontier, connections, required_rooms)
        remaining_attempts -= 1

        usage = Counter(template["source_path"] for template, _ in placements)
        options = _options(placements, frontier, connecting_rooms)
        needs_branches = any(deficits.values())

        def priority(option):
            next_frontier = _frontier_after_option(frontier, option)
            return (
                sum(_opening_deficits(next_frontier, required_openings).values()),
                -len(next_frontier) if needs_branches else 0,
                usage[option[1]["source_path"]],
            )

        options.sort(key=priority)
        for option in options:
            if remaining_attempts <= 0:
                break
            result = search(*_extend(placements, frontier, connections, option), count - 1)
            if result is not None:
                return result
        return None

    for count in range(target_count, max(-1, target_count - 3), -1):
        remaining_attempts = 4000
        result = search([(entry, (0, 0))], _structural_connectors(entry), [], count)
        if result is not None:
            return result
    raise ValueError("Cannot assemble Act Three with all room connectors joined; check room shapes and dead-end directions")
