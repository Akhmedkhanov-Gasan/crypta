from dataclasses import dataclass

from game.combat_log import add_log_message

from acts.act_one.controls import POTION_KEYS
from acts.act_one.crates import break_act_one_crate
from application.directional_input import WAIT_KEYS
from logic import get_enemy_occupied_positions
from systems.grid_geometry import can_reach_adjacent_cell
from systems.player_actions import (
    break_secret_passage,
    open_chest,
    try_move_player,
    try_use_potion,
)
from systems.player_combat import (
    perform_basic_attack,
    perform_warlock_attack,
)


@dataclass(frozen=True)
class ActOnePlayerActionResult:
    player_acted: bool = False
    movement_blocked: bool = False


def _target_at(game_state, target):
    floor = game_state.floor
    enemy = next(
        (
            candidate
            for candidate in floor.enemies
            if candidate.health > 0
            and target in get_enemy_occupied_positions(candidate)
        ),
        None,
    )
    chest = next(
        (
            candidate
            for candidate in floor.chests
            if not candidate.is_open
            and (candidate.column, candidate.row) == target
        ),
        None,
    )
    crate = next(
        (
            candidate
            for candidate in floor.breakable_crates
            if not candidate.is_broken
            and (candidate.column, candidate.row) == target
        ),
        None,
    )
    column, row = target
    secret_wall = (
        0 <= row < len(floor.map)
        and 0 <= column < len(floor.map[row])
        and floor.map[row][column] == "S"
    )
    return enemy, chest, crate, secret_wall


def resolve_act_one_player_action(
    game_state,
    key,
    direction,
    current_time,
    final_floor_index,
    hit_reaction,
) -> ActOnePlayerActionResult:
    player = game_state.player
    potion_slot = POTION_KEYS.get(key)
    player_waited = key in WAIT_KEYS

    if not player_waited:
        player.act_one_wait_effect_started_at = -1

    if potion_slot is not None and potion_slot < player.potion_count:
        player_acted = try_use_potion(game_state)
        if player_acted:
            player.potion_effect_started_at = current_time
        return ActOnePlayerActionResult(player_acted=player_acted)

    if player_waited:
        player.act_one_wait_effect_started_at = current_time
        add_log_message(game_state.combat_log, "The player waits.")
        return ActOnePlayerActionResult(player_acted=True)

    column_change, row_change = direction
    if column_change == 0 and row_change == 0:
        return ActOnePlayerActionResult()

    floor = game_state.floor
    target = (
        floor.player_column + column_change,
        floor.player_row + row_change,
    )
    if not can_reach_adjacent_cell(
        floor.map,
        (floor.player_column, floor.player_row),
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return ActOnePlayerActionResult(movement_blocked=True)

    enemy, chest, crate, secret_wall = _target_at(game_state, target)
    player_acted = False

    if enemy is not None:
        if player.subclass == "warlock":
            perform_warlock_attack(game_state, target, hit_reaction)
        else:
            perform_basic_attack(
                game_state,
                column_change,
                row_change,
                hit_reaction,
            )
        player.attack_animation_started_at = current_time
        player_acted = True
    elif chest is not None:
        player_acted = open_chest(game_state, chest, current_time)
    elif crate is not None:
        player_acted = break_act_one_crate(game_state, crate)
        if player_acted:
            player.attack_animation_started_at = current_time
    elif secret_wall:
        player_acted = break_secret_passage(
            game_state,
            target[0],
            target[1],
        )
        if player_acted:
            player.attack_animation_started_at = current_time
    else:
        player_acted = try_move_player(
            game_state,
            target[0],
            target[1],
            final_floor_index,
            current_time,
        )

    return ActOnePlayerActionResult(player_acted=player_acted)


__all__ = [
    "ActOnePlayerActionResult",
    "resolve_act_one_player_action",
]
