from dataclasses import dataclass

import pygame

from presentation.camera import PixelCamera, update_pixel_camera
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
)
from presentation.map_navigation import get_map_navigation
from presentation.movement import smoothstep
from settings import GAME_WIDTH


_DEAD_ZONE = (
    ACT_THREE_TILE_SIZE * 2,
    ACT_THREE_TILE_SIZE * 2,
    ACT_THREE_TILE_SIZE + ACT_THREE_TILE_SIZE // 2,
    ACT_THREE_TILE_SIZE * 3 // 4,
)

_ZOOM_DURATION_MS = 240
_OVERVIEW_SCALE = 0.5


@dataclass
class ActThreeCamera(PixelCamera):
    scale: float = 1.0
    zoom_start_scale: float = 1.0
    zoom_target_scale: float = 1.0
    zoom_started_at: int = 0


_CAMERA = ActThreeCamera(zoom=1)


def act_three_camera_scale(floor):
    if _CAMERA.floor_index == id(floor):
        return _CAMERA.scale
    return _target_scale(floor)


def _target_scale(floor):
    return _OVERVIEW_SCALE if get_map_navigation(floor).overview else 1.0


def act_three_view_buffer_size(size):
    normal_size = (ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT)
    if size == normal_size:
        return normal_size
    return (
        round(ACT_THREE_VIEW_WIDTH / _OVERVIEW_SCALE),
        round(ACT_THREE_VIEW_HEIGHT / _OVERVIEW_SCALE),
    )


def act_three_world_view_size(floor):
    scale = act_three_camera_scale(floor)
    return (
        round(ACT_THREE_VIEW_WIDTH / scale),
        round(ACT_THREE_VIEW_HEIGHT / scale),
    )


def _world_size(floor):
    return (
        len(floor.map[0]) * ACT_THREE_TILE_SIZE,
        len(floor.map) * ACT_THREE_TILE_SIZE,
    )


def _player_focus(floor):
    return (
        floor.player_column * ACT_THREE_TILE_SIZE
        + ACT_THREE_TILE_SIZE / 2,
        floor.player_row * ACT_THREE_TILE_SIZE
        + ACT_THREE_TILE_SIZE / 2,
    )


def _update_zoom(floor, current_time, focus):
    target = _target_scale(floor)
    if _CAMERA.floor_index != id(floor) or current_time < _CAMERA.updated_at:
        _CAMERA.scale = target
        _CAMERA.zoom_start_scale = target
        _CAMERA.zoom_target_scale = target
        _CAMERA.updated_at = -1
        return

    if target != _CAMERA.zoom_target_scale:
        _CAMERA.zoom_start_scale = _CAMERA.scale
        _CAMERA.zoom_target_scale = target
        _CAMERA.zoom_started_at = current_time

    if _CAMERA.scale == target:
        return

    previous_width, previous_height = act_three_world_view_size(floor)
    elapsed = current_time - _CAMERA.zoom_started_at
    if elapsed >= _ZOOM_DURATION_MS:
        _CAMERA.scale = target
    else:
        progress = smoothstep(elapsed / _ZOOM_DURATION_MS)
        _CAMERA.scale = (
            _CAMERA.zoom_start_scale
            + (target - _CAMERA.zoom_start_scale) * progress
        )
    width, height = act_three_world_view_size(floor)
    shift_x = (focus[0] - _CAMERA.x) * (1.0 - width / previous_width)
    shift_y = (focus[1] - _CAMERA.y) * (1.0 - height / previous_height)
    _CAMERA.x += shift_x
    _CAMERA.y += shift_y
    _CAMERA.target_x += shift_x
    _CAMERA.target_y += shift_y


def update_act_three_camera(
    floor,
    current_time,
    player_position=None,
    cinematic=False,
):
    focus = _player_focus(floor)

    if player_position is not None:
        focus = (
            player_position[0] + ACT_THREE_TILE_SIZE / 2,
            player_position[1] + ACT_THREE_TILE_SIZE / 2,
        )

    _update_zoom(floor, current_time, focus)
    viewport = pygame.Rect((0, 0), act_three_world_view_size(floor))

    update_pixel_camera(
        _CAMERA,
        _world_size(floor),
        viewport,
        focus,
        id(floor),
        current_time,
        (
            (0, 0, 0, 0)
            if cinematic
            else _DEAD_ZONE
        ),
        response_ms=210 if cinematic else 145,
        constrain_to_world=False,
    )


def act_three_camera_position():
    return round(_CAMERA.x), round(_CAMERA.y)


def act_three_centered_camera_position(floor, position):
    view_width, view_height = act_three_world_view_size(floor)

    return (
        round(
            position[0] * ACT_THREE_TILE_SIZE
            + ACT_THREE_TILE_SIZE / 2
            - view_width / 2
        ),
        round(
            position[1] * ACT_THREE_TILE_SIZE
            + ACT_THREE_TILE_SIZE / 2
            - view_height / 2
        ),
    )


def act_three_camera_controls_offset(rectangle):
    return (
        GAME_WIDTH - rectangle.width - 24 - rectangle.x,
        24 - rectangle.y,
    )
