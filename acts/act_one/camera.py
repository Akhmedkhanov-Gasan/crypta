from dataclasses import dataclass

import pygame

from presentation.camera import (
    PixelCamera,
    draw_pixel_camera_view,
    update_pixel_camera,
)
from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import BACKGROUND_COLOR, GAME_HEIGHT, GAME_WIDTH, TILE_SIZE


ACT_ONE_CAMERA_SCALE = 2

_CAMERA_RESPONSE_MS = 145

_DEAD_ZONE = (
    TILE_SIZE * 2,
    TILE_SIZE * 2,
    TILE_SIZE * 3 // 2,
    TILE_SIZE * 3 // 4,
)

_VIEWPORT = pygame.Rect(
    0,
    0,
    GAME_WIDTH,
    GAME_HEIGHT,
)


@dataclass
class ActOneCamera(PixelCamera):
    zoom: int = ACT_ONE_CAMERA_SCALE


def update_act_one_camera(
    camera,
    dungeon_map,
    player_column,
    player_row,
    floor_index,
    current_time,
):
    world_size = (
        len(dungeon_map[0]) * TILE_SIZE,
        len(dungeon_map) * TILE_SIZE,
    )
    player_focus = (
        player_column * TILE_SIZE + TILE_SIZE / 2,
        player_row * TILE_SIZE + TILE_SIZE / 2,
    )

    update_pixel_camera(
        camera,
        world_size,
        _VIEWPORT,
        player_focus,
        floor_index,
        current_time,
        _DEAD_ZONE,
        response_ms=_CAMERA_RESPONSE_MS,
        constrain_to_world=False,
    )


def draw_act_one_camera_view(screen, world_surface, camera):
    draw_pixel_camera_view(
        screen,
        world_surface,
        camera,
        _VIEWPORT,
        source_origin=(MAP_OFFSET_X, MAP_OFFSET_Y),
        background=BACKGROUND_COLOR,
    )


__all__ = [
    "ActOneCamera",
    "draw_act_one_camera_view",
    "update_act_one_camera",
]