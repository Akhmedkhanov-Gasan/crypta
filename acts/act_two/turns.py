from game.events import GameEventType
from acts.act_two.enemies.oracle.combat import (
    advance_oracle_fire,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    advance_oracle_phase_two_hazards,
)
from game.state import GameState
from acts.act_two.hazards import (
    get_act_two_enemy_hazard_costs,
)
from acts.act_two.combat_pacing import enemy_reaction_delay
from acts.act_two.consumables import advance_fire_zones
from acts.act_two.enemies.brute.aftershocks import (
    advance_brute_aftershocks,
    create_brute_aftershocks_from_events,
)
from acts.act_two.held_movement import apply_turn_movement_interruptions
from acts.act_two.presentation.turn_events import present_act_two_turn_events
from acts.act_two.traps import advance_spike_traps
from acts.act_two.treasury import update_treasury_trial


def resolve_enemy_turn(
    game_state: GameState,
    *args,
    **kwargs,
):
    scene = game_state.floor.oracle_intro

    if scene is not None and not scene.finished:
        return

    from systems.enemy_turn import resolve_enemy_turn as shared_turn

    advance_oracle_fire(game_state)
    advance_oracle_phase_two_hazards(game_state)

    if game_state.player.health <= 0:
        return

    return shared_turn(
        game_state,
        *args,
        hazard_costs=get_act_two_enemy_hazard_costs(game_state),
        goblin_summoning_enabled=True,
        **kwargs,
    )


def act_two_combat_is_active(game_state: GameState) -> bool:
    player_performed_attack = any(
        event.actor == "hero"
        and event.type in (
            GameEventType.ATTACK,
            GameEventType.ABILITY,
        )
        for event in game_state.events
    )

    active_enemy_exists = any(
        enemy.health > 0
        and (
            enemy.is_aggro
            or bool(enemy.attack_targets)
            or enemy.heal_target is not None
        )
        for enemy in game_state.floor.enemies
    )

    return player_performed_attack or active_enemy_exists


def complete_act_two_player_turn(
    game_state: GameState,
    player_position_before_action,
    rogue_ability_activated: bool,
    movement_state,
    sounds,
    current_time: int,
) -> None:
    game_state.player.familiar_turn_started_at = current_time

    advance_spike_traps(game_state)
    advance_brute_aftershocks(game_state)
    update_treasury_trial(game_state)

    if game_state.player.health > 0:
        resolve_enemy_turn(
            game_state,
            player_position_before_action,
            rogue_ability_activated,
        )

    create_brute_aftershocks_from_events(game_state)
    advance_fire_zones(game_state)
    update_treasury_trial(game_state)

    present_act_two_turn_events(
        game_state,
        current_time,
        enemy_reaction_delay(
            game_state,
            act_two_combat_is_active(game_state),
        ),
    )
    sounds.play_events(
        game_state.events,
        game_state.player.player_class,
        game_state.floor,
    )
    apply_turn_movement_interruptions(
        movement_state,
        game_state,
    )


__all__ = [
    "act_two_combat_is_active",
    "complete_act_two_player_turn",
    "resolve_enemy_turn",
]
