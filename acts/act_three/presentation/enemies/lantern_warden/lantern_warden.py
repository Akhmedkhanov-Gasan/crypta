import pygame

from .lantern_warden_animation import (
    warden_action,
    warden_death_frame,
    warden_direction,
)
from .lantern_warden_combat import (
    draw_warden_combat_effects,
    draw_warden_death_effects,
)
from acts.act_three.presentation.animation import _stable_text_seed
from acts.act_three.presentation.enemies.lantern_warden.lantern_warden_effects import (
    draw_warden_presence,
)
from acts.act_three.presentation.lighting import draw_actor_shadow
from acts.act_three.presentation.primitives import _draw_health_bar
from presentation.layout import ACT_THREE_TILE_SIZE
from settings import HEALTH_BAR_COLOR


LANTERN_WARDEN_DIRECTIONS = (
    "down",
    "left",
    "right",
    "up",
)
LANTERN_WARDEN_FRAME_COUNT = 8
LANTERN_WARDEN_IDLE_FRAME_MS = 1100
LANTERN_WARDEN_IDLE_BLEND_MS = 300
LANTERN_WARDEN_IDLE_SEQUENCE = (
    0, 1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1,
)
LANTERN_WARDEN_IDLE_ANIMATED = True
LANTERN_WARDEN_IDLE_DIRECTION = "down"
LANTERN_WARDEN_MOVE_DURATION_MS = 220
LANTERN_WARDEN_EFFECTS_ENABLED = True


def _idle_frames(current_time, identity_seed):
    sequence = LANTERN_WARDEN_IDLE_SEQUENCE

    if not LANTERN_WARDEN_IDLE_ANIMATED or len(sequence) == 1:
        return sequence[0], sequence[0], 0.0

    frame_duration = max(1, LANTERN_WARDEN_IDLE_FRAME_MS)
    blend_duration = max(
        0,
        min(
            frame_duration,
            LANTERN_WARDEN_IDLE_BLEND_MS,
        ),
    )
    cycle_duration = len(sequence) * frame_duration
    elapsed = (
        current_time + identity_seed % cycle_duration
    ) % cycle_duration

    sequence_index, frame_elapsed = divmod(
        elapsed,
        frame_duration,
    )
    current_frame = sequence[sequence_index]
    next_frame = sequence[
        (sequence_index + 1) % len(sequence)
    ]

    if blend_duration == 0:
        return current_frame, next_frame, 0.0

    hold_duration = frame_duration - blend_duration
    blend = max(
        0.0,
        min(
            1.0,
            (frame_elapsed - hold_duration) / blend_duration,
        ),
    )
    blend = blend * blend * (3.0 - 2.0 * blend)

    return current_frame, next_frame, blend


def _draw_idle_sprite(
    surface,
    sprite,
    next_sprite,
    position,
    blend,
):
    if blend <= 0.0 or sprite is next_sprite:
        surface.blit(sprite, position)
        return

    next_weight = round(blend * 255)
    current_weight = 255 - next_weight

    blended = sprite.premul_alpha()
    incoming = next_sprite.premul_alpha()

    blended.fill(
        (current_weight,) * 4,
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    incoming.fill(
        (next_weight,) * 4,
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    blended.blit(
        incoming,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )
    surface.blit(
        blended,
        position,
        special_flags=pygame.BLEND_PREMULTIPLIED,
    )


def _direction(enemy):
    if enemy.movement_origin is None:
        return LANTERN_WARDEN_IDLE_DIRECTION

    column_change = enemy.column - enemy.movement_origin[0]
    row_change = enemy.row - enemy.movement_origin[1]

    if abs(column_change) > abs(row_change):
        return "right" if column_change > 0 else "left"

    if row_change:
        return "down" if row_change > 0 else "up"

    return LANTERN_WARDEN_IDLE_DIRECTION


def _world_position(enemy, current_time, tile_size):
    origin = enemy.movement_origin

    if origin is None or enemy.movement_animation_started_at <= 0:
        return (
            enemy.column * tile_size,
            enemy.row * tile_size,
        )

    elapsed = current_time - enemy.movement_animation_started_at
    progress = max(
        0.0,
        min(
            1.0,
            elapsed / max(1, LANTERN_WARDEN_MOVE_DURATION_MS),
        ),
    )
    progress = progress * progress * (3.0 - 2.0 * progress)

    return (
        (
            origin[0]
            + (enemy.column - origin[0]) * progress
        ) * tile_size,
        (
            origin[1]
            + (enemy.row - origin[1]) * progress
        ) * tile_size,
    )


def draw_lantern_warden(
    context,
    assets,
    enemy,
    current_time,
):
    tile_size = ACT_THREE_TILE_SIZE
    sprite_size = tile_size * 2
    world_position = _world_position(
        enemy,
        current_time,
        tile_size,
    )
    position = (
        round(world_position[0] - context.camera_x),
        round(world_position[1] - context.camera_y),
    )
    identity_seed = (
        context.floor.visual_seed
        ^ _stable_text_seed(enemy.name)
    )
    if enemy.health <= 0:
        direction = warden_direction(enemy)
        frame_index = warden_death_frame(
            enemy,
            current_time,
        )
        sprite = assets[
            f"enemy_lantern_warden_death_{direction}_{frame_index}"
        ]

        draw_actor_shadow(
            context.view_surface,
            sprite,
            position,
            sprite_size,
            (),
            context.camera_x,
            context.camera_y,
            (
                "enemy",
                enemy.type,
                sprite.get_size(),
            ),
        )

        if LANTERN_WARDEN_EFFECTS_ENABLED:
            draw_warden_death_effects(
                context.view_surface,
                position,
                sprite_size,
                enemy,
                current_time,
                identity_seed,
            )

        context.view_surface.blit(sprite, position)

        if LANTERN_WARDEN_EFFECTS_ENABLED:
            draw_warden_death_effects(
                context.view_surface,
                position,
                sprite_size,
                enemy,
                current_time,
                identity_seed,
                foreground=True,
            )

        return
    action, direction, frame_index = warden_action(
        enemy,
        current_time,
        LANTERN_WARDEN_MOVE_DURATION_MS,
        LANTERN_WARDEN_FRAME_COUNT,
    )

    if action == "idle":
        frame_index, next_frame_index, blend = _idle_frames(
            current_time,
            identity_seed,
        )
    else:
        next_frame_index = frame_index
        blend = 0.0

    sprite = assets[
        f"enemy_lantern_warden_{action}_{direction}_{frame_index}"
    ]
    next_sprite = assets[
        f"enemy_lantern_warden_{action}_{direction}_{next_frame_index}"
    ]

    draw_actor_shadow(
        context.view_surface,
        sprite,
        position,
        sprite_size,
        (),
        context.camera_x,
        context.camera_y,
        (
            "enemy",
            enemy.type,
            sprite.get_size(),
        ),
    )

    if LANTERN_WARDEN_EFFECTS_ENABLED:
        draw_warden_presence(
            context.view_surface,
            position,
            sprite_size,
            current_time,
            identity_seed,
        )

    _draw_idle_sprite(
        context.view_surface,
        sprite,
        next_sprite,
        position,
        blend,
    )

    if LANTERN_WARDEN_EFFECTS_ENABLED:
        draw_warden_presence(
            context.view_surface,
            position,
            sprite_size,
            current_time,
            identity_seed,
            foreground=True,
        )
    draw_warden_combat_effects(
        context.view_surface,
        position,
        sprite_size,
        sprite,
        enemy,
        current_time,
        action,
    )
    _draw_health_bar(
        context.view_surface,
        position[0] + tile_size // 2,
        position[1] + tile_size,
        enemy.health,
        enemy.max_health,
        HEALTH_BAR_COLOR,
    )
