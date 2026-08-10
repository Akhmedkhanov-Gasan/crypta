from dataclasses import dataclass
import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


WARRIOR_MOVE_TRAVEL_MS = 195
WARRIOR_MOVE_SETTLE_MS = 45
WARRIOR_MOVE_DURATION_MS = (
    WARRIOR_MOVE_TRAVEL_MS + WARRIOR_MOVE_SETTLE_MS
)
ROGUE_MOVE_TRAVEL_MS = 170
ROGUE_MOVE_SETTLE_MS = 40
ROGUE_MOVE_DURATION_MS = ROGUE_MOVE_TRAVEL_MS + ROGUE_MOVE_SETTLE_MS
MAGE_MOVE_TRAVEL_MS = 215
MAGE_MOVE_SETTLE_MS = 35
MAGE_MOVE_DURATION_MS = MAGE_MOVE_TRAVEL_MS + MAGE_MOVE_SETTLE_MS


@dataclass(frozen=True)
class PlayerMovementPose:
    position: tuple[int, int]
    ground_position: tuple[int, int]
    direction: tuple[int, int]
    progress: float
    landing_progress: float
    active: bool


def _cell_position(column, row):
    return (
        MAP_OFFSET_X + column * TILE_SIZE,
        MAP_OFFSET_Y + row * TILE_SIZE,
    )


def _smoothstep(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def _smootherstep(progress):
    progress = max(0.0, min(1.0, progress))
    return (
        progress
        * progress
        * progress
        * (progress * (progress * 6.0 - 15.0) + 10.0)
    )


def sample_warrior_movement(
    column,
    row,
    origin,
    current_time,
    movement_started_at,
):
    destination_position = _cell_position(column, row)
    inactive_pose = PlayerMovementPose(
        position=destination_position,
        ground_position=destination_position,
        direction=(0, 0),
        progress=1.0,
        landing_progress=1.0,
        active=False,
    )
    if origin is None or movement_started_at <= 0:
        return inactive_pose

    direction = (column - origin[0], row - origin[1])
    if abs(direction[0]) + abs(direction[1]) != 1:
        return inactive_pose

    elapsed = current_time - movement_started_at
    if not 0 <= elapsed < WARRIOR_MOVE_DURATION_MS:
        return inactive_pose

    travel_progress = min(1.0, elapsed / WARRIOR_MOVE_TRAVEL_MS)
    eased_progress = _smoothstep(travel_progress)
    origin_position = _cell_position(*origin)
    ground_position = (
        round(
            origin_position[0]
            + (destination_position[0] - origin_position[0])
            * eased_progress
        ),
        round(
            origin_position[1]
            + (destination_position[1] - origin_position[1])
            * eased_progress
        ),
    )

    stride = math.sin(math.pi * travel_progress)
    body_lift = round(stride * 1.35)
    landing_progress = 0.0
    landing_drop = 0
    if elapsed >= WARRIOR_MOVE_TRAVEL_MS:
        landing_progress = min(
            1.0,
            (elapsed - WARRIOR_MOVE_TRAVEL_MS)
            / WARRIOR_MOVE_SETTLE_MS,
        )
        landing_drop = round(math.sin(math.pi * landing_progress))

    return PlayerMovementPose(
        position=(
            ground_position[0],
            ground_position[1] - body_lift + landing_drop,
        ),
        ground_position=ground_position,
        direction=direction,
        progress=travel_progress,
        landing_progress=landing_progress,
        active=True,
    )


def sample_rogue_movement(
    column,
    row,
    origin,
    current_time,
    movement_started_at,
):
    destination_position = _cell_position(column, row)
    inactive_pose = PlayerMovementPose(
        position=destination_position,
        ground_position=destination_position,
        direction=(0, 0),
        progress=1.0,
        landing_progress=1.0,
        active=False,
    )
    if origin is None or movement_started_at <= 0:
        return inactive_pose

    direction = (column - origin[0], row - origin[1])
    if abs(direction[0]) + abs(direction[1]) != 1:
        return inactive_pose

    elapsed = current_time - movement_started_at
    if not 0 <= elapsed < ROGUE_MOVE_DURATION_MS:
        return inactive_pose

    travel_progress = min(1.0, elapsed / ROGUE_MOVE_TRAVEL_MS)
    eased_progress = _smoothstep(travel_progress)
    origin_position = _cell_position(*origin)
    ground_position = (
        round(
            origin_position[0]
            + (destination_position[0] - origin_position[0])
            * eased_progress
        ),
        round(
            origin_position[1]
            + (destination_position[1] - origin_position[1])
            * eased_progress
        ),
    )

    landing_progress = 0.0
    settle_recoil = 0
    if elapsed >= ROGUE_MOVE_TRAVEL_MS:
        landing_progress = min(
            1.0,
            (elapsed - ROGUE_MOVE_TRAVEL_MS) / ROGUE_MOVE_SETTLE_MS,
        )
        settle_recoil = round(math.sin(math.pi * landing_progress))

    return PlayerMovementPose(
        position=(
            ground_position[0] - direction[0] * settle_recoil,
            ground_position[1] - direction[1] * settle_recoil,
        ),
        ground_position=ground_position,
        direction=direction,
        progress=travel_progress,
        landing_progress=landing_progress,
        active=True,
    )


def sample_mage_movement(
    column,
    row,
    origin,
    current_time,
    movement_started_at,
):
    destination_position = _cell_position(column, row)
    inactive_pose = PlayerMovementPose(
        position=destination_position,
        ground_position=destination_position,
        direction=(0, 0),
        progress=1.0,
        landing_progress=1.0,
        active=False,
    )
    if origin is None or movement_started_at <= 0:
        return inactive_pose

    direction = (column - origin[0], row - origin[1])
    if abs(direction[0]) + abs(direction[1]) != 1:
        return inactive_pose

    elapsed = current_time - movement_started_at
    if not 0 <= elapsed < MAGE_MOVE_DURATION_MS:
        return inactive_pose

    travel_progress = min(1.0, elapsed / MAGE_MOVE_TRAVEL_MS)
    eased_progress = _smootherstep(travel_progress)
    origin_position = _cell_position(*origin)
    ground_position = (
        round(
            origin_position[0]
            + (destination_position[0] - origin_position[0])
            * eased_progress
        ),
        round(
            origin_position[1]
            + (destination_position[1] - origin_position[1])
            * eased_progress
        ),
    )

    landing_progress = 0.0
    body_lift = round(math.sin(math.pi * travel_progress) * 2.2)
    if elapsed >= MAGE_MOVE_TRAVEL_MS:
        landing_progress = min(
            1.0,
            (elapsed - MAGE_MOVE_TRAVEL_MS) / MAGE_MOVE_SETTLE_MS,
        )
        body_lift = round(math.sin(math.pi * landing_progress))

    return PlayerMovementPose(
        position=(ground_position[0], ground_position[1] - body_lift),
        ground_position=ground_position,
        direction=direction,
        progress=travel_progress,
        landing_progress=landing_progress,
        active=True,
    )


def draw_warrior_movement_grounding(screen, pose):
    if not pose.active:
        return

    stride = math.sin(math.pi * pose.progress)
    shadow_width = 18 - round(stride * 3)
    shadow_height = 5 - round(stride)
    shadow = pygame.Surface((28, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (4, 6, 8, round(118 - stride * 30)),
        (
            (shadow.get_width() - shadow_width) // 2,
            4,
            shadow_width,
            shadow_height,
        ),
    )
    screen.blit(
        shadow,
        (
            pose.ground_position[0] + TILE_SIZE // 2 - 14,
            pose.ground_position[1] + TILE_SIZE - 9,
        ),
    )

    if not 0 < pose.landing_progress < 1:
        return

    visibility = math.sin(math.pi * pose.landing_progress)
    dust = pygame.Surface((34, 14), pygame.SRCALPHA)
    for index, horizontal_offset in enumerate((-9, -5, 6, 10)):
        drift = round(horizontal_offset * pose.landing_progress * 0.45)
        rise = round((index % 2 + 1) * visibility)
        pygame.draw.rect(
            dust,
            (104, 94, 78, round(72 * visibility)),
            (
                17 + horizontal_offset + drift,
                8 - rise,
                2,
                1 if index % 2 else 2,
            ),
        )
    screen.blit(
        dust,
        (
            pose.ground_position[0] + TILE_SIZE // 2 - 17,
            pose.ground_position[1] + TILE_SIZE - 10,
        ),
    )


def draw_rogue_movement_grounding(screen, sprite, pose):
    if not pose.active:
        return

    stride = math.sin(math.pi * pose.progress)
    shadow = pygame.Surface((28, 10), pygame.SRCALPHA)
    shadow_width = 16 - round(stride * 3)
    pygame.draw.ellipse(
        shadow,
        (5, 4, 8, round(92 - stride * 24)),
        (
            (shadow.get_width() - shadow_width) // 2,
            4,
            shadow_width,
            3,
        ),
    )
    screen.blit(
        shadow,
        (
            pose.ground_position[0] + TILE_SIZE // 2 - 14,
            pose.ground_position[1] + TILE_SIZE - 8,
        ),
    )

    visibility = math.sin(math.pi * min(1.0, pose.progress))
    for echo_index, distance in enumerate((8, 4)):
        echo = sprite.copy()
        echo.fill((44, 8, 65, 0), special_flags=pygame.BLEND_RGBA_ADD)
        echo.set_alpha(round((24 + echo_index * 18) * visibility))
        screen.blit(
            echo,
            (
                pose.position[0] - pose.direction[0] * distance,
                pose.position[1] - pose.direction[1] * distance,
            ),
        )

    if pose.progress <= 0.2 or pose.progress >= 0.95:
        return

    trace = pygame.Surface((44, 44), pygame.SRCALPHA)
    trace_center = (22, 22)
    for index, spread in enumerate((-5, 0, 5)):
        trace_position = (
            trace_center[0]
            - pose.direction[0] * (11 + index * 2)
            - pose.direction[1] * spread,
            trace_center[1]
            - pose.direction[1] * (11 + index * 2)
            + pose.direction[0] * spread,
        )
        pygame.draw.rect(
            trace,
            (153, 73, 195, round((48 + index * 12) * visibility)),
            (*trace_position, 2, 2),
        )
    screen.blit(
        trace,
        (
            pose.position[0] + TILE_SIZE // 2 - trace_center[0],
            pose.position[1] + TILE_SIZE // 2 - trace_center[1],
        ),
    )


def draw_mage_movement_grounding(screen, pose):
    if not pose.active:
        return

    hover = math.sin(math.pi * pose.progress)
    shadow = pygame.Surface((32, 12), pygame.SRCALPHA)
    shadow_width = 18 - round(hover * 5)
    pygame.draw.ellipse(
        shadow,
        (5, 8, 13, round(86 - hover * 34)),
        (
            (shadow.get_width() - shadow_width) // 2,
            4,
            shadow_width,
            4,
        ),
    )
    pygame.draw.ellipse(
        shadow,
        (58, 139, 205, round(28 + hover * 34)),
        (
            (shadow.get_width() - shadow_width - 4) // 2,
            3,
            shadow_width + 4,
            6,
        ),
        width=1,
    )
    screen.blit(
        shadow,
        (
            pose.ground_position[0] + TILE_SIZE // 2 - 16,
            pose.ground_position[1] + TILE_SIZE - 9,
        ),
    )

    if pose.progress <= 0.08 or pose.progress >= 0.97:
        return

    effect = pygame.Surface((52, 52), pygame.SRCALPHA)
    center = (26, 27)
    visibility = math.sin(math.pi * pose.progress)
    for index in range(7):
        phase = index * 1.71
        trail_distance = 7 + index * 2 + pose.progress * 5
        perpendicular = math.sin(phase + pose.progress * 2.4) * (4 + index % 3)
        particle_position = (
            round(
                center[0]
                - pose.direction[0] * trail_distance
                - pose.direction[1] * perpendicular
            ),
            round(
                center[1]
                - pose.direction[1] * trail_distance
                + pose.direction[0] * perpendicular
                - (index % 2) * 3
            ),
        )
        color = (91, 184, 239) if index % 3 else (153, 220, 255)
        pygame.draw.rect(
            effect,
            (*color, round((52 + index * 8) * visibility)),
            (*particle_position, 2 if index % 2 else 3, 2),
        )
    screen.blit(
        effect,
        (
            pose.position[0] + TILE_SIZE // 2 - center[0],
            pose.position[1] + TILE_SIZE // 2 - center[1],
        ),
    )
