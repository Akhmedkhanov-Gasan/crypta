from acts.act_three.bloody_altar.runtime import altar_position
from acts.act_three.abilities.summoner_targeting import totem_blocks_cell
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell


def teleport_destination(floor, player):
    position = altar_position(floor)
    if position is None:
        return None
    blocked = {cell for enemy in floor.enemies if enemy.health > 0
               for cell in get_enemy_occupied_positions(enemy)}
    blocked.update((chest.column, chest.row) for chest in floor.chests if not chest.is_open)
    blocked.update((crate.column, crate.row) for crate in floor.breakable_crates if not crate.is_broken)
    blocked.update(floor.act_three_spring_traps)
    for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
        cell = position[0] + dx, position[1] + dy
        if (not 0 <= cell[1] < len(floor.map) or not 0 <= cell[0] < len(floor.map[cell[1]])
                or floor.map[cell[1]][cell[0]] != "." or totem_blocks_cell(player, cell)):
            continue
        if cell not in blocked and can_reach_adjacent_cell(
            floor.map, cell, position, floor.barriers, target_must_be_walkable=False,
        ):
            return cell
    return None
