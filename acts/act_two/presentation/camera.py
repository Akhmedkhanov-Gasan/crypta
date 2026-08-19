from dataclasses import dataclass
import math

import pygame

from presentation.layout import (
    ACT_TWO_RENDER_SCALE,
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_LOGICAL_HEIGHT,
    ACT_TWO_VIEW_LOGICAL_WIDTH,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
)
from settings import BACKGROUND_COLOR, TILE_SIZE


_CAMERA_RESPONSE_MS = 145
_DEAD_ZONE_X = TILE_SIZE * 2
_DEAD_ZONE_Y = TILE_SIZE


@dataclass
class ActTwoCamera:
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    floor_index: int = -1
    updated_at: int = -1


def act_two_world_surface_size(dungeon_map) -> tuple[int, int]:
    map_width = len(dungeon_map[0]) * TILE_SIZE
    map_height = len(dungeon_map) * TILE_SIZE
    return (
        MAP_OFFSET_X + max(map_width, ACT_TWO_VIEW_LOGICAL_WIDTH),
        MAP_OFFSET_Y + max(map_height, ACT_TWO_VIEW_LOGICAL_HEIGHT),
    )


def _camera_limits(dungeon_map) -> tuple[int, int]:
    return (
        max(
            0,
            len(dungeon_map[0]) * TILE_SIZE
            - ACT_TWO_VIEW_LOGICAL_WIDTH,
        ),
        max(
            0,
            len(dungeon_map) * TILE_SIZE
            - ACT_TWO_VIEW_LOGICAL_HEIGHT,
        ),
    )


def _clamp(value, maximum):
    return max(0.0, min(float(maximum), float(value)))


def _centered_camera_target(
    dungeon_map,
    player_column,
    player_row,
):
    maximum_x, maximum_y = _camera_limits(dungeon_map)
    player_x = player_column * TILE_SIZE + TILE_SIZE / 2
    player_y = player_row * TILE_SIZE + TILE_SIZE / 2
    return (
        _clamp(player_x - ACT_TWO_VIEW_LOGICAL_WIDTH / 2, maximum_x),
        _clamp(player_y - ACT_TWO_VIEW_LOGICAL_HEIGHT / 2, maximum_y),
    )


def update_act_two_camera(
    camera,
    dungeon_map,
    player_column,
    player_row,
    floor_index,
    current_time,
):
    if camera.floor_index != floor_index or camera.updated_at < 0:
        camera.x, camera.y = _centered_camera_target(
            dungeon_map,
            player_column,
            player_row,
        )
        camera.target_x = camera.x
        camera.target_y = camera.y
        camera.floor_index = floor_index
        camera.updated_at = current_time
        return

    player_x = player_column * TILE_SIZE + TILE_SIZE / 2
    player_y = player_row * TILE_SIZE + TILE_SIZE / 2
    center_x = camera.target_x + ACT_TWO_VIEW_LOGICAL_WIDTH / 2
    center_y = camera.target_y + ACT_TWO_VIEW_LOGICAL_HEIGHT / 2

    if player_x < center_x - _DEAD_ZONE_X:
        camera.target_x = player_x + _DEAD_ZONE_X - (
            ACT_TWO_VIEW_LOGICAL_WIDTH / 2
        )
    elif player_x > center_x + _DEAD_ZONE_X:
        camera.target_x = player_x - _DEAD_ZONE_X - (
            ACT_TWO_VIEW_LOGICAL_WIDTH / 2
        )
    if player_y < center_y - _DEAD_ZONE_Y:
        camera.target_y = player_y + _DEAD_ZONE_Y - (
            ACT_TWO_VIEW_LOGICAL_HEIGHT / 2
        )
    elif player_y > center_y + _DEAD_ZONE_Y:
        camera.target_y = player_y - _DEAD_ZONE_Y - (
            ACT_TWO_VIEW_LOGICAL_HEIGHT / 2
        )

    elapsed = max(0, min(50, current_time - camera.updated_at))
    blend = 1 - math.exp(-elapsed / _CAMERA_RESPONSE_MS)
    camera.x += (camera.target_x - camera.x) * blend
    camera.y += (camera.target_y - camera.y) * blend
    if abs(camera.target_x - camera.x) < 0.05:
        camera.x = camera.target_x
    if abs(camera.target_y - camera.y) < 0.05:
        camera.y = camera.target_y
    camera.updated_at = current_time


def _draw_camera_vignette(screen):
    vignette = pygame.Surface(
        (ACT_TWO_VIEW_WIDTH, ACT_TWO_VIEW_HEIGHT),
        pygame.SRCALPHA,
    )
    for inset, alpha, width in (
        (0, 92, 28),
        (24, 51, 22),
        (47, 25, 18),
    ):
        pygame.draw.rect(
            vignette,
            (1, 3, 7, alpha),
            (
                inset,
                inset,
                ACT_TWO_VIEW_WIDTH - inset * 2,
                ACT_TWO_VIEW_HEIGHT - inset * 2,
            ),
            width=width,
        )
    screen.blit(vignette, (ACT_TWO_VIEW_X, ACT_TWO_VIEW_Y))


def draw_act_two_camera_view(screen, world_surface, camera):
    source_rectangle = pygame.Rect(
        MAP_OFFSET_X + round(camera.x),
        MAP_OFFSET_Y + round(camera.y),
        ACT_TWO_VIEW_LOGICAL_WIDTH,
        ACT_TWO_VIEW_LOGICAL_HEIGHT,
    )
    view = pygame.Surface(
        (ACT_TWO_VIEW_LOGICAL_WIDTH, ACT_TWO_VIEW_LOGICAL_HEIGHT)
    )
    view.fill(BACKGROUND_COLOR)

    visible_rectangle = source_rectangle.clip(world_surface.get_rect())

    if visible_rectangle.width > 0 and visible_rectangle.height > 0:
        visible_piece = world_surface.subsurface(visible_rectangle)

        destination = (
            visible_rectangle.x - source_rectangle.x,
            visible_rectangle.y - source_rectangle.y,
        )

        view.blit(visible_piece, destination)

    enlarged = pygame.transform.scale(
        view,
        (ACT_TWO_VIEW_WIDTH, ACT_TWO_VIEW_HEIGHT),
    )
    screen.blit(enlarged, (ACT_TWO_VIEW_X, ACT_TWO_VIEW_Y))
    _draw_camera_vignette(screen)


def act_two_screen_to_cell(position, camera):
    screen_x, screen_y = position
    if not (
        ACT_TWO_VIEW_X <= screen_x < ACT_TWO_VIEW_X + ACT_TWO_VIEW_WIDTH
        and ACT_TWO_VIEW_Y
        <= screen_y
        < ACT_TWO_VIEW_Y + ACT_TWO_VIEW_HEIGHT
    ):
        return None
    world_x = (
        (screen_x - ACT_TWO_VIEW_X) // ACT_TWO_RENDER_SCALE
        + round(camera.x)
    )
    world_y = (
        (screen_y - ACT_TWO_VIEW_Y) // ACT_TWO_RENDER_SCALE
        + round(camera.y)
    )
    return world_x // TILE_SIZE, world_y // TILE_SIZE
