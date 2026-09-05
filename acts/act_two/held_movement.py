from logic import distance_between

from application.movement_interruptions import (
    ATTACK_FEEDBACK_PAUSE_MS,
    PLAYER_ATTACK_PAUSE_MS,
)
from acts.act_two.combat_pacing import (
    ENEMY_ATTACK_DURATION_MS,
    ENEMY_ATTACK_RECOVERY_MS,
    PLAYER_HIT_BREATH_MS,
)
from acts.act_two.input_state import ActTwoInputRuntimeState
from application.auto_movement import auto_move_has_new_warning
from acts.act_two.state import BruteAftershockPhase
from game.events import GameEventType


TELEGRAPH_READ_TIME_MS = 180
DISTANT_RANGED_ATTACK_DISTANCE = 5


def apply_turn_movement_interruptions(
    state: ActTwoInputRuntimeState,
    game_state,
) -> None:
    player_position = (
        game_state.floor.player_column,
        game_state.floor.player_row,
    )
    player_performed_basic_attack = any(
        (
            event.type is GameEventType.ATTACK
            and event.actor == "hero"
            and event.data.get("kind") == "basic"
        )
        for event in game_state.events
    )

    player_was_hit = any(
        (
            event.type is GameEventType.HIT
            and event.target == "hero"
            and event.amount
        )
        for event in game_state.events
    )
    attack_feedback_target_names = {
        event.target
        for event in game_state.events
        if (
            event.actor == "hero"
            and event.target not in (None, "hero", "familiar")
            and event.type in (
                GameEventType.HIT,
                GameEventType.DODGE,
            )
        )
    }

    repeated_movement_interrupted = (
        player_performed_basic_attack
        or any(
            (
                event.type in (
                    GameEventType.PREPARE_ATTACK,
                    GameEventType.PREPARE_SUMMON,
                )
                or (
                    event.type is GameEventType.ATTACK
                    and event.actor != "hero"
                    and player_position in event.positions
                )
                or (
                    event.type in (
                        GameEventType.HIT,
                        GameEventType.DODGE,
                    )
                    and event.target == "hero"
                )
            )
            for event in game_state.events
        )
    )

    warning_aftershock_exists = any(
        (
            aftershock.phase is BruteAftershockPhase.WARNING
            and aftershock.warning_visible_at >= 0
        )
        for aftershock in game_state.floor.brute_aftershocks
    )

    if warning_aftershock_exists:
        repeated_movement_interrupted = True

    distant_ranged_attack_names = {
        event.actor
        for event in game_state.events
        if (
            event.type is GameEventType.PREPARE_ATTACK
            and event.data.get("mode") == "ranged"
            and event.origin is not None
            and player_position in event.positions
            and distance_between(
                event.origin[0],
                event.origin[1],
                player_position[0],
                player_position[1],
            )
            > DISTANT_RANGED_ATTACK_DISTANCE
        )
    }

    distant_ranged_enemies = [
        enemy
        for enemy in game_state.floor.enemies
        if enemy.name in distant_ranged_attack_names
    ]

    if distant_ranged_enemies:
        state.movement_input_locked_until = max(
            state.movement_input_locked_until,
            max(
                enemy.attack_telegraph_visible_at + TELEGRAPH_READ_TIME_MS
                for enemy in distant_ranged_enemies
            ),
        )

    if player_performed_basic_attack:
        state.movement_input_locked_until = max(
            state.movement_input_locked_until,
            game_state.player.attack_animation_started_at
            + PLAYER_ATTACK_PAUSE_MS,
        )

    attack_feedback_targets = [
        enemy
        for enemy in game_state.floor.enemies
        if enemy.name in attack_feedback_target_names
        and enemy.hit_animation_started_at >= 0
    ]
    if attack_feedback_targets:
        state.movement_input_locked_until = max(
            state.movement_input_locked_until,
            max(
                enemy.hit_animation_started_at
                + ATTACK_FEEDBACK_PAUSE_MS
                for enemy in attack_feedback_targets
            ),
        )

    incoming_attack_names = {
        event.actor
        for event in game_state.events
        if (
            event.type is GameEventType.ATTACK
            and event.actor != "hero"
            and player_position in event.positions
        )
    }

    incoming_attackers = [
        enemy
        for enemy in game_state.floor.enemies
        if enemy.name in incoming_attack_names
    ]

    if incoming_attackers:
        state.movement_input_locked_until = max(
            state.movement_input_locked_until,
            max(
                enemy.attack_animation_started_at
                for enemy in incoming_attackers
            )
            + ENEMY_ATTACK_DURATION_MS
            + ENEMY_ATTACK_RECOVERY_MS,
        )

    if (
        player_was_hit
        and game_state.player.hit_animation_started_at >= 0
    ):
        state.movement_input_locked_until = max(
            state.movement_input_locked_until,
            game_state.player.hit_animation_started_at
            + PLAYER_HIT_BREATH_MS,
        )

    if repeated_movement_interrupted:
        state.reset_held_movement()

    incoming_attack_event = any(
        (
            event.type is GameEventType.ATTACK
            and event.actor != "hero"
            and player_position in event.positions
        )
        or (
            event.type in (
                GameEventType.HIT,
                GameEventType.DODGE,
            )
            and event.target == "hero"
        )
        for event in game_state.events
    )

    if (
        auto_move_has_new_warning(state, game_state)
        or incoming_attack_event
    ):
        state.cancel_auto_move()

