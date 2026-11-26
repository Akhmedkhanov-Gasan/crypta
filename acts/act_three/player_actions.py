from dataclasses import dataclass

import pygame

from acts.act_three.combat.attacks import attack_breakable_environment_object
from acts.act_three.combat.pacing import player_attack_recovery_active
from acts.act_three.environment_objects import get_breakable_environment_object
from acts.player_abilities import resolve_targeted_player_ability
from acts.act_three.npcs import get_npc_at, open_npc_dialog
from acts.act_three.items.use import use_belt_item
from acts.act_three.items.pickup import resolve_item_pickup
from acts.act_three.trader_catalog import POTION_HEALING
from acts.act_three.mining.runtime import start_mining
from acts.act_three.mining.world import get_ore_at
from acts.act_three.abilities.berserker import (
    perform_berserker_crushing_leap,
    request_berserker_last_rage,
)
from acts.act_three.abilities.warlock import request_warlock_demon_form
from presentation.cursors import (
    set_berserker_crushing_leap_cursor,
    set_warlock_staff_cursor,
)
from acts.act_three.trials.assassin import handle_trial_action
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
    crate = get_breakable_environment_object(floor, target)
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
    if getattr(event, "ability_turn_commit", False):
        return ActThreePlayerActionResult(player_acted=True)

    if getattr(event, "act_three_pickup_item", None) is not None:
        return ActThreePlayerActionResult(
            player_acted=resolve_item_pickup(game_state, event, pygame.time.get_ticks()),
        )

    from acts.act_three.trials.archer import handle_action as handle_piercing_action
    from acts.act_three.trials.summoner import handle_action as handle_summoner_action

    summoner_result = handle_summoner_action(game_state, event, direction)
    if summoner_result is not None:
        return ActThreePlayerActionResult(player_acted=summoner_result, movement_blocked=not summoner_result)
    from acts.act_three.trials.warlock import handle_action as handle_curse_action

    curse_result = handle_curse_action(game_state, event, direction)
    if curse_result is not None:
        return ActThreePlayerActionResult(player_acted=curse_result, movement_blocked=not curse_result)
    from acts.act_three.trials.paladin import handle_action as handle_shield_action

    shield_result = handle_shield_action(game_state, event, direction)
    if shield_result is not None:
        return ActThreePlayerActionResult(player_acted=shield_result, movement_blocked=not shield_result)
    from acts.act_three.trials.berserker import handle_action as handle_crushing_action

    crushing_result = handle_crushing_action(game_state, event, direction)
    if crushing_result is not None:
        return ActThreePlayerActionResult(player_acted=crushing_result, movement_blocked=not crushing_result)

    piercing_result = handle_piercing_action(game_state, event, direction)
    if piercing_result is not None:
        return ActThreePlayerActionResult(
            player_acted=piercing_result,
            movement_blocked=not piercing_result,
        )
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

    belt_slot = getattr(event, "act_three_belt_slot", None)
    if belt_slot is not None:
        acted = use_belt_item(
            game_state, belt_slot, getattr(event, "act_three_belt_target", None),
            pygame.time.get_ticks(),
        )
        if acted:
            game_state.player.act_three.consumable_aim_slot = None
        return ActThreePlayerActionResult(player_acted=acted)

    if event.key == pygame.K_f and game_state.player.subclass == "berserker":
        acted = request_berserker_last_rage(game_state, pygame.time.get_ticks())
        set_berserker_crushing_leap_cursor()
        return ActThreePlayerActionResult(player_acted=acted)

    if event.key == pygame.K_f and game_state.player.subclass == "warlock":
        acted = request_warlock_demon_form(
            game_state,
            pygame.time.get_ticks(),
        )
        set_warlock_staff_cursor()
        return ActThreePlayerActionResult(player_acted=acted)

    if game_state.player.berserker_crushing_leap_aiming:
        if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return ActThreePlayerActionResult()

        acted = perform_berserker_crushing_leap(
            game_state, pygame.time.get_ticks(), hit_reaction,
        )
        if acted:
            set_berserker_crushing_leap_cursor()
        return ActThreePlayerActionResult(player_acted=acted)

    ability_result = resolve_targeted_player_ability(
        game_state,
        event,
        3,
        direction,
        mage_ability_target,
        getattr(event, "resonance_target", None),
        directional_ability_cast,
        rogue_ability_activated,
        hit_reaction,
    )
    if ability_result is not None:
        return ActThreePlayerActionResult(player_acted=ability_result)

    player = game_state.player
    if event.key == pygame.K_h:
        acted = try_use_potion(
            game_state, healing_amount=POTION_HEALING if player.act_three.inventory_unlocked else 4,
        )
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
    from acts.act_three.abilities.summoner_targeting import totem_blocks_cell
    from acts.act_three.abilities.summoner_follow import yield_mobile_summon

    if not yield_mobile_summon(game_state, target, pygame.time.get_ticks()):
        return ActThreePlayerActionResult(movement_blocked=True)
    if totem_blocks_cell(player, target):
        return ActThreePlayerActionResult(movement_blocked=True)
    started_at = pygame.time.get_ticks()
    if not can_reach_adjacent_cell(
        floor.map,
        (floor.player_column, floor.player_row),
        target,
        floor.barriers,
        target_must_be_walkable=False,
    ):
        return ActThreePlayerActionResult(movement_blocked=True)

    from acts.act_three.quests.trader_urn import interact_with_trader_altar

    altar_result = interact_with_trader_altar(game_state, target, started_at)
    if altar_result is not None:
        return ActThreePlayerActionResult(player_acted=altar_result, movement_blocked=not altar_result)

    ore = get_ore_at(floor, target)
    if ore is not None and ore["stage"] < 3:
        started = start_mining(game_state, target, started_at)
        return ActThreePlayerActionResult(
            player_acted=started,
            movement_blocked=not started,
        )

    npc = get_npc_at(floor, target)
    if npc is not None:
        open_npc_dialog(game_state, npc, started_at)
        return ActThreePlayerActionResult(movement_blocked=True)

    enemy, chest, crate, secret_wall = _cell_targets(game_state, target)
    if enemy is not None and enemy.possessed_by_summoner:
        from acts.act_three.abilities.summoner_companion import yield_companion

        if not yield_companion(game_state, enemy, target, started_at):
            return ActThreePlayerActionResult(movement_blocked=True)
        moved = try_move_player(game_state, target[0], target[1], final_floor_index, started_at)
        return ActThreePlayerActionResult(player_acted=moved, movement_blocked=not moved)
    if (
        (enemy is not None or crate is not None or secret_wall)
        and player_attack_recovery_active(player, started_at)
    ):
        return ActThreePlayerActionResult(movement_blocked=True)

    acted = False
    if enemy is not None:
        if player.subclass == "warlock":
            acted = perform_warlock_attack(game_state, target, hit_reaction)
        else:
            perform_basic_attack(
                game_state,
                column_change,
                row_change,
                hit_reaction,
            )
            acted = True
        if acted:
            player.attack_animation_started_at = started_at
    elif chest is not None:
        acted = open_chest(game_state, chest, started_at)
    elif crate is not None:
        acted = attack_breakable_environment_object(game_state, crate, started_at)
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
        if acted:
            from acts.act_three.rune_master.trial import advance_trial

            advance_trial(game_state, started_at)

    return ActThreePlayerActionResult(player_acted=acted)


__all__ = [
    "ActThreePlayerActionResult",
    "resolve_act_three_player_action",
]
