import math

import pygame

from game.events import GameEventType


FORCED_MOVEMENT_TRAVEL_MS = 260
FORCED_MOVEMENT_EFFECT_MS = 460


def record_forced_movement(player, events, started_at):
    movement = next(
        (
            event
            for event in reversed(events)
            if (
                event.type is GameEventType.MOVE
                and event.actor == "hero"
                and event.data.get("kind") == "sentinel_shield_knockback"
            )
        ),
        None,
    )
    if movement is None:
        return

    state = player.forced_movement
    state.origin = movement.origin
    state.destination = movement.destination
    state.direction = movement.data["direction"]
    state.collided = movement.data.get("collided", False)
    state.started_at = started_at


def forced_movement_is_active(player, current_time):
    started_at = player.forced_movement.started_at
    return (
        started_at >= 0
        and current_time < started_at + FORCED_MOVEMENT_EFFECT_MS
    )


def draw_stun_effect(screen, center_x, top_y, current_time):
    rotation = current_time / 190
    for star_index in range(3):
        angle = rotation + star_index * math.tau / 3
        star_center = (
            round(center_x + math.cos(angle) * 13),
            round(top_y + 7 + math.sin(angle) * 4),
        )
        pygame.draw.circle(
            screen,
            (246, 203, 77),
            star_center,
            3,
        )
        pygame.draw.circle(
            screen,
            (255, 244, 176),
            star_center,
            1,
        )


def draw_player_control_effects(
    screen,
    sprite,
    position,
    destination_position,
    player,
    current_time,
    tile_size,
):
    if player is None or player.health <= 0:
        return sprite, position

    state = player.forced_movement
    elapsed = current_time - state.started_at
    active = forced_movement_is_active(player, current_time)

    if active:
        progress = max(
            0.0,
            min(1.0, elapsed / FORCED_MOVEMENT_TRAVEL_MS),
        )
        travel = 1 - (1 - progress) ** 2
        displacement = (
            (state.origin[0] - state.destination[0]) * tile_size,
            (state.origin[1] - state.destination[1]) * tile_size,
        )
        bump = (
            math.sin(math.pi * progress) * tile_size * 0.16
            if state.collided
            else 0
        )
        position = (
            round(
                destination_position[0]
                + displacement[0] * (1 - travel)
                + state.direction[0] * bump
            ),
            round(
                destination_position[1]
                + displacement[1] * (1 - travel)
                + state.direction[1] * bump
                - math.sin(math.pi * progress) * tile_size * 0.12
            ),
        )

        if 0 <= elapsed < FORCED_MOVEMENT_TRAVEL_MS:
            tilt = -state.direction[0] * 16
            if not tilt:
                tilt = state.direction[1] * 10
            rotated = pygame.transform.rotate(
                sprite,
                tilt * math.sin(math.pi * progress),
            )
            center = (
                position[0] + sprite.get_width() / 2,
                position[1] + sprite.get_height() / 2,
            )
            position = rotated.get_rect(center=center).topleft
            sprite = rotated

            for index in (3, 2, 1):
                ghost = sprite.copy()
                ghost.set_alpha(28 + (3 - index) * 15)
                screen.blit(
                    ghost,
                    (
                        position[0] - state.direction[0] * index * 7,
                        position[1] - state.direction[1] * index * 7,
                    ),
                )

        if FORCED_MOVEMENT_TRAVEL_MS <= elapsed < FORCED_MOVEMENT_EFFECT_MS:
            landing = (
                elapsed - FORCED_MOVEMENT_TRAVEL_MS
            ) / (
                FORCED_MOVEMENT_EFFECT_MS - FORCED_MOVEMENT_TRAVEL_MS
            )
            center = (
                round(destination_position[0] + tile_size / 2),
                round(destination_position[1] + tile_size * 0.8),
            )
            color = (
                (246, 112, 78)
                if state.collided
                else (190, 180, 157)
            )
            for index in range(8):
                angle = index * math.tau / 8
                radius = tile_size * (0.15 + landing * 0.35)
                point = (
                    round(center[0] + math.cos(angle) * radius),
                    round(center[1] + math.sin(angle) * radius * 0.4),
                )
                pygame.draw.circle(
                    screen,
                    color,
                    point,
                    max(1, round(3 * (1 - landing))),
                )

    if player.stun_turns > 0:
        draw_stun_effect(
            screen,
            position[0] + sprite.get_width() / 2,
            position[1] - 7,
            current_time,
        )

    return sprite, position
