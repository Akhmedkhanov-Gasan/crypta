from acts.act_three.altar import (
    get_upgrade_altar_cells,
    open_upgrade_altar,
)
from acts.act_three.combat.attacks import navigation_attack
from acts.act_two.input.auto_movement import (
    player_attack_warnings as act_two_attack_warnings,
)
from acts.act_two.player_actions import find_act_two_cell_targets
from logic import (
    distance_between,
    get_enemy_occupied_positions,
    has_line_of_sight,
)
from settings import MAGE_RESONANCE_RANGE
from systems.grid_geometry import can_reach_adjacent_cell


def navigation_cell_is_visible(game_state, position):
    if position is None:
        return False

    floor = game_state.floor
    column, row = position
    if not (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[row])
    ):
        return False

    return (
        floor.presentation_act == 1
        or position in floor.visible_cells
    )


def player_attack_warnings(game_state):
    floor = game_state.floor
    if floor.presentation_act == 2:
        return act_two_attack_warnings(game_state)

    position = (floor.player_column, floor.player_row)
    return tuple(
        enemy.attack_targets
        for enemy in floor.enemies
        if enemy.health > 0
        and position in enemy.attack_targets
    )


def navigation_target_info(game_state, target):
    floor = game_state.floor

    if floor.presentation_act == 2:
        targets = find_act_two_cell_targets(
            game_state,
            target,
            True,
            require_adjacent=False,
        )
        return targets.enemy, any(
            (
                targets.enemy is not None,
                targets.chest is not None,
                targets.breakable_crate is not None,
                targets.treasury_chest,
                targets.rune_wall,
                targets.rune_pedestal,
                targets.trader,
                targets.bloody_altar,
                targets.secret_wall,
            )
        )

    enemy = next(
        (
            candidate
            for candidate in floor.enemies
            if candidate.health > 0
            and target in get_enemy_occupied_positions(candidate)
        ),
        None,
    )
    chest = any(
        not candidate.is_open
        and (candidate.column, candidate.row) == target
        for candidate in floor.chests
    )
    crate = any(
        not candidate.is_broken
        and (candidate.column, candidate.row) == target
        for candidate in floor.breakable_crates
    )
    column, row = target
    secret_wall = floor.map[row][column] == "S"
    altar = (
        floor.presentation_act == 3
        and target in get_upgrade_altar_cells(floor)
    )
    return enemy, (
        enemy is not None or chest or crate or secret_wall or altar
    )


def navigation_action(game_state, origin, target, has_enemy):
    floor = game_state.floor
    player = game_state.player

    if (
        has_enemy
        and player.player_class == "mage"
        and player.selected_rune_id == "rune_of_resonance"
    ):
        if (
            0 < distance_between(*origin, *target)
            <= MAGE_RESONANCE_RANGE
            and (
                origin[0] == target[0]
                or origin[1] == target[1]
            )
            and has_line_of_sight(
                floor.map,
                *origin,
                *target,
                barriers=floor.barriers,
            )
        ):
            return {"resonance_target": target}
        return None

    if floor.presentation_act == 3:
        if target in get_upgrade_altar_cells(floor):
            if any(
                abs(origin[0] - cell[0])
                + abs(origin[1] - cell[1]) == 1
                and can_reach_adjacent_cell(
                    floor.map,
                    origin,
                    cell,
                    floor.barriers,
                    target_must_be_walkable=False,
                )
                for cell in get_upgrade_altar_cells(floor)
            ):
                return {"navigation_altar": True}
            return None

        if has_enemy:
            attack = navigation_attack(
                game_state,
                target,
                origin=origin,
            )
            if attack is not None:
                return (
                    {"navigation_attack_target": target}
                    if attack[1]
                    else None
                )

    if can_reach_adjacent_cell(
        floor.map,
        origin,
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return {
            "movement_direction": (
                target[0] - origin[0],
                target[1] - origin[1],
            )
        }

    return None


def activate_navigation_action(game_state, event):
    if getattr(event, "navigation_altar", False):
        return (
            game_state.floor.presentation_act == 3
            and open_upgrade_altar(game_state)
        )

    target = getattr(event, "navigation_attack_target", None)
    if target is not None:
        if game_state.floor.presentation_act != 3:
            return False

        attack = navigation_attack(game_state, target)
        if attack is None or not attack[1]:
            return False

        setattr(game_state.player, attack[0], target)

    return True
