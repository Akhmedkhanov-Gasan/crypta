from acts.act_three.presentation.combat_effects import (
    record_enemy_death_feedback,
    record_enemy_hit_feedback,
    record_familiar_hit_feedback,
    record_player_death_feedback,
    record_player_hit_feedback,
)
from game.events import GameEventType
from systems.player_combat import (
    remove_enemy_corpses_at_position,
)
from acts.act_two.presentation.enemies.timing import (
    enemy_movement_duration,
)

def _record_enemy_dodge_feedback(game_state, started_at: int) -> None:
    feedback_events_by_target = {
        event.target: event
        for event in game_state.events
        if (
            event.target not in (None, "hero", "familiar")
            and event.type in (
                GameEventType.HIT,
                GameEventType.DODGE,
            )
        )
    }

    for enemy in game_state.floor.enemies:
        event = feedback_events_by_target.get(enemy.name)
        if event is None:
            continue

        enemy.hit_dodged = event.type is GameEventType.DODGE

        if not enemy.hit_dodged:
            continue

        enemy.hit_animation_started_at = started_at
        enemy.hit_damage = 0
        enemy.hit_critical = False
        enemy.hit_blocked = False
        enemy.hit_origin = event.origin
        enemy.hit_attacker_class = event.data.get("player_class")

def _record_player_dodge_feedback(
    game_state,
    started_at: int,
) -> None:
    player_dodged = any(
        event.type is GameEventType.DODGE
        and event.target == "hero"
        for event in game_state.events
    )

    if player_dodged:
        game_state.player.act_two.dodge_effect_started_at = started_at


def _visual_direction(
    direction: tuple[int, int],
) -> tuple[int, int]:
    column_change, row_change = direction

    if row_change:
        return 0, 1 if row_change > 0 else -1

    if column_change:
        return 1 if column_change > 0 else -1, 0

    return 0, 1


def present_act_two_turn_events(
    game_state,
    started_at: int,
    enemy_reaction_delay_ms: int = 0,
) -> bool:
    world_started_at = (
        started_at + enemy_reaction_delay_ms
    )
    events = game_state.events

    _record_enemy_dodge_feedback(game_state, started_at)
    _record_player_dodge_feedback(
        game_state,
        world_started_at,
    )
    record_enemy_hit_feedback(game_state, started_at)
    record_enemy_death_feedback(game_state, started_at)
    record_player_hit_feedback(
        game_state,
        world_started_at,
    )
    record_player_death_feedback(
        game_state,
        world_started_at,
    )
    record_familiar_hit_feedback(
        game_state,
        world_started_at,
    )

    if any(
        event.type is GameEventType.LEVEL_UP
        and event.actor == "hero"
        for event in events
    ):
        game_state.player.act_two.level_up_effect_started_at = (
            started_at
        )

    if game_state.player.health <= 0:
        remove_enemy_corpses_at_position(
            game_state.floor,
            (
                game_state.floor.player_column,
                game_state.floor.player_row,
            ),
        )

    for barrage_shot in game_state.player.archer_barrage_shots:
        if barrage_shot.started_at == 0:
            barrage_shot.started_at = started_at

    hero_move_event = next(
        (
            event
            for event in reversed(events)
            if (
                event.type is GameEventType.MOVE
                and event.actor == "hero"
                and event.origin is not None
                and event.destination is not None
            )
        ),
        None,
    )

    if hero_move_event is not None:
        player = game_state.player
        player.act_two_movement_started_at = started_at
        player.act_two_movement_origin = hero_move_event.origin

        movement_direction = (
            hero_move_event.destination[0]
            - hero_move_event.origin[0],
            hero_move_event.destination[1]
            - hero_move_event.origin[1],
        )
        player.act_two_facing_direction = _visual_direction(
            movement_direction
        )

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
    prepared_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.PREPARE_ATTACK
    }
    healed_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.HEAL
    }
    prepared_summon_enemy_names = {
        event.actor
        for event in events
        if event.type is GameEventType.PREPARE_SUMMON
    }
    summoned_enemy_names = {
        summoned_name
        for event in events
        if event.type is GameEventType.SUMMON
        for summoned_name in event.data.get(
            "summoned_names",
            (),
        )
    }
    for enemy in game_state.floor.enemies:
        if enemy.name in moved_enemy_names:
            movement_event = next(
                (
                    event
                    for event in reversed(events)
                    if (
                        event.type is GameEventType.MOVE
                        and event.actor == enemy.name
                        and event.origin is not None
                    )
                ),
                None,
            )

            if movement_event is not None:
                enemy.movement_animation_started_at = (
                    world_started_at
                )
                enemy.movement_origin = movement_event.origin
                enemy.movement_animation_kind = (
                    movement_event.data.get("kind")
                )

                if (
                    enemy.movement_animation_kind
                    == "arcane_burst_knockback"
                ):
                    enemy.movement_animation_started_at += 220

        if (
            enemy.name in attacked_enemy_names
            or enemy.name in healed_enemy_names
        ):
            enemy.attack_animation_started_at = (
                world_started_at
            )
        if enemy.name in prepared_enemy_names:
            telegraph_visible_at = world_started_at

            if enemy.name in moved_enemy_names:
                movement_duration = (
                    enemy_movement_duration(enemy)
                )
                telegraph_visible_at = (
                    enemy.movement_animation_started_at
                    + movement_duration
                )

            enemy.attack_telegraph_visible_at = (
                telegraph_visible_at
            )
        if enemy.name in prepared_summon_enemy_names:
            enemy.summon_animation_started_at = (
                world_started_at
            )

        if enemy.name in summoned_enemy_names:
            enemy.summon_spawn_animation_started_at = (
                world_started_at
            )
        if enemy.name in attacked_enemy_names:
            attack_event = next(
                (
                    event
                    for event in reversed(events)
                    if (
                        event.type is GameEventType.ATTACK
                        and event.actor == enemy.name
                    )
                ),
                None,
            )

            if attack_event is not None:
                enemy.attack_effect_mode = (
                    attack_event.data.get("mode")
                )
                enemy.attack_effect_positions = (
                    attack_event.positions
                )

        elif enemy.name in healed_enemy_names:
            enemy.attack_effect_mode = "heal"
            enemy.attack_effect_positions = ()

        if (
            enemy.type == "warden"
            and enemy.second_phase_announced
            and enemy.phase_transition_started_at < 0
        ):
            enemy.phase_transition_started_at = (
                world_started_at
            )

    return any(
        event.target == "hero"
        and event.type in (
            GameEventType.HIT,
            GameEventType.DODGE,
        )
        for event in events
    )