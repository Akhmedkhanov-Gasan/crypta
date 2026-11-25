from heapq import heappop, heappush
from itertools import count

from acts.act_three.room_connections import extend_layout, placement_options
from acts.act_three.room_generation import _bounds


def _distance(position, targets):
    return min(abs(position[0] - target[0]) + abs(position[1] - target[1]) for target in targets)


def connect_openings(placements, frontier, connections, corridors, node_budget=None, maximum_nodes=1500):
    if len(frontier) < 2:
        return
    start_index = min(
        range(len(frontier)),
        key=lambda index: _distance(
            frontier[index]["position"],
            [opening["position"] for other, opening in enumerate(frontier) if other != index],
        ),
    )
    start = frontier[start_index]
    targets = [opening["position"] for index, opening in enumerate(frontier) if index != start_index]
    boxes = [_bounds(template, offset) for template, offset in placements]
    left = min(box[0] for box in boxes) - 28
    top = min(box[1] for box in boxes) - 28
    right = max(box[2] for box in boxes) + 28
    bottom = max(box[3] for box in boxes) + 28
    sequence = count()
    pending = []
    heappush(pending, (0, next(sequence), placements, frontier, connections, start["position"], start["direction"], 0))
    visited = {(start["position"], start["direction"]): 0}
    solutions = 0

    for _ in range(maximum_nodes):
        if not pending or solutions >= 4:
            return
        if node_budget is not None:
            if node_budget[0] <= 0:
                return
            node_budget[0] -= 1
        _, _, current_placements, current_frontier, current_connections, position, direction, steps = heappop(pending)
        if steps >= 32:
            continue
        opening_index = next(
            index for index, opening in enumerate(current_frontier)
            if opening["position"] == position and opening["direction"] == direction
        )
        options = placement_options(current_placements, current_frontier, corridors, opening_index)
        for option in options:
            box = _bounds(option[1], option[3])
            if box[0] < left or box[1] < top or box[2] > right or box[3] > bottom:
                continue
            state = extend_layout(current_placements, current_frontier, current_connections, option)
            if len(state[1]) == len(frontier) - 2:
                solutions += 1
                yield state
                continue
            outgoing = next(
                opening for opening in state[1]
                if opening.get("room_origin") == option[3]
            )
            key = outgoing["position"], outgoing["direction"]
            next_steps = steps + 1
            if visited.get(key, float("inf")) <= next_steps:
                continue
            visited[key] = next_steps
            priority = next_steps * 5 + _distance(outgoing["position"], targets)
            heappush(pending, (priority, next(sequence), *state, outgoing["position"], outgoing["direction"], next_steps))
