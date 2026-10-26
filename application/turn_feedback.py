import pygame

from game.events import GameEventType

from acts.act_three.presentation.assassin import record_shadow_reflex_feedback
from acts.act_three.presentation.combat_effects import (
    record_enemy_death_feedback,
    record_enemy_hit_feedback,
    record_familiar_hit_feedback,
    record_player_death_feedback,
    record_player_hit_feedback,
)
from acts.act_two.controls import visual_direction as act_two_visual_direction
from application.movement_input import mark_movement_step
from application.movement_interruptions import apply_movement_interruptions
from systems.player_combat import remove_enemy_corpses_at_position


def _latest_event(events, event_type, actor=None, target=None):
    return next(
        (
            event
            for event in reversed(events)
            if event.type is event_type
            and (actor is None or event.actor == actor)
            and (target is None or event.target == target)
        ),
        None,
    )


def _record_player_feedback(
    game_state,
    current_act,
    started_at,
    movement_state,
    movement_profile,
):
    events = game_state.events
    player = game_state.player
    hero_attack_event = next(
        (
            event
            for event in reversed(events)
            if event.type is GameEventType.ATTACK
            and event.actor == "hero"
            and event.positions
        ),
        None,
    )
    if hero_attack_event is not None:
        player.act_one_attack_target = hero_attack_event.positions[0]
        player.act_one_attack_was_critical = any(
            event.type is GameEventType.HIT
            and event.actor == "hero"
            and event.data.get("critical", False)
            for event in events
        )

    dodge_event = _latest_event(
        events,
        GameEventType.DODGE,
        target="hero",
    )
    if current_act == 1 and dodge_event is not None:
        player.act_one_dodge_started_at = started_at
        player.act_one_dodge_origin = dodge_event.origin

    move_event = next(
        (
            event
            for event in reversed(events)
            if event.type is GameEventType.MOVE
            and event.actor == "hero"
            and event.origin is not None
        ),
        None,
    )
    if move_event is None:
        return

    if current_act == 1:
        player.act_one_movement_origin = move_event.origin
        player.movement_animation_started_at = started_at
    elif current_act == 2:
        player.act_two_movement_started_at = started_at
        player.act_two_movement_origin = move_event.origin
        if move_event.destination is not None:
            player.act_two_facing_direction = act_two_visual_direction(
                (
                    move_event.destination[0] - move_event.origin[0],
                    move_event.destination[1] - move_event.origin[1],
                )
            )
    else:
        player.movement_origin = move_event.origin
        player.movement_animation_started_at = started_at
        mark_movement_step(
            movement_state,
            started_at,
            profile=movement_profile,
        )


def _record_enemy_feedback(game_state, started_at):
    events = game_state.events
    moved_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.MOVE
    }
    attacked_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.ATTACK
    }
    healed_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.HEAL
    }

    for enemy in game_state.floor.enemies:
        if enemy.name in moved_enemy_names:
            enemy.movement_animation_started_at = started_at
            movement_event = next(
                (
                    event
                    for event in reversed(events)
                    if event.type is GameEventType.MOVE
                    and event.actor == enemy.name
                    and event.origin is not None
                ),
                None,
            )
            if movement_event is not None:
                enemy.movement_origin = movement_event.origin
                enemy.movement_animation_kind = movement_event.data.get("kind")
                if enemy.movement_animation_kind == "arcane_burst_knockback":
                    enemy.movement_animation_started_at += 220

        if enemy.name in attacked_enemy_names or enemy.name in healed_enemy_names:
            enemy.attack_animation_started_at = started_at

        if enemy.name in attacked_enemy_names:
            attack_event = _latest_event(
                events,
                GameEventType.ATTACK,
                actor=enemy.name,
            )
            if attack_event is not None:
                enemy.attack_effect_mode = attack_event.data.get("mode")
                enemy.attack_effect_positions = attack_event.positions
        elif enemy.name in healed_enemy_names:
            enemy.attack_effect_mode = "heal"
            enemy.attack_effect_positions = ()

        if (
            enemy.type == "warden"
            and enemy.second_phase_announced
            and enemy.phase_transition_started_at < 0
        ):
            enemy.phase_transition_started_at = started_at


def _play_turn_sounds(
    game_state,
    current_act,
    movement_state,
    act_one_sounds,
    act_two_sounds,
    act_three_sounds,
):
    if current_act == 1:
        act_one_sounds.play_events(game_state.events)
    elif current_act == 2:
        if any(
            event.target == "hero"
            and event.type in (GameEventType.HIT, GameEventType.DODGE)
            for event in game_state.events
        ):
            movement_state.cancel_auto_move()
        act_two_sounds.play_events(
            game_state.events,
            game_state.player.player_class,
            game_state.floor,
        )
    elif current_act == 3:
        act_three_sounds.play_events(
            game_state.events,
            game_state.player,
        )


def present_turn_feedback(
    game_state,
    current_act,
    started_at,
    movement_state,
    movement_profile,
    act_one_sounds,
    act_two_sounds,
    act_three_sounds,
):
    record_enemy_hit_feedback(game_state, started_at)
    record_enemy_death_feedback(game_state, started_at)
    record_player_hit_feedback(game_state, started_at)
    record_player_death_feedback(game_state, started_at)
    record_shadow_reflex_feedback(game_state, started_at)

    if any(
        event.type is GameEventType.LEVEL_UP and event.actor == "hero"
        for event in game_state.events
    ) and current_act == 2:
        game_state.player.act_two.level_up_effect_started_at = started_at

    if current_act == 2 and game_state.player.health <= 0:
        remove_enemy_corpses_at_position(
            game_state.floor,
            (
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
        )

    record_familiar_hit_feedback(game_state, started_at)
    for barrage_shot in game_state.player.archer_barrage_shots:
        if barrage_shot.started_at == 0:
            barrage_shot.started_at = started_at

    _record_player_feedback(
        game_state,
        current_act,
        started_at,
        movement_state,
        movement_profile,
    )
    _record_enemy_feedback(game_state, started_at)
    apply_movement_interruptions(
        movement_state,
        game_state,
        pygame.time.get_ticks(),
    )
    _play_turn_sounds(
        game_state,
        current_act,
        movement_state,
        act_one_sounds,
        act_two_sounds,
        act_three_sounds,
    )


__all__ = ["present_turn_feedback"]
