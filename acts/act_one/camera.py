from dataclasses import dataclass
import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


ACT_ONE_CAMERA_SCALE = 2
ACT_ONE_CAMERA_VIEW_WIDTH = GAME_WIDTH // ACT_ONE_CAMERA_SCALE
ACT_ONE_CAMERA_VIEW_HEIGHT = GAME_HEIGHT // ACT_ONE_CAMERA_SCALE
_CAMERA_RESPONSE_MS = 145
_DEAD_ZONE_X = TILE_SIZE * 2
_DEAD_ZONE_Y = TILE_SIZE


@dataclass
class ActOneCamera:
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    floor_index: int = -1
    updated_at: int = -1


def _camera_limits(dungeon_map):
    return (
        max(
            0,
            len(dungeon_map[0]) * TILE_SIZE
            - ACT_ONE_CAMERA_VIEW_WIDTH,
        ),
        max(
            0,
            len(dungeon_map) * TILE_SIZE
            - ACT_ONE_CAMERA_VIEW_HEIGHT,
        ),
    )


def _clamp(value, maximum):
    return max(0.0, min(float(maximum), float(value)))


def _centered_target(dungeon_map, player_column, player_row):
    maximum_x, maximum_y = _camera_limits(dungeon_map)
    player_x = player_column * TILE_SIZE + TILE_SIZE / 2
    player_y = player_row * TILE_SIZE + TILE_SIZE / 2
    return (
        _clamp(
            player_x - ACT_ONE_CAMERA_VIEW_WIDTH / 2,
            maximum_x,
        ),
        _clamp(
            player_y - ACT_ONE_CAMERA_VIEW_HEIGHT / 2,
            maximum_y,
        ),
    )


def update_act_one_camera(
    camera,
    dungeon_map,
    player_column,
    player_row,
    floor_index,
    current_time,
):
    maximum_x, maximum_y = _camera_limits(dungeon_map)
    if camera.floor_index != floor_index or camera.updated_at < 0:
        camera.x, camera.y = _centered_target(
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
    center_x = camera.target_x + ACT_ONE_CAMERA_VIEW_WIDTH / 2
    center_y = camera.target_y + ACT_ONE_CAMERA_VIEW_HEIGHT / 2

    if player_x < center_x - _DEAD_ZONE_X:
        camera.target_x = (
            player_x + _DEAD_ZONE_X - ACT_ONE_CAMERA_VIEW_WIDTH / 2
        )
    elif player_x > center_x + _DEAD_ZONE_X:
        camera.target_x = (
            player_x - _DEAD_ZONE_X - ACT_ONE_CAMERA_VIEW_WIDTH / 2
        )
    if player_y < center_y - _DEAD_ZONE_Y:
        camera.target_y = (
            player_y + _DEAD_ZONE_Y - ACT_ONE_CAMERA_VIEW_HEIGHT / 2
        )
    elif player_y > center_y + _DEAD_ZONE_Y:
        camera.target_y = (
            player_y - _DEAD_ZONE_Y - ACT_ONE_CAMERA_VIEW_HEIGHT / 2
        )

    camera.target_x = _clamp(camera.target_x, maximum_x)
    camera.target_y = _clamp(camera.target_y, maximum_y)
    elapsed = max(0, min(50, current_time - camera.updated_at))
    blend = 1 - math.exp(-elapsed / _CAMERA_RESPONSE_MS)
    camera.x += (camera.target_x - camera.x) * blend
    camera.y += (camera.target_y - camera.y) * blend
    if abs(camera.target_x - camera.x) < 0.05:
        camera.x = camera.target_x
    if abs(camera.target_y - camera.y) < 0.05:
        camera.y = camera.target_y
    camera.updated_at = current_time


def draw_act_one_camera_view(screen, world_surface, camera):
    source_rectangle = pygame.Rect(
        MAP_OFFSET_X + round(camera.x),
        MAP_OFFSET_Y + round(camera.y),
        ACT_ONE_CAMERA_VIEW_WIDTH,
        ACT_ONE_CAMERA_VIEW_HEIGHT,
    )
    view = world_surface.subsurface(source_rectangle)
    enlarged = pygame.transform.scale(view, (GAME_WIDTH, GAME_HEIGHT))
    screen.blit(enlarged, (0, 0))


__all__ = [
    "ActOneCamera",
    "draw_act_one_camera_view",
    "update_act_one_camera",
]
