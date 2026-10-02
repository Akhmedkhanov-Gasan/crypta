from acts.act_three.presentation.animation import _stable_text_seed
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
LANTERN_WARDEN_IDLE_FRAME_MS = 450
LANTERN_WARDEN_IDLE_SEQUENCE = (
    0, 1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1,
)
LANTERN_WARDEN_IDLE_ANIMATED = True
LANTERN_WARDEN_IDLE_DIRECTION = "down"
LANTERN_WARDEN_MOVE_DURATION_MS = 220


def _idle_frame(enemy, current_time, visual_seed):
    if not LANTERN_WARDEN_IDLE_ANIMATED:
        return LANTERN_WARDEN_IDLE_SEQUENCE[0]

    identity_seed = (
        visual_seed
        ^ _stable_text_seed(enemy.name)
    )
    sequence_index = (
        current_time // max(1, LANTERN_WARDEN_IDLE_FRAME_MS)
        + identity_seed
    ) % len(LANTERN_WARDEN_IDLE_SEQUENCE)

    return LANTERN_WARDEN_IDLE_SEQUENCE[sequence_index]


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
    if enemy.health <= 0:
        return

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
    frame_index = _idle_frame(
        enemy,
        current_time,
        context.floor.visual_seed,
    )
    direction = _direction(enemy)
    sprite = assets[
        f"enemy_lantern_warden_idle_{direction}_{frame_index}"
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
    context.view_surface.blit(sprite, position)

    _draw_health_bar(
        context.view_surface,
        position[0] + tile_size // 2,
        position[1] + tile_size,
        enemy.health,
        enemy.max_health,
        HEALTH_BAR_COLOR,
    )
