import pygame

from acts.act_three.presentation.camera import act_three_world_view_size
from acts.act_three.presentation.view import _camera_position
from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)


def get_act_three_cell_from_position(game_state, game_position):
    if game_position is None:
        return None

    viewport = pygame.Rect(
        ACT_THREE_VIEW_X,
        ACT_THREE_VIEW_Y,
        ACT_THREE_VIEW_WIDTH,
        ACT_THREE_VIEW_HEIGHT,
    )
    if not viewport.collidepoint(game_position):
        return None

    floor = game_state.floor
    camera_x, camera_y = _camera_position(floor)
    view_width, view_height = act_three_world_view_size(floor)

    world_x = (game_position[0] - viewport.x) * view_width / viewport.width + camera_x
    world_y = (game_position[1] - viewport.y) * view_height / viewport.height + camera_y

    return (
        int(world_x // ACT_THREE_TILE_SIZE),
        int(world_y // ACT_THREE_TILE_SIZE),
    )
