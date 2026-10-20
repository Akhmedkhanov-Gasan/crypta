from acts.act_one.settings import VISION_RADIUS_TILES


def _line_of_sight(dungeon_map, origin, target):
    column, row = origin
    target_column, target_row = target
    delta_column = abs(target_column - column)
    delta_row = abs(target_row - row)
    step_column = 1 if column < target_column else -1
    step_row = 1 if row < target_row else -1
    error = delta_column - delta_row

    while (column, row) != (target_column, target_row):
        if (
            (column, row) != origin
            and dungeon_map[row][column] in ("#", "S")
        ):
            return False

        doubled_error = error * 2
        if doubled_error > -delta_row:
            error -= delta_row
            column += step_column
        if doubled_error < delta_column:
            error += delta_column
            row += step_row

    return True


def update_act_one_visibility(floor):
    origin = (floor.player_column, floor.player_row)
    radius_squared = VISION_RADIUS_TILES * VISION_RADIUS_TILES
    visible_cells = set()

    for row in range(len(floor.map)):
        for column in range(len(floor.map[row])):
            delta_column = column - origin[0]
            delta_row = row - origin[1]

            if (
                delta_column * delta_column
                + delta_row * delta_row
                > radius_squared
            ):
                continue

            if _line_of_sight(
                floor.map,
                origin,
                (column, row),
            ):
                visible_cells.add((column, row))

    floor.visible_cells = visible_cells
    floor.explored_cells.update(visible_cells)
    return visible_cells


def position_is_visible(floor, column, row):
    return (column, row) in floor.visible_cells
