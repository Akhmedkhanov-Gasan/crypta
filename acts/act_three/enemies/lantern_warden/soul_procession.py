from logic import can_move_to, get_enemy_occupied_positions, has_line_of_sight


def procession_targets(floor, enemy, blocking_positions):
    player = (floor.player_column, floor.player_row)
    footprint = get_enemy_occupied_positions(enemy)
    if player in blocking_positions or min(abs(x - player[0]) + abs(y - player[1]) for x, y in footprint) > 6:
        return []
    if not any(has_line_of_sight(floor.map, x, y, *player, floor.barriers) for x, y in footprint):
        return []
    targets = [player]
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        previous = player
        for step in range(1, 4):
            cell = (player[0] + dx * step, player[1] + dy * step)
            if cell in footprint or cell in blocking_positions or not can_move_to(floor.map, *cell):
                break
            if not has_line_of_sight(floor.map, *previous, *cell, floor.barriers):
                break
            targets.append(cell)
            previous = cell
    return targets
