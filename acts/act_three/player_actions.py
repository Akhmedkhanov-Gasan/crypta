from dataclasses import dataclass

import pygame

from acts.crates import break_crate
from acts.player_abilities import resolve_targeted_player_ability
from acts.act_three.npcs import get_npc_at, open_npc_dialog
from acts.act_three.shadow_step_trial import handle_trial_action
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
class ActThreePlayerActionResult:
    player_acted: bool = False
    movement_blocked: bool = False


def _cell_targets(game_state, target):
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


def resolve_act_three_player_action(
    game_state,
    event,
    direction,
    mage_ability_target,
    directional_ability_cast,
    rogue_ability_activated,
    final_floor_index,
    hit_reaction,
) -> ActThreePlayerActionResult:
    trial_result = handle_trial_action(
        game_state,
        event,
        direction,
    )

    if trial_result is not None:
        return ActThreePlayerActionResult(
            player_acted=trial_result,
            movement_blocked=not trial_result,
        )

    ability_result = resolve_targeted_player_ability(
        game_state,
        event,
        3,
        direction,
        mage_ability_target,
        None,
        directional_ability_cast,
        rogue_ability_activated,
        hit_reaction,
    )
    if ability_result is not None:
        return ActThreePlayerActionResult(player_acted=ability_result)

    player = game_state.player
    if event.key == pygame.K_h:
        acted = try_use_potion(game_state)
        if acted:
            player.potion_effect_started_at = pygame.time.get_ticks()
        return ActThreePlayerActionResult(player_acted=acted)

    if event.key in WAIT_KEYS:
        return ActThreePlayerActionResult(player_acted=True)

    column_change, row_change = direction
    if column_change == 0 and row_change == 0:
        return ActThreePlayerActionResult()

    floor = game_state.floor
    target = (
        floor.player_column + column_change,
        floor.player_row + row_change,
    )
    started_at = pygame.time.get_ticks()
    if not can_reach_adjacent_cell(
        floor.map,
        (floor.player_column, floor.player_row),
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return ActThreePlayerActionResult(movement_blocked=True)

    npc = get_npc_at(floor, target)
    if npc is not None:
        open_npc_dialog(game_state, npc, started_at)
        return ActThreePlayerActionResult(movement_blocked=True)

    enemy, chest, crate, secret_wall = _cell_targets(game_state, target)
    acted = False
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
        player.attack_animation_started_at = started_at
        acted = True
    elif chest is not None:
        acted = open_chest(game_state, chest, started_at)
    elif crate is not None:
        acted = break_crate(game_state, crate)
        if acted:
            player.attack_animation_started_at = started_at
    elif secret_wall:
        acted = break_secret_passage(game_state, target[0], target[1])
        if acted:
            player.attack_animation_started_at = started_at
    else:
        acted = try_move_player(
            game_state,
            target[0],
            target[1],
            final_floor_index,
            started_at,
        )

    return ActThreePlayerActionResult(player_acted=acted)


__all__ = [
    "ActThreePlayerActionResult",
    "resolve_act_three_player_action",
]
