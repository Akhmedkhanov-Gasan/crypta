import random
from collections import Counter
from pathlib import Path

from acts.act_three.room_generation import (
    DIRECTION_STEP,
    OPPOSITE_DIRECTION,
    _bounds,
    _compose,
    _structural_connectors,
    _template_paths,
    _passage_positions,
)
from acts.act_three.room_connections import (
    extend_layout as _extend,
    placement_options as _options,
)
from acts.act_three.tmx_loader import load_tmx_floor
from acts.act_three.world_geometry import reachable_cells
from acts.act_three.loop_generation import connect_openings
from acts.act_three.floor_templates import floor_template_pairs


class LayoutSearchExhausted(ValueError):
    pass


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


def _required_openings(rooms):
    required = Counter()
    for room in rooms:
        connectors = _structural_connectors(room)
        if len(connectors) != 1:
            continue
        required[OPPOSITE_DIRECTION[connectors[0]["direction"]]] += 1
    return required


def _opening_deficits(frontier, required):
    grouped_openings = Counter(
        (opening.get("room_origin"), opening["direction"])
        for opening in frontier
    )
    available = Counter(
        direction
        for (_, direction), count in grouped_openings.items()
        if count == 1
    )
    return {direction: max(0, count - available[direction]) for direction, count in required.items()}


def _paired_openings(frontier):
    groups = {}
    for opening in frontier:
        key = opening.get("room_origin"), opening["direction"]
        groups.setdefault(key, []).append(opening)
    return [openings for openings in groups.values() if len(openings) > 1]


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
    exits = [item for item in floor["connectors"] if item["name"] in ("exit_down", "exit_next_floor")]
    if not exits:
        return False
    trial_door = floor.get("trial_entrance")
    for edge in floor["room_connections"]:
        if any(position not in reachable and position != trial_door for position in edge):
            return False
    for connector in exits:
        positions = _passage_positions(connector)
        if positions is None or positions[1] not in reachable:
            return False
    for connector in floor["connectors"]:
        if connector["name"] in ("exit_up", "exit_back"):
            positions = _passage_positions(connector)
            if positions is None or positions[1] not in reachable:
                return False
    entrance = floor.get("trial_entrance")
    return entrance is None or (entrance[0], entrance[1] + 1) in reachable


def generate_room_layout(config, trial_path=None):
    project_root = Path(__file__).resolve().parents[2]
    pairs = floor_template_pairs(config)
    required_templates = [
        load_tmx_floor(project_root / path)
        for path in config.get("required_room_paths", ())
    ]
    required_sources = {template["source_path"] for template in required_templates}
    templates = [
        load_tmx_floor(path)
        for path in _template_paths(project_root / config["room_template_directory"], project_root / config["map_path"])
    ]
    templates = [template for template in templates if template["source_path"] not in required_sources]
    trial = load_tmx_floor(project_root / trial_path) if trial_path else None
    variants = {room["source_path"]: room for pair in pairs for room in pair}
    for template in [*variants.values(), *templates, *required_templates]:
        _validate_template(template)
    failures = []
    for thorough in (False, True):
        for entry, exit_room in pairs:
            try:
                return _generate_room_layout(
                    config, trial, entry, exit_room, templates, required_templates,
                    thorough=thorough,
                )
            except LayoutSearchExhausted:
                if thorough:
                    failures.append(f"{Path(entry['source_path']).name} / {Path(exit_room['source_path']).name}")
    raise LayoutSearchExhausted(
        "Cannot assemble Act Three after searching all entry/exit pairs: " + "; ".join(failures)
    )


def _generate_room_layout(config, trial, entry, exit_room, templates, required_templates, *, thorough=True):
    allow_dead_ends = config.get("allow_dead_ends", True)
    dead_ends = [
        template for template in templates
        if allow_dead_ends and len(_structural_connectors(template)) == 1
    ]
    connecting_rooms = [template for template in templates if len(_structural_connectors(template)) > 1]
    corridors = [template for template in connecting_rooms if len(_structural_connectors(template)) == 2]
    branch_rooms = [
        room for room in connecting_rooms
        if len({connector["direction"] for connector in _structural_connectors(room)}) > 1
    ]
    featured_rooms = []
    layout_rooms = []
    for room in branch_rooms:
        directions = Counter(connector["direction"] for connector in _structural_connectors(room))
        if max(directions.values()) > 1:
            featured_rooms.append(room)
        else:
            layout_rooms.append(room)
    featured_rooms = featured_rooms or branch_rooms
    layout_rooms = layout_rooms or branch_rooms
    if not connecting_rooms or (allow_dead_ends and not dead_ends):
        raise ValueError("Act Three has no templates to complete the floor")

    required_rooms = [entry, exit_room, *required_templates]
    if trial is not None:
        required_rooms.append(trial)
    required_openings = _required_openings(required_rooms)
    required_growth = Counter()
    for room in required_rooms:
        connectors = _structural_connectors(room)
        if len(connectors) > 1:
            required_growth.update(connector["direction"] for connector in connectors)
    maximum_openings = {
        direction: max(
            sum(connector["direction"] == direction for connector in _structural_connectors(room))
            for room in connecting_rooms
        )
        for direction in required_openings
    }
    target_count = config["generated_piece_count"] - 1 - len(required_rooms)
    remaining_attempts = 0
    loop_budget = [0]

    def resolve_pairs(placements, frontier, connections, adapters_left=6):
        nonlocal remaining_attempts
        groups = _paired_openings(frontier)
        if not groups:
            yield placements, frontier, connections
            return
        if remaining_attempts <= 0 or adapters_left <= 0:
            return
        remaining_attempts -= 1
        candidates_by_group = [[] for _ in groups]
        for option in _options(placements, frontier, connecting_rooms):
            state = _extend(placements, frontier, connections, option)
            matched_positions = {first for first, _ in state[2][len(connections):]}
            for index, group in enumerate(groups):
                if {opening["position"] for opening in group} <= matched_positions:
                    candidates_by_group[index].append(state)
        candidates = min(candidates_by_group, key=len)
        candidates.sort(key=lambda state: (
            len(_paired_openings(state[1])),
            len(state[1]),
        ))
        for state in candidates:
            if remaining_attempts <= 0:
                break
            yield from resolve_pairs(*state, adapters_left - 1)

    def finish(placements, frontier, connections, required):
        nonlocal remaining_attempts
        minimum_openings = sum(2 - len(_structural_connectors(room)) for room in required)
        if remaining_attempts <= 0 or len(frontier) < minimum_openings:
            return None
        remaining_attempts -= 1

        if not frontier:
            if required:
                return None
            if any(sum(template.get(key) is not None for template, _ in placements) > 1
                   for key in ("trader_altar", "rune_trial")):
                return None
            entry_placement = next(placement for placement in placements if placement[0] is entry)
            ordered_placements = [entry_placement] + [placement for placement in placements if placement is not entry_placement]
            floor = _compose(ordered_placements, connections)
            _seal_boundaries(floor, placements, connections)
            return floor if _valid_floor(floor) else None

        if _paired_openings(frontier):
            for state in resolve_pairs(placements, frontier, connections):
                result = finish(*state, required)
                if result is not None:
                    return result
            return None

        if (
            not allow_dead_ends
            and all(len(_structural_connectors(room)) == 1 for room in required)
            and (len(frontier) - len(required)) % 2
        ):
            return None

        if required:
            branching_indices = [
                index for index, room in enumerate(required)
                if len(_structural_connectors(room)) > 1
            ]
            demands = _required_openings(required)
            if not branching_indices and any(_opening_deficits(frontier, demands).values()):
                return None
            choices = [
                (index, _options(placements, frontier, [required[index]]))
                for index in (branching_indices or range(len(required)))
            ]
            required_index, options = min(choices, key=lambda choice: len(choice[1]))
            next_required = required[:required_index] + required[required_index + 1:]
        else:
            if not allow_dead_ends:
                if len(frontier) % 2:
                    return None
                for state in connect_openings(placements, frontier, connections, corridors, loop_budget):
                    result = finish(*state, required)
                    if result is not None:
                        return result
                return None
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
        if any(
            deficit > count * maximum_openings[direction] + required_growth[direction]
            for direction, deficit in deficits.items()
        ):
            return None
        if count == 0:
            return finish(placements, frontier, connections, required_rooms)
        remaining_attempts -= 1

        usage = Counter(template["source_path"] for template, _ in placements)
        options = _options(placements, frontier, layout_rooms)
        needs_branches = any(deficits.values())

        def priority(option):
            next_frontier = _extend(placements, frontier, [], option)[1]
            independent_openings = Counter(
                (opening.get("room_origin"), opening["direction"])
                for opening in next_frontier
            )
            return (
                sum(_opening_deficits(next_frontier, required_openings).values()),
                usage[option[1]["source_path"]],
                -sum(count == 1 for count in independent_openings.values()) if needs_branches else 0,
            )

        options.sort(key=priority)
        for option in options:
            if remaining_attempts <= 0:
                break
            for state in resolve_pairs(*_extend(placements, frontier, connections, option)):
                result = search(*state, count - 1)
                if result is not None:
                    return result
        return None

    random.shuffle(featured_rooms)
    size_variants = 3 if thorough else 1
    restarts = 4 if thorough else 1
    for featured in featured_rooms:
        for count in range(target_count, max(-1, target_count - size_variants), -1):
            for _ in range(restarts):
                remaining_attempts = 1000 if thorough else 120
                loop_budget[0] = 1500 if thorough else 200
                for state in resolve_pairs([(featured, (0, 0))], _structural_connectors(featured), []):
                    result = search(*state, count)
                    if result is not None:
                        return result
    raise LayoutSearchExhausted("Cannot assemble Act Three with all room connectors joined; check room geometry and corridor connections")
