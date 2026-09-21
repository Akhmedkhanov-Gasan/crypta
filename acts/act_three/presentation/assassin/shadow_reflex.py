import math

import pygame

from acts.act_three.presentation.view import _view_position
from acts.act_three.settings import (
    ASSASSIN_SHADOW_REFLEX_DAGGER_IMPACT_MS,
    ASSASSIN_SHADOW_REFLEX_DAGGER_RELEASE_MS,
    ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS,
    ASSASSIN_SHADOW_REFLEX_LABEL_MS,
    ASSASSIN_SHADOW_REFLEX_LABEL_RISE,
)
from game.events import GameEventType
from presentation.layout import ACT_THREE_TILE_SIZE


_DAGGER_SURFACE = None


def _smooth_progress(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3 - 2 * progress)


def _dagger_surface():
    global _DAGGER_SURFACE

    if _DAGGER_SURFACE is not None:
        return _DAGGER_SURFACE

    dagger = pygame.Surface((24, 12), pygame.SRCALPHA)

    pygame.draw.polygon(
        dagger,
        (77, 85, 96, 235),
        (
            (3, 4),
            (15, 3),
            (22, 6),
            (15, 9),
            (3, 8),
        ),
    )
    pygame.draw.polygon(
        dagger,
        (202, 215, 224, 255),
        (
            (5, 4),
            (15, 4),
            (21, 6),
            (15, 6),
            (5, 6),
        ),
    )
    pygame.draw.line(
        dagger,
        (238, 246, 250, 245),
        (8, 4),
        (19, 6),
        1,
    )
    pygame.draw.rect(
        dagger,
        (38, 24, 31, 255),
        (3, 2, 3, 8),
    )
    pygame.draw.line(
        dagger,
        (126, 46, 58, 255),
        (2, 2),
        (2, 9),
        2,
    )
    pygame.draw.circle(
        dagger,
        (178, 44, 58, 255),
        (3, 6),
        1,
    )

    _DAGGER_SURFACE = dagger
    return dagger


def record_shadow_reflex_feedback(
    game_state,
    started_at,
):
    if game_state.player.subclass != "assassin":
        return

    event = next(
        (
            event
            for event in reversed(game_state.events)
            if (
                event.type is GameEventType.ATTACK
                and event.actor == "hero"
                and event.data.get("kind")
                == "assassin_shadow_reflex"
                and event.origin is not None
                and event.positions
            )
        ),
        None,
    )
    if event is None:
        return

    player = game_state.player
    player.shadow_reflex_started_at = started_at
    player.shadow_reflex_origin = event.origin
    player.shadow_reflex_target = event.positions[0]
    player.shadow_reflex_ranged = bool(
        event.data.get("ranged", False)
    )
    player.attack_animation_started_at = started_at
    game_state.player_attack_targets = [
        event.positions[0]
    ]


def _draw_smoke_trail(
    surface,
    position,
    direction,
    progress,
):
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )

    for index in range(5):
        distance = 5 + index * 5
        drift = math.sin(
            progress * math.tau * 2
            + index * 1.7
        ) * 2
        perpendicular = (
            -direction[1],
            direction[0],
        )
        center = (
            round(
                position[0]
                - direction[0] * distance
                + perpendicular[0] * drift
            ),
            round(
                position[1]
                - direction[1] * distance
                + perpendicular[1] * drift
            ),
        )
        radius = 3 if index < 2 else 2
        alpha = round(
            75
            * (1 - index / 5)
            * (0.6 + math.sin(math.pi * progress) * 0.4)
        )

        pygame.draw.circle(
            overlay,
            (38, 43, 54, alpha),
            center,
            radius + 2,
        )
        pygame.draw.circle(
            overlay,
            (91, 101, 116, alpha // 2),
            center,
            radius,
        )

    surface.blit(overlay, (0, 0))


def _draw_dagger_impact(
    surface,
    destination,
    elapsed,
):
    progress = min(
        1,
        elapsed / ASSASSIN_SHADOW_REFLEX_DAGGER_IMPACT_MS,
    )
    visibility = 1 - progress
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    radius = round(4 + progress * 12)
    alpha = round(175 * visibility)

    pygame.draw.circle(
        overlay,
        (188, 42, 58, alpha // 3),
        destination,
        radius + 4,
    )
    pygame.draw.circle(
        overlay,
        (225, 220, 211, alpha),
        destination,
        radius,
        width=1,
    )

    for index in range(5):
        angle = index * math.tau / 5 + 0.35
        start = (
            round(
                destination[0]
                + math.cos(angle) * radius * 0.4
            ),
            round(
                destination[1]
                + math.sin(angle) * radius * 0.4
            ),
        )
        end = (
            round(
                destination[0]
                + math.cos(angle) * radius
            ),
            round(
                destination[1]
                + math.sin(angle) * radius
            ),
        )

        pygame.draw.line(
            overlay,
            (194, 54, 67, alpha),
            start,
            end,
            1,
        )

    surface.blit(overlay, (0, 0))


def _draw_shadow_reflex_dagger(
    surface,
    player,
    current_time,
    camera_x,
    camera_y,
):
    if (
        not player.shadow_reflex_ranged
        or player.shadow_reflex_origin is None
        or player.shadow_reflex_target is None
    ):
        return

    elapsed = (
        current_time
        - player.shadow_reflex_started_at
        - ASSASSIN_SHADOW_REFLEX_DAGGER_RELEASE_MS
    )
    total_duration = (
        ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS
        + ASSASSIN_SHADOW_REFLEX_DAGGER_IMPACT_MS
    )
    if not 0 <= elapsed < total_duration:
        return

    origin_position = _view_position(
        player.shadow_reflex_origin[0],
        player.shadow_reflex_origin[1],
        camera_x,
        camera_y,
    )
    target_position = _view_position(
        player.shadow_reflex_target[0],
        player.shadow_reflex_target[1],
        camera_x,
        camera_y,
    )
    origin = (
        origin_position[0] + ACT_THREE_TILE_SIZE // 2,
        origin_position[1] + ACT_THREE_TILE_SIZE // 2,
    )
    destination = (
        target_position[0] + ACT_THREE_TILE_SIZE // 2,
        target_position[1] + ACT_THREE_TILE_SIZE // 2,
    )

    if elapsed >= ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS:
        _draw_dagger_impact(
            surface,
            destination,
            elapsed - ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS,
        )
        return

    progress = (
        elapsed
        / ASSASSIN_SHADOW_REFLEX_DAGGER_TRAVEL_MS
    )
    eased_progress = _smooth_progress(progress)
    difference_x = destination[0] - origin[0]
    difference_y = destination[1] - origin[1]
    distance = max(
        1.0,
        math.hypot(difference_x, difference_y),
    )
    direction = (
        difference_x / distance,
        difference_y / distance,
    )
    arc = math.sin(math.pi * progress) * 7

    position = (
        origin[0] + difference_x * eased_progress,
        origin[1] + difference_y * eased_progress - arc,
    )

    _draw_smoke_trail(
        surface,
        position,
        direction,
        progress,
    )

    dagger = pygame.transform.rotate(
        _dagger_surface(),
        -math.degrees(
            math.atan2(
                difference_y,
                difference_x,
            )
        ),
    )
    dagger_rectangle = dagger.get_rect(
        center=(
            round(position[0]),
            round(position[1]),
        )
    )

    glow = pygame.Surface(
        (28, 28),
        pygame.SRCALPHA,
    )
    pygame.draw.circle(
        glow,
        (142, 34, 49, 42),
        (14, 14),
        10,
    )
    surface.blit(
        glow,
        glow.get_rect(center=dagger_rectangle.center),
    )
    surface.blit(dagger, dagger_rectangle)


def _draw_shadow_reflex_label(
    surface,
    player,
    current_time,
    camera_x,
    camera_y,
    font,
):
    if player.shadow_reflex_origin is None:
        return

    elapsed = (
        current_time
        - player.shadow_reflex_started_at
    )
    if not 0 <= elapsed < ASSASSIN_SHADOW_REFLEX_LABEL_MS:
        return

    progress = elapsed / ASSASSIN_SHADOW_REFLEX_LABEL_MS
    fade_in = min(1.0, progress / 0.16)
    fade_out = min(1.0, (1 - progress) / 0.38)
    alpha = round(
        235 * min(fade_in, fade_out)
    )
    rise = round(
        ASSASSIN_SHADOW_REFLEX_LABEL_RISE
        * _smooth_progress(progress)
    )
    player_position = _view_position(
        player.shadow_reflex_origin[0],
        player.shadow_reflex_origin[1],
        camera_x,
        camera_y,
    )
    center = (
        player_position[0] + ACT_THREE_TILE_SIZE // 2,
        player_position[1] - 5 - rise,
    )

    shadow = font.render(
        "Shadow Reflex",
        True,
        (12, 10, 16),
    )
    label = font.render(
        "Shadow Reflex",
        True,
        (211, 202, 211),
    )
    shadow.set_alpha(alpha)
    label.set_alpha(alpha)

    label_rectangle = label.get_rect(
        midbottom=center,
    )
    surface.blit(
        shadow,
        label_rectangle.move(1, 2),
    )
    surface.blit(
        label,
        label_rectangle,
    )


def draw_shadow_reflex_feedback(
    surface,
    player,
    current_time,
    camera_x,
    camera_y,
    font,
):
    if player.shadow_reflex_started_at < 0:
        return

    _draw_shadow_reflex_dagger(
        surface,
        player,
        current_time,
        camera_x,
        camera_y,
    )
    _draw_shadow_reflex_label(
        surface,
        player,
        current_time,
        camera_x,
        camera_y,
        font,
    )
