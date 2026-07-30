

from acts.act_three.presentation.view import _camera_position

from presentation.layout import (
    ACT_THREE_TILE_SIZE,
    ACT_THREE_VIEW_HEIGHT,
    ACT_THREE_VIEW_WIDTH,
    ACT_THREE_VIEW_X,
    ACT_THREE_VIEW_Y,
)


_TORCH_LIGHT_SURFACE = None
_IDLE_FRAME_SEQUENCE = (0, 1, 2, 1)
_IDLE_TIMELINE_CYCLE_COUNT = 4
_MOVE_FRAME_COUNT = 2
_MOVE_FRAME_DURATION_MS = 90
_ATTACK_FRAME_DURATION_MS = 240
_FAMILIAR_MOVE_DURATION_MS = 180
_TELEPORT_CAMERA_DURATION_MS = 480
_TELEPORT_EFFECT_DURATION_MS = 600
_ARCHER_BARRAGE_SHOT_EFFECT_MS = 360
_TOP_VOID_CORNER_Y_OFFSET = 47
_TOP_VOID_CORNER_X_OFFSETS = {
    "wall_corner_top_left": -18,
    "wall_corner_top_right": 18,
}
_TOP_VOID_DOUBLE_CORNER_CROP_WIDTH = 24

def get_act_three_cell_from_position(game_state, game_position):
    mouse_x, mouse_y = game_position
    if not (
        ACT_THREE_VIEW_X <= mouse_x < ACT_THREE_VIEW_X + ACT_THREE_VIEW_WIDTH
        and ACT_THREE_VIEW_Y <= mouse_y < ACT_THREE_VIEW_Y + ACT_THREE_VIEW_HEIGHT
    ):
        return None

    camera_x, camera_y = _camera_position(game_state.floor)
    column = (
        mouse_x - ACT_THREE_VIEW_X + camera_x
    ) // ACT_THREE_TILE_SIZE
    row = (
        mouse_y - ACT_THREE_VIEW_Y + camera_y
    ) // ACT_THREE_TILE_SIZE
    return (column, row)
