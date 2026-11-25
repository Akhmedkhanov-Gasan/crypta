from logic import can_move_to, get_enemy_occupied_positions, has_line_of_sight
from acts.act_three.enemies.balance import (
    LANTERN_WARDEN_PROCESSION_ARM_LENGTH,
    LANTERN_WARDEN_PROCESSION_RANGE,
)


def procession_targets(floor, enemy, blocking_positions):
    player = (floor.player_column, floor.player_row)
    footprint = get_enemy_occupied_positions(enemy)
    if player in blocking_positions or min(abs(x - player[0]) + abs(y - player[1]) for x, y in footprint) > LANTERN_WARDEN_PROCESSION_RANGE:
        return []
    if not any(has_line_of_sight(floor.map, x, y, *player, floor.barriers) for x, y in footprint):
        return []
    targets = [player]
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        previous = player
        for step in range(1, LANTERN_WARDEN_PROCESSION_ARM_LENGTH + 1):
            cell = (player[0] + dx * step, player[1] + dy * step)
            if cell in footprint or cell in blocking_positions or not can_move_to(floor.map, *cell):
                break
            if not has_line_of_sight(floor.map, *previous, *cell, floor.barriers):
                break
            targets.append(cell)
            previous = cell
    return targets
