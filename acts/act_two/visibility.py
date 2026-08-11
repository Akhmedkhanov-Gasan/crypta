from acts.act_two.settings import VISION_RADIUS_TILES


def _line_of_sight(
    dungeon_map,
    origin,
    target,
    blockers=(),
):
    """Return whether a grid ray reaches a cell before hitting a wall."""
    x0, y0 = origin
    x1, y1 = target
    delta_x = abs(x1 - x0)
    delta_y = abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    error = delta_x - delta_y

    while (x0, y0) != (x1, y1):
        if (
            (x0, y0) != origin
            and (
                dungeon_map[y0][x0] in ("#", "S")
                or (x0, y0) in blockers
            )
        ):
            return False

        doubled_error = error * 2
        if doubled_error > -delta_y:
            error -= delta_y
            x0 += step_x
        if doubled_error < delta_x:
            error += delta_x
            y0 += step_y

    return True


def update_act_two_visibility(floor):
    """Update current sight and remember terrain visited on this floor."""
    origin = (floor.player_column, floor.player_row)
    radius_squared = VISION_RADIUS_TILES * VISION_RADIUS_TILES
    visible_cells = set()
    blockers = set()

    if floor.boss_door is not None and not floor.boss_fight_started:
        blockers.add(floor.boss_door)

    for row in range(len(floor.map)):
        for column in range(len(floor.map[0])):
            delta_x = column - origin[0]
            delta_y = row - origin[1]
            if delta_x * delta_x + delta_y * delta_y > radius_squared:
                continue
            if _line_of_sight(
                floor.map,
                origin,
                (column, row),
                blockers,
            ):
                visible_cells.add((column, row))

    floor.visible_cells = visible_cells
    floor.explored_cells.update(visible_cells)
    _update_remembered_objects(floor)
    return visible_cells


def position_is_visible(floor, column, row):
    return (column, row) in floor.visible_cells


def _update_remembered_objects(floor):
    stairs_position = (floor.stairs_column, floor.stairs_row)
    if stairs_position in floor.visible_cells:
        floor.act_two_remembered_stairs_open = not any(
            enemy.health > 0
            for enemy in floor.enemies
        )

    for chest in floor.chests:
        position = (chest.column, chest.row)
        if position not in floor.visible_cells:
            continue
        floor.act_two_remembered_chests[position] = {
            "column": chest.column,
            "row": chest.row,
            "contains": chest.contains,
            "is_open": chest.is_open,
            "loot_available": chest.loot_available,
            "open_animation_started_at": -1,
            "requires_key": chest.requires_key,
            "appearance": chest.appearance,
        }
