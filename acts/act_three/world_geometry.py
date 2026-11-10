from collections import deque

from systems.grid_geometry import can_reach_adjacent_cell


def reachable_cells(dungeon_map, origin, barriers=()):
    if origin is None:
        return set()
    column, row = origin
    if not (0 <= row < len(dungeon_map) and 0 <= column < len(dungeon_map[row]) and dungeon_map[row][column] == "."):
        return set()
    visited = {origin}
    pending = deque([origin])
    while pending:
        current = pending.popleft()
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            target = current[0] + dx, current[1] + dy
            if target in visited:
                continue
            if can_reach_adjacent_cell(dungeon_map, current, target, barriers):
                visited.add(target)
                pending.append(target)
    return visited
