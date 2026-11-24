import random

from acts.act_three.room_generation import (
    DIRECTION_STEP,
    OPPOSITE_DIRECTION,
    _bounds,
    _bounds_overlap,
    _placement_offset,
    _structural_connectors,
    _translated,
)


def _frontier_is_clear(placements, frontier):
    bounds = [_bounds(template, offset) for template, offset in placements]
    for opening in frontier:
        dx, dy = DIRECTION_STEP[opening["direction"]]
        x = opening["position"][0] + dx
        y = opening["position"][1] + dy
        if any(left <= x < right and top <= y < bottom for left, top, right, bottom in bounds):
            return False
    return True


def extend_layout(placements, frontier, connections, option):
    index, template, connector, offset = option
    opening = frontier[index]
    remaining = frontier[:index] + frontier[index + 1:]
    added_connections = [(opening["position"], _translated(connector["position"], offset))]
    new_openings = []
    for item in _structural_connectors(template):
        if item is connector:
            continue
        position = _translated(item["position"], offset)
        dx, dy = DIRECTION_STEP[item["direction"]]
        neighbor = position[0] + dx, position[1] + dy
        matching_index = next(
            (
                other_index
                for other_index, other in enumerate(remaining)
                if other["position"] == neighbor
                and other["direction"] == OPPOSITE_DIRECTION[item["direction"]]
                and other["width"] == item["width"]
            ),
            None,
        )
        if matching_index is None:
            new_openings.append({**item, "position": position, "room_origin": offset})
        else:
            other = remaining.pop(matching_index)
            added_connections.append((other["position"], position))
    return (
        placements + [(template, offset)],
        remaining + new_openings,
        connections + added_connections,
    )


def placement_options(placements, frontier, templates):
    options = []
    seen_placements = set()
    for frontier_index, opening in enumerate(frontier):
        for template in templates:
            for connector in _structural_connectors(template):
                if connector["direction"] != OPPOSITE_DIRECTION[opening["direction"]]:
                    continue
                if connector["width"] != opening["width"] or connector["width"] != 1:
                    continue
                offset = _placement_offset(opening, connector)
                placement_key = template["source_path"], offset
                if placement_key in seen_placements:
                    continue
                candidate_bounds = _bounds(template, offset)
                if any(
                    _bounds_overlap(candidate_bounds, _bounds(placed, position))
                    for placed, position in placements
                ):
                    continue
                option = frontier_index, template, connector, offset
                next_placements, next_frontier, _ = extend_layout(placements, frontier, [], option)
                if not _frontier_is_clear(next_placements, next_frontier):
                    continue
                seen_placements.add(placement_key)
                options.append(option)
    random.shuffle(options)
    return options
