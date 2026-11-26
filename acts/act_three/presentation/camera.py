import pygame

from presentation.camera import PixelCamera, update_pixel_camera
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
)


_DEAD_ZONE = (
    ACT_THREE_TILE_SIZE * 2,
    ACT_THREE_TILE_SIZE * 2,
    ACT_THREE_TILE_SIZE + ACT_THREE_TILE_SIZE // 2,
    ACT_THREE_TILE_SIZE * 3 // 4,
)

_CAMERA = PixelCamera(zoom=1)


def act_three_world_view_size(floor):
    return ACT_THREE_VIEW_WIDTH, ACT_THREE_VIEW_HEIGHT


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


def snap_act_three_camera(floor, current_time):
    _CAMERA.floor_index = -1
    update_act_three_camera(floor, current_time)


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


