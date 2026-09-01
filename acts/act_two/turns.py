from game.events import GameEventType
from acts.act_two.presentation.bosses.oracle_combat import (
    advance_oracle_fire,
)
from acts.act_two.presentation.bosses.oracle_phase_two import (
    advance_oracle_phase_two_hazards,
)
from game.state import GameState
from acts.act_two.hazards import (
    get_act_two_enemy_hazard_costs,
)


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