import math

import pygame

from game.events import GameEventType
from presentation.layout import ACT_THREE_TILE_SIZE


DODGE_FEEDBACK_DURATION_MS = 680
DODGE_REACTION_DURATION_MS = 220


def record_dodge_feedback(
    game_state,
    started_at,
):
    if game_state.floor.presentation_act < 3:
        return

    player_dodge_event = next(
        (
            event
            for event in reversed(game_state.events)
            if (
                event.type is GameEventType.DODGE
                and event.target == "hero"
            )
        ),
        None,
    )

    if player_dodge_event is not None:
        game_state.player.dodge_animation_started_at = (
            started_at
        )

    enemy_dodge_events = {
        event.target: event
        for event in game_state.events
        if (
            event.type is GameEventType.DODGE
            and event.target not in (
                None,
                "hero",
                "familiar",
            )
        )
    }

    for enemy in game_state.floor.enemies:
        dodge_event = enemy_dodge_events.get(
            enemy.name,
        )

        if dodge_event is None:
            continue

        enemy.hit_animation_started_at = started_at
        enemy.hit_damage = 0
        enemy.hit_critical = False
        enemy.hit_blocked = False
        enemy.hit_dodged = True
        enemy.hit_origin = dodge_event.origin
        enemy.hit_attacker_class = (
            dodge_event.data.get("player_class")
        )


def _draw_dodge_feedback(
    surface,
    sprite,
    position,
    current_time,
    started_at,
    damage_font,
):
    if started_at < 0:
        return False

    elapsed = current_time - started_at

    if not 0 <= elapsed < DODGE_FEEDBACK_DURATION_MS:
        return False

    reaction_progress = min(
        1.0,
        elapsed / DODGE_REACTION_DURATION_MS,
    )
    echo_visibility = (
        math.sin(math.pi * reaction_progress)
        if reaction_progress < 1.0
        else 0.0
    )
    echo_offset = round(
        echo_visibility * 7
    )

    if echo_offset:
        for direction, alpha in (
            (-1, 42),
            (1, 68),
        ):
            echo = sprite.copy()
            echo.fill(
                (24, 92, 112, 0),
                special_flags=pygame.BLEND_RGBA_ADD,
            )
            echo.set_alpha(
                round(alpha * echo_visibility)
            )
            surface.blit(
                echo,
                (
                    position[0]
                    + direction * echo_offset,
                    position[1],
                ),
            )

    surface.blit(sprite, position)

    progress = min(
        1.0,
        elapsed / DODGE_FEEDBACK_DURATION_MS,
    )
    alpha = round(
        255 * min(1.0, (1.0 - progress) * 2.4)
    )
    label = damage_font.render(
        "DODGE",
        True,
        (102, 226, 237),
    )
    label.set_alpha(alpha)

    label_position = label.get_rect(
        center=(
            position[0] + ACT_THREE_TILE_SIZE // 2,
            position[1] - 7 - round(progress * 14),
        )
    )

    shadow = damage_font.render(
        "DODGE",
        True,
        (6, 16, 20),
    )
    shadow.set_alpha(alpha)

    surface.blit(
        shadow,
        label_position.move(1, 2),
    )
    surface.blit(
        label,
        label_position,
    )

    return True


def draw_enemy_dodge_feedback(
    surface,
    sprite,
    position,
    enemy,
    current_time,
    damage_font,
):
    if not enemy.hit_dodged:
        return False

    return _draw_dodge_feedback(
        surface,
        sprite,
        position,
        current_time,
        enemy.hit_animation_started_at,
        damage_font,
    )


def draw_player_dodge_feedback(
    surface,
    sprite,
    position,
    player,
    current_time,
    damage_font,
):
    return _draw_dodge_feedback(
        surface,
        sprite,
        position,
        current_time,
        player.dodge_animation_started_at,
        damage_font,
    )
