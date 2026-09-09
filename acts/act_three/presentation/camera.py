from presentation.layout import (
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
)
from presentation.map_navigation import get_map_navigation
from settings import GAME_WIDTH


def act_three_camera_scale(floor):
    return 0.5 if get_map_navigation(floor).overview else 1.0


def act_three_world_view_size(floor):
    scale = act_three_camera_scale(floor)
    return (
        round(ACT_THREE_VIEW_WIDTH / scale),
        round(ACT_THREE_VIEW_HEIGHT / scale),
    )


def act_three_camera_controls_offset(rectangle):
    return (
        GAME_WIDTH - rectangle.width - 24 - rectangle.x,
        24 - rectangle.y,
    )
