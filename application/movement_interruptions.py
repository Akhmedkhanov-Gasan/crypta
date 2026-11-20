from application.auto_movement import auto_move_has_new_warning
from acts.act_three.combat.pacing import player_attack_recovery_until
from game.events import GameEventType


PLAYER_ATTACK_PAUSE_MS = 180
ATTACK_FEEDBACK_PAUSE_MS = 160
INCOMING_ATTACK_PAUSE_MS = 320
PLAYER_HIT_PAUSE_MS = 100
TELEGRAPH_READ_PAUSE_MS = 180


def apply_movement_interruptions(state, game_state, current_time):
    events = game_state.events
    floor = game_state.floor
    player = game_state.player
    position = (floor.player_column, floor.player_row)

    player_attacked = any(
        event.type is GameEventType.ATTACK
        and event.actor == "hero"
        for event in events
    )
    attack_feedback = any(
        event.actor == "hero"
        and event.target not in (None, "hero", "familiar")
        and event.type in (
            GameEventType.HIT,
            GameEventType.DODGE,
        )
        for event in events
    )
    incoming_attack = any(
        event.type is GameEventType.ATTACK
        and event.actor not in ("hero", "phantom")
        and position in event.positions
        for event in events
    )
    player_hit_or_dodged = any(
        event.target == "hero"
        and event.type in (
            GameEventType.HIT,
            GameEventType.DODGE,
        )
        for event in events
    )
    enemy_prepared_action = any(
        event.type in (
            GameEventType.PREPARE_ATTACK,
            GameEventType.PREPARE_SUMMON,
        )
        for event in events
    )
    player_is_targeted = any(
        enemy.health > 0
        and position in enemy.attack_targets
        for enemy in floor.enemies
    )
    safe_kill = (
        floor.presentation_act == 3
        and player.health > 0
        and player_attacked
        and any(
            event.type is GameEventType.DEATH
            and event.actor not in ("hero", "familiar")
            for event in events
        )
        and not incoming_attack
        and not player_hit_or_dodged
        and not enemy_prepared_action
        and not player_is_targeted
        and not any(
            enemy.health > 0 and enemy.is_aggro
            for enemy in floor.enemies
        )
    )

    if player_attacked:
        state.resume_held_movement_after_attack = safe_kill

    pause_until = state.movement_input_locked_until

    if player_attacked:
        pause_until = max(
            pause_until,
            player.attack_animation_started_at
            + PLAYER_ATTACK_PAUSE_MS,
        )
        if floor.presentation_act == 3 and not safe_kill:
            pause_until = max(pause_until, player_attack_recovery_until(player))

    if attack_feedback:
        feedback_names = {
            event.target
            for event in events
            if event.actor == "hero"
            and event.type in (
                GameEventType.HIT,
                GameEventType.DODGE,
            )
        }
        for enemy in floor.enemies:
            if (
                enemy.name in feedback_names
                and enemy.hit_animation_started_at >= 0
            ):
                pause_until = max(
                    pause_until,
                    enemy.hit_animation_started_at
                    + ATTACK_FEEDBACK_PAUSE_MS,
                )

    if incoming_attack:
        pause_until = max(
            pause_until,
            current_time + INCOMING_ATTACK_PAUSE_MS,
        )

    if player_hit_or_dodged:
        pause_until = max(
            pause_until,
            current_time + PLAYER_HIT_PAUSE_MS,
        )

    if player_is_targeted and enemy_prepared_action:
        pause_until = max(
            pause_until,
            current_time + TELEGRAPH_READ_PAUSE_MS,
        )

    state.movement_input_locked_until = pause_until

    if (
        (player_attacked and not safe_kill)
        or enemy_prepared_action
        or incoming_attack
        or player_hit_or_dodged
    ):
        state.reset_held_movement()

    if (
        auto_move_has_new_warning(state, game_state)
        or incoming_attack
        or player_hit_or_dodged
    ):
        state.cancel_auto_move()
