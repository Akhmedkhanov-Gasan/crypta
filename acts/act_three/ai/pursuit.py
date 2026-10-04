from game.state import EnemyBehaviorState
from logic import (
    can_move_between,
    get_enemy_occupied_positions,
    move_enemy_toward_cell,
    positions_are_adjacent,
)
from systems.enemy_ai.common import (
    move_toward_player,
    movement_is_ready,
)


def _move_toward_player_with_footprint(
    dungeon_map,
    enemy,
    player_column,
    player_row,
    occupied_positions,
    barriers=(),
    hazard_costs=None,
    *,
    destination_test=None,
):
    offsets = get_enemy_occupied_positions(
        {
            "column": 0,
            "row": 0,
            "footprint_width": enemy.footprint_width,
            "footprint_height": enemy.footprint_height,
        }
    )
    blocked_positions = set(occupied_positions)
    blocked_positions.add((player_column, player_row))
    barrier_edges = set(barriers)

    def occupied_cells(position):
        column, row = position
        return {
            (column + offset_x, row + offset_y)
            for offset_x, offset_y in offsets
        }

    def reached_player(position):
        if destination_test is not None:
            return destination_test(position)

        return any(
            positions_are_adjacent(
                column,
                row,
                player_column,
                player_row,
            )
            for column, row in occupied_cells(position)
        )

    def valid_step(origin, destination):
        destination_cells = occupied_cells(destination)

        if destination_cells & blocked_positions:
            return False

        if enemy.movement_bounds is not None:
            left, top, right, bottom = enemy.movement_bounds

            if any(
                not (
                    left <= column <= right
                    and top <= row <= bottom
                )
                for column, row in destination_cells
            ):
                return False

        for column, row in destination_cells:
            for neighbor in (
                (column + 1, row),
                (column, row + 1),
            ):
                if (
                    neighbor in destination_cells
                    and tuple(sorted(((column, row), neighbor)))
                    in barrier_edges
                ):
                    return False

        return all(
            can_move_between(
                dungeon_map,
                origin[0] + offset_x,
                origin[1] + offset_y,
                destination[0] + offset_x,
                destination[1] + offset_y,
                barrier_edges,
            )
            for offset_x, offset_y in offsets
        )

    return move_enemy_toward_cell(
        dungeon_map,
        enemy,
        player_column,
        player_row,
        occupied_positions,
        barriers,
        hazard_costs,
        step_validator=valid_step,
        destination_test=reached_player,
    )


def take_pursuit_turn(
    game_state,
    enemy,
    occupied_positions,
    attack_blocking_positions,
    hazard_costs,
):
    if not enemy.is_aggro:
        enemy.behavior_state = EnemyBehaviorState.IDLE
        return

    enemy.behavior_state = EnemyBehaviorState.CHASING

    if enemy.is_immobile or not movement_is_ready(enemy):
        return

    move_toward_player(
        game_state,
        enemy,
        occupied_positions,
        hazard_costs,
        movement_resolver=_move_toward_player_with_footprint,
    )
    